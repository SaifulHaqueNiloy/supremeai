"""Unit tests for CostGuard enforcement inside TaskRouter.route_and_dispatch.

বাংলা: TaskRouter-এর রাউট-এন্ড-ডিসপ্যাচে CostGuard বাজেট গেট ঠিকমতো কাজ করছে কিনা যাচাই করা হচ্ছে।
"""

import pytest

from core.queue.task_router import TaskRouter


@pytest.fixture
def router():
    return TaskRouter()


@pytest.mark.asyncio
async def test_route_rejected_when_budget_exceeded(monkeypatch, router):
    """Non-free tier with exhausted quota must be rejected before execution."""

    async def _reject(tenant_id, tier):
        return False

    monkeypatch.setattr("core.queue.task_router.cost_guard.validate_budget", _reject)

    result = await router.route_and_dispatch(
        {"task_type": "coding", "cost_limit": 0.05, "tenant_id": "acme"}
    )

    assert result["status"] == "rejected"
    assert result["reason"] == "budget_exceeded"
    assert result["tier"] == "economy"
    assert result["tenant_id"] == "acme"


@pytest.mark.asyncio
async def test_route_proceeds_when_budget_ok(monkeypatch, router):
    """When budget is available the task is dispatched to the local executor."""

    async def _allow(tenant_id, tier):
        return True

    monkeypatch.setattr("core.queue.task_router.cost_guard.validate_budget", _allow)

    captured = {}

    async def _fake_execute(code):
        captured["called"] = True
        return {"output": "ok"}

    monkeypatch.setattr(router.local_executor, "execute_local_code", _fake_execute)

    result = await router.route_and_dispatch(
        {"task_type": "coding", "cost_limit": 0.05, "code": "print('hi')"}
    )

    assert captured.get("called") is True
    assert result["output"] == "ok"
    assert result["cost"] == 0.05


@pytest.mark.asyncio
async def test_free_tier_dispatched_when_redis_down(monkeypatch, router):
    """Mirror CostGuard fail-safe: free tier allowed, non-free rejected (Redis down)."""

    async def _fail_safe(tenant_id, tier):
        return tier == "free"

    monkeypatch.setattr("core.queue.task_router.cost_guard.validate_budget", _fail_safe)

    # free tier (zero cost) -> dispatched
    captured = {}

    async def _fake_execute(code):
        captured["called"] = True
        return {"output": "ok"}

    monkeypatch.setattr(router.local_executor, "execute_local_code", _fake_execute)
    free_result = await router.route_and_dispatch(
        {"task_type": "local", "cost_limit": 0.0, "code": "print('hi')"}
    )
    assert free_result["output"] == "ok"
    assert captured.get("called") is True

    # economy tier (Redis down) -> rejected
    econ_result = await router.route_and_dispatch(
        {"task_type": "coding", "cost_limit": 0.05, "tenant_id": "acme"}
    )
    assert econ_result["status"] == "rejected"
    assert econ_result["tier"] == "economy"
