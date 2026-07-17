from __future__ import annotations

from core.messaging.event_bus import ErrorContext


"""SupremeAI 2.0 — Core FastAPI app bootstrapping, middleware chain, and router loading.

বাংলা: কোর FastAPI অ্যাপ বুটস্ট্র্যাপিং, মিডলওয়্যার চেইন এবং রাউটার লোডিং।

Key Components:
- InterceptHandler: Routes stdlib logging to Loguru.
- _safe_include_router: Dynamic lazy router loader with fail-fast.
- router_health_check: Ensures minimum route count on startup.
"""

import base64
import logging
import os
import secrets
import sys
from typing import Any

import sentry_sdk
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic
from fastapi.security import HTTPBasicCredentials
from loguru import logger

from api.middleware import ChaosInjectorMiddleware
from api.middleware import IdempotencyMiddleware
from api.middleware import ResponseStandardizationMiddleware
from api.middleware import SupremeContextMiddleware
from api.middleware import TenantExtractionMiddleware
from api.routers import register_all_routers
from core import lifespan
from core import services
from core.admin_routes import router as admin_router
from core.config import settings
from core.messaging.event_bus import ErrorEvent
from core.messaging.event_bus import error_event_bus
from core.observability.observability_middleware import ObservabilityMiddleware
from core.security.api_key_middleware import APIKeyAuthMiddleware
from core.security.auth_middleware import AuthMiddleware
from core.security.honeypot_middleware import HoneypotMiddleware
from core.security.origin_validator import TrustedOriginMiddleware


class InterceptHandler(logging.Handler):
    """Redirect stdlib logging to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

security = HTTPBasic()

if settings.sentry_dsn:
    try:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=0.2 if settings.env.lower() == "production" else 1.0,
            environment=settings.env,
        )
    except Exception:  # noqa: BLE001
        logger.critical("Sentry SDK initialization failed. Configuration error.")
        if os.getenv("ENV", "development").lower() != "test":
            sys.exit(1)


def _docs_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Authenticate docs access via HTTP Basic."""
    correct = secrets.compare_digest(credentials.username, settings.docs_username) and secrets.compare_digest(
        credentials.password, settings.docs_password
    )
    if not correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def _maybe_docs_auth() -> list[Depends]:
    if settings.docs_auth_enabled and not settings.debug:
        return [Depends(_docs_auth)]
    return []


docs_auth_dep = _maybe_docs_auth()

is_prod = settings.env.lower() == "production"
docs_enabled = settings.debug or not is_prod or settings.docs_auth_enabled

tags_metadata = [
    {"name": "admin", "description": "God-mode admin operations."},
    {"name": "agent", "description": "Autonomous agents execution and planning."},
    {"name": "marketplace", "description": "Discover and manage AI skills and tools."},
    {"name": "tools", "description": "Registry and management of integrated tools."},
]

app = FastAPI(
    title=f"{settings.app_name} (Production Ready)",
    description="Multi-cloud AI orchestration platform with zero-cost edge computing.",
    version="2.0.0",
    openapi_tags=tags_metadata,
    debug=settings.debug,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)


@app.middleware("http")
async def basic_auth_for_docs_middleware(request: Request, call_next: Any) -> JSONResponse:  # noqa: ANN401
    """Protect docs with Basic Auth if enabled."""
    if settings.docs_auth_enabled and not settings.debug:
        path = request.url.path
        if path in {"/docs", "/redoc", "/openapi.json"}:
            auth = request.headers.get("Authorization")
            if not auth or not auth.startswith("Basic "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid credentials"},
                    headers={"WWW-Authenticate": "Basic"},
                )
            try:
                decoded = base64.b64decode(auth[6:]).decode("utf-8")
                username, password = decoded.split(":", 1)
                if username != settings.docs_username or password != settings.docs_password:
                    raise ValueError("Mismatch")
            except (ValueError, UnicodeDecodeError):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid credentials"},
                    headers={"WWW-Authenticate": "Basic"},
                )
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Tenant-ID", "X-API-Key", "X-Correlation-ID"],
)

