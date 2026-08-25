"""SSE replacement for websocket_agent.py `/chat` endpoint.

R10 FIX: WebSocket → Server-Sent Events migration.

Why SSE > WS on Render free-tier:
  - One-way server→client push (sufficient for chat tokens, HITL, voice frames)
  - HTTP/2 multiplexing — no separate connection limit
  - Auto-reconnect via EventSource browser API
  - No idle-timeout disconnect (we send `: ping` every 15s)

Endpoint: GET /api/v1/stream/chat
Auth: ?token=<JWT> (query param — EventSource cannot set headers)
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from core.security import verify_token

router = APIRouter(prefix="/api/v1/stream", tags=["SSE Chat Stream"])

HEARTBEAT_SECONDS = 15


async def _event_stream(prompt: str, user_id: str, task_type: str = "chat") -> AsyncIterator[str]:
    """Generator yielding SSE-formatted events."""
    yield f"event: connected\ndata: {json.dumps({'user_id': user_id})}\n\n"

    last_heartbeat = asyncio.get_event_loop().time()

    try:
        # Lazy import to avoid circular dependency at module load
        from core.llm.llm_gateway import llm_gateway

        async for chunk in llm_gateway._stream_completion_iter(
            messages_payload=[{"role": "user", "content": prompt}],
            call_chain=["gemini/gemini-2.0-flash"],
            timeout=60.0,
        ):
            if not chunk:
                continue
            payload = json.dumps({"delta": chunk, "user_id": user_id})
            yield f"event: token\ndata: {payload}\n\n"

            now = asyncio.get_event_loop().time()
            if now - last_heartbeat > HEARTBEAT_SECONDS:
                yield ": ping\n\n"
                last_heartbeat = now

        yield f"event: done\ndata: {json.dumps({'user_id': user_id})}\n\n"
    except asyncio.CancelledError:
        logger.info(f"[SSE] Client disconnected for user {user_id}")
        raise
    except Exception as e:
        logger.error(f"[SSE] stream_chat_sse error: {e}")
        err = json.dumps({"error": str(e), "user_id": user_id})
        yield f"event: error\ndata: {err}\n\n"


@router.get("/chat")
async def stream_chat_sse(
    prompt: str = Query(..., description="User prompt to stream"),
    token: str = Query(..., description="JWT token (EventSource cannot set headers)"),
    task_type: str = Query("chat"),
):
    """SSE stream that replaces ``ws://.../ws/chat``.

    Frontend usage::

        const es = new EventSource('/api/v1/stream/chat?prompt=...&token=...');
        es.addEventListener('token', (e) => { appendText(JSON.parse(e.data).delta); });
        es.addEventListener('done',  () => es.close());
        es.addEventListener('error', (e) => { console.error(e); es.close(); });

    Rollback: keep WS route active by setting ``WS_FALLBACK=true`` (default).
    Once SSE is verified end-to-end, set ``WS_FALLBACK=false`` and remove
    ``websocket_agent`` from ``api/routers.py``.
    """
    payload = verify_token(token)
    user_id = payload.get("sub") or payload.get("user_id") or "anonymous"

    return StreamingResponse(
        _event_stream(prompt, user_id, task_type),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
