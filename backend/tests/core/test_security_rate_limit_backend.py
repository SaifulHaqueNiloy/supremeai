"""P1 — Redis-authoritative security rate limiter tests.

বাংলা: RequestValidationMiddleware._check_rate_limit এখন Redis-authoritative;
Redis না থাকলে per-instance in-memory EMERGENCY fallback (WARNING লগসহ)।
"""

import time
from importlib import import_module
from unittest.mock import patch

import pytest

from core.middleware.security import RequestValidationMiddleware

# বাংলা: core.cache.__init__ নিজেই 'redis_manager' নামে ইনস্ট্যান্স রি-এক্সপোর্ট
# করে, তাই 'import core.cache.redis_manager as m' মডিউল নয় ইনস্ট্যান্স দেয়।
# মডিউল অবজেক্ট সরাসরি নিতে হয়।
redis_manager_module = import_module("core.cache.redis_manager")


class _FakePipeline:
    """Pipeline stub: execute() returns queued results for the fake zset."""

    def __init__(self, fake, count_after_prune: int | None = None):
        self._fake = fake
        self._count_after_prune = count_after_prune
        self._ops: list[str] = []

    def zremrangebyscore(self, *_a, **_k):
        self._ops.append("prune")

    def zcard(self, *_a, **_k):
        self._ops.append("count")

    def zadd(self, *_a, **_k):
        self._ops.append("add")

    def expire(self, *_a, **_k):
        self._ops.append("expire")

    async def execute(self):
        if "count" in self._ops and "add" not in self._ops:
            # check phase: [prune result, count]
            return [None, self._count_after_prune]
        return [None, None]  # add phase: [add result, expire result]


class _FakeRedis:
    """Minimal redis client stub. `counts` maps zset key -> next reported count."""

    def __init__(self, counts: dict[str, int] | None = None):
        self.counts = counts or {}
        self.added: list[str] = []

    def pipeline(self, transaction: bool = True):  # noqa: ARG002
        key = getattr(self, "_current_key", None)
        return _FakePipeline(self, self.counts.get(key, 0))

    # helper used by tests to point the stub at a zset key
    def _prime(self, zset_key: str):
        self._current_key = zset_key


@pytest.fixture
def mw():
    """Build a middleware instance without a real app."""
    return RequestValidationMiddleware(app=None)


@pytest.fixture
def fake_redis(monkeypatch):
    fake = _FakeRedis()

    class _Manager:
        async def get_client_async(self):
            return fake

    # বাংলা: core.cache.redis_manager হলো মডিউল — সেখানেই module-level
    # redis_manager ভেরিয়েবল প্যাচ করতে হয় (core.cache থেকে ইমপোর্ট করলে
    # ইনস্ট্যান্স পাওয়া যায়, মডিউল নয়)।
    monkeypatch.setattr(redis_manager_module, "redis_manager", _Manager())
    return fake


@pytest.mark.asyncio
async def test_redis_authoritative_allows_under_limit(mw, fake_redis):
    def _pipeline(self, transaction=True):  # noqa: ARG001
        return _FakePipeline(fake_redis, 0)

    fake_redis.pipeline = _pipeline.__get__(fake_redis)
    allowed = await mw._check_rate_limit("1.2.3.4", "/api/v1/anything")
    assert allowed is True


@pytest.mark.asyncio
async def test_redis_authoritative_rejects_at_limit(mw, fake_redis):
    state = {"count": 100}  # default limit is 100/min → count >= limit rejects

    def _pipeline(self, transaction=True):  # noqa: ARG001
        return _FakePipeline(fake_redis, state["count"])

    fake_redis.pipeline = _pipeline.__get__(fake_redis)
    allowed = await mw._check_rate_limit("1.2.3.4", "/api/v1/anything")
    assert allowed is False


@pytest.mark.asyncio
async def test_critical_path_limit_override(mw, fake_redis):
    """Login path uses 5/600 limit, not the default 100/60."""

    def _pipeline(self, transaction=True):  # noqa: ARG001
        return _FakePipeline(fake_redis, 5)

    fake_redis.pipeline = _pipeline.__get__(fake_redis)
    allowed = await mw._check_rate_limit("9.9.9.9", "/api/v1/auth/login")
    # count=5 >= limit=5 → rejected
    assert allowed is False


@pytest.mark.asyncio
async def test_fallback_when_redis_unavailable(mw, monkeypatch):
    class _NoneManager:
        async def get_client_async(self):
            return None

    monkeypatch.setattr(redis_manager_module, "redis_manager", _NoneManager())

    results = []
    for _ in range(3):
        results.append(await mw._check_rate_limit("7.7.7.7", "/api/v1/anything"))
    assert results == [True, True, True]
    for _ in range(97):
        assert await mw._check_rate_limit("7.7.7.7", "/api/v1/anything") is True
    # next one breaches the default 100/min limit
    assert await mw._check_rate_limit("7.7.7.7", "/api/v1/anything") is False


@pytest.mark.asyncio
async def test_fallback_memory_is_per_instance():
    class _NoneManager:
        async def get_client_async(self):
            return None

    with patch.object(redis_manager_module, "redis_manager", _NoneManager()):
        a = RequestValidationMiddleware(app=None)
        b = RequestValidationMiddleware(app=None)
        # both allow the first request; state is independent per instance
        assert await a._check_rate_limit("5.5.5.5", "/api/v1/anything") is True
        assert await b._check_rate_limit("5.5.5.5", "/api/v1/anything") is True
        assert "5.5.5.5" in a._request_log
        assert "5.5.5.5" in b._request_log


@pytest.mark.asyncio
async def test_old_entries_ignored_in_fallback(mw, monkeypatch):
    class _NoneManager:
        async def get_client_async(self):
            return None

    monkeypatch.setattr(redis_manager_module, "redis_manager", _NoneManager())
    # seed stale timestamps far outside the window
    mw._request_log["6.6.6.6"] = [time.time() - 10_000] * 500
    assert await mw._check_rate_limit("6.6.6.6", "/api/v1/anything") is True
