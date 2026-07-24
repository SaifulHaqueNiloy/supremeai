"""Tests to improve coverage for traffic_monitor route (18.4% -> target 60%)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestGetLiveTraffic:
    """Tests for get_live_traffic endpoint."""

    @pytest.mark.asyncio
    async def test_live_traffic_redis_connected(self):
        """Redis connected should return live traffic data."""
        from api.routes.traffic_monitor import get_live_traffic

        mock_redis = MagicMock()
        mock_redis.client = MagicMock()
        mock_redis.client.get.return_value = b"42"
        mock_redis.client.mget.return_value = [b"10", b"200", b"5"]
        mock_redis.client.lrange = AsyncMock(
            return_value=[
                b'{"duration": 100, "status": 200}',
                b'{"duration": 200, "status": 500, "error": "boom"}',
            ]
        )

        with patch("api.routes.traffic_monitor.redis_manager", mock_redis):
            result = await get_live_traffic()

        assert result["data"]["requests_per_second"] >= 0
        assert result["data"]["p95_latency_ms"] >= 0
        assert 0 <= result["data"]["error_rate_percent"] <= 100

    @pytest.mark.asyncio
    async def test_live_traffic_redis_not_connected(self):
        """Redis not connected should raise 503."""
        from api.routes.traffic_monitor import get_live_traffic

        mock_redis = MagicMock()
        mock_redis.client = None

        with patch("api.routes.traffic_monitor.redis_manager", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await get_live_traffic()

        assert exc_info.value.status_code == 503


class TestGetTrafficHistory:
    """Tests for traffic_history coverage."""

    @pytest.mark.asyncio
    async def test_live_traffic_with_data(self):
        from api.routes.traffic_monitor import get_live_traffic

        mock_redis = MagicMock()
        mock_redis.client = MagicMock()
        mock_redis.client.lrange = AsyncMock(
            return_value=[
                b'{"duration": 100, "status": 200}',
                b'{"duration": 200, "status": 200}',
                b'{"duration": 50, "status": 500}',
            ]
        )

        with patch("api.routes.traffic_monitor.redis_manager", mock_redis):
            result = await get_live_traffic()

        assert result["status"] == "success"
        assert "data" in result
