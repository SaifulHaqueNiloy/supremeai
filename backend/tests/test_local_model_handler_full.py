# tests/test_local_model_handler_full.py
"""Unit tests for LocalModelHandler (Ollama / Local Inference)."""

import pytest
import respx
from httpx import Response

from models.local_model_handler import LocalModelHandler


@pytest.mark.asyncio
async def test_health_check_success():
    handler = LocalModelHandler("http://localhost:11434")
    async with respx.mock:
        respx.get("http://localhost:11434/api/tags").mock(return_value=Response(200, json={"models": []}))
        assert await handler.health_check() is True


@pytest.mark.asyncio
async def test_health_check_failure():
    handler = LocalModelHandler("http://localhost:11434")
    async with respx.mock:
        respx.get("http://localhost:11434/api/tags").mock(return_value=Response(500))
        assert await handler.health_check() is False


@pytest.mark.asyncio
async def test_list_models_success():
    handler = LocalModelHandler("http://localhost:11434")
    async with respx.mock:
        respx.get("http://localhost:11434/api/tags").mock(
            return_value=Response(200, json={"models": [{"name": "llama3:latest"}, {"name": "mistral:latest"}]})
        )
        models = await handler.list_models()
        assert models == ["llama3:latest", "mistral:latest"]


@pytest.mark.asyncio
async def test_infer_success_and_caching():
    handler = LocalModelHandler("http://localhost:11434")
    async with respx.mock:
        route = respx.post("http://localhost:11434/api/generate").mock(
            return_value=Response(200, json={"response": "Hello from Ollama!", "eval_count": 12})
        )

        res1 = await handler.infer("llama3", "Hi")
        assert res1["status"] == "success"
        assert res1["text"] == "Hello from Ollama!"
        assert res1["cached"] is False
        assert route.call_count == 1

        # Second call should use in-memory cache
        res2 = await handler.infer("llama3", "Hi")
        assert res2["status"] == "success"
        assert res2["text"] == "Hello from Ollama!"
        assert res2["cached"] is True
        assert route.call_count == 1
