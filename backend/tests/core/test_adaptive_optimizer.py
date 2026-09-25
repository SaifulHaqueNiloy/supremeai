"""Tests for core/adaptive_optimizer.py — Adaptive performance optimizer."""
import pytest
from core.adaptive_optimizer import AdaptiveOptimizer


class TestAdaptiveOptimizer:
    def test_init(self):
        opt = AdaptiveOptimizer()
        assert opt is not None

    @pytest.mark.asyncio
    async def test_analyze_returns_metrics(self):
        opt = AdaptiveOptimizer()
        result = await opt.analyze({"latency": 100, "throughput": 50})
        assert result is not None

    @pytest.mark.asyncio
    async def test_optimize_returns_recommendations(self):
        opt = AdaptiveOptimizer()
        result = await opt.optimize({"bottleneck": "database"})
        assert result is not None
        assert isinstance(result, (list, dict))

    def test_record_metric(self):
        opt = AdaptiveOptimizer()
        opt.record("latency", 150)
        metrics = opt.get_metrics()
        assert "latency" in metrics or len(metrics) > 0

    def test_get_trend(self):
        opt = AdaptiveOptimizer()
        for i in range(10): opt.record("cpu", 50 + i)
        trend = opt.get_trend("cpu")
        assert trend is not None
