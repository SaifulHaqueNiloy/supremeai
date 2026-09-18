"""M03 P0/P1 tests — InferenceContext contract + gateway bypass ratchet.

বাংলা: চুক্তি (context.py), স্ট্রাকচার্ড এরর (errors.py) এবং zero-bypass
ratchet (scripts/ci/check_gateway_bypass.py) — তিনটিরই CI-টেনাবল প্রমাণ।
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core.llm.llm_gateway.context import InferenceContext
from core.llm.llm_gateway.errors import (
    GatewayError,
    GatewayExhaustionError,
    GatewayUnavailableError,
    ProviderUnavailableError,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load(name: str, path: Path):
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bypass_gate = _load(
    "check_gateway_bypass", REPO_ROOT / "scripts" / "ci" / "check_gateway_bypass.py"
)


# ---------------------------------------------------------------------------
# InferenceContext চুক্তি (M03 P0 baseline)
# ---------------------------------------------------------------------------


class TestInferenceContext:
    def test_prompt_only_is_valid(self):
        ctx = InferenceContext(prompt="hi", tenant_id="t1")
        assert ctx.validate() == []

    def test_messages_only_is_valid(self):
        ctx = InferenceContext(messages=({"role": "user", "content": "hi"},), tenant_id="t1")
        assert ctx.validate() == []

    def test_both_or_neither_is_contract_violation(self):
        assert InferenceContext().validate()
        both = InferenceContext(prompt="p", messages=({"role": "user", "content": "c"},))
        assert both.validate()

    def test_negative_budget_rejected(self):
        errors = InferenceContext(prompt="p", max_cost_usd=-1).validate()
        assert any("max_cost_usd" in e for e in errors)

    def test_trace_id_auto_generated_and_fields_safe(self):
        ctx = InferenceContext(prompt="secret prompt content", tenant_id="t1")
        assert ctx.trace_id
        fields = ctx.to_log_fields()
        assert fields["prompt_chars"] == len("secret prompt content")
        # বাংলা: লগ-ক্ষেত্রে প্রম্পট কনটেন্ট কখনো যায় না (শুধু দৈর্ঘ্য)।
        assert "secret" not in str(fields)

    def test_created_at_defaults_to_utc_now(self):
        before = datetime.now(UTC)
        ctx = InferenceContext(prompt="p")
        assert before <= ctx.created_at <= datetime.now(UTC)


# ---------------------------------------------------------------------------
# স্ট্রাকচার্ড এরর ডোমেইন (M03 P1)
# ---------------------------------------------------------------------------


class TestStructuredErrors:
    def test_hierarchy(self):
        # বাংলা: দুটি কংক্রিট এররই GatewayError ভিত্তি থেকে — stream.py ভিত্তি ধরলেই সব ধরা পড়ে।
        assert issubclass(GatewayExhaustionError, GatewayUnavailableError)
        assert issubclass(ProviderUnavailableError, GatewayError)

    def test_retry_after_carried(self):
        err = GatewayUnavailableError("down", retry_after_seconds=30)
        assert err.retry_after_seconds == 30


# ---------------------------------------------------------------------------
# Gateway delegation (M03 P1: competitive_kit ভুয়া উত্তর অবসান)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_competitive_kit_call_llm_delegates_to_gateway(monkeypatch):
    """বাংলা: _call_llm এখন প্রকৃত গেটওয়ে থেকে উত্তর আনে — বানানো টেক্সট নয়।"""
    from core.competitive_kit import MultiLLMRouter

    kit = MultiLLMRouter()

    async def fake_acompletion(**kwargs):
        assert kwargs["task_type"] == "competitive_route"
        return {"text": "real gateway answer"}

    import core.llm.llm_gateway as gw_mod

    monkeypatch.setattr(gw_mod.llm_gateway, "acompletion", fake_acompletion)
    text = await kit._call_llm("Groq", "llama-3.1-70b", "hello")
    assert text == "real gateway answer"
    assert "[Response from" not in text


@pytest.mark.asyncio
async def test_competitive_kit_call_llm_raises_structured_error_on_gateway_failure(monkeypatch):
    from core.competitive_kit import MultiLLMRouter
    from core.llm.llm_gateway.errors import GatewayUnavailableError

    kit = MultiLLMRouter()

    async def broken(**kwargs):
        raise RuntimeError("network down")

    import core.llm.llm_gateway as gw_mod

    monkeypatch.setattr(gw_mod.llm_gateway, "acompletion", broken)
    with pytest.raises(GatewayUnavailableError):
        await kit._call_llm("Groq", "llama-3.1-70b", "hello")


# ---------------------------------------------------------------------------
# Zero-Bypass ratchet (M03 P0)
# ---------------------------------------------------------------------------


def test_bypass_ratchet_holds():
    """বাংলা: বর্তমান ট্রি-তে গেটওয়ে-বাইপাস চিহ্ন বেসলাইনের বেশি নয়।"""
    offenders = bypass_gate.scan()
    assert len(offenders) <= bypass_gate.BASELINE, offenders


def test_bypass_ratchet_exit_zero_now():
    assert bypass_gate.main() == 0


def test_bypass_scanner_excludes_gateway_home():
    """বাংলা: গেটওয়ের নিজস্ব ভূমি স্ক্যান-বহির্ভূত — নইলে গেটওয়ে নিজেই offender।"""
    assert "core/llm/llm_gateway/" in bypass_gate.ALLOWED_PREFIXES
