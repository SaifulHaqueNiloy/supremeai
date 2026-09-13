# backend/core/llm/llm_gateway/registry.py
"""Provider registry for the LLM Gateway package.

Task 4-a package split: code moved VERBATIM from core/llm/llm_gateway.py —
provider → settings-attribute mapping, the multi-key rotation pool and the
longest-prefix key resolver. `_provider_key_pool` is THE single shared
instance (kept in exactly this one module and re-exported by the package).
"""

import asyncio
import time

# বাংলা মন্তব্ব: Provider → settings attribute mapping।
# এই dict update করলেই নতুন provider add হয় — no code duplication।
_MODEL_KEY_MAP: dict[str, str] = {
    "groq": "groq_api_key",
    "gemini": "gemini_api_key",
    "gpt": "openai_api_key",
    "openai": "openai_api_key",
    "deepseek": "deepseek_api_key",
    "openrouter": "openrouter_api_key",
    "hf": "hf_api_key",
    "huggingface": "hf_api_key",
    "nvidia": "nvidia_api_key",
    "moonshot": "MOONSHOT_API_KEY",
    "together": "TOGETHER_API_KEY",
    "ollama": "OLLAMA_API_KEY",
    "hf_space": "HF_API_KEY",
}


class _ProviderKeyPool:
    """SECURITY/RELIABILITY FIX (P0, review 2026-09-12): multi-key rotation.

    Deployment .env keeps GEMINI_API_KEY/GROQ_API_KEY/OPENROUTER_API_KEY as
    comma-joined multi-key strings ("k1,k2,k3"). The old code sent the entire
    raw string as one API key, so every provider call failed with 401/403 and
    the whole zero-cost fallback chain was dead. This pool:
      1. splits on commas into individual keys,
      2. rotates round-robin (spreads quota evenly),
      3. puts a key on cooldown after 401/403/429 so the next call picks a
         healthy key instead of hammering the broken one.
    """

    _COOLDOWNS = {401: 300.0, 403: 300.0, 429: 60.0}

    def __init__(self) -> None:
        self._idx: dict[str, int] = {}
        self._cooldown_until: dict[tuple[str, str], float] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _keys_for(raw: str | None) -> list[str]:
        if not raw:
            return []
        return [k.strip() for k in str(raw).split(",") if k.strip()]

    async def next_key(self, provider: str, raw: str | None) -> str | None:
        keys = self._keys_for(raw)
        if not keys:
            return None
        if len(keys) == 1:
            key = keys[0]
        else:
            async with self._lock:
                idx = self._idx.get(provider, 0) % len(keys)
                self._idx[provider] = idx + 1
                key = keys[idx]
        # best-effort: skip a cooling key if a healthy sibling exists
        if await self.is_cooling(provider, key):
            for alt in keys:
                if alt != key and not await self.is_cooling(provider, alt):
                    return alt
        return key

    async def is_cooling(self, provider: str, key: str) -> bool:
        until = self._cooldown_until.get((provider, key), 0.0)
        if until and time.monotonic() < until:
            return True
        if until:
            self._cooldown_until.pop((provider, key), None)
        return False

    async def mark_error(self, provider: str, key: str | None, status: int) -> None:
        if not key:
            return
        ttl = self._COOLDOWNS.get(status)
        if ttl:
            self._cooldown_until[(provider, key)] = time.monotonic() + ttl


_provider_key_pool = _ProviderKeyPool()


def _resolve_key_attr(model: str) -> str | None:
    """FIX (P1, review 2026-09-12): longest-prefix provider matching.

    The old substring loop matched "openrouter/deepseek/..." against the
    "deepseek" prefix (and "openrouter/openai/gpt-*" against "gpt"), sending
    the WRONG provider's key. Longest matching prefix wins now, so
    "openrouter/..." always resolves to the openrouter key.
    """
    if not model:
        return None
    model_lower = model.lower()
    best_prefix = ""
    best_attr: str | None = None
    for prefix, attr_name in _MODEL_KEY_MAP.items():
        if prefix in model_lower and len(prefix) > len(best_prefix):
            best_prefix = prefix
            best_attr = attr_name
    return best_attr
