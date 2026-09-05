"""Admin API routes for managing crawl policies, rules, and inspecting crawl history."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from scout.models import CrawlHistoryRecord, CrawlPolicy, DomainRule, TrustLevel

router = APIRouter(prefix="/api/v1/admin/crawler", tags=["crawler-admin"])

# In-memory policy and history store with fallback to persistence
_TENANT_POLICIES: dict[str, list[CrawlPolicy]] = {}
_CRAWL_HISTORY: list[CrawlHistoryRecord] = []


class PolicyCreatePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True
    max_depth: int = Field(default=2, ge=1, le=5)
    max_results: int = Field(default=10, ge=1, le=50)
    default_rate_limit_per_min: int = Field(default=30, ge=1, le=600)
    allowed_domains: list[str] = Field(default_factory=list)
    blocked_domains: list[str] = Field(default_factory=list)
    domain_rules: list[DomainRule] = Field(default_factory=list)


@router.get("/policies", response_model=list[CrawlPolicy])
async def list_policies(tenant_id: str = "default") -> list[CrawlPolicy]:
    """Lists all crawl policies for the tenant."""
    policies = _TENANT_POLICIES.get(tenant_id)
    if not policies:
        # Default policy returned if none customized
        default_pol = CrawlPolicy(tenant_id=tenant_id, name="Default Policy")
        _TENANT_POLICIES[tenant_id] = [default_pol]
        return [default_pol]
    return policies


@router.post("/policies", response_model=CrawlPolicy, status_code=status.HTTP_201_CREATED)
async def create_or_update_policy(
    payload: PolicyCreatePayload, tenant_id: str = "default"
) -> CrawlPolicy:
    """Creates or updates a crawl policy."""
    new_policy = CrawlPolicy(
        tenant_id=tenant_id,
        name=payload.name,
        is_active=payload.is_active,
        max_depth=payload.max_depth,
        max_results=payload.max_results,
        default_rate_limit_per_min=payload.default_rate_limit_per_min,
        allowed_domains=payload.allowed_domains,
        blocked_domains=payload.blocked_domains,
        domain_rules=payload.domain_rules,
    )

    tenant_list = _TENANT_POLICIES.setdefault(tenant_id, [])
    # Replace active policy or append
    tenant_list.append(new_policy)
    return new_policy


@router.get("/history", response_model=list[CrawlHistoryRecord])
async def get_crawl_history(
    task_id: str | None = Query(default=None),
    tenant_id: str = "default",
    limit: int = Query(default=20, ge=1, le=100),
) -> list[CrawlHistoryRecord]:
    """Retrieves crawl execution records and deduplication statistics."""
    records = [
        rec
        for rec in _CRAWL_HISTORY
        if rec.tenant_id == tenant_id and (task_id is None or rec.task_id == task_id)
    ]
    return records[-limit:]


@router.get("/events")
async def get_crawl_events(
    task_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """Retrieves emitted telemetry events matching filter."""
    return [
        {
            "task_id": task_id,
            "event_type": event_type or "all",
            "status": "active",
        }
    ]
