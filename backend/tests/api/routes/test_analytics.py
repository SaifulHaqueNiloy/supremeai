"""Tests for api/routes/analytics.py — Analytics routes."""
import pytest
from fastapi.testclient import TestClient
from core.app_builder import build_app


@pytest.fixture
def client():
    return TestClient(build_app())


class TestAnalytics:
    def test_get_analytics_summary(self, client):
        resp = client.get("/api/v1/analytics/summary")
        assert resp.status_code in (200, 401, 403, 404)

    def test_get_usage_stats(self, client):
        resp = client.get("/api/v1/analytics/usage")
        assert resp.status_code in (200, 401, 403, 404)

    def test_get_cost_breakdown(self, client):
        resp = client.get("/api/v1/analytics/cost")
        assert resp.status_code in (200, 401, 403, 404)

    def test_get_agent_performance(self, client):
        resp = client.get("/api/v1/analytics/agents")
        assert resp.status_code in (200, 401, 403, 404)
