"""Tests for core/cache_manager.py — Central cache manager."""
import pytest
from core.cache_manager import CacheManager


class TestCacheManager:
    """Cache manager: get, set, delete, TTL, pattern."""

    def test_init(self):
        mgr = CacheManager()
        assert mgr is not None

    def test_set_and_get(self):
        mgr = CacheManager()
        mgr.set("key", "value")
        assert mgr.get("key") == "value"

    def test_get_missing(self):
        mgr = CacheManager()
        assert mgr.get("missing") is None

    def test_delete(self):
        mgr = CacheManager()
        mgr.set("key", "value")
        mgr.delete("key")
        assert mgr.get("key") is None

    def test_clear(self):
        mgr = CacheManager()
        mgr.set("k1", "v1")
        mgr.set("k2", "v2")
        mgr.clear()
        assert mgr.get("k1") is None

    def test_exists(self):
        mgr = CacheManager()
        mgr.set("key", "value")
        assert mgr.exists("key") is True
        assert mgr.exists("missing") is False
