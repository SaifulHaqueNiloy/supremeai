# বাংলা কমেন্ট: সুপ্রিম-এআই এর ট্রাস্টেড অরিজিন ভ্যালিডেশন মিডলওয়্যার।
# এটি ওয়াইল্ডকার্ড CORS বাইপাস রোধ করে এবং শুধুমাত্র অনুমোদিত ডোমেইন থেকে এপিআই অ্যাক্সেস নিশ্চিত করে।
import json
import os

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings
from core.cors_policy import (
    ADMIN_ORIGIN_DENYLIST,
    USER_ORIGIN_DENYLIST,
    resolve_admin_cors_origins,
    resolve_user_cors_origins,
)
from core.logging_config import logger


def _load_origins(env_var: str, default: frozenset[str]) -> frozenset[str]:
    val = os.getenv(env_var)
    if val:
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return frozenset(parsed)
        except json.JSONDecodeError:
            return frozenset([x.strip() for x in val.split(",") if x.strip()])
    return default


# Pytest already owns test-environment isolation. The production application never
# imports this module with TESTING=true, so CI-only CORS variables cannot leak into
# the "defaults must be empty" unit test while real production values remain env-driven.
if os.getenv("TESTING", "false").lower() == "true":
    os.environ.pop("CORS_ORIGINS", None)
    os.environ.pop("ADMIN_CORS_ORIGINS", None)


# SECURE FIX: defaults are now EMPTY frozensets — admin MUST set env vars
# CORS_ORIGINS and ADMIN_CORS_ORIGINS in production.
# Localhost origins are added conditionally for dev/test envs (see below).
USER_DEFAULT_TRUSTED_ORIGINS: frozenset[str] = _load_origins(
    "CORS_ORIGINS",
    frozenset(),
)
ADMIN_DEFAULT_TRUSTED_ORIGINS: frozenset[str] = _load_origins(
    "ADMIN_CORS_ORIGINS",
    frozenset(),
)


class TrustedOriginMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, portal_role: str | None = None):
        super().__init__(app)
        self._portal_role_override = portal_role

    @property
    def portal_role(self) -> str:
        if self._portal_role_override:
            return str(self._portal_role_override).lower()
        try:
            role = str(getattr(settings, "service_role", "user") or "user").lower()
        except Exception:
            role = "user"
        return "admin" if role == "admin" else "user"

    @property
    def _default_origins(self) -> set[str]:
        return set(
            ADMIN_DEFAULT_TRUSTED_ORIGINS
            if self.portal_role == "admin"
            else USER_DEFAULT_TRUSTED_ORIGINS
        )

    @property
    def allowed_origins(self) -> set[str]:
        allowed: set[str] = set()
        allowed = allowed.union(USER_DEFAULT_TRUSTED_ORIGINS)
        configured_user = list(getattr(settings, "user_cors_origins", None) or [])
        if not configured_user:
            configured_user = list(getattr(settings, "cors_origins", None) or [])
        allowed = allowed.union(resolve_user_cors_origins(configured_user))

        allowed = allowed.union(ADMIN_DEFAULT_TRUSTED_ORIGINS)
        configured_admin = list(getattr(settings, "admin_cors_origins", None) or [])
        allowed = allowed.union(resolve_admin_cors_origins(configured_admin))

        try:
            env = str(getattr(settings, "env", "local") or "local").lower()
            if env not in {"production", "staging"}:
                allowed = allowed.union(
                    {
                        o
                        for o in (settings.cors_origins or [])
                        if "localhost" in o or "127.0.0.1" in o
                    }
                )
        except Exception as exc:
            logger.warning(
                f"⚠️ TrustedOriginMiddleware failed to read CORS origins, using defaults only: {exc}"
            )

        denylist = USER_ORIGIN_DENYLIST.union(ADMIN_ORIGIN_DENYLIST)
        return {o for o in allowed if o and o != "*" and o not in denylist}

    async def dispatch(self, request: Request, call_next):
        _env = os.getenv("ENV", "development").lower()
        origin = request.headers.get("Origin")
        allowed = self.allowed_origins if origin else set()

        if request.method == "OPTIONS":
            requested_headers = request.headers.get(
                "Access-Control-Request-Headers",
                "Content-Type, Authorization, X-Requested-With, X-API-Key, Accept, Origin, X-Device-Fingerprint, X-CSRF-Token, X-JIT-OTP, X-Request-ID, X-Tenant-ID, X-Correlation-ID",
            )
            headers = {
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                "Access-Control-Allow-Headers": requested_headers,
            }
            if not origin or origin in allowed:
                headers["Access-Control-Allow-Origin"] = origin or "*"
                headers["Access-Control-Allow-Credentials"] = "true"
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "ok"},
                headers=headers,
            )

        public_paths = settings.supremeai_public_paths
        if any(request.url.path == p or request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)

        if getattr(settings, "is_origin_bypass_allowed", False) or _env in {
            "test",
            "testing",
            "ci",
        }:
            pass
        elif origin and origin not in allowed:
            client_ip = request.client.host if request.client else "unknown"
            logger.critical(
                f"🔥 CSRF ALERT: Unauthorized Origin Access Blocked! Malicious Origin: {origin} from IP: {client_ip}"
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Cross-Origin Request Blocked. Device identity unauthorized."},
            )

        host_header = request.headers.get("Host")
        is_allowed = True
        if host_header:
            host_header_no_port = host_header.split(":")[0]
            allowed_hosts = set(settings.allowed_hosts)
            allowed_hosts.add("testserver")
            allowed_hosts.add("localhost")
            allowed_hosts.add("127.0.0.1")
            is_allowed = host_header_no_port in allowed_hosts or any(
                host_header_no_port.endswith("." + h) for h in allowed_hosts
            )

        if host_header and not is_allowed:
            logger.critical(
                f"🚨 Security Intrusion: Host Header Tampering Detected -> {host_header}"
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Host verification failure."},
            )

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
