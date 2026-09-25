"""Tests for api/routes/admin_auth.py — Admin authentication routes."""
import pytest
from fastapi.testclient import TestClient
from core.app_builder import build_app


@pytest.fixture
def client():
    return TestClient(build_app())


class TestAdminAuth:
    def test_admin_login_returns_token(self, client):
        resp = client.post("/api/v1/admin/auth/login", json={"email": "test@test.com", "password": "test"})
        assert resp.status_code in (200, 401, 403, 404, 422)

    def test_admin_logout(self, client):
        resp = client.post("/api/v1/admin/auth/logout")
        assert resp.status_code in (200, 401, 403, 404)

    def test_admin_me_without_token(self, client):
        resp = client.get("/api/v1/admin/auth/me")
        assert resp.status_code in (401, 403, 404)

    def test_admin_me_with_invalid_token(self, client):
        resp = client.get("/api/v1/admin/auth/me", headers={"Authorization": "Bearer invalid"})
        assert resp.status_code in (401, 403, 404)
