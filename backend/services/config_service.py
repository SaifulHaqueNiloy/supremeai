import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.logging_config import logger
from models.system_config import SystemConfig


class ConfigService:
    """Service to fetch dynamic configurations from the database with Redis caching."""

    CACHE_PREFIX = "sys_config:"
    DEFAULT_TTL = 300  # 5 minutes TTL for config cache

    @classmethod
    async def get_config(cls, db: AsyncSession, key: str, default: any = None) -> any:
        """
        Fetch configuration by key.
        1. Checks Redis cache.
        2. If not in cache, queries DB.
        3. Caches result in Redis.
        4. Returns default if not found.
        """
        cache_key = f"{cls.CACHE_PREFIX}{key}"
        redis = None

        try:
            from core.optimization.optimized_redis_client import get_redis_client

            redis = await get_redis_client()
            if redis:
                cached_val = await redis.execute_with_retry("get", cache_key)
                if cached_val is not None:
                    try:
                        return json.loads(cached_val)
                    except json.JSONDecodeError:
                        return cached_val
        except Exception as e:
            logger.warning(f"Redis cache error when getting config {key}: {e}")

        # Fallback to DB
        if db is None:
            return default

        try:
            # বাংলা মন্তব্য (BUG FIX): db.query(...) SQLAlchemy 1.x sync ORM API —
            # AsyncSession-এ এই attribute নেই ('AsyncSession' object has no attribute
            # 'query'), ফলে প্রতিটা config fetch এই except ব্লকে পড়ে default রিটার্ন
            # করত (config hot-reload silently কাজ করছিল না)। SQLAlchemy 2.0 async
            # style-এ select() + await db.execute() ব্যবহার করা হলো।
            result = await db.execute(
                select(SystemConfig).where(
                    SystemConfig.key == key, SystemConfig.is_active
                )
            )
            config = result.scalars().first()

            if config is not None:
                val = config.value
                # Cache in Redis
                if redis:
                    try:
                        await redis.execute_with_retry(
                            "setex",
                            cache_key,
                            cls.DEFAULT_TTL,
                            json.dumps(val) if not isinstance(val, str) else val,
                        )
                    except Exception as e:
                        logger.warning(f"Failed to cache config {key} in Redis: {e}")
                return val

            return default
        except Exception as e:
            logger.error(f"DB error fetching config {key}: {e}")
            return default

    @classmethod
    def get_config_sync(cls, db: Session, key: str, default: any = None) -> any:
        """Synchronous version for when async is not available, bypasses Redis caching for simplicity."""
        if db is None:
            return default

        try:
            config = (
                db.query(SystemConfig)
                .filter(SystemConfig.key == key, SystemConfig.is_active)
                .first()
            )
            if config is not None:
                return config.value
            return default
        except Exception as e:
            logger.error(f"DB error fetching config sync {key}: {e}")
            return default
