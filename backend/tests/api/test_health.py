"""Health route (api/routes/health.py) এর ইউনিট টেস্ট।

বাংলা: হেলথ রাউটার সরাসরি একটি মিনিমাল FastAPI অ্যাপে মাউন্ট করে TestClient দিয়ে
লাইভনেস/রেডিনেস/হেলথ চেক কভার করা হয়েছে। redis_manager ও registry মক করা হয়েছে।
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_client():
    from api.routes.health import router

    app = FastAPI()
    app.include_router(router)
    return app


def test_health_live_returns_alive():
    client = TestClient(_build_client())
    resp = client.get("/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


def test_health_ready_returns_ok():
    client = TestClient(_build_client())
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["service"] == "supremeai-backend"


def test_health_check_ok_without_subsystems():
    # বাংলা: app.state-এ db_pool/redis সাবসিস্টেম না থাকলে 'degraded' ফেরত দেওয়া উচিত (কিন্তু HTTP 200)
    client = TestClient(_build_client())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "degraded"


def test_health_agents_requires_registry():
    # বাংলা: registry-এ redis_manager না থাকলে graceful error ফেরত দেওয়া উচিত
    client = TestClient(_build_client())
    with patch("api.routes.health.registry") as reg:
        reg.get.side_effect = KeyError("redis_manager")
        resp = client.post("/health/agents", json={"agent_ids": ["a1"]})
        assert resp.status_code == 200
        assert "error" in resp.json()
