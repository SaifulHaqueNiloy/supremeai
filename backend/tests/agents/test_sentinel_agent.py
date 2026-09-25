"""Tests for agents/sentinel_agent.py — Security sentinel agent."""
import pytest
from agents.sentinel_agent import SentinelAgent


class TestSentinelAgent:
    """Sentinel: monitor, alert, investigate."""

    def test_init(self):
        agent = SentinelAgent()
        assert agent is not None

    @pytest.mark.asyncio
    async def test_monitor_returns_status(self):
        agent = SentinelAgent()
        result = await agent.monitor()
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_investigate_alert(self):
        agent = SentinelAgent()
        result = await agent.investigate({"type": "suspicious_activity", "source": "test"})
        assert result is not None

    @pytest.mark.asyncio
    async def test_no_threat_detected(self):
        agent = SentinelAgent()
        result = await agent.monitor()
        assert "threats" in result or "status" in result
