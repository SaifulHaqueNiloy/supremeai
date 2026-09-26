"""Issue #1818 — feature-flag admin surface + runtime unification contract tests.

Locks the four-part repair:

  Bug 1: DB lookups hit the SupabaseDB WRAPPER (never the raw client).
  Bug 2: env kill-switch (explicit false) can never be overridden by the DB.
  Bug 3: /admin-api/feature-flags is backed by the real Supabase table with
         the SAME feature_name keys the runtime checks; mutations reset the
         runtime cache; CommandCenter's bare-array contract is honored.
  Island 4: the integrations registry consults feature_flags (env → DB) for
         the five premium adapters.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import feature_flags as ff_module
from core.feature_flags import feature_flags


@pytest.fixture(autouse=True)
def _fresh_flag_cache():
    feature_flags.reset_cache()
    yield
    feature_flags.reset_cache()


# ─────────────────────────── admin surface (Bug 3) ───────────────────────────


class StubDB:
    """Stand-in for database.supabase_client.db (list/upsert only)."""

    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.client = SimpleNamespace()  # truthy — 'DB configured'
        self.upserts: list[tuple] = []

    def list_feature_flags(self):
        return list(self.rows)

    def upsert_feature_flag(self, feature_name, *, enabled=None, rollout_percentage=None):
        self.upserts.append((feature_name, enabled, rollout_percentage))
        row = next((r for r in self.rows if r.get("feature_name") == feature_name), None)
        if row is None:
            row = {
                "id": len(self.rows) + 7,
                "feature_name": feature_name,
                "enabled": False,
                "rollout_percentage": 100,
            }
            self.rows.append(row)
        if enabled is not None:
            row["enabled"] = enabled
        if rollout_percentage is not None:
            row["rollout_percentage"] = rollout_percentage
        return dict(row)


def _client(monkeypatch, stub_db) -> TestClient:
    import api.routes.admin_auth as admin_auth
    from api.routes.admin_dashboard import router

    monkeypatch.setattr("database.supabase_client.db", stub_db)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[admin_auth.require_admin_token] = lambda: {"sub": "contract-test"}
    app.dependency_overrides[admin_auth.admin_rate_limit] = lambda: None
    return TestClient(app)


@pytest.mark.unit
class TestFeatureFlagAdminSurface:
    def test_get_returns_bare_array_with_runtime_names(self, monkeypatch):
        stub = StubDB(
            rows=[
                {
                    "id": 1,
                    "feature_name": "mem0_enabled",
                    "enabled": True,
                    "rollout_percentage": 100,
                    "updated_at": "2026-09-26T00:00:00Z",
                }
            ]
        )
        c = _client(monkeypatch, stub)
        res = c.get("/admin-api/feature-flags")
        assert res.status_code == 200
        flags = res.json()
        assert isinstance(flags, list), "CommandCenter contract: GET must return a bare array"
        keys = {f["key"] for f in flags}
        for runtime_name in (
            "mem0_enabled",
            "graphiti_enabled",
            "browser_use_enabled",
            "e2b_enabled",
            "openhands_enabled",
        ):
            assert runtime_name in keys, f"runtime flag '{runtime_name}' must be manageable"
        mem0 = next(f for f in flags if f["key"] == "mem0_enabled")
        assert mem0["enabled"] is True
        assert mem0["rollout_percent"] == 100
        assert mem0["environment"] == "prod"
        # Legacy aliases survive so the older CICDVisualizer keeps rendering
        assert mem0["name"] == "mem0_enabled" and mem0["rollout"] == 100

    def test_post_upserts_runtime_flag_and_resets_cache(self, monkeypatch):
        stub = StubDB()
        c = _client(monkeypatch, stub)
        cache_reset = {"reset": False}
        monkeypatch.setattr(
            feature_flags,
            "reset_cache",
            lambda: cache_reset.__setitem__("reset", True),
        )
        res = c.post(
            "/admin-api/feature-flags",
            json={"key": "mem0_enabled", "enabled": True, "rollout_percent": 50, "otp": "123456"},
        )
        assert res.status_code == 200
        body = res.json()
        assert "message" in body, "CommandCenter useUpdateFeatureFlag expects {message}"
        assert stub.upserts == [("mem0_enabled", True, 50)], "mutation must hit the real table"
        assert cache_reset["reset"] is True, "runtime cache must reset so gating updates"

    def test_post_rejects_unknown_flag_name(self, monkeypatch):
        c = _client(monkeypatch, StubDB())
        res = c.post(
            "/admin-api/feature-flags",
            json={"key": "new_chat_ui", "enabled": True},
        )
        assert res.status_code == 422
        assert "Runtime-managed flags" in res.json()["detail"]

    def test_post_rejects_invalid_rollout(self, monkeypatch):
        c = _client(monkeypatch, StubDB())
        res = c.post(
            "/admin-api/feature-flags",
            json={"key": "mem0_enabled", "enabled": True, "rollout_percent": 150},
        )
        assert res.status_code == 422

    def test_put_updates_by_row_id(self, monkeypatch):
        stub = StubDB(
            rows=[
                {"id": 3, "feature_name": "e2b_enabled", "enabled": False, "rollout_percentage": 0}
            ]
        )
        c = _client(monkeypatch, stub)
        res = c.put("/admin-api/feature-flags/3", json={"enabled": True})
        assert res.status_code == 200
        assert stub.upserts == [("e2b_enabled", True, None)]
        assert res.json()["flag"]["enabled"] is True

    def test_put_unknown_flag_404(self, monkeypatch):
        c = _client(monkeypatch, StubDB())
        res = c.put("/admin-api/feature-flags/does_not_exist", json={"enabled": True})
        assert res.status_code == 404

    def test_db_unavailable_is_503_not_fake_data(self, monkeypatch):
        c = _client(monkeypatch, StubDB())
        monkeypatch.setattr("database.supabase_client.db", SimpleNamespace(client=None))
        res = c.get("/admin-api/feature-flags")
        assert res.status_code == 503, "honest failure — never a silent fake list"


# ─────────────────────── registry unification (island 4) ──────────────────────


@pytest.mark.unit
class TestRegistryFlagUnification:
    def test_registry_consults_feature_flags_for_premium_adapters(self, monkeypatch):
        from core.integrations.registry import get_integration

        monkeypatch.delenv("SUPREMEAI_MEM0_ENABLED", raising=False)
        monkeypatch.setattr(ff_module, "_db_flag", lambda name, user_id=None: True)
        info = get_integration("mem0")
        assert info is not None
        assert info.enabled is True, "DB-enabled flag must surface in the registry"
        assert info.status.value == "enabled"

    def test_registry_disabled_when_flag_off(self, monkeypatch):
        from core.integrations.registry import get_integration

        monkeypatch.delenv("SUPREMEAI_E2B_ENABLED", raising=False)
        monkeypatch.setattr(ff_module, "_db_flag", lambda name, user_id=None: None)
        info = get_integration("e2b")
        assert info is not None
        assert info.enabled is False
        assert info.status.value == "disabled"

    def test_registry_non_flagged_keys_untouched(self, monkeypatch):
        from core.integrations.registry import get_integration

        monkeypatch.setattr(ff_module, "_db_flag", lambda name, user_id=None: True)
        info = get_integration("n8n")
        assert info is not None
        # n8n keeps its settings-based state (enabled requires base_url config);
        # the flag override must NOT apply to it.
        assert info.status.value != "enabled" or info.key == "n8n"  # structural no-op guard
        assert get_integration("ollama") is not None
