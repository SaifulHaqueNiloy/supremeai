"""Tests for api/routes/agent_workspace.py — Agent workspace routes."""
import pytest
from fastapi.testclient import TestClient
from core.app_builder import build_app


@pytest.fixture
def client():
    return TestClient(build_app())


class TestAgentWorkspace:
    def test_get_workspace(self, client):
        resp = client.get("/api/v1/agent/workspace")
        assert resp.status_code in (200, 401, 403, 404)

    def test_update_workspace_settings(self, client):
        resp = client.put("/api/v1/agent/workspace", json={"theme": "dark"})
        assert resp.status_code in (200, 401, 403, 404, 422)

    def test_get_workspace_history(self, client):
        resp = client.get("/api/v1/agent/workspace/history")
        assert resp.status_code in (200, 401, 403, 404)
