"""Privacy-safe contracts for behavioral intelligence signals.

Signals are short-lived hypotheses used to choose response strategy. They are
not diagnoses, identity claims, or durable user profiles.
"""


from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SignalLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class ResponseStrategy(StrEnum):
    DIRECT = "direct_answer"
    TARGETED_CLARIFICATION = "direct_with_targeted_clarification"
    STEP_BY_STEP = "step_by_step_guidance"
    CONCISE = "concise_actionable"
    EMPATHIC_DIRECT = "acknowledge_then_act"
    SAFETY_BOUNDARY = "safety_boundary"


@dataclass(frozen=True)
class BehavioralSignals:
    """Ephemeral, uncertainty-aware observations for one request."""

    likely_goal: str | None = None
    intent_clarity: SignalLevel = SignalLevel.UNKNOWN
    frustration: float | None = None
    urgency: float | None = None
    domain_familiarity: float | None = None
    preferred_density: str = "balanced"
    interaction_mode: str = "direct_answer"
    risk: SignalLevel = SignalLevel.UNKNOWN
    needs_clarification: float = 0.0
    confidence: float = 0.0
    trajectory: str = "unknown"
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "likely_goal": self.likely_goal,
            "intent_clarity": self.intent_clarity.value,
            "frustration": self.frustration,
            "urgency": self.urgency,
            "domain_familiarity": self.domain_familiarity,
            "preferred_density": self.preferred_density,
            "interaction_mode": self.interaction_mode,
            "risk": self.risk.value,
            "needs_clarification": self.needs_clarification,
            "confidence": self.confidence,
            "trajectory": self.trajectory,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class StrategyDecision:
    strategy: ResponseStrategy
    confidence: float
    reason: str
    requires_policy_review: bool = False


@dataclass(frozen=True)
class PreferenceRecord:
    """De-identified candidate preference record; raw conversation is excluded."""

    record_id: str
    dataset_version: str
    task_type: str
    chosen_strategy: ResponseStrategy
    rejected_strategy: ResponseStrategy
    dimensions: tuple[str, ...]
    consent_basis: str
    approved: bool = False


__all__ = [
    "BehavioralSignals",
    "PreferenceRecord",
    "ResponseStrategy",
    "SignalLevel",
    "StrategyDecision",
]


def clamp_probability(value: float | None) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def bounded_signals(signals: BehavioralSignals) -> BehavioralSignals:
    """Return signals with bounded probabilities and no durable identity fields."""
    return BehavioralSignals(
        likely_goal=signals.likely_goal[:120] if signals.likely_goal else None,
        intent_clarity=signals.intent_clarity,
        frustration=clamp_probability(signals.frustration),
        urgency=clamp_probability(signals.urgency),
        domain_familiarity=clamp_probability(signals.domain_familiarity),
        preferred_density=signals.preferred_density[:32],
        interaction_mode=signals.interaction_mode[:48],
        risk=signals.risk,
        needs_clarification=clamp_probability(signals.needs_clarification) or 0.0,
        confidence=clamp_probability(signals.confidence) or 0.0,
        trajectory=signals.trajectory[:32],
        evidence=tuple(item[:120] for item in signals.evidence[:8]),
    )
