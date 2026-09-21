from unittest.mock import AsyncMock, patch

import pytest


def test_setup_logging_runs():
    from core.logging_config import setup_logging

    # Should not raise
    setup_logging()


def test_config_validators_basic():
    from core.config import Settings

    s = Settings(env="test")
    # Default CORS origins are localhost dev URLs (127.0.0.1 is not in the
    # default set; the cors_origins property is env-driven, not a field).
    assert "localhost" in " ".join(s.cors_origins)  # is_local()
    # ensure debug remains a bool
    assert isinstance(s.debug, bool)


@pytest.mark.anyio
async def test_llm_gateway_acompletion_monkeypatched(monkeypatch, tmp_path):
    class FakeChoiceMessage:
        def __init__(self, content):
            self.content = content
            self.role = "assistant"  # cloud_adapter reads message.role

    class FakeChoice:
        def __init__(self, msg):
            self.message = FakeChoiceMessage(msg)

    class FakeUsage:
        prompt_tokens = 1
        completion_tokens = 1
        total_tokens = 2

    class FakeResponse:
        def __init__(self, text):
            self.choices = [FakeChoice(text)]
            self.usage = FakeUsage()
            self.model = "test-model"
            self._response_metadata = {"api_cost": 0.001}

    async def fake_acompletion(*args, **kwargs):
        return FakeResponse("mocked-response")

    from core.llm.llm_gateway import LLMGateway

    with (
        patch("litellm.acompletion", new=fake_acompletion),
        patch(
            "core.cache.semantic_cache.SemanticCache.query_similar",
            new=AsyncMock(return_value=None),
        ),
    ):
        gateway = LLMGateway()
        res = await gateway.acompletion(prompt="hi")
        assert res["success"] is True
        assert res["text"] == "mocked-response"
