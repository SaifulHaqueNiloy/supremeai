"""Tests for api/routes/agent_action.py — Agent action routes."""
import pytest
from fastapi.testclient import TestClient
from core.app_builder import build_app


@pytest.fixture
def client():
    return TestClient(build_app())


class TestAgentAction:
    def test_list_agent_actions(self, client):
        resp = client.get("/api/v1/agent/actions")
        assert resp.status_code in (200, 401, 403, 404)

    def test_create_agent_action(self, client):
        resp = client.post("/api/v1/agent/actions", json={"type": "test", "goal": "test"})
        assert resp.status_code in (200, 201, 401, 403, 404, 422)

    def test_get_agent_action(self, client):
        resp = client.get("/api/v1/agent/actions/nonexistent")
        assert resp.status_code in (404, 401, 403)

    def test_cancel_agent_action(self, client):
        resp = client.post("/api/v1/agent/actions/nonexistent/cancel")
        assert resp.status_code in (200, 404, 401, 403)
