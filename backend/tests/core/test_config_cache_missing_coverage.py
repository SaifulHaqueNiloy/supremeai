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


# ========================== config_cache.py ==========================


class TestConfigCacheMissingBranches:
    def test_should_refresh_after_ttl(self):
        from core.config_cache import ConfigCache

        cache = ConfigCache(ttl_seconds=0)
        cache._last_refresh = time.time() - 1
        assert cache._should_refresh() is True

    def test_should_refresh_within_ttl(self):
        from core.config_cache import ConfigCache

        cache = ConfigCache(ttl_seconds=60)
        cache._last_refresh = time.time()
        assert cache._should_refresh() is False

    def test_refresh_sync_loads_defaults_on_db_failure(self, monkeypatch):
        from core.config_cache import DEFAULT_CONFIGS, ConfigCache

        async def fake_load_from_db_async(self):
            raise RuntimeError("db down")

        monkeypatch.setattr(ConfigCache, "_load_from_db_async", fake_load_from_db_async)
        cache = ConfigCache()
        cache.refresh_sync_bootstrap()
        assert cache._loaded is True
        assert cache.get("cache_threshold_code") == DEFAULT_CONFIGS["cache_threshold_code"]

    def test_get_all_category_filter(self):
        from core.config_cache import DEFAULT_CONFIGS, ConfigCache

        cache = ConfigCache()
        cache._loaded = True
        cache._cache = dict(DEFAULT_CONFIGS)
        filtered = cache.get_all("cache_threshold_")
        assert "cache_threshold_code" in filtered
        assert "feature_semantic_cache" not in filtered

    def test_get_all_no_category_returns_copy(self):
        from core.config_cache import DEFAULT_CONFIGS, ConfigCache

        cache = ConfigCache()
        cache._loaded = True
        cache._cache = dict(DEFAULT_CONFIGS)
        all_conf = cache.get_all()
        all_conf["new_key"] = "new_val"
        assert "new_key" not in cache._cache

    @pytest.mark.asyncio
    async def test_set_updates_in_memory_cache(self):
        from core.config_cache import ConfigCache

        # বাংলা মন্তব্য: testing loop triggers এবং refresh bypass করতে ttl ও last_refresh নির্ধারণ করা হলো
        cache = ConfigCache(ttl_seconds=3600)
        cache._last_refresh = time.time()
        cache._loaded = True

        mock_session = MagicMock()
        mock_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("database.session._get_session_maker") as mock_maker:
            mock_maker.return_value = MagicMock(return_value=mock_session)
            ok = await cache.set("new_key", "new_value")
        assert ok is True
        assert cache.get("new_key") == "new_value"

    def test_invalidate_specific_key(self):
        from core.config_cache import ConfigCache

        cache = ConfigCache()
        cache._cache = {"a": 1, "b": 2}
        cache._loaded = True
        cache.invalidate("a")
        assert "a" not in cache._cache
        assert cache.get("a") is None

    def test_invalidate_all_clears_cache(self):
        from core.config_cache import ConfigCache

        cache = ConfigCache()
        cache._cache = {"a": 1}
        cache._loaded = True
        cache.invalidate()
        assert cache._cache == {}
        assert cache._loaded is False

    @pytest.mark.asyncio
    async def test_refresh_async_db_failure_uses_defaults(self):
        from core.config_cache import DEFAULT_CONFIGS, ConfigCache

        cache = ConfigCache()
        with patch("database.session._get_session_maker", side_effect=RuntimeError("db down")):
            await cache.refresh_async()
        assert cache._loaded is True
        assert cache.get("cache_threshold_code") == DEFAULT_CONFIGS["cache_threshold_code"]


