"""Route tests for the Self-Evolving Memory API (BLUEPRINT-MEM-001 / Phase 5 M5.1).

বাংলা মন্তব্য: এন্ডপয়েন্টগুলো অ্যাডমিন-টোকেন দিয়ে সুরক্ষিত এবং ডিফল্টে non-destructive
(dry_run) — এই টেস্ট সেই দুইটি নিশ্চয়তা ও রেসপন্স শেপ যাচাই করে।
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.routes.self_evolve import require_admin_token
from core.app import app

client = TestClient(app)

_BASE = "/api/self-evolve"


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    """Bypass the admin-token gate only (settings.supremeai_api_token is a read-only secret)."""
    app.dependency_overrides[require_admin_token] = lambda: True
    try:
        yield {"X-Admin-Token": "test-admin-token"}
    finally:
        app.dependency_overrides.pop(require_admin_token, None)


def test_endpoints_require_admin_token():
    assert client.get(f"{_BASE}/clusters").status_code == 401
    assert client.get(f"{_BASE}/decay-report").status_code == 401
    assert client.post(f"{_BASE}/deduplicate", json={}).status_code == 401
    assert client.get(f"{_BASE}/auto-loop/status").status_code == 401


def test_decay_report_shape(admin_headers):
    response = client.get(f"{_BASE}/decay-report?limit=5", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert "count" in body
    assert isinstance(body["scores"], list)
    for score in body["scores"]:
        assert 0.0 <= score["retention"] <= 1.0
        assert "stability_days" in score


def test_deduplicate_defaults_to_dry_run(admin_headers):
    response = client.post(f"{_BASE}/deduplicate", json={}, headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert body["merged_count"] == 0
    assert isinstance(body["groups"], list)


def test_decay_prune_defaults_to_dry_run(admin_headers):
    response = client.post(f"{_BASE}/decay-prune", json={}, headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert isinstance(body["removed_ids"], list)


def test_decay_prune_rejects_invalid_threshold(admin_headers):
    response = client.post(
        f"{_BASE}/decay-prune", json={"retention_threshold": 1.5}, headers=admin_headers
    )
    assert response.status_code == 422


def test_hierarchical_search_reports_scan_stats(admin_headers):
    response = client.post(
        f"{_BASE}/search",
        json={"query": "memory evolution", "n_results": 3},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["docs_scanned"] <= body["docs_total"]
    assert isinstance(body["matches"], list)
    assert len(body["matches"]) <= 3


def test_search_requires_non_empty_query(admin_headers):
    response = client.post(f"{_BASE}/search", json={"query": ""}, headers=admin_headers)
    assert response.status_code == 422


def test_auto_loop_status_reports_config(admin_headers):
    response = client.get(f"{_BASE}/auto-loop/status", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["running"] is False
    assert body["interval_seconds"] >= 30
    assert "merge_duplicates" in body["config"]
    assert "cycles" in body["stats"]


def test_reorganize_is_non_destructive_by_default(admin_headers):
    # max_age_days is set far beyond any real memory's age so this test can never
    # prune data from the shared dev store — it only asserts the opt-in defaults.
    response = client.post(
        f"{_BASE}/reorganize", json={"max_age_days": 36500}, headers=admin_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["merged"] == 0
    assert body["decay_pruned"] == 0
    assert body["pruned"] == 0
    assert body["clusters_persisted"] == 0
    assert body["duration_ms"] >= 0
