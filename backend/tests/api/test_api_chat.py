from __future__ import annotations

from types import SimpleNamespace

import pytest

from api.routes.chat import ChatPayload, get_completion, stream_chat


class FakeCache:
    def __init__(self, value=None):
        self.value = value
        self.saved = None

    async def get(self, prompt: str, model_name: str, session_id: str = None, user_id: str = None):
        # AUD-5.6: chat now passes user_id for user-scoped cache keys.
        return self.value

    async def set(
        self,
        prompt: str,
        response: str,
        model_name: str,
        session_id: str = None,
        user_id: str = None,
    ):
        self.saved = {
            "prompt": prompt,
            "response": response,
            "model_name": model_name,
            "session_id": session_id,
            "user_id": user_id,
        }


class FakeModel:
    def __init__(self, model_name: str):
        self.model_name = model_name

    async def generate_content_async(self, prompt: str, stream: bool = False):
        if prompt == "raise-error":
            raise RuntimeError("boom")
        return SimpleNamespace(text=f"generated:{prompt}")


@pytest.mark.asyncio
async def test_get_completion_returns_cached_result(monkeypatch):
    fake_cache = FakeCache(
        value={
            "success": True,
            "response": "cached-response",
            "source": "L5_CACHE",
            "latency_ms": 10,
        }
    )
    monkeypatch.setattr("api.routes.chat.multi_layer_cache", fake_cache)
    request = SimpleNamespace(headers={"X-Session-ID": "session-1"})
    payload = ChatPayload(prompt="hello")
    result = await get_completion(request, payload, db=SimpleNamespace(tenant_id="tenant-1"))

    assert result["cached"] is True
    assert result["response"] == "cached-response"
    assert result["cache_source"] == "L5_CACHE"


@pytest.mark.asyncio
async def test_get_completion_generates_response_and_saves_cache(monkeypatch):
    fake_cache = FakeCache(value=None)
    monkeypatch.setattr("api.routes.chat.multi_layer_cache", fake_cache)
    # বাংলা মন্তব্য (#2835): প্রোডাকশন কল-সাইট (#2726) এখন model= override +
    # InferenceContext পাঠায় — পুরনো (prompt, context=None) স্টাব সিগনেচারে
    # TypeError → নীরবে graceful-fallback → টেস্ট RED। স্টাব চুক্তি হালনাগাদ।
    # context-engine ডকুমেন্টেড kill-switch ব্যবহার — raw-prompt passthrough,
    # যাতে টেস্টের মূল উদ্দেশ্য (completion+cache চুক্তি) prompt-identity ছাড়াই
    # পৃথক থাকে (ইঞ্জিন ডিফল্ট চালু — enriched prompt ≠ raw prompt)।
    monkeypatch.setenv("SUPREMEAI_CONTEXT_ENGINE", "off")

    async def mock_acompletion(prompt, model=None, context=None):
        if prompt == "raise-error":
            raise RuntimeError("boom")
        return {"text": f"generated:{prompt}"}

    async def mock_recall_memories(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "api.routes.chat.llm_gateway", SimpleNamespace(acompletion=mock_acompletion)
    )
    monkeypatch.setattr("services.memory_service.recall_memories", mock_recall_memories)

    request = SimpleNamespace(headers={"X-Session-ID": "session-2"})
    payload = ChatPayload(prompt="live-prompt")
    result = await get_completion(request, payload, db=SimpleNamespace(tenant_id="tenant-2"))

    assert result["cached"] is False
    assert result["response"] == "generated:live-prompt"
    assert fake_cache.saved is not None
    assert fake_cache.saved["model_name"] == "gemini-2.5-pro"


@pytest.mark.asyncio
async def test_get_completion_returns_graceful_fallback_on_model_failure(monkeypatch):
    fake_cache = FakeCache(value=None)
    monkeypatch.setattr("api.routes.chat.multi_layer_cache", fake_cache)

    # বাংলা মন্তব্য (#2835): #2726-পরবর্তী কল-চুক্তি (model= kwarg) + raw-prompt
    # passthrough — নইলতে enriched prompt-এ "raise-error" সনাক্ত হয় না।
    monkeypatch.setenv("SUPREMEAI_CONTEXT_ENGINE", "off")

    async def mock_acompletion(prompt, model=None, context=None):
        raise RuntimeError("boom")

    async def mock_recall_memories(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "api.routes.chat.llm_gateway", SimpleNamespace(acompletion=mock_acompletion)
    )
    monkeypatch.setattr("services.memory_service.recall_memories", mock_recall_memories)

    request = SimpleNamespace(headers={"X-Session-ID": "session-3"})
    payload = ChatPayload(prompt="raise-error")

    result = await get_completion(request, payload, db=SimpleNamespace(tenant_id="tenant-3"))

    assert result["success"] is True
    assert result["source"] == "no_match"
    assert "দুঃখিত" in result["response"]


@pytest.mark.asyncio
async def test_stream_chat_yields_sse_chunks(monkeypatch):
    # বাংলা মন্তব্য (#2835): স্ট্রিমিং পথেও #2726-পরবর্তী model= kwarg —
    # স্টাব সিগনেচার হালনাগাদ (chunk-চুক্তি অক্ষত)।
    async def mock_acompletion(prompt, model=None, context=None):
        class Response:
            async def __aiter__(self):
                yield "chunk-one"
                yield "chunk-two"

        return Response()

    monkeypatch.setattr(
        "api.routes.chat.llm_gateway", SimpleNamespace(acompletion=mock_acompletion)
    )
    request_payload = ChatPayload(prompt="stream-prompt")
    response = await stream_chat(request_payload, db=SimpleNamespace(tenant_id="tenant-4"))

    assert response.media_type == "text/event-stream"

    body = b""
    async for chunk in response.body_iterator:
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        body += chunk

    assert b"chunk-one" in body
    assert b"chunk-two" in body
