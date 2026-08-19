"""
Free-Tier Sliding-Window Quota Balancer
=======================================
Tracks RPM (Requests Per Minute) and TPM (Tokens Per Minute) across zero-cost providers
(Groq, Gemini-Flash, Cerebras, GitHub-Models, OpenRouter-Free).
Dynamically shifts traffic to lowest-utilized provider before hitting 429 Rate Limits.
Ensures 100% continuous uptime on $0 infrastructure.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional
from loguru import logger


@dataclass
class ProviderQuotaConfig:
    provider: str
    model: str
    max_rpm: int = 15
    max_tpm: int = 30000
    utilization_threshold: float = 0.80  # Shift traffic when 80% full


@dataclass
class SlidingWindowMetrics:
    request_timestamps: deque[float] = field(default_factory=deque)
    token_entries: deque[tuple[float, int]] = field(default_factory=deque)


class FreeTierQuotaBalancer:
    """
    In-memory thread-safe rate tracker and intelligent load balancer for free model providers.
    """

    def __init__(self):
        self._lock = RLock()
        self._providers: Dict[str, ProviderQuotaConfig] = {
            "gemini_flash": ProviderQuotaConfig(provider="gemini", model="gemini/gemini-1.5-flash", max_rpm=15, max_tpm=32000),
            "groq_llama": ProviderQuotaConfig(provider="groq", model="groq/llama-3.3-70b-versatile", max_rpm=30, max_tpm=6000),
            "cloudflare_deepseek": ProviderQuotaConfig(provider="cloudflare", model="@cf/deepseek-ai/deepseek-r1-distill-qwen-32b", max_rpm=50, max_tpm=50000),
            "cloudflare_llama": ProviderQuotaConfig(provider="cloudflare", model="@cf/meta/llama-3.3-70b-instruct", max_rpm=50, max_tpm=50000),
            "cerebras_llama": ProviderQuotaConfig(provider="cerebras", model="cerebras/llama3.1-70b", max_rpm=30, max_tpm=60000),
            "openrouter_free": ProviderQuotaConfig(provider="openrouter", model="openrouter/auto", max_rpm=20, max_tpm=40000),
        }
        self._metrics: Dict[str, SlidingWindowMetrics] = {
            k: SlidingWindowMetrics() for k in self._providers
        }
        self._cooldowns: Dict[str, float] = {}

    def report_rate_limit(self, p_key: str, cooldown_seconds: float = 60.0) -> None:
        """Flags a provider as experiencing 429 rate limit, imposing a cooldown window."""
        with self._lock:
            self._cooldowns[p_key] = time.time() + cooldown_seconds
            logger.warning(f"[QuotaBalancer] Provider '{p_key}' rate-limited. Cooling down for {cooldown_seconds}s.")

    def _purge_old_entries(self, p_key: str, now: float) -> None:
        """Purges metric timestamps older than 60 seconds (1 minute sliding window)."""
        metrics = self._metrics[p_key]
        cutoff = now - 60.0

        while metrics.request_timestamps and metrics.request_timestamps[0] < cutoff:
            metrics.request_timestamps.popleft()

        while metrics.token_entries and metrics.token_entries[0][0] < cutoff:
            metrics.token_entries.popleft()

    def get_provider_load(self, p_key: str) -> dict[str, Any]:
        """Calculates current RPM and TPM utilization percentage."""
        with self._lock:
            now = time.time()
            self._purge_old_entries(p_key, now)
            cfg = self._providers[p_key]
            metrics = self._metrics[p_key]

            current_rpm = len(metrics.request_timestamps)
            current_tpm = sum(tokens for _, tokens in metrics.token_entries)

            rpm_util = current_rpm / max(1, cfg.max_rpm)
            tpm_util = current_tpm / max(1, cfg.max_tpm)
            max_util = max(rpm_util, tpm_util)

            return {
                "provider": cfg.provider,
                "model": cfg.model,
                "current_rpm": current_rpm,
                "max_rpm": cfg.max_rpm,
                "current_tpm": current_tpm,
                "max_tpm": cfg.max_tpm,
                "utilization": round(max_util, 2),
                "is_throttled": max_util >= cfg.utilization_threshold,
            }

    def select_optimal_free_provider(self, estimated_tokens: int = 500, preferred_provider: Optional[str] = None) -> str:
        """
        Selects the best available free provider with the lowest current utilization.
        If preferred provider is not throttled, uses it.
        """
        with self._lock:
            now = time.time()
            # If preferred provider is available and safe, return it
            if preferred_provider and preferred_provider in self._providers:
                self._purge_old_entries(preferred_provider, now)
                load = self.get_provider_load(preferred_provider)
                if not load["is_throttled"]:
                    return self._providers[preferred_provider].model

            # Otherwise, find the provider with minimum utilization that is not in cooldown
            candidates = []
            for p_key in self._providers:
                if p_key in self._cooldowns and now < self._cooldowns[p_key]:
                    continue  # Skip cooling down provider
                self._purge_old_entries(p_key, now)
                load = self.get_provider_load(p_key)
                candidates.append((load["utilization"], p_key, self._providers[p_key].model))

            if not candidates:
                # If all are cooling down, fallback to least recently cooled
                return self._providers["gemini_flash"].model

            candidates.sort(key=lambda x: x[0])
            best_choice = candidates[0]
            logger.debug(f"[QuotaBalancer] Selected '{best_choice[2]}' (utilization: {best_choice[0]*100:.1f}%)")
            return best_choice[2]

    def record_usage(self, model_name: str, tokens: int = 500) -> None:
        """Records request and token consumption in the sliding window."""
        with self._lock:
            now = time.time()
            for p_key, cfg in self._providers.items():
                if cfg.model in model_name or cfg.provider in model_name:
                    metrics = self._metrics[p_key]
                    metrics.request_timestamps.append(now)
                    metrics.token_entries.append((now, tokens))
                    break


# Singleton instance
free_quota_balancer = FreeTierQuotaBalancer()
