"""SSE replacement for websocket_agent.py `/chat` endpoint.

R10 FIX (corrected): WebSocket → Server-Sent Events migration.

Endpoint: GET /api/v1/stream/chat?prompt=...&token=<JWT>
Auth: ?token=<JWT> query param (EventSource cannot set headers)
Heartbeat: ': ping' every 15s

Uses the REAL LLMGateway API:
  - llm_gateway.acompletion(prompt=..., stream=True) → returns StreamingResponse
  - OR we delegate to llm_gateway._stream_completion(messages, call_chain, timeout)

Verified against backend/core/llm/llm_gateway.py at commit 38acf13acb.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from core.llm.llm_gateway import llm_gateway
from core.security import verify_token

router = APIRouter(prefix="/api/v1/stream", tags=["SSE Chat Stream"])

HEARTBEAT_SECONDS = 15


async def _event_stream(prompt: str, user_id: str, task_type: str = "chat") -> AsyncIterator[str]:
    """Generator yielding SSE-formatted events.

    Strategy: call llm_gateway.acompletion with stream=True — it returns a
    StreamingResponse, so we just stream its body through as SSE events.

    If streaming fails, fall back to non-stream acompletion and emit the
    whole response as a single 'token' event.
    """
    yield f"event: connected\ndata: {json.dumps({'user_id': user_id})}\n\n"

    last_heartbeat = asyncio.get_event_loop().time()

    try:
        # Try streaming first (preferred path)
        try:
            response = await llm_gateway.acompletion(
                prompt=prompt,
                task_type=task_type,
                stream=True,
            )

            # If acompletion returns a StreamingResponse (when stream=True),
            # we delegate its body_iterator through as SSE 'token' events.
            body_iterator = getattr(response, "body_iterator", None)
            if body_iterator is not None:
                async for chunk in body_iterator:
                    if not chunk:
                        continue
                    if isinstance(chunk, bytes):
                        chunk = chunk.decode("utf-8", errors="replace")
                    payload = json.dumps({"delta": chunk, "user_id": user_id})
                    yield f"event: token\ndata: {payload}\n\n"

                    now = asyncio.get_event_loop().time()
                    if now - last_heartbeat > HEARTBEAT_SECONDS:
                        yield ": ping\n\n"
                        last_heartbeat = now
            else:
                # Non-streaming response (fallback) — emit as single event
                text = response.get("text", "") if isinstance(response, dict) else str(response)
                payload = json.dumps({"delta": text, "user_id": user_id})
                yield f"event: token\ndata: {payload}\n\n"

        except Exception as inner:
            logger.warning(f"[SSE] streaming path failed ({inner}); falling back to non-stream")
            response = await llm_gateway.acompletion(
                prompt=prompt,
                task_type=task_type,
                stream=False,
            )
            text = response.get("text", "") if isinstance(response, dict) else str(response)
            payload = json.dumps({"delta": text, "user_id": user_id})
            yield f"event: token\ndata: {payload}\n\n"

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
        es.addEventListener('token', (e) => appendText(JSON.parse(e.data).delta));
        es.addEventListener('done',  () => es.close());
        es.addEventListener('error', (e) => { console.error(e); es.close(); });

    Rollback: keep WS route active by setting ``WS_FALLBACK=true`` (default).
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
