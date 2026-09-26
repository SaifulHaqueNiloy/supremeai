"""Focused tests for the dependency-free portal CORS policy."""

from __future__ import annotations

from middleware import cors_policy


def test_user_origins_drop_wildcard_and_duplicates(monkeypatch):
    monkeypatch.setattr(cors_policy, "USER_ALLOWED_ORIGINS", ())

    assert cors_policy.resolve_user_cors_origins(
        ["*", " https://app.example.com ", "https://app.example.com"]
    ) == ["https://app.example.com"]


def test_user_origins_fall_back_to_configured_defaults(monkeypatch):
    monkeypatch.setattr(cors_policy, "USER_ALLOWED_ORIGINS", ("https://app.example.com",))

    assert cors_policy.resolve_user_cors_origins([]) == ["https://app.example.com"]


def test_admin_origins_always_include_configured_admin_origins(monkeypatch):
    monkeypatch.setattr(cors_policy, "ADMIN_ALLOWED_ORIGINS", ("https://admin.example.com",))

    assert cors_policy.resolve_admin_cors_origins(["https://custom.example.com"]) == [
        "https://custom.example.com",
        "https://admin.example.com",
    ]


def test_admin_origins_drop_wildcard_and_duplicates(monkeypatch):
    monkeypatch.setattr(cors_policy, "ADMIN_ALLOWED_ORIGINS", ())

    assert cors_policy.resolve_admin_cors_origins(
        ["*", "https://admin.example.com", "https://admin.example.com"]
    ) == ["https://admin.example.com"]


def test_empty_admin_configuration_does_not_invent_an_origin(monkeypatch):
    monkeypatch.setattr(cors_policy, "ADMIN_ALLOWED_ORIGINS", ())

    assert cors_policy.resolve_admin_cors_origins([]) == []


def test_origin_denylist_is_applied(monkeypatch):
    monkeypatch.setattr(
        cors_policy, "ADMIN_ORIGIN_DENYLIST", frozenset({"https://admin.example.com"})
    )
    monkeypatch.setattr(cors_policy, "USER_ORIGIN_DENYLIST", frozenset())
    monkeypatch.setattr(cors_policy, "USER_ALLOWED_ORIGINS", ())

    assert cors_policy.resolve_user_cors_origins(["https://admin.example.com"]) == []


# The policy intentionally remains pure and dependency-free; app boot tests belong
# in the API test suite and require the backend runtime dependencies.


def test_production_frontend_origins_are_safe_defaults(monkeypatch):
    """Issues #1483/#1484/#1455 regression guard: the deployed user portal
    (https://supremeai-a.web.app) and admin console (https://supremeai-admin.web.app)
    must be preflight-able even when USER_CORS_ORIGINS / ADMIN_CORS_ORIGINS fail to
    sync to the host. The module-level defaults are the last line of defense.

    FIX (CI red 36219425476): the CI Pipeline exports USER_CORS_ORIGINS /
    ADMIN_CORS_ORIGINS (localhost values) as process env — env always wins by
    design, so asserting the module-level EFFECTIVE constants here made the
    guard depend on runner env. The fallback contract is now asserted through
    the same loader the module uses, with env explicitly cleared.
    """
    monkeypatch.delenv("USER_CORS_ORIGINS", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("ADMIN_CORS_ORIGINS", raising=False)
    assert "https://supremeai-a.web.app" in cors_policy.DEFAULT_USER_ALLOWED_ORIGINS
    assert "https://supremeai-admin.web.app" in cors_policy.DEFAULT_ADMIN_ALLOWED_ORIGINS
    # The loader (env → vault-cache → default) must land on the production
    # defaults in a clean environment — this is the last-line-of-defense path.
    user_resolved = cors_policy._load_origins(
        "CORS_ORIGINS", cors_policy.DEFAULT_USER_ALLOWED_ORIGINS
    )
    admin_resolved = cors_policy._load_origins(
        "ADMIN_CORS_ORIGINS", cors_policy.DEFAULT_ADMIN_ALLOWED_ORIGINS
    )
    assert user_resolved, "user fallback must not be empty"
    assert admin_resolved, "admin fallback must not be empty"
    assert "https://supremeai-a.web.app" in user_resolved
    assert "https://supremeai-admin.web.app" in admin_resolved
