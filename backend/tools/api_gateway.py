import asyncio
import ipaddress
import os
import socket
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.dependencies import get_current_user_token
from core.automation.dispatcher import automation_dispatcher
from core.automation.models import AutomationEvent, ExecutionEnvelope
from core.config import settings
from core.logging_config import logger
from core.rate_limiter import AsyncRateLimiter
from core.security.authentication.auth_middleware import AuthMiddleware

auth_middleware = AuthMiddleware.__new__(AuthMiddleware)
auth_middleware.enabled = bool(getattr(settings, "supremeai_api_token", None))
rate_limiter = AsyncRateLimiter()

from brain.api_router import ApiRouter

api_router = ApiRouter()
router = APIRouter(prefix="/api/v1/gateway", tags=["gateway"])


class GatewayRequest(BaseModel):
    path: str
    method: str = "GET"
    payload: dict[str, Any] | None = None
    source: str | None = None  # 'vscode' | 'flutter' | 'telegram' | 'web'
    headers: dict[str, str] | None = None


class InternalGateway:
    def __init__(self) -> None:
        self.webhook_allowlist = {
            host.strip().lower()
            for host in (os.getenv("MAKE_WEBHOOK_ALLOWLIST") or "").split(",")
            if host.strip()
        }

    @staticmethod
    def _validate_webhook_url(webhook_url: str, allowlist: set[str]) -> None:
        parsed = urlparse(webhook_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.port not in (None, 443):
            raise ValueError("webhook URL must use HTTPS on the default port")
        hostname = parsed.hostname.lower().rstrip(".")
        if allowlist and hostname not in allowlist:
            raise ValueError("webhook host is not allowlisted")
        if not allowlist:
            raise ValueError("webhook allowlist is not configured")
        try:
            addresses = {ipaddress.ip_address(info[4][0]) for info in socket.getaddrinfo(hostname, 443)}
        except socket.gaierror as exc:
            raise ValueError("webhook host could not be resolved") from exc
        if any(address.is_private or address.is_loopback or address.is_link_local or address.is_reserved for address in addresses):
            raise ValueError("webhook host resolves to a private or reserved address")

    async def trigger_make_webhook(self, webhook_url: str, payload: dict[str, Any]) -> dict[str, Any]:
        logger.info("Triggering Make.com webhook")
        try:
            self._validate_webhook_url(webhook_url, self.webhook_allowlist)
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                response = await client.post(webhook_url, json=payload)
            return {"success": response.is_success, "status_code": response.status_code}
        except (httpx.HTTPError, ValueError, OSError):
            logger.exception("Make.com webhook request failed")
            return {"success": False, "error": "webhook request failed"}


APIGateway = InternalGateway
ALLOWED_BACKEND_PATHS = {
    "vscode": [
        "/api/chat/completion",
        "/api/chat/stream",
        "/api/knowledge/learn",
        "/api/memory/ingest",
        "/api/codeflow/analyze",
    ],
    "flutter": ["/api/chat/message", "/api/chat/history", "/api/knowledge/stats"],
    "telegram": ["/api/chat/message", "/api/knowledge/feedback"],
    "web": ["/api/chat/message", "/api/chat/stream"],
}


@router.post("/forward")
async def gateway_forward(
    request: GatewayRequest,
    http_request: Request,
    user: dict[str, Any] = Depends(get_current_user_token),
) -> Response:
    source = (request.source or "web").lower()
    if source not in ALLOWED_BACKEND_PATHS:
        raise HTTPException(status_code=400, detail="unknown source")

    allowed = ALLOWED_BACKEND_PATHS.get(source, [])
    normalized = request.path.strip().lower()
    if not any(
        normalized == allowed_path.lower() or normalized.startswith(allowed_path.lower() + "/")
        for allowed_path in allowed
    ):
        logger.warning(f"Blocked path for source={source}: {request.path}")
        raise HTTPException(status_code=403, detail="path not allowed for source")

    client_ip = http_request.client.host if http_request.client else "unknown"
    tenant_id = str(user.get("tenant_id") or user.get("org_id") or "").strip()
    actor_id = str(user.get("sub") or user.get("user_id") or user.get("email") or "").strip()
    if not tenant_id or not actor_id:
        raise HTTPException(status_code=403, detail="Verified tenant and actor context required")
    rate_limit_key = f"{tenant_id}:{actor_id}:{client_ip}"
    if not rate_limiter.check(rate_limit_key):
        raise HTTPException(status_code=429, detail="rate limit exceeded")

    # ✅ SAFE: Environment-aware backend URL resolution
    backend_url = os.environ.get("SUPREMEAI_BACKEND_URL") or os.environ.get("BACKEND_URL")

    if not backend_url:
        try:
            backend_url = settings.auto_backend_url
        except asyncio.CancelledError:
            raise
        except Exception as e:
            import logging

            logging.getLogger(__name__).exception(f"Silenced error: {e}")

    if not backend_url:
        current_env = getattr(settings, "env", "local") or "local"
        is_local = current_env.lower() in ("local", "development", "dev", "test")
        if is_local:
            backend_url = "http://127.0.0.1:8000/api/v1"  # is_local()
            logger.warning("[gateway] Using localhost backend (dev mode)")
        else:
            raise HTTPException(status_code=500, detail="Backend URL not configured for production")

    target = backend_url.rstrip("/") + "/" + request.path.lstrip("/")

    tenant_id = str(user.get("tenant_id") or user.get("org_id") or "").strip()
    actor_id = str(user.get("sub") or user.get("user_id") or user.get("email") or "").strip()
    if not tenant_id or not actor_id:
        raise HTTPException(status_code=403, detail="Verified tenant and actor context required")

    envelope = ExecutionEnvelope(
        actor_id=actor_id,
        tenant_id=tenant_id,
        intent=f"gateway:{source}:{request.method.upper()}:{normalized}",
        policy_decision="approved",
        status="forwarding",
        trace_id=getattr(http_request.state, "correlation_id", None),
    )
    allowed_headers = {"accept", "content-type", "user-agent"}
    headers = {key: value for key, value in (request.headers or {}).items() if key.lower() in allowed_headers}
    headers["X-Source"] = source
    headers["X-Execution-ID"] = envelope.execution_id
    headers["X-Actor-ID"] = envelope.actor_id
    headers["X-Trace-ID"] = envelope.trace_id or envelope.execution_id

    # Provider selection is kept server-side; provider credentials must never
    # cross this boundary as client-controlled or forwarded HTTP headers.
    if any(
        endpoint in normalized for endpoint in ["chat/completion", "chat/stream", "chat/message"]
    ):
        try:
            from core.llm.free_tier_tracker import get_tracker
            from tools.security_tools.multi_account_rotator import TaskType, get_rotator

            tracker = get_tracker()
            rotator = get_rotator()

            best_provider_name = tracker.get_best_provider()
            if best_provider_name:
                # Tell rotator to get an account (task=CHAT)
                provider_account = rotator.get_best_provider_for_task(TaskType.CHAT)
                if provider_account:
                    provider, account = provider_account
                    if account and account.api_key:
                        headers["X-Dynamic-Provider"] = provider.name
                        # Never forward account.api_key to another HTTP service.
                        # The downstream provider boundary owns credential injection.
                        # Record a basic hit (backend should ideally report exact tokens later)
                        tracker.record(provider.name, token_count=100)
                        logger.info(f"Injected {provider.name} key from rotator for {normalized}")
        except Exception as e:
            logger.warning(f"Failed to inject dynamic API key: {e}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            req_method = (request.method or "GET").upper()
            if req_method == "POST":
                response = await client.post(target, json=request.payload or {}, headers=headers)
            elif req_method == "GET":
                response = await client.get(target, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="method not allowed")

            # If rate limited (429), pause the provider
            if response.status_code == 429 and "X-Dynamic-Provider" in headers:
                try:
                    failed_provider = headers["X-Dynamic-Provider"]
                    tracker.mark_rate_limited(failed_provider, pause_seconds=60)
                    logger.warning(f"Provider {failed_provider} hit 429, paused for 60s.")
                except Exception as e:
                    try:
                        import loguru

                        loguru.logger.error(f"Tool execution error: {e}")
                    except Exception as e:
                        logger.warning(f"Exception suppressed: {e}")
                    pass

        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("gateway forward failed")
        raise HTTPException(status_code=502, detail="gateway request failed") from exc


@router.post("/dispatch/{capability}")
async def api_dispatch(
    capability: str,
    payload: dict[str, Any],
    user: dict[str, Any] = Depends(get_current_user_token),
) -> JSONResponse:
    tenant_id = str(user.get("tenant_id") or user.get("org_id") or "").strip()
    actor_id = str(user.get("sub") or user.get("user_id") or "").strip()
    if not tenant_id or not actor_id:
        raise HTTPException(status_code=403, detail="verified tenant and actor context required")
    dispatch_payload = {**(payload or {}), "_tenant_id": tenant_id, "_actor_id": actor_id}
    try:
        result = api_router.dispatch(capability, dispatch_payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    status = 200 if result.get("success", True) else 502
    return JSONResponse(content=result, status_code=status)


@router.post("/automation")
async def trigger_automation(
    workflow_key: str,
    payload: dict[str, Any] | None = None,
    user: dict[str, Any] = Depends(get_current_user_token),
) -> JSONResponse:
    tenant_id = str(user.get("tenant_id") or user.get("org_id") or "").strip()
    actor_id = str(user.get("sub") or user.get("user_id") or user.get("email") or "").strip()
    if not tenant_id or not actor_id:
        raise HTTPException(status_code=403, detail="verified tenant and actor context required")
    if payload is None:
        payload = {}

    event = AutomationEvent(workflow_key=workflow_key, payload=payload)

    result = await automation_dispatcher.dispatch(event)

    status_code = 200 if result.status != "failed" else 502
    return JSONResponse(
        content={
            "success": result.status != "failed",
            "status": result.status,
            "provider": result.provider,
            "message": result.message,
            "execution_id": result.execution_id,
        },
        status_code=status_code,
    )


@router.post("/make")
async def trigger_make(
    webhook_url: str = "",
    payload: dict[str, Any] | None = None,
    user: dict[str, Any] = Depends(get_current_user_token),
) -> JSONResponse:
    if not user.get("tenant_id") and not user.get("org_id"):
        raise HTTPException(status_code=403, detail="verified tenant context required")
    if payload is None:
        payload = {}
    internal = InternalGateway()
    result = await internal.trigger_make_webhook(webhook_url, payload)
    status = 200 if result.get("success") else 502
    return JSONResponse(content=result, status_code=status)
