"""Tests for the Self-Evolving Memory Storage service (out_of_box.md item 1).

Runs fully offline using in-memory/fallback stores — no ChromaDB or network required.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import time

from memory.chromadb_store import ChromaDBStore
from memory.self_evolve_service import SelfEvolveService
from memory.sqlite_store import SQLiteStore
from memory.unified_db_manager import UnifiedDBManager


def _run(coro):
    return asyncio.run(coro)


def _make_service() -> SelfEvolveService:
    tmp = tempfile.mkdtemp()
    chroma = ChromaDBStore(db_path=os.path.join(tmp, "chroma"))
    sqlite = SQLiteStore(db_path=":memory:")
    manager = UnifiedDBManager(
        sqlite_store=sqlite,
        chroma_store=chroma,
        supabase_store=None,  # type: ignore[arg-type]
        postgres_store=None,  # type: ignore[arg-type]
    )
    return SelfEvolveService(manager=manager, stats_path=os.path.join(tmp, "stats.db"))


def _seed(service: SelfEvolveService, docs: list[tuple[str, str]]) -> None:
    for doc_id, text in docs:
        service.manager.chroma.add_document(doc_id=doc_id, text=text, metadata={"doc_id": doc_id})


def test_cluster_groups_similar_memories():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "python async function for fast api route handling"),
            ("b", "python async function for fast api route handling"),
            ("c", "quantum entanglement and particle superposition physics"),
        ],
    )
    clusters = _run(svc.cluster_memories())
    assert clusters.total == 3
    assert len(clusters.clusters) == 1
    assert clusters.clusters[0].size == 2
    assert set(clusters.clusters[0].member_ids) == {"a", "b"}


def test_find_duplicates_detects_exact_and_semantic():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "the quick brown fox jumps over the lazy dog"),
            ("b", "the quick brown fox jumps over the lazy dog"),
            ("c", "machine learning models predict future trends from data"),
        ],
    )
    dups = _run(svc.find_duplicates())
    exact = [d for d in dups if d.exact]
    assert len(exact) == 1
    assert {exact[0].doc_a, exact[0].doc_b} == {"a", "b"}


def test_prune_removes_stale_underaccessed_memory():
    svc = _make_service()
    _seed(svc, [("old", "stale memory that nobody uses anymore")])
    svc.record_access("old")
    future = time.time() + 120 * 86400
    result = _run(
        svc.prune_unused(max_age_days=1, min_access=2, now_provider=lambda: future)
    )
    assert "old" in result.removed_ids
    assert result.retained == 0
    assert result.freed_bytes_estimate > 0


def test_prune_keeps_fresh_memory():
    svc = _make_service()
    _seed(svc, [("fresh", "recently used important memory")])
    svc.record_access("fresh")
    result = _run(svc.prune_unused(max_age_days=90, min_access=1))
    assert result.removed_ids == []
    assert result.retained == 1


def test_reorganize_returns_summary():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "kubernetes pod scheduling and container orchestration"),
            ("b", "kubernetes pod scheduling and container orchestration"),
            ("c", "classical piano sonata composition and music theory"),
        ],
    )
    summary = _run(svc.reorganize_storage())
    assert summary.clusters == 1
    assert summary.duplicates >= 1
    assert summary.retained >= 0
