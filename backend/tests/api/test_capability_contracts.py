"""Contract tests for the canonical capability boundaries."""

from pathlib import Path

# বাংলা মন্তব্য: pytest CI-তে cwd `backend/` (দেখুন ci.yml: working-directory: ./backend),
# কিন্তু লোকাল ডেভে রুট থেকেও চলতে পারে -- তাই __file__ থেকে repo root বের করা হচ্ছে,
# হার্ডকোডেড "backend/..." প্রিফিক্স আর ধরে নেওয়া হচ্ছে না।
_REPO_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = _REPO_ROOT / "backend"


def test_control_plane_registry_declares_all_runtime_services():
    source = (_BACKEND_ROOT / "core/service_registry.py").read_text()
    for service in ("core-api", "async-worker", "scraper", "mcp-control-plane"):
        assert f'"{service}"' in source


def test_worker_exposes_task_lifecycle_routes():
    source = (_BACKEND_ROOT / "worker_service.py").read_text()
    assert '@app.post("/tasks")' in source
    assert '@app.get("/tasks/{task_id}")' in source
    assert '@app.post("/tasks/{task_id}/cancel")' in source


def test_scraper_boundaries_apply_ssrf_validation():
    source = (_BACKEND_ROOT / "api/routes/scraper.py").read_text()
    assert source.count("is_safe_url(request.url)") >= 2


def test_frontend_mcp_connector_uses_authenticated_client():
    # বাংলা মন্তব্য: #228 (smooth controlled MCP connector flow) MCPConnector.tsx-এর
    # ইনলাইন fetch কল সরিয়ে services/controlPlane.ts-এর getJson/postJson/deleteJson
    # হেল্পারে সরিয়ে নিয়েছে -- সবগুলোই getAuthHeaders() দিয়ে authenticated। তাই এই
    # কন্ট্রাক্ট টেস্ট এখন component-এর বদলে সার্ভিস লেয়ার যাচাই করে।
    component_source = (_REPO_ROOT / "frontend/src/components/plugins/MCPConnector.tsx").read_text()
    service_source = (_REPO_ROOT / "frontend/src/services/controlPlane.ts").read_text()
    assert "controlPlane." in component_source
    assert "fetch('/api/v1/mcp/discover'" not in component_source
    assert "fetch('/api/v1/mcp/discover'" not in service_source
    assert "any[]" not in component_source
    assert "any[]" not in service_source
    assert "getAuthHeaders" in service_source
    for helper in (
        "async function getJson",
        "async function postJson",
        "async function deleteJson",
    ):
        assert helper in service_source
    assert "revokeExternalClient: (id: string) => deleteJson" in service_source
