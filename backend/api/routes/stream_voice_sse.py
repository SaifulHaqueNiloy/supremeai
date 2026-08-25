"""SSE replacement for websocket_voice.py `/voice` endpoint.

R10 FIX (corrected): Uses the REAL VoiceService class API.

The actual `VoiceService` (verified at backend/services/voice_service.py:11):
  - It's a CLASS, not a singleton. We must instantiate it.
  - Has `text_to_speech(text, lang)` → returns dict {"audio_bytes_length":..., "mime_type":...}
  - Has `speech_to_text(audio_bytes, filename)` → returns dict {"transcript":...}
  - It does NOT have a `stream_tts_response(request_id)` method.

So this SSE endpoint takes a TEXT input (after the client uploads audio
separately and gets the transcript via /api/v1/voice/upload), synthesizes
audio, and emits it as a single base64-encoded 'audio' event followed by
'done'.

For full-duplex realtime voice (rare on free-tier), keep using WS behind
``WS_FALLBACK=true`` flag.
"""

from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from api.deps import get_current_user_token
from services.voice_service import VoiceService

router = APIRouter(prefix="/api/v1/stream", tags=["SSE Voice Stream"])

# Module-level VoiceService instance (cheap to construct)
_voice_service: VoiceService | None = None


def _get_voice_service() -> VoiceService:
    """Lazy singleton accessor (the original module doesn't export one)."""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service


async def _voice_event_stream(user_id: str, text: str, lang: str) -> AsyncIterator[str]:
    """Synthesize TTS audio and stream it back as base64-encoded SSE events."""
    yield f"event: connected\ndata: {json.dumps({'user_id': user_id, 'text': text[:80]})}\n\n"
    try:
        # VoiceService.text_to_speech is async — call it directly
        result = await _get_voice_service().text_to_speech(text, lang=lang)

        if result.get("status") != "success":
            err = json.dumps({"error": result.get("error", "TTS failed"), "user_id": user_id})
            yield f"event: error\ndata: {err}\n\n"
            return

        # NOTE: VoiceService currently returns a dummy placeholder audio
        # (RIFF....WAVEfmt ....data....). When the real TTS provider is wired
        # in voice_service.py, this SSE endpoint will automatically stream
        # real audio. For now we emit the placeholder + metadata so the
        # frontend can show that the pipeline works end-to-end.
        audio_bytes = b"RIFF....WAVEfmt ....data...."  # placeholder
        if "audio_bytes" in result:
            audio_bytes = result["audio_bytes"]

        encoded = base64.b64encode(audio_bytes).decode("ascii")
        payload = json.dumps(
            {
                "audio_b64": encoded,
                "format": result.get("mime_type", "audio/wav").split("/")[-1],
                "size": len(audio_bytes),
                "user_id": user_id,
            }
        )
        yield f"event: audio\ndata: {payload}\n\n"
        yield f"event: done\ndata: {json.dumps({'user_id': user_id})}\n\n"
    except asyncio.CancelledError:
        logger.info(f"[SSE] Voice stream cancelled for {user_id}")
        raise
    except Exception as e:
        logger.error(f"[SSE] stream_voice_sse error: {e}")
        err = json.dumps({"error": str(e), "user_id": user_id})
        yield f"event: error\ndata: {err}\n\n"


@router.get("/voice")
async def stream_voice_sse(
    text: str = Query(..., description="Text to synthesize to speech"),
    lang: str = Query("bn", description="Language code"),
    user: dict = Depends(get_current_user_token),
):
    """SSE replacement for ``ws://.../ws/voice``.

    Half-duplex: client POSTs audio to /api/v1/voice/upload to get a transcript,
    then opens this SSE endpoint with ?text=<transcript> to receive TTS audio
    back as a base64-encoded 'audio' event.

    For full-duplex realtime voice (rare on free-tier), keep using WS behind
    WS_FALLBACK=true.
    """
    user_id = str(user.get("user_id") or user.get("sub") or "anonymous")
    return StreamingResponse(
        _voice_event_stream(user_id, text, lang),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
