import asyncio
import hashlib
import ipaddress
import json
import os
import socket
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from api.deps import get_current_tenant, get_current_user_token
from api.routes.admin_dashboard import require_admin_token
from core.browser_compat_store import browser_compat_store
from core.browser_session_catalog import SavedBrowserSession, browser_session_catalog
from core.browser_session_manager import session_manager
from core.cache.redis_manager import MultiLevelCache
from core.effective_policy import get_effective_policy, policy_store
from core.error_bus import with_error_bus
from core.logging_config import logger
from core.neon_repository import (
    create_task as create_neon_task,
)
from core.neon_repository import (
    delete_task as delete_neon_task,
)
from core.neon_repository import (
    list_tasks as list_neon_tasks,
)
from core.neon_repository import (
    load_policy as load_neon_policy,
)
from core.neon_repository import (
    save_policy as save_neon_policy,
)
from core.neon_repository import (
    update_task_status as update_neon_task_status,
)
from core.observability.audit_logger import AuditLogger
from core.security.secure_credential_store import SecureCredentialStore
from core.task_policy import evaluate_goal

router = APIRouter(
    prefix="/api/browser", tags=["browser"], dependencies=[Depends(get_current_user_token)]
)


class AutomationSessionRequest(BaseModel):
    """Create an isolated session; credentials are entered by the user in-browser."""

    label: str = Field(default="Browser session", min_length=1, max_length=120)
    saved_url: str | None = Field(default=None, max_length=2048)


class SavedSessionRequest(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=2048)
    session_id: str | None = Field(default=None, max_length=128)


class BrowserActionRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    action: Literal["navigate", "click", "fill", "type", "screenshot", "content", "extract"]
    url: str | None = Field(default=None, max_length=2048)
    selector: str | None = Field(default=None, min_length=1, max_length=512)
    value: str | None = Field(default=None, max_length=20_000)
    full_page: bool = False


class BrowserSessionResponse(BaseModel):
    session_id: str
    status: str
    url: str


def get_audit() -> AuditLogger:
    return AuditLogger()


@router.get("/automation/saved-sessions")
async def list_saved_sessions(user: dict = Depends(get_current_user_token)):
    owner_id = str(user.get("sub") or "")
    tenant_id = str(user.get("tenant_id") or "")
    if not owner_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Authenticated tenant claim required")
    return {
        "sessions": [item.__dict__ for item in browser_session_catalog.list(tenant_id, owner_id)]
    }


@router.post("/automation/saved-sessions")
async def save_session(payload: SavedSessionRequest, user: dict = Depends(get_current_user_token)):
    from core.security import is_safe_url

    owner_id = str(user.get("sub") or "")
    tenant_id = str(user.get("tenant_id") or "")
    if not owner_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Authenticated tenant claim required")
    if not owner_id or not tenant_id or not is_safe_url(payload.url):
        raise HTTPException(
            status_code=400, detail="Valid authenticated owner and safe URL are required"
        )
    item = browser_session_catalog.save(
        SavedBrowserSession(
            tenant_id=tenant_id,
            owner_id=owner_id,
            label=payload.label,
            url=payload.url,
            session_id=payload.session_id,
        )
    )
    return {"session": item.__dict__}


@router.delete("/automation/saved-sessions/{saved_session_id}")
async def revoke_saved_session(saved_session_id: str, user: dict = Depends(get_current_user_token)):
    owner_id = str(user.get("sub") or "")
    tenant_id = str(user.get("tenant_id") or "")
    if not owner_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Authenticated tenant claim required")
    if not browser_session_catalog.revoke(saved_session_id, tenant_id, owner_id):
        raise HTTPException(status_code=404, detail="Saved browser session not found")
    return {"success": True}


@router.post("/automation/sessions", response_model=BrowserSessionResponse)
async def create_automation_session(
    req: AutomationSessionRequest,
    user_token: str = Depends(get_current_user_token),
):
    from core.security import is_safe_url

    if req.saved_url and not is_safe_url(req.saved_url):
        raise HTTPException(status_code=400, detail="Unsafe or invalid saved URL")
    session = await session_manager.create(user_token, label=req.label, saved_url=req.saved_url)
    return BrowserSessionResponse(session_id=session.id, status="ready", url=session.page.url)


@router.get("/automation/sessions")
async def list_automation_sessions(user_token: str = Depends(get_current_user_token)):
    return {"sessions": [s for s in session_manager.snapshot() if s["owner_id"] == user_token]}


@router.delete("/automation/sessions/{session_id}")
async def close_automation_session(
    session_id: str, user_token: str = Depends(get_current_user_token)
):
    if not await session_manager.close(session_id, user_token):
        raise HTTPException(status_code=404, detail="Browser session not found")
    return {"success": True}


@router.post("/automation/actions")
async def execute_automation_action(
    req: BrowserActionRequest, user_token: str = Depends(get_current_user_token)
):
    from core.security import is_safe_url

    try:
        session = await session_manager.get(req.session_id, user_token)
    except PermissionError as exc:
        raise HTTPException(status_code=423, detail=str(exc)) from exc
    page = session.page
    action = req.action.lower()
    if action not in session.allowed_actions:
        raise HTTPException(status_code=403, detail="Action is not allowed for this session")
    if action == "navigate":
        if not req.url or not is_safe_url(req.url):
            raise HTTPException(status_code=400, detail="Unsafe or invalid URL")
        await page.goto(req.url, wait_until="domcontentloaded", timeout=30_000)
    elif action == "click":
        if not req.selector:
            raise HTTPException(status_code=422, detail="selector is required")
        await page.locator(req.selector).click(timeout=15_000)
    elif action in {"fill", "type"}:
        if not req.selector or req.value is None:
            raise HTTPException(status_code=422, detail="selector and value are required")
        await page.locator(req.selector).fill(req.value, timeout=15_000)
    elif action == "screenshot":
        image = await page.screenshot(type="png", full_page=req.full_page)
        import base64

        return {
            "success": True,
            "action": action,
            "url": page.url,
            "screenshot": base64.b64encode(image).decode("ascii"),
        }
    elif action in {"content", "extract"}:
        return {
            "success": True,
            "action": action,
            "url": page.url,
            "content": await page.locator("body").inner_text(timeout=15_000),
        }
    else:
        raise HTTPException(status_code=422, detail="Unsupported browser action")
    return {"success": True, "action": action, "url": page.url}


