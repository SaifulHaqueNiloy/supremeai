"""Issue #1819 — trusted-browsers '/api' alias contract tests.

The Settings "Authorized browsers" card (frontend SettingsPage.tsx) calls
``/api/admin/trusted-browsers`` (GET + DELETE) and
``/api/admin/trusted-browsers/{id}`` (DELETE). Before #1819 the backend only
served the unprefixed ``/admin/trusted-browsers`` family, so the security-
hygiene feature was silently dead (the frontend catch() swallowed the 404 and
always rendered an empty list).

Contract locked here:
  1. Both path families are advertised in the OpenAPI schema
     (``/api/admin/trusted-browsers`` AND ``/admin/trusted-browsers``).
  2. Both path families hit the SAME handler functions (no drift).
  3. The aliased surface works end-to-end (list → revoke one → revoke all).
  4. Aliased paths are reachable (503 when Redis is down, never 404).
"""

from __future__ import annotations

import json
import time

import pytest

fakeredis = pytest.importorskip("fakeredis", reason="fakeredis not installed")
import fakeredis.aioredis
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from core.cache.redis_manager import redis_manager

UID = "contract-test-admin"

ALIAS_LIST = "/api/admin/trusted-browsers"
ALIAS_REVOKE_ONE = "/api/admin/trusted-browsers/{browser_id}"
ALIAS_REVOKE_ALL = "/api/admin/trusted-browsers"
LEGACY_LIST = "/admin/trusted-browsers"
LEGACY_REVOKE_ONE = "/admin/trusted-browsers/{browser_id}"
LEGACY_REVOKE_ALL = "/admin/trusted-browsers"


def _build() -> tuple[FastAPI, AsyncClient]:
    import api.routes.admin_routes as ar

    app = FastAPI()
    app.include_router(ar.router)
    # Auth-free contract probing: the alias contract is about routing, not the
    # auth layer (locked elsewhere in test_admin_routes_full.py).
    app.dependency_overrides[ar.get_current_admin] = lambda: {"sub": UID, "role": "admin"}
    return app, AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def fake_redis(monkeypatch):
    fake = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr(redis_manager, "_client", fake)
    yield fake
    await fake.aclose()


async def _seed_browser(fake, browser_id: str) -> None:
    """Seed the exact record shape _issue_trusted_browser writes."""
    record = {
        "token_key": f"admin:trusted-browser:{browser_id}",
        "id": browser_id,
        "uid": UID,
        "email": "contract-test@supremeai.com",
        "created_at": int(time.time()),
    }
    # NOTE: fakeredis.aioredis commands are coroutines — must be awaited.
    await fake.setex(f"admin:trusted-browser-record:{UID}:{browser_id}", 600, json.dumps(record))
    await fake.sadd(f"admin:trusted-browsers:{UID}", browser_id)


@pytest.mark.unit
class TestTrustedBrowserApiAlias:
    async def test_openapi_advertises_both_path_families(self, fake_redis):
        app, _ = _build()
        schema = app.openapi()["paths"]

        # Aliased surface (what the frontend calls)
        assert ALIAS_LIST in schema, "GET /api/admin/trusted-browsers missing — #1819 regressed"
        assert "get" in schema[ALIAS_LIST]
        assert ALIAS_REVOKE_ALL in schema
        assert "delete" in schema[ALIAS_REVOKE_ALL]
        assert ALIAS_REVOKE_ONE in schema
        assert "delete" in schema[ALIAS_REVOKE_ONE]

        # Legacy surface must stay (existing consumers + test_admin_routes_full.py)
        for path in (LEGACY_LIST, LEGACY_REVOKE_ALL, LEGACY_REVOKE_ONE):
            assert path in schema, f"legacy path {path} unexpectedly removed"
        assert "get" in schema[LEGACY_LIST]
        assert "delete" in schema[LEGACY_REVOKE_ALL]
        assert "delete" in schema[LEGACY_REVOKE_ONE]

    async def test_alias_and_legacy_share_the_same_handler(self, fake_redis):
        from fastapi.routing import APIRoute

        app, _ = _build()
        by_path: dict[tuple[str, str], APIRoute] = {}
        for route in app.routes:
            if isinstance(route, APIRoute) and "trusted-browsers" in route.path:
                for method in route.methods or ():
                    by_path[(method, route.path)] = route

        for alias, legacy in [
            (("GET", ALIAS_LIST), ("GET", LEGACY_LIST)),
            (("DELETE", ALIAS_REVOKE_ALL), ("DELETE", LEGACY_REVOKE_ALL)),
            (("DELETE", ALIAS_REVOKE_ONE), ("DELETE", LEGACY_REVOKE_ONE)),
        ]:
            assert by_path[alias].endpoint is by_path[legacy].endpoint, (
                f"alias {alias} and legacy {legacy} must wrap the same handler"
            )

    async def test_alias_end_to_end_list_revoke_one_and_all(self, fake_redis):
        await _seed_browser(fake_redis, "browser-one")
        await _seed_browser(fake_redis, "browser-two")
        _, http = _build()

        listing = await http.get(ALIAS_LIST)
        assert listing.status_code == 200
        browsers = listing.json()["browsers"]
        assert sorted(b["id"] for b in browsers) == ["browser-one", "browser-two"]
        # token_key must never leak through the alias either
        assert all("token_key" not in b for b in browsers)

        # revoke one via the aliased path (frontend: DELETE /api/admin/trusted-browsers/{id})
        ok = await http.delete(ALIAS_REVOKE_ONE.format(browser_id="browser-one"))
        assert ok.status_code == 200
        assert ok.json() == {"ok": True}
        missing = await http.delete(ALIAS_REVOKE_ONE.format(browser_id="nope"))
        assert missing.status_code == 404

        # revoke all via the aliased path (frontend: DELETE /api/admin/trusted-browsers)
        ok_all = await http.delete(ALIAS_REVOKE_ALL)
        assert ok_all.status_code == 200
        assert ok_all.json() == {"ok": True}
        empty = await http.get(ALIAS_LIST)
        assert empty.json()["browsers"] == []

    async def test_alias_reachable_when_redis_down_is_503_not_404(self, fake_redis, monkeypatch):
        import api.routes.admin_routes as ar

        async def no_redis():
            return None

        monkeypatch.setattr(ar, "_get_redis_client", no_redis)
        _, http = _build()
        assert (await http.get(ALIAS_LIST)).status_code == 503
        assert (await http.delete(ALIAS_REVOKE_ONE.format(browser_id="some-id"))).status_code == 503
        assert (await http.delete(ALIAS_REVOKE_ALL)).status_code == 503
