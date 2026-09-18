# SupremeAI 2.0 - Multimodal Voice Service Engine
# বাংলা মন্তব্য: এটি স্পিচ-টু-টেক্সট (Whisper STT) এবং টেক্সট-টু-স্পিচ (Bengali TTS) ভয়েস ইন্টারেকশন প্রসেস করে।

from __future__ import annotations

import os
import time
from typing import Any

from core.logging_config import logger

# Issue #445 doctrine (real work or loud failure, never fabricated success):
# the old implementation returned a FIXED Bengali transcript with confidence
# 0.96 for ANY audio and synthesized fake RIFF WAV bytes for ANY text. This
# service now performs REAL provider calls when configured — Groq Whisper
# (whisper-large-v3) for STT and edge-tts (free, no key) or ElevenLabs for
# TTS — and otherwise returns an explicit, honest "unavailable" status.
_stt_unavailable_announced = False
_tts_unavailable_announced = False

# Extension -> (mime, Groq-accepted format token)
_AUDIO_MIMES: dict[str, str] = {
    ".wav": "audio/wav",
    ".webm": "audio/webm",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
}

# edge-tts neural voices (Bengali Bangladesh first, per the service's bn default)
_EDGE_TTS_VOICES: dict[str, str] = {
    "bn": "bn-BD-NabanitaNeural",
    "bn-BD": "bn-BD-NabanitaNeural",
    "bn-IN": "bn-IN-TanishaaNeural",
    "en": "en-US-AriaNeural",
    "hi": "hi-IN-SwaraNeural",
}


def _get_settings():
    from core.config import settings

    return settings


def _sniff_audio_mime(filename: str) -> str:
    lower = (filename or "").lower()
    for ext, mime in _AUDIO_MIMES.items():
        if lower.endswith(ext):
            return mime
    return "audio/wav"


