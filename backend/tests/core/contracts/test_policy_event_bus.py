import pytest

from backend.core.contracts.canonical import EventEnvelope, ExecutionContext, PolicyDecision
from backend.core.contracts.event_bus import EventBus
from backend.core.contracts.policy import PolicyEvaluator


def ctx(tenant="t1"):
    return ExecutionContext(
        tenant_id=tenant,
        actor_id="a1",
        workspace_id="w1",
        correlation_id="c1",
        idempotency_key="k1",
        capability="task.execute",
    )


def test_policy_requires_approval_for_missing_permission():
    result = PolicyEvaluator().evaluate(
        capability_id="cap.deploy",
        actor_id="a1",
        tenant_id="t1",
        required_permissions=("deploy",),
    )
    assert result.decision is PolicyDecision.REQUIRE_APPROVAL


def test_policy_denies_rule_and_allows_granted_permission():
    denied = PolicyEvaluator({"cap.delete": lambda actor, tenant: False}).evaluate(
        capability_id="cap.delete", actor_id="a1", tenant_id="t1"
    )
    allowed = PolicyEvaluator().evaluate(
        capability_id="cap.read", actor_id="a1", tenant_id="t1", required_permissions=("read",), granted_permissions=frozenset({"read"})
    )
    assert denied.decision is PolicyDecision.DENY
    assert allowed.decision is PolicyDecision.ALLOW


def test_event_bus_namespaces_and_filters_by_tenant():
    bus = EventBus()
    bus.publish(EventEnvelope("run.completed", ctx("t1"), {"ok": True}))
    bus.publish(EventEnvelope("run.completed", ctx("t2"), {"ok": True}))
    assert len(bus.tenant_events("t1")) == 1
    with pytest.raises(ValueError):
        bus.publish(EventEnvelope("invalid", ctx(), {}))
