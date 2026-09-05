"""Unit tests verifying AI Chat Streaming dual contract and backwards compatibility.

Tests both /api/chat/stream and /api/v1/stream/chat with both 'prompt' and 'message' payloads.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from core.app import app

client = TestClient(app)


@pytest.fixture
def mock_streaming_gateway():
    import core.services as services_mod
    from core.llm.llm_gateway import llm_gateway

    previous_router = getattr(services_mod, "model_router", None)
    fake_router = MagicMock()

    async def fake_stream(*args, **kwargs):
        for token in ["Hello", " world", "!"]:
            yield token.encode("utf-8")

    fake_router.async_route_and_stream = fake_stream
    services_mod.model_router = fake_router

    async def fake_gateway_stream(*args, **kwargs):
        if kwargs.get("stream"):

            async def _gen():
                for token in ["Hello", " from", " SSE", "!"]:
                    yield token

            return _gen()
        return {"text": "Hello fallback"}

    orig_acompletion = llm_gateway.acompletion
    llm_gateway.acompletion = AsyncMock(side_effect=fake_gateway_stream)

    yield

    if previous_router:
        services_mod.model_router = previous_router
    llm_gateway.acompletion = orig_acompletion


def test_post_chat_stream_legacy_payload(mock_streaming_gateway):
    """Verify POST /api/chat/stream handles legacy {message: '...'} and yields token + delta."""
    response = client.post(
        "/api/chat/stream",
        json={"message": "test message", "sessionId": "sess-123"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert "data: " in body
    assert "token" in body
    assert "delta" in body
    assert "[DONE]" in body


def test_post_stream_chat_sse_with_prompt(mock_streaming_gateway):
    """Verify POST /api/v1/stream/chat handles modern {prompt: '...'} without 422 error."""
    response = client.post(
        "/api/v1/stream/chat",
        json={"prompt": "test prompt", "session_id": "sess-456"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert "event: connected" in body
    assert "event: token" in body
    assert "token" in body
    assert "delta" in body
    assert "event: done" in body
    assert "[DONE]" in body


def test_post_stream_chat_sse_with_message_alias(mock_streaming_gateway):
    """Verify POST /api/v1/stream/chat handles UI {message: '...'} without 422 error."""
    response = client.post(
        "/api/v1/stream/chat",
        json={"message": "hello UI message", "sessionId": "sess-789"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert "event: token" in body
    assert "delta" in body
    assert "token" in body


def test_validation_error_when_neither_prompt_nor_message():
    """Verify 422 validation error when neither prompt nor message is provided."""
    response = client.post(
        "/api/v1/stream/chat",
        json={"task_type": "chat"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422
