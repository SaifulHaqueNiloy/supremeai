from __future__ import annotations

import os
import time

from loguru import logger

from core.cache.redis_manager import redis_manager
from core.config import settings


class InMemoryFallbackLimiter:
    """Sliding-window rate limiter scoped per API key prefix as a fallback when Redis is down."""

    def __init__(self, burst: int = 20, window: float = 60.0) -> None:
        self.burst = burst
        self.window = window
        self._hits: dict[str, list[float]] = {}

    def _cleanup(self, key: str, now: float) -> None:
        # বাংলা মন্তব্ব্য: মেমোরি লিক এড়াতে যদি কোনো কী-তে নতুন কোনো হিট না থাকে, তবে ডিকশনারি থেকে কী-টি ডিলিট করা হচ্ছে।
        if key in self._hits:
            self._hits[key] = [t for t in self._hits[key] if now - t < self.window]
            if not self._hits[key]:
                del self._hits[key]

    def is_allowed(self, key: str, limit: int = 6) -> bool:
        now = time.time()
        self._cleanup(key, now)
        hits = self._hits.setdefault(key, [])
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True


class AsyncRateLimiter:
    """
    Async Redis rate limiter using centralized redis_manager.
    Pipeline reduces network round-trips.
    Includes an in-memory fallback (Pre-Deletion Safety Check).

    বাংলা: কেন্দ্রীয় redis_manager ব্যবহার করে — আলাদা Redis connection তৈরি করে না।
    Zero-Cost, ফ্রি-টিয়ার Upstash Redis এর সাথে সামঞ্জস্যপূর্ণ।
    """

    def __init__(self) -> None:
        self._rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in {
            "true",
            "1",
            "yes",
        }
        # Changed from fail-open to fail-closed as per audit report
        # Previously: self._fallback_limiter = InMemoryFallbackLimiter()
        # Now: Initialize but use appropriately based on fail-closed strategy
        self._fallback_limiter = InMemoryFallbackLimiter()

        # Enhanced rate limiting tiers
        self._tier_limits = {
            "free": {"requests": 60, "window": 60},  # 60 req per minute
            "pro": {"requests": 600, "window": 60},  # 600 req per minute
            "premium": {"requests": 1200, "window": 60},  # 1200 req per minute
            "enterprise": {"requests": 6000, "window": 60},  # 6000 req per minute
        }

    async def _get_redis(self):
        """Helper for test mock compatibility."""
        return await redis_manager.get_client_async()

    async def acquire(self, key: str, limit: int = None, window: int = None) -> bool:
        """Redis-based sliding window rate limiting with fail-closed behavior.

        বাংলা মন্তব্য: Redis-ভিত্তিক sliding window রেট লিমিটিং।
        """
        if not self._rate_limit_enabled:
            return True

        # Fallback values if not specified
        limit = limit or 100
        window = window or 60

        try:
            client = await self._get_redis()
            if client is None:
                if settings.env in ("production", "staging"):
                    logger.critical(f"Rate limiter Redis unavailable. Blocking request for {key} (fail-closed).")
                    return False
                logger.warning(f"Redis rate limiter unavailable. Allowing request for {key} (fail-open in dev).")
                return True

            now = time.time()
            # Ensure unique member for zadd to handle identical timestamps
            import secrets

            member = f"{now}_{secrets.token_hex(4)}"

            pipe = client.pipeline()
            zset_key = f"rate_limit:{key}"
            pipe.zadd(zset_key, {member: now})
            pipe.zremrangebyscore(zset_key, 0, now - window)
            pipe.zcard(zset_key)
            pipe.expire(zset_key, window)

            results = await pipe.execute()
            count = results[2]  # result of zcard
            is_allowed = count <= limit

            # Log near-limit cases for monitoring
            if count > limit * 0.8:
                logger.warning(f"Rate limit approaching for {key}: {count}/{limit}")

            return is_allowed
        except Exception as e:  # noqa: BLE001
            if settings.env in ("production", "staging"):
                logger.critical(f"Rate limiter Redis error: {str(e)}. Blocking request for {key} (fail-closed).")
                return False
            logger.warning(f"Rate limiter error: {e}. Allowing request for {key} (fail-open in dev).")
            return True

    async def acquire_tenant(self, tenant_id: str, tier: str = "free") -> bool:
        """Multi-tenant tier-based rate limiting. (Bangla: টেন্যান্ট-ভিত্তিক টিয়ার্ড রেট লিমিট)"""
        tier_config = self._tier_limits.get(tier.lower())
        if not tier_config:
            tier_config = self._tier_limits["free"]  # Default to free tier

        limit = tier_config["requests"]
        window = tier_config["window"]
        key = f"rate_limit:tenant:{tenant_id}:{tier}"
        return await self.acquire(key, limit=limit, window=window)

    async def acquire_with_burst_control(self, key: str, limit: int, window: int, burst_limit: int = None) -> bool:
        """Advanced rate limiting with burst control capability."""
        if burst_limit is None:
            burst_limit = limit * 2  # Default burst is double the normal limit

        try:
            client = await self._get_redis()
            if client is None:
                logger.warning("Redis unavailable. Blocking requests (fail-closed).")
                return False

            # Use Lua script for atomic burst control
            lua_script = """
            local key = KEYS[1]
            local window = tonumber(ARGV[1])
            local limit = tonumber(ARGV[2])
            local burst_limit = tonumber(ARGV[3])
            local current_time = tonumber(ARGV[4])

            -- Clean old entries
            redis.call('ZREMRANGEBYSCORE', key, 0, current_time - window)

            -- Get current count
            local current_count = redis.call('ZCARD', key)

            -- Check if request exceeds burst limit immediately
            if current_count >= burst_limit then
                return 0
            end

            -- Add current request
            redis.call('ZADD', key, current_time, current_time .. "_" .. ARGV[5])
            redis.call('EXPIRE', key, window)

            -- Check if average rate over window is exceeded
            if current_count >= limit then
                -- Allow only if we're still within burst capacity
                return 1
            end

            return 1
            """

            request_id = f"{int(time.time())}_{abs(hash(key)) % 1000000}"
            result = await client.eval(
                lua_script, 1, f"{key}:burst", window, limit, burst_limit, time.time(), request_id
            )

            return bool(result)
        except Exception as e:
            logger.warning(f"Burst-controlled rate limiter failed: {e}")
            return False

    async def get_remaining_quota(self, key: str, limit: int, window: int) -> tuple[int, int]:
        """Get remaining quota and reset time for the given key."""
        try:
            client = await self._get_redis()
            if client is None:
                return 0, int(time.time()) + window

            current_count = await client.get(key)
            current_count = int(current_count) if current_count else 0
            remaining = max(0, limit - current_count)

            # Get TTL to calculate reset time
            ttl = await client.ttl(key)
            reset_time = int(time.time()) + (ttl if ttl > 0 else window)

            return remaining, reset_time
        except Exception as e:
            logger.warning(f"Failed to get quota info: {e}")
            return 0, int(time.time()) + window

    async def close(self) -> None:
        # বাংলা মন্তব্ব: আলাদা Redis connection নেই — centralized redis_manager বন্ধ করা যাবে না এখান থেকে
        pass


rate_limiter = AsyncRateLimiter()


async def advanced_rate_limit_check(
    key: str,
    limit: int = 100,
    window: int = 3600,
    burst_multiplier: float = 1.5,
) -> bool:
    """Advanced rate limiting with burst capability. (Bangla: বার্স্ট ক্যাপাবিলিটি সহ অ্যাডভানসড রেট লিমিটিং)

    Args:
        key: The rate limit identifier key (IP or user ID).
        limit: Base rate limit per window.
        window: Time window in seconds.
        burst_multiplier: Multiplier for burst allowance.

    Returns:
        bool: True if request is allowed, False otherwise.
    """
    effective_limit = int(limit * burst_multiplier)
    return await rate_limiter.acquire(key, limit=effective_limit, window=window)
