"""Tests for the Self-Evolving Memory Storage service (out_of_box.md item 1).

Covers BLUEPRINT-MEM-001: semantic clustering, semantic deduplication (merge into a
synthesized memory), Ebbinghaus decay GC, hierarchical cluster-probe retrieval and the
autonomous MemoryEvolutionLoop.

Runs fully offline using in-memory/fallback stores — no ChromaDB or network required.
"""

from __future__ import annotations

import asyncio
import math
import os
import tempfile
import time

from memory.chromadb_store import ChromaDBStore
from memory.memory_evolution_loop import _MIN_INTERVAL_SECONDS, MemoryEvolutionLoop
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


def _stored(service: SelfEvolveService) -> dict[str, dict]:
    """Read the store back as {doc_id: doc}.

    Uses get_all_documents() because it is the backend-agnostic read path (it merges
    the local fallback), unlike get_document() which returns mock objects when the
    chromadb package is stubbed out in the test environment.
    """
    return {d["id"]: d for d in service.manager.chroma.get_all_documents()}


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


# ----------------------------------------------------------------------
# Ebbinghaus decay (BLUEPRINT-MEM-001 §3.1)
# ----------------------------------------------------------------------
def test_retention_decays_over_time():
    svc = _make_service()
    _seed(svc, [("d", "a fact that will be forgotten if never revisited")])
    # register_memory sets a birth time without counting an access, so stability is
    # exactly the 30-day base curve: R = e^(-t/S).
    svc.register_memory("d")
    now = time.time()
    fresh = svc.retention_score("d", now=now)
    later = svc.retention_score("d", now=now + 60 * 86400)
    assert fresh.retention > 0.99
    assert later.retention < fresh.retention
    assert later.stability_days == 30.0
    assert abs(later.retention - math.exp(-2.0)) < 0.01
    # The curve must hold for the reported stability at any horizon.
    far = svc.retention_score("d", now=now + 200 * 86400)
    assert abs(far.retention - math.exp(-far.age_days / far.stability_days)) < 1e-9


def test_frequent_access_flattens_decay_curve():
    svc = _make_service()
    _seed(svc, [("hot", "hot memory"), ("cold", "cold memory")])
    for _ in range(10):
        svc.record_access("hot")
    svc.record_access("cold")
    now = time.time() + 60 * 86400
    hot = svc.retention_score("hot", now=now)
    cold = svc.retention_score("cold", now=now)
    assert hot.stability_days > cold.stability_days
    assert hot.retention > cold.retention


def test_importance_score_extends_retention():
    svc = _make_service()
    _seed(svc, [("vip", "critical architectural decision"), ("plain", "ordinary note")])
    svc.record_access("vip")
    svc.record_access("plain")
    svc.set_importance("vip", 5.0)
    now = time.time() + 60 * 86400
    vip = svc.retention_score("vip", now=now)
    plain = svc.retention_score("plain", now=now)
    assert vip.importance_score == 5.0
    assert vip.stability_days == plain.stability_days * 5.0
    assert vip.retention > plain.retention


def test_prune_decayed_removes_forgotten_memory():
    svc = _make_service()
    _seed(svc, [("forgotten", "nobody ever reads this memory again")])
    svc.record_access("forgotten")
    future = time.time() + 200 * 86400
    result = _run(svc.prune_decayed_memories(now_provider=lambda: future))
    assert "forgotten" in result.removed_ids
    assert result.retained == 0
    assert result.scores["forgotten"] < 0.15


def test_prune_decayed_respects_min_age_floor():
    svc = _make_service()
    _seed(svc, [("young", "recent but rarely read memory")])
    svc.record_access("young")
    future = time.time() + 200 * 86400
    # Retention is far below threshold, but the hard age floor must still protect it.
    result = _run(
        svc.prune_decayed_memories(min_age_days=365, now_provider=lambda: future)
    )
    assert result.removed_ids == []
    assert result.retained == 1


