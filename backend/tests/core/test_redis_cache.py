"""Tests for core.cache.redis_manager — SecureRedisManager & IdempotencyLock."""

import pytest

from core.cache.redis_manager import (
    IdempotencyUnavailableError,
    SecureRedisManager,
    _AcquireIdempotencyLockContext,
    acquire_idempotency_lock,
    redis_manager,
)


@pytest.fixture
def manager():
    """Create a fresh SecureRedisManager for each test."""
    m = SecureRedisManager()
    m._client = None
    m._initialized = False
    return m


class TestSecureRedisManagerInitialization:
    """SecureRedisManager init & connection tests."""

    @pytest.mark.anyio
    async def test_init_no_url(self, monkeypatch):
        """No REDIS_URL → _client remains None, _initialized False."""
        monkeypatch.setenv("REDIS_URL", "")
        from core.config import settings

        old = settings.redis_url
        settings.redis_url = ""
        try:
            mgr = SecureRedisManager()
            assert mgr._client is None
            assert mgr._initialized is False
        finally:
            settings.redis_url = old

    @pytest.mark.anyio
    async def test_ensure_connected_no_url(self, monkeypatch):
        """No URL → _ensure_connected logs critical, _initialized True."""
        monkeypatch.setenv("REDIS_URL", "")
        from core.config import settings

        old = settings.redis_url
        settings.redis_url = ""
        try:
            mgr = SecureRedisManager()
            await mgr._ensure_connected()
            assert mgr._initialized is True
            assert mgr._client is None
        finally:
            settings.redis_url = old

    @pytest.mark.anyio
    async def test_get_client_async_returns_none_when_no_url(self, monkeypatch):
        """get_client_async returns None when no Redis URL configured."""
        monkeypatch.setenv("REDIS_URL", "")
        from core.config import settings

        old = settings.redis_url
        settings.redis_url = ""
        try:
            mgr = SecureRedisManager()
            client = await mgr.get_client_async()
            assert client is None
        finally:
            settings.redis_url = old

    @pytest.mark.anyio
    async def test_init_lock_prevents_race(self, monkeypatch):
        """_init_lock prevents double initialization."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        from core.config import settings

        old = settings.redis_url
        settings.redis_url = "redis://localhost:6379/0"
        try:
            mgr = SecureRedisManager()
            await mgr._ensure_connected()
            await mgr._ensure_connected()
            assert mgr._initialized is True
        finally:
            settings.redis_url = old

    @pytest.mark.anyio
    async def test_client_property_sync_fallback(self, monkeypatch):
        """client property triggers sync fallback init."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
        from core.config import settings

        old = settings.redis_url
        settings.redis_url = "redis://localhost:6379/0"
        try:
            mgr = SecureRedisManager()
            mgr._initialized = False
            mgr._client = None
            _ = mgr.client
            assert mgr._initialized is True
        finally:
            settings.redis_url = old


class TestSecureRedisManagerOperations:
    """SecureRedisManager SET/GET/DELETE operations."""

    @pytest.mark.anyio
    async def test_set_no_client(self, manager):
        result = await manager.set("key", "value")
        assert result is False

    @pytest.mark.anyio
    async def test_get_no_client(self, manager):
        result = await manager.get("key")
        assert result is None

    @pytest.mark.anyio
    async def test_delete_no_client(self, manager):
        result = await manager.delete("key")
        assert result is False

    @pytest.mark.anyio
    async def test_set_cache_alias(self, manager):
        result = await manager.set_cache("k", "v", ex_seconds=60)
        assert result is False

    @pytest.mark.anyio
    async def test_get_cache_alias(self, manager):
        result = await manager.get_cache("k")
        assert result is None

    @pytest.mark.anyio
    async def test_set_json_no_client(self, manager):
        result = await manager.set_json("k", {"a": 1})
        assert result is False

    @pytest.mark.anyio
    async def test_get_json_no_client(self, manager):
        result = await manager.get_json("k")
        assert result is None


class TestRedisManagerClose:
    """SecureRedisManager.close() behavior."""

    @pytest.mark.anyio
    async def test_close_without_client(self, manager):
        await manager.close()
        assert manager._client is None


class TestModuleLevelSingleton:
    """Module-level redis_manager singleton."""

    def test_redis_manager_is_instance(self):
        assert isinstance(redis_manager, SecureRedisManager)


class TestIdempotencyLock:
    """_AcquireIdempotencyLockContext & acquire_idempotency_lock."""

    @pytest.mark.anyio
    async def test_acquire_no_client_fail_closed(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "")
        from core.config import settings

        old = settings.redis_url
        settings.redis_url = ""
        try:
            redis_manager._initialized = False
            redis_manager._client = None
            with pytest.raises(IdempotencyUnavailableError):
                async with acquire_idempotency_lock("test-key", fail_closed=True):
                    pass
        finally:
            settings.redis_url = old

    @pytest.mark.anyio
    async def test_acquire_no_client_fail_open(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "")
        from core.config import settings

        old = settings.redis_url
        settings.redis_url = ""
        try:
            redis_manager._initialized = False
            redis_manager._client = None
            async with acquire_idempotency_lock("test-key", fail_closed=False):
                pass
        finally:
            settings.redis_url = old

    @pytest.mark.anyio
    async def test_lock_context_manager(self):
        ctx = _AcquireIdempotencyLockContext("test", ttl=30, fail_closed=False)
        async with ctx as lock:
            assert lock is ctx
            assert ctx.acquired is False

    def test_lock_context_key_format(self):
        ctx = _AcquireIdempotencyLockContext("my-key")
        assert ctx.key == "idempotency:my-key"

    @pytest.mark.anyio
    async def test_lock_acquire_release_exit(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "")
        from core.config import settings

        old = settings.redis_url
        settings.redis_url = ""
        try:
            ctx = _AcquireIdempotencyLockContext("test", fail_closed=False)
            async with ctx:
                pass
        finally:
            settings.redis_url = old
