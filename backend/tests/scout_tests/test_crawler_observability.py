"""Unit tests for Crawler Observability, Telemetry, and Admin API endpoints."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.routes.crawler_admin import router
from scout.models import CrawlEventType
from scout.telemetry import CrawlerTelemetry

app = FastAPI()
app.include_router(router)


def test_crawler_telemetry_emit() -> None:
    telemetry = CrawlerTelemetry(tenant_id="tenant-123", task_id="task-abc")
    # Emit info and error events - verify no exception is raised
    telemetry.emit_event(
        CrawlEventType.NAV_START, "Navigating to test site", metadata={"url": "https://example.com"}
    )
    telemetry.emit_event(
        CrawlEventType.ERROR, "Encountered 500 error", severity="ERROR", metadata={"status": 500}
    )


@pytest.mark.asyncio
async def test_crawler_admin_api_policy_crud() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Get default policies
        resp = await client.get("/api/v1/admin/crawler/policies?tenant_id=tenant-test")
        assert resp.status_code == 200
        policies = resp.json()
        assert len(policies) >= 1

        # 2. Create custom policy
        create_payload = {
            "name": "Custom Restricted Policy",
            "is_active": True,
            "max_depth": 3,
            "max_results": 15,
            "default_rate_limit_per_min": 45,
            "allowed_domains": ["example.org"],
            "domain_rules": [
                {
                    "domain": "example.org",
                    "trust_level": "trusted",
                    "rate_limit_per_min": 60,
                    "render_js": False,
                }
            ],
        }
        create_resp = await client.post(
            "/api/v1/admin/crawler/policies?tenant_id=tenant-test", json=create_payload
        )
        assert create_resp.status_code == 201
        new_pol = create_resp.json()
        assert new_pol["name"] == "Custom Restricted Policy"
        assert new_pol["max_depth"] == 3


@pytest.mark.asyncio
async def test_crawler_admin_api_history_and_events() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Query history
        hist_resp = await client.get("/api/v1/admin/crawler/history?tenant_id=tenant-test")
        assert hist_resp.status_code == 200
        assert isinstance(hist_resp.json(), list)

        # Query events
        events_resp = await client.get("/api/v1/admin/crawler/events?task_id=task-123")
        assert events_resp.status_code == 200
        events = events_resp.json()
        assert len(events) == 1
        assert events[0]["task_id"] == "task-123"
