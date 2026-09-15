from types import SimpleNamespace

import pytest

from backend.ecosystem.runtime_selector import PlacementError, select_placement
from adaptive_engine.capability_registry import CapabilityLifecycleState
from adaptive_engine.resource_registry import ProviderKind, ResourceState


class FakeCapabilityRegistry:
    def find_by_signature(self, signature):
        if signature != "task.execute.v1":
            return None
        return SimpleNamespace(
            capability_id="cap-task",
            signature=signature,
            lifecycle_state=CapabilityLifecycleState.ACTIVE,
        )


class FakeResourceRegistry:
    def __init__(self, resources):
        self.resources = resources

    def list(self, **kwargs):
        return self.resources


def resource(resource_id, state, capabilities, tenant_id=None):
    return SimpleNamespace(
        resource_id=resource_id,
        state=state,
        capabilities=capabilities,
        tenant_id=tenant_id,
        provider=ProviderKind.CUSTOM,
    )


def test_selects_healthy_matching_resource_deterministically():
    placement = select_placement(
        FakeCapabilityRegistry(),
        FakeResourceRegistry(
            [
                resource("res-2", ResourceState.REGISTERED, ["cap-task"]),
                resource("res-1", ResourceState.HEALTHY, ["cap-task"]),
            ]
        ),
        capability_signature="task.execute.v1",
    )
    assert placement.resource.resource_id == "res-1"
    assert placement.capability.capability_id == "cap-task"


def test_rejects_missing_capability_or_resource():
    with pytest.raises(PlacementError, match="capability_not_found"):
        select_placement(FakeCapabilityRegistry(), FakeResourceRegistry([]), capability_signature="missing")

    with pytest.raises(PlacementError, match="resource_unavailable"):
        select_placement(FakeCapabilityRegistry(), FakeResourceRegistry([]), capability_signature="task.execute.v1")
