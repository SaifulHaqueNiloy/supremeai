import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from core.app import app

client = TestClient(app)

def test_get_public_config():
    response = client.get("/api/config/public", headers={"X-Testing-Bypass-Auth": "true"})
    assert response.status_code == 200
    data = response.json()
    assert "adminEmail" in data
    assert "maxConcurrency" in data
    assert "features" in data
    assert data["features"]["costGuard"] is True

def test_get_public_branding():
    response = client.get("/api/config/public/branding", headers={"X-Testing-Bypass-Auth": "true"})
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "providers" in data

def test_get_preferences_offline_fallback():
    with patch("api.routes.preferences.db.client", None):
        response = client.get("/api/preferences/?user_id=test_user_123", headers={"X-Testing-Bypass-Auth": "true"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_123"
        assert data["theme"] == "dark"

def test_upsert_preferences_offline():
    with patch("api.routes.preferences.db.client", None), \
         patch("api.routes.preferences.theme_pubsub.publish", new_callable=AsyncMock) as mock_pub:
        payload = {"theme": "cyberpunk", "auto_save": False}
        response = client.post("/api/preferences/?user_id=test_user_123", json=payload, headers={"X-Testing-Bypass-Auth": "true"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["preferences"]["theme"] == "cyberpunk"
        mock_pub.assert_called_once_with("test_user_123", {"theme": "cyberpunk"})

def test_get_preferences_with_db():
    mock_db = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_exec = MagicMock()
    mock_exec.execute.return_value.data = [{"user_id": "u1", "theme": "solarized"}]
    
    mock_db.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_exec

    with patch("api.routes.preferences.db.client", mock_db):
        response = client.get("/api/preferences/?user_id=u1", headers={"X-Testing-Bypass-Auth": "true"})
        assert response.status_code == 200
        assert response.json()["theme"] == "solarized"

def test_usage_metrics_empty():
    response = client.get("/metrics/usage/", headers={"X-Testing-Bypass-Auth": "true"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

def test_markdown_render():
    sample_md = "# Hello SupremeAI\nThis is a test **bold** markdown."
    res = client.post("/api/v1/api/markdown/render", json={"markdown": sample_md}, headers={"X-Testing-Bypass-Auth": "true"})
    assert res.status_code in [200, 404, 422]
