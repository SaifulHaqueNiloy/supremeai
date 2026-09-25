"""Tests for brain/model_router.py — Model routing logic."""
import pytest
from brain.model_router import ModelRouter


class TestModelRouter:
    """Model router: task-type → model mapping."""

    def test_init(self):
        router = ModelRouter()
        assert router is not None

    def test_route_coding_task(self):
        router = ModelRouter()
        result = router.route("Write a Python function", task_type="coding")
        assert result is not None
        assert "model" in result or "provider" in result

    def test_route_reasoning_task(self):
        router = ModelRouter()
        result = router.route("Analyze the implications", task_type="reasoning")
        assert result is not None

    def test_route_vision_task(self):
        router = ModelRouter()
        result = router.route("Describe this image", task_type="vision")
        assert result is not None

    def test_route_chat_task(self):
        router = ModelRouter()
        result = router.route("Hello", task_type="chat")
        assert result is not None

    def test_route_unknown_task_defaults(self):
        router = ModelRouter()
        result = router.route("Do something", task_type="unknown")
        assert result is not None

    def test_route_considers_available_providers(self):
        router = ModelRouter()
        result = router.route("Complex task", task_type="reasoning", available_providers=["groq", "gemini"])
        assert result is not None
