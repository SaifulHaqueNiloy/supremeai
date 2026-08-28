from collections.abc import AsyncGenerator, Sequence
from typing import Any

from loguru import logger

from ..interfaces import ModelProvider


class CloudProviderAdapter(ModelProvider):
    """
    Adapter for cloud execution, wrapping LiteLLM.
    Handles multiple providers (OpenAI, Anthropic, Gemini, Groq, etc.)
    and enforces SupremeAI's telemetry and key rotation policies.
    """

    def __init__(self):
        # We lazy import litellm to avoid cold starts if only running locally
        pass

    def _get_litellm(self):
        try:
            import litellm

            # Enforce SupremeAI telemetry policies - disable LiteLLM's internal telemetry
            litellm.telemetry = False
            litellm.drop_params = True
            return litellm
        except ImportError:
            logger.error("litellm is not installed. CloudProviderAdapter requires litellm.")
            raise

    async def generate(
        self,
        model: str,
        messages: Sequence[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        timeout: float = 60.0,
        api_key: str | None = None,
        api_base: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a complete text completion using LiteLLM."""
        litellm = self._get_litellm()

        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                api_key=api_key,
                api_base=api_base,
                **kwargs,
            )

            # Format to consistent output
            return {
                "choices": [
                    {
                        "message": {
                            "role": response.choices[0].message.role,
                            "content": response.choices[0].message.content,
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "model": response.model,
                "provider": "cloud",  # We could extract the exact provider from litellm if needed
            }
        except Exception as e:
            logger.error(f"[CloudProviderAdapter] Failed to generate completion: {e}")
            raise

    async def stream(
        self,
        model: str,
        messages: Sequence[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        timeout: float = 60.0,
        api_key: str | None = None,
        api_base: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream a text completion using LiteLLM."""
        litellm = self._get_litellm()

        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                api_key=api_key,
                api_base=api_base,
                stream=True,
                **kwargs,
            )

            async for chunk in response:
                yield {
                    "choices": [
                        {
                            "delta": {
                                "role": chunk.choices[0].delta.role
                                if hasattr(chunk.choices[0].delta, "role")
                                else "",
                                "content": chunk.choices[0].delta.content or "",
                            }
                        }
                    ],
                    "model": chunk.model,
                    "provider": "cloud",
                }
        except Exception as e:
            logger.error(f"[CloudProviderAdapter] Failed to stream completion: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Cloud providers are assumed to be handled per-request by LiteLLM exceptions.
        A true health check would ping a specific provider API.
        """
        return True
