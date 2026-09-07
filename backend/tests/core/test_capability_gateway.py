from __future__ import annotations

import pytest

from core.capability_gateway import HEALTH_CAPABILITY, execute_capability
from core.circles.registry import circle_registry


@pytest.mark.asyncio
async def test_health_capability_uses_canonical_gateway(monkeypatch):
    async def fake_db():
        return "healthy"

    async def fake_cache():
        return "not_configured"

    monkeypatch.setattr("api.routes.health._check_database", fake_db)
    monkeypatch.setattr("api.routes.health._check_redis", fake_cache)

    result = await execute_capability(
        actor_id="user-1",
        tenant_id="tenant-1",
        source="dashboard",
        capability=HEALTH_CAPABILITY,
    )

    assert result.status.value == "succeeded"
    assert result.data["verified"] is True
    assert result.data["services"]["database"] == "healthy"
    assert result.verification is not None
    assert result.verification.verified is True
    assert result.audit is not None
    assert result.audit.event_type == "capability.succeeded"


@pytest.mark.asyncio
async def test_unknown_capability_is_unavailable():
    result = await execute_capability(
        actor_id="user-1",
        tenant_id="tenant-1",
        source="chat",
        capability="unknown.capability",
    )

    assert result.status.value == "unavailable"
    assert "capability" in result.error_code


def test_gateway_has_single_registered_health_handler():
    assert HEALTH_CAPABILITY in circle_registry.capabilities()
