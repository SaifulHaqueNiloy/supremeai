from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.circles.contracts import (
    CapabilityRef,
    CapabilityRequest,
    CircleName,
    ExecutionContext,
    ExecutionResult,
    PolicyDecision,
    RiskLevel,
)
from core.circles.registry import circle_registry

HEALTH_CAPABILITY = "system.health.read"


def _policy(request: CapabilityRequest) -> PolicyDecision:
    """Small central policy boundary for the first migrated capability."""
    if not request.context.actor_id.strip() or not request.context.tenant_id.strip():
        return PolicyDecision(allowed=False, reason="actor_context_invalid")
    if request.capability.name == HEALTH_CAPABILITY and request.capability.risk_level is not RiskLevel.LOW:
        return PolicyDecision(allowed=False, reason="health_read_must_be_low_risk")
    return PolicyDecision(allowed=True)


async def _health_read(request: CapabilityRequest) -> Mapping[str, Any]:
    from api.routes.health import _check_database, _check_redis

    database, cache = await _check_database(), await _check_redis()
    return {
        "capability": request.capability.name,
        "tenant_id": request.context.tenant_id,
        "services": {"database": database, "cache": cache},
        "verified": database in {"healthy", "unhealthy"} and cache in {"healthy", "unhealthy", "not_configured"},
    }


def register_core_capabilities() -> None:
    """Register only capabilities that have a canonical gateway contract."""
    if HEALTH_CAPABILITY in circle_registry.capabilities():
        return
    circle_registry.register_handler(HEALTH_CAPABILITY, _health_read)
    circle_registry.set_policy_evaluator(_policy)


async def execute_capability(
    *,
    actor_id: str,
    tenant_id: str,
    source: str,
    capability: str = HEALTH_CAPABILITY,
    payload: Mapping[str, Any] | None = None,
) -> ExecutionResult:
    register_core_capabilities()
    request = CapabilityRequest(
        capability=CapabilityRef(
            name=capability,
            owner_circle=CircleName.GATEWAY,
            risk_level=RiskLevel.LOW,
        ),
        context=ExecutionContext(actor_id=actor_id, tenant_id=tenant_id),
        payload={"source": source, **(payload or {})},
    )
    return await circle_registry.dispatch(request)
