"""Tests for Learning Pipeline — Phase 3 Evolution Activation (#1035)."""

import asyncio
import sys
from pathlib import Path

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evolution.evolution_orchestrator import (
    EvolutionOrchestrator,
    EvolutionResult,
    get_evolution_orchestrator,
)
from evolution.learning_pipeline import (
    FailurePattern,
    LearningPipeline,
    LearningResult,
    get_learning_pipeline,
)


class TestLearningPipeline:
    """Test the Learning Pipeline module."""

    @pytest.mark.asyncio
    async def test_process_new_failure(self):
        """New failure → stored as new pattern."""
        pipeline = LearningPipeline()
        failure = {
            "test_id": "tests.core.test_x::test_y",
            "failure_type": "import_error",
            "message": "ImportError: cannot import name 'X' from 'core.y'",
            "snippet": "ModuleNotFoundError",
            "file_path": "backend/tests/core/test_x.py",
        }
        result = await pipeline.process_failure(failure)
        assert result.pattern_found is False
        assert result.pattern is not None
        assert result.pattern.failure_type == "import_error"
        assert result.confidence == 0.3

    @pytest.mark.asyncio
    async def test_process_repeated_failure(self):
        """Same failure twice → pattern found on second occurrence."""
        pipeline = LearningPipeline()
        failure = {
            "test_id": "tests.core.test_x::test_y",
            "failure_type": "assertion_mismatch",
            "message": "AssertionError: assert 1 == 2",
            "snippet": "assert result == 2",
            "file_path": "backend/tests/core/test_x.py",
        }
        # First time — new pattern
        result1 = await pipeline.process_failure(failure)
        assert result1.pattern_found is False
        assert result1.pattern.occurrences == 1

        # Second time — pattern found
        result2 = await pipeline.process_failure(failure)
        assert result2.pattern_found is True
        assert result2.pattern.occurrences == 2

    @pytest.mark.asyncio
    async def test_different_failures_different_patterns(self):
        """Different failures → different patterns."""
        pipeline = LearningPipeline()
        failure1 = {
            "test_id": "test_a",
            "failure_type": "import_error",
            "message": "ModuleNotFoundError: No module named 'x'",
            "snippet": "",
            "file_path": "a.py",
        }
        failure2 = {
            "test_id": "test_b",
            "failure_type": "syntax_error",
            "message": "SyntaxError: invalid syntax",
            "snippet": "",
            "file_path": "b.py",
        }
        await pipeline.process_failure(failure1)
        await pipeline.process_failure(failure2)
        stats = await pipeline.get_stats()
        assert stats["total_patterns"] == 2

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Stats return correct info."""
        pipeline = LearningPipeline()
        stats = await pipeline.get_stats()
        assert "total_patterns" in stats
        assert "pattern_recognizer_active" in stats
        assert "memory_consolidator_active" in stats

    def test_suggest_fix_for_type(self):
        """Fix suggestion returns None for unknown types."""
        pipeline = LearningPipeline()
        assert pipeline.suggest_fix_for_type("unknown_type") is None

    def test_singleton(self):
        """get_learning_pipeline returns same instance."""
        p1 = get_learning_pipeline()
        p2 = get_learning_pipeline()
        assert p1 is p2


class TestEvolutionOrchestrator:
    """Test the Evolution Orchestrator."""

    @pytest.mark.asyncio
    async def test_process_task_no_failure(self):
        """Task without failure_data → success."""
        orch = EvolutionOrchestrator()
        result = await orch.process_task({"type": "feature", "description": "add dark mode"})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_process_task_with_failure(self):
        """Task with failure_data → learning result."""
        orch = EvolutionOrchestrator()
        result = await orch.process_task(
            {
                "type": "fix_ci_failure",
                "description": "fix import error",
                "failure_data": {
                    "test_id": "test_x",
                    "failure_type": "import_error",
                    "message": "ImportError: cannot import name 'Y'",
                    "snippet": "",
                    "file_path": "test_x.py",
                },
            }
        )
        assert result.success is True
        assert result.learning is not None

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Status returns module availability."""
        orch = EvolutionOrchestrator()
        status = await orch.get_status()
        assert "living_engine_active" in status
        assert "self_correction_active" in status
        assert "auto_healer_active" in status
        assert "learning_pipeline" in status

    def test_singleton(self):
        """get_evolution_orchestrator returns same instance."""
        o1 = get_evolution_orchestrator()
        o2 = get_evolution_orchestrator()
        assert o1 is o2
