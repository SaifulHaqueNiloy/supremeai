"""Full-coverage tests for api/routes/browser_routes.py (Task 7-c).

Strategy:
    - Minimal FastAPI app mounting ONLY browser_routes.router (prefix
      /api/browser, admin-guarded — satisfied by the conftest auth bypass).
    - SSRFProtection.validate_url is patched at class level with a
      deterministic host-based decision (the real one does DNS lookups).
    - LLM gateway, Playwright browser and unified memory are patched.
    - No real network anywhere.
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlparse

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import api.routes.browser_routes as br
from core.security.protection.ssrf_protection import SSRFValidationResult

PUBLIC_URL = "https://example.com/page"
BLOCKED_URL = "http://169.254.169.254/latest/meta-data"


def fake_validate_url(self, url: str) -> SSRFValidationResult:
    host = (urlparse(url).hostname or "").lower()
    blocked = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "169.254.169.254",
        "10.0.0.1",
        "192.168.1.1",
        "metadata.google.internal",
    }
    if not host or host in blocked or host.endswith(".internal"):
        return SSRFValidationResult(is_safe=False, reason="internal target", validated_url=url)
    return SSRFValidationResult(is_safe=True, reason="OK", validated_url=url)


class FakeLLMResult:
    text = "AI analysis text"
    model = "test-model"
    tokens_used = 42


@pytest_asyncio.fixture
async def browser_env(monkeypatch):
    app = FastAPI()
    app.include_router(br.router)

    monkeypatch.setattr(
        "core.security.protection.ssrf_protection.SSRFProtection.validate_url",
        fake_validate_url,
    )

    llm_calls: list[dict[str, Any]] = []

    async def fake_acompletion(**kwargs):
        llm_calls.append(kwargs)
        return FakeLLMResult()

    monkeypatch.setattr("core.llm.llm_gateway.llm_gateway.acompletion", fake_acompletion)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http, llm_calls

    app.dependency_overrides.clear()


@pytest.mark.unit
class TestAIAction:
    async def test_summarize_success(self, browser_env):
        http, llm_calls = browser_env
        resp = await http.post(
            "/api/browser/ai-action",
            json={"action": "summarize", "url": PUBLIC_URL, "context": "hello page"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["response"] == "AI analysis text"
        assert body["action"] == "summarize"
        assert body["metadata"]["model_used"] == "test-model"
        assert body["metadata"]["context_length"] == len("hello page")
        assert llm_calls[0]["context"].task_type == "browser_ai_action"

    async def test_all_actions_map_to_prompts(self, browser_env):
        http, llm_calls = browser_env
        for action in ("explain", "extract_links", "find_issues"):
            resp = await http.post(
                "/api/browser/ai-action",
                json={"action": action, "url": PUBLIC_URL, "context": "ctx"},
            )
            assert resp.status_code == 200
        interact = await http.post(
            "/api/browser/ai-action",
            json={
                "action": "interact",
                "url": PUBLIC_URL,
                "payload": {"question": "what is this?"},
            },
        )
        assert interact.status_code == 200
        unknown = await http.post(
            "/api/browser/ai-action",
            json={"action": "mystery", "url": PUBLIC_URL},
        )
        assert unknown.status_code == 200  # falls back to summarize prompt
        assert len(llm_calls) == 5

    async def test_ssrf_blocked_403(self, browser_env):
        http, _ = browser_env
        resp = await http.post(
            "/api/browser/ai-action",
            json={"action": "summarize", "url": BLOCKED_URL},
        )
        assert resp.status_code == 403
        assert "not allowed" in resp.json()["detail"]

    async def test_llm_failure_503(self, browser_env, monkeypatch):
        http, _ = browser_env

        async def boom(**kwargs):
            raise RuntimeError("llm exploded")

        monkeypatch.setattr("core.llm.llm_gateway.llm_gateway.acompletion", boom)
        resp = await http.post(
            "/api/browser/ai-action",
            json={"action": "summarize", "url": PUBLIC_URL},
        )
        assert resp.status_code == 503
        assert "temporarily unavailable" in resp.json()["detail"]

    async def test_llm_gateway_import_failure_fallback(self, browser_env, monkeypatch):
        http, _ = browser_env
        with monkeypatch.context() as m:
            m.setitem(__import__("sys").modules, "core.llm.llm_gateway", None)
            resp = await http.post(
                "/api/browser/ai-action",
                json={"action": "explain", "url": PUBLIC_URL},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["metadata"] == {"mode": "fallback"}
        assert "Technical Analysis" in body["response"]


@pytest.mark.unit
class TestSecurityScan:
    async def test_invalid_url_400(self, browser_env):
        http, _ = browser_env
        resp = await http.post("/api/browser/security-scan", json={"url": "not-a-url"})
        assert resp.status_code == 400

    async def test_ssrf_blocked_403(self, browser_env):
        http, _ = browser_env
        resp = await http.post("/api/browser/security-scan", json={"url": BLOCKED_URL})
        assert resp.status_code == 403

    async def test_scan_with_external_checks(self, browser_env, monkeypatch):
        http, _ = browser_env

        async def fake_ssl(url):
            return 70, [
                br.SecurityIssue(
                    severity="high",
                    category="SSL/TLS",
                    message="not https",
                    remediation="enable TLS",
                )
            ]

        async def fake_headers(url):
            return 100, [
                br.SecurityIssue(severity="low", category="Security Headers", message="missing x")
            ]

        monkeypatch.setattr(br, "check_ssl_security", fake_ssl)
        monkeypatch.setattr(br, "check_security_headers", fake_headers)

        resp = await http.post(
            "/api/browser/security-scan",
            json={"url": "http://example.com/x", "deep_scan": True},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        # high (-15) + low (-3) = 82
        assert body["score"] == 82
        assert body["checks_performed"] == [
            "ssl_validation",
            "security_headers",
            "ssrf_check",
            "vulnerability_patterns",
        ]
        assert body["scan_url"].startswith("http://example.com")

    async def test_deep_scan_url_vulnerability_patterns(self, browser_env, monkeypatch):
        http, _ = browser_env

        async def clean_ssl(url):
            return 100, []

        async def clean_headers(url):
            return 100, []

        monkeypatch.setattr(br, "check_ssl_security", clean_ssl)
        monkeypatch.setattr(br, "check_security_headers", clean_headers)
        resp = await http.post(
            "/api/browser/security-scan",
            json={"url": "https://example.com/?q=<script>alert(1)</script>", "deep_scan": True},
        )
        assert resp.status_code == 200
        body = resp.json()
        patterns = [i for i in body["issues"] if i["category"] == "Vulnerability Pattern"]
        assert patterns and "XSS" in patterns[0]["message"]
        assert body["score"] == 85  # one high pattern

    async def test_scan_unexpected_error_503(self, browser_env, monkeypatch):
        http, _ = browser_env

        async def broken_ssl(url):
            raise RuntimeError("ssl checker crashed")

        monkeypatch.setattr(br, "check_ssl_security", broken_ssl)
        resp = await http.post("/api/browser/security-scan", json={"url": PUBLIC_URL})
        assert resp.status_code == 503


@pytest.mark.unit
class TestScreenshot:
    async def test_screenshot_success(self, browser_env, monkeypatch):
        http, _ = browser_env

        class FakePage:
            async def goto(self, url, **kwargs):
                self.goto_url = url

            async def evaluate(self, script):
                pass

            async def wait_for_timeout(self, ms):
                pass

            async def screenshot(self, **kwargs):
                return b"FAKEPNG"

            async def close(self):
                pass

        captured: dict[str, Any] = {}

        class FakeBrowser:
            async def new_page(self, viewport=None):
                captured["viewport"] = viewport
                return FakePage()

        async def fake_browser():
            return FakeBrowser()

        monkeypatch.setattr("core.playwright_manager.get_global_browser", fake_browser)

        resp = await http.post(
            "/api/browser/screenshot",
            json={"url": PUBLIC_URL, "width": 800, "height": 600, "full_page": True},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert "screenshot_" in resp.headers["content-disposition"]
        assert resp.headers["x-screenshot-url"] == PUBLIC_URL
        assert captured["viewport"] == {"width": 800, "height": 600}

    async def test_screenshot_ssrf_blocked(self, browser_env):
        http, _ = browser_env
        resp = await http.post("/api/browser/screenshot", json={"url": "http://localhost:8080"})
        # CURRENT BEHAVIOUR NOTE: the SSRF gate raises HTTPException(403) but
        # the screenshot handler's blanket ``except Exception`` converts it
        # into a 500 — the 403 is masked (documented as a source finding).
        assert resp.status_code == 500
        assert "not allowed" in resp.json()["detail"]

    async def test_screenshot_playwright_failure_500(self, browser_env, monkeypatch):
        http, _ = browser_env

        class FailingPage:
            async def goto(self, url, **kwargs):
                raise RuntimeError("page crashed")

            async def close(self):
                pass

        class FakeBrowser:
            async def new_page(self, viewport=None):
                return FailingPage()

        async def fake_browser():
            return FakeBrowser()

        monkeypatch.setattr("core.playwright_manager.get_global_browser", fake_browser)
        resp = await http.post("/api/browser/screenshot", json={"url": PUBLIC_URL})
        assert resp.status_code == 500

    async def test_screenshot_playwright_missing_503(self, browser_env, monkeypatch):
        http, _ = browser_env
        with monkeypatch.context() as m:
            m.setitem(__import__("sys").modules, "core.playwright_manager", None)
            resp = await http.post("/api/browser/screenshot", json={"url": PUBLIC_URL})
        assert resp.status_code == 503
        assert "Playwright" in resp.json()["detail"]


@pytest.mark.unit
class TestBrowseSessions:
    async def test_save_browse_session(self, browser_env, monkeypatch):
        http, _ = browser_env
        stored: dict[str, Any] = {}

        def fake_store(**kwargs):
            stored.update(kwargs)

        monkeypatch.setattr("core.unified_memory.unified_memory.store_long_term_memory", fake_store)
        resp = await http.post(
            "/api/browser/browse-session",
            json={"url": PUBLIC_URL, "userId": "u1", "timestamp": 123, "tabId": "t1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["session_id"].startswith("browse_123_")
        assert stored["user_id"] == "u1"
        assert stored["metadata"]["url"] == PUBLIC_URL

    async def test_save_browse_session_failure_non_critical(self, browser_env, monkeypatch):
        http, _ = browser_env

        def broken(**kwargs):
            raise RuntimeError("memory down")

        monkeypatch.setattr("core.unified_memory.unified_memory.store_long_term_memory", broken)
        resp = await http.post("/api/browser/browse-session", json={"url": PUBLIC_URL})
        assert resp.status_code == 200  # never fails the request
        body = resp.json()
        assert body["success"] is False
        assert body["session_id"] == "error"
        assert "memory down" in body["message"]

    async def test_get_browse_sessions_filters(self, browser_env, monkeypatch):
        http, _ = browser_env
        now = int(time.time())
        rows = [
            {
                "task_type": "browse_session",
                "user_id": "u1",
                "session_id": "legacy-s1",
                "created_at": "2026-01-01T00:00:00Z",
                "metadata": {
                    "session_id": "s1",
                    "url": "https://a.example",
                    "userId": "u1",
                    "timestamp": now - 10,
                },
            },
            {  # too old → filtered by hours window
                "task_type": "browse_session",
                "user_id": "u1",
                "created_at": "old",
                "metadata": {
                    "session_id": "s2",
                    "url": "https://old.example",
                    "userId": "u1",
                    "timestamp": now - 40 * 3600,
                },
            },
            {  # wrong task type → skipped
                "task_type": "chat",
                "metadata": {"session_id": "s3", "timestamp": now},
            },
            {  # zero timestamp → kept (ts filter skipped)
                "task_type": "browse_session",
                "created_at": "c3",
                "metadata": {"session_id": "s4", "url": "https://c.example"},
            },
        ]
        monkeypatch.setattr(
            "core.unified_memory.unified_memory.long_term_memory.retrieve_memories",
            lambda user_id: rows,
        )
        resp = await http.get(
            "/api/browser/browse-sessions", params={"userId": "u1", "hours": 24, "limit": 10}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["count"] == 2
        assert [s["session_id"] for s in body["sessions"]] == ["s1", "s4"]
        assert body["query_params"]["limit"] == 10

    async def test_get_browse_sessions_limit_cap(self, browser_env, monkeypatch):
        http, _ = browser_env
        now = int(time.time())
        rows = [
            {
                "task_type": "browse_session",
                "created_at": "c",
                "metadata": {"session_id": f"s{i}", "timestamp": now},
            }
            for i in range(5)
        ]
        monkeypatch.setattr(
            "core.unified_memory.unified_memory.long_term_memory.retrieve_memories",
            lambda user_id: rows,
        )
        resp = await http.get("/api/browser/browse-sessions", params={"limit": 2})
        body = resp.json()
        assert body["count"] == 2

    async def test_get_browse_sessions_failure(self, browser_env, monkeypatch):
        http, _ = browser_env

        def broken(user_id):
            raise RuntimeError("retrieval exploded")

        monkeypatch.setattr(
            "core.unified_memory.unified_memory.long_term_memory.retrieve_memories",
            broken,
        )
        resp = await http.get("/api/browser/browse-sessions")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "retrieval exploded" in body["error"]


@pytest.mark.unit
class TestGalleryAndHealth:
    async def test_screenshot_gallery_entry(self, browser_env):
        http, _ = browser_env
        resp = await http.post(
            "/api/browser/screenshots",
            params={"userId": "u1", "url": PUBLIC_URL, "timestamp": 42},
        )
        assert resp.status_code == 200
        entry = resp.json()["galleryEntry"]
        assert entry["userId"] == "u1"
        assert entry["url"] == PUBLIC_URL
        assert entry["capturedAt"] == 42
        assert "screenshots/u1/" in entry["storageLocation"]

    async def test_health_all_available(self, browser_env, monkeypatch):
        http, _ = browser_env

        async def ok():
            return True

        for fn in (
            "check_llm_gateway",
            "check_security_modules",
            "check_playwright",
            "check_unified_memory",
        ):
            monkeypatch.setattr(br, fn, ok)
        resp = await http.get("/api/browser/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert len(body["capabilities"]) == 4

    async def test_health_degraded_and_error(self, browser_env, monkeypatch):
        http, _ = browser_env

        async def ok():
            return True

        async def unavailable():
            return False

        async def explodes():
            raise RuntimeError("check crashed")

        monkeypatch.setattr(br, "check_llm_gateway", ok)
        monkeypatch.setattr(br, "check_security_modules", unavailable)
        monkeypatch.setattr(br, "check_playwright", explodes)
        monkeypatch.setattr(br, "check_unified_memory", ok)
        resp = await http.get("/api/browser/health")
        body = resp.json()
        assert body["status"] == "degraded"
        caps = {c["name"]: c for c in body["capabilities"]}
        assert caps["security-scan"]["available"] is False
        assert caps["screenshot"]["available"] is False
        assert "check crashed" in caps["screenshot"]["error"]
        assert caps["ai-action"]["available"] is True

    async def test_real_capability_checks(self, browser_env):
        """check_* helpers with real imports (all deps exist in this env)."""
        assert await br.check_llm_gateway() is True
        assert await br.check_security_modules() is True
        assert await br.check_playwright() is True
        assert await br.check_unified_memory() is True


@pytest.mark.unit
class TestSSRFGateDirect:
    async def test_assert_helper_blocks(self, browser_env):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            br._assert_safe_public_url(BLOCKED_URL)
        assert exc.value.status_code == 403
        # safe URL passes silently (sync helper, returns None)
        assert br._assert_safe_public_url(PUBLIC_URL) is None

    async def test_real_ssrf_blocks_localhost_without_dns(self):
        """The real SSRFProtection blocks loopback without any network."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            await br._assert_safe_public_url("http://127.0.0.1:9/x")
        assert exc.value.status_code == 403

    async def test_admin_guard_403_for_non_admin(self):
        """Router-level get_current_admin rejects a non-admin payload."""
        from api.dependencies import get_current_user_token

        app = FastAPI()
        app.include_router(br.router)

        def non_admin():
            return {"sub": "u@x.com", "role": "user"}

        app.dependency_overrides[get_current_user_token] = non_admin
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            resp = await http.get("/api/browser/health")
        app.dependency_overrides.clear()
        assert resp.status_code == 403
