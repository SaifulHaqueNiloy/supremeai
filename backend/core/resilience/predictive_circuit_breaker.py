import time

from core.logging_config import logger
from core.resilience.circuit_breaker import CircuitBreakerState
from core.resilience.predictive_metrics import PredictiveMetricsTracker


class PredictiveCircuitBreaker:
    """
    প্রোঅ্যাক্টিভ ও প্রেডিক্টিভ সার্কিট ব্রেকার।
    সিস্টেম সম্পূর্ণ ক্র্যাশ করার আগেই অ্যানমেলি ধরা পড়লে স্বয়ংক্রিয়ভাবে ফলব্যাক রাউটে শিফট করে।
    """

    def __init__(
        self, name: str, fallback_provider: str | None = "openrouter", cooldown_seconds: int = 60
    ):
        self.name = name
        self.fallback_provider = fallback_provider
        self.cooldown_seconds = cooldown_seconds
        self.tracker = PredictiveMetricsTracker()
        # Issue #684 (H-05): state now uses the canonical CircuitBreakerState
        # enum (values CLOSED/OPEN/HALF_OPEN) instead of raw literals that
        # historically included the divergent "HALF-OPEN" spelling.
        self.state = CircuitBreakerState.CLOSED
        self.last_state_change = time.time()
        self.primary_provider = "gemini"

    def record_request_outcome(self, latency_ms: float, status_code: int) -> None:
        """
        রিকোয়েস্টের মেট্রিক রেকর্ড করা এবং প্রয়োজন হলে স্টেট পরিবর্তন করা।
        """
        self.tracker.record_request(latency_ms, status_code)

        # অ্যানমেলি চেক করা
        if self.state == CircuitBreakerState.CLOSED and self.tracker.is_anomaly_detected():
            logger.warning(
                f"[PredictiveCircuitBreaker] Anomaly detected on '{self.name}'. "
                f"Proactively shifting route from '{self.primary_provider}' to '{self.fallback_provider}'."
            )
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = time.time()

    def get_active_provider(self) -> str:
        """
        বর্তমানে সক্রিয় এআই প্রোভাইডারের নাম প্রদান করা।
        """
        current_time = time.time()

        # Cooldown সময় শেষ হলে অটোমেটিক HALF-OPEN স্টেটে চেক করা
        if (
            self.state == CircuitBreakerState.OPEN
            and (current_time - self.last_state_change) > self.cooldown_seconds
        ):
            logger.info(
                f"[PredictiveCircuitBreaker] Cooldown expired for '{self.name}'. Switching to HALF-OPEN to test primary provider."
            )
            self.state = CircuitBreakerState.HALF_OPEN
            return self.primary_provider

        if self.state == CircuitBreakerState.OPEN:
            return self.fallback_provider or "groq"

        return self.primary_provider

    def mark_recovery_success(self) -> None:
        """
        HALF-OPEN অবস্থায় প্রাইমারি সার্ভিস সফল হলে পুনরায় CLOSED স্টেটে প্রমোট করা।
        """
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info(
                f"[PredictiveCircuitBreaker] Primary provider recovered for '{self.name}'. State restored to CLOSED."
            )
            self.state = CircuitBreakerState.CLOSED
            self.last_state_change = time.time()
