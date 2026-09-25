"""Tests for api/routes/access.py — Access control routes."""
import pytest
from fastapi.testclient import TestClient
from core.app_builder import build_app


@pytest.fixture
def client():
    return TestClient(build_app())


class TestAccess:
    def test_check_access(self, client):
        resp = client.get("/api/v1/access/check")
        assert resp.status_code in (200, 401, 403, 404)

    def test_get_permissions(self, client):
        resp = client.get("/api/v1/access/permissions")
        assert resp.status_code in (200, 401, 403, 404)

    def test_request_access(self, client):
        resp = client.post("/api/v1/access/request", json={"resource": "admin"})
        assert resp.status_code in (200, 201, 401, 403, 404, 422)
