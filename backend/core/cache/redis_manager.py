"""Manages asynchronous interactions with a Redis cache for the SupremeAI ecosystem.

বাংলা: SupremeAI-এর জন্য Redis ক্যাশ ব্যবস্থাপনা। পুরোপুরি async,
event-loop blocking মুক্ত, fail-closed প্যাটার্ন অনুসরণ করে।
"""

import asyncio
import json
import os
import time
from typing import Any

from core.logging_config import logger

try:
    import redis.asyncio as aioredis
except ImportError:
    try:
        import aioredis
    except ImportError:
        aioredis = None

# Import pybreaker for circuit breaker functionality as mentioned in audit report
try:
    from pybreaker import CircuitBreaker

    _redis_circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=30, name="redis")
except ImportError:
    # Fallback if pybreaker is not installed
    class MockCircuitBreaker:
        def call(self, func, *args, **kwargs):
            return func(*args, **kwargs)

        async def call_async(self, func, *args, **kwargs):
            return await func(*args, **kwargs)

    _redis_circuit_breaker = MockCircuitBreaker()


# Quota-exhaustion signatures observed from Upstash free tier (Round-13 incident:
# 500000/500000 monthly commands exhausted → every command returned
# "max request limit exceeded" and 42–51% of boot log lines were per-request
# fallback warnings across all consumers). Matching is lowercased substring
# against the exception message; deliberately avoids bare "429"/"402" numeric
# matches to prevent false positives from key names embedded in error strings.
_REDIS_QUOTA_SIGNATURES = (
    "max request limit exceeded",
    "max requests limit exceeded",
    "request limit exceeded",
    "monthly request limit",
    "monthly limit",
    "quota exceeded",
    "quota exhausted",
    "limit exceeded",
    "too many requests",
    "payment required",
    "upgrade your plan",
    "subscription",
)

# Breaker cooldown schedule (seconds) indexed by consecutive trip count:
# first trip 15min → 30min → 1h → cap 1h. Quota exhaustion persists until
# monthly reset or plan upgrade, so probing must stay rare; half-open probes
# happen naturally when the cooldown expires and a consumer retries.
_REDIS_QUOTA_COOLDOWNS = (900.0, 1800.0, 3600.0, 3600.0)


