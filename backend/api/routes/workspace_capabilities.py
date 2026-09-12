"""Tenant-scoped capability discovery for the workspace control plane."""

from __future__ import annotations

from urllib.parse import urlparse
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import get_current_user_token
from core.logging_config import logger

router = APIRouter(prefix="/api/v1/workspace", tags=["Workspace Capabilities"])


class CapabilityRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=2048)
    name: str = Field(..., min_length=1, max_length=255)
    connection_type: str = Field(default="mcp", max_length=32)


class CapabilityResponse(BaseModel):
    id: str
    name: str
    url: str
    connection_type: str
    status: str
    capabilities: list[str]
    message: str


def _tenant(user: dict) -> tuple[str, str]:
    tenant = str(user.get("tenant_id") or user.get("org_id") or "").strip()
    actor = str(user.get("sub") or user.get("user_id") or user.get("email") or "").strip()
    if not tenant or not actor:
        raise HTTPException(status_code=403, detail="Tenant and actor context required")
    return tenant, actor


@router.get("/capabilities")
async def list_workspace_capabilities(user: dict = Depends(get_current_user_token)) -> dict:
    tenant, actor = _tenant(user)
    return {
        "tenant_id": tenant,
        "actor_id": actor,
        "capabilities": [],
        "message": "No external capability connections are registered for this workspace.",
    }


@router.post(
    "/capabilities", response_model=CapabilityResponse, status_code=status.HTTP_202_ACCEPTED
)
async def register_workspace_capability(
    req: CapabilityRequest, user: dict = Depends(get_current_user_token)
) -> CapabilityResponse:
    tenant, actor = _tenant(user)
    parsed = urlparse(req.url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=422, detail="A valid HTTPS or HTTP capability URL is required"
        )
    connection_id = str(uuid4())
    logger.info(
        "Capability registration requested",
        extra={
            "tenant_id": tenant,
            "actor_id": actor,
            "connection_id": connection_id,
            "url": req.url,
        },
    )
    return CapabilityResponse(
        id=connection_id,
        name=req.name,
        url=req.url,
        connection_type=req.connection_type,
        status="pending",
        capabilities=[],
        message="Connection request accepted for capability discovery. Provider consent is still required.",
    )
