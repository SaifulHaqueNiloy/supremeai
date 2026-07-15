"""Circuit Breaker — Resilience pattern for preventing cascading failures.

বাংলা: সার্কিট ব্রেকার — ক্যাসকেডিং ফেইলিওর প্রতিরোধের জন্য রেজিলিয়েন্স প্যাটার্ন।

Tracks failure/success counts and opens the circuit when threshold exceeded.
After cooldown, transitions to half-open state for recovery testing.
"""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import Any, TypeVar

from loguru import logger

from core.config import settings

T = TypeVar("T")


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation — requests pass through
    OPEN = "OPEN"  # Failing — requests are rejected immediately
    HALF_OPEN = "HALF_OPEN"  # Testing — limited requests allowed


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is OPEN and a request is rejected.

    বাংলা: সার্কিট ব্রেকার OPEN থাকলে রিকোয়েস্ট রিজেক্ট হলে এই এক্সেপশন রেইজ হয়।
    """

    def __init__(self, name: str, state: CircuitBreakerState) -> None:
        self.name = name
        self.state = state
        super().__init__(f"Circuit breaker '{name}' is {state.value}. Request rejected.")


class CircuitBreaker:
    """Circuit breaker for a specific operation or service.

    বাংলা: নির্দিষ্ট অপারেশন বা সার্ভিসের জন্য সার্কিট ব্রেকার।

    Attributes:
        name: Identifier for this breaker (e.g., service name).
        failure_threshold: Number of consecutive failures to open the circuit.
        recovery_timeout: Seconds to wait before transitioning to HALF_OPEN.
        state: Current circuit state.
        failure_count: Current consecutive failure count.
        success_count: Current consecutive success count (for half-open recovery).
        last_failure_time: Timestamp of the last failure.
        last_success_time: Timestamp of the last success.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int | None = None,
        recovery_timeout: float | None = None,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold or settings.circuit_breaker_failure_threshold
        self.recovery_timeout = float(recovery_timeout or settings.circuit_breaker_cooldown_period)

        self.state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self.failure_count: int = 0
        self.success_count: int = 0
        self.last_failure_time: float | None = None
        self.last_success_time: float | None = None

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name='{self.name}', state={self.state.value}, "
            f"failures={self.failure_count}, successes={self.success_count})"
        )

    @property
    def is_open(self) -> bool:
        """Check if the circuit is currently open.

        বাংলা: সার্কিট বর্তমানে OPEN কিনা চেক করে।
        """
        return self.state == CircuitBreakerState.OPEN

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery.

        বাংলা: রিকভারি চেষ্টা করার জন্য যথেষ্ট সময় পেরিয়েছে কিনা চেক করে।
        """
        if self.last_failure_time is None:
            return True
        return (time.monotonic() - self.last_failure_time) >= self.recovery_timeout

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a function with circuit breaker protection (sync).

        বাংলা: সার্কিট ব্রেকার প্রোটেকশন সহ সিঙ্ক্রোনাস ফাংশন এক্সিকিউট করে।

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN and not ready for recovery.
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_recovery():
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN for recovery test")
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(self.name, self.state)

        try:
            result = func(*args, **kwargs)
            self._mark_success()
            return result
        except (ConnectionError, TimeoutError, OSError) as exc:
            logger.warning(f"Circuit breaker '{self.name}' caught recoverable error: {exc}")
            self._mark_failure()
            raise
        except Exception:  # noqa: BLE001
            logger.opt(exception=True).error(f"Circuit breaker '{self.name}' caught unexpected error")
            self._mark_failure()
            raise

    async def acall(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """Execute an async function with circuit breaker protection.

        বাংলা: সার্কিট ব্রেকার প্রোটেকশন সহ অ্যাসিঙ্ক্রোনাস ফাংশন এক্সিকিউট করে।

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN and not ready for recovery.
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_recovery():
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN for recovery test")
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(self.name, self.state)

        try:
            result = await func(*args, **kwargs)
            self._mark_success()
            return result
        except (ConnectionError, TimeoutError, OSError) as exc:
            logger.warning(f"Circuit breaker '{self.name}' caught recoverable error: {exc}")
            self._mark_failure()
            raise
        except Exception:  # noqa: BLE001
            logger.opt(exception=True).error(f"Circuit breaker '{self.name}' caught unexpected error")
            self._mark_failure()
            raise

    def _mark_success(self) -> None:
        """Record a successful call and potentially close the circuit.

        বাংলা: সফল কল রেকর্ড করে এবং সম্ভবত সার্কিট বন্ধ করে।
        """
        self.success_count += 1
        self.failure_count = 0
        self.last_success_time = time.monotonic()

        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}' recovered — transitioning to CLOSED")
            self.state = CircuitBreakerState.CLOSED

    def _mark_failure(self) -> None:
        """Record a failed call and potentially open the circuit.

        বাংলা: ব্যর্থ কল রেকর্ড করে এবং সম্ভবত সার্কিট খোলে।
        """
        self.failure_count += 1
        self.success_count = 0
        self.last_failure_time = time.monotonic()

        if self.failure_count >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker '{self.name}' opened after {self.failure_count} consecutive failures"
            )
            self.state = CircuitBreakerState.OPEN

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state.

        বাংলা: ম্যানুয়ালি সার্কিট ব্রেকারকে CLOSED স্টেটে রিসেট করে।
        """
        logger.info(f"Circuit breaker '{self.name}' manually reset")
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics for monitoring.

        বাংলা: মনিটরিংয়ের জন্য বর্তমান মেট্রিক্স রিটার্ন করে।
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
        }

    # বাংলা মন্তব্য: LLMGateway-তে ম্যানুয়াল রিকোয়েস্ট চেকিং প্যাটার্ন সচল করার জন্য এই মেথডগুলো যোগ করা হলো।
    def allow_request(self) -> bool:
        """Check if request is allowed through the breaker.

        বাংলা: রিকোয়েস্ট সার্কিট দিয়ে পাস হতে পারবে কিনা চেক করে।
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_recovery():
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN for recovery test")
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        return True

    def mark_success(self) -> None:
        """Record successful request."""
        self._mark_success()

    def mark_failure(self) -> None:
        """Record failed request."""
        self._mark_failure()
