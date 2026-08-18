"""Self-Evolving Memory Storage API endpoints (optional/self-healing safe)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from core.config import settings
from memory.unified_db_manager import unified_db

router = APIRouter(prefix="/self-evolve", tags=["self-evolving-memory"])


class PruneRequest(BaseModel):
    max_age_days: int = Field(default=90, ge=1, description="Days since last access before pruning")
    min_access: int = Field(default=1, ge=0, description="Minimum access count to be retained")


class ReorganizeRequest(BaseModel):
    max_age_days: int = Field(default=90, ge=1)
    min_access: int = Field(default=1, ge=0)


async def require_admin_token(x_admin_token: str | None = Header(default=None)) -> bool:
    expected = getattr(settings, "supremeai_api_token", None)
    if not expected or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
    return True


@router.get("/clusters")
async def get_clusters(_: bool = Depends(require_admin_token)) -> dict[str, Any]:
    service = unified_db.get_self_evolve_service()
    result = await service.cluster_memories()
    return {
        "total": result.total,
        "clusters": [c.__dict__ for c in result.clusters],
        "noise_count": len(result.noise),
    }


@router.get("/duplicates")
async def get_duplicates(_: bool = Depends(require_admin_token)) -> dict[str, Any]:
    service = unified_db.get_self_evolve_service()
    pairs = await service.find_duplicates()
    return {"count": len(pairs), "duplicates": [p.__dict__ for p in pairs]}


@router.post("/prune")
async def prune(
    body: PruneRequest, _: bool = Depends(require_admin_token)
) -> dict[str, Any]:
    service = unified_db.get_self_evolve_service()
    result = await service.prune_unused(
        max_age_days=body.max_age_days, min_access=body.min_access
    )
    return result.__dict__


@router.post("/reorganize")
async def reorganize(
    body: ReorganizeRequest, _: bool = Depends(require_admin_token)
) -> dict[str, Any]:
    service = unified_db.get_self_evolve_service()
    result = await service.reorganize_storage(
        max_age_days=body.max_age_days, min_access=body.min_access
    )
    return result.__dict__
