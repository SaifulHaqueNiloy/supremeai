"""LLMRouter - Thin wrapper for compatibility with LLMGateway."""

# বাংলা মন্তব্য: এলএলএম-রাউটার — গেটওয়ের সাথে কম্প্যাটিবিলিটি বজায় রাখার জন্য তৈরি করা থিন র‍্যাপার ক্লাস।

from __future__ import annotations

from typing import Any
from core.llm.llm_gateway import get_llm_gateway


class LLMRouter:
    """Wrapper around LLMGateway to expose 'route' method."""

    def __init__(self) -> None:
        self.gateway = get_llm_gateway()

    async def route(
        self,
        prompt: str,
        task_type: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Route generation request to LLMGateway and format output."""
        res = await self.gateway.acompletion(prompt=prompt, task_type=task_type, max_tokens=max_tokens, temperature=temperature, **kwargs)
        if isinstance(res, dict):
            res["content"] = res.get("text", "")
        return res
