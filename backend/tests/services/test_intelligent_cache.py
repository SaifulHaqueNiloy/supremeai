"""Tests for services/intelligent_cache.py — Smart caching service."""
import pytest
from services.intelligent_cache import IntelligentCache


class TestIntelligentCache:
    """Intelligent cache: get, set, TTL, invalidation."""

    def test_init(self):
        cache = IntelligentCache()
        assert cache is not None

    def test_set_and_get(self):
        cache = IntelligentCache()
        cache.set("key-1", "value-1")
        assert cache.get("key-1") == "value-1"

    def test_get_nonexistent(self):
        cache = IntelligentCache()
        assert cache.get("nonexistent") is None

    def test_set_with_ttl(self):
        cache = IntelligentCache()
        cache.set("key-1", "value-1", ttl=3600)
        assert cache.get("key-1") == "value-1"

    def test_invalidate_key(self):
        cache = IntelligentCache()
        cache.set("key-1", "value-1")
        cache.invalidate("key-1")
        assert cache.get("key-1") is None

    def test_clear_all(self):
        cache = IntelligentCache()
        cache.set("key-1", "value-1")
        cache.set("key-2", "value-2")
        cache.clear()
        assert cache.get("key-1") is None
        assert cache.get("key-2") is None

    def test_cache_size(self):
        cache = IntelligentCache()
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        size = cache.size()
        assert size >= 2

    def test_overwrite(self):
        cache = IntelligentCache()
        cache.set("key", "v1")
        cache.set("key", "v2")
        assert cache.get("key") == "v2"
