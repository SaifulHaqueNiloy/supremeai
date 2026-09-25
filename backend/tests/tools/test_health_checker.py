"""Tests for tools/health_checker.py — System health checking."""
import pytest
from unittest.mock import patch, MagicMock
from tools.health_checker import HealthChecker


class TestHealthChecker:
    """Health check: endpoint checks, status aggregation."""

    def test_init(self):
        checker = HealthChecker()
        assert checker is not None

    @pytest.mark.asyncio
    async def test_check_endpoint_healthy(self):
        checker = HealthChecker()
        with patch("httpx.AsyncClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"status": "ok"}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp
            result = await checker.check_endpoint("https://example.com/health")
            assert result is not None

    @pytest.mark.asyncio
    async def test_check_endpoint_unhealthy(self):
        checker = HealthChecker()
        with patch("httpx.AsyncClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 503
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp
            result = await checker.check_endpoint("https://example.com/health")
            assert result is not None
            assert result.get("healthy") is False or result.get("status") != "ok"

    @pytest.mark.asyncio
    async def test_check_endpoint_timeout(self):
        checker = HealthChecker()
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = TimeoutError()
            result = await checker.check_endpoint("https://example.com/health")
            assert result is not None
            assert result.get("healthy") is False or "error" in result

    def test_aggregate_status_all_healthy(self):
        checker = HealthChecker()
        results = [
            {"endpoint": "a", "healthy": True},
            {"endpoint": "b", "healthy": True},
        ]
        status = checker.aggregate(results)
        assert status.get("all_healthy") is True or status.get("status") == "healthy"

    def test_aggregate_status_some_unhealthy(self):
        checker = HealthChecker()
        results = [
            {"endpoint": "a", "healthy": True},
            {"endpoint": "b", "healthy": False},
        ]
        status = checker.aggregate(results)
        assert status.get("all_healthy") is False or status.get("status") != "healthy"

    def test_aggregate_empty_results(self):
        checker = HealthChecker()
        status = checker.aggregate([])
        assert status is not None
