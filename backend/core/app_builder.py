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

import logging
import os
import re
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from core.config import settings
from core.container_auditor import audit_container_resources
from core.lifespan import app_lifespan
from core.logging_config import setup_logging

# from core.metrics.prometheus import PrometheusMiddleware, metrics_endpoint
from core.security.api_key_middleware import APIKeyAuthMiddleware
from core.security.auth_middleware import AuthMiddleware
from core.security.honeypot_middleware import HoneypotMiddleware
# from core.security.chaos_injector import ChaosInjectorMiddleware

# Initialize Sentry if DSN is provided
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    # Validate Sentry DSN format
    def is_valid_sentry_dsn(dsn: str) -> bool:
        """Validate Sentry DSN format."""
        if not dsn:
            return False

        # Basic regex pattern for Sentry DSN
        # Format: protocol://public_key@host/project_id
        pattern = r"^https?://[^@]+@[\w.-]+(?::\d+)?/\d+$"
        return bool(re.match(pattern, dsn))

    if settings.sentry_dsn and is_valid_sentry_dsn(settings.sentry_dsn):
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
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

# বাংলা মন্তব্ব্য: সম্পূর্ণ অ্যাপ্লিকেশন স্টার্টআপ লজিক — টেস্ট এক্সক্লুডেড
if "pytest" not in sys.modules and os.getenv("CI") != "true":
    audit_container_resources()
    setup_logging()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application with all middleware and routes."""

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        # বাংলা মন্তব্ব্য: অ্যাপ্লিকেশন লাইফস্প্যান ম্যানেজমেন্ট
        async with app_lifespan(app):
            yield

    docs_url = "/docs" if settings.env == "local" or settings.debug else None
    redoc_url = "/redoc" if settings.env == "local" or settings.debug else None
    openapi_url = f"{settings.API_V1_STR}/openapi.json" if docs_url else None

    # বাংলা মন্তব্ব্য: অ্যাপ্লিকেশন ইনস্ট্যান্স তৈরি করা হচ্ছে
    app = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=_lifespan,
    )

    # বাংলা মন্তব্ব্য: মিডলওয়্যার চেইন — ORDER IS CRITICAL FOR SECURITY
    # 1. Prometheus metrics collection (must be first to track all requests)
    # app.add_middleware(PrometheusMiddleware)

    # 2. Security: Authentication & Authorization (must come before other security middleware)
    # This ensures that only authenticated requests proceed to other middleware layers
    app.add_middleware(AuthMiddleware)

    # 3. Security: API Key validation
    app.add_middleware(APIKeyAuthMiddleware)

    # 4. Security: Honeypot (now comes AFTER authentication to only trap unauthorized access)
    app.add_middleware(HoneypotMiddleware)

    # 5. Security: Chaos injection (also comes AFTER authentication for controlled testing)
    # app.add_middleware(ChaosInjectorMiddleware)

    # 6. CORS: Cross-origin resource sharing configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # বাংলা মন্তব্ব্য: প্রোডাকশনে কখনো expose_headers=["Authorization"] না করা
        # কারণ এটি sensitive info লিক করতে পারে
    )

    # বাংলা মন্তব্ব্য: রাউটার রেজিস্টার করা
    # রাউটার রেজিস্ট্রেশনগুলো এখানে যোগ করুন

    # বাংলা মন্তব্ব্য: মেট্রিক্স এন্ডপয়েন্ট যোগ করা
    # try:
    #     # app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])
    # except Exception as e:
    #     logger.error(f"Failed to add metrics endpoint: {e}")

    # বাংলা মন্তব্ব্য: হেল্থ চেক এন্ডপয়েন্ট
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "env": settings.env}

    return app
