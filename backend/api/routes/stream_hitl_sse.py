"""SSE replacement for websocket_hitl.py `/` endpoint.

Streams Human-In-The-Loop approval events to the admin Command Center.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from loguru import logger

from api.deps import get_current_user_token

router = APIRouter(prefix="/api/v1/stream", tags=["SSE HITL Stream"])

HEARTBEAT_SECONDS = 15


async def _hitl_event_stream(user_id: str) -> AsyncIterator[str]:
    """Listen to the in-process HITL event bus and forward as SSE events."""
    from core.queue.task_queue import task_queue

    queue: asyncio.Queue = asyncio.Queue()

    async def _enqueue() -> None:
        async for event in task_queue.subscribe_hitl_events(user_id):
            await queue.put(event)

    task = asyncio.create_task(_enqueue())
    try:
        yield f"event: connected\ndata: {json.dumps({'user_id': user_id})}\n\n"
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                payload = json.dumps(event, default=str)
                yield f"event: hitl\ndata: {payload}\n\n"
            except asyncio.TimeoutError:
                yield ": ping\n\n"
    except asyncio.CancelledError:
        logger.info(f"[SSE] HITL stream cancelled for {user_id}")
        task.cancel()
        raise
    finally:
        task.cancel()


@router.get("/hitl")
async def stream_hitl_sse(user: dict = Depends(get_current_user_token)):
    """SSE replacement for ``ws://.../ws/`` (HITL approval events)."""
    user_id = str(user.get("user_id") or user.get("sub") or "admin")
    return StreamingResponse(
        _hitl_event_stream(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
