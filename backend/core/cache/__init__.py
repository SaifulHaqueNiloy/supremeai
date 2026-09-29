"""Cache initialization and SimpleCacheProxy helper."""

# বাংলা মন্তব্য: ক্যাশ প্যাকেজ ইনিশিয়ালাইজেশন এবং এজেন্টদের জন্য সাধারণ গেট ও সেট মেথড সম্পন্ন ক্যাশ প্রক্সি ক্লাস।

from __future__ import annotations

import json
from typing import Any

# ISOLATION FIX (#2551, full-tier red): `from .redis_manager import
# redis_manager` circular-import-timing-এ SUBMODULE-ই bind করতে পারে
# (from-package fallback) — ফলে SimpleCacheProxy.get রানটাইমে
# "module has no attribute get_cache" দিত (tests/services/
# test_minio_client.py প্রমাণ)। রিপো-প্রতিষ্ঠিত সমাধান (#2207 — state_store/
# circuit_breaker/observability_middleware-এ একই প্যাটার্ন): ব্যবহারের
# জায়গায় function-local import — তখন singleton সম্পূর্ণ initialized।


class SimpleCacheProxy:
    """A clean wrapper around SecureRedisManager for simple key-value retrieval."""

    async def get(self, key: str) -> Any | None:
        """Get value from cache and deserialize JSON if applicable."""
        # বাংলা মন্তব্য: ক্যাশ থেকে কি (key) রিড করা এবং ডি-সিরিয়ালাইজ করা
        from core.cache.redis_manager import redis_manager  # #2551: call-time instance

        val = await redis_manager.get_cache(key)
        if val is not None:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Serialize and save value to cache with expiration TTL."""
        # বাংলা মন্তব্য: ক্যাশে ডাটা সিরিয়ালাইজ করে সেভ করা
        from core.cache.redis_manager import redis_manager  # #2551: call-time instance

        val_str = json.dumps(value)
        await redis_manager.set_cache(key, val_str, ex_seconds=ttl)


def get_cache() -> SimpleCacheProxy:
    """Return the SimpleCacheProxy instance."""
    return SimpleCacheProxy()


def get_redis_client() -> Any:
    """Return the raw redis client for custom operations."""
    from core.cache.redis_manager import redis_manager  # #2551: call-time instance

    return redis_manager.client