# SupremeContextMiddleware - must be first to capture all requests
app.add_middleware(SupremeContextMiddleware)
app.add_middleware(TrustedOriginMiddleware)
app.add_middleware(ChaosInjectorMiddleware)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(HoneypotMiddleware)
app.add_middleware(AuthMiddleware)
# TenantExtractionMiddleware enriches request.state.tenant_id after auth so downstream
# handlers and dependencies can rely on it without re-deriving context from JWT.
app.add_middleware(TenantExtractionMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(APIKeyAuthMiddleware)
# ResponseStandardizationMiddleware normalizes non-JSON error responses into the
# standard envelope as the last middleware in the chain.
app.add_middleware(ResponseStandardizationMiddleware)


# বাংলা মন্তব্য: slowapi টেস্টে মক করা হলেও RateLimitExceeded যেন সত্যিকারের Exception ক্লাস থাকে
# তা নিশ্চিত করা হলো। MagicMock দিয়ে issubclass() ডাকলে TypeError হয়।
try:
    from slowapi import Limiter
    from slowapi import _rate_limit_exceeded_handler as _slowapi_rate_limit_handler
    from slowapi.errors import RateLimitExceeded as _SlowAPIRateLimitExceeded
    from slowapi.util import get_remote_address as _slowapi_get_remote_address

    # মক হলে fallback ক্লাস ব্যবহার করো
    if not isinstance(_SlowAPIRateLimitExceeded, type) or not issubclass(_SlowAPIRateLimitExceeded, Exception):
        class RateLimitExceeded(Exception):  # type: ignore[no-redef]
            """Fallback RateLimitExceeded for test environments where slowapi is mocked."""

        def _rate_limit_exceeded_handler(request: Any, exc: Any) -> JSONResponse:  # type: ignore[misc]
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

        def get_remote_address(request: Any) -> str:  # type: ignore[misc]
            return request.client.host if request.client else "127.0.0.1"

        limiter = None
    else:
        RateLimitExceeded = _SlowAPIRateLimitExceeded  # type: ignore[misc,assignment]
        _rate_limit_exceeded_handler = _slowapi_rate_limit_handler
        get_remote_address = _slowapi_get_remote_address
        limiter = Limiter(key_func=get_remote_address)
except Exception:  # noqa: BLE001
    # বাংলা মন্তব্য: slowapi ইম্পোর্ট সম্পূর্ণ ব্যর্থ হলে fallback
    class RateLimitExceeded(Exception):  # type: ignore[no-redef]
        """Fallback RateLimitExceeded for test environments."""

    def _rate_limit_exceeded_handler(request: Any, exc: Any) -> JSONResponse:  # type: ignore[misc]
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    limiter = None

app.state.limiter = limiter


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "title": "Task Execution Failed",
            "detail": exc.detail,
            "instance": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler — never returns 500 detail to client in production."""
    logger.error(f"Unhandled Exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "title": "Internal Server Error",
            "detail": "An unexpected error occurred. This has been logged.",
            "instance": request.url.path,
        },
    )


# বাংলা মন্তব্য: শুধুমাত্র তখনই হ্যান্ডলার রেজিস্টার করো যখন RateLimitExceeded সত্যিকারের class
if isinstance(RateLimitExceeded, type) and issubclass(RateLimitExceeded, Exception):
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint — API info and health summary.

    বাংলা: রুট এন্ডপয়েন্ট — API তথ্য এবং সার্ভার স্ট্যাটাস।
    """
    return {
        "name": settings.app_name,
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs",
        "health": "/api/v1/health",
        "description": "Multi-cloud AI orchestration platform.",
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    """Comprehensive health check — Redis + API key status."""
    redis_ok = False
    if hasattr(services, "redis_queue") and services.redis_queue.configured:
        try:
            services.redis_queue.set("health", "ok", ex=5)
            redis_ok = services.redis_queue.get("health") == "ok"
        except Exception:  # noqa: BLE001
            logger.exception("Health check failed on redis connection")
            error_event_bus.emit(
                ErrorEvent(module="app.health", error_type="REDIS_HEALTH_FAIL", message="Redis health error", severity="ERROR", structured_context=ErrorContext(module="auto_fixed"))
            )
            redis_ok = False
    else:
        redis_ok = True

    api_keys_ok = bool(
        settings.openrouter_api_key
        or settings.gemini_api_key
        or settings.deepseek_api_key
        or settings.groq_api_key
        or settings.nvidia_api_key
    )
    checks = {"redis": redis_ok, "api_keys_configured": api_keys_ok}
    all_ok = all(checks.values())
    return {"status": "ok" if all_ok else "degraded", "orchestrator": "online", "checks": checks}


@app.get("/actuator/health")
def actuator_health() -> dict[str, str]:
    return {"status": "UP", "orchestrator": "online"}


app.include_router(admin_router)

register_all_routers(app)

app.router.lifespan_context = lifespan.app_lifespan


def router_health_check(fastapi_app: FastAPI) -> None:
    """Fail-fast if fewer than minimum routes loaded."""
    expected_count = int(os.getenv("MIN_EXPECTED_ROUTES", "20"))
    if len(fastapi_app.routes) < expected_count:
        logger.critical(
            f"🔥 CRITICAL: Only {len(fastapi_app.routes)} routes loaded. "
            f"Expected at least {expected_count}. Some routers failed to load!"
        )
        sys.exit(1)


router_health_check(app)
