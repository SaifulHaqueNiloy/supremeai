import asyncio
import json
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger


class RedisTaskQueue:
    """
    G6: Redis-backed distributed task queue for long LLM operations.
    Replaces local asyncio.Tasks for better scaling and load balancing.
    """

    def __init__(self, queue_name: str = "supreme_task_queue"):
        self.queue_name = queue_name
        self.redis = None
        self._handlers: dict[str, Callable[[dict], Awaitable[Any]]] = {}

    async def _get_redis(self):
        if not self.redis:
            import redis.asyncio as aioredis

            try:
                from core.config import settings

                redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379")
            except ImportError:
                redis_url = "redis://localhost:6379"
            self.redis = aioredis.from_url(redis_url, decode_responses=True)
        return self.redis

    async def enqueue(self, task_type: str, payload: dict, user_id: str) -> str:
        redis = await self._get_redis()
        task_id = str(uuid.uuid4())
        task_data = {
            "task_id": task_id,
            "task_type": task_type,
            "user_id": user_id,
            "payload": payload,
            "status": "pending",
        }
        await redis.rpush(self.queue_name, json.dumps(task_data))
        # Store metadata for polling status
        await redis.set(f"task:{task_id}", json.dumps(task_data), ex=86400)
        logger.info(f"Queued task {task_id} of type {task_type} for user {user_id}")
        return task_id

    def register_handler(self, task_type: str, handler: Callable[[dict], Awaitable[Any]]):
        self._handlers[task_type] = handler

    async def worker_loop(self):
        redis = await self._get_redis()
        logger.info(f"Task queue worker listening on {self.queue_name}...")
        while True:
            try:
                result = await redis.blpop(self.queue_name, timeout=5)
                if result:
                    _, task_json = result
                    task_data = json.loads(task_json)
                    # Run in background to avoid blocking other pop requests
                    asyncio.create_task(self._process_task(task_data))
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)

    async def _process_task(self, task_data: dict):
        task_id = task_data["task_id"]
        task_type = task_data["task_type"]
        redis = await self._get_redis()

        handler = self._handlers.get(task_type)
        if not handler:
            logger.error(f"No handler for task type {task_type}")
            task_data["status"] = "failed"
            task_data["error"] = "No handler"
            await redis.set(f"task:{task_id}", json.dumps(task_data), ex=86400)
            return

        try:
            task_data["status"] = "processing"
            await redis.set(f"task:{task_id}", json.dumps(task_data), ex=86400)

            result = await handler(task_data)

            task_data["status"] = "completed"
            task_data["result"] = result
            await redis.set(f"task:{task_id}", json.dumps(task_data), ex=86400)

            # Broadcast completion via pubsub
            try:
                from api.routes.websocket_agent import manager

                if hasattr(manager, "broadcast_to_user"):
                    await manager.broadcast_to_user(
                        task_data.get("user_id", "unknown"),
                        json.dumps(
                            {"type": "task_completed", "task_id": task_id, "result": result}
                        ),
                    )
            except ImportError:
                pass

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            task_data["status"] = "failed"
            task_data["error"] = str(e)
            await redis.set(f"task:{task_id}", json.dumps(task_data), ex=86400)


task_queue = RedisTaskQueue()
