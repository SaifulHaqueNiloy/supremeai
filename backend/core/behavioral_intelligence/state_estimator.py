"""Conservative, rule-based behavioral signal estimator.

This is intentionally not a psychological profiler. It emits bounded hypotheses
from the current turn and optional local context only.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .schema import BehavioralSignals, SignalLevel, bounded_signals

_FRUSTRATION = re.compile(r"\b(again|broken|failed|frustrated|stuck|জানি না|বিরক্ত)\b", re.I)
_URGENT = re.compile(r"\b(urgent|asap|immediately|production|outage|জরুরি)\b", re.I)
_QUESTION = re.compile(r"\?|what|how|কী|কিভাবে", re.I)


def estimate_signals(message: str, context: Mapping[str, Any] | None = None) -> BehavioralSignals:
    """Estimate short-lived interaction signals without storing the message."""
    text = str(message or "")[:4000]
    lower = text.lower()
    frustration = (
        min(1.0, 0.35 + 0.2 * len(_FRUSTRATION.findall(lower)))
        if _FRUSTRATION.search(lower)
        else 0.0
    )
    urgency = 0.75 if _URGENT.search(lower) else 0.15
    ambiguity = 0.65 if len(text.split()) < 4 or (" or " in lower and "?" not in text) else 0.1
    risk = (
        SignalLevel.HIGH
        if any(word in lower for word in ("delete", "payment", "credential", "medical", "legal"))
        else SignalLevel.UNKNOWN
    )
    goal = (
        "debugging"
        if any(word in lower for word in ("bug", "error", "broken", "failed"))
        else "information"
    )
    evidence = tuple(
        filter(
            None,
            (
                "frustration_signal" if frustration else "",
                "urgency_signal" if urgency > 0.5 else "",
                "short_or_ambiguous" if ambiguity > 0.5 else "",
            ),
        )
    )
    return bounded_signals(
        BehavioralSignals(
            likely_goal=goal,
            intent_clarity=SignalLevel.LOW if ambiguity > 0.5 else SignalLevel.MEDIUM,
            frustration=frustration,
            urgency=urgency,
            preferred_density="concise" if urgency > 0.5 else "balanced",
            interaction_mode="clarification" if ambiguity > 0.5 else "direct_answer",
            risk=risk,
            needs_clarification=ambiguity,
            confidence=0.55 if context else 0.45,
            evidence=evidence,
        )
    )


__all__ = ["estimate_signals"]