def test_prune_decayed_skips_pinned_and_untracked():
    svc = _make_service()
    svc.manager.chroma.add_document(
        doc_id="pinned", text="permanent core principle", metadata={"pinned": True}
    )
    svc.manager.chroma.add_document(doc_id="untracked", text="never registered memory")
    svc.record_access("pinned")
    future = time.time() + 500 * 86400
    result = _run(svc.prune_decayed_memories(now_provider=lambda: future))
    assert result.removed_ids == []
    assert result.retained == 2


def test_prune_decayed_dry_run_keeps_data():
    svc = _make_service()
    _seed(svc, [("ghost", "stale memory targeted by a dry run")])
    svc.record_access("ghost")
    future = time.time() + 200 * 86400
    result = _run(svc.prune_decayed_memories(dry_run=True, now_provider=lambda: future))
    assert result.removed_ids == ["ghost"]
    assert result.dry_run is True
    assert "ghost" in _stored(svc)


def test_decay_report_orders_weakest_first():
    svc = _make_service()
    _seed(svc, [("stale", "old memory"), ("active", "active memory")])
    svc.record_access("stale")
    for _ in range(5):
        svc.record_access("active")
    report = _run(svc.decay_report(now_provider=lambda: time.time() + 120 * 86400))
    assert next(s.doc_id for s in report) == "stale"


# ----------------------------------------------------------------------
# Semantic deduplication (merge into synthesized memory)
# ----------------------------------------------------------------------
def test_deduplicate_merges_exact_duplicates():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "redis cluster failover configuration guide"),
            ("b", "redis cluster failover configuration guide"),
            ("c", "unrelated memory about watercolor painting"),
        ],
    )
    result = _run(svc.deduplicate_memories())
    assert result.merged_count == 1
    assert len(result.groups) == 1
    assert result.groups[0].similarity == 1.0
    survivor = result.groups[0].survivor_id
    absorbed = result.groups[0].merged_ids[0]
    assert {survivor, absorbed} == {"a", "b"}
    remaining = _stored(svc)
    assert set(remaining) == {survivor, "c"}
    assert absorbed not in remaining


def test_deduplicate_synthesizes_union_of_content():
    svc = _make_service()
    _seed(
        svc,
        [
            ("long", "deploy with docker compose. use the staging profile first."),
            ("short", "deploy with docker compose."),
        ],
    )
    result = _run(svc.deduplicate_memories(threshold=0.5))
    assert result.merged_count == 1
    survivor = _stored(svc)[result.groups[0].survivor_id]
    # Both unique sentences survive the merge — no information loss.
    assert "docker compose" in survivor["text"]
    assert "staging profile" in survivor["text"]
    assert survivor["metadata"]["is_synthesized"] is True
    assert survivor["metadata"]["merged_count"] == 1


def test_deduplicate_survivor_is_most_accessed():
    svc = _make_service()
    _seed(
        svc,
        [
            ("cold", "identical memory content here"),
            ("hot", "identical memory content here"),
        ],
    )
    for _ in range(3):
        svc.record_access("hot")
    result = _run(svc.deduplicate_memories())
    assert result.groups[0].survivor_id == "hot"
    # Absorbed access stats fold into the survivor.
    assert svc.get_access_record("hot").access_count >= 3
    assert svc.get_access_record("cold").known is False


def test_deduplicate_merges_three_way_group():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "opentelemetry span export batching"),
            ("b", "opentelemetry span export batching"),
            ("c", "opentelemetry span export batching"),
            ("d", "unrelated note on bicycle gear ratios"),
        ],
    )
    result = _run(svc.deduplicate_memories())
    # A transitive duplicate group collapses to a single survivor, not pairwise merges.
    assert len(result.groups) == 1
    assert result.merged_count == 2
    assert set(_stored(svc)) == {result.groups[0].survivor_id, "d"}


