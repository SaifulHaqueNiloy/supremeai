"""Tests to improve coverage for traffic_monitor route (18.4% -> target 60%)."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


class TestGetLiveTraffic:
    """Tests for get_live_traffic endpoint."""

    def test_live_traffic_redis_connected(self):
        """Redis connected should return live traffic data."""
        from api.routes.traffic_monitor import get_live_traffic

        mock_redis = MagicMock()
        mock_redis.client = MagicMock()
        mock_redis.client.get.return_value = b"42"
        mock_redis.client.mget.return_value = [b"10", b"200", b"5"]

        with patch("api.routes.traffic_monitor.redis_manager", mock_redis):
            result = get_live_traffic()

        assert "requests_per_second" in result
        assert "p95_latency_ms" in result
        assert "error_rate" in result

    def test_live_traffic_redis_not_connected(self):
        """Redis not connected should raise 503."""
        from api.routes.traffic_monitor import get_live_traffic

        mock_redis = MagicMock()
        mock_redis.client = None

        with patch("api.routes.traffic_monitor.redis_manager", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                get_live_traffic()

        assert exc_info.value.status_code == 503


class TestGetTrafficHistory:
    """Tests for get_traffic_history endpoint."""

    def test_traffic_history_returns_data(self):
        """Should return traffic history data."""
        from api.routes.traffic_monitor import get_traffic_history

        mock_redis = MagicMock()
        mock_redis.client = MagicMock()
        mock_redis.client.lrange.return_value = [
            b'{"timestamp": 1000, "rps": 10}',
            b'{"timestamp": 1060, "rps": 20}',
        ]

        with patch("api.routes.traffic_monitor.redis_manager", mock_redis):
            result = get_traffic_history()

        assert "history" in result
        assert len(result["history"]) == 2

    def test_traffic_history_redis_not_connected(self):
        """Redis not connected should raise 503."""
        from api.routes.traffic_monitor import get_traffic_history

        mock_redis = MagicMock()
        mock_redis.client = None

        with patch("api.routes.traffic_monitor.redis_manager", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                get_traffic_history()

        assert exc_info.value.status_code == 503


class TestGetTrafficAlerts:
    """Tests for get_traffic_alerts endpoint."""

    def test_traffic_alerts_returns_data(self):
        """Should return traffic alerts data."""
        from api.routes.traffic_monitor import get_traffic_alerts

        mock_redis = MagicMock()
        mock_redis.client = MagicMock()
        mock_redis.client.lrange.return_value = [
            b'{"type": "spike", "value": 100}',
        ]

        with patch("api.routes.traffic_monitor.redis_manager", mock_redis):
            result = get_traffic_alerts()

        assert "alerts" in result
        assert len(result["alerts"]) == 1

    def test_traffic_alerts_redis_not_connected(self):
        """Redis not connected should raise 503."""
        from api.routes.traffic_monitor import get_traffic_alerts

        mock_redis = MagicMock()
        mock_redis.client = None

        with patch("api.routes.traffic_monitor.redis_manager", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                get_traffic_alerts()

        assert exc_info.value.status_code == 503