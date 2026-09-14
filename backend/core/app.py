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
from core.app_builder import create_app
from core.health_check import health_checker
from monitoring import init_observability

# Initialize observability (Sentry APM & Error Tracking) before creating app
init_observability()

app = create_app()

# Import and add MemoryAwareMiddleware for Render Free Tier optimization
from core.memory_manager import MemoryAwareMiddleware

app.add_middleware(MemoryAwareMiddleware)


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


# Mount-hygiene note (2026-09-15): the direct ``include_router(admin_router)``
# that used to sit here duplicated the canonical ALL_ROUTERS registry entry
# (core.admin_routes, is_critical=True — fail-fast mount with boot-proof
# accounting), giving every /admin/* route a second registration. The registry
# is the single mount point; service-role filtering (scraper/worker intentionally
# skip admin surface) also now applies uniformly.
register_all_routers(app)

# FIX (API-contract audit): legacy `/api/chat/stream` alias — previously a dead
# path (prefixed router concatenation). Exported prefix-less from
# stream_chat_sse and mounted here so the existing frontend/vscode-extension
# clients keep working alongside the new /api/v1/stream/chat pipeline.
from api.routes.stream_chat_sse import legacy_router as chat_stream_legacy_router

app.include_router(chat_stream_legacy_router)

# Task 7-c / 7-d mount hygiene (2026-09-15): missions and mcp_hub are mounted
# through the canonical ALL_ROUTERS registry (api/routers.py — AUDIT-WIRE FIX 3,
# boot-proofed mounted=N/N accounting). The direct include_router() blocks that
# PR #304/#305 shipped alongside the registry entries caused a DOUBLE mount
# (22 mission + 14 mcp routes on the app; first-match wins at runtime, but the
# duplicate registration corrupted OpenAPI listing and registry accounting).
# Keep the registry as the single source of truth for these routers.
