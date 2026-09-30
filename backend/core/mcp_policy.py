"""MCP Policy Engine — schema-driven (SSoT: config/mcp_policy_schema.json).

বাংলা মন্তব্য (#2429 — Unify TS Tower & Python Policy Engine):
আগে এই মডিউলটি infrastructure/mcp-control-plane/src/policy/risk.engine.ts
এর হাতে-লেখা Python mirror ছিল — দুই দিকে আলাদাভাবে maintain করতে হতো,
ফলে drift তৈরি হয়েছিল (Python-এ ৪টি নতুন provider যোগ হলে TS টাওয়ারে
যেত না)। এখন উভয় ইঞ্জিনই একই canonical schema থেকে **generated** snapshot
পড়ে (`mcp_policy_schema_generated.py` — scripts/ci/generate_mcp_policy.py
তৈরি করে)। Drift এখন structurally অসম্ভব: এক জায়গায় বদলালে generator
চালালেই দুই দিকে প্রতিফলিত হয়, আর check_mcp_policy_parity.py gate
mismatch ধরে ফেলে।

Risk Levels (R0-R6):
  R0 = Safe Read-Only     → Auto-allow
  R1 = Safe Write         → Auto-allow
  R2 = Low Risk Write     → Require Approval
  R3 = Moderate Risk      → Require Approval
  R4 = High Risk          → Require Approval
  R5 = Critical           → Require Approval
  R6 = Catastrophic      → Require Approval (strict HITL)

Constitution Compliance:
  - Law #11 (Think Before You Act): every tool call evaluated before execution
  - Law #19 (Observable): every evaluation logged to audit
  - Law #1 (Centralized): single policy engine for ALL Python MCP servers
  - Law #4 (SSoT): policy একবারই define — schema-তে
"""

from __future__ import annotations

from typing import Any, Literal

from core.mcp_policy_schema_generated import (
    DECISION_MATRIX,
    DEFAULT_RISK,
    PROVIDER_RULES,
    READ_ONLY_KEYWORDS,
    READ_ONLY_PROVIDERS,
    SCHEMA_HASH,
    SCHEMA_VERSION,
    TOOL_PROVIDER_ACTION,
    UNKNOWN_TOOL_MAPPING,
)

RiskLevel = Literal["R0", "R1", "R2", "R3", "R4", "R5", "R6"]
PolicyDecision = Literal["ALLOW", "REQUIRE_APPROVAL", "DENY"]

# বাংলা মন্তব্য: TS-সংস্করণ নন-ডিফল্ট PROVIDER_RULES-কে fallback-এ ফেলত (R3),
# কিন্তু Python আগে unknown action-এ provider-specific default ব্যবহার করত
# (memory/mcp_tools/mesh → R0)। Schema-র "_default" কী সেই semantics বহন করে —
# দুই দিক এখন একই আচরণ করবে।
_VALID_RISK_LEVELS = frozenset(DECISION_MATRIX.keys())


def _risk(provider: str, action: str) -> RiskLevel:
    """Canonical schema থেকে (provider, action) → risk level।"""
    # ১. Read-only shortcut: system/health provider বা read-only keyword action।
    if provider in READ_ONLY_PROVIDERS or any(kw in action for kw in READ_ONLY_KEYWORDS):
        return "R0"

    # ২. Provider-specific টেবিল (schema-generated)।
    rules = PROVIDER_RULES.get(provider)
    if rules is not None:
        action_risk = rules.get("actions", {}).get(action)
        if action_risk is not None:
            return action_risk  # type: ignore[return-value]
        # ৩. Provider-specific default (যেমন memory → R0) — না থাকলে গ্লোবাল default।
        provider_default = rules.get("default")
        if provider_default is not None:
            return provider_default  # type: ignore[return-value]

    # ৪. গ্লোবাল default (unknown provider-ও এখানে পড়ে)।
    return DEFAULT_RISK  # type: ignore[return-value]


class RiskEngine:
    """Schema-driven risk evaluation (SSoT: mcp_policy_schema_generated)।"""

    def evaluate(self, provider: str, action: str) -> RiskLevel:
        return _risk(provider, action)


class PolicyEngine:
    """Schema-driven decision matrix (SSoT: mcp_policy_schema_generated)।"""

    def __init__(self) -> None:
        self.risk_engine = RiskEngine()

    def decide(self, risk_level: RiskLevel) -> PolicyDecision:
        # বাংলা মন্তব্য: decision matrix schema-তে declarative — R0/R1 → ALLOW,
        # বাকি সব → REQUIRE_APPROVAL। Unknown risk fail-closed (REQUIRE_APPROVAL)।
        decision = DECISION_MATRIX.get(risk_level, "REQUIRE_APPROVAL")
        return decision  # type: ignore[return-value]

    def evaluate(self, provider: str, action: str) -> tuple[PolicyDecision, RiskLevel]:
        risk = self.risk_engine.evaluate(provider, action)
        decision = self.decide(risk)
        return decision, risk


def schema_info() -> dict[str, Any]:
    """বর্তমান embedded schema snapshot-এর পরিচয় (observability, Law #19)।"""
    return {
        "schema_version": SCHEMA_VERSION,
        "schema_hash": SCHEMA_HASH,
        "providers": sorted(PROVIDER_RULES.keys()),
        "tools": len(TOOL_PROVIDER_ACTION),
    }


# ── Tool → (provider, action) mapping (schema-driven) ──────────────────
# প্রতিটি MCP tool (provider, action) জোড়ায় ম্যাপ করা — canonical টেবিল
# এখন schema-তে (tool_provider_action), এখানে শুধু re-export।

TOOL_PROVIDER_ACTION_MAP: dict[str, tuple[str, str]] = dict(TOOL_PROVIDER_ACTION)


# ── Singleton ──────────────────────────────────────────────────────────

_global_policy_engine = PolicyEngine()


def get_policy_engine() -> PolicyEngine:
    """Returns the singleton PolicyEngine instance."""
    return _global_policy_engine


def evaluate_tool(tool_name: str) -> tuple[PolicyDecision, RiskLevel]:
    """Evaluate a tool call and return (decision, risk_level)."""
    provider, action = TOOL_PROVIDER_ACTION_MAP.get(tool_name, UNKNOWN_TOOL_MAPPING)
    engine = get_policy_engine()
    return engine.evaluate(provider, action)


def is_tool_allowed(tool_name: str) -> bool:
    """Quick check: is this tool auto-allowed (R0/R1)?"""
    decision, _ = evaluate_tool(tool_name)
    return decision == "ALLOW"
