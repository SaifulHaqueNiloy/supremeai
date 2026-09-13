"""Focused tests for the dependency-free portal CORS policy."""

from __future__ import annotations

from middleware import cors_policy


def test_user_origins_drop_wildcard_and_duplicates(monkeypatch):
    monkeypatch.setattr(cors_policy, "USER_ALLOWED_ORIGINS", ())

    assert cors_policy.resolve_user_cors_origins(
        ["*", " https://app.example.com ", "https://app.example.com"]
    ) == ["https://app.example.com"]


def test_user_origins_fall_back_to_configured_defaults(monkeypatch):
    monkeypatch.setattr(
        cors_policy, "USER_ALLOWED_ORIGINS", ("https://app.example.com",)
    )

    assert cors_policy.resolve_user_cors_origins([]) == ["https://app.example.com"]


def test_admin_origins_always_include_configured_admin_origins(monkeypatch):
    monkeypatch.setattr(
        cors_policy, "ADMIN_ALLOWED_ORIGINS", ("https://admin.example.com",)
    )

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
