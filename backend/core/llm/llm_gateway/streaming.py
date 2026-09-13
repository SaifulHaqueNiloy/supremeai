# backend/core/llm/llm_gateway/streaming.py
"""Streaming completion with fallback chain.

Task 4-a package split: code moved VERBATIM from core/llm/llm_gateway.py into
the StreamingMixin used by LLMGateway (core/llm/llm_gateway/gateway.py).
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from core.logging_config import logger

from .registry import _resolve_litellm_target


class StreamingMixin:
    """Streaming fallback method for LLMGateway (verbatim move)."""

    async def _stream_completion(
        self,
        messages: list[dict[str, Any]],
        call_chain: list[str],
        timeout: float,
    ) -> AsyncGenerator[str, None]:
        """বাংলা মন্তব্ব: Streaming completion — fallback chain সহ।"""
        self._ensure_litellm_ready()
        import asyncio

        import litellm  # lazy import

        last_exception: Exception | None = None
        for current_model in call_chain:
            # FINAL-TEST FIX (2026-09-13): skip retired models + route
            # OpenAI-compatible routers (BYNARA/BAI) via their base URL.
            try:
                _litellm_model, _api_base = _resolve_litellm_target(current_model)
            except ValueError as retired_err:
                logger.warning(f"[LLMGateway] Streaming skip {current_model}: {retired_err}")
                continue
            # Circuit Breaker check
            cb = self._get_or_create_circuit_breaker(current_model)
            if not cb.allow_request():
                logger.warning(
                    f"[LLMGateway] Circuit breaker OPEN for {current_model}. Skipping..."
                )
                continue

            try:
                logger.info(f"[LLMGateway] Streaming attempt: {current_model}")
                # api_key per-call — os.environ injection নিষিদ্ধ
                api_key = await self._get_api_key_for_model(current_model)
                response_stream = await litellm.acompletion(
                    model=_litellm_model,
                    messages=messages,
                    timeout=timeout,
                    stream=True,
                    api_key=api_key,
                    api_base=_api_base,
                )
                async for chunk in response_stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                cb.mark_success()
                return
            except asyncio.CancelledError:
                # বাংলা মন্তব্ব: CancelledError re-raise — কখনো suppress করা যাবে না
                logger.warning(f"[LLMGateway] Stream cancelled at model {current_model}")
                raise
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    # Handle rate limit in streaming case too
                    handled = await self._handle_rate_limit_error(current_model, exc)
                    if handled:
                        logger.info(
                            f"[LLMGateway] Retrying streaming {current_model} after rate limit backoff..."
                        )
                        try:
                            api_key = await self._get_api_key_for_model(current_model)
                            response_stream = await litellm.acompletion(
                                model=_litellm_model,
                                messages=messages,
                                timeout=timeout,
                                stream=True,
                                api_key=api_key,
                                api_base=_api_base,
                            )
                            async for chunk in response_stream:
                                content = chunk.choices[0].delta.content
                                if content:
                                    yield content
                            cb.mark_success()
                            return
                        except Exception as retry_exc:
                            logger.warning(
                                f"[LLMGateway] Retry failed for streaming {current_model}: {retry_exc}"
                            )
                last_exception = exc
                cb.mark_failure()
                logger.opt(exception=True).warning(
                    f"[LLMGateway] Stream model {current_model} failed."
                )
                continue
            except Exception as exc:
                last_exception = exc
                cb.mark_failure()
                logger.opt(exception=True).warning(
                    f"[LLMGateway] Stream model {current_model} failed."
                )
                continue

        raise last_exception or RuntimeError("All streaming fallback options failed.")
