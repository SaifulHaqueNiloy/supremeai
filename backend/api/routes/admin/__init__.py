"""Admin package — aggregates all sub-routers into two FastAPI routers.

Usage (in api/routes/admin_dashboard.py or main router registration):
    from api.routes.admin import router, sse_router
"""
from fastapi import APIRouter, Depends

from api.routes.admin_auth import admin_rate_limit, require_admin_token, validate_sse_token
from api.dependencies import get_current_admin

# Sub-modules
from api.routes.admin import (
    users,
    costs,
    providers,
    system,
    deploy,
    backup,
    feature_flags,
    security,
    streams,
    ci_gate,
    config,
)

# ─── Main authenticated router ────────────────────────────────────────────────
router = APIRouter(
    prefix="/admin-api",
    tags=["admin-dashboard"],
    dependencies=[Depends(require_admin_token), Depends(admin_rate_limit)],
)

router.include_router(users.router)
router.include_router(costs.router)
router.include_router(providers.router)
router.include_router(system.router)
router.include_router(deploy.router)
router.include_router(backup.router)
router.include_router(feature_flags.router)
router.include_router(security.router)
router.include_router(streams.router)   # /events + /ws
router.include_router(ci_gate.router)
router.include_router(config.router)

# ─── SSE router (uses SSE token auth) ────────────────────────────────────────
sse_router = APIRouter(
    prefix="/admin-api",
    tags=["admin-dashboard-sse"],
    dependencies=[Depends(validate_sse_token), Depends(admin_rate_limit)],
)

sse_router.include_router(streams.router)  # /logs/stream + /events/stream

__all__ = ["router", "sse_router", "get_current_admin"]
