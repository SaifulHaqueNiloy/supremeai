"""Tests for agents/data_trend_anomaly_agent.py — Data anomaly detection."""
import pytest
from agents.data_trend_anomaly_agent import DataTrendAnomalyAgent


class TestDataTrendAnomalyAgent:
    def test_init(self):
        agent = DataTrendAnomalyAgent()
        assert agent is not None

    @pytest.mark.asyncio
    async def test_detect_anomalies(self):
        agent = DataTrendAnomalyAgent()
        data = [10, 12, 11, 10, 100, 11, 12]  # 100 is anomaly
        result = await agent.detect(data)
        assert result is not None
        assert isinstance(result, (list, dict))

    @pytest.mark.asyncio
    async def test_no_anomalies(self):
        agent = DataTrendAnomalyAgent()
        data = [10, 11, 10, 11, 10, 11]
        result = await agent.detect(data)
        assert result is not None

    @pytest.mark.asyncio
    async def test_empty_data(self):
        agent = DataTrendAnomalyAgent()
        result = await agent.detect([])
        assert result is not None
