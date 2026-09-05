from __future__ import annotations

import os
import sys

from core.logging_config import logger

# Ensure backend root is in sys.path to resolve top-level packages (api, core, utils)
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi import HTTPException

from api.routers import register_all_routers
from core.admin_routes import router as admin_router
from core.app_builder import create_app
from core.health_check import health_checker
from monitoring import init_observability

# Initialize observability (Sentry APM & Error Tracking) before creating app
init_observability()

app = create_app()

# Import and add MemoryAwareMiddleware for Render Free Tier optimization
from core.memory_manager import MemoryAwareMiddleware

app.add_middleware(MemoryAwareMiddleware)


@app.get("/")
async def root_welcome():
    """Root endpoint to prevent 404s and provide a fast wake-up route."""
    return {"message": "Welcome to SupremeAI Backend API", "status": "Active", "docs_url": "/docs"}


@app.get("/health/aggregated")
async def aggregated_health_check():
    try:
        health_data = await health_checker.check_all()
        return health_data
    except Exception as e:
        logger.error(f"Aggregated health check failed: {e}")
        raise HTTPException(
            status_code=503, detail=f"Health check service unavailable: {e!s}"
        ) from e


app.include_router(admin_router)
register_all_routers(app)

# FIX (API-contract audit): legacy `/api/chat/stream` alias — previously a dead
# path (prefixed router concatenation). Exported prefix-less from
# stream_chat_sse and mounted here so the existing frontend/vscode-extension
# clients keep working alongside the new /api/v1/stream/chat pipeline.
from api.routes.stream_chat_sse import legacy_router as chat_stream_legacy_router

app.include_router(chat_stream_legacy_router)

from api.routes.tier_s_routes import register_tier_s_routes

register_tier_s_routes(app)
