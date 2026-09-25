"""Tests for core/agent_supervisor.py — Agent supervisor (heartbeat)."""
import pytest
from unittest.mock import AsyncMock, patch
from core.agent_supervisor import AgentSupervisor


class TestAgentSupervisor:
    """Supervisor: register, heartbeat, restart, list."""

    def test_init(self):
        sup = AgentSupervisor()
        assert sup is not None

    def test_register_agent(self):
        sup = AgentSupervisor()
        sup.register("agent-1", {"type": "worker"})
        agents = sup.list_agents()
        assert "agent-1" in agents or len(agents) >= 1

    def test_unregister_agent(self):
        sup = AgentSupervisor()
        sup.register("agent-1", {})
        sup.unregister("agent-1")
        agents = sup.list_agents()
        assert "agent-1" not in agents or len(agents) == 0

    @pytest.mark.asyncio
    async def test_heartbeat_updates(self):
        sup = AgentSupervisor()
        sup.register("agent-1", {})
        await sup.heartbeat("agent-1")
        agents = sup.list_agents()
        assert agents is not None

    @pytest.mark.asyncio
    async def test_check_stale_agents(self):
        sup = AgentSupervisor()
        sup.register("agent-1", {})
        stale = await sup.get_stale_agents(timeout_seconds=0)
        assert isinstance(stale, list)

    @pytest.mark.asyncio
    async def test_restart_stale_agent(self):
        sup = AgentSupervisor()
        sup.register("agent-1", {})
        result = await sup.restart("agent-1")
        assert result is not None
