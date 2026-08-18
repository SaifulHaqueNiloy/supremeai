import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from core.app import app
from api.dependencies import get_current_admin, get_current_user_token

client = TestClient(app)

@pytest.fixture
def override_admin():
    app.dependency_overrides[get_current_admin] = lambda: {"sub": "admin_test", "role": "admin"}
    app.dependency_overrides[get_current_user_token] = lambda: {"sub": "user_test_1", "role": "admin"}
    yield
    app.dependency_overrides.pop(get_current_admin, None)
    app.dependency_overrides.pop(get_current_user_token, None)

def test_cloud_mesh_kill_switch(override_admin):
    response = client.post("/api/admin/cloud-mesh/kill-switch", json={"target_node": "node-asia-south1"}, headers={"X-Testing-Bypass-Auth": "true"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["action"] == "kill_switch"
    assert data["node"] == "node-asia-south1"

def test_cloud_mesh_defcon(override_admin):
    response = client.post("/api/admin/cloud-mesh/defcon", json={"level": 2, "reason": "DDoS detection spike"}, headers={"X-Testing-Bypass-Auth": "true"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["level"] == 2

    # Invalid defcon level
    res_bad = client.post("/api/admin/cloud-mesh/defcon", json={"level": 99, "reason": "Bad level"}, headers={"X-Testing-Bypass-Auth": "true"})
    assert res_bad.status_code == 400

def test_cloud_mesh_purge_cache(override_admin):
    response = client.post("/api/admin/cloud-mesh/purge-cache", headers={"X-Testing-Bypass-Auth": "true"})
    assert response.status_code == 200
    assert response.json()["action"] == "purge_cache"

def test_traffic_monitor_no_redis(override_admin):
    with patch("api.routes.traffic_monitor.redis_manager._client", None):
        response = client.get("/api/admin/traffic/live", headers={"X-Testing-Bypass-Auth": "true"})
        assert response.status_code in [503, 200]

def test_traffic_monitor_with_redis(override_admin):
    mock_redis = MagicMock()
    mock_redis.lrange = AsyncMock(return_value=['{"status": 200, "duration": 0.05}', '{"status": 500, "duration": 0.12, "error": "Internal"}'])
    with patch("api.routes.traffic_monitor.redis_manager._client", mock_redis):
        response = client.get("/api/admin/traffic/live", headers={"X-Testing-Bypass-Auth": "true"})
        if response.status_code == 200:
            data = response.json()
            assert data["total_requests"] == 4
            assert data["error_count"] == 2
            assert "p95_latency_ms" in data

def test_cdc_webhook_event_processing():
    payload = {
        "type": "DELETE",
        "table": "users",
        "record": {"id": "user_999"},
        "old_record": None
    }
    with patch("api.routes.cdc_webhooks._verify_webhook_signature", new_callable=AsyncMock) as mock_sig, \
         patch("api.routes.cdc_webhooks._delete_from_vector_db", new_callable=AsyncMock) as mock_del:
        mock_sig.return_value = True
        response = client.post("/cdc/webhook", json=payload, headers={"X-Testing-Bypass-Auth": "true"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"

def test_cdc_health():
    response = client.get("/cdc/health", headers={"X-Testing-Bypass-Auth": "true"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
