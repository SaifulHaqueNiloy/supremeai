# backend/evolution/cost_guard.py
"""Distributed Redis Budget Guard for SupremeAI.

Provides:
- CostGuard: Autonomous Financial Firewall for LLM API usage
- BudgetExceededError: Exception raised when daily budget is exceeded
- Real-time cost tracking with Redis for multi-instance deployments
"""

from __future__ import annotations

import datetime
from typing import Any

import redis.asyncio as redis
from loguru import logger

from core.config import settings
from core.messaging.event_bus import ErrorContext, ErrorEvent, error_event_bus


class BudgetExceededError(Exception):
    """Raised when the daily budget limit is exceeded."""

    pass


class CostGuard:
    """
    Autonomous Financial Firewall.
    Tracks LLM API usage globally using Redis to prevent runaway costs.

    বাংলা মন্তব্য: Render-এর একাধিক ইনস্ট্যান্স চললেও Redis-এর মাধ্যমে গ্লোবালি খরচ ট্র্যাক করে।
    বাজেট ক্রস করলে সিস্টেমকে সেফ-মোডে নিয়ে যায় (Zero-Cost Policy)।
    """

    def __init__(self) -> None:
        self.redis_pool: redis.Redis | None = None
        self.daily_budget_usd: float = 5.00  # Strict daily limit
        # Pricing table (can be moved to DB or config)
        self._rates: dict[str, dict[str, float]] = {
            "gpt-4o": {"prompt": 0.005 / 1000, "completion": 0.015 / 1000},
            "gpt-4-turbo": {"prompt": 0.01 / 1000, "completion": 0.03 / 1000},
            "gpt-3.5-turbo": {"prompt": 0.0005 / 1000, "completion": 0.0015 / 1000},
            "claude-3-5-sonnet": {"prompt": 0.003 / 1000, "completion": 0.015 / 1000},
            "gemini-2.0-flash": {"prompt": 0.000075 / 1000, "completion": 0.0003 / 1000},
            "gemini-2.5-pro": {"prompt": 0.00025 / 1000, "completion": 0.00125 / 1000},
            "llama-3.1-70b": {"prompt": 0.0002 / 1000, "completion": 0.0002 / 1000},
            "default": {"prompt": 0.00001, "completion": 0.00001},
        }

    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        if not self.redis_pool and settings.redis_url:
            try:
                self.redis_pool = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                )
                logger.info("CostGuard: Redis connection pool initialized")
            except Exception as e:
                logger.error(f"CostGuard: Failed to initialize Redis: {e}")
                # Fail open - will not block on Redis issues

    async def check_and_log_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """
        Calculates cost and blocks execution if budget is exceeded.

        Args:
            model: The LLM model name
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion

        Raises:
            BudgetExceededError: If daily budget is exceeded
        """
        if not self.redis_pool:
            return

        # Get rate for model (default to safe rate)
        rate = self._rates.get(model, self._rates["default"])

        cost = (prompt_tokens * rate["prompt"]) + (completion_tokens * rate["completion"])

        try:
            # Increment global daily counter
            today = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
            key = f"supremeai:cost:{today}"

            # Use Redis atomic increment for distributed safety
            current_spend = await self.redis_pool.incrbyfloat(key, cost)

            # Set TTL for 48 hours to auto-cleanup
            await self.redis_pool.expire(key, 172800)

            if current_spend > self.daily_budget_usd:
                error_event_bus.emit(
                    ErrorEvent(
                        module="CostGuard",
                        error_type="BUDGET_EXCEEDED",
                        message=f"Daily budget of ${self.daily_budget_usd} exceeded. Current spend: ${current_spend:.4f}",
                        severity="CRITICAL",
                        context={
                            "spend": current_spend,
                            "budget": self.daily_budget_usd,
                            "model": model,
                            "cost": cost,
                        },
                        structured_context=ErrorContext(
                            module="evolution.cost_guard",
                            env=settings.env,
                        ),
                    )
                )
                raise BudgetExceededError(
                    f"Daily budget of ${self.daily_budget_usd} exceeded. Current spend: ${current_spend:.4f}"
                )

        except BudgetExceededError:
            raise
        except Exception as e:
            # Fail open for Redis issues, but log it
            error_event_bus.emit(
                ErrorEvent(
                    module="CostGuard",
                    error_type="REDIS_ERROR",
                    message=str(e)[:500],
                    severity="WARNING",
                    context={"action": "redis_increment", "model": model},
                    structured_context=ErrorContext(
                        module="evolution.cost_guard",
                        env=settings.env,
                    ),
                )
            )
            logger.warning(f"CostGuard: Redis error (fail-open): {e}")

    async def get_current_spend(self) -> float:
        """Get the current day's spend."""
        if not self.redis_pool:
            return 0.0

        try:
            today = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
            key = f"supremeai:cost:{today}"
            spend = await self.redis_pool.get(key)
            return float(spend) if spend else 0.0
        except Exception:
            return 0.0


# Singleton instance
cost_guard = CostGuard()
