"""Coverage tests for core/cache_manager.py (FreeTierCacheManager)."""

import json
import zlib
from unittest.mock import AsyncMock, patch

import pytest

from core.cache_manager import FreeTierCacheManager, get_cache_manager


def _result_json():
    from core.automation.models import AutomationResult, AutomationStatus

    r = AutomationResult(
        status=AutomationStatus.DELIVERED, provider="t", message="m", execution_id="e"
    )
    return r.model_dump_json()


@pytest.fixture
def manager():
    return FreeTierCacheManager(redis_url="redis://localhost:6379/0")


@pytest.fixture
def redis_pair():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.mget = AsyncMock(return_value=[None])
    client.close = AsyncMock()
    with patch("redis.asyncio.from_url", return_value=client) as factory:
        yield client, factory


def test_init_defaults(monkeypatch):
    monkeypatch.setenv("REDIS_DAILY_LIMIT", "5")
    m = FreeTierCacheManager(redis_url="redis://x")
    assert m.daily_limit == 5
    assert m.redis is None
    assert m.l1_cache == {}
    assert m.command_count == 0


def test_init_default_limit(monkeypatch):
    monkeypatch.delenv("REDIS_DAILY_LIMIT", raising=False)
    m = FreeTierCacheManager(redis_url="redis://x")
    assert m.daily_limit == 9000


async def test_connect_creates_and_is_idempotent(redis_pair):
    client, factory = redis_pair
    m = FreeTierCacheManager(redis_url="redis://localhost")
    await m.connect()
    assert m.redis is client
    await m.connect()  # second connect is a no-op
    assert factory.call_count == 1


async def test_disconnect_resets(redis_pair):
    client, _ = redis_pair
    m = FreeTierCacheManager(redis_url="redis://localhost")
    await m.connect()
    await m.disconnect()
    assert m.redis is None
    assert client.close.await_count == 1


def test_l1_set_get_and_eviction():
    m = FreeTierCacheManager(redis_url="redis://x")
    m._set_l1("k1", "v1")
    assert m._get_from_l1("k1") == "v1"
    m.l1_max_size = 3
    for i in range(4):
        m._set_l1(f"k{i}", f"v{i}")
    assert "k0" not in m.l1_cache
    assert len(m.l1_cache) == 3
    assert m._get_from_l1("k1") == "v1"


def test_l1_get_hit_and_miss_counters():
    m = FreeTierCacheManager(redis_url="redis://x")
    m._set_l1("a", 1)
    assert m._get_from_l1("a") == 1
    assert m.l1_hits == 1
    assert m._get_from_l1("missing") is None
    assert m.l1_misses == 1


def test_compress_and_decompress_roundtrip():
    m = FreeTierCacheManager(redis_url="redis://x")
    small = b"hi"
    assert m._compress_value(small) == small
    big = b"x" * (m.compress_threshold + 10)
    comp = m._compress_value(big)
    assert len(comp) < len(big)
    assert m._decompress_value(comp) == big
    assert m._decompress_value(b"not compressed json") == b"not compressed json"


def test_decompress_handles_garbage():
    m = FreeTierCacheManager(redis_url="redis://x")
    raw = b"\x00\x01\x02 not zlib"
    assert m._decompress_value(raw) == raw


# ---------------------------------------------------------------------------
# get()
# ---------------------------------------------------------------------------


async def test_get_l1_hit(redis_pair):
    m = FreeTierCacheManager(redis_url="redis://x")
    m._set_l1("k", {"a": 1})
    m.redis = redis_pair[0]
    assert await m.get("k") == {"a": 1}


async def test_get_from_redis_json(redis_pair):
    client, _ = redis_pair
    client.get = AsyncMock(return_value=json.dumps(7))
    m = FreeTierCacheManager(redis_url="redis://x")
    m.redis = client
    assert await m.get("k") == 7
    assert "k" in m.l1_cache  # cached in L1


async def test_get_from_redis_compressed_bytes(redis_pair):
    from core.cache_manager import FreeTierCacheManager

    client, _ = redis_pair
    import zlib

    payload = json.dumps("ok").encode()
    client.get = AsyncMock(return_value=zlib.compress(payload))
    m = FreeTierCacheManager(redis_url="redis://x")
    m.redis = client
    assert await m.get("k") == "ok"


