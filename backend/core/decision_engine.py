"""Decision Engine Module for SupremeAI 2.0
Provides intelligent decision-making for autonomous operations based on risk assessment.

বাংলা: SupremeAI ২.০-এর জন্য স্মার্ট ডিসিশন এঞ্জিন — রিস্ক অ্যাসেসমেন্টের উপর ভিত্তি করে স্বায়ত্তশাসিত枸成。
"""

import os
from typing import Any

from loguru import logger


class DecisionEngine:
    """Intelligent decision engine for routing and approving autonomous operations.

    বাংলা: স্বায়ত্তশাসিত অপারেশনগুলো রাউট এবং অ্যাপ্রুভ করার জন্য বুদ্ধিমান ডিসিশন ইঞ্জিন।
    """

    def __init__(self) -> None:
        """Initialize the decision engine with configuration from environment.

        বাংলা: এনভায়রনমেন্ট থেকে কনফিগারেশন লোড করে ডিসিশন ইঞ্জিন ইনিশিয়ালাইজ করে।
        """
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self._min_confidence = float(os.getenv("DECISION_MIN_CONFIDENCE", "0.6"))

    async def decide(self, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze request context and return a routing decision.

        Args:
            context: Dictionary containing:
                - risk_flags (list): List of risk flags detected
                - recent_error_rate (float): Recent error rate (0.0 to 1.0)
                - sandbox_passed (bool|None): Whether sandbox validation passed

        Returns:
            Dictionary with decision result containing:
                - action (str): One of "proceed", "review", "block"
                - confidence (float): Confidence score (0.0 to 1.0)
                - reason (str|None): Reason for the decision
                - trace (Any): Optional trace information

        Raises:
            None. All decisions are returned as dictionaries without exceptions.

        বাংলা: রিকোয়েস্ট কনটেক্সট অ্যানালাইজ করে একটি রাউটিং ডিসিশন রিটার্ন করে।

        Decision Matrix:
            - sandbox_failed → "block" (confidence: 1.0)
            - risk_flags present → "review" (confidence: 0.5)
            - confidence < min_confidence → "review"
            - otherwise → "proceed"
        """
        risk_flags = context.get("risk_flags") or []
        error_rate = context.get("recent_error_rate", 0.0)
        sandbox_passed = context.get("sandbox_passed")

        if sandbox_passed is False:
            logger.warning("DecisionEngine: sandbox failed, blocking action")
            return {
                "action": "block",
                "confidence": 1.0,
                "reason": "sandbox_failed",
                "trace": None,
            }

        if risk_flags:
            logger.info(f"DecisionEngine: risk flags present {risk_flags}, routing to review")
            return {
                "action": "review",
                "confidence": 0.5,
                "reason": "risk_flags",
                "trace": None,
            }

        confidence = max(0.0, 1.0 - error_rate)
        action = "proceed" if confidence >= self._min_confidence else "review"
        logger.debug(f"DecisionEngine: action={action} confidence={confidence:.2f}")
        return {
            "action": action,
            "confidence": confidence,
            "reason": None,
            "trace": None,
        }
