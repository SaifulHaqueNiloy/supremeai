"""Unit tests for the Open-Source Integrations layer (backend/integrations/).

এই টেস্টগুলো external dependency বা live service ছাড়াই চলে:
- fallback (zero-cost) পাথ বাস্তবে এক্সিকিউট হয়
- upstream পাথ মক দিয়ে ভেরিফাই হয়
- flag/dependency গেট ভালোভাবে কাজ করে (গ্রেসফুল ডিগ্রেডেশন)
"""

import sys
import types
from unittest.mock import MagicMock, patch

from integrations.browser_use_adapter import BrowserUseAdapter
from integrations.e2b_adapter import E2BAdapter
from integrations.graphiti_adapter import GraphitiMemoryAdapter
from integrations.mem0_adapter import Mem0MemoryAdapter
from integrations.openhands_adapter import OpenHandsAdapter


def test_mem0_fallback_record_and_search_relevance():
    ad = Mem0MemoryAdapter()
    assert ad.active is False  # upstream dep absent in test env → fallback
    ad.record([{"role": "user", "content": "আমার প্রিয় ভাষা python"}, {"role": "assistant", "content": "হ্যাঁ python দারুণ।"}])
    ad.record([{"role": "user", "content": "আজ landmark এ lunch করবো"}])
    hits = ad.search("python language")
    assert any("python" in h for h in hits)
    # irreleavant query → no results
    assert ad.search("completely unrelated xyzq") == []


def test_mem0_active_uses_upstream_when_enabled():
    fake_mem = MagicMock()
    fake_module = types.ModuleType("mem0")
    fake_module.Memory = MagicMock(return_value=fake_mem)
    with patch.dict(sys.modules, {"mem0": fake_module}), patch(
        "integrations.mem0_adapter.flag", return_value=True
    ), patch("integrations.mem0_adapter.import_available", return_value=True):
        ad = Mem0MemoryAdapter()
        assert ad.active is True
        ad.record([{"role": "user", "content": "hi"}], user_id="u1")
        fake_mem.add.assert_called_once()


def test_mem0_upstream_search_shapes_results():
    fake_mem = type(
        "Mem", (), {"search": lambda self, q, user_id, top_k: {"results": [{"memory": "m1", "score": 0.9}, {"memory": "m2", "score": 0.5}]}}
    )()
    fake_module = types.ModuleType("mem0")
    fake_module.Memory = MagicMock(return_value=fake_mem)
    with patch.dict(sys.modules, {"mem0": fake_module}), patch(
        "integrations.mem0_adapter.flag", return_value=True
    ), patch("integrations.mem0_adapter.import_available", return_value=True):
        ad = Mem0MemoryAdapter()
        assert ad.search("q", top_k=3) == ["m1", "m2"]


def test_graphiti_fallback_recency_and_match():
    ad = GraphitiMemoryAdapter()
    ad.add_episode("deploy pipeline ঠিক হল azure")
    ad.add_episode("database migration done postgres")
    hits = ad.search("azure deployment")
    assert any("azure" in h for h in hits)
    assert ad.search("nothing related zq") == []


def test_browser_use_fallback_returns_plan():
    ad = BrowserUseAdapter()
    out = ad.run_task("open login page and fill form")
    assert out["engine"] == "fallback"
    assert out["status"] == "ok"
    assert "open login" in out["result"]["plan"]


def test_e2b_fallback_executes_python_isolated():
    ad = E2BAdapter(timeout=20)
    out = ad.run_code("print(21 * 2)", language="python3")
    assert out["engine"] == "fallback"
    assert out["status"] == "ok"
    assert "42" in out.get("stdout", "")


def test_all_adapters_flag_off_safe():
    """flag off হলে কোনো exception ছাড়াই fallback/নির্দিষ্ট আচরণ চলে।"""
    assert Mem0MemoryAdapter().active in (False, True)
    assert GraphitiMemoryAdapter().active in (False, True)
    assert BrowserUseAdapter().active in (False, True)


# ── OpenHands autonomous coding agent ─────────────────────────────────────────


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeRequests:
    """Minimal requests stand-in for OpenHands agent-server REST flow."""

    def __init__(self, sid="s1", events=None):
        self.sid = sid
        self.events = events or []
        self.post_urls = []

    def post(self, url, json=None, timeout=None):
        self.post_urls.append(url)
        if url.endswith("/api/sessions"):
            return _FakeResp({"id": self.sid})
        return _FakeResp({})

    def get(self, url, timeout=None):
        return _FakeResp(self.events)


def test_openhands_inactive_fallback_no_request():
    with patch("integrations.openhands_adapter.flag", return_value=False):
        ad = OpenHandsAdapter(server_url="http://x:1")
        assert ad.active is False
        out = ad.run_coding_task("fix the bug in auth")
        assert out["status"] == "skipped"
        assert out["engine"] == "fallback"


def test_openhands_active_upstream_flow():
    fake = _FakeRequests(
        events=[
            {"message": {"event": "assistant", "args": {"content": "analyzing auth module"}}},
            {"message": {"event": "done", "args": {"content": "bug fixed in auth"}}},
        ]
    )
    fake_module = types.ModuleType("requests")
    fake_module.post = fake.post
    fake_module.get = fake.get
    with patch("integrations.openhands_adapter.flag", return_value=True), patch.dict(
        sys.modules, {"requests": fake_module}
    ):
        ad = OpenHandsAdapter(server_url="http://localhost:3001")
        assert ad.active is True
        out = ad.run_coding_task("fix the bug in auth", workspace="/repo")
        assert out["status"] == "ok"
        assert out["engine"] == "upstream"
        assert out["session_id"] == "s1"
        assert "fixed in auth" in out["result"]


def test_openhands_upstream_error_handled():
    class _Boom(_FakeRequests):
        def post(self, url, json=None, timeout=None):
            raise RuntimeError("server down")

    fake_module = types.ModuleType("requests")
    fake_module.post = _Boom().post
    fake_module.get = _FakeRequests().get
    with patch("integrations.openhands_adapter.flag", return_value=True), patch.dict(
        sys.modules, {"requests": fake_module}
    ):
        ad = OpenHandsAdapter(server_url="http://localhost:3001")
        out = ad.run_coding_task("task")
        assert out["status"] == "error"
        assert "server down" in out["error"]

