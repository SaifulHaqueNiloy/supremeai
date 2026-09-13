"""AI response engine for :class:`TelegramBotHandler`
(verbatim split artifact of the former single-module telegram_bot.py).

Direct Gemini → Groq → SupremeOrchestrator fallback chain.
"""

from __future__ import annotations

import asyncio
import os

import httpx

from core.config import settings
from core.logging_config import logger


class AIEngineMixin:
    """AI-response mixin for :class:`TelegramBotHandler`."""

    async def _ai_response(self, text: str, user_id: str) -> str:
        """Route user query through SupremeAI reasoning engine and persist chat memory."""
        # 1. Primary: Gemini 2.5 Flash (Ultra-fast & Intelligent)
        gem_keys = [
            k.strip()
            for k in os.getenv("GEMINI_API_KEY", "").split(",")
            if k.strip().startswith("AIza")
        ]
        system_instruction = (
            "You are SupremeAI 2.0, a living self-evolving autonomous intelligence. "
            "Respond helpfully, clearly, and concisely in Bengali or English according to the user's language."
        )

        for gem_key in gem_keys:
            try:
                async with httpx.AsyncClient(timeout=25) as client:
                    configured_model = getattr(settings, "model_vision", "gemini/gemini-2.0-flash")
                    model_name = configured_model.split("/", 1)[-1]
                    gem_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gem_key}"
                    payload = {
                        "contents": [{"parts": [{"text": text}]}],
                        "systemInstruction": {"parts": [{"text": system_instruction}]},
                    }
                    r = await client.post(gem_url, json=payload)
                    if r.status_code == 200:
                        data = r.json()
                        candidates = data.get("candidates", [])
                        if candidates and "parts" in candidates[0].get("content", {}):
                            return candidates[0]["content"]["parts"][0]["text"]
            except Exception as direct_exc:
                logger.warning(f"Gemini key attempt notice: {direct_exc}")

        # 2. Fallback: Groq (Ultra-low latency GPT-OSS / Qwen)
        groq_keys = [k.strip() for k in os.getenv("GROQ_API_KEY", "").split(",") if k.strip()]
        for groq_key in groq_keys:
            for model_name in ["openai/gpt-oss-120b", "qwen/qwen3.6-27b", "openai/gpt-oss-20b"]:
                try:
                    async with httpx.AsyncClient(timeout=20) as client:
                        r = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {groq_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model_name,
                                "messages": [
                                    {"role": "system", "content": system_instruction},
                                    {"role": "user", "content": text},
                                ],
                            },
                        )
                        if r.status_code == 200:
                            return r.json()["choices"][0]["message"]["content"]
                except Exception as groq_exc:
                    logger.debug(f"Groq {model_name} attempt notice: {groq_exc}")

        # 3. Fallback: Orchestrator / ModelRouter
        if self.processor:
            try:
                task_type = (
                    "coding"
                    if any(k in text.lower() for k in ["code", "function", "script", "fix", "bug"])
                    else "general"
                )
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: self.processor.execute_task(text, task_type)
                )
                if isinstance(result, dict) and result.get("result"):
                    return str(result["result"])
            except Exception as exc:
                logger.error(f"Orchestrator fallback error: {exc}")

        return "🤖 SupremeAI 2.0: আপনার বার্তাটি গ্রহণ করা হয়েছে। আমি সিস্টেম মেমোরি ও মডেল রুট করছি।"

