# বাংলা মন্তব্য: core module-এর কম-কভার লাইন কভার করার জন্য অতিরিক্ত টেস্টসমূহ
import asyncio
import contextlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.messaging.event_bus import ErrorContext

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_test_env(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("SUPREMEAI_JWT_SECRET", "test-secret-placeholder")
    monkeypatch.setenv("SUPREMEAI_ADMIN_PASSWORD_HASH", "")
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    yield
    return


# ========================== config.py ==========================


class TestSettingsValidators:
    """Cover validator branches not exercised by test_config.py."""

    def test_parse_admin_emails_comma_separated(self):
        from core.config import Settings

        assert Settings.parse_admin_emails("a@b.com, c@d.com") == ["a@b.com", "c@d.com"]

    def test_parse_allowed_hosts_comma_separated(self):
        from core.config import Settings

        assert Settings.parse_allowed_hosts("host1,host2") == ["host1", "host2"]

    def test_parse_cors_origins_json_string(self):
        from core.config import Settings

        assert Settings.parse_cors_origins(
            '["http://a.com", "http://b.com"]',
            type("FakeInfo", (), {"data": {"env": "local"}})(),
        ) == ["http://a.com", "http://b.com"]

    def test_parse_cors_origins_comma_string(self):
        from core.config import Settings

        assert Settings.parse_cors_origins(
            "http://a.com,http://b.com",
            type("FakeInfo", (), {"data": {"env": "local"}})(),
        ) == ["http://a.com", "http://b.com"]

    def test_parse_cors_origins_production_filters_localhost(self):
        from core.config import Settings

        result = Settings.validate_cors_origins(
            ["http://localhost:3000", "https://prod.com"],
            type(
                "FakeInfo",
                (),
                {"data": {"env": "production"}, "field_name": "cors_origins"},
            )(),
        )
        assert "http://localhost:3000" not in result
        assert "https://prod.com" in result

    def test_validate_debug_mode(self):
        from core.config import Settings

        result = Settings.validate_debug_mode(True, type("FakeInfo", (), {"data": {"env": "production"}})())
        assert result is False

    def test_set_jwt_secret_non_production_returns_placeholder(self, monkeypatch):
        from core.config import Settings

        monkeypatch.setenv("ENV", "test")
        monkeypatch.setenv("SUPREMEAI_JWT_SECRET", "a" * 64)
        s = Settings()
        assert len(s.jwt_secret) >= 64

    def test_get_cached_secret_caches_value(self, monkeypatch):
        from core.config import Settings

        calls = []

        def fake_fetch(key, *args, **kwargs):
            calls.append(key)
            return f"secret-for-{key}"

        monkeypatch.setattr("core.config_secrets.secret_vault.fetch_secret", fake_fetch)
        s = Settings()
        s._secrets_batch_loaded = False
        s._BATCH_SECRET_KEYS = ["X"]
        v1 = s._get_cached_secret("X")
        v2 = s._get_cached_secret("X")
        assert v1 == v2 == "secret-for-X"
        assert len(calls) == 1

    def test_computed_fields_read_from_vault(self, monkeypatch):
        from core.config import Settings

        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_DATABASE_URL_POOLER", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setattr("core.config_secrets.secret_vault.fetch_secret", lambda k, *a, **kw: f"val-{k}")
        s = Settings()
        assert s.supabase_database_url == "val-SUPABASE_DATABASE_URL_POOLER"
        assert s.redis_url == "redis://val-REDIS_URL"
        assert s.openrouter_api_key == "val-OPENROUTER_API_KEY"


