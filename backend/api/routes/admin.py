import json
import secrets
from datetime import UTC
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel

from admin.god import AdminGodLayer  # Your existing god.py
from api.dependencies import get_current_user_token
from core.health.self_healer import SelfHealerService
from core.cache.redis_manager import redis_manager
from utils.firestore_helpers import get_firestore_db


def get_current_admin(payload: dict = Depends(get_current_user_token)) -> dict:
    if payload.get("role") != "admin":
        logger.warning(f"Unauthorized admin access attempt by {payload.get('sub')}")
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload


router = APIRouter(
    prefix="/api/admin",
    tags=["Core Admin"],
    dependencies=[Depends(get_current_admin)],
)
_db_path = str(Path(__file__).resolve().parent.parent.parent / "data" / "admin_rules.db")
god_layer = AdminGodLayer(db_path=_db_path)


def get_healer_service() -> SelfHealerService:
    db = get_firestore_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return SelfHealerService(db)


class RuleUpdate(BaseModel):
    key: str
    value: str


@router.post("/rules")
async def update_constitutional_rule(payload: RuleUpdate, admin_user: dict = Depends(get_current_admin)):
    """Update God.py constitutional rules directly from the Command Center UI"""
    try:
        god_layer.set_rule(payload.key, payload.value)
        logger.critical(f"🔒 Constitutional rule '{payload.key}' changed to '{payload.value}' by {admin_user.get('sub')}")
        return {"status": "success", "message": f"Rule {payload.key} updated to {payload.value}"}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/actions/{action_type}")
async def trigger_quick_action(action_type: str, admin_user: dict = Depends(get_current_admin)):
    """Trigger 1-click Quick Actions from Dashboard"""
    # Verify if admin actions are currently allowed by god.py
    god_layer.enforce("admin_action")
    logger.critical(f"🔒 Admin quick-action '{action_type}' triggered by {admin_user.get('sub')}")

    if action_type == "rollback":
        return {"status": "Rollback initiated"}
    elif action_type == "backup":
        return {"status": "Backup triggered"}
    elif action_type == "cache":
        return {"status": "Redis cache cleared"}
    else:
        raise HTTPException(status_code=404, detail="Action not found")


@router.get("/fixes")
async def get_fixes(
    tenant_id: str = "default",
    status: str = "pending_review",
    admin_user: dict = Depends(get_current_admin),
    healer: SelfHealerService = Depends(get_healer_service),
):
    """Fetch all fixes for a tenant with a specific status."""
    db = get_firestore_db()
    fixes_ref = db.collection("tenants").document(tenant_id).collection("fixes")
    query = fixes_ref.where("status", "==", status)

    try:
        results = await query.get()
    except TypeError:
        # Fallback for sync mock
        results = query.get()

    fixes = []
    for doc in results:
        fix_data = doc.to_dict()
        fix_data["id"] = doc.id
        fixes.append(fix_data)

    return {"fixes": fixes}


@router.post("/fixes/{fix_id}/approve")
async def approve_fix(
    fix_id: str, tenant_id: str = "default", admin_user: dict = Depends(get_current_admin), healer: SelfHealerService = Depends(get_healer_service)
):
    """Approve a pending fix."""
    admin_id = admin_user.get("sub", "unknown_admin")
    logger.info(f"Admin {admin_id} approving fix {fix_id} for tenant {tenant_id}")

    success = await healer.apply_fix(tenant_id, fix_id, admin_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to apply fix. It may not exist or is already processed.")

    return {"status": "success", "fix_id": fix_id}


@router.post("/fixes/{fix_id}/reject")
async def reject_fix(fix_id: str, tenant_id: str = "default", admin_user: dict = Depends(get_current_admin)):
    """Reject a pending fix."""
    admin_id = admin_user.get("sub", "unknown_admin")
    logger.info(f"Admin {admin_id} rejecting fix {fix_id} for tenant {tenant_id}")

    db = get_firestore_db()
    doc_ref = db.collection("tenants").document(tenant_id).collection("fixes").document(fix_id)

    update_data = {"status": "rejected", "reviewed_by": admin_id, "applied_at": datetime.now(UTC).isoformat()}

    try:
        await doc_ref.update(update_data)
    except TypeError:
        doc_ref.update(update_data)

    return {"status": "success", "fix_id": fix_id}


class VerifyOtpRequest(BaseModel):
    code: str


@router.post("/verify-otp")
async def verify_otp(payload: VerifyOtpRequest, admin_user: dict = Depends(get_current_admin)):
    """Validate a JIT OTP issued by AntiHackingContextMiddleware and promote the
    pending (mismatched) context to trusted, so the admin isn't re-challenged
    on their next request from this IP/fingerprint.

    বাংলা: অ্যাডমিন OTP সাবমিট করলে এখানে ভ্যালিডেট হয় এবং সফল হলে Redis-এ
    ট্রাস্টেড কনটেক্সট (last_context) আপডেট হয়ে যায়।
    """
    admin_id = admin_user.get("sub", "unknown_admin")

    if not redis_manager or not redis_manager.client:
        raise HTTPException(status_code=503, detail="Security store unavailable")

    pending_key = f"security:otp_pending:{admin_id}"
    raw_pending = await redis_manager.get_cache(pending_key)
    if not raw_pending:
        raise HTTPException(status_code=400, detail="No pending verification for this admin, or it has expired")

    pending = json.loads(raw_pending)

    if not secrets.compare_digest(str(pending["code"]), str(payload.code)):
        logger.warning(f"❌ Failed OTP verification attempt for admin {admin_id}")
        raise HTTPException(status_code=401, detail="Invalid code")

    # বাংলা: সফল ভেরিফিকেশনে বর্তমান (আগে মিসম্যাচড) সিগন্যালকেই নতুন ট্রাস্টেড কনটেক্সট হিসেবে সেট করা হচ্ছে
    await redis_manager.set_cache(
        f"security:last_context:{admin_id}",
        json.dumps(pending["signal"]),
        ex_seconds=86400,
    )
    await redis_manager.client.delete(pending_key)

    logger.info(f"✅ Admin {admin_id} passed OTP verification — context promoted to trusted")
    return {"status": "verified"}