def test_deduplicate_dry_run_does_not_mutate():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "duplicate content for preview"),
            ("b", "duplicate content for preview"),
        ],
    )
    result = _run(svc.deduplicate_memories(dry_run=True))
    assert result.dry_run is True
    assert result.merged_count == 0
    assert len(result.groups) == 1
    assert len(_stored(svc)) == 2


def test_deduplicate_keeps_distinct_memories():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "postgres connection pooling with pgbouncer"),
            ("b", "frontend animation timing curves in css"),
        ],
    )
    result = _run(svc.deduplicate_memories())
    assert result.merged_count == 0
    assert len(_stored(svc)) == 2


# ----------------------------------------------------------------------
# Cluster persistence + hierarchical retrieval
# ----------------------------------------------------------------------
def test_assign_cluster_ids_persists_metadata():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "graphql schema stitching across microservices"),
            ("b", "graphql schema stitching across microservices"),
            ("c", "baking sourdough bread at home"),
        ],
    )
    assignments = _run(svc.assign_cluster_ids())
    assert set(assignments) == {"a", "b"}
    assert assignments["a"] == assignments["b"]
    stored = _stored(svc)
    assert stored["a"]["metadata"]["cluster_id"] == assignments["a"]
    assert stored["a"]["metadata"]["cluster_size"] == 2
    # Unclustered memory keeps no cluster metadata.
    assert "cluster_id" not in (stored["c"]["metadata"] or {})


def test_hierarchical_search_scans_fewer_docs_than_corpus():
    svc = _make_service()
    docs = [
        ("k1", "kubernetes ingress controller tls termination"),
        ("k2", "kubernetes ingress controller tls termination"),
    ]
    # Distinct filler memories so probing a subset of clusters is a real reduction.
    filler_topics = [
        "sourdough bread fermentation timing",
        "watercolor pigment granulation techniques",
        "orbital mechanics hohmann transfer window",
        "medieval lute tablature notation",
        "tax depreciation schedule for equipment",
        "coral reef bleaching temperature thresholds",
    ]
    docs += [(f"f{i}", topic) for i, topic in enumerate(filler_topics)]
    _seed(svc, docs)
    _run(svc.assign_cluster_ids())
    result = _run(
        svc.hierarchical_search("kubernetes ingress controller tls", cluster_probe=1)
    )
    assert result.docs_total == len(docs)
    assert result.docs_scanned < result.docs_total
    assert result.fallback_full_scan is False
    assert result.matches[0].doc_id in {"k1", "k2"}


def test_hierarchical_search_handles_unclustered_corpus():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "rust borrow checker lifetime elision"),
            ("b", "japanese tea ceremony utensils"),
        ],
    )
    result = _run(svc.hierarchical_search("rust borrow checker", cluster_probe=5))
    assert result.matches[0].doc_id == "a"
    assert result.clusters_total == 2  # each singleton is its own probe bucket


def test_hierarchical_search_empty_store():
    svc = _make_service()
    result = _run(svc.hierarchical_search("anything"))
    assert result.matches == []
    assert result.docs_total == 0


# ----------------------------------------------------------------------
# Full cycle orchestration
# ----------------------------------------------------------------------
def test_reorganize_full_cycle_merges_and_persists_clusters():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "terraform state locking with dynamodb"),
            ("b", "terraform state locking with dynamodb"),
            ("c", "gardening compost nitrogen balance"),
        ],
    )
    summary = _run(
        svc.reorganize_storage(merge_duplicates=True, apply_decay=True, persist_clusters=True)
    )
    assert summary.merged == 1
    assert summary.duration_ms >= 0
    assert len(_stored(svc)) == 2


def test_reorganize_default_is_non_destructive():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "identical memory for safety check"),
            ("b", "identical memory for safety check"),
        ],
    )
    summary = _run(svc.reorganize_storage())
    assert summary.merged == 0
    assert summary.decay_pruned == 0
    assert len(_stored(svc)) == 2


