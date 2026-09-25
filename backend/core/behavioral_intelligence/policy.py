"""Deterministic safety and privacy gates for behavioral intelligence."""


from dataclasses import dataclass
from typing import Any

from core.action_policy import ActionMode, get_action_definition

_FORBIDDEN_TERMS = ("diagnose", "psychological disorder", "mental state certainty")


@dataclass(frozen=True)
class BehavioralPolicyDecision:
    allowed: bool
    reason: str
    redactions: tuple[str, ...] = ()


def review_behavioral_request(
    *, signals: Any, requested_action: str | None = None
) -> BehavioralPolicyDecision:
    """Keep inference advisory and ensure consequential actions retain governance."""
    if requested_action:
        action = get_action_definition(requested_action)
        if action.mode in {ActionMode.MANUAL, ActionMode.DISABLED}:
            return BehavioralPolicyDecision(False, action.description)
        if action.mode is ActionMode.APPROVAL:
            return BehavioralPolicyDecision(
                True, "Behavioral signals may inform strategy; approval remains required."
            )
    risk = getattr(signals, "risk", None)
    if getattr(risk, "value", risk) == "high":
        return BehavioralPolicyDecision(
            True,
            "High-risk context requires conservative response and explicit uncertainty.",
            ("mental_state_claims", "sensitive_attributes"),
        )
    return BehavioralPolicyDecision(True, "Behavioral signals are advisory only.")


def sanitize_learning_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Allow only operational labels into learning records; never raw dialogue."""
    if not isinstance(metadata, dict):
        return {}
    allowed = {"task_type", "strategy", "risk", "evaluation", "dataset_version", "consent_basis"}
    result: dict[str, Any] = {}
    for key, value in metadata.items():
        key_text = str(key).lower()
        if key_text not in allowed or any(
            term in key_text for term in ("prompt", "response", "content", "text")
        ):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            result[key_text] = str(value)[:120] if isinstance(value, str) else value
    return result


__all__ = ["BehavioralPolicyDecision", "review_behavioral_request", "sanitize_learning_metadata"]
