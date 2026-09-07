from __future__ import annotations

from dataclasses import dataclass

from core.effective_policy import get_effective_policy


@dataclass(frozen=True)
class TaskPolicyDecision:
    allowed: bool
    risk: str
    message: str


def evaluate_goal(goal: str, user_id: str | None = None) -> TaskPolicyDecision:
    normalized = goal.casefold()
    policy = get_effective_policy(user_id)
    if not policy.features.get("browser_tasks", True):
        return TaskPolicyDecision(False, "disabled", "This task type is currently disabled by your workspace administrator.")
    manual_terms = tuple(str(term).casefold() for term in policy.rules.get("manual_only_terms", []))
    approval_terms = tuple(str(term).casefold() for term in policy.rules.get("approval_terms", []))
    if any(term in normalized for term in manual_terms):
        return TaskPolicyDecision(False, "manual", "SupremeAI does not have permission to perform payments, password changes, security changes, or account deletion. Please complete that step manually.")
    if any(term in normalized for term in approval_terms):
        if not policy.rules.get("allow_submissions", True):
            return TaskPolicyDecision(False, "disabled", "This action is currently disabled by your workspace administrator.")
        return TaskPolicyDecision(True, "approval", "This action needs your approval immediately before it is submitted.")
    return TaskPolicyDecision(True, "low", "SupremeAI can start with a safe read-only step and will pause before anything sensitive.")
