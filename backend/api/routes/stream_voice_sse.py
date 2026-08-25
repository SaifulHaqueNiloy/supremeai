"""SSE replacement for websocket_voice.py `/voice` endpoint.

Voice is half-duplex on SSE: client POSTs audio chunks to /api/v1/voice/upload,
server STTs them, then streams TTS responses back as base64-encoded audio frames
over this SSE endpoint.

For full-duplex realtime voice (rare on free-tier), keep using WS behind
``WS_FALLBACK=true`` flag.
"""

from __future__ import annotations

import asyncio
import base64
import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from api.deps import get_current_user_token
from services.voice_service import voice_service

router = APIRouter(prefix="/api/v1/stream", tags=["SSE Voice Stream"])


async def _voice_event_stream(
    user_id: str, transcript_request_id: str
) -> AsyncIterator[str]:
    """Stream TTS audio chunks (base64-encoded) back to client."""
    yield f"event: connected\ndata: {json.dumps({'user_id': user_id, 'request_id': transcript_request_id})}\n\n"
    try:
        async for audio_chunk in voice_service.stream_tts_response(transcript_request_id):
            if not audio_chunk:
                continue
            encoded = base64.b64encode(audio_chunk).decode("ascii")
            payload = json.dumps({"audio_b64": encoded, "format": "mp3"})
            yield f"event: audio\ndata: {payload}\n\n"
        yield f"event: done\ndata: {json.dumps({'request_id': transcript_request_id})}\n\n"
    except asyncio.CancelledError:
        logger.info(f"[SSE] Voice stream cancelled for {user_id}")
        raise
    except Exception as e:
        logger.error(f"[SSE] stream_voice_sse error: {e}")
        err = json.dumps({"error": str(e), "request_id": transcript_request_id})
        yield f"event: error\ndata: {err}\n\n"


@router.get("/voice")
async def stream_voice_sse(
    request_id: str = Query(..., description="ID returned by /api/v1/voice/upload"),
    user: dict = Depends(get_current_user_token),
):
    """SSE replacement for ``ws://.../ws/voice``. Streams TTS audio back to client."""
    user_id = str(user.get("user_id") or user.get("sub") or "anonymous")
    return StreamingResponse(
        _voice_event_stream(user_id, request_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
