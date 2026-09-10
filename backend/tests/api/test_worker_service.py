from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError


@pytest.fixture
def worker_app():
    from worker_service import app

    return app


@pytest.mark.asyncio
async def test_liveness_is_process_only(worker_app):
    transport = ASGITransport(app=worker_app)
    async with AsyncClient(transport=transport, base_url="http://worker") as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "supremeai-worker"}


@pytest.mark.asyncio
async def test_readiness_returns_503_when_queue_is_unavailable(worker_app):
    transport = ASGITransport(app=worker_app)
    with patch("worker_service._redis_url", return_value="redis://unavailable"), patch(
        "worker_service._queue_call", side_effect=ConnectionError("offline")
    ):
        async with AsyncClient(transport=transport, base_url="http://worker") as client:
            response = await client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["queue_available"] is False


@pytest.mark.asyncio
async def test_degraded_health_reports_queue_failure(worker_app):
    transport = ASGITransport(app=worker_app)
    with patch("worker_service._redis_url", return_value="redis://unavailable"), patch(
        "worker_service._queue_call", side_effect=ConnectionError("offline")
    ):
        async with AsyncClient(transport=transport, base_url="http://worker") as client:
            response = await client.get("/health/degraded")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"


def test_task_contract_requires_tenant_scope():
    from worker_service import TaskContract

    with pytest.raises(ValidationError):
        TaskContract(goal="run this")


def test_task_contract_validates_scrape_url_and_metadata_size():
    from worker_service import TaskContract

    with pytest.raises(ValidationError):
        TaskContract(tenant_id="tenant-a", goal="scrape", capability="scrape")

    with pytest.raises(ValidationError):
        TaskContract(
            tenant_id="tenant-a",
            goal="large",
            metadata={"payload": "x" * 40_000},
        )


def test_task_contract_accepts_supported_capabilities():
    from worker_service import TaskContract

    contract = TaskContract(
        tenant_id="tenant-a",
        user_id="user-a",
        goal="scrape docs",
        capability="scrape",
        idempotency_key="request-1",
        metadata={"url": "https://example.com"},
    )

    assert contract.tenant_id == "tenant-a"
    assert contract.idempotency_key == "request-1"
