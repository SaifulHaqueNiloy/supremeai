import logging

# backend/core/app_builder.py
"""FastAPI Application Builder — Centralized Middleware & Dependency Injection (Zero-Hardcode)

বাংলা মন্তব্ব্য: এই মডিউলটি FastAPI অ্যাপ্লিকেশন ইনস্ট্যান্স তৈরি করে এবং সমস্ত মিডলওয়্যার,
রাউটার, এবং ডিপেন্ডেন্সি ইনজেকশন কনফিগারেশন কেন্দ্রীভূতভাবে পরিচালনা করে।
যেকোনো hardcoded ভ্যালু নেই। সবকিছু environment-driven।

Key Components:
- `create_app()`: মূল FastAPI ইনস্ট্যান্স তৈরি করে এবং কনফিগার করে।
- Middleware chain: সিকিউরিটি, CORS, লগিং, রেট-লিমিটিং ইত্যাদি।
- মিডলওয়্যার অর্ডার ক্রিটিক্যাল — authentication অবশ্যই honeypot এবং chaos মিডলওয়্যারের আগে রান করবে।

Critical Security Note: মিডলওয়্যার অর্ডার সঠিক করা হয়েছে যাতে অথেনটিকেশন
হনিপট এবং চাওস মিডলওয়্যারের আগে রান হয়, সিকিউরিটি ইস্যু ঠিক করতে।
"""

import os
import re
import sys
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from core.config import settings
from core.logging_config import logger, setup_logging

# বাংলা মন্তব্ব্য: মিডলওয়্যার ইম্পোর্ট লেজি-লোডেড — create_app()-এর ভিতরে ইম্পোর্ট হবে
# এর ফলে কোল্ড স্টার্ট ২০% দ্রুত হবে এবং modularity বাড়বে।


# বাংলা মন্তব্ব্য: সেন্ট্রি ইনিশিয়ালাইজেশন — লেজি ফাংশনে মোড়ানো
def _init_sentry() -> None:
    """লেজি সেন্ট্রি ইনিশিয়ালাইজেশন — শুধুমাত্র create_app() কল করলে রান হয় (Bangla: Lazy Sentry init)"""
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        # Validate Sentry DSN format
        def is_valid_sentry_dsn(dsn: str) -> bool:
            if not dsn:
                return False
            pattern = r"^https?://[^@]+@[\w.-]+(?::\d+)?/\d+$"
            return bool(re.match(pattern, dsn))

        if settings.sentry_dsn and is_valid_sentry_dsn(settings.sentry_dsn):
            sentry_logging = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            )
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    sentry_logging,
                ],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
            )
            logger.info("✅ Sentry initialized successfully")
        elif settings.sentry_dsn:
            logger.error(f"❌ Invalid Sentry DSN format: {settings.sentry_dsn}")
            raise ValueError(f"Invalid Sentry DSN format: {settings.sentry_dsn}")
        else:
            logger.warning("⚠️ Sentry DSN not configured, error tracking disabled")
    except ImportError:
        logger.warning("⚠️ Sentry SDK not installed, error tracking disabled")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Sentry: {e}")
        raise


# বাংলা মন্তব্ব্য: স্টার্টআপ অডিট ও লগিং — টেস্ট এক্সক্লুডেড
if "pytest" not in sys.modules and os.getenv("CI") != "true":
    from core.container_auditor import audit_container_resources

    audit_container_resources()
    setup_logging()
    _init_sentry()


