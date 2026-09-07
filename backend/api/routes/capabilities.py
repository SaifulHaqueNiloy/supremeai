from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.dependencies import get_current_user_token
from core.capability_discovery import discover_capabilities
from core.capability_gateway import HEALTH_CAPABILITY, execute_capability

router = APIRouter(prefix="/api/v1/capabilities", tags=["capabilities"])


class CapabilityExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: str = Field(default=HEALTH_CAPABILITY, min_length=1, max_length=160)
    source: str = Field(default="api", min_length=1, max_length=40)
    payload: dict = Field(default_factory=dict)


@router.get("")
async def list_capabilities(user: dict = Depends(get_current_user_token)) -> dict:
    actor_id = str(user.get("sub") or "")
    tenant_id = str(user.get("tenant_id") or actor_id)
    if not actor_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Execution identity is incomplete")
    return {"capabilities": discover_capabilities(tenant_id)}


@router.post("/execute")
async def execute(
    request: CapabilityExecuteRequest,
    user: dict = Depends(get_current_user_token),
) -> dict:
    actor_id = str(user.get("sub") or "")
    tenant_id = str(user.get("tenant_id") or actor_id)
    if not actor_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Execution identity is incomplete")

    result = await execute_capability(
        actor_id=actor_id,
        tenant_id=tenant_id,
        source=request.source,
        capability=request.capability,
        payload=request.payload,
    )
    if result.status.value == "unavailable":
        raise HTTPException(
            status_code=404, detail=result.error_message or "Capability unavailable"
        )
    if result.status.value == "rejected":
        raise HTTPException(status_code=403, detail=result.error_message or "Capability rejected")
    return result.model_dump(mode="json")
