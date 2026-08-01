from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

router = APIRouter()

_tts_engine = None


def get_tts_engine():
    # বাংলা মন্তব্য: মেমরি ওভারহেড কমাতে MultilingualTTS অলসভাবে (lazy) লোড করা হচ্ছে।
    global _tts_engine
    if _tts_engine is None:
        from tools.media.multilingual_tts import MultilingualTTS

        _tts_engine = MultilingualTTS()
    return _tts_engine


@router.get("/stream_audio")
async def stream_audio(text: str = "", voice: str | None = None):
    # বাংলা মন্তব্য: text প্যারামিটারটি ঐচ্ছিক করা হলো যাতে টেক্সট না থাকলে ৪২২ এর বদলে ৪০০ রেসপন্স জেনারেট হয়
    """Stream TTS audio bytes in real-time for the given text.
    Uses ElevenLabs for primary synthesis (if API key configured) with fallback to edge-tts.
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    async def audio_stream():
        try:
            # Stream audio bytes from TTS engine (ElevenLabs with edge-tts fallback)
            async for chunk in get_tts_engine().synthesize_stream(
                text=text.strip(),
                voice_id=None,  # Use language-based voice for ElevenLabs; voice param for edge-tts fallback handled internally
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Audio streaming failed: {e}")
            yield b""  # Return empty bytes on error to avoid breaking the stream

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Disposition": "inline",
        },
    )
