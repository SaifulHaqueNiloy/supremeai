"""
Admin JWT fail-closed revocation tests (production-readiness plan, item 2).

নিশ্চিত করে:
- Redis ডাউন (client None) + is_admin=True  → is_token_revoked = True (fail-CLOSED)
- Redis ডাউন + is_admin=False               → is_token_revoked = False (fail-open)
- Redis সুস্থ + blacklist-এ jti             → True
- TTL-aware admin LRU cache: revoked admin jti Redis ছাড়াই ধরা পড়ে
- verify_token_async: role=admin token Redis ডাউনে 401 দেয়
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from core.security import (
    _ADMIN_REVOCATION_CACHE,
    _admin_cache_get,
    _admin_cache_put,
    is_token_revoked,
    verify_token_async,
)

pytestmark = [pytest.mark.unit, pytest.mark.security]


class _FakeRedis:
    def __init__(self, down: bool = False):
        self.client = None if down else AsyncMock()


@pytest.fixture(autouse=True)
def _clean_cache():
    _ADMIN_REVOCATION_CACHE.clear()
    yield
    _ADMIN_REVOCATION_CACHE.clear()


@pytest.mark.asyncio
async def test_admin_fail_closed_when_redis_down():
    with patch("core.cache.redis_manager.redis_manager", _FakeRedis(down=True)):
        assert await is_token_revoked("jti-admin-1", is_admin=True) is True


@pytest.mark.asyncio
async def test_regular_user_fail_open_when_redis_down():
    with patch("core.cache.redis_manager.redis_manager", _FakeRedis(down=True)):
        assert await is_token_revoked("jti-user-1", is_admin=False) is False


@pytest.mark.asyncio
async def test_revoked_jti_detected_via_redis():
    redis = _FakeRedis(down=False)
    redis.client.exists = AsyncMock(return_value=1)
    with patch("core.cache.redis_manager.redis_manager", redis):
        assert await is_token_revoked("jti-x", is_admin=False) is True
        assert await is_token_revoked("jti-x", is_admin=True) is True


@pytest.mark.asyncio
async def test_admin_lru_cache_hit_when_redis_down():
    # revoke_token করার সময় admin jti LRU-তে থাকে — Redis ডাউন হলেও ধরা পড়ে
    _admin_cache_put("jti-admin-revoked", ttl_seconds=300)
    with patch("core.cache.redis_manager.redis_manager", _FakeRedis(down=True)):
        assert await is_token_revoked("jti-admin-revoked", is_admin=True) is True


def test_admin_cache_expiry():
    import time

    _admin_cache_put("jti-ttl", ttl_seconds=60)
    assert _admin_cache_get("jti-ttl") is True
    # সরাসরি মেয়াদ উত্তীর্ণ করা হয় (put-এর max(1.0s) গার্ড এড়িয়ে)
    with __import__("core.security", fromlist=["_ADMIN_REVOCATION_LOCK"])._ADMIN_REVOCATION_LOCK:
        _ADMIN_REVOCATION_CACHE["jti-ttl"] = time.monotonic() - 1
    assert _admin_cache_get("jti-ttl") is False


def test_admin_cache_lru_bound():
    from core.security import _ADMIN_REVOCATION_CACHE_MAX

    for i in range(_ADMIN_REVOCATION_CACHE_MAX + 50):
        _admin_cache_put(f"jti-{i}")
    assert len(_ADMIN_REVOCATION_CACHE) <= _ADMIN_REVOCATION_CACHE_MAX
    # সবচেয়ে পুরনো entry evict হয়েছে
    assert _admin_cache_get("jti-0") is False
    # সর্বশেষ entry আছে
    assert _admin_cache_get(f"jti-{_ADMIN_REVOCATION_CACHE_MAX + 49}") is True


@pytest.mark.asyncio
async def test_verify_token_async_admin_401_when_redis_down():
    token = _make_admin_token()
    with patch("core.cache.redis_manager.redis_manager", _FakeRedis(down=True)):
        with pytest.raises(HTTPException) as exc_info:
            await verify_token_async(token)
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_token_async_user_ok_when_redis_down():
    token = _make_user_token()
    with patch("core.cache.redis_manager.redis_manager", _FakeRedis(down=True)):
        payload = await verify_token_async(token)
        assert payload["role"] == "user"


# ── helpers ──────────────────────────────────────────────────────────────


def _make_admin_token() -> str:
    from core.config import settings
    from core.security import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, create_access_token

    admin_email = (
        sorted(settings.admin_emails)[0] if settings.admin_emails else "admin@supremeai.dev"
    )
    return create_access_token({"sub": admin_email, "role": "admin"})


def _make_user_token() -> str:
    from core.security import create_access_token

    return create_access_token({"sub": "regular-user@supremeai.dev", "role": "user"})
