"""Tests for services/living_engine.py — Living intelligence engine."""
import pytest
from services.living_engine import LivingEngine


class TestLivingEngine:
    def test_init(self):
        engine = LivingEngine()
        assert engine is not None

    @pytest.mark.asyncio
    async def test_process_input(self):
        engine = LivingEngine()
        result = await engine.process("Hello, what can you do?")
        assert result is not None

    @pytest.mark.asyncio
    async def test_learn_from_feedback(self):
        engine = LivingEngine()
        result = await engine.learn({"input": "test", "feedback": "good"})
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_state(self):
        engine = LivingEngine()
        state = await engine.get_state()
        assert state is not None
        assert isinstance(state, dict)
