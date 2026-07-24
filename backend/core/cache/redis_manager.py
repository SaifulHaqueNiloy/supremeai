"""Manages asynchronous interactions with a Redis cache for the SupremeAI ecosystem."""

import asyncio
import json
import os

from loguru import logger
from redis import asyncio as aioredis



class SecureRedisManager:
    def __init__(self):
        from core.config import settings

        self.url = settings.redis_url or os.getenv("REDIS_URL")
        self._client = None
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def _ensure_connected(self) -> None:
        """Async-safe Redis connection initialization with locking."""
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            if self.url:
                pool = aioredis.ConnectionPool.from_url(
                    self.url,
                    max_connections=20,
                    socket_keepalive=True,
                    socket_connect_timeout=5.0,
                    decode_responses=True,
                )
                self._client = aioredis.Redis(connection_pool=pool)
                logger.info("⚡ Serverless Upstash Redis REST Provider Active with Connection Pool (limit=20).")
            else:
                logger.critical("🔥 CRITICAL: Serverless Redis Endpoint Missing! System entering Fail-Closed state.")
            self._initialized = True

    async def get_client_async(self) -> aioredis.Redis | None:
        """Get Redis client with async-safe initialization."""
        await self._ensure_connected()
        return self._client

    @property
    def client(self) -> aioredis.Redis | None:
        """Sync property accessor — ensures connection initialization.

        Note: Accessing this property before _ensure_connected() has completed
        may return None if connection is in progress. Prefer get_client_async().
        """
        if not self._initialized and self.url and not self._client:
            # Sync fallback initialization for startup context
            try:
                pool = aioredis.ConnectionPool.from_url(
                    self.url,
                    max_connections=20,
                    socket_keepalive=True,
                    socket_connect_timeout=5.0,
                    decode_responses=True,
                )
                self._client = aioredis.Redis(connection_pool=pool)
                self._initialized = True
            except Exception as exc:
                logger.error(f"Failed sync initialization of Redis client: {exc}")
        return self._client

    async def close() -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
            self._initialized = False

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        client = await self.get_client_async()
        if not client:
            return False
        try:
            await client.set(key, value, ex=ex)
            return True
        except Exception as exc:
            logger.error(f"Redis SET error: {exc}")
            return False

    async def get(self, key: str) -> str | None:
        client = await self.get_client_async()
        if not client:
            return None
        try:
            return await client.get(key)
        except Exception as exc:
            logger.error(f"Redis GET error: {exc}")
            return None

    async def delete(self, key: str) -> bool:
        client = await self.get_client_async()
        if not client:
            return False
        try:
            await client.delete(key)
            return True
        except Exception as exc:
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
        except Exception:
            return None


redis_manager = SecureRedisManager()
