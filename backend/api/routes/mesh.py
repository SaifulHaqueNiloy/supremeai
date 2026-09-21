"""Mesh presence REST API — MESH-1, issue #939.

বাংলা সারসংক্ষেপ:
------------------
এই router চারটি endpoint প্রদান করে যা SupremeAI Distributed Multi-Agent Mesh-এর
foundation layer হিসেবে কাজ করে:

- POST   /api/v1/nodes/heartbeat       — একটি agent তার heartbeat পাঠায়
- GET    /api/v1/nodes                  — সব active node-এর তালিকা (MESH-2 dashboard পড়ে)
- GET    /api/v1/nodes/{node_id}        — একটি node-এর বিস্তারিত record
- PATCH  /api/v1/nodes/{node_id}        — node-এর role পরিবর্তন (MESH-2 dropdown)

conventions:
- FastAPI APIRouter + Pydantic v2 models (match existing routes যেমন health.py)
- prefix=/api/v1 (routers.py থেকে mount করা হয়, এখানে prefix দেওয়া নেই)
- সব endpoint process-wide `PresenceRegistry` singleton ব্যবহার করে
- কোনো fake/mock নেই — সব endpoint আসল registry-তে লেখে/পড়ে

সম্পর্কিত:
- Master plan: docs/plans/MULTI_AGENT_MESH_MASTER_PLAN.md (Section 6, MESH-1)
- Issue: #939 (P1-high, Phase A)
- Depends on: backend/core/presence_registry.py (নতুন file, এই PR-এ যোগ হয়েছে)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.logging_config import logger
from core.presence_registry import (
    DEFAULT_STALE_AFTER_SECONDS,
    HeartbeatResult,
    NodeLoad,
    NodeRecord,
    PresenceRegistry,
    VALID_NODE_TYPES,
    VALID_ROLES,
    get_presence_registry,
)

router = APIRouter(
    prefix="/api/v1/nodes",
    tags=["mesh-presence"],
    # বাংলা: এই endpoints public mesh presence প্রদান করে। Auth যোগ করা হয়নি
    # কারণ (১) heartbeat একটি agent-এর প্রথম কল হতে পারে — pre-auth; (২) কেবল
    # presence state পড়ে/লেখে, কোনো privileged resource স্পর্শ করে না। একটি
    # follow-up issue আলাদা auth যোগ করবে (MESH-3 local daemon-এর সাথে)।
)


# ── Request Models ───────────────────────────────────────────────────────────
class HeartbeatRequest(BaseModel):
    """POST /api/v1/nodes/heartbeat — request body schema (issue #939 spec-এর সাথে মিল)।"""

    node_id: str = Field(..., min_length=1, max_length=128, description="Unique node identifier")
    node_type: str = Field(
        ..., description=f"One of {sorted(VALID_NODE_TYPES)}"
    )
    role: str = Field(..., description=f"One of {sorted(VALID_ROLES)}")
    capabilities: list[str] = Field(default_factory=list)
    timestamp: str | None = Field(
        default=None,
        description="Client-provided ISO 8601 timestamp (optional; server uses its own clock for lease calc)",
    )
    load: NodeLoad | None = Field(default=None, description="System load snapshot")
    # বাংলা: None মানে "caller omitted করেছে" — registry তখন আগের record-এর
    # assigned_tasks বজায় রাখে (lease continuation contract)। খালি list পাঠালে
    # সেটাই override হবে (caller স্পষ্টভাবে পরিষ্কার করতে চাইলে)।
    assigned_tasks: list[str] | None = Field(
        default=None,
        description="Omit to preserve existing tasks (lease continuation); empty list clears.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Omit to preserve existing metadata; explicit dict replaces.",
    )


class RoleUpdateRequest(BaseModel):
    """PATCH /api/v1/nodes/{node_id} — role update body (MESH-2 dashboard-এর জন্য)।"""

    role: str = Field(..., description=f"One of {sorted(VALID_ROLES)}")


# ── Response Models ───────────────────────────────────────────────────────────
class NodeListResponse(BaseModel):
    """GET /api/v1/nodes — list of active nodes wrapped in metadata envelope।"""

    nodes: list[NodeRecord]
    count: int
    stale_after_seconds: int


class NodeDetailResponse(BaseModel):
    """GET /api/v1/nodes/{node_id} — single node detail (or 404 if unknown)।"""

    node: NodeRecord


# ── Endpoints ────────────────────────────────────────────────────────────────
@router.post(
    "/heartbeat",
    response_model=HeartbeatResult,
    status_code=status.HTTP_200_OK,
    summary="Register a mesh node heartbeat",
)
async def post_node_heartbeat(
    payload: HeartbeatRequest,
    registry: PresenceRegistry = Depends(get_presence_registry),
) -> HeartbeatResult:
    """একটি agent তার heartbeat পাঠায় — registry-তে presence ও lease refresh হয়।

    প্রতিটি heartbeat একটি lease প্রদান করে যা ডিফল্টভাবে ১০ মিনিট পর মেয়াদোত্তীর্ণ হয়।
    পরবর্তী heartbeat এলে lease আবার refresh হয়। Lease মেয়াদোত্তীর্ণ হলেও record
    সরানো হয় না — শুধু `lease_active=false` চিহ্নিত করা হয়।

    Invalid `node_type` বা `role` হলে 422 + detailed error ফেরত আসে।
    """
    try:
        result = await registry.register_heartbeat(
            node_id=payload.node_id,
            node_type=payload.node_type,
            role=payload.role,
            capabilities=payload.capabilities,
            load=payload.load,
            assigned_tasks=payload.assigned_tasks,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        # Pydantic-style validation error — 422 is correct contract.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001 — surface any unexpected registry error
        logger.error("mesh.post_node_heartbeat: registry failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="presence registry unavailable",
        ) from exc
    return result


@router.get(
    "",
    response_model=NodeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all active mesh nodes",
)
async def list_active_nodes(
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
    registry: PresenceRegistry = Depends(get_presence_registry),
) -> NodeListResponse:
    """সব active (non-stale) mesh nodes — MESH-2 dashboard এই endpoint কল করে।

    বাংলা: ডিফল্টভাবে last_seen থেকে ৬০০ সেকেন্ড (১০ মিনিট) পুরোনো node
    stale হিসেবে গণ্য হয় এবং এই তালিকায় থাকবে না। `stale_after_seconds`
    query param দিয়ে caller-নির্দিষ্ট threshold যোগ করা যায় (min ১ সেকেন্ড)।
    """
    if stale_after_seconds < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="stale_after_seconds must be >= 1",
        )
    nodes = await registry.list_active_nodes(stale_after_seconds=stale_after_seconds)
    return NodeListResponse(
        nodes=nodes,
        count=len(nodes),
        stale_after_seconds=stale_after_seconds,
    )


@router.get(
    "/{node_id}",
    response_model=NodeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single mesh node detail",
)
async def get_node_detail(
    node_id: str,
    registry: PresenceRegistry = Depends(get_presence_registry),
) -> NodeDetailResponse:
    """একটি নির্দিষ্ট node-এর presence record দেখাও (stale হলেও ফেরত দেয়)।

    বাংলা: node_id পাওয়া না গেলে 404। পাওয়া গেলে lease state সহ full record ফেরত দেয়।
    """
    record = await registry.get_node(node_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"node_id {node_id!r} not registered",
        )
    return NodeDetailResponse(node=record)


@router.patch(
    "/{node_id}",
    response_model=NodeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a mesh node's role (MESH-2 dashboard dropdown)",
)
async def patch_node_role(
    node_id: str,
    payload: RoleUpdateRequest,
    registry: PresenceRegistry = Depends(get_presence_registry),
) -> NodeDetailResponse:
    """Node-এর role পরিবর্তন করো — MESH-2 dashboard-এর Planner/Coder/Tester/Gate
    dropdown এই endpoint কল করবে।

    বাংলা: invalid role হলে 422, unknown node_id হলে 404।
    """
    try:
        updated = await registry.set_role(node_id, payload.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return NodeDetailResponse(node=updated)


__all__ = [
    "HeartbeatRequest",
    "NodeDetailResponse",
    "NodeListResponse",
    "RoleUpdateRequest",
    "router",
]
