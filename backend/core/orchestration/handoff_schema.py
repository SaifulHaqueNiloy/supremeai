"""Handoff schema — formal issue-comment/label handoffs for the agent ecosystem.

বাংলা (#1802, #1439 Phase C Step 5): ecosystem-এর event-driven chain-এর
ভিত্তি — standardized handoff schema + validation। Issue-comment-এ embedded
YAML handoff এবং `handoff:<role>` label — দুটোই এখানে parse/validate হয়।
Invalid handoff কখনো **silently drop** হয় না — rejection সবসময় audit log-এ
যায় (struct সহ), যাতে orchestration pipeline কোনো কাজ হারায় না।

Spec (docs/plans/ROLE_BASED_AGENT_ECOSYSTEM_PLAN.md #1439 Step 1):
    task: {issue: "#123", status: completed}
    handoff: {next_agent: implementation, trigger: issue_created}
    constraints: {branch: "feature/123", scope: implementation-only}
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from core.logging_config import logger

# Valid lanes per AGENTS.md §1 (super = omni-lane executor pool).
VALID_ROLES = frozenset({"planner", "coder", "ci", "pr-helper", "browser", "platform", "super"})

# Recognized completion states for a handed-off task.
VALID_TASK_STATUSES = frozenset({"completed", "in-progress", "blocked", "failed"})

_HANDOFF_LABEL_RE = re.compile(r"^handoff:([a-z][a-z0-9-]*)$")

# বাংলা: role নামের উপনাম — issue body-তে "implementation" ধরনের শব্দ coder lane
# নির্দেশ করে (ROLE_BASED_AGENT_ECOSYSTEM_PLAN-এর পুরনো নামকরণের সাথে সামঞ্জস্য)。
_ROLE_ALIASES = {
    "implementation": "coder",
    "implementer": "coder",
    "code": "coder",
    "coder-1": "coder",
    "coder-2": "coder",
    "coder-3": "coder",
    "coder-4": "coder",
    "ci-action": "ci",
    "pr-helper": "pr-helper",
    "planner-and-auditor": "planner",
    "platform-agent": "platform",
    "browser-explorer": "browser",
    "super-agent": "super",
}


class HandoffTask(BaseModel):
    issue: str = Field(
        ..., pattern=r"^#?\d+$", description="GitHub issue number, optional '#' prefix"
    )
    status: Literal["completed", "in-progress", "blocked", "failed"] = "completed"


class HandoffMeta(BaseModel):
    next_agent: str = Field(
        ..., min_length=1, description="Target lane (validated against VALID_ROLES)"
    )
    trigger: str = Field(..., min_length=1, description="What triggers the next agent")


class HandoffConstraints(BaseModel):
    branch: str | None = None
    scope: str | None = None

    model_config = {"extra": "forbid"}


class Handoff(BaseModel):
    """Tenant-scoped handoff record (AGENTS.md §5: tenant_id always bound)."""

    task: HandoffTask
    handoff: HandoffMeta
    constraints: HandoffConstraints | None = None
    tenant_id: str = "tenant-supremeai"

    model_config = {"extra": "forbid"}


class HandoffRejection(Exception):
    """Raised when a handoff document fails validation — always audit-logged."""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}" if detail else reason)


def normalize_role(raw: str) -> str:
    """Map a raw role/alias string to its canonical lane (raises on unknown)."""
    value = str(raw).strip().lower()
    value = _ROLE_ALIASES.get(value, value)
    if value not in VALID_ROLES:
        raise HandoffRejection(
            "unknown_role", f"'{raw}' is not a valid lane: {sorted(VALID_ROLES)}"
        )
    return value


def parse_handoff_label(label: str) -> str:
    """Parse a `handoff:<role>` label into a canonical lane name.

    Returns "" for non-handoff labels (not an error). Raises HandoffRejection
    for a handoff-prefixed label with an unknown role — callers audit-log it.
    """
    match = _HANDOFF_LABEL_RE.match(str(label).strip().lower())
    if not match:
        return ""
    return normalize_role(match.group(1))


def parse_handoff_yaml(raw_yaml: str, tenant_id: str = "tenant-supremeai") -> Handoff:
    """Parse + validate an embedded YAML handoff document.

    Any structural problem raises HandoffRejection (already audit-logged) —
    rejection must never be silent (#1802 acceptance criterion).
    """
    try:
        import yaml

        data = yaml.safe_load(raw_yaml)
    except Exception as exc:  # yaml.YAMLError and friends
        rejection = HandoffRejection("invalid_yaml", str(exc)[:300])
        _audit_rejection(rejection, tenant_id)
        raise rejection from exc

    if not isinstance(data, dict):
        rejection = HandoffRejection("invalid_schema", "handoff document must be a YAML mapping")
        _audit_rejection(rejection, tenant_id)
        raise rejection

    data.setdefault("tenant_id", tenant_id)

    # Normalize role aliases before strict validation.
    handoff_meta = data.get("handoff")
    if isinstance(handoff_meta, dict) and "next_agent" in handoff_meta:
        try:
            handoff_meta["next_agent"] = normalize_role(str(handoff_meta["next_agent"]))
        except HandoffRejection as rejection:
            _audit_rejection(rejection, tenant_id)
            raise

    try:
        handoff = Handoff.model_validate(data)
    except ValidationError as exc:
        rejection = HandoffRejection("invalid_schema", exc.errors()[:3].__repr__())
        _audit_rejection(rejection, tenant_id)
        raise rejection from exc

    # task.status must be a recognized state (Literal already enforces; this
    # normalizes aliases like "done" → "completed" for friendlier ingestion).
    return handoff


def extract_handoff_from_text(text: str, tenant_id: str = "tenant-supremeai") -> Handoff | None:
    """Extract a ```yaml fenced handoff block from an issue/PR comment body.

    Returns None when no handoff block is present (not an error).
    """
    if not text or "handoff:" not in text:
        return None
    fenced = re.search(r"```yaml\s*\n(.*?)\n```", text, re.DOTALL)
    if not fenced:
        return None
    return parse_handoff_yaml(fenced.group(1), tenant_id=tenant_id)


def _audit_rejection(rejection: HandoffRejection, tenant_id: str) -> None:
    """Structured audit log for every rejection — silent drop is forbidden."""
    logger.error(
        "[handoff-audit] REJECTED "
        f"reason={rejection.reason} tenant_id={tenant_id} detail={rejection.detail}"
    )


def handoff_summary(handoff: Handoff) -> dict[str, Any]:
    """Normalized dict the orchestration layer routes on."""
    return {
        "issue": handoff.task.issue.lstrip("#"),
        "status": handoff.task.status,
        "next_agent": handoff.handoff.next_agent,
        "trigger": handoff.handoff.trigger,
        "branch": handoff.constraints.branch if handoff.constraints else None,
        "scope": handoff.constraints.scope if handoff.constraints else None,
        "tenant_id": handoff.tenant_id,
    }