def get_credential_store() -> SecureCredentialStore:
    return SecureCredentialStore()


# Legacy UI state is retained for compatibility while canonical automation is owner-scoped.
# New endpoints should use browser_compat_store; these aliases are migration shims.
BROWSER_STATUS: dict[str, Any] = {"browsing": False, "currentUrl": "about:blank"}
RECENT_ACTIVITIES: list[dict[str, Any]] = []
CREDENTIALS: list[dict[str, Any]] = []
PAUSED_STATE: dict[str, Any] = {"paused": False}
URL_PERMISSIONS: list[dict[str, Any]] = []
PERMISSION_REQUESTS: list[dict[str, Any]] = []
SYSTEM_LEARNING: dict[str, Any] = {"enabled": True}
TASKS: dict[str, dict[str, Any]] = {}
FINDINGS: list[dict[str, Any]] = []

# বাংলা মন্তব���য: সার্কিট ব্রেকার থ্রেশোল্ড — টাস্ক এক্সিকিউশন ক্যাপ (৪৫ সেকেন্ড)
EXECUTION_CAP_MS = 45000


class GoalRequest(BaseModel):
    goal: str


class NavigateRequest(BaseModel):
    url: str


class ClickRequest(BaseModel):
    selector: str


class FillRequest(BaseModel):
    selector: str
    value: str


class ClickAtRequest(BaseModel):
    x: int
    y: int


class KeyRequest(BaseModel):
    key: str


class CredentialRequest(BaseModel):
    serviceName: str | None = None  # Frontend compat
    provider: str | None = None  # Canonical schema
    username: str | None = None  # Frontend compat
    label: str | None = None  # Canonical schema
    password: str | None = None  # Frontend compat
    secret: str | None = None  # Canonical schema
    userId: str | None = "default"
    authType: str | None = None
    secret_metadata: dict[str, Any] | None = None


class CredentialUseRequest(BaseModel):
    action: str | None = "autofill"
    target_url: str | None = None


class UrlPermissionRequest(BaseModel):
    urlPattern: str
    userId: str | None = "default"
    reason: str | None = "None"


class DecisionRequest(BaseModel):
    approved: bool


@router.post("/automation/pause")
async def pause_automation(user: dict = Depends(get_current_user_token)):
    owner_id = str(user.get("sub") or "")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Authenticated owner required")
    session_manager.pause_owner(owner_id)
    return {"status": "paused"}


@router.post("/automation/resume")
async def resume_automation(user: dict = Depends(get_current_user_token)):
    owner_id = str(user.get("sub") or "")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Authenticated owner required")
    session_manager.resume_owner(owner_id)
    return {"status": "active"}


@router.get("/surf/status")
def get_status(user: dict = Depends(get_current_user_token)):
    if not user.get("sub") or not user.get("tenant_id"):
        raise HTTPException(status_code=401, detail="Authenticated tenant required")
    return BROWSER_STATUS


@router.post("/surf/start")
def start_surf(user: dict = Depends(get_current_user_token)):
    if not user.get("sub") or not user.get("tenant_id"):
        raise HTTPException(status_code=401, detail="Authenticated tenant required")
    BROWSER_STATUS["browsing"] = True
    return {"status": "started"}


@router.post("/surf/stop")
def stop_surf(user: dict = Depends(get_current_user_token)):
    if not user.get("sub") or not user.get("tenant_id"):
        raise HTTPException(status_code=401, detail="Authenticated tenant required")
    BROWSER_STATUS["browsing"] = False
    return {"status": "stopped"}


@router.get("/activity/recent")
def get_recent_activity(user: dict = Depends(get_current_user_token)):
    if not user.get("sub") or not user.get("tenant_id"):
        raise HTTPException(status_code=401, detail="Authenticated tenant required")
    return {"activities": RECENT_ACTIVITIES}