async def test_get_redis_falsy(redis_pair):
    client, _ = redis_pair
    client.get = AsyncMock(return_value=None)
    m = FreeTierCacheManager(redis_url="redis://x")
    m.redis = client
    assert await m.get("k") is None


# ---------------------------------------------------------------------------
# set() / delete() / get_many() / stats / singleton
# ---------------------------------------------------------------------------


async def test_set_stores_l1_and_redis(redis_pair):
    client, _ = redis_pair
    m = FreeTierCacheManager(redis_url="redis://x")
    m.redis = client
    ok = await m.set("k", {"v": 1}, ttl_seconds=10)
    assert ok is True
    assert m.l1_cache["k"] == {"v": 1}
    client.setex.assert_awaited_once()


async def test_set_returns_false_when_redis_over_limit(redis_pair):
    m = FreeTierCacheManager(redis_url="redis://x")
    m.redis = redis_pair[0]
    m.command_count = m.daily_limit  # at limit -> cannot set to redis
    ok = await m.set("k", 1, ttl_seconds=10)
    assert ok is False
    assert m.l1_cache["k"] == 1


async def test_set_no_redis_returns_false():
    m = FreeTierCacheManager(redis_url="redis://x")
    ok = await m.set("k", 1, ttl_seconds=10, use_redis=False)
    assert ok is False


async def test_delete_l1_and_redis(redis_pair):
    client, _ = redis_pair
    m = FreeTierCacheManager(redis_url="redis://x")
    m.redis = client
    m._set_l1("k", 1)
    await m.delete("k")
    assert "k" not in m.l1_cache
    client.delete.assert_awaited_once_with("k")


async def test_get_many_l1_and_redis(redis_pair):
    m = FreeTierCacheManager(redis_url="redis://x")
    m._set_l1("a", 1)
    m.redis = redis_pair[0]
    redis_pair[0].mget = AsyncMock(return_value=[json.dumps({"result": "x"}), None])
    res = await m.get_many(["a", "k2"])
    assert res["a"] == 1
    assert res["k2"] == {"result": "x"}


async def test_get_many_invalid_json(redis_pair):
    client, _ = redis_pair
    m = FreeTierCacheManager(redis_url="redis://x")
    m.redis = client
    client.mget = AsyncMock(return_value=["not-json"])
    res = await m.get_many(["k"])
    assert res["k"] == "not-json"  # raw value returned on parse failure


async def test_get_many_redis_error(redis_pair):
    client, _ = redis_pair
    m = FreeTierCacheManager(redis_url="redis://x")
    m.redis = client
    client.mget = AsyncMock(side_effect=ConnectionError("boom"))
    res = await m.get_many(["k"])
    assert res == {}


def test_get_stats():
    m = FreeTierCacheManager(redis_url="redis://x")
    s = m.get_stats()
    assert s["l1_max_size"] == 100
    assert s["redis_daily_limit"] == 9000
    assert "remaining_commands" in s


def test_track_command_warns_past_limit():
    m = FreeTierCacheManager(redis_url="redis://x")
    m.daily_limit = 1
    m.command_count = 1
    with pytest.warns(UserWarning):
        m._track_command()


async def test_get_cache_manager_raises_without_url(monkeypatch):
    import core.cache_manager as cm

    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.setattr(cm, "_cache_manager", None)
    with pytest.raises(ValueError):
        await get_cache_manager()


async def test_get_cache_manager_creates_with_url(monkeypatch):
    import core.cache_manager as cm

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(cm, "_cache_manager", None)
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    with patch("redis.asyncio.from_url", return_value=client):
        mgr1 = await get_cache_manager()
        assert isinstance(mgr1, FreeTierCacheManager)
        mgr2 = await get_cache_manager()
        assert mgr2 is mgr1  # singleton
    monkeypatch.setattr(cm, "_cache_manager", None)


async def test_get_redis_error_returns_none(redis_pair):
    client, _ = redis_pair
    client.get = AsyncMock(side_effect=ConnectionError("boom"))
    m = FreeTierCacheManager(redis_url="redis://x")
    m.redis = client
    assert await m.get("k") is None
