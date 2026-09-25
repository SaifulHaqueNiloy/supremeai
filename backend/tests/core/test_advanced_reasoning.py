"""Tests for core/advanced_reasoning.py — Advanced reasoning engine."""
import pytest
from core.advanced_reasoning import ReasoningEngine


class TestReasoningEngine:
    def test_init(self):
        engine = ReasoningEngine()
        assert engine is not None

    @pytest.mark.asyncio
    async def test_reason_returns_chain(self):
        engine = ReasoningEngine()
        result = await engine.reason("Why is the sky blue?")
        assert result is not None
        assert isinstance(result, (dict, list))

    @pytest.mark.asyncio
    async def test_decompose_problem(self):
        engine = ReasoningEngine()
        result = await engine.decompose("Build a web app with auth")
        assert result is not None

    @pytest.mark.asyncio
    async def test_synthesize_answer(self):
        engine = ReasoningEngine()
        result = await engine.synthesize(["fact1", "fact2", "fact3"])
        assert result is not None
        assert isinstance(result, str)

    def test_set_reasoning_depth(self):
        engine = ReasoningEngine()
        engine.set_depth(3)
        assert engine.depth == 3 or engine._depth == 3
