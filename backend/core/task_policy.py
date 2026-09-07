from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskPolicyDecision:
    allowed: bool
    risk: str
    message: str


MANUAL_ONLY_TERMS = ("payment", "pay", "password", "security setting", "delete account", "wire transfer")


def evaluate_goal(goal: str) -> TaskPolicyDecision:
    normalized = goal.casefold()
    if any(term in normalized for term in MANUAL_ONLY_TERMS):
        return TaskPolicyDecision(False, "manual", "SupremeAI does not have permission to perform payments, password changes, security changes, or account deletion. Please complete that step manually.")
    if any(term in normalized for term in ("post", "publish", "send", "submit", "upload", "book")):
        return TaskPolicyDecision(True, "approval", "This action needs your approval immediately before it is submitted.")
    return TaskPolicyDecision(True, "low", "SupremeAI can start with a safe read-only step and will pause before anything sensitive.")
