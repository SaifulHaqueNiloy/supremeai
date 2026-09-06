"""Render Deployment Preflight and Account State Admin API.

Provides:
  - GET /api/v1/admin/render/preflight
  - POST /api/v1/admin/render/accounts/{role}/recheck
  - POST /api/v1/admin/render/accounts/{role}/override
  - GET /api/v1/admin/render/events
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.dependencies import get_current_admin
from api.routes.admin_auth import admin_rate_limit, require_admin_token
from database.supabase_client import db
from services.render_account_service import RenderAccountService

router = APIRouter(
    prefix="/api/v1/admin/render",
    tags=["admin-render-preflight"],
    dependencies=[Depends(require_admin_token), Depends(admin_rate_limit)],
)


class ManualOverrideRequest(BaseModel):
    status: Literal["ready", "blocked", "cooldown", "recheck_required"] = Field(
        ..., description="Desired overridden status"
    )
    reason: str = Field(..., min_length=3, description="Audit reason for manual override")


class RecheckRequest(BaseModel):
    force: bool = Field(default=False, description="Force recheck even during cooldown")


@router.get("/preflight")
async def get_render_deploy_preflight(admin: dict = Depends(get_current_admin)) -> dict[str, Any]:
    """Return preflight status, limits, and deployment authorization across Render roles.

    Can also be used directly as the target of RENDER_PREFLIGHT_URL in GitHub Actions CI.
    """
    return RenderAccountService.get_status_overview()


@router.post("/accounts/{role}/recheck")
async def recheck_render_account(
    role: str,
    payload: RecheckRequest = RecheckRequest(),
    admin: dict = Depends(get_current_admin),
) -> dict[str, Any]:
    """Trigger a live audit/refresh against Render for a given account role."""
    admin_user = admin.get("sub", admin.get("email", "admin"))
    result = RenderAccountService.refresh_account_status(
        account_role=role,
        force=payload.force,
        manual_by=admin_user,
    )
    return {
        "status": "success",
        "role": role,
        "account_state": result,
    }


@router.post("/accounts/{role}/override")
async def override_render_account(
    role: str,
    payload: ManualOverrideRequest,
    admin: dict = Depends(get_current_admin),
) -> dict[str, Any]:
    """Apply an explicit manual override with a logged reason."""
    admin_user = admin.get("sub", admin.get("email", "admin"))
    result = RenderAccountService.manual_override(
        account_role=role,
        status=payload.status,
        reason=payload.reason,
        admin_user=admin_user,
    )
    return {
        "status": "success",
        "role": role,
        "overridden_state": result,
    }


@router.get("/events")
async def get_render_preflight_events(
    account_key: str | None = Query(None, description="Filter by account key/role"),
    limit: int = Query(50, ge=1, le=200),
    admin: dict = Depends(get_current_admin),
) -> list[dict[str, Any]]:
    """Get audit trail of preflight events, cooldowns, and overrides."""
    return db.get_render_preflight_events(account_key=account_key, limit=limit)