class VoiceService:
    """
    Multimodal Voice Interaction Service Engine.
    Handles Speech-to-Text (STT) transcription and Text-to-Speech (TTS) audio synthesis.
    """

    def __init__(self, tts_provider: str = "auto"):
        self.tts_provider = tts_provider

    async def speech_to_text(
        self, audio_bytes: bytes, filename: str = "input.wav"
    ) -> dict[str, Any]:
        """
        Transcribe raw audio bytes to text via Groq Whisper (real provider call).

        বাংলা: আসল Whisper কল (Groq) — কী না থাকলে সৎ "unavailable"; কোনো
        বানানো ট্রান্সক্রিপ্ট নয় (issue #445)।
        """
        global _stt_unavailable_announced
        try:
            if not audio_bytes:
                return {
                    "status": "error",
                    "transcript": "",
                    "error": "EMPTY_AUDIO",
                    "message": "No audio bytes were provided for transcription.",
                }

            groq_key = os.getenv("GROQ_API_KEY") or getattr(_get_settings(), "groq_api_key", "")
            if not groq_key:
                if not _stt_unavailable_announced:
                    _stt_unavailable_announced = True
                    logger.warning(
                        "Speech-to-text UNAVAILABLE: GROQ_API_KEY missing — returning "
                        "honest 'unavailable' status instead of a placeholder transcript "
                        "(issue #445)."
                    )
                return {
                    "status": "unavailable",
                    "reason": "STT_NOT_CONFIGURED",
                    "transcript": "",
                    "message": (
                        "No speech-to-text provider is configured on this deployment "
                        "(GROQ_API_KEY missing), so the audio was NOT transcribed."
                    ),
                }

            return await self._transcribe_with_groq(audio_bytes, filename, groq_key)
        except Exception as e:
            logger.error(f"STT Transcription failed: {e}")
            return {"status": "error", "transcript": "", "error": str(e)}

    async def _transcribe_with_groq(
        self, audio_bytes: bytes, filename: str, api_key: str
    ) -> dict[str, Any]:
        """Real Groq Whisper API call (same provider/contract as websocket_voice)."""
        import httpx

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        mime = _sniff_audio_mime(filename)

        files = {"file": (filename or "input.wav", audio_bytes, mime)}
        data = {"model": "whisper-large-v3", "response_format": "json"}

        started = time.monotonic()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, files=files, data=data)
        latency_ms = int((time.monotonic() - started) * 1000)

        if response.status_code != 200:
            logger.error("Groq STT failed: HTTP %s: %s", response.status_code, response.text[:200])
            return {
                "status": "error",
                "transcript": "",
                "error": "STT_PROVIDER_ERROR",
                "provider_status": response.status_code,
                "message": response.text[:300],
            }

        transcript = (response.json() or {}).get("text", "")
        if not transcript:
            return {
                "status": "error",
                "transcript": "",
                "error": "EMPTY_TRANSCRIPT",
                "message": "STT provider returned an empty transcript.",
            }

        logger.info(
            "STT transcription completed (%d bytes audio, %dms)", len(audio_bytes), latency_ms
        )
        return {
            "status": "success",
            "transcript": transcript,
            "language": None,  # provider-determined; not fabricated
            "model": "whisper-large-v3",
            "latency_ms": latency_ms,
        }

    async def text_to_speech(self, text: str, lang: str = "bn") -> dict[str, Any]:
        """
        Synthesize text into audio bytes (TTS response).

        বাংলা: edge-tts ইনস্টল থাকলে আসল নিউরাল TTS (ফ্রি, কী-লেস); ElevenLabs
        কী থাকলে সেটাও ব্যবহারযোগ্য। কোনোটাই না থাকলে সৎ "unavailable" — কখনো
        ফাঁকা RIFF বাইট নয় (issue #445)।
        """
        global _tts_unavailable_announced
        try:
            if not text or not text.strip():
                return {
                    "status": "error",
                    "error": "EMPTY_TEXT",
                    "message": "No text was provided for synthesis.",
                }

            eleven_key = os.getenv("ELEVENLABS_API_KEY") or getattr(
                _get_settings(), "elevenlabs_api_key", ""
            )
            if eleven_key and self.tts_provider in ("auto", "elevenlabs"):
                result = await self._tts_with_elevenlabs(text, lang, eleven_key)
                if result.get("status") == "success":
                    return result
                logger.warning(
                    "ElevenLabs TTS failed (%s) — falling back to edge-tts if available",
                    result.get("error"),
                )

            result = await self._tts_with_edge(text, lang)
            if result.get("status") == "success":
                return result

            if not _tts_unavailable_announced:
                _tts_unavailable_announced = True
                logger.warning(
                    "Text-to-speech UNAVAILABLE: no TTS provider reachable (edge-tts "
                    "not installed and ELEVENLABS_API_KEY missing) — returning honest "
                    "'unavailable' status instead of placeholder audio bytes (issue #445)."
                )
            return {
                "status": "unavailable",
                "reason": "TTS_NOT_CONFIGURED",
                "message": (
                    "No text-to-speech provider is available on this deployment "
                    "(edge-tts not installed and ELEVENLABS_API_KEY missing), so NO "
                    "audio was synthesized."
                ),
                "detail": result.get("error"),
            }
        except Exception as e:
            logger.error(f"TTS Synthesis failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _tts_with_edge(self, text: str, lang: str) -> dict[str, Any]:
        """Real neural TTS via edge-tts (free Microsoft Edge voices, no API key)."""
        try:
            import edge_tts  # type: ignore[import-untyped]
        except ImportError:
            return {"status": "unavailable", "error": "edge_tts not installed"}

        voice = _EDGE_TTS_VOICES.get(lang) or _EDGE_TTS_VOICES.get(str(lang).split("-")[0])
        if not voice:
            voice = "en-US-AriaNeural"

        communicate = edge_tts.Communicate(text, voice)
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                chunks.append(chunk.get("data", b""))
        audio = b"".join(chunks)
        if not audio:
            return {"status": "error", "error": "edge-tts returned no audio"}

        logger.info("TTS synthesis completed via edge-tts (%s, %d bytes)", voice, len(audio))
        return {
            "status": "success",
            "audio_bytes": audio,
            "audio_bytes_length": len(audio),
            "mime_type": "audio/mpeg",
            "voice": voice,
        }

    async def _tts_with_elevenlabs(self, text: str, lang: str, api_key: str) -> dict[str, Any]:
        """Real TTS via ElevenLabs (requires ELEVENLABS_API_KEY)."""
        import httpx

        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        payload = {"text": text, "model_id": "eleven_multilingual_v2"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return {
                "status": "error",
                "error": f"ELEVENLABS_HTTP_{response.status_code}",
                "message": response.text[:200],
            }
        audio = response.content
        logger.info("TTS synthesis completed via ElevenLabs (%d bytes)", len(audio))
        return {
            "status": "success",
            "audio_bytes": audio,
            "audio_bytes_length": len(audio),
            "mime_type": "audio/mpeg",
            "voice": voice_id,
        }
