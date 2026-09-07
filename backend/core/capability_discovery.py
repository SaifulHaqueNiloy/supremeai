from __future__ import annotations

from core.capability_activation import capability_activation_store
from core.circles.contracts import CapabilityRef
from core.circles.registry import circle_registry


def discover_capability(capability: str, tenant_id: str) -> dict[str, object] | None:
    """Return one canonical, tenant-aware capability description."""
    reference: CapabilityRef | None = circle_registry.describe(capability)
    if reference is None:
        return None
    return {
        "name": reference.name,
        "circle": reference.owner_circle.value,
        "risk": reference.risk_level.value,
        "approval_required": reference.approval_required,
        "enabled": capability_activation_store.is_enabled(
            tenant_id,
            reference.name,
            core=not reference.tenant_activation_required,
        ),
        "version": reference.version,
    }


def discover_capabilities(tenant_id: str) -> tuple[dict[str, object], ...]:
    return tuple(
        description
        for capability in circle_registry.capabilities()
        if (description := discover_capability(capability, tenant_id)) is not None
    )
