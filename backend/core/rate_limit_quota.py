import time

import redis.asyncio as aioredis
from loguru import logger


class DailyQuotaLimiter:
    """
    Tracks and enforces daily usage quotas per user to prevent abuse
    and control LLM costs over a 24-hour period.
    """

    def __init__(self, redis_url: str | None = None):
        from core.config import settings

        self.redis_url = redis_url or getattr(settings, "redis_url", None)
        self._redis = None
        self.DAILY_LIMITS = {
            "anonymous": 50,
            "authenticated": 500,
            "premium": 5000,
            "admin": 999999,
        }

    async def get_redis(self):
        if not self._redis:
            self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def check_daily_quota(self, user_id: str, tier: str) -> bool:
        """
        Check if the user has exceeded their daily quota.
        Increments the counter and returns True if allowed, False if exceeded.
        """
        limit = self.DAILY_LIMITS.get(tier, self.DAILY_LIMITS["anonymous"])

        try:
            redis = await self.get_redis()

            # Use current date as part of the key
            today = time.strftime("%Y-%m-%d")
            key = f"daily_quota:{user_id}:{today}"

            current = await redis.incr(key)
            if current == 1:
                # First request of the day, set expiration to 24 hours (86400 seconds)
                await redis.expire(key, 86400)

            if current > limit:
                logger.warning(f"User {user_id} exceeded daily quota of {limit} for tier {tier}")
                return False

            return True
        except Exception as e:
            logger.error(f"Quota error for {user_id}: {e}")
            # Fail open if Redis is down so we don't break the app
            return True