@router.get("/credentials", dependencies=[Depends(require_admin_token)])
@with_error_bus("get_credentials")
def get_credentials(
    userId: str = "default",
    current_user: dict = Depends(get_current_user_token),
):
    import json

    from database.supabase_client import db

    cred_store = get_credential_store()
    effective_owner = current_user.get("sub") or userId or "default"
    user_creds = []

    # 1. Try fetching from Supabase DB
    db_rows = db.list_browser_credentials(effective_owner, include_revoked=False)
    if not db_rows and effective_owner != userId:
        db_rows = db.list_browser_credentials(userId, include_revoked=False)

    if db_rows:
        for row in db_rows:
            decrypted = cred_store.decrypt(row.get("encrypted_secret", ""), row.get("key_ref"))
            try:
                decrypted_dict = json.loads(decrypted)
            except Exception:
                decrypted_dict = {"secret": decrypted}

            masked_dict = {
                "id": row.get("id"),
                "serviceName": row.get("provider") or row.get("label"),
                "provider": row.get("provider"),
                "username": row.get("label"),
                "label": row.get("label"),
                "status": "revoked" if row.get("is_revoked") else "active",
                "createdAt": row.get("created_at"),
                "updatedAt": row.get("updated_at"),
                "lastUsedAt": row.get("updated_at"),
            }
            # Mask sensitive values
            for k, v in decrypted_dict.items():
                if k in ("password", "token", "secret", "api_key") and isinstance(v, str):
                    masked_dict[k] = cred_store.mask(v)
                elif k == "username":
                    masked_dict["username"] = v
            if "password" not in masked_dict and "secret" in decrypted_dict:
                masked_dict["password"] = cred_store.mask(decrypted_dict.get("secret", ""))

            user_creds.append(masked_dict)
    else:
        # Fallback to in-memory store for backwards compatibility or offline/test mode
        for c in CREDENTIALS:
            if c.get("userId") in (effective_owner, userId):
                decrypted = cred_store.decrypt(c.get("ciphertext", ""), c.get("key_ref"))
                try:
                    decrypted_dict = json.loads(decrypted)
                except Exception:
                    decrypted_dict = {}

                masked_dict = {"id": c.get("id")}
                for k, v in decrypted_dict.items():
                    if k in ("password", "token", "secret", "api_key", "username") and isinstance(
                        v, str
                    ):
                        if k == "username":
                            masked_dict[k] = v
                        else:
                            masked_dict[k] = cred_store.mask(v)
                    else:
                        masked_dict[k] = v
                masked_dict["serviceName"] = str(c.get("serviceName", ""))
                masked_dict["username"] = masked_dict.get("username") or str(c.get("username", ""))
                masked_dict["status"] = "active"
                user_creds.append(masked_dict)

    return {"credentials": user_creds}


@router.post("/credentials", dependencies=[Depends(require_admin_token)])
def save_credential(
    cred: CredentialRequest,
    current_user: dict = Depends(get_current_user_token),
):
    import json
    import uuid

    from database.supabase_client import db

    provider = cred.provider or cred.serviceName or "unknown_provider"
    label = cred.label or cred.username or "default"
    raw_secret = cred.secret or cred.password or ""
    owner_id = current_user.get("sub") or cred.userId or "default"

    if not raw_secret:
        raise HTTPException(status_code=400, detail="Secret or password is required")

    cred_store = get_credential_store()
    secret_payload = json.dumps(
        {
            "serviceName": provider,
            "username": label,
            "password": raw_secret,
            "secret": raw_secret,
            "authType": cred.authType or "basic_auth",
        }
    )
    ciphertext, key_ref = cred_store.encrypt(secret_payload)
    cred_id = f"cred_{uuid.uuid4().hex[:12]}"

    # Persist to Supabase
    db_row = {
        "id": cred_id,
        "owner_id": owner_id,
        "provider": provider,
        "label": label,
        "encrypted_secret": ciphertext,
        "key_ref": key_ref,
        "secret_metadata": cred.secret_metadata or {"auth_type": cred.authType or "basic_auth"},
        "is_revoked": False,
    }
    db.save_browser_credential(db_row)

    # In-memory mirror for local fallback
    new_cred = {
        "id": cred_id,
        "userId": owner_id,
        "serviceName": provider,
        "username": label,
        "ciphertext": ciphertext,
        "key_ref": key_ref,
    }
    CREDENTIALS.append(new_cred)

    # Redacted audit logging (Zero Secrets Exposed)
    get_audit().log_decision(
        action_type="browser_credential_created",
        decision_details=f"Stored credential id '{cred_id}' for provider '{provider}' and label '{label}'",
        reasoning=f"Owner '{owner_id}' created an encrypted browser credential.",
    )

    return {
        "id": cred_id,
        "serviceName": provider,
        "provider": provider,
        "label": label,
        "owner_id": owner_id,
        "success": True,
    }


@router.post("/credentials/{credential_id}/use", dependencies=[Depends(require_admin_token)])
def use_credential(
    credential_id: str,
    req: CredentialUseRequest | None = None,
    current_user: dict = Depends(get_current_user_token),
):
    import json

    from database.supabase_client import db

    caller_id = current_user.get("sub") or "admin"
    cred_store = get_credential_store()

    # Look up in Supabase
    row = db.get_browser_credential(credential_id)
    if not row:
        # Fallback to in-memory
        row = next((c for c in CREDENTIALS if c.get("id") == credential_id), None)

    if not row:
        get_audit().log_decision(
            action_type="browser_credential_access_failed",
            decision_details=f"Attempted access to non-existent credential id '{credential_id}'",
            reasoning=f"Caller '{caller_id}' requested unknown credential.",
        )
        raise HTTPException(status_code=404, detail="Credential not found")

    owner_id = row.get("owner_id") or row.get("userId")
    # Ownership verification: must be owner or admin
    if current_user.get("role") != "admin" and owner_id != caller_id:
        get_audit().log_decision(
            action_type="browser_credential_unauthorized_access",
            decision_details=f"Unauthorized use attempt for credential '{credential_id}' owned by '{owner_id}'",
            reasoning=f"Caller '{caller_id}' denied access due to ownership mismatch.",
        )
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this credential")

    if row.get("is_revoked"):
        get_audit().log_decision(
            action_type="browser_credential_access_failed",
            decision_details=f"Attempted access to revoked credential id '{credential_id}'",
            reasoning="Credential has been revoked.",
        )
        raise HTTPException(
            status_code=400, detail="Credential has been revoked and cannot be used"
        )

    # Decrypt in memory for automation execution
    ciphertext = row.get("encrypted_secret") or row.get("ciphertext") or ""
    key_ref = row.get("key_ref")
    decrypted = cred_store.decrypt(ciphertext, key_ref)
    try:
        decrypted_payload = json.loads(decrypted)
    except Exception:
        decrypted_payload = {"secret": decrypted}

    # Audit log (audit log receives NO raw secrets)
    action = req.action if req else "autofill"
    provider = row.get("provider") or row.get("serviceName") or "unknown"
    get_audit().log_decision(
        action_type="browser_credential_used",
        decision_details=f"Used credential id '{credential_id}' for provider '{provider}', action='{action}'",
        reasoning=f"Authorized autonomous browser execution by '{caller_id}'.",
    )

    return {
        "id": credential_id,
        "provider": provider,
        "label": row.get("label") or row.get("username"),
        "status": "active",
        "action": action,
        "secret": decrypted_payload.get("password") or decrypted_payload.get("secret"),
        "username": decrypted_payload.get("username"),
    }


