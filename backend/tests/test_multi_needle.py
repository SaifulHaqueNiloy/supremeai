import os
import tempfile

import pytest

from services.memory_service import CascadeMemoryService


@pytest.fixture
def memory_service():
    """Use temp SQLite DB to avoid touching live production DB."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    svc = CascadeMemoryService(db_path=db_path)
    yield svc
    import gc
    gc.collect()
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.close()
    except Exception:
        pass
    try:
        os.remove(db_path)
    except PermissionError:
        pass


class TestMultiNeedleContext:
    """Tests for multi-hop cross-referencing in CascadeMemoryService."""

    def test_multi_needle_filters_irrelevant_results(self, memory_service):
        """Multi-needle should filter out irrelevant haystack noise."""
        # Use unique file_path per entry to avoid SQLite ON CONFLICT overwrite
        test_memories = [
            ("sess-1", "CodeReview", "refactoring",
             "Supabase pgvector connection pooling configuration for backend services"),
            ("sess-1", "CodeReview", "infra",
             "Redis cache strategy for short-lived worker processes"),
            ("sess-1", "CodeReview", "memory",
             "ai_memory table embedding storage using JSON string format"),
            ("sess-2", "Design", "general",
             "UI color palette for the admin dashboard using Tailwind CSS"),
            ("sess-1", "CodeReview", "rag",
             "pgvector RPC call for multi-needle similarity search optimization"),
        ]
        for idx, (session_id, agent_type, task_type, content) in enumerate(test_memories):
            memory_service.store_memory(
                file_path=f"file-{idx}",  # Unique file_path per entry
                content=content,
                summary=content[:200],
                structure="{}",
                session_id=session_id,
                agent_type=agent_type,
                task_type=task_type,
            )

        multi = memory_service.query_multi_needle_context(
            prompt="Supabase pgvector memory optimization",
            top_k=5,
            needles_count=2,
        )

        assert len(multi) > 0
        summaries = [r["summary"] for r in multi]
        assert not any("color palette" in s.lower() for s in summaries), (
            "Multi-needle should have filtered the unrelated UI design entry"
        )

    def test_multi_needle_returns_subset_of_standard(self, memory_service):
        """Multi-needle results should be a subset of standard results."""
        for i in range(5):
            memory_service.store_memory(
                file_path=f"subset-{i}",
                content=f"Memory entry about topic_{i} with some context",
                summary=f"Memory entry about topic_{i} with some context",
                structure="{}",
                session_id="sess-test",
                agent_type="TestAgent",
                task_type="test",
            )

        prompt = "topic_0 context"
        standard = memory_service.query_context(prompt=prompt, top_k=5)
        multi = memory_service.query_multi_needle_context(
            prompt=prompt, top_k=5, needles_count=2
        )

        standard_summaries = {r["summary"] for r in standard}
        multi_summaries = {r["summary"] for r in multi}
        assert multi_summaries.issubset(standard_summaries)

    def test_multi_needle_single_result_returns_raw(self, memory_service):
        """Edge case: if only 1 result, return it as-is."""
        memory_service.store_memory(
            file_path="single-1",
            content="Unique entry",
            summary="Unique entry",
            structure="{}",
            session_id="sess-single",
            agent_type="Test",
            task_type="test",
        )
        result = memory_service.query_multi_needle_context(
            prompt="Unique entry", top_k=5, needles_count=2
        )
        assert len(result) == 1
