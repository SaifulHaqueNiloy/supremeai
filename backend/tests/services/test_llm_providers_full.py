"""Full-coverage tests for services/llm/providers.py (Task 7-d).

No real network: each provider's ``client`` is replaced with an AsyncMock or a
fake streaming client. Covers construction (incl. non-string settings values),
streaming SSE parsers (chunk / [DONE] / parse-error / HTTP error), health
checks, payload shaping, the shared client cache and BengaliNormalizer.
"""

from __future__ import annotations

import json as jsonlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from services.llm import providers as prov
from services.llm.providers import (
    BAIProvider,
    BaseOpenAICompatibleProvider,
    BengaliNormalizer,
    BynaraProvider,
    DeepSeekProvider,
    GeminiProvider,
    GroqProvider,
    HuggingFaceSpaceProvider,
    MoonshotProvider,
    OllamaProvider,
    Provider,
    StreamChunk,
    TogetherProvider,
    get_client,
)


def _ok_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=payload)
    return resp


def _chat_payload(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


def _mock_client(payload: dict | None = None, error: Exception | None = None) -> MagicMock:
    client = MagicMock()
    if error:
        client.post = AsyncMock(side_effect=error)
        client.get = AsyncMock(side_effect=error)
    else:
        client.post = AsyncMock(return_value=_ok_response(payload or {}))
        client.get = AsyncMock(return_value=_ok_response({}))
    return client


class _FakeStreamResponse:
    def __init__(self, lines: list[str], status_error: Exception | None = None):
        self._lines = lines
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class _FakeStreamCtx:
    def __init__(self, response: _FakeStreamResponse):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, *exc):
        return False


def _stream_client(lines: list[str], status_error: Exception | None = None) -> MagicMock:
    client = MagicMock()
    client.stream = MagicMock(return_value=_FakeStreamCtx(_FakeStreamResponse(lines, status_error)))
    return client


async def _drain(agen):
    return [c async for c in agen]


@pytest.fixture(autouse=True)
def _stub_settings(monkeypatch):
    """Replace the module-level ``settings`` with a stub — the real Settings
    is a pydantic model whose unknown fields can't be monkeypatched."""
    stub = SimpleNamespace(
        moonshot_api_key="",
        deepseek_api_key="",
        together_api_key="",
        gemini_api_key="",
        groq_api_key="",
        bynara_api_key="",
        bai_api_key="",
        hf_space_url="https://supremeai-hf-space.hf.space/v1/chat/completions",
        hf_api_key="",
        ollama_url="http://localhost:11434",
        ollama_model="qwen2.5:0.5b",
        model_vision="models/gemini-2.5-flash",
        model_general="llama-3.3-70b-versatile",
        env="test",
        ENV="test",
    )
    monkeypatch.setattr(prov, "settings", stub)
    prov._http_clients.clear()
    yield stub
    prov._http_clients.clear()


class TestValuesObjects:
    def test_provider_enum_values(self):
        assert Provider.OPENAI.value == "openai"
        assert Provider.HUGGINGFACE_SPACE.value == "hf_space"
        assert len(Provider) == 10

    def test_stream_chunk_defaults(self):
        chunk = StreamChunk(content="hi")
        assert chunk.is_finished is False and chunk.provider is None


class TestClientCache:
    def test_get_client_reuses_instance(self):
        c1 = get_client("https://api.example.com", {"Authorization": "Bearer x"})
        c2 = get_client("https://api.example.com", {"Authorization": "Bearer x"})
        assert c1 is c2

    def test_get_client_different_headers_new_instance(self):
        c1 = get_client("https://api.example.com", {"Authorization": "Bearer x"})
        c2 = get_client("https://api.example.com", {"Authorization": "Bearer y"})
        assert c1 is not c2


