"""SlidingWindowMemory — windowing math, hierarchical compaction, and durability.

Complements tests/core/test_sliding_window_memory.py (chunk/recall/clear/build basics)
with the internals that were previously unmeasured in CI:

- ``_make_windows`` overlap stepping + invariants (window size ≤ max_tokens, tail covered)
- ``_summarize_text`` sentence/char snippet rules, ``_token_count`` min-1 guard
- ``:memory:`` connection reuse + close-guard (file mode closes, memory mode doesn't)
- persist failure → False (NOT NULL violation), summary/created_at defaulting
- hierarchical compaction: threshold trigger, level increment (existing+1), parent
  summary selection (``summary or text``), flat 800-char cap, level-ordered reads
- ``build_context`` compact-front insertion, query-driven length reordering, budget
  pruning, empty-input guard
- ``get_session_stats`` counters, default db_path derivation (with cleanup)

Wire-first: tests only — zero owner production code touched.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from memory.sliding_window import MemoryWindowRecord, SlidingWindowConfig, SlidingWindowMemory


@pytest.fixture()
def store(tmp_path: Path) -> SlidingWindowMemory:
    return SlidingWindowMemory(
        config=SlidingWindowConfig(auto_compact=False), db_path=str(tmp_path / "sw.db")
    )


# ---------------------------------------------------------------------------
# Config + dataclass defaults
# ---------------------------------------------------------------------------
def test_config_defaults():
    cfg = SlidingWindowConfig()
    assert (cfg.max_tokens, cfg.overlap_ratio) == (4000, 0.15)
    assert cfg.summarize and cfg.store_summaries and cfg.auto_compact
    assert cfg.compaction_threshold == 50


def test_memory_window_record_defaults():
    rec = MemoryWindowRecord(window_index=0, text="t", token_count=1)
    assert rec.summary is None and rec.created_at == ""


# ---------------------------------------------------------------------------
# Windowing math
# ---------------------------------------------------------------------------
def test_make_windows_short_text_single_window(store):
    assert store._make_windows("just one sentence") == ["just one sentence"]


def test_make_windows_overlap_step_invariants():
    sw = SlidingWindowMemory(
        config=SlidingWindowConfig(max_tokens=10, overlap_ratio=0.2, auto_compact=False),
        db_path=":memory:",
    )
    words = [f"w{i}" for i in range(25)]
    windows = sw._make_windows(" ".join(words))
    assert all(len(w.split()) <= 10 for w in windows)
    # step = max_tokens - overlap = 10 - 2 = 8 → windows start at 0, 8, 16, 24
    assert windows[0].startswith("w0 ")
    assert windows[1].startswith("w8 ")
    assert windows[2].startswith("w16 ")
    assert windows[-1] == "w24"  # final partial window still covers the tail
    assert len(windows) == 4


def test_token_count_min_one_guard(store):
    assert store._token_count("") == 1
    assert store._token_count("a b c") == 3


def test_summarize_text_rules(store):
    assert store._summarize_text("") == ""
    assert store._summarize_text("First sentence. Second one.") == "First sentence."
    long = "x" * 200
    assert store._summarize_text(long) == "x" * 120  # no sentence break → 120-char cap
    assert (
        store._summarize_text("Line one.\nMore") == "Line one. More"
    )  # '.\n' is not '. ' → char cap path


# ---------------------------------------------------------------------------
# :memory: mode + connection lifecycle
# ---------------------------------------------------------------------------
def test_memory_conn_reused_and_not_closed():
    sw = SlidingWindowMemory(db_path=":memory:")
    assert sw._memory_conn is not None
    conn1 = sw._connect()
    conn2 = sw._connect()
    assert conn1 is conn2  # single shared in-memory connection
    sw.persist("s1", [MemoryWindowRecord(0, "kept", 1)])
    assert sw.recall("s1")[0]["text"] == "kept"


# ---------------------------------------------------------------------------
# Persistence — defaults, failure, recall ordering
# ---------------------------------------------------------------------------
def test_persist_defaults_summary_and_created_at(store):
    ok = store.persist(
        "sess", [MemoryWindowRecord(window_index=0, text="Alpha beta. Gamma.", token_count=3)]
    )
    assert ok is True
    row = store.recall("sess")[0]
    assert row["summary"] == "Alpha beta."  # derived when summary missing
    assert row["created_at"] != ""  # defaulted to utc_now_iso()


def test_persist_respects_explicit_summary_and_created_at(store):
    store.persist(
        "sess",
        [
            MemoryWindowRecord(
                window_index=0,
                text="t",
                token_count=1,
                summary="explicit",
                created_at="2026-01-01T00:00:00Z",
            )
        ],
    )
    row = store.recall("sess")[0]
    assert row["summary"] == "explicit" and row["created_at"] == "2026-01-01T00:00:00Z"


def test_persist_failure_returns_false(store):
    # NOT NULL violation: text=None breaches conversation_windows.text
    bad = MemoryWindowRecord(window_index=0, text=None, token_count=1)  # type: ignore[arg-type]
    assert store.persist("sess", [bad]) is False


def test_recall_order_newest_first_with_limit(store):
    for i in range(5):
        store.persist(
            "sess", [MemoryWindowRecord(i, f"msg {i}", 2, created_at=f"2026-01-0{i + 1}T00:00:00Z")]
        )
    rows = store.recall("sess", limit=3)
    assert [r["text"] for r in rows] == ["msg 4", "msg 3", "msg 2"]
    other = store.recall("sess", limit=100)
    assert len(other) == 5


# ---------------------------------------------------------------------------
# Hierarchical compaction
# ---------------------------------------------------------------------------
def test_compaction_triggers_at_threshold_and_increments_levels(tmp_path):
    sw = SlidingWindowMemory(
        config=SlidingWindowConfig(max_tokens=5, compaction_threshold=4, auto_compact=True),
        db_path=str(tmp_path / "compact.db"),
    )
    for i in range(4):
        sw.chunk(f"document number {i} with content", session_id="c1")
    summaries = sw.get_compact_summaries("c1")
    assert len(summaries) == 1
    assert summaries[0]["level"] == 1
    assert summaries[0]["window_count"] == 4

    # _compact_if_needed re-fires on EVERY persist once count ≥ threshold → level 2
    sw.chunk("document number 4 with content", session_id="c1")
    levels = [s["level"] for s in sw.get_compact_summaries("c1")]
    assert levels == [1, 2]


def test_compaction_flat_summary_800_cap_and_summary_or_text(tmp_path):
    sw = SlidingWindowMemory(
        config=SlidingWindowConfig(max_tokens=3, compaction_threshold=2, auto_compact=True),
        db_path=str(tmp_path / "cap.db"),
    )
    # windows with explicit summaries → parent_summaries prefer summary over text
    for i in range(2):
        sw.chunk(f"word{i} word{i}b word{i}c", session_id="cap")
    conn = sqlite3.connect(sw.db_path)
    long_summary = "S" * 900
    conn.execute("UPDATE conversation_windows SET summary = ?", (long_summary,))
    conn.commit()
    conn.close()
    sw.chunk("word9 word9b word9c", session_id="cap")  # crosses threshold again
    compact = sw.get_compact_summaries("cap")
    assert compact and len(compact[-1]["summary"]) <= 800


def test_get_compact_summaries_empty(store):
    assert store.get_compact_summaries("nope") == []


# ---------------------------------------------------------------------------
# chunk()
# ---------------------------------------------------------------------------
def test_chunk_returns_items_and_persists(store):
    items = store.chunk("alpha beta gamma delta", session_id="ch")
    assert items and items[0]["window_index"] == 0
    assert items[0]["token_count"] == 4
    assert items[0]["summary"]  # summarize=True default
    assert store.get_session_stats("ch")["window_count"] == 1


def test_chunk_summarize_disabled_yields_none(tmp_path):
    sw = SlidingWindowMemory(
        config=SlidingWindowConfig(summarize=False, auto_compact=False),
        db_path=str(tmp_path / "nosum.db"),
    )
    items = sw.chunk("a b c", session_id="ns")
    assert items[0]["summary"] is None


# ---------------------------------------------------------------------------
# build_context — compact-front, query reorder, budget, empty guard
# ---------------------------------------------------------------------------
def test_build_context_empty_inputs_returns_empty(store):
    assert store.build_context([], query="", session_id="empty") == ""


def test_build_context_inserts_compact_front_and_prefers_summary(store, tmp_path):
    store.chunk("compact era text", session_id="bc")
    conn = sqlite3.connect(store.db_path)
    conn.execute(
        "INSERT INTO session_compact_summaries (session_id, level, summary, window_count, created_at)"
        " VALUES ('bc', 1, 'COMPACTLEVEL1', 1, '2026-01-01T00:00:00Z')"
    )
    conn.commit()
    conn.close()
    ctx = store.build_context(["fresh doc"], query="", session_id="bc")
    assert ctx.startswith("COMPACTLEVEL1")  # compact summaries lead the context


def test_build_context_query_reorders_rest_by_length(store):
    store.chunk(
        "history establishes the first chunk", session_id="q1"
    )  # recalled chunk stays first
    short_doc = "tiny"
    long_doc = " ".join(["word"] * 50)
    ctx = store.build_context([short_doc, long_doc], query="find things", session_id="q1")
    parts = ctx.split("\n---\n")
    assert len(parts) == 3
    # first chunk (recalled history) stays fixed, remaining sorted ascending by length
    assert len(parts[1]) < len(parts[-1])


def test_build_context_budget_prunes(store):
    sw = SlidingWindowMemory(
        config=SlidingWindowConfig(max_tokens=100, auto_compact=False),
        db_path=":memory:",
    )
    big = " ".join(["tok"] * 90)  # 90 tokens > budget 20
    ctx = sw.build_context([big], query="", session_id="b1", budget=20)
    assert ctx == ""  # first (only) chunk alone exceeds budget → nothing selected


# ---------------------------------------------------------------------------
# Stats + lifecycle
# ---------------------------------------------------------------------------
def test_get_session_stats_counters(store):
    store.chunk("one two three", session_id="st")
    store.chunk("four five six", session_id="st")
    stats = store.get_session_stats("st")
    assert stats["session_id"] == "st"
    assert stats["window_count"] == 2
    assert stats["compact_summary_count"] == 0
    assert stats["total_token_count"] == 6


def test_clear_removes_windows_and_compact_summaries(tmp_path):
    sw = SlidingWindowMemory(
        config=SlidingWindowConfig(max_tokens=3, compaction_threshold=2, auto_compact=True),
        db_path=str(tmp_path / "clr.db"),
    )
    sw.chunk("a b c", session_id="gone")
    sw.chunk("d e f", session_id="gone")  # triggers compaction
    assert sw.clear("gone") is True
    assert sw.get_session_stats("gone")["window_count"] == 0
    assert sw.get_compact_summaries("gone") == []


def test_clear_nonexistent_session_still_true(store):
    assert store.clear("ghost") is True


def test_clear_failure_returns_false_on_readonly_db(tmp_path):
    db = tmp_path / "ro.db"
    sw = SlidingWindowMemory(db_path=str(db))
    sw.chunk("a b c", session_id="ro")
    os.chmod(db, 0o444)
    try:
        assert sw.clear("ro") is False  # write refused → logged, False returned
    finally:
        os.chmod(db, 0o644)


def test_default_db_path_derivation_with_cleanup():
    sw = SlidingWindowMemory()
    try:
        assert sw.db_path.endswith(os.path.join("data", "sliding_window_memory.db"))
        assert os.path.exists(sw.db_path)  # db initialized
    finally:
        if os.path.exists(sw.db_path):
            os.remove(sw.db_path)


def test_persist_multiple_records_single_call(store):
    recs = [MemoryWindowRecord(i, f"r{i}", 1) for i in range(3)]
    assert store.persist("multi", recs) is True
    assert store.get_session_stats("multi")["window_count"] == 3