class SecureRedisManager:
    # Issue #460 (Pillar 2): sibling free-tier account URLs, consulted in
    # order after the primary. With the current vault this yields a
    # 5-account federation pool ⇒ 5 × 500k = 2.5M ops/month at zero cost.
    _FEDERATION_ENV_KEYS = (
        "REDIS_SECONDARY_URL",
        "REDIS_TERTIARY_URL",
        "REDIS_QUATERNARY_URL",
        "REDIS_QUINARY_URL",
    )

    def __init__(self):
        from ..config import settings  # Fixed import path

        self.url = settings.redis_url or os.getenv("REDIS_URL")
        self._client = None
        self._initialized = False
        self._init_lock = asyncio.Lock()
        # Multi-account federation pool (issue #460, Pillar 2). Primary URL
        # first, then every sibling free-tier account discovered in the env.
        # On a quota-exhaustion trip the manager FAILS OVER to the next pool
        # instead of dropping all consumers to in-memory fallbacks — N
        # accounts ⇒ N× monthly quota, zero code change for consumers.
        self._urls: list[str] = []  # resolved lazily at first connect (vault-aware)
        self._active = 0
        self._tripped: set[int] = set()
        # Quota circuit-breaker state (issue #437). While open,
        # get_client_async() returns None and every consumer engages its own
        # documented in-memory fallback — the same fail-closed contract as the
        # "memory://" scheme below. Zero network round-trips are attempted
        # against a quota-exhausted provider while the breaker is open.
        self._quota_open_until = 0.0
        self._quota_trips = 0
        self._quota_announced = False

    @staticmethod
    def _resolve_secret(key: str) -> str:
        """Resolve a secret from process env first, then the Infisical vault.

        বাংলা: 12-factor — প্রথমে os.getenv, না পেলে config_secrets-এর
        vault-aware cache (bulk লোড হয়ে গেলে কোনো নেটওয়ার্ক কল নেই)।
        """
        val = (os.getenv(key) or "").strip()
        if val:
            return val
        try:
            from ..config import settings

            return (settings._get_cached_secret(key) or "").strip()
        except Exception:  # noqa: BLE001 — resolver must never break init
            return ""

    def _collect_federation_urls(self) -> list[str]:
        """Primary + sibling account URLs (deduped, memory:// excluded).

        বাংলা: প্রাইমারি REDIS_URL ছাড়াও REDIS_{SECONDARY,TERTIARY,QUATERNARY,
        QUINARY}_URL এবং REDIS_FEDERATION_URLS (comma-separated) থেকে
        ফেডারেশন পুল তৈরি হয়। memory:// স্কিম বাদ — সেটা কনজিউমারের নিজস্ব
        in-memory fallback চুক্তি।
        """
        urls: list[str] = []
        primary = self.url
        if primary and "memory://" not in primary:
            urls.append(primary)
        for key in self._FEDERATION_ENV_KEYS:
            val = self._resolve_secret(key)
            if val and "memory://" not in val and val not in urls:
                urls.append(val)
        for val in self._resolve_secret("REDIS_FEDERATION_URLS").split(","):
            val = val.strip()
            if val and "memory://" not in val and val not in urls:
                urls.append(val)
        return urls

    @staticmethod
    def _is_quota_error(exc: BaseException) -> bool:
        """Classify an exception as provider quota exhaustion."""
        message = str(exc).lower()
        return any(sig in message for sig in _REDIS_QUOTA_SIGNATURES)

    @property
    def quota_breaker_open(self) -> bool:
        """True while the quota circuit breaker is tripped (no Redis attempts)."""
        return time.monotonic() < self._quota_open_until

    def report_failure(self, exc: BaseException) -> None:
        """Report a Redis operation failure for quota-breaker classification.

        বাংলা: Redis কনজিউমাররা (rate limiter, security middleware, cache)
        নিজেরা exception ধরে fallback-এ চলে যায় — এই মেথড সেই failure গুলো
        ব্রেকারকে জানায় যাতে quota-exhausted provider-এর বিরুদ্ধে প্রতি
        রিকোয়েস্টে অপ্রয়োজনীয় network round-trip ও log-storm বন্ধ হয়।
        """
        if not self._is_quota_error(exc):
            return
        if self.quota_breaker_open:
            return  # already tripped; nothing new to announce
        # Issue #460 (Pillar 2): try to fail over to the next federation pool
        # BEFORE degrading every consumer to in-memory fallbacks.
        if self._try_failover(exc):
            return
        cooldown = _REDIS_QUOTA_COOLDOWNS[min(self._quota_trips, len(_REDIS_QUOTA_COOLDOWNS) - 1)]
        self._quota_trips += 1
        self._quota_open_until = time.monotonic() + cooldown
        if not self._quota_announced:
            self._quota_announced = True
            logger.critical(
                "🔥 Redis provider QUOTA EXHAUSTED (%s) — quota circuit breaker OPEN for "
                "%.0fs. All Redis consumers now run on their documented in-memory "
                "fallbacks (per-instance, NOT aggregate-safe). Zero further commands "
                "will be attempted until the probe window. Fix: upgrade the Redis "
                "plan or wait for quota reset.",
                str(exc)[:160],
                cooldown,
            )
        else:
            logger.warning(
                "Redis quota breaker re-tripped (%s) — cooldown %.0fs (trip #%d).",
                str(exc)[:160],
                cooldown,
                self._quota_trips,
            )

    def _try_failover(self, exc: BaseException) -> bool:
        """Rotate to the next untripped federation pool on quota exhaustion.

        বাংলা: বর্তমান অ্যাকাউন্টের কোটা শেষ হলে পরের পুলে failover করে —
        সব পুল শেষ না হলে কনজিউমাররা কখনোই in-memory fallback-এ যায় না।
        Returns True when a healthy next pool took over.
        """
        if len(self._urls) <= 1 or not self._initialized:
            return False
        failed_index = self._active
        self._tripped.add(failed_index)
        nxt = next((i for i in range(len(self._urls)) if i not in self._tripped), None)
        if nxt is None:
            return False  # every pool exhausted → caller opens the breaker
        old_client = self._client
        self._active = nxt
        self._client = None
        self._initialized = False  # rebuild against the new pool on next use
        # The new pool has fresh quota — reset breaker state for it.
        self._quota_trips = 0
        self._quota_open_until = 0.0
        # Drop the old pool's sockets without blocking the caller.
        aclose = getattr(old_client, "aclose", None)
        if aclose is not None:
            try:
                asyncio.get_running_loop().create_task(aclose())
            except RuntimeError:
                pass
        logger.critical(
            "🔥 Redis federation pool %d/%d QUOTA EXHAUSTED (%s) — failed over to "
            "pool %d/%d. Consumers keep running on real Redis (no in-memory "
            "degradation). %d pool(s) remain.",
            failed_index + 1,
            len(self._urls),
            str(exc)[:120],
            nxt + 1,
            len(self._urls),
            len(self._urls) - len(self._tripped),
        )
        return True

    async def _reset_federation_probe(self) -> None:
        """Half-open reset: every pool tripped + cooldown expired → probe cycle
        restarts cleanly at pool 1. বাংলা: সব পুল শেষ হয়ে কুলডাউন শেষ হলে
        আবার পুল ১ থেকে প্রোব শুরু হয়।"""
        old_client = self._client
        self._tripped.clear()
        self._active = 0
        self._client = None
        self._initialized = False
        if old_client is not None:
            try:
                await old_client.aclose()
            except Exception:  # noqa: BLE001 — probe reset must never raise
                pass
        await self._ensure_connected()

    async def _ensure_connected(self) -> None:
        """Async-safe Redis connection initialization with locking.

        বাংলা: async lock ব্যবহার করে শুধুমাত্র একবার Redis কানেকশন ইনিশিয়ালাইজ করে।
        Synchronous fallback সম্পূর্ণ মুক্ত — event loop ব্লক করে না।
        """
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            # FIX (memory-fallback contract): REDIS_URL="memory://" is the codebase's
            # documented in-memory fallback scheme (core/rate_limit.py,
            # core/middleware/security.py, tests). redis-py cannot parse it, and the
            # settings normalizer (config_secrets.redis_url) mangles it into a
            # VALID-looking TCP URL "redis://memory://" — so this method used to build
            # a broken TCP pool and cache the client on the SINGLETON. Any later
            # consumer (e.g. TenantRateLimiter with redis_client=None) then hit a
            # real ConnectionError storm against host "memory" instead of falling
            # back to its own documented in-memory path (observed: health-check
            # poisoning billing tests in group runs; 4 failures, order-dependent).
            # Honor the contract: stay fail-closed (client None) for the memory
            # scheme — both the plain and the mangled-normalized form — so every
            # consumer engages its own in-memory fallback. Real redis URLs are
            # completely unaffected.
            # Issue #460: resolve the federation pool lazily at connect time —
            # sibling URLs may live in the Infisical vault, not just os.environ.
            self._urls = self._collect_federation_urls()
            if not self._urls:
                if self.url and "memory://" in self.url:
                    logger.info(
                        "REDIS_URL memory:// in-memory fallback active — SecureRedisManager "
                        "stays fail-closed (no TCP client); consumers use their documented "
                        "in-memory fallbacks."
                    )
                else:
                    logger.critical(
                        "🔥 CRITICAL: Serverless Redis Endpoint Missing! System entering Fail-Closed state."
                    )
                self._initialized = True
                return
            if aioredis is not None:
                pool = aioredis.ConnectionPool.from_url(
                    self._urls[self._active],
                    max_connections=20,
                    socket_keepalive=True,
                    socket_connect_timeout=5.0,
                    decode_responses=True,
                )
                self._client = aioredis.Redis(connection_pool=pool)
                if len(self._urls) > 1:
                    logger.info(
                        "⚡ Serverless Redis federation pool %d/%d active with Connection Pool "
                        "(limit=20) — issue #460 multi-account failover enabled.",
                        self._active + 1,
                        len(self._urls),
                    )
                else:
                    logger.info(
                        "⚡ Serverless Upstash Redis REST Provider Active with Connection Pool (limit=20)."
                    )
            else:
                logger.critical(
                    "🔥 CRITICAL: redis.asyncio unavailable! System entering Fail-Closed state."
                )
            self._initialized = True

    async def get_client_async(self) -> Any:
        """Get Redis client with async-safe initialization.

        বাংলা: async-safe Redis ক্লায়েন্ট রিটার্ন করে।
        সকল মডিউলের উচিত এই মেথড ব্যবহার করা, `.client` প্রপার্টি না।
        """
        await self._ensure_connected()
        # Quota breaker (issue #437): while tripped, hand back None so every
        # consumer engages its own documented in-memory fallback immediately —
        # no network round-trips against a quota-exhausted provider.
        if self._client is not None and self.quota_breaker_open:
            return None
        # Issue #460 half-open probe: every pool tripped and the cooldown has
        # now expired → restart a clean probe cycle at pool 1.
        if self._tripped and len(self._tripped) >= len(self._urls) and not self.quota_breaker_open:
            await self._reset_federation_probe()
        return self._client

    @property
    def client(self) -> aioredis.Redis | None:
        """Sync property accessor — returns existing client without blocking.

        বাংলা: synchronous accessor যা event loop ব্লক না করেই বিদ্যমান ক্লায়েন্ট রিটার্ন করে।
        যদি ক্লায়েন্ট এখনো ইনিশিয়ালাইজ না হয়, তাহলে None রিটার্ন করে (fail-closed)।
        সকল কনজিউমার ইতিমধ্যেই ``if redis_manager.client:`` চেক করে, তাই এটি নিরাপদ।

        Note: যদি ক্লায়েন্ট ইনিশিয়ালাইজ না হয়, তাহলে None রিটার্ন হবে।
        Prefer ``await redis_manager.get_client_async()`` for guaranteed initialization.
        """
        # বাংলা: কোনো অবস্থাতেই event loop ব্লক করে এমন synchronous init করব না।
        # _initialized True না হলে None রিটার্ন করি — consumer fail-closed behaviour handle করবে।
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if Redis client is initialized and ready.

        বাংলা: Redis ক্লায়েন্ট ইনিশিয়ালাইজ হয়েছে কিনা চেক করে।
        """
        return self._client is not None

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
            self._initialized = False
        self._active = 0
        self._tripped.clear()

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        client = await self.get_client_async()
        if not client:
            return False
        try:
            await client.set(key, value, ex=ex)
            return True
        except Exception as exc:
            self.report_failure(exc)
            logger.error(f"Redis SET error: {exc}")
            return False

    async def set_cache(self, key: str, value: str, ex_seconds: int | None = None) -> bool:
        """Alias for set(), supporting ex_seconds parameter."""
        return await self.set(key, value, ex=ex_seconds)

    async def get(self, key: str) -> str | None:
        client = await self.get_client_async()
        if not client:
            return None
        try:
            return await client.get(key)
        except Exception as exc:
            self.report_failure(exc)
            logger.error(f"Redis GET error: {exc}")
            return None

    async def get_cache(self, key: str) -> str | None:
        """Alias for get()."""
        return await self.get(key)

    async def delete(self, key: str) -> bool:
        client = await self.get_client_async()
        if not client:
            return False
        try:
            await client.delete(key)
            return True
        except Exception as exc:
            self.report_failure(exc)
            logger.error(f"Redis DELETE error: {exc}")
            return False

    async def set_json(self, key: str, data: dict, ex: int | None = None) -> bool:
        return await self.set(key, json.dumps(data), ex=ex)

    async def get_json(self, key: str) -> dict | None:
        val = await self.get(key)
        if not val:
            return None
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return None

    # REMOVED: _execute_with_breaker method due to critical bug and unused status
    # As per audit report Phase 3, Section 3.1: This method had a critical bug where
    # pybreaker.CircuitBreaker.call() was called with a coroutine that was never awaited,
    # and the method was never actually called anywhere in the codebase.

    async def incrbyfloat(self, key: str, amount: float, ex_seconds: int = 86400) -> float:
        """Increment floating point value in Redis with optional expiration.

        বাংলা: Redis-এ ফ্লোটিং পয়েন্ট মান বৃদ্ধি করে এবং TTL সেট করে।
        """
        client = await self.get_client_async()
        if client:
            try:
                val = await client.incrbyfloat(key, amount)
                if ex_seconds:
                    await client.expire(key, ex_seconds)
                return float(val)
            except Exception as exc:
                self.report_failure(exc)
                logger.error(f"Redis INCRBYFLOAT error: {exc}")
                return 0.0
        return 0.0


redis_manager = SecureRedisManager()


class IdempotencyUnavailableError(Exception):
    """Raised when Redis idempotency lock fails or is unavailable."""

    pass


class _AcquireIdempotencyLockContext:
    def __init__(self, key: str, ttl: int = 60, fail_closed: bool = True):
        self.key = f"idempotency:{key}"
        self.ttl = ttl
        self.fail_closed = fail_closed
        self.acquired = False

    async def __aenter__(self):
        client = await redis_manager.get_client_async()
        if client:
            try:
                self.acquired = await client.set(self.key, "locked", nx=True, ex=self.ttl)
            except Exception as exc:
                redis_manager.report_failure(exc)
                logger.error(f"Failed to set idempotency lock in Redis: {exc}")
                self.acquired = False
        if not self.acquired and self.fail_closed:
            raise IdempotencyUnavailableError(f"Idempotency lock unavailable for key: {self.key}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            try:
                await redis_manager.delete(self.key)
            except Exception as exc:
                logger.error(f"Failed to release idempotency lock: {exc}")

    def __await__(self):
        async def _run():
            try:
                async with self as lock:
                    return True if not self.fail_closed else lock.acquired
            except IdempotencyUnavailableError:
                if self.fail_closed:
                    raise
                return True

        return _run().__await__()


def acquire_idempotency_lock(key: str, ttl: int = 60, fail_closed: bool = True):
    return _AcquireIdempotencyLockContext(key, ttl=ttl, fail_closed=fail_closed)


async def release_idempotency_lock(key: str) -> bool:
    """Release an idempotency lock immediately.

    বাংলা মন্তব্য: idempotency lock manually release করার জন্য।
    যখন একটি অনুরোধ সফলভাবে সম্পন্ন হয়, তখন lock release করা উচিত।
    """
    try:
        redis_key = f"idempotency:{key}"
        deleted = await redis_manager.delete(redis_key)
        if deleted:
            logger.debug(f"Idempotency lock released for key: {key}")
            return True
        else:
            logger.warning(f"Idempotency lock not found for key: {key}")
            return False
    except Exception as exc:
        logger.error(f"Failed to release idempotency lock for key {key}: {exc}")
        return False


class _TTLCacheItem:
    """TTL-ভিত্তিক ক্যাশ আইটেম — স্বয়ংক্রিয় মেয়াদোত্তীর্ণ (Bangla: TTL-based cache item with auto-expiry)"""

    __slots__ = ("expires_at", "value")

    def __init__(self, value: Any, ttl: int = 60):
        self.value = value
        self.expires_at = time.monotonic() + ttl

    @property
    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class TTLCacheDict:
    """TTL-সক্ষম ইন-মেমরি ক্যাশ ডিকশনারি (Bangla: TTL-enabled in-memory cache dictionary with auto-cleanup)"""

    def __init__(self, default_ttl: int = 60, maxsize: int = 2000):
        self._store: dict[str, _TTLCacheItem] = {}
        self._default_ttl = default_ttl
        self._maxsize = maxsize
        self._last_cleanup = time.monotonic()

    def get(self, key: str) -> Any | None:
        """মেয়াদোত্তীর্ণ চেক করে ভ্যালু রিটার্ন করে (Bangla: Get value with expiry check)"""
        item = self._store.get(key)
        if item is None:
            return None
        if item.is_expired:
            del self._store[key]
            return None
        return item.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """TTL সহ ভ্যালু সংরক্ষণ (Bangla: Store value with TTL)"""
        if len(self._store) >= self._maxsize:
            self._evict_lru()
        self._store[key] = _TTLCacheItem(value, ttl or self._default_ttl)

    def delete(self, key: str) -> None:
        """ক্যাশ থেকে কী মুছে ফেলা (Bangla: Delete key from cache)"""
        self._store.pop(key, None)

    def clear(self) -> None:
        """সম্পূর্ণ ক্যাশ পরিষ্কার (Bangla: Clear entire cache)"""
        self._store.clear()

    @property
    def size(self) -> int:
        """বর্তমান ক্যাশ সাইজ (Bangla: Current cache size)"""
        return len(self._store)

    def _evict_lru(self) -> None:
        """সবচেয়ে পুরনো আইটেম সরিয়ে ফেলা (Bangla: Evict oldest item)"""
        if not self._store:
            return
        oldest_key = min(self._store.keys(), key=lambda k: self._store[k].expires_at)
        del self._store[oldest_key]

    def cleanup_expired(self) -> int:
        """মেয়াদোত্তীর্ণ আইটেমসমূহ পরিষ্কার (Bangla: Remove all expired items)"""
        now = time.monotonic()
        expired = [k for k, v in self._store.items() if v.expires_at <= now]
        for k in expired:
            del self._store[k]
        return len(expired)


class MultiLevelCache:
    """Multi-Level Cache System — L1 (TTL In-Memory) & L2 (Redis). (Bangla: মাল্টি-লেভেল ক্যাশে সিস্টেম)

    L1: TTL-ভিত্তিক ইন-মেমরি ক্যাশ (default TTL: ৬০ সেকেন্ড)
    L2: Redis ক্যাশ (TTL কনফিগারেবল)
    Optimization: L1 TTL L2 TTL-এর চেয়ে ছোট — stale data পড়ার রিস্ক কম
    """

    def __init__(
        self, redis_mgr: SecureRedisManager | None = None, l1_ttl: int = 60, l2_ttl: int = 3600
    ):
        self._l1_cache = TTLCacheDict(default_ttl=l1_ttl, maxsize=2000)
        self._l2_ttl = l2_ttl
        self.redis_cache = redis_mgr or redis_manager

    @property
    def local_cache(self) -> dict[str, Any]:
        """Backward-compatibility wrapper mapping local_cache accesses to L1 store."""

        class _LocalCacheDictAdapter(dict):
            def __init__(self, outer: MultiLevelCache):
                self.outer = outer

            def __getitem__(self, key: str) -> Any:
                val = self.outer._l1_cache.get(key)
                if val is None:
                    raise KeyError(key)
                return val

            def __setitem__(self, key: str, value: Any) -> None:
                self.outer._l1_cache.set(key, value)

            def __delitem__(self, key: str) -> None:
                self.outer._l1_cache.delete(key)

            def __contains__(self, key: object) -> bool:
                return self.outer._l1_cache.get(str(key)) is not None

            def pop(self, key: str, default: Any = None) -> Any:
                val = self.outer._l1_cache.get(key)
                if val is not None:
                    self.outer._l1_cache.delete(key)
                    return val
                return default

            def clear(self) -> None:
                self.outer._l1_cache.clear()

        return _LocalCacheDictAdapter(self)

    async def get(self, key: str) -> Any:
        """L1 (TTL মেমরি) → L2 (Redis) — ক্রমান্বয়ে চেক (Bangla: Cascade check L1→L2)

        L1 TTL L2 TTL-এর চেয়ে ছোট (৬০s vs ৩৬০০s) — L1 মেয়াদোত্তীর্ণ হলেও
        L2 থেকে তাজা ডাটা নিয়ে L1 ওয়ার্ম-আপ করা যায়।
        """
        # L1 — TTL-ভিত্তিক দ্রুত চেক
        l1_val = self._l1_cache.get(key)
        if l1_val is not None:
            return l1_val

        # L2 — Redis থেকে আনা
        val = await self.redis_cache.get_cache(key)
        if val is not None:
            # L1 ওয়ার্ম-আপ — Redis থেকে পাওয়া ডাটা L1-তেও সংরক্ষণ
            self._l1_cache.set(key, val)
        return val

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """L1 ও L2 উভয় জায়গায় একসাথে ক্যাশ সংরক্ষণ (Bangla: Set in both L1 and L2)

        L1 TTL সবসময় L2 TTL-এর চেয়ে ছোট বা সমান হবে।
        """
        if value is None:
            return  # Bangla: None ডাটা ক্যাশে করবেন না, স্পেস বাঁচান
        effective_ttl = ttl or self._l2_ttl
        # L1 — ছোট TTL (max ৬০s বা কনফিগারেবল)
        l1_ttl = min(effective_ttl, self._l1_cache._default_ttl)
        self._l1_cache.set(key, value, ttl=l1_ttl)
        # L2 — পূর্ণ TTL
        await self.redis_cache.set_cache(
            key, str(value) if not isinstance(value, str) else value, ex_seconds=effective_ttl
        )

    def invalidate_local(self, key: str | None = None) -> None:
        """L1 ইন-মেমরি ক্যাশ পরিষ্কার (Bangla: Clear L1 cache)

        Args:
            key: নির্দিষ্ট কী (None হলে সম্পূর্ণ ক্যাশ ক্লিয়ার)
        """
        if key:
            self._l1_cache.delete(key)
        else:
            self._l1_cache.clear()

    async def invalidate(self, key: str | None = None) -> None:
        """L1 + L2 উভয় ক্যাশ ইনভ্যালিডেট (Bangla: Invalidate both L1 and L2)

        Stale cache প্রতিরোধে L1 এবং L2 একসাথে ক্লিয়ার করা হয়।
        """
        self.invalidate_local(key)
        if key:
            await self.redis_cache.delete(key)

    def cleanup_expired_l1(self) -> int:
        """মেয়াদোত্তীর্ণ L1 ক্যাশ আইটেমসমূহ পরিষ্কার (Bangla: Cleanup expired L1 items)

        Returns:
            কতগুলি আইটেম ক্লিয়ার করা হয়েছে
        """
        return self._l1_cache.cleanup_expired()
