import json

from loguru import logger
from sqlalchemy.orm import Session

from models.system_config import SystemConfig


class ConfigService:
    """Service to fetch dynamic configurations from the database with Redis caching."""

    CACHE_PREFIX = "sys_config:"
    DEFAULT_TTL = 300  # 5 minutes TTL for config cache

    @classmethod
    async def get_config(cls, db: Session, key: str, default: any = None) -> any:
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
                cached_val = await redis.get(cache_key)
                if cached_val is not None:
                    try:
                        return json.loads(cached_val)
                    except json.JSONDecodeError:
                        return cached_val
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Redis cache error when getting config {key}: {e}")

        # Fallback to DB
        if db is None:
            return default

        try:
            config = (
                db.query(SystemConfig)
                .filter(SystemConfig.key == key, SystemConfig.is_active)
                .first()
            )

            if config is not None:
                val = config.value
                # Cache in Redis
                if redis:
                    try:
                        await redis.setex(
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