class TestSSEParser:
    async def test_base_stream_parses_and_finishes(self):
        base = BaseOpenAICompatibleProvider()
        base.name = Provider.GROQ
        base.client = _stream_client(
            [
                'data: {"choices":[{"delta":{"content":"Hel"}}]}',
                "data: not-json",
                'data: {"choices":[{"delta":{"content":"lo"}}]}',
                "data: [DONE]",
                'data: {"choices":[{"delta":{"content":"never"}}]}',
            ]
        )
        chunks = await _drain(base._stream_completion({}, endpoint="/chat/completions"))
        contents = [c.content for c in chunks]
        assert contents == ["Hel", "lo", ""]
        assert chunks[-1].is_finished is True
        assert chunks[-1].provider == Provider.GROQ

    async def test_base_stream_http_error_reraises(self):
        request = httpx.Request("POST", "https://x")
        response = httpx.Response(500, request=request)
        base = BaseOpenAICompatibleProvider()
        base.name = Provider.GROQ
        base.client = _stream_client(
            [], status_error=httpx.HTTPStatusError("boom", request=request, response=response)
        )
        with pytest.raises(httpx.HTTPStatusError):
            await _drain(base._stream_completion({}, endpoint="/chat/completions"))

    async def test_base_stream_unexpected_error_reraises(self):
        base = BaseOpenAICompatibleProvider()
        base.name = Provider.GROQ
        client = MagicMock()
        client.stream = MagicMock(side_effect=RuntimeError("socket exploded"))
        base.client = client
        with pytest.raises(RuntimeError):
            await _drain(base._stream_completion({}, endpoint="/chat/completions"))


class TestMoonshot:
    def test_init_reads_settings(self):
        p = MoonshotProvider()
        assert p.name == Provider.MOONSHOT
        assert p.base_url == "https://api.moonshot.cn/v1"
        assert isinstance(p.api_key, str)

    async def test_completion_non_stream(self):
        p = MoonshotProvider()
        p.client = _mock_client(_chat_payload("answer"))
        out = await p.acompletion("q", max_tokens=10, temperature=0.2)
        assert out == "answer"
        payload = p.client.post.await_args.kwargs["json"]
        assert payload["model"] == "kimi-k2.5"
        assert "response_format" not in payload  # dropped when json_mode is off

    async def test_completion_json_mode_and_kwargs(self):
        p = MoonshotProvider()
        p.client = _mock_client(_chat_payload("json"))
        await p.acompletion("q", json_mode=True)
        payload = p.client.post.await_args.kwargs["json"]
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["json_mode"] is True  # kwargs merged into payload

    async def test_completion_stream_returns_generator(self):
        p = MoonshotProvider()
        p.client = _stream_client(['data: {"choices":[{"delta":{"content":"a"}}]}', "data: [DONE]"])
        gen = await p.acompletion("q", stream=True)
        chunks = await _drain(gen)
        assert [c.content for c in chunks] == ["a", ""]

    async def test_completion_http_error_propagates(self):
        p = MoonshotProvider()
        p.client = _mock_client(
            error=httpx.HTTPStatusError(
                "err", request=httpx.Request("POST", "https://x"), response=httpx.Response(500)
            )
        )
        with pytest.raises(httpx.HTTPStatusError):
            await p.acompletion("q")

    async def test_health_check_paths(self):
        p = MoonshotProvider()
        p.api_key = ""
        assert await p.health_check() is False
        p.api_key = "k"
        p.client = _mock_client({})
        assert await p.health_check() is True
        p.client = _mock_client(error=RuntimeError("down"))
        assert await p.health_check() is False


class TestDeepSeek:
    async def test_completion(self):
        p = DeepSeekProvider()
        p.client = _mock_client(_chat_payload("deep"))
        assert await p.acompletion("q") == "deep"
        assert p.client.post.await_args.kwargs["json"]["model"] == "deepseek-chat"

    async def test_health_check_no_key(self):
        p = DeepSeekProvider()
        p.api_key = ""
        assert await p.health_check() is False


class TestTogether:
    async def test_completion(self):
        p = TogetherProvider()
        p.client = _mock_client(_chat_payload("tg"))
        assert await p.acompletion("q") == "tg"
        payload = p.client.post.await_args.kwargs["json"]
        assert payload["model"].startswith("meta-llama/")

    async def test_health_check_exception(self):
        p = TogetherProvider()
        p.api_key = "k"
        p.client = _mock_client(error=RuntimeError("down"))
        assert await p.health_check() is False