@router.post("/credentials/{credential_id}/revoke", dependencies=[Depends(require_admin_token)])
def revoke_credential(
    credential_id: str,
    current_user: dict = Depends(get_current_user_token),
):
    from database.supabase_client import db

    caller_id = current_user.get("sub") or "admin"
    row = db.get_browser_credential(credential_id)
    if not row:
        row = next((c for c in CREDENTIALS if c.get("id") == credential_id), None)

    if not row:
        raise HTTPException(status_code=404, detail="Credential not found")

    owner_id = row.get("owner_id") or row.get("userId")
    if current_user.get("role") != "admin" and owner_id != caller_id:
        get_audit().log_decision(
            action_type="browser_credential_unauthorized_access",
            decision_details=f"Unauthorized revoke attempt for credential '{credential_id}'",
            reasoning=f"Caller '{caller_id}' denied access due to ownership mismatch.",
        )
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this credential")

    # Update in DB
    db.revoke_browser_credential(credential_id, owner_id)
    # Update in-memory
    for c in CREDENTIALS:
        if c.get("id") == credential_id:
            c["is_revoked"] = True

    get_audit().log_decision(
        action_type="browser_credential_revoked",
        decision_details=f"Revoked credential id '{credential_id}'",
        reasoning=f"Revocation executed by '{caller_id}'.",
    )
    return {"id": credential_id, "is_revoked": True, "success": True}


@router.delete("/credentials/{id}", dependencies=[Depends(require_admin_token)])
@router.delete("/credentials/{credential_id}", dependencies=[Depends(require_admin_token)])
def delete_credential(
    id: str | None = None,
    credential_id: str | None = None,
    current_user: dict = Depends(get_current_user_token),
):
    global CREDENTIALS
    from database.supabase_client import db

    target_id = id or credential_id
    if not target_id:
        raise HTTPException(status_code=400, detail="Credential id is required")

    caller_id = current_user.get("sub") or "admin"
    row = db.get_browser_credential(target_id)
    if not row:
        row = next((c for c in CREDENTIALS if c.get("id") == target_id), None)

    if not row:
        raise HTTPException(status_code=404, detail="Credential not found")

    owner_id = row.get("owner_id") or row.get("userId")
    if current_user.get("role") != "admin" and owner_id != caller_id:
        get_audit().log_decision(
            action_type="browser_credential_unauthorized_access",
            decision_details=f"Unauthorized delete attempt for credential '{target_id}'",
            reasoning=f"Caller '{caller_id}' denied access due to ownership mismatch.",
        )
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this credential")

    db.delete_browser_credential(target_id, owner_id)
    CREDENTIALS = [c for c in CREDENTIALS if c.get("id") != target_id]

    get_audit().log_decision(
        action_type="browser_credential_deleted",
        decision_details=f"Deleted credential id '{target_id}'",
        reasoning=f"Deletion executed by '{caller_id}'.",
    )
    return {"id": target_id, "success": True}


@router.post("/surf/resume", dependencies=[Depends(require_admin_token)])
def resume_surf(body: dict[str, str]):
    PAUSED_STATE["paused"] = False
    return {"status": "resumed"}


@router.post("/surf/skip-auth", dependencies=[Depends(require_admin_token)])
def skip_auth(body: dict[str, str]):
    PAUSED_STATE["paused"] = False
    return {"status": "auth_skipped"}


@router.post("/surf/pause-manual", dependencies=[Depends(require_admin_token)])
def pause_manual(body: dict[str, str]):
    PAUSED_STATE["paused"] = True
    return {"status": "paused_for_manual"}


@router.get("/surf/paused-state")
def get_paused_state():
    return PAUSED_STATE


@router.get("/urls/allowed")
def get_allowed_urls(userId: str = "default"):
    allowed = [
        u for u in URL_PERMISSIONS if u.get("type") == "allowed" and u.get("userId") == userId
    ]
    return {"urls": allowed}


@router.get("/urls/denied")
def get_denied_urls(userId: str = "default"):
    denied = [u for u in URL_PERMISSIONS if u.get("type") == "denied" and u.get("userId") == userId]
    return {"urls": denied}


@router.post("/urls/allowed", dependencies=[Depends(require_admin_token)])
def add_allowed_url(req: UrlPermissionRequest):
    perm = req.model_dump()
    perm["id"] = f"perm_{uuid.uuid4().hex[:12]}"
    perm["type"] = "allowed"
    URL_PERMISSIONS.append(perm)
    return perm


@router.post("/urls/denied", dependencies=[Depends(require_admin_token)])
def add_denied_url(req: UrlPermissionRequest):
    perm = req.model_dump()
    perm["id"] = f"perm_{uuid.uuid4().hex[:12]}"
    perm["type"] = "denied"
    URL_PERMISSIONS.append(perm)
    return perm


@router.post("/urls/allowAll", dependencies=[Depends(require_admin_token)])
def allow_all_urls(userId: str = "default"):
    perm = {
        "id": f"perm_{uuid.uuid4().hex[:12]}",
        "urlPattern": "*",
        "userId": userId,
        "type": "allowAll",
        "reason": "Allow all URLs",
    }
    URL_PERMISSIONS.append(perm)
    return perm


