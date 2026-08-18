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
    merge_duplicates: bool = Field(
        default=False, description="Merge near-duplicate memories into one synthesized memory"
    )
    apply_decay: bool = Field(
        default=False, description="Garbage-collect memories whose Ebbinghaus retention decayed"
    )
    persist_clusters: bool = Field(
        default=False, description="Write cluster_id into memory metadata for hierarchical retrieval"
    )


class DeduplicateRequest(BaseModel):
    threshold: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Similarity cutoff (defaults to service setting)"
    )
    dry_run: bool = Field(default=True, description="Preview merges without mutating memory")


class DecayPruneRequest(BaseModel):
    retention_threshold: float = Field(
        default=0.15, gt=0.0, le=1.0, description="Prune below this Ebbinghaus retention value"
    )
    min_age_days: int = Field(default=30, ge=1, description="Hard safety floor before any GC")
    dry_run: bool = Field(default=True, description="Preview GC without deleting anything")


class HierarchicalSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    n_results: int = Field(default=5, ge=1, le=50)
    cluster_probe: int = Field(default=3, ge=1, le=50)


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
        max_age_days=body.max_age_days,
        min_access=body.min_access,
        merge_duplicates=body.merge_duplicates,
        apply_decay=body.apply_decay,
        persist_clusters=body.persist_clusters,
    )
    return result.__dict__


@router.post("/deduplicate")
async def deduplicate(
    body: DeduplicateRequest, _: bool = Depends(require_admin_token)
) -> dict[str, Any]:
    """Merge near-duplicate memories into one synthesized memory (BLUEPRINT-MEM-001 §3.1)."""
    service = unified_db.get_self_evolve_service()
    result = await service.deduplicate_memories(threshold=body.threshold, dry_run=body.dry_run)
    return {
        "dry_run": result.dry_run,
        "merged_count": result.merged_count,
        "merged_ids": result.merged_ids,
        "groups": [g.__dict__ for g in result.groups],
    }


@router.get("/decay-report")
async def decay_report(
    limit: int = 50, _: bool = Depends(require_admin_token)
) -> dict[str, Any]:
    """Weakest-retention memories first (R = e^(-t/S)) — the GC candidate queue."""
    service = unified_db.get_self_evolve_service()
    scores = await service.decay_report(limit=max(1, min(limit, 500)))
    return {"count": len(scores), "scores": [s.__dict__ for s in scores]}


@router.post("/decay-prune")
async def decay_prune(
    body: DecayPruneRequest, _: bool = Depends(require_admin_token)
) -> dict[str, Any]:
    """Garbage-collect forgotten memories using the Ebbinghaus decay curve."""
    service = unified_db.get_self_evolve_service()
    result = await service.prune_decayed_memories(
        retention_threshold=body.retention_threshold,
        min_age_days=body.min_age_days,
        dry_run=body.dry_run,
    )
    return result.__dict__


@router.post("/assign-clusters")
async def assign_clusters(_: bool = Depends(require_admin_token)) -> dict[str, Any]:
    """Persist cluster_id metadata so retrieval can probe clusters instead of full scans."""
    service = unified_db.get_self_evolve_service()
    assignments = await service.assign_cluster_ids()
    return {"assigned": len(assignments), "assignments": assignments}


@router.post("/search")
async def hierarchical_search(
    body: HierarchicalSearchRequest, _: bool = Depends(require_admin_token)
) -> dict[str, Any]:
    """Cluster-probe (IVF-style) retrieval — reports how much of the corpus was skipped."""
    service = unified_db.get_self_evolve_service()
    result = await service.hierarchical_search(
        query=body.query, n_results=body.n_results, cluster_probe=body.cluster_probe
    )
    return {
        "matches": [m.__dict__ for m in result.matches],
        "clusters_probed": result.clusters_probed,
        "clusters_total": result.clusters_total,
        "docs_scanned": result.docs_scanned,
        "docs_total": result.docs_total,
        "fallback_full_scan": result.fallback_full_scan,
    }


# ----------------------------------------------------------------------
# Autonomous evolution loop control
# ----------------------------------------------------------------------
@router.get("/auto-loop/status")
async def auto_loop_status(_: bool = Depends(require_admin_token)) -> dict[str, Any]:
    return unified_db.get_evolution_loop().status()


@router.post("/auto-loop/start")
async def auto_loop_start(_: bool = Depends(require_admin_token)) -> dict[str, Any]:
    loop = unified_db.get_evolution_loop()
    started = await loop.start()
    return {"started": started, **loop.status()}


@router.post("/auto-loop/stop")
async def auto_loop_stop(_: bool = Depends(require_admin_token)) -> dict[str, Any]:
    loop = unified_db.get_evolution_loop()
    stopped = await loop.stop()
    return {"stopped": stopped, **loop.status()}


@router.post("/auto-loop/run-once")
async def auto_loop_run_once(_: bool = Depends(require_admin_token)) -> dict[str, Any]:
    """Trigger a single evolution cycle immediately (uses the loop's configuration)."""
    loop = unified_db.get_evolution_loop()
    result = await loop.run_once()
    return {"result": result.__dict__, "stats": loop.status()["stats"]}

