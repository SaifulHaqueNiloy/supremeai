from __future__ import annotations

from typing import Any
from fastapi import Request
from loguru import logger
from core.failure_fingerprint import make_fingerprint
from core.request_context import get_correlation_id


class ReliabilityController:
    """
    বাংলা মন্তব্য: অ্যাপ্লিকেশনের সেলফ-হিলিং এবং এরর রিকভারি স্ট্যাটাস ট্র্যাকার ও কন্ট্রোলার।
    """

    _failures: dict[str, int] = {}
    _health_score = 100.0

    @classmethod
    async def initialize(cls) -> None:
        logger.info("⚡ Reliability Control Plane initialized.")

    @classmethod
    async def register_failure(cls, request: Request | None, exception: Exception) -> Any:
        fingerprint = make_fingerprint(exception)
        corr_id = "unknown"
        if request and hasattr(request.state, "correlation_id"):
            corr_id = request.state.correlation_id
        else:
            corr_id = get_correlation_id() or "unknown"

        cls._failures[fingerprint] = cls._failures.get(fingerprint, 0) + 1
        cls._health_score = max(0.0, cls._health_score - 1.0)

        logger.warning(f"⚠️ Registered failure {fingerprint} under correlation {corr_id}")

        class FailureContext:
            def __init__(self, c_id, f_print):
                self.correlation_id = c_id
                self.fingerprint = f_print

            def to_log_dict(self):
                return {"correlation_id": self.correlation_id, "fingerprint": self.fingerprint}

        return FailureContext(corr_id, fingerprint)

    @classmethod
    def health(cls) -> dict:
        return {"health_score": cls._health_score, "failures_tracked": len(cls._failures)}

    @classmethod
    def middleware_ok(cls) -> bool:
        return True

    @classmethod
    def failure_store_ok(cls) -> bool:
        return True
