"""Contract tests for the canonical capability boundaries."""

from pathlib import Path


def test_control_plane_registry_declares_all_runtime_services():
    source = Path("backend/core/service_registry.py").read_text()
    for service in ("core-api", "async-worker", "scraper", "mcp-control-plane"):
        assert f'"{service}"' in source


def test_worker_exposes_task_lifecycle_routes():
    source = Path("backend/worker_service.py").read_text()
    assert '@app.post("/tasks")' in source
    assert '@app.get("/tasks/{task_id}")' in source
    assert '@app.post("/tasks/{task_id}/cancel")' in source


def test_scraper_boundaries_apply_ssrf_validation():
    source = Path("backend/api/routes/scraper.py").read_text()
    assert source.count("is_safe_url(request.url)") >= 2


def test_frontend_mcp_connector_uses_authenticated_client():
    source = Path("frontend/src/components/plugins/MCPConnector.tsx").read_text()
    assert "apiClient.post" in source
    assert "fetch('/api/v1/mcp/discover'" not in source
    assert "any[]" not in source
