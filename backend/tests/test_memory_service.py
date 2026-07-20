"""
Tests for services/memory_service.py
Focus: chunking/embedding logic and query routing.
"""

from __future__ import annotations


from services.memory_service import CascadeMemoryService, hash_vectorize


# ── hash_vectorize ─────────────────────────────────────────────────────────────


def test_hash_vectorize_returns_fixed_size_list():
    vec = hash_vectorize("hello world", size=8)
    assert isinstance(vec, list)
    assert len(vec) == 8
    assert all(isinstance(v, float) for v in vec)


def test_hash_vectorize_deterministic():
    v1 = hash_vectorize("hello", size=16)
    v2 = hash_vectorize("hello", size=16)
    assert v1 == v2


def test_hash_vectorize_different_texts_differ():
    v1 = hash_vectorize("hello world", size=16)
    v2 = hash_vectorize("goodbye world", size=16)
    assert v1 != v2


# ── CascadeMemoryService ───────────────────────────────────────────────────────


def _make_svc(tmp_path):
    return CascadeMemoryService(db_path=str(tmp_path / "test_memory.db"))


def test_chunk_and_embed_returns_chunks(tmp_path):
    svc = _make_svc(tmp_path)
    content = "Line one.\n\nLine two.\n\nLine three."
    chunks = svc.chunk_and_embed("/fake/file.py", content)
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    for c in chunks:
        assert "file" in c or "summary" in c or "vector" in c


def test_chunk_and_embed_empty_content(tmp_path):
    svc = _make_svc(tmp_path)
    chunks = svc.chunk_and_embed("/fake/file.py", "")
    # May return empty list or placeholder chunk depending on implementation
    assert isinstance(chunks, list)


def test_query_context_returns_list(tmp_path):
    svc = _make_svc(tmp_path)
    # Pre-seed with chunks via chunk_and_embed
    svc.chunk_and_embed("/fake/a.py", "def foo(): pass\ndef bar(): pass\n")
    results = svc.query_context("foo", top_k=3)
    assert isinstance(results, list)
    # Should find at least one chunk mentioning foo or fallback gracefully
    assert all("content" in r or "score" in r or "embedding" in r for r in results)


def test_query_context_top_k_limits_results(tmp_path):
    svc = _make_svc(tmp_path)
    svc.chunk_and_embed("/fake/a.py", "alpha " * 100)
    svc.chunk_and_embed("/fake/b.py", "beta " * 100)
    results = svc.query_context("alpha", top_k=2)
    assert len(results) <= 2


# ── Module-level memory_service instance ──────────────────────────────────────


def test_module_memory_service_is_importable():
    from services import memory_service as ms

    assert hasattr(ms, "memory_service")