# ----------------------------------------------------------------------
# Autonomous evolution loop
# ----------------------------------------------------------------------
def test_evolution_loop_run_once_records_stats():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "grpc streaming backpressure handling"),
            ("b", "grpc streaming backpressure handling"),
        ],
    )
    loop = MemoryEvolutionLoop(service=svc, interval_seconds=30)
    result = _run(loop.run_once())
    assert result.merged == 1
    assert loop.stats.cycles == 1
    assert loop.stats.failures == 0
    assert loop.stats.total_merged == 1
    assert loop.stats.last_error is None
    assert loop.status()["stats"]["cycles"] == 1


def test_evolution_loop_dry_run_does_not_mutate():
    svc = _make_service()
    _seed(
        svc,
        [
            ("a", "identical dry run memory"),
            ("b", "identical dry run memory"),
        ],
    )
    loop = MemoryEvolutionLoop(service=svc, interval_seconds=30, dry_run=True)
    result = _run(loop.run_once())
    assert result.duplicates == 1
    assert result.merged == 0
    assert len(_stored(svc)) == 2


def test_evolution_loop_survives_cycle_failure():
    svc = _make_service()
    loop = MemoryEvolutionLoop(service=svc, interval_seconds=30)

    async def _boom(*args, **kwargs):
        raise RuntimeError("store offline")

    svc.reorganize_storage = _boom  # type: ignore[method-assign]
    result = _run(loop.run_once())
    assert result.merged == 0
    assert loop.stats.failures == 1
    assert "store offline" in (loop.stats.last_error or "")


def test_evolution_loop_start_stop_lifecycle():
    svc = _make_service()
    _seed(svc, [("a", "loop lifecycle memory")])
    loop = MemoryEvolutionLoop(service=svc, interval_seconds=_MIN_INTERVAL_SECONDS)

    async def _scenario() -> None:
        assert await loop.start() is True
        # A second start must not spawn a duplicate task.
        assert await loop.start() is False
        assert loop.running is True
        # Give the loop time to complete its first cycle.
        for _ in range(50):
            if loop.stats.cycles >= 1:
                break
            await asyncio.sleep(0.02)
        assert await loop.stop(timeout=5.0) is True
        assert loop.running is False

    _run(_scenario())
    assert loop.stats.cycles >= 1


def test_evolution_loop_interval_floor_and_env_flag(monkeypatch):
    loop = MemoryEvolutionLoop(interval_seconds=1)
    assert loop.interval_seconds == _MIN_INTERVAL_SECONDS
    monkeypatch.setenv("ENABLE_MEMORY_EVOLUTION", "true")
    assert MemoryEvolutionLoop.is_enabled() is True
    monkeypatch.setenv("ENABLE_MEMORY_EVOLUTION", "false")
    assert MemoryEvolutionLoop.is_enabled() is False


def test_evolution_loop_from_env_reads_overrides(monkeypatch):
    monkeypatch.setenv("MEMORY_EVOLUTION_INTERVAL_SECONDS", "120")
    monkeypatch.setenv("MEMORY_EVOLUTION_APPLY_DECAY", "false")
    monkeypatch.setenv("MEMORY_EVOLUTION_RETENTION_THRESHOLD", "0.4")
    monkeypatch.setenv("MEMORY_EVOLUTION_DRY_RUN", "true")
    loop = MemoryEvolutionLoop.from_env()
    assert loop.interval_seconds == 120
    assert loop.apply_decay is False
    assert loop.retention_threshold == 0.4
    assert loop.dry_run is True


def test_evolution_loop_from_env_survives_bad_values(monkeypatch):
    monkeypatch.setenv("MEMORY_EVOLUTION_INTERVAL_SECONDS", "not-a-number")
    monkeypatch.setenv("MEMORY_EVOLUTION_RETENTION_THRESHOLD", "abc")
    loop = MemoryEvolutionLoop.from_env()
    assert loop.interval_seconds == 3600
    assert loop.retention_threshold == 0.15