@router.delete("/urls/{id}", dependencies=[Depends(require_admin_token)])
def delete_url(url_id: str):
    global URL_PERMISSIONS
    URL_PERMISSIONS = [u for u in URL_PERMISSIONS if u.get("id") != url_id]
    return {"success": True}


@router.get("/urls/requests")
def get_requests():
    return {"requests": PERMISSION_REQUESTS}


@router.post("/urls/requests/{id}/decision", dependencies=[Depends(require_admin_token)])
def decision(request_id: str, req: DecisionRequest):
    """AUD-2.6/AUD-3.5: URL permission decisions grant browser access scope and
    therefore require an admin token (previously any authenticated user could
    self-approve URL permissions)."""
    for r in PERMISSION_REQUESTS:
        if r["id"] == request_id:
            r["status"] = "APPROVED" if req.approved else "DENIED"
            return {"success": True}
    raise HTTPException(status_code=404, detail="Request not found")


@router.get("/system-learning")
def get_system_learning():
    return SYSTEM_LEARNING


@router.post("/system-learning/toggle", dependencies=[Depends(require_admin_token)])
def toggle_learning(body: dict[str, bool]):
    SYSTEM_LEARNING["enabled"] = body.get("enabled", True)
    return {"success": True}


@router.get("/tasks")
async def get_tasks(
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    owner_id = str(user.get("sub") or "")
    return {"tasks": await list_neon_tasks(tenant_id, owner_id)}


class TaskPreviewRequest(BaseModel):
    url: str | None = Field(default=None, max_length=2048)
    goal: str = Field(min_length=1, max_length=10_000)
    approved: bool = False


class PolicyUpdateRequest(BaseModel):
    rules: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, bool] = Field(default_factory=dict)
    actions: dict[str, str] = Field(default_factory=dict)
    limits: dict[str, int] = Field(default_factory=dict)


class UserPolicyUpdateRequest(BaseModel):
    rules: dict[str, Any] = Field(default_factory=dict)


