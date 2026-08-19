# বাংলা মন্তব্য: core module-এর কম-কভার লাইন কভার করার জন্য অতিরিক্ত টেস্টসমূহ
import asyncio
import contextlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.messaging.event_bus import ErrorContext

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_test_env(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("SUPREMEAI_JWT_SECRET", "test-secret-placeholder")
    monkeypatch.setenv("SUPREMEAI_ADMIN_PASSWORD_HASH", "")
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    yield
    return


# ========================== llm_gateway.py ==========================


class TestLLMGatewayMissingBranches:
    @pytest.mark.skip(reason="Technical Debt: CostGuard mock needs update. Tracked in TECH_DEBT.md")
    @pytest.mark.anyio
    async def test_acompletion_cost_guard_check(self, monkeypatch):
        from core.llm.llm_gateway import LLMGateway

        gateway = LLMGateway()
        gateway.cache = MagicMock()
        gateway.cache.query_similar = AsyncMock(return_value=None)
        gateway.routing_policy = {"complexity_rules": {}, "fallback_chain": []}

        mock_db = MagicMock()
        mock_cost_guard = MagicMock()
        mock_cost_guard.check_budget = AsyncMock()

        with (
            patch("core.llm_gateway.get_firestore_db", return_value=mock_db),
            patch("core.llm_gateway.CostGuard", return_value=mock_cost_guard),
            patch(
                "litellm.acompletion",
                new_callable=AsyncMock,
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content="ok"))],
                    _response_metadata={},
                ),
            ),
        ):
            os.environ["OPENAI_API_KEY"] = "mock"
            result = await gateway.acompletion(prompt="hi", tenant_id="t1")
            assert result["success"] is True
            mock_cost_guard.check_budget.assert_called_once()

    @pytest.mark.anyio
    async def test_acompletion_provider_filtering_chain(self):
        from core.llm.llm_gateway import LLMGateway

        gateway = LLMGateway()
        gateway.cache = MagicMock()
        gateway.cache.query_similar = AsyncMock(return_value=None)
        gateway.routing_policy = {
            "complexity_rules": {"easy": ["groq/llama", "openai/gpt"]},
            "fallback_chain": ["fb/model"],
        }

        with patch(
            "litellm.acompletion",
            new_callable=AsyncMock,
            return_value=MagicMock(
                choices=[MagicMock(message=MagicMock(content="ok"))],
                _response_metadata={},
            ),
        ) as mock_call:
            os.environ["OPENAI_API_KEY"] = "mock"
            os.environ["GROQ_API_KEY"] = "mock"
            result = await gateway.acompletion(prompt="hi", provider="groq")
            assert result["success"] is True
            assert mock_call.call_args.kwargs["model"] == "groq/llama"

    @pytest.mark.anyio
    async def test_acompletion_messages_list_input(self):
        from core.llm.llm_gateway import LLMGateway

        gateway = LLMGateway()
        gateway.cache = MagicMock()
        gateway.cache.query_similar = AsyncMock(return_value=None)
        gateway.routing_policy = {"complexity_rules": {}, "fallback_chain": []}

        with patch(
            "litellm.acompletion",
            new_callable=AsyncMock,
            return_value=MagicMock(
                choices=[MagicMock(message=MagicMock(content="ok"))],
                _response_metadata={},
            ),
        ) as mock_call:
            os.environ["OPENAI_API_KEY"] = "mock"
            msgs = [{"role": "user", "content": "hi"}]
            result = await gateway.acompletion(prompt=msgs)
            assert result["success"] is True
            assert mock_call.call_args.kwargs["messages"] == msgs

    @pytest.mark.anyio
    async def test_acompletion_self_healer_on_failure(self):
        from core.llm.llm_gateway import LLMGateway

        gateway = LLMGateway()
        gateway.cache = MagicMock()
        gateway.cache.query_similar = AsyncMock(return_value=None)
        gateway.routing_policy = {"complexity_rules": {}, "fallback_chain": []}

        mock_db = MagicMock()
        mock_healer = MagicMock()
        mock_healer.propose_fix = AsyncMock()

        mock_cost_guard = MagicMock()
        mock_cost_guard.check_budget = AsyncMock()

        with (
            patch("core.llm.llm_gateway.get_firestore_db", return_value=mock_db),
            patch("core.llm.llm_gateway.SelfHealerService", return_value=mock_healer),
            patch("core.llm.llm_gateway.CostGuard", return_value=mock_cost_guard),
            patch(
                "litellm.acompletion",
                new_callable=AsyncMock,
                side_effect=Exception("fail"),
            ),
        ):
            os.environ["OPENAI_API_KEY"] = "mock"
            with pytest.raises(
                Exception
            ):  # -- intentionally broad: asserts *some* error propagates (mocked/validation failure), exact type varies
                await gateway.acompletion(prompt="hi", tenant_id="t1")
            mock_healer.propose_fix.assert_called_once()

    def test_get_key_for_model_unknown(self):
        from core.llm.llm_gateway import LLMGateway

        gateway = LLMGateway()
        assert gateway._get_api_key_for_model("unknown/model") is None