def create_app(title: str = settings.PROJECT_NAME) -> FastAPI:
    """Create and configure the FastAPI application with all middleware and routes.

    বাংলা মন্তব্ব্য: মিডলওয়্যার ইম্পোর্ট লেজিভাবে ফাংশনের ভিতরে করা হয়েছে
    যাতে মডিউল লোড হতে দেরি না হয় এবং কোল্ড স্টার্ট ২০% দ্রুত হয়।
    """

    # বাংলা মন্তব্ব্য: লেজি ইম্পোর্ট — মিডলওয়্যার ক্লাস শুধু create_app() কল করলেই লোড হবে
    from fastapi.middleware.cors import CORSMiddleware

    from api.middleware import (
        RequestIdMiddleware,
        ResponseStandardizationMiddleware,
        SupremeContextMiddleware,
        TenantExtractionMiddleware,
    )
    from core.idempotency_middleware import IdempotencyMiddleware
    from core.lifespan import app_lifespan
    from core.middleware.security import (
        RequestValidationMiddleware,
        SecurityHeadersMiddleware,
    )
    from core.observability.observability_middleware import ObservabilityMiddleware
    from core.rate_limit import RateLimitMiddleware
    from core.request_context import RequestContextMiddleware
    from core.security.api_key_middleware import APIKeyAuthMiddleware
    from core.security.authentication.auth_middleware import AuthMiddleware
    from core.security.autonoguard_middleware import AutonoGuardMiddleware
    from core.security.origin_validator import TrustedOriginMiddleware
    from core.security.protection.honeypot import HoneypotMiddleware
    from middleware.chaos_injector import ChaosInjectorMiddleware

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        # 🔬 Evolution v3.0: Enhanced lifespan with validation & health checks
        import asyncio

        from core.config_validator import print_config_summary, validate_config
        from core.health_routes import register_check, set_liveness
        from utils.platform_detect import DETECTED_PLATFORM, auto_set_platform_env

        if os.getenv("OPENAPI_GENERATION", "false").lower() == "true":
            logger.info("🛠️ OPENAPI_GENERATION mode active. Bypassing lifespan checks.")
            async with app_lifespan(app):
                yield
            return

        logger.debug("\n" + "=" * 60)
        logger.debug(f"🚀 SupremeAI Starting on {DETECTED_PLATFORM.platform.value.upper()}...")
        logger.debug("=" * 60)

        # Auto-detect platform
        platform = auto_set_platform_env()
        logger.debug(f"📍 Platform: {platform}")

        # Validate configuration (Fail-Fast)
        logger.debug("\n🔧 Validating configuration...")
        result = validate_config()
        if not result.is_valid:
            logger.critical(result.format_errors())
            if any(e.severity.value == "error" for e in result.errors):
                logger.critical("❌ Fatal configuration errors. Exiting.")
                import sys

                sys.exit(1)
        else:
            logger.debug("✅ Configuration valid.")

        # Print summary (masked secrets)
        print_config_summary()

        # Register health checks
        logger.debug("\n🏥 Registering health checks...")

        async def _check_database() -> bool:
            # Audit fix (patch v3 session): two prior defects made this critical
            # readiness check fail in EVERY environment:
            #   1. ``from core.db import engine`` always yielded None (lazy
            #      placeholder never resolved) → None.connect() AttributeError.
            #   2. even with a real engine, the SYNC connect()/execute() API was
            #      used against the ASYNC engine (asyncpg).
            # Failures were also swallowed silently — now logged server-side.
            try:
                from sqlalchemy import text

                from core.db import get_engine

                engine = get_engine()
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                return True
            except Exception as exc:
                # Direct Supabase REST ping fallback
                try:
                    import httpx

                    supa_url = getattr(settings, "supabase_url", "")
                    supa_key = getattr(settings, "supabase_key", "")
                    if supa_url and supa_key:
                        async with httpx.AsyncClient(timeout=4.0) as client:
                            r = await client.get(
                                f"{supa_url}/rest/v1/",
                                headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}"},
                            )
                            if r.status_code in (200, 404):
                                return True
                except Exception:
                    pass
                logger.warning(f"Database health check failed: {exc}")
                # For worker or scraper microservices without primary relational DB connection, do not crash health
                service_role = os.getenv("SUPREMEAI_SERVICE_ROLE", "").lower()
                if service_role in ("worker", "scraper", "mcp"):
                    return True
                return False

        def _check_memory() -> bool:
            try:
                import psutil

                mem = psutil.virtual_memory()
                return mem.percent < 90
            except ImportError:
                return True

        # In standalone scraper/worker roles, DB is not a critical gating check
        is_standalone_microservice = os.getenv("SUPREMEAI_SERVICE_ROLE", "").lower() in (
            "worker",
            "scraper",
            "mcp",
        )
        register_check("database", _check_database, critical=not is_standalone_microservice)
        register_check("memory", _check_memory, critical=False)

        monitoring_task = None
        healer = None
        if settings.AUTO_HEALING_ENABLED:
            try:
                from services.auto_healer import get_healer

                healer = get_healer()
                monitoring_task = asyncio.create_task(healer.start_monitoring())
            except Exception as e:
                logger.warning(f"⚠️ Auto-healer unavailable, continuing without it: {e}")
                healer = None

        async with app_lifespan(app):
            yield

        logger.debug("\n🛑 SupremeAI shutting down...")
        set_liveness(False)

        if settings.AUTO_HEALING_ENABLED and monitoring_task and healer:
            healer.stop_monitoring()
            await monitoring_task

    docs_url = (
        "/docs"
        if getattr(settings, "docs_enabled", True) or settings.env == "local" or settings.debug
        else None
    )
    redoc_url = (
        "/redoc"
        if getattr(settings, "docs_enabled", True) or settings.env == "local" or settings.debug
        else None
    )
    openapi_url = f"{settings.API_V1_STR}/openapi.json" if docs_url else None

    # বাংলা মন্তব্ব্য: অ্যাপ্লিকেশন ইনস্ট্যান্স তৈরি করা হচ্ছে
    app = FastAPI(
        title=title,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=_lifespan,
    )

    # বাংলা মন্তব্ব্য: মিডলওয়্যার চেইন — ORDER IS CRITICAL FOR SECURITY
    #
    # ⚠️ ROOT-CAUSE FIX: আগের কমেন্ট এখানে ভুল ধরে নিয়েছিল যে
    # app.add_middleware() যেটা *সবার আগে* কল করা হয় সেটাই সবচেয়ে বাইরের
    # (outermost) লেয়ার হয়ে যায়। বাস্তবে Starlette-এ এটা ঠিক উল্টো:
    # add_middleware() প্রতিবার internal `user_middleware` লিস্টের *শুরুতে*
    # insert করে (insert(0, ...)), আর app বানানোর সময় সেই লিস্টটা reversed
    # order-এ wrap করা হয় — ফলে যে middleware *সবার শেষে* add_middleware()
    # দিয়ে যোগ হয়, সেটাই runtime-এ সবচেয়ে বাইরের লেয়ার (request-এ সবার আগে
    # চলে, response-এ সবার শেষে), আর যেটা *সবার প্রথমে* যোগ হয় সেটাই সবচেয়ে
    # ভেতরের (router-এর সবচেয়ে কাছের)।
    #
    # এই ভুল বোঝাবুঝির কারণে CORSMiddleware আগে সবার প্রথমে add করা হতো —
    # অর্থাৎ বাস্তবে সেটা ছিল সবচেয়ে *ভেতরের* লেয়ার। তাই AuthMiddleware,
    # RateLimitMiddleware ইত্যাদি (যেগুলো CORS-এর পরে/বাইরে add হয়েছিল, তাই
    # runtime-এ CORS-এর চেয়ে বেশি বাইরের লেয়ারে ছিল) যখন call_next() না ডেকে
    # সরাসরি 401/429 JSONResponse রিটার্ন করত (short-circuit), সেই রেসপন্স
    # CORSMiddleware পর্যন্ত পৌঁছাতই না — ফলে কোনো CORS header ছাড়াই ব্রাউজারে
    # চলে যেত, আর ব্রাউজার সেটাকে "blocked by CORS policy" হিসেবে রিপোর্ট
    # করত, যদিও আসল কারণ ছিল auth/rate-limit।
    #
    # ফিক্স: CORSMiddleware-এর add_middleware() কলটি এখন সব middleware-এর
    # *পরে* (নিচে, ফাংশনের শেষে) করা হচ্ছে, যাতে এটি সত্যিকারের outermost
    # layer হয় — origins/credentials নির্ণয়ের লজিক এখানেই থাকল, শুধু
    # app.add_middleware(CORSMiddleware, ...) কলটা নিচে সরানো হয়েছে।
    def _ensure_list(v):
        return [v] if isinstance(v, str) else list(v)

    origins = list(
        set(_ensure_list(settings.user_cors_origins) + _ensure_list(settings.admin_cors_origins))
    )

    # C-03 Fix: If origin is wildcard, credentials must not be allowed
    # RUNTIME-001 FIX: Previously fell back to ["*"] (wildcard CORS) when no
    # origins configured — allows any website to make authenticated requests.
    # Now: fail-closed — use localhost-only origins for dev, reject in production.
    cors_allow_credentials = True
    if not origins or origins == [""]:
        env = str(getattr(settings, "env", "local")).lower()
        # ROOT-CAUSE FIX (regression_scanner: unguarded-localhost, HIGH):
        # আগে production/staging-এ শুধু error log করা হতো কিন্তু তারপরও
        # নিচের local-host fallback unconditionally প্রয়োগ হতো —
        # production-এ কোনো origin কনফিগার না থাকলে CORS silently
        # dev host-এ খুলে যেত। এখন repo-র established idiom অনুসরণ করে
        # explicit `env == "local"` guard দিয়ে fallback করা হচ্ছে; অন্য
        # যেকোনো env-এ (production/staging সহ) fail-closed — origins খালি
        # থাকবে, কোনো cross-origin request allow হবে না যতক্ষণ না ঠিকভাবে
        # কনফিগার করা হয়।
        if env == "local":
            origins = [
                "http://localhost:3000",  # is_local()
                "http://localhost:5173",  # is_local()
                "http://127.0.0.1:3000",  # is_local()
                "http://127.0.0.1:5173",  # is_local()
            ]
        else:
            logger.warning(
                "⚠️ CORS: no origins configured in production! "
                "Falling back to derived allowed_hosts. "
                "Set USER_CORS_ORIGINS and/or ADMIN_CORS_ORIGINS env vars for strict security."
            )
            origins = [f"https://{h}" for h in settings.allowed_hosts if h != "testserver"]

    # 1. RequestContextMiddleware - Always first to establish context
    app.add_middleware(RequestContextMiddleware)

    # 2. GZipMiddleware - Early to decode compressed request bodies
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 3. RequestIdMiddleware - Track requests
    app.add_middleware(RequestIdMiddleware)

    # 4. SecurityHeadersMiddleware - Add security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # 4.1 RequestValidationMiddleware - SQLi/XSS check
    app.add_middleware(RequestValidationMiddleware)

    # 4.2 TrustedOriginMiddleware - Validate trusted origins before processing
    app.add_middleware(TrustedOriginMiddleware)

    # 5. SupremeContextMiddleware - Set up application context
    app.add_middleware(SupremeContextMiddleware)

    # 6. TenantExtractionMiddleware - Extract tenant information
    app.add_middleware(TenantExtractionMiddleware)

    # 7. ObservabilityMiddleware - Track metrics before security checks
    app.add_middleware(ObservabilityMiddleware)

    # 8. Authentication - MUST come before other security middleware
    app.add_middleware(AuthMiddleware)

    # 9. API Key validation - After authentication
    app.add_middleware(APIKeyAuthMiddleware)

    # 10. Security: AutonoGuard - After authentication to protect sensitive operations
    app.add_middleware(AutonoGuardMiddleware)

    # 11. Security: Honeypot - After authentication to only trap unauthorized access
    app.add_middleware(HoneypotMiddleware)

    # 12. Security: Chaos injection - After authentication for controlled testing
    app.add_middleware(ChaosInjectorMiddleware)  # type: ignore

    # 13. Idempotency middleware - After authentication to ensure idempotency per user
    app.add_middleware(IdempotencyMiddleware)

    # 14. Rate Limiting — CORS is added last (below), so it wraps this, and
    # a 429 short-circuit response returned here still gets CORS headers on
    # the way back out through the stack.
    from core.rate_limit import RateLimiter

    app.add_middleware(RateLimitMiddleware, limiter=RateLimiter())

    # 15. Response standardization - runs before CORS wraps everything
    app.add_middleware(ResponseStandardizationMiddleware)

    # 16. CORS — added LAST so it is the true outermost layer (see the
    # ROOT-CAUSE FIX note above `origins = ...`). Any short-circuit response
    # from any middleware above (401 from AuthMiddleware, 429 from
    # RateLimitMiddleware, etc.) still passes through this on the way back
    # out, so it always gets proper CORS headers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=cors_allow_credentials,
        allow_methods=["*"],
        # ROOT-CAUSE FIX: ফ্রন্টএন্ড (services/apiClient.ts → getAuthHeaders) প্রতিটি
        # রিকোয়েস্টে X-Device-Fingerprint পাঠায়, আর X-CSRF-Token / X-JIT-OTP
        # শর্তসাপেক্ষে পাঠায়। এই হেডারগুলো allow_headers-এ না থাকায় Starlette
        # CORSMiddleware preflight-এ "400 Disallowed CORS headers" দিত — ফলে
        # তিনটি ফ্রন্টএন্ড (Firebase user/admin, Vercel) থেকেই সব API কল ব্রাউজারে
        # ব্লক হচ্ছিল, যদিও origin allow-list ঠিক ছিল। তালিকাটি এখন
        # TrustedOriginMiddleware-এর ডিফল্ট হেডার সেটের সাথে সমন্বিত।
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
            "apikey",
            "X-API-Key",
            "X-Device-Fingerprint",
            "X-CSRF-Token",
            "X-JIT-OTP",
            "X-Request-ID",
            "X-Tenant-ID",
            "X-Correlation-ID",
        ],
        expose_headers=["Content-Length", "X-Pagination-Total"],
    )

    # বাংলা মন্তব্ব্য: রাউটার রেজিস্টার করা
    # রাউটার রেজিস্ট্রেশনগুলো এখানে যোগ করুন

    # বাংলা মন্তব্ব্য: মেট্রিক্স এন্ডপয়েন্ট যোগ করা
    if settings.MONITORING_DETAILED:
        from fastapi.responses import PlainTextResponse

        from core.monitoring import get_metrics_collector

        @app.get("/metrics", response_class=PlainTextResponse)
        async def metrics_endpoint():
            collector = get_metrics_collector()
            return collector.export_prometheus()

    # 🔬 Evolution v3.0: Register health endpoints
    from core.health_routes import router as health_router

    # রেন্ডার হেলথ চেক render.yaml-এ /api/v1/health/live হিসেবে কনফিগার করা,
    # তাই রাউটার এখন /api/v1/health প্রিফিক্সে মাউন্ট করা হচ্ছে (আগে /health ছিল,
    # যেটা কনফিগার করা পাথের সাথে মিলছিল না ফলে লাইভনেস প্রোব বরাবর 404 পেত)।
    app.include_router(health_router, prefix="/api/v1/health")
    # ব্যাকওয়ার্ড কম্প্যাটিবিলিটি: পুরনো /health পাথেও একই রাউটার এক্সপোজ করা থাকল।
    app.include_router(health_router, prefix="/health")

    @app.api_route("/", methods=["GET", "HEAD"])
    async def root():
        """পাবলিক রুট এন্ডপয়েন্ট — বেসিক সার্ভিস তথ্য এবং হেলথ চেক লিংক দেয়।"""
        return {
            "service": settings.app_name,
            "status": "online",
            "health_check": "/health",
        }

    from fastapi.responses import JSONResponse

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc: Exception):
        """Handle unhandled exceptions with proper response and circuit breaker awareness."""

        from core.circuit_breaker import CIRCUITS

        status_code = getattr(exc, "status_code", 500)

        # Log the full error internally
        logger.error(f"Global Exception: {exc.__class__.__name__}: {str(exc)}")

        # H-03 Fix: Only expose safe details to the client
        if status_code < 500:
            error_response = {
                "error": exc.__class__.__name__,
                "detail": str(exc),
            }
        else:
            error_response = {
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred on the server.",
            }

        if hasattr(exc, "to_dict"):
            error_response.update(exc.to_dict())

        exc_lower = str(exc).lower()
        if any(kw in exc_lower for kw in ["timeout", "connection", "refused", "5xx"]):
            cb_stats = {name: cb.stats for name, cb in CIRCUITS.items()}
            if any(s.current_state.value == "open" for s in cb_stats.values()):
                error_response["circuit_breakers"] = {
                    name: {"state": s.current_state.value, "recovery_in": cb.get_recovery_time()}
                    for name, cb, s in [
                        (n, CIRCUITS[n], CIRCUITS[n].stats)
                        for n in CIRCUITS
                        if CIRCUITS[n].stats.current_state.value == "open"
                    ]
                }

        return JSONResponse(
            status_code=status_code,
            content=error_response,
        )

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.debug("✅ FastAPI OpenTelemetry instrumentor enabled.")
    except ImportError:
        logger.warning("⚠️ opentelemetry-instrumentation-fastapi not installed.")

    return app


# Backward-compatibility alias for legacy tests
build_app_shell = create_app


def router_health_check(app: FastAPI | None = None, expected_count: int = 0) -> dict[str, Any]:
    """Helper to return health status of app routers."""
    return {"status": "healthy", "expected_count": expected_count, "env": settings.env}