@router.get("/policy")
async def get_policy(
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    user_id = str(user.get("sub") or "")
    policy = get_effective_policy(user_id)
    admin_row = await load_neon_policy(tenant_id)
    user_row = await load_neon_policy(tenant_id, user_id)
    if admin_row:
        policy_store.update_admin(
            admin_row["rules"], admin_row["features"], admin_row["actions"], admin_row["limits"]
        )
        policy = get_effective_policy(user_id)
    if user_row:
        policy_store.update_user(user_id, user_row["rules"])
        policy = get_effective_policy(user_id)
    return {
        "rules": policy.rules,
        "features": policy.features,
        "actions": policy.actions,
        "limits": policy.limits,
        "sources": policy.sources,
        "version": policy.version,
    }


@router.put("/policy")
async def update_user_policy(
    payload: UserPolicyUpdateRequest,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    user_id = str(user.get("sub") or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authenticated user required")
    policy = policy_store.update_user(user_id, payload.rules)
    await save_neon_policy(tenant_id, user_id, user_id=user_id, rules=payload.rules)
    return {
        "rules": policy.rules,
        "features": policy.features,
        "actions": policy.actions,
        "limits": policy.limits,
        "sources": policy.sources,
    }


@router.put("/admin/policy", dependencies=[Depends(require_admin_token)])
async def update_admin_policy(
    payload: PolicyUpdateRequest,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    updated_by = str(user.get("sub") or "admin")
    policy = policy_store.update_admin(
        payload.rules, payload.features, payload.actions, payload.limits
    )
    await save_neon_policy(
        tenant_id,
        updated_by,
        rules=payload.rules,
        features=payload.features,
        actions=payload.actions,
        limits=payload.limits,
    )
    return {
        "rules": policy.rules,
        "features": policy.features,
        "actions": policy.actions,
        "limits": policy.limits,
        "sources": policy.sources,
    }


@router.post("/tasks/preview")
async def preview_task(
    req: TaskPreviewRequest,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    actor_id = str(user.get("sub") or "")
    decision = evaluate_goal(req.goal, actor_id)
    if not actor_id:
        raise HTTPException(status_code=401, detail="Authenticated user required")
    if not decision.allowed:
        return {"status": "manual", "risk": decision.risk, "message": decision.message}
    if decision.risk == "approval" and not req.approved:
        return {"status": "approval_required", "risk": decision.risk, "message": decision.message}
    task_id = uuid.uuid4()
    task = await create_neon_task(
        task_id=task_id,
        tenant_id=tenant_id,
        user_id=actor_id,
        url=req.url,
        goal=req.goal,
        status="ACTIVE",
        plan=[{"risk": decision.risk, "message": decision.message}],
    )
    return {
        "status": "started",
        "message": "Your safe task has started. SupremeAI will pause if it needs your approval.",
        "task": task,
    }


@router.post("/tasks")
async def create_task(
    req: GoalRequest,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    owner_id = str(user.get("sub") or "")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Authenticated user required")
    return await create_neon_task(
        task_id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=owner_id,
        url=None,
        goal=req.goal,
        status="ACTIVE",
    )


async def _set_task_status(
    task_id: str,
    status: str,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    owner_id = str(user.get("sub") or "")
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    updated = await update_neon_task_status(
        task_id=task_uuid, tenant_id=tenant_id, user_id=owner_id, status=status
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "status": status}


@router.post("/tasks/{id}/circuit-open")
async def set_task_circuit_open(
    task_id: str,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    return await _set_task_status(task_id, "CIRCUIT_OPEN", user, tenant_id)


@router.post("/tasks/{id}/complete")
async def set_task_complete(
    task_id: str,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    return await _set_task_status(task_id, "SUCCESS", user, tenant_id)


@router.post("/tasks/{id}/fail")
async def set_task_failed(
    task_id: str,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    return await _set_task_status(task_id, "FAILED", user, tenant_id)


@router.delete("/tasks/{id}")
async def delete_task(
    task_id: str,
    user: dict = Depends(get_current_user_token),
    tenant_id: str = Depends(get_current_tenant),
):
    owner_id = str(user.get("sub") or "")
    try:
        deleted = await delete_neon_task(
            task_id=uuid.UUID(task_id), tenant_id=tenant_id, user_id=owner_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}
    TASKS[task_id]["status"] = "CIRCUIT_OPEN"
    TASKS[task_id]["durationMs"] = EXECUTION_CAP_MS
    return {"success": True, "status": "CIRCUIT_OPEN"}


@router.post("/tasks/{id}/complete")
def set_task_complete(task_id: str):
    """বাংলা মন্তব্য: টাস্ক সফলভাবে সম্পন্ন হলে কল করু���"""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    TASKS[task_id]["status"] = "SUCCESS"
    return {"success": True, "status": "SUCCESS"}


@router.post("/tasks/{id}/fail")
def set_task_failed(task_id: str):
    """বাংলা মন্তব্য: টাস্ক ব্যর্থ হলে কল করুন"""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    TASKS[task_id]["status"] = "FAILED"
    return {"success": True, "status": "FAILED"}


@router.delete("/tasks/{id}")
def delete_task(task_id: str):
    if task_id in TASKS:
        del TASKS[task_id]
        return {"success": True}
    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/tasks/{id}/findings")
def get_findings(task_id: str):
    task_findings = [f for f in FINDINGS if f.get("taskId") == task_id]
    return {"findings": task_findings}


@router.post("/findings")
def add_finding(finding: dict[str, Any]):
    FINDINGS.append(finding)
    return finding


@router.get("/surf/screenshot")
def get_screenshot():
    # Return a mock transparent 1x1 PNG or read browser screenshot if initialized
    mock_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    return {"screenshot": mock_png}


@router.post("/surf/navigate")
def navigate(req: NavigateRequest):
    BROWSER_STATUS["currentUrl"] = req.url
    RECENT_ACTIVITIES.append(
        {
            "url": req.url,
            "action": "navigate",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    return {"success": True}


@router.post("/surf/click")
def click(req: ClickRequest):
    RECENT_ACTIVITIES.append(
        {
            "url": str(BROWSER_STATUS["currentUrl"]),
            "action": f"click {req.selector}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    return {"success": True}


@router.post("/surf/fill")
def fill(req: FillRequest):
    RECENT_ACTIVITIES.append(
        {
            "url": str(BROWSER_STATUS["currentUrl"]),
            "action": f"fill {req.selector} with {req.value}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    return {"success": True}


@router.post("/surf/click-at")
def click_at(req: ClickAtRequest):
    RECENT_ACTIVITIES.append(
        {
            "url": str(BROWSER_STATUS["currentUrl"]),
            "action": f"click at {req.x}, {req.y}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    return {"success": True}


@router.post("/surf/type-key")
def type_key(req: KeyRequest):
    RECENT_ACTIVITIES.append(
        {
            "url": str(BROWSER_STATUS["currentUrl"]),
            "action": f"type key {req.key}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    return {"success": True}


@router.get("/surf/accessibility")
def get_accessibility_tree():
    return {"role": "WebArea", "name": "SupremeAI Console", "children": []}


@router.post("/simulate-activity")
def simulate_activity(body: dict[str, str]):
    activity = {
        "url": body.get("url", "http://example.com"),
        "action": body.get("action", "surf"),
        "title": body.get("title", "Page Title"),
        "reasoning": body.get("reasoning", "Exploring content"),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    RECENT_ACTIVITIES.append(activity)
    return activity


# --- Crown Jewel Endpoints ---


@router.post("/browse-session")
def browse_session(body: dict[str, Any]):
    raw_url = str(body.get("url") or "")
    session_hash = hashlib.sha256(raw_url.encode("utf-8")).hexdigest()[:16]
    return {"success": True, "session_id": f"sess_{session_hash}"}


@router.post("/ai-action")
def ai_action(body: dict[str, Any]):
    action = body.get("action")
    return {
        "success": True,
        "action": action,
        "response": f"AI successfully processed {action}",
        "summary": "This is a mock summary for " + str(body.get("url")),
        "analysis": "This is a mock analysis.",
        "links": [],
        "issues": [],
        "criticalIssues": [],
    }


@router.post("/security-scan")
def security_scan(body: dict[str, Any]):
    return {"success": True, "score": 100, "issues": []}


@router.post("/screenshot")
def capture_screenshot(body: dict[str, Any]):
    # Returns the mock screenshot already in /surf/screenshot
    mock_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    import base64

    return Response(content=base64.b64decode(mock_png_base64), media_type="image/png")


# -----------------------------


@router.post("/tasks/{id}/step")
def execute_step(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    # Simulate a step execution
    return {
        "success": True,
        "action": "navigated to dashboard",
        "details": "Autonomous step succeeded",
    }


# ──────────────────────────────────────────────
# বাংলা মন্তব্য: সেশন স্টোর — Firestore-ভিত্তিক সেশন সিঙ্ক (VaultPage-এর মত ব্যাকএন্ড API কল)
# ──────────────────────────────────────────────
SESSIONS: dict[str, dict[str, Any]] = {}


class SessionMessageIn(BaseModel):
    id: int
    sender: str
    text: str
    timestamp: str


class SessionIn(BaseModel):
    id: str
    title: str
    status: str = "running"
    created_at: str = ""
    updated_at: str = ""
    messages: list[SessionMessageIn] = []


@router.get("/sessions")
def list_sessions():
    """বাংলা মন্তব্য: সব সেশন ত���লিকা রিটার্ন করে"""
    return {"sessions": list(SESSIONS.values())}


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    """বাংলা মন্তব্য: নির্দিষ্ট সেশন রিটার্ন করে"""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    return SESSIONS[session_id]


@router.post("/sessions")
def create_session(session: SessionIn):
    """বাংলা মন্তব্য: নতুন সেশন তৈরি করে"""
    now = datetime.now(UTC).isoformat()
    data = session.model_dump()
    if not data.get("created_at"):
        data["created_at"] = now
    if not data.get("updated_at"):
        data["updated_at"] = now
    SESSIONS[session.id] = data
    return {"success": True, "session": data}


@router.put("/sessions/{session_id}")
def update_session(session_id: str, session: SessionIn):
    """বাংলা মন্তব্য: বিদ্যমান সেশন আপডেট করে"""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    data = session.model_dump()
    data["updated_at"] = datetime.now(UTC).isoformat()
    SESSIONS[session_id] = data
    return {"success": True, "session": data}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """বাংলা মন্তব্য: সেশন মুছে ফেলে"""
    SESSIONS.pop(session_id, None)
    return {"success": True}


from pydantic import BaseModel

from tools.ai_agents.browser_agent import BrowseRequest


class ScrapeRequest(BaseModel):
    url: str


# বাংলা মন্তব্য: আগের BrowserAgent গ্লোবাল সিঙ্গলটন সরিয়ে দিয়েছি।
# এখন ব্র���উজার অটোমেশন স্ক্র্যা���ার মাইক্রোসার্ভিসে HTTP প্রক্সি করে (zero-cost,
# decoupled)। AGENTS.md §2: "Never treat tasks in isolation" — এই পরিবর্তনের পাশাপাশি
# Cloudflare Worker (worker.js) এবং render.yaml-এ scraper route যোগ করতে হবে।

import httpx

from core.config import settings

_SCRAPER_URL = settings.scraper_service_url.rstrip("/") if settings.scraper_service_url else None

# Hybrid-plan cache: keep scraped results in Upstash Redis (L2) + in-memory (L1)
# so the (off-Render, scale-to-zero) scraper microservice is invoked as rarely as
# possible — directly cutting its compute/quota consumption.
_SCRAPE_CACHE_TTL = 3600  # 1h
_scrape_cache = MultiLevelCache(l2_ttl=_SCRAPE_CACHE_TTL)


def _scrape_cache_key(url: str) -> str:
    return "scrape_cache:" + hashlib.sha256(url.encode("utf-8")).hexdigest()


async def _proxy_to_scraper(endpoint: str, payload: dict) -> dict:
    """Forward browser/scrape requests to the standalone scraper microservice."""
    if not _SCRAPER_URL:
        # Fallback: use local BrowserAgent (for local dev / when scraper service is not deployed)
        from tools.ai_agents.browser_agent import BrowserAgent

        agent = BrowserAgent()
        return await agent.navigate_and_interact(**payload)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{_SCRAPER_URL}/{endpoint}", json=payload)
            return resp.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.error(f"Scraper service proxy failed: {e}")
        return {"success": False, "error": str(e)}


async def _cached_scrape(payload: dict) -> dict:
    """Scrape with a Redis-backed cache (idempotent fetch only)."""
    url = payload.get("url", "")
    if not url:
        return await _proxy_to_scraper("scrape", payload)
    key = _scrape_cache_key(url)
    cached = await _scrape_cache.get(key)
    if cached is not None:
        try:
            return json.loads(cached)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            import logging

            logging.getLogger(__name__).exception(f"Silenced error: {e}")
    result = await _proxy_to_scraper("scrape", payload)
    if isinstance(result, dict) and result.get("success"):
        await _scrape_cache.set(key, json.dumps(result), ttl=_SCRAPE_CACHE_TTL)
    return result


@router.post("/scrape", dependencies=[Depends(require_admin_token)])
async def scrape(request: ScrapeRequest):
    """Fetch URL and return cleaned content via the Scraper Microservice."""
    result = await _cached_scrape({"url": request.url})
    return result


@router.post("/browse", dependencies=[Depends(require_admin_token)])
async def browse(request: BrowseRequest):
    """Navigate to a URL and perform browser actions via the Scraper Microservice (Admin Only)."""
    if request.action in ("click", "type", "scroll", "screenshot"):
        result = await _proxy_to_scraper(
            "browse",
            {
                "url": request.url,
                "action": request.action,
                "selector": request.selector,
                "text": request.text,
                "wait_for": request.wait_for,
            },
        )
        return result

    # Default action (fetch) — delegate to scraper service (cache-backed)
    result = await _cached_scrape({"url": request.url})
    return result


@router.post("/extract", dependencies=[Depends(require_admin_token)])
async def extract(url: str, extraction_prompt: str):
    """Fetch page and extract structured data with AI (Admin Only).

    Now proxies to the standalone scraper microservice for browser automation,
    then performs AI extraction on the returned content.
    """
    from core.security.protection.ssrf_protection import is_safe_url

    if not is_safe_url(url):
        raise HTTPException(
            status_code=400,
            detail="URL is not allowed: restricted by SSRF protection policy",
        )

    from tools.browser.ai_web_extractor import AIWebExtractor

    extractor = AIWebExtractor()
    return await extractor.extract_data(url, extraction_prompt)


# বাংলা মন্তব্য: ইন-অ্যাপ ব্রাউজার proxy (public) — বাহিরের সাইট X-Frame-Options/frame-ancestors দিয়ে
# iframe ব্লক করে, তাই সার্ভার-সাইড ফেচ করে iframe-এ রেন্ডার করা হয়। SSRF প্রতিরোধ জরুরি।
_BLOCKED_NETS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _host_is_blocked(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, 80)
    except (socket.gaierror, socket.herror, OSError):
        # DNS resolution failure means we cannot verify the host — treat as
        # blocked to fail-closed (deny-by-default) rather than masking the error.
        logger.warning("Host resolution failed for %s", hostname, exc_info=True)
        return True
    for info in infos:
        raw_ip = info[4][0].split("%")[0]
        try:
            addr = ipaddress.ip_address(raw_ip)
        except ValueError:
            return True
        if addr.is_loopback or addr.is_private or addr.is_reserved or addr.is_link_local:
            return True
        for net in _BLOCKED_NETS:
            if addr in net:
                return True
    return False


def _frame_ancestors_sources() -> str:
    """Build the CSP ``frame-ancestors`` source list for the render proxy.

    SEC-HARDEN P6: the proxy previously sent ``frame-ancestors *`` (plus a
    non-standard ``X-Frame-Options: ALLOWALL``). That let ANY third-party site
    embed the proxy — a clickjacking / UI-redressing surface. Now only the
    app's own surface (``'self'``) plus every operator-configured frontend
    origin (``ALLOWED_ORIGINS``) may frame it. Never ``*``.
    """
    sources = ["'self'"]
    for raw in os.getenv("ALLOWED_ORIGINS", "").split(","):
        origin = raw.strip()
        if origin:
            sources.append(origin)
    return " ".join(sources)


@router.get("/render")
def render_proxy(url: str):
    """Server-side web proxy so the in-app browser can render sites that block iframes.

    Uses stdlib urllib only (no third-party http client) so the route cannot be dropped
    because of a missing optional dependency at import time.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Only absolute http(s) URLs are supported.")
    if _host_is_blocked(parsed.hostname):
        raise HTTPException(status_code=400, detail="Blocked or unresolvable host.")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SupremeAI-Browser/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            ctype = resp.headers.get("Content-Type", "") or ""
            data = resp.read()
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=502, detail="Response too large to proxy.")
        proxy_headers = {
            "Cache-Control": "no-store",
            # SEC-HARDEN P6: never ALLOWALL / frame-ancestors * — only the app's
            # own surfaces may embed the proxy response (prevents clickjacking).
            "X-Frame-Options": "SAMEORIGIN",
            "Content-Security-Policy": f"frame-ancestors {_frame_ancestors_sources()}",
        }
        if "text/html" in ctype:
            text = data.decode("utf-8", errors="replace")
            base_tag = f'<base href="{url}">'
            if "<head" in text:
                text = text.replace("<head", f"<head>{base_tag}", 1)
            elif "<HEAD" in text:
                text = text.replace("<HEAD", f"<HEAD>{base_tag}", 1)
            else:
                text = base_tag + text
            return Response(
                content=text,
                media_type="text/html; charset=utf-8",
                headers=proxy_headers,
            )
        return Response(
            content=data, media_type=ctype or "application/octet-stream", headers=proxy_headers
        )
    except HTTPException:
        raise
    except urllib.error.HTTPError as e:
        logger.error(f"Render proxy upstream error: {e.code} {e.reason}")
        raise HTTPException(status_code=502, detail=f"Upstream returned {e.code}.") from e
    except Exception as e:
        logger.error(f"Render proxy error: {e!s}")
        raise HTTPException(status_code=502, detail="Failed to fetch the requested URL.") from e


# ═════════════════════════════════════════════════════════════════════════════
# 🌐 SUPREMEBROWSER ADVANCED COGNITIVE SUITE (L1 — L5)
# ═════════════════════════════════════════════════════════════════════════════


class SemanticClickRequest(BaseModel):
    target: str
    context: str = ""


class SwarmExploreRequest(BaseModel):
    site: str
    sub_goals: list[str]


@router.post("/semantic-click")
async def semantic_click(req: SemanticClickRequest):
    """L4: Click by meaning — matches natural language intent to dynamic DOM embeddings."""
    from browser.semantic_dom import SemanticDOM

    sdom = SemanticDOM(page=None)
    await sdom.build_index()
    el = await sdom.query(req.target)
    return {
        "status": "clicked",
        "matched_text": el.get("text"),
        "xpath": el.get("xpath"),
        "confidence": el.get("semantic_confidence"),
    }


@router.post("/smart-click")
async def smart_click(req: SemanticClickRequest):
    """L4 Cascade: Semantic DOM → Vision Grounding Fallback → HITL Takeover."""
    from browser.semantic_dom import ElementNotFoundSemantically, SemanticDOM
    from browser.vision_grounding import LowConfidenceGrounding, VisionGrounding

    # 1. Semantic DOM
    try:
        sdom = SemanticDOM(page=None)
        await sdom.build_index()
        el = await sdom.query(req.target)
        return {"status": "clicked", "method": "semantic_dom", "element": el}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        import logging

        logging.getLogger(__name__).exception(f"Silenced error: {e}")

    # 2. Vision Grounding
    try:
        vg = VisionGrounding(page=None)
        click_res = await vg.click(req.target)
        return {"status": "clicked", "method": "vision_grounding", "coordinates": click_res}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        import logging

        logging.getLogger(__name__).exception(f"Silenced error: {e}")

    # 3. HITL Takeover Escalation
    return {"status": "escalated_to_hitl", "method": "hitl", "target": req.target}


@router.post("/autonomous/run")
async def run_autonomous_goal(req: GoalRequest):
    """L5: Execute natural language browsing goal with reasoning, replanning, and memory."""
    from browser.autonomous_browser import AutonomousBrowserAgent

    agent = AutonomousBrowserAgent(session=None)
    result = await agent.achieve(req.goal)
    return result


@router.post("/swarm/explore")
async def explore_swarm(req: SwarmExploreRequest):
    """L5+: Deploy parallel agent swarm across web sub-goals and synthesize multi-agent findings."""
    from browser.swarm_browser import SwarmBrowser

    swarm = SwarmBrowser()
    result = await swarm.explore(req.site, req.sub_goals)
    return result
