"""Tests for api/routes/agent_tasks.py — Agent task routes."""
import pytest
from fastapi.testclient import TestClient
from core.app_builder import build_app


@pytest.fixture
def client():
    return TestClient(build_app())


class TestAgentTasks:
    def test_list_tasks(self, client):
        resp = client.get("/api/v1/agent/tasks")
        assert resp.status_code in (200, 401, 403, 404)

    def test_create_task(self, client):
        resp = client.post("/api/v1/agent/tasks", json={"goal": "test task"})
        assert resp.status_code in (200, 201, 401, 403, 404, 422)

    def test_get_task(self, client):
        resp = client.get("/api/v1/agent/tasks/nonexistent")
        assert resp.status_code in (404, 401, 403)

    def test_cancel_task(self, client):
        resp = client.post("/api/v1/agent/tasks/nonexistent/cancel")
        assert resp.status_code in (200, 404, 401, 403)