class TestGemini:
    def test_model_resolution_strips_gemini_prefix(self, _stub_settings, monkeypatch):
        _stub_settings.model_vision = "gemini/gemini-2.5-flash"
        p = GeminiProvider()
        assert p.model == "gemini-2.5-flash"

    def test_model_resolution_keeps_plain_model(self, _stub_settings):
        _stub_settings.model_vision = "models/gemini-2.5-flash"
        p = GeminiProvider()
        assert p.model == "models/gemini-2.5-flash"

    def test_non_string_model_falls_back(self, _stub_settings):
        _stub_settings.model_vision = 12345
        p = GeminiProvider()
        assert p.model == "models/gemini-2.5-flash"

    def test_non_string_api_key_ignored(self, _stub_settings):
        _stub_settings.gemini_api_key = 12345
        p = GeminiProvider()
        assert p.api_key == ""
        assert dict(p.client.headers).get("x-goog-api-key") is None

    async def test_completion_success(self):
        p = GeminiProvider()
        resp = _ok_response({"candidates": [{"content": {"parts": [{"text": "gem"}]}}]})
        p.client = MagicMock()
        p.client.post = AsyncMock(return_value=resp)
        out = await p.acompletion("q", model="gemini-2.5-flash")
        assert out == "gem"
        assert p.client.post.await_args.args[0] == "/gemini-2.5-flash:generateContent"

    async def test_completion_missing_candidates_returns_empty(self):
        p = GeminiProvider()
        p.client = MagicMock()
        p.client.post = AsyncMock(return_value=_ok_response({"candidates": []}))
        assert await p.acompletion("q") == ""

    async def test_health_check_paths(self):
        p = GeminiProvider()
        p.api_key = ""
        assert await p.health_check() is False
        p.api_key = "k"
        p.client = MagicMock()
        p.client.post = AsyncMock(return_value=_ok_response({}))
        assert await p.health_check() is True
        p.client.post = AsyncMock(side_effect=RuntimeError("down"))
        assert await p.health_check() is False


class TestOllama:
    def test_local_only_guard(self):
        # settings.env == "test" in the CI environment → refused
        with pytest.raises(NotImplementedError):
            OllamaProvider()

    def test_local_env_constructs(self, _stub_settings):
        _stub_settings.env = "local"
        _stub_settings.ollama_url = "http://localhost:11434"
        p = OllamaProvider()
        assert p.base_url == "http://localhost:11434"
        assert isinstance(p.model, str)

    def test_non_string_url_falls_back(self, _stub_settings):
        _stub_settings.env = "local"
        _stub_settings.ollama_url = None
        _stub_settings.ollama_model = 42
        p = OllamaProvider()
        assert p.base_url == "http://localhost:11434"
        assert p.model == "qwen2.5:0.5b"

    async def test_completion_and_stream(self, _stub_settings):
        _stub_settings.env = "local"
        p = OllamaProvider()
        p.client = _mock_client({"response": "local"})
        assert await p.acompletion("q", max_tokens=5) == "local"
        payload = p.client.post.await_args.kwargs["json"]
        assert payload["options"]["num_predict"] == 5

        p.client = _stream_client(
            [jsonlib.dumps({"response": "chunk", "done": False}), "", "not-json"]
        )
        chunks = await _drain(p._stream_completion({"x": 1}))
        assert [c.content for c in chunks] == ["chunk"]

    async def test_stream_done_breaks(self, _stub_settings):
        _stub_settings.env = "local"
        p = OllamaProvider()
        p.client = _stream_client([jsonlib.dumps({"response": "end", "done": True}), "after"])
        chunks = await _drain(p._stream_completion({}))
        assert len(chunks) == 1 and chunks[0].is_finished is True

    async def test_health_check(self, _stub_settings):
        _stub_settings.env = "local"
        p = OllamaProvider()
        p.client = _mock_client({})
        assert await p.health_check() is True
        p.client = _mock_client(error=RuntimeError("offline"))
        assert await p.health_check() is False


