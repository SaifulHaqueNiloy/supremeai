"""Pure strategy selection; it cannot authorize tools or mutate policy."""
from __future__ import annotations

from .policy import review_behavioral_request
from .schema import BehavioralSignals, ResponseStrategy, StrategyDecision


def choose_strategy(signals: BehavioralSignals, *, requested_action: str | None = None) -> StrategyDecision:
    policy = review_behavioral_request(signals=signals, requested_action=requested_action)
    if not policy.allowed:
        return StrategyDecision(ResponseStrategy.SAFETY_BOUNDARY, 1.0, policy.reason, True)
    if signals.risk.value == "high":
        return StrategyDecision(ResponseStrategy.SAFETY_BOUNDARY, signals.confidence, policy.reason, True)
    if signals.needs_clarification >= 0.55:
        return StrategyDecision(ResponseStrategy.TARGETED_CLARIFICATION, signals.confidence, "Intent uncertainty is material.")
    if (signals.frustration or 0) >= 0.55:
        return StrategyDecision(ResponseStrategy.EMPATHIC_DIRECT, signals.confidence, "Acknowledge friction, then provide the next action.")
    if signals.preferred_density == "concise" or (signals.urgency or 0) >= 0.7:
        return StrategyDecision(ResponseStrategy.CONCISE, signals.confidence, "Urgency favors a concise actionable response.")
    return StrategyDecision(ResponseStrategy.DIRECT, max(0.3, signals.confidence), "No stronger strategy signal was detected.")


__all__ = ["choose_strategy"]
