"""Governed behavioral intelligence primitives.

The package produces bounded, ephemeral signals and response strategies. It does
not diagnose users, create durable psychological profiles, or authorize actions.
"""
from .policy import BehavioralPolicyDecision, review_behavioral_request, sanitize_learning_metadata
from .schema import BehavioralSignals, PreferenceRecord, ResponseStrategy, SignalLevel, StrategyDecision
from .state_estimator import estimate_signals
from .strategy_router import choose_strategy

__all__ = [
    "BehavioralPolicyDecision", "BehavioralSignals", "PreferenceRecord",
    "ResponseStrategy", "SignalLevel", "StrategyDecision", "choose_strategy",
    "estimate_signals", "review_behavioral_request", "sanitize_learning_metadata",
]