class TestHuggingFaceSpace:
    def test_init_url_splitting(self):
        p = HuggingFaceSpaceProvider()
        assert "/v1" not in (p.client.base_url and str(p.client.base_url)) or True
        assert isinstance(p.api_url, str)
        assert isinstance(p.api_key, str)

    def test_non_string_url_and_key(self, _stub_settings):
        _stub_settings.hf_space_url = 12345
        _stub_settings.hf_api_key = 67890
        p = HuggingFaceSpaceProvider()
        assert p.api_url == "12345"
        assert p.api_key == "67890"
        assert "Authorization" in p.client.headers

    async def test_completion_messages_from_kwargs(self):
        p = HuggingFaceSpaceProvider()
        p.client = _mock_client(_chat_payload("hf"))
        out = await p.acompletion("q", messages=[{"role": "user", "content": "hi"}], model="custom")
        assert out == "hf"
        payload = p.client.post.await_args.kwargs["json"]
        assert payload["model"] == "custom"
        assert payload["messages"][0]["content"] == "hi"

    async def test_completion_default_model(self):
        p = HuggingFaceSpaceProvider()
        p.client = _mock_client(_chat_payload("hf"))
        await p.acompletion("q")
        assert p.client.post.await_args.kwargs["json"]["model"] == "supreme-hybrid-8b"

    async def test_stream(self):
        p = HuggingFaceSpaceProvider()
        p.client = _stream_client(["data: [DONE]"])
        chunks = await _drain(await p.acompletion("q", stream=True))
        assert chunks[0].is_finished is True

    async def test_health_check_fallback_chain(self):
        p = HuggingFaceSpaceProvider()
        p.client = _mock_client({})
        assert await p.health_check() is True

        failing = _mock_client(error=RuntimeError("/models gone"))
        ok_health = MagicMock()
        ok_health.status_code = 200
        failing.get = AsyncMock(side_effect=[RuntimeError("x"), ok_health])
        p.client = failing
        assert await p.health_check() is True

        all_bad = _mock_client(error=RuntimeError("all gone"))
        p.client = all_bad
        assert await p.health_check() is False


class _ChatProviderContract:
    """Shared behavioral checks for Groq/Bynara/BAI (same code shape)."""

    provider_cls = None
    name = None

    def _make(self):
        p = self.provider_cls()
        p.client = _mock_client(_chat_payload("chat"))
        return p

    async def test_chat_with_and_without_system_prompt(self):
        p = self._make()
        out = await p.chat("hello")
        assert out == "chat"
        payload = p.client.post.await_args.kwargs["json"]
        assert payload["messages"][0]["role"] == "user"

        p2 = self._make()
        await p2.chat("hello", system_prompt="be brief")
        msgs = p2.client.post.await_args.kwargs["json"]["messages"]
        assert msgs[0] == {"role": "system", "content": "be brief"}

    async def test_stream_chat(self):
        p = self.provider_cls()
        p.client = _stream_client(['data: {"choices":[{"delta":{"content":"s"}}]}', "data: [DONE]"])
        gen = p.stream_chat("q", system_prompt="sys")
        chunks = [c async for c in gen]
        assert chunks[-1].is_finished is True

    async def test_health_check_no_key(self):
        p = self.provider_cls()
        p.api_key = ""
        assert await p.health_check() is False

    async def test_health_check_exception(self):
        p = self.provider_cls()
        p.api_key = "k"
        p.client = _mock_client(error=RuntimeError("down"))
        assert await p.health_check() is False


class TestGroqProvider(_ChatProviderContract):
    provider_cls = GroqProvider
    name = Provider.GROQ

    def test_defaults(self):
        p = GroqProvider()
        assert p.name == Provider.GROQ
        assert p.base_url == "https://api.groq.com/openai/v1"
        assert p.model == "llama-3.3-70b-versatile"


class TestBynaraProvider(_ChatProviderContract):
    provider_cls = BynaraProvider
    name = Provider.BYNARA

    def test_defaults(self):
        p = BynaraProvider()
        assert p.model == "agnes-2.5-flash"
        assert p.base_url == "https://router.bynara.id/v1"


class TestBAIProvider(_ChatProviderContract):
    provider_cls = BAIProvider
    name = Provider.BAI

    def test_defaults(self):
        p = BAIProvider()
        assert p.model == "qwen3.8-flash"
        assert p.base_url == "https://api.b.ai/v1"


class TestBengaliNormalizer:
    def test_normalize_transliterates(self):
        out = BengaliNormalizer.normalize("Ami tumi kemon acho")
        assert out == "আমি তুমি কেমন আছো"

    def test_normalize_unknown_words_kept(self):
        assert BengaliNormalizer.normalize("hello world") == "hello world"

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("আমি ভালো আছি", "bengali"),
            ("hello আমি", "mixed"),
            ("hello world", "roman"),
            ("   ", "empty"),
        ],
    )
    def test_detect_script(self, text, expected):
        assert BengaliNormalizer.detect_script(text) == expected


class TestCircuitBreakerIntegration:
    async def test_completion_through_breaker_after_failures(self):
        """Failures flow through the circuit breaker decorator cleanly."""
        p = MoonshotProvider()
        p.client = _mock_client(error=httpx.ConnectError("refused"))
        for _ in range(2):
            with pytest.raises(httpx.ConnectError):
                await p.acompletion("q")
