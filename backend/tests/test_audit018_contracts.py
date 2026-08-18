# backend/tests/test_audit018_contracts.py
import pytest
from fastapi.testclient import TestClient
from core.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_skills_catalog_endpoint(client):
    """Verify /api/skills/catalog endpoint responds properly."""
    response = client.get("/api/skills/catalog", headers={"Authorization": "Bearer mock-admin-token"})
    # Either returns list of skills or empty list (200 OK)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_skills_search_endpoint(client):
    """Verify /api/skills/search endpoint responds properly."""
    response = client.post(
        "/api/skills/search?query=test",
        headers={"Authorization": "Bearer mock-admin-token"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_voice_voices_endpoint(client):
    """Verify /api/voice/voices endpoint exists and does not return 404."""
    response = client.get("/api/voice/voices", headers={"Authorization": "Bearer mock-admin-token"})
    # It will either return voice list (200) or fallback (502 if external voice API down), but NEVER 404
    assert response.status_code in [200, 502]
