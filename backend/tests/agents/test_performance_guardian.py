"""Tests for agents/performance_guardian.py — Performance monitoring agent."""
import pytest
from agents.performance_guardian import PerformanceGuardian


class TestPerformanceGuardian:
    """Performance guardian: metrics, thresholds, alerts."""

    def test_init(self):
        guardian = PerformanceGuardian()
        assert guardian is not None

    @pytest.mark.asyncio
    async def test_collect_metrics(self):
        guardian = PerformanceGuardian()
        metrics = await guardian.collect_metrics()
        assert metrics is not None
        assert isinstance(metrics, dict)

    @pytest.mark.asyncio
    async def test_check_thresholds(self):
        guardian = PerformanceGuardian()
        result = await guardian.check_thresholds({"latency_p95": 100, "error_rate": 0.01})
        assert result is not None

    @pytest.mark.asyncio
    async def test_alert_on_breach(self):
        guardian = PerformanceGuardian()
        result = await guardian.check_thresholds({"latency_p95": 10000, "error_rate": 0.5})
        assert result is not None
        assert result.get("breached") is True or len(result.get("alerts", [])) > 0
