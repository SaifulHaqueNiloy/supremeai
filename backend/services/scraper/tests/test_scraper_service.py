"""Tests for SupremeAI Scraper Microservice."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def test_health_check(client):
    """GET /health should return healthy status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "supremeai-scraper"
    assert "playwright_available" in data


def test_scrape_invalid_url_rejected(client):
    """SSRF protection should block localhost URLs."""
    resp = client.post("/scrape", json={"url": "http://127.0.0.1:8081/admin"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "SSRF" in data["error"]


def test_scrape_empty_url_rejected(client):
    """Empty URL should return 400."""
    resp = client.post("/scrape", json={"url": ""})
    assert resp.status_code == 400


def test_browse_ssrf_blocked(client):
    """Browse endpoint should also enforce SSRF protection."""
    resp = client.post("/browse", json={"url": "http://localhost:5432", "action": "fetch"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "SSRF" in data["error"]
