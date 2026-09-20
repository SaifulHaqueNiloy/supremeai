"""Shared fixtures for MCP tool tests (Task 7-f).

``tools/mcp/mcp_supabase.py`` and ``tools/mcp/mcp_neon.py`` hard-import
``psycopg2`` at module top, but psycopg2 lives in the optional
``mcp-tools`` poetry group and is NOT installed in the unit-test
environment.  We inject a lightweight stand-in module into
``sys.modules`` **before** the test modules import the MCP modules so
that collection succeeds; the tests themselves monkeypatch
``psycopg2.connect`` per test (never touching a real database).
"""

from __future__ import annotations

import sys
import types

import pytest


def _ensure_fake_psycopg2() -> None:
    if "psycopg2" in sys.modules:
        return
    try:  # pragma: no cover - depends on optional group installation
        import psycopg2  # noqa: F401
    except ImportError:
        fake = types.ModuleType("psycopg2")
        fake.connect = None  # tests monkeypatch this per-test
        fake.Error = type("Error", (Exception,), {})
        sys.modules["psycopg2"] = fake


_ensure_fake_psycopg2()


@pytest.fixture(autouse=True)
def _mcp_env(monkeypatch):
    """Deterministic MCP environment for every test in this directory.

    - A FAKE postgres URL is pre-set (psycopg2 itself is faked, so no real
      connection can ever happen).
    - Settings attributes that could leak real URLs are blanked so the env
      var stays the single source of truth.
    - Admin authorization defaults to TRUE; tests that exercise the
      unauthorized branches flip it explicitly.
    """
    from types import SimpleNamespace

    import tools.mcp.mcp_neon as mn
    import tools.mcp.mcp_supabase as ms

    monkeypatch.setenv("SUPABASE_DATABASE_URL", "postgresql://supabase-mcp-test.invalid/db")
    monkeypatch.setenv("NEON_DATABASE_URL", "postgresql://neon-mcp-test.invalid/db")
    monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
    # core.config.settings exposes these as read-only properties → swap the
    # module-level reference for a controllable namespace instead.
    monkeypatch.setattr(ms, "settings", SimpleNamespace(supabase_database_url=""), raising=False)
    monkeypatch.setattr(
        mn,
        "settings",
        SimpleNamespace(neon_database_url="", database_url="", neon_api_key=""),
        raising=False,
    )
