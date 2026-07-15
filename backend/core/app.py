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
import importlib
import logging
import os
import secrets
import sys
from typing import Any

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from loguru import logger

from core import lifespan, services
from core.admin_routes import router as admin_router
from core.config import settings
from core.messaging.event_bus import ErrorEvent, error_event_bus
from core.observability.observability_middleware import ObservabilityMiddleware
from core.security.api_key_middleware import APIKeyAuthMiddleware
from core.security.auth_middleware import AuthMiddleware
from core.security.honeypot_middleware import HoneypotMiddleware
from core.security.origin_validator import TrustedOriginMiddleware
from middleware.chaos_injector import ChaosInjectorMiddleware
from middleware.idempotency import IdempotencyMiddleware


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
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Tenant-ID", "X-API-Key"],
)

app.add_middleware(TrustedOriginMiddleware)
app.add_middleware(ChaosInjectorMiddleware)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(HoneypotMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(APIKeyAuthMiddleware)


from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
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


app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _safe_include_router(fastapi_app: FastAPI, router_module: str, prefix: str = "") -> None:
    """Lazy-load a router module with strict error handling and fail-fast.

    বাংলা: লেজি রাউটার লোডার — ক্রিটিকাল এরর = sys.exit(1)।
    """
    try:
        module = importlib.import_module(router_module)
        router = getattr(module, "router", None)
        if router:
            fastapi_app.include_router(router, prefix=prefix)
    except ImportError as exc:
        logger.warning(f"Optional router {router_module} not installed/found: {exc}")
        error_event_bus.emit(
            ErrorEvent(
                module="app",
                error_type="ROUTER_NOT_FOUND",
                message=str(exc)[:200],
                severity="WARNING", structured_context=ErrorContext(module="auto_fixed"),
                context={"router_module": router_module},
            )
        )
    except (AttributeError, TypeError) as exc:
        logger.critical(f"Critical error loading router {router_module}: {exc}")
        error_event_bus.emit(
            ErrorEvent(
                module="app",
                error_type="ROUTER_LOAD_FAILED",
                message=str(exc)[:500],
                severity="CRITICAL", structured_context=ErrorContext(module="auto_fixed"),
                context={"router_module": router_module},
            )
        )
        sys.exit(1)


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

# Core Routers
core_routers: list[tuple[str, str]] = [
    ("api.routes.memory", ""),
    ("api.routes.task", ""),
    ("api.routes.markdown", "/api/v1"),
    ("api.routes.simulator", ""),
    ("api.routes.site_actions", ""),
    ("api.routes.llm_gateway", ""),
    ("api.routes.browser", ""),
    ("api.routes.stream", ""),
    ("api.routes.media", ""),
    ("api.routes.graph", ""),
    ("api.routes.knowledge", ""),
    ("api.routes.marketplace_endpoints", ""),
    ("api.routes.auth", "/api/v1"),
    ("api.routes.onboarding", "/api/v1/onboarding"),
    ("api.routes.evolution", "/api/v1/evolution"),
    ("api.routes.admin_dashboard", ""),
    ("api.routes.email", ""),
    ("api.routes.github", ""),
    ("api.routes.internal", ""),
    ("api.routes.config", ""),
    ("api.routes.repos", ""),
    ("api.routes.tools_ops", ""),
    ("api.routes.agents", ""),
    ("api.routes.admin", ""),
    ("api.routes.tools_registry", ""),
    ("api.routes.preferences", ""),
    ("api.routes.usage_metrics", ""),
    ("api.routes.sso", ""),
    ("api.routes.health", ""),
    ("api.routes.api_keys", ""),
    ("api.routes.ci_webhooks", ""),
    ("api.routes.task_workspace", "/api/v1"),
    ("api.routes.websocket_agent", ""),
    ("api.routes.agent_workspace", "/api/v1"),
    ("api.routes.integrations", "/api/v1"),
    ("api.routes.public_config", "/api"),
    ("api.routes.traffic_monitor", ""),
    ("api.routes.swarm", "/api/v1"),
    ("api.routes.agent_action", "/api/v1"),
    ("api.routes.websocket_hitl", ""),
    ("core.orchestrator", ""),
]

for router_path, prefix in core_routers:
    _safe_include_router(app, router_path, prefix)

# Optional / External Tools Routers
optional_routers: list[tuple[str, str]] = [
    ("api.routes.dock_actions", "/api"),
    ("api.routes.websocket_voice", ""),
    ("tools.collaborative_editor", "/api/v1"),
    ("tools.image_to_code", ""),
    ("tools.browser_agent", "/api"),
    ("tools.voice_coder", "/api"),
    ("tools.style_learner", "/api"),
    ("tools.diagram_to_architecture", "/api"),
    ("tools.ai_pair_programmer", "/api"),
    ("api.routes.codeflow", ""),
    ("api.routes.feedback", ""),
    ("tools.media.multilingual_tts", "/api"),
    ("api.routes.voice", "/api/voice"),
    ("tools.comment_thread_ai", "/api"),
    ("tools.auto_test_generator", "/api"),
    ("api.routes.tenant_admin", "/api"),
    ("api.routes.mobile_bff", ""),
    ("api.routes.billing_api", ""),
    ("api.routes.metrics", ""),
    ("api.routes.cloud_mesh", ""),
    ("api.routes.events", "/api"),
    ("api.routes.payments", ""),
    ("api.routes.maintenance", "/api/v1"),
    ("api.routes.sandbox_api", ""),
    ("api.routes.pr_review_api", ""),
]

for router_path, prefix in optional_routers:
    _safe_include_router(app, router_path, prefix)

if settings.encryption_key and settings.encryption_key.get_secret_value():
    _safe_include_router(app, "api.routes.byoc_api", "")
else:
    logger.warning("Universal BYOC router not loaded: ENCRYPTION_KEY missing")

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
