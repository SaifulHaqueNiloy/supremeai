"""
Tests for backend/services/memory_service.py (critical-tier coverage ramp).

CascadeMemoryService has THREE selectable backends, each covered here:
  1. pooled Postgres (pooled_pg fakes — never a real DB),
  2. local SQLite file (real sqlite3 against tmp_path),
  3. degraded in-process InMemoryRing (production DB-loss policy, P0).

Also covered: the public async API (save_memory / recall_memories /
get+set_semantic_cache / summarize_and_save_session), the Supabase helper,
get_embedding, hash_vectorize and the lazy singleton wrapper.

No test touches a real Postgres/Supabase instance: every external seam
(pooled_pg, sqlite_fallback_allowed, embed_for_pgvector, supabase client,
LLM gateway) is faked at the boundary memory_service actually imports.
"""

import json
import sqlite3
import sys
import types
from types import SimpleNamespace

import pytest

import core.persistence.pooled_pg as pgmod
import services.memory_service as ms

# ═══════════════════════════════════════════════════════════════════════
# Fakes
# ═══════════════════════════════════════════════════════════════════════


class FakePooledPg:
    """Scriptable stand-in for the pooled_pg module.

    query_results is a queue: each entry is either a list of dict rows
    (returned) or an Exception instance (raised) — consumed per call.
    """

    def __init__(self):
        self.ddl_calls: list[str] = []
        self.execute_calls: list[tuple] = []
        self.query_calls: list[tuple] = []
        self.query_results: list = []
        self.execute_error: Exception | None = None
        self.ddl_error: Exception | None = None

    def is_available(self) -> bool:
        return True

    def execute_ddl(self, sql, params=()):
        self.ddl_calls.append(sql)
        if self.ddl_error is not None:
            raise self.ddl_error

    def execute(self, sql, params=()):
        self.execute_calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def query_dicts(self, sql, params=()):
        self.query_calls.append((sql, params))
        if not self.query_results:
            return []
        item = self.query_results.pop(0)
        if isinstance(item, Exception):
            raise item
        return list(item)


def _pg_row(summary="s", embedding="[]", session="sess1", user="u1", score=None):
    row = {
        "id": "row-1",
        "user_id": user,
        "session_id": session,
        "agent_type": "main",
        "task_type": "general",
        "summary": summary,
        "embedding": embedding,
        "metadata": {"k": "v"},
        "created_at": "2026-09-14T00:00:00Z",
    }
    if score is not None:
        row["score"] = score
    return row


@pytest.fixture
def fake_pg(monkeypatch):
    fake = FakePooledPg()
    monkeypatch.setattr(pgmod, "is_available", fake.is_available)
    monkeypatch.setattr(pgmod, "execute_ddl", fake.execute_ddl)
    monkeypatch.setattr(pgmod, "execute", fake.execute)
    monkeypatch.setattr(pgmod, "query_dicts", fake.query_dicts)
    return fake


@pytest.fixture
def pg_service(fake_pg):
    return ms.CascadeMemoryService()


@pytest.fixture
def sqlite_service(tmp_path):
    """Real SQLite backend in a temp dir (never the repo's data/memory.db)."""
    return ms.CascadeMemoryService(db_path=str(tmp_path / "memory-test.db"))


@pytest.fixture
def degraded_service(monkeypatch):
    """Production DB-loss policy: no Postgres, SQLite fallback refused."""
    monkeypatch.setattr(pgmod, "is_available", lambda: False)
    monkeypatch.setattr(ms, "sqlite_fallback_allowed", lambda feature: False)
    return ms.CascadeMemoryService()


@pytest.fixture
def fake_embed(monkeypatch):
    """Deterministic in-process embedding (hash trick, no network)."""
    monkeypatch.setattr(
        "core.embeddings.embed_for_pgvector",
        lambda text, pg_dim=384: ms.hash_vectorize(text, size=pg_dim),
    )


class FakeSupabase:
    """Stand-in for the supabase-py sync client used by save/recall."""

    def __init__(self, insert_data=None, insert_error=None, rpc_data=None, rpc_error=None):
        self.insert_data = insert_data
        self.insert_error = insert_error
        self.rpc_data = rpc_data
        self.rpc_error = rpc_error
        self.inserted: list[tuple] = []
        self.rpc_calls: list[tuple] = []
        self._op = "insert"
        self._table = None

    def table(self, name):
        self._table = name
        self._op = "insert"
        return self

    def insert(self, record):
        self.inserted.append((self._table, record))
        return self

    def rpc(self, name, params):
        self.rpc_calls.append((name, params))
        self._op = "rpc"
        return self

    def execute(self):
        if self._op == "insert":
            if self.insert_error is not None:
                raise self.insert_error
            return SimpleNamespace(data=self.insert_data)
        if self.rpc_error is not None:
            raise self.rpc_error
        return SimpleNamespace(data=self.rpc_data)


class FakeCascade:
    """Records cascade-store calls made by the public async API."""

    def __init__(self):
        self.stored: list[dict] = []
        self.queried: list[dict] = []
        self.store_error: Exception | None = None
        self.query_result: list = []

    def store_memory(self, **kwargs):
        self.stored.append(kwargs)
        if self.store_error is not None:
            raise self.store_error

    def query_context(self, prompt, **kwargs):
        self.queried.append({"prompt": prompt, **kwargs})
        return self.query_result


@pytest.fixture
def fake_cascade(monkeypatch):
    """Replace the module-level lazy singleton with a recorder."""
    fake = FakeCascade()
    monkeypatch.setattr(ms, "memory_service", fake)
    return fake


# ═══════════════════════════════════════════════════════════════════════
# hash_vectorize (pure function)
# ═══════════════════════════════════════════════════════════════════════


def test_hash_vectorize_default_size():
    vec = ms.hash_vectorize("hello world of embeddings")
    assert len(vec) == 384
    assert pytest.approx(sum(x * x for x in vec), abs=1e-9) == 1.0


def test_hash_vectorize_empty_text_returns_unit_vector():
    vec = ms.hash_vectorize("")
    assert vec[0] == 1.0
    assert all(x == 0.0 for x in vec[1:])


def test_hash_vectorize_only_short_words_returns_unit_vector():
    # Words of length <= 1 are filtered out -> same empty path as "".
    vec = ms.hash_vectorize("a b c")
    assert vec[0] == 1.0


def test_hash_vectorize_custom_size():
    vec = ms.hash_vectorize("some meaningful words here", size=64)
    assert len(vec) == 64
    assert pytest.approx(sum(x * x for x in vec), abs=1e-9) == 1.0


def test_hash_vectorize_deterministic_within_process():
    assert ms.hash_vectorize("stable input") == ms.hash_vectorize("stable input")


# ═══════════════════════════════════════════════════════════════════════
# CascadeMemoryService — backend selection in __init__
# ═══════════════════════════════════════════════════════════════════════


def test_pg_backend_selected_when_pool_available(fake_pg):
    svc = ms.CascadeMemoryService()
    assert svc._use_pg is True
    assert svc.db_path is None
    assert any("CREATE TABLE IF NOT EXISTS ai_memory" in sql for sql in fake_pg.ddl_calls)


def test_pg_ddl_failure_falls_back(fake_pg, monkeypatch):
    fake_pg.ddl_error = RuntimeError("writer pool down")
    monkeypatch.setattr(ms, "sqlite_fallback_allowed", lambda feature: False)
    svc = ms.CascadeMemoryService()
    assert svc._use_pg is False
    assert svc._degraded_memory is True


def test_sqlite_backend_with_explicit_path(sqlite_service):
    assert sqlite_service._use_pg is False
    assert sqlite_service._degraded_memory is False
    assert sqlite_service.db_path.endswith("memory-test.db")
    # Schema table exists
    with sqlite3.connect(sqlite_service.db_path) as conn:
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
    assert "file_memories" in tables


def test_degraded_mode_when_sqlite_refused(degraded_service):
    assert degraded_service._use_pg is False
    assert degraded_service._degraded_memory is True
    assert degraded_service._memory_rows is not None
    assert degraded_service.db_path is None


# ═══════════════════════════════════════════════════════════════════════
# _embed / _parse_code_structure / _cosine_similarity
# ═══════════════════════════════════════════════════════════════════════


def test_embed_uses_core_embedding(sqlite_service, monkeypatch):
    monkeypatch.setattr(
        "core.embeddings.embed_for_pgvector", lambda text, pg_dim=384: [0.5] * pg_dim
    )
    assert sqlite_service._embed("hello") == [0.5] * 384


def test_embed_falls_back_on_failure(sqlite_service, monkeypatch):
    def boom(text, pg_dim=384):
        raise RuntimeError("provider down")

    monkeypatch.setattr("core.embeddings.embed_for_pgvector", boom)
    vec = sqlite_service._embed("hello")
    assert len(vec) == 384
    assert pytest.approx(sum(x * x for x in vec), abs=1e-9) == 1.0


def test_parse_code_structure_python_file(sqlite_service):
    code = (
        "class Analyzer:\n"
        '    """Analyzes data."""\n'
        "    def run(self):\n"
        '        """Runs it."""\n'
        "        pass\n"
        "\n"
        "def standalone():\n"
        '    """Standalone helper."""\n'
        "    return 1\n"
    )
    parsed = sqlite_service._parse_code_structure("mod.py", code)
    structure = json.loads(parsed["structure"])
    assert structure["classes"][0]["name"] == "Analyzer"
    assert structure["classes"][0]["methods"][0]["name"] == "run"
    assert structure["functions"][0]["name"] == "standalone"
    assert "Class: Analyzer" in parsed["summary"]
    assert "Function: standalone" in parsed["summary"]


def test_parse_code_structure_non_python_file(sqlite_service):
    parsed = sqlite_service._parse_code_structure("notes.txt", "line one\nline two\n")
    assert json.loads(parsed["structure"]) == {"lines": 2}
    assert "Lines: 2" in parsed["summary"]


def test_parse_code_structure_syntax_error_falls_back(sqlite_service):
    parsed = sqlite_service._parse_code_structure("broken.py", "def broken(:\n")
    structure = json.loads(parsed["structure"])
    assert "error" in structure
    assert "AST parsing error" in parsed["summary"]


def test_cosine_similarity_identical_and_orthogonal(sqlite_service):
    a = [1.0, 0.0, 0.0]
    assert pytest.approx(sqlite_service._cosine_similarity(a, a), abs=1e-9) == 1.0
    assert pytest.approx(sqlite_service._cosine_similarity(a, [0.0, 1.0, 0.0]), abs=1e-9) == 0.0


def test_cosine_similarity_zero_vector_is_zero(sqlite_service):
    assert sqlite_service._cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
    assert sqlite_service._cosine_similarity([1.0, 0.0], [0.0, 0.0]) == 0.0


# ═══════════════════════════════════════════════════════════════════════
# store / retrieve / delete — SQLite (real round-trip)
# ═══════════════════════════════════════════════════════════════════════


def test_sqlite_store_retrieve_roundtrip(sqlite_service, fake_embed):
    sqlite_service.store_memory("s1", "content-1", "alpha summary", "{}")
    sqlite_service.store_memory("s2", "content-2", "beta report", "{}")
    rows = sqlite_service.retrieve_memories()
    assert len(rows) == 2
    by_path = {r["file_path"]: r for r in rows}
    assert by_path["s1"]["content"] == "content-1"
    assert by_path["s2"]["summary"] == "beta report"


def test_sqlite_store_upserts_on_same_path(sqlite_service, fake_embed):
    sqlite_service.store_memory("s1", "v1", "summary v1", "{}")
    sqlite_service.store_memory("s1", "v2", "summary v2", "{}")
    rows = sqlite_service.retrieve_memories()
    assert len(rows) == 1
    assert rows[0]["content"] == "v2"


def test_sqlite_delete_memory(sqlite_service, fake_embed):
    sqlite_service.store_memory("s1", "c", "sum", "{}")
    sqlite_service.delete_memory("s1")
    assert sqlite_service.retrieve_memories() == []


def test_sqlite_clear_user_memories(sqlite_service, fake_embed):
    sqlite_service.store_memory("u1/a", "c", "sum", "{}")
    sqlite_service.store_memory("u1/b", "c", "sum", "{}")
    sqlite_service.store_memory("u2/c", "c", "sum", "{}")
    sqlite_service.clear_user_memories("u1")
    remaining = {r["file_path"] for r in sqlite_service.retrieve_memories()}
    assert remaining == {"u2/c"}


# ═══════════════════════════════════════════════════════════════════════
# store / retrieve / delete — degraded in-process ring
# ═══════════════════════════════════════════════════════════════════════


def test_degraded_store_upsert_and_retrieve(degraded_service, fake_embed):
    degraded_service.store_memory("u1/task", "c1", "alpha", "{}")
    degraded_service.store_memory("u1/task", "c2", "alpha2", "{}")
    degraded_service.store_memory("u1/other", "c3", "beta", "{}")
    rows = degraded_service.retrieve_memories()
    assert len(rows) == 2
    by_path = {r["file_path"]: r for r in rows}
    assert by_path["u1/task"]["content"] == "c2"


def test_degraded_delete_and_clear(degraded_service, fake_embed):
    degraded_service.store_memory("u1/a", "c", "sum", "{}")
    degraded_service.store_memory("u1/b", "c", "sum", "{}")
    degraded_service.store_memory("u2/c", "c", "sum", "{}")
    degraded_service.delete_memory("u1/a")
    degraded_service.clear_user_memories("u1")
    remaining = {r["file_path"] for r in degraded_service.retrieve_memories()}
    assert remaining == {"u2/c"}


def test_degraded_query_context_skips_rows_without_embedding(degraded_service, fake_embed):
    degraded_service.store_memory("u1/task", "c", "alpha summary", "{}")
    degraded_service._memory_rows.append({"file_path": "broken", "embedding": None})
    results = degraded_service.query_context("alpha summary", top_k=3)
    assert len(results) == 1
    assert results[0]["file"] == "u1/task"
    assert results[0]["score"] > 0.5


def test_degraded_query_context_survives_corrupt_embedding_json(degraded_service, fake_embed):
    degraded_service.store_memory("u1/task", "c", "alpha summary", "{}")
    degraded_service._memory_rows.append(
        {"file_path": "corrupt", "embedding": "not-json", "summary": "x", "structure": "{}"}
    )
    results = degraded_service.query_context("alpha summary", top_k=3)  # warning path, no raise
    assert [r["file"] for r in results] == ["u1/task"]


# ═══════════════════════════════════════════════════════════════════════
# store / retrieve / delete — Postgres path
# ═══════════════════════════════════════════════════════════════════════


def test_pg_store_memory_inserts(pg_service, fake_pg, fake_embed):
    pg_service.store_memory(
        "sess1", "content", "summary", "struct", session_id="sess1", user_id="u1"
    )
    assert len(fake_pg.execute_calls) == 1
    sql, params = fake_pg.execute_calls[0]
    assert "INSERT INTO ai_memory" in sql
    # user_id, session_id, agent_type, task_type, summary, embedding, metadata
    assert params[0] == "u1"
    assert params[1] == "sess1"
    assert params[3] == "general"
    assert params[4] == "summary"
    assert json.loads(params[5]) == ms.hash_vectorize("summary")
    assert json.loads(params[6]) == {}


def test_pg_store_memory_write_failure_is_swallowed(pg_service, fake_pg):
    fake_pg.execute_error = RuntimeError("pg write failed")
    pg_service.store_memory("sess1", "content", "summary", "struct")  # must not raise


def test_pg_retrieve_memories_filter_combinations(pg_service, fake_pg):
    # One queued result per retrieve call (4 combos below).
    fake_pg.query_results = [[_pg_row()]] * 4
    assert len(pg_service.retrieve_memories(session_id="sess1", user_id="u1")) == 1
    assert len(pg_service.retrieve_memories(session_id="sess1")) == 1
    assert len(pg_service.retrieve_memories(user_id="u1")) == 1
    assert len(pg_service.retrieve_memories()) == 1
    assert len(fake_pg.query_calls) == 4
    sqls = [sql for sql, _ in fake_pg.query_calls]
    assert "session_id = %s AND user_id = %s" in sqls[0]
    assert "WHERE session_id = %s" in sqls[1]
    assert "WHERE user_id = %s" in sqls[2]
    assert "WHERE" not in sqls[3]


def test_pg_retrieve_memories_read_failure_returns_empty(pg_service, fake_pg):
    fake_pg.query_results = [RuntimeError("pg read failed")]
    assert pg_service.retrieve_memories() == []


def test_pg_delete_and_clear_user(pg_service, fake_pg):
    pg_service.delete_memory("sess1")
    pg_service.clear_user_memories("u1")
    assert len(fake_pg.execute_calls) == 2
    assert "DELETE FROM ai_memory WHERE session_id" in fake_pg.execute_calls[0][0]
    assert "DELETE FROM ai_memory WHERE user_id" in fake_pg.execute_calls[1][0]
    assert fake_pg.execute_calls[1][1] == ("u1",)


def test_pg_delete_failure_is_swallowed(pg_service, fake_pg):
    fake_pg.execute_error = RuntimeError("pg delete failed")
    pg_service.delete_memory("sess1")  # must not raise


def test_pg_clear_user_failure_is_swallowed(pg_service, fake_pg):
    fake_pg.execute_error = RuntimeError("pg clear failed")
    pg_service.clear_user_memories("u1")  # must not raise


# ═══════════════════════════════════════════════════════════════════════
# query_context — pgvector RPC path + in-Python cosine fallback
# ═══════════════════════════════════════════════════════════════════════


def test_query_context_prefers_pgvector_rpc(pg_service, fake_pg, fake_embed):
    pg_service._pgvector_rpc = True
    fake_pg.query_results.append([_pg_row(score=0.42)])
    results = pg_service.query_context("prompt", top_k=2)
    assert len(results) == 1
    assert results[0]["score"] == pytest.approx(0.42)
    assert results[0]["metadata"] == {"k": "v"}
    assert "match_ai_memories" in fake_pg.query_calls[0][0]


def test_query_context_rpc_results_sorted_and_capped(pg_service, fake_pg, fake_embed):
    pg_service._pgvector_rpc = True
    fake_pg.query_results.append(
        [
            _pg_row(score=0.1, session="a"),
            _pg_row(score=0.9, session="b"),
            _pg_row(score=0.5, session="c"),
        ]
    )
    results = pg_service.query_context("prompt", top_k=2)
    assert [r["session_id"] for r in results] == ["b", "c"]


def test_query_context_rpc_failure_falls_back_to_cosine(pg_service, fake_pg, fake_embed):
    pg_service._pgvector_rpc = True
    vector = json.dumps(ms.hash_vectorize("alpha summary"))
    fake_pg.query_results = [RuntimeError("rpc exploded"), [_pg_row(embedding=vector)]]
    results = pg_service.query_context("alpha summary", top_k=3)
    assert len(results) == 1
    assert results[0]["score"] > 0.99


def test_query_context_pg_cosine_skips_corrupt_embedding(pg_service, fake_pg, fake_embed):
    pg_service._pgvector_rpc = False
    good = json.dumps(ms.hash_vectorize("alpha summary"))
    fake_pg.query_results.append(
        [_pg_row(embedding="not-json", session="bad"), _pg_row(embedding=good, session="ok")]
    )
    results = pg_service.query_context("alpha summary", top_k=5)
    assert [r["session_id"] for r in results] == ["ok"]


def test_query_context_pg_cosine_filter_combinations(pg_service, fake_pg, fake_embed):
    pg_service._pgvector_rpc = False
    good = json.dumps(ms.hash_vectorize("alpha summary"))
    fake_pg.query_results = [[_pg_row(embedding=good)]] * 4
    assert (
        len(pg_service.query_context("alpha summary", top_k=1, session_id="sess1", user_id="u1"))
        == 1
    )
    assert len(pg_service.query_context("alpha summary", top_k=1, session_id="sess1")) == 1
    assert len(pg_service.query_context("alpha summary", top_k=1, user_id="u1")) == 1
    assert len(pg_service.query_context("alpha summary", top_k=1)) == 1
    sqls = [sql for sql, _ in fake_pg.query_calls]
    assert "ORDER BY created_at DESC LIMIT 2000" in sqls[0]
    assert "session_id = %s AND user_id = %s" in sqls[0]
    assert "WHERE session_id = %s" in sqls[1]
    assert "WHERE user_id = %s" in sqls[2]


def test_query_context_pg_read_failure_returns_empty(pg_service, fake_pg, fake_embed):
    pg_service._pgvector_rpc = False
    fake_pg.query_results = [RuntimeError("pg down")]
    assert pg_service.query_context("prompt") == []


def test_query_context_sqlite_ranks_identical_text_first(sqlite_service, fake_embed):
    sqlite_service.store_memory("a", "c", "alpha summary about cats", "{}")
    sqlite_service.store_memory("b", "c", "completely unrelated dogs report", "{}")
    results = sqlite_service.query_context("alpha summary about cats", top_k=2)
    assert results[0]["file"] == "a"
    assert results[0]["score"] == pytest.approx(1.0, abs=1e-6)
    assert results[0]["structure"] == {}


def test_query_context_sqlite_skips_corrupt_embedding_row(sqlite_service, fake_embed):
    sqlite_service.store_memory("a", "c", "alpha summary", "{}")
    with sqlite3.connect(sqlite_service.db_path) as conn:
        conn.execute(
            "INSERT INTO file_memories (file_path, content, summary, structure, embedding) VALUES (?, ?, ?, ?, ?)",
            ("corrupt", "c", "corrupt summary", "{}", "not-json"),
        )
        conn.commit()
    results = sqlite_service.query_context("alpha summary", top_k=5)
    assert [r["file"] for r in results] == ["a"]


# ═══════════════════════════════════════════════════════════════════════
# pgvector RPC probe
# ═══════════════════════════════════════════════════════════════════════


def test_pgvector_probe_positive_is_cached(pg_service, fake_pg):
    fake_pg.query_results.append([{"pgvector_ready": True}])
    assert pg_service._pgvector_rpc_available() is True
    fake_pg.query_results.append([{"pgvector_ready": False}])
    assert pg_service._pgvector_rpc_available() is True  # cached, second query unconsumed
    assert len(fake_pg.query_calls) == 1


def test_pgvector_probe_negative(pg_service, fake_pg):
    fake_pg.query_results.append([{"pgvector_ready": False}])
    assert pg_service._pgvector_rpc_available() is False


def test_pgvector_probe_failure_is_false_and_cached(pg_service, fake_pg):
    fake_pg.query_results = [RuntimeError("no pg")]
    assert pg_service._pgvector_rpc_available() is False
    assert pg_service._pgvector_rpc_available() is False
    assert len(fake_pg.query_calls) == 1


def test_query_via_rpc_shapes_rows(pg_service, fake_pg):
    fake_pg.query_results.append(
        [
            {
                "id": 1,
                "summary": "s",
                "metadata": None,
                "score": None,
                "session_id": "x",
                "user_id": "u",
            }
        ]
    )
    rows = pg_service._query_via_pgvector_rpc([0.1, 0.2], top_k=1, session_id="x", user_id="u")
    assert rows[0]["embedding"] is None  # shape parity key, no vector over the wire
    assert rows[0]["metadata"] == {}
    assert rows[0]["score"] == 0.0
    sql, params = fake_pg.query_calls[0]
    assert params[0].startswith("[") and params[1] == 0.0 and params[2] == 1


# ═══════════════════════════════════════════════════════════════════════
# chunk_and_embed + backward-compatible aliases
# ═══════════════════════════════════════════════════════════════════════


def test_chunk_and_embed_returns_vector_and_stores(sqlite_service, fake_embed):
    code = "def helper():\n    return 1\n"
    out = sqlite_service.chunk_and_embed("m.py", code)
    assert len(out) == 1
    assert out[0]["file"] == "m.py"
    assert len(out[0]["vector"]) == 384
    assert len(sqlite_service.retrieve_memories()) == 1


def test_alias_store_and_get_memories(sqlite_service, fake_embed):
    sqlite_service.store("u1", "agentA", "hello content", {"summary": "S", "structure": "{}"})
    rows = sqlite_service.get_memories("u1")
    assert rows[0]["file_path"] == "u1/agentA"
    assert rows[0]["summary"] == "S"


def test_alias_search_semantic_and_recent(sqlite_service, fake_embed):
    sqlite_service.store("u1", "a", "c", {"summary": "alpha search target", "structure": "{}"})
    hits = sqlite_service.search_memories("u1", "alpha search target")
    assert hits[0]["summary"] == "alpha search target"
    assert sqlite_service.semantic_search("alpha search target", limit=3)
    recent = sqlite_service.get_recent_interactions("u1", limit=1)
    assert len(recent) <= 1


def test_alias_delete_and_context_window(sqlite_service, fake_embed):
    sqlite_service.store("u1", "a", "c", {"summary": "sum", "structure": "{}"})
    sqlite_service.delete("u1/a")
    assert sqlite_service.retrieve_memories() == []
    sqlite_service.update_context_window(
        "u1", [{"role": "user", "content": "m1"}, {"role": "assistant", "content": "m2"}]
    )
    rows = sqlite_service.retrieve_memories()
    # Both messages share the "u1/context" key -> last write wins (upsert).
    assert len(rows) == 1
    assert rows[0]["file_path"] == "u1/context"
    assert rows[0]["content"] == "m2"


def test_get_context_window_alias(sqlite_service, fake_embed):
    sqlite_service.store("u1", "a", "c", {"summary": "find me please", "structure": "{}"})
    hits = sqlite_service.get_context_window("u1", "a", limit=3)
    assert isinstance(hits, list)


# ═══════════════════════════════════════════════════════════════════════
# LazyCascadeMemoryService + module singleton
# ═══════════════════════════════════════════════════════════════════════


def test_lazy_wrapper_defers_construction_and_delegates(monkeypatch):
    created = []

    class FakeSvc:
        def ping(self):
            return "pong"

    def factory():
        created.append(1)
        return FakeSvc()

    monkeypatch.setattr(ms, "CascadeMemoryService", factory)
    lazy = ms.LazyCascadeMemoryService()
    assert created == []  # nothing built yet
    assert lazy.ping() == "pong"
    assert lazy.ping() == "pong"
    assert len(created) == 1  # singleton per wrapper


def test_module_singleton_is_lazy_wrapper():
    assert isinstance(ms.memory_service, ms.LazyCascadeMemoryService)


# ═══════════════════════════════════════════════════════════════════════
# get_embedding / _get_supabase
# ═══════════════════════════════════════════════════════════════════════


def test_get_embedding_success(monkeypatch):
    monkeypatch.setattr(
        "core.embeddings.embed_for_pgvector", lambda text, pg_dim=1536: [0.1] * pg_dim
    )
    assert ms.get_embedding("hello") == [0.1] * 1536


def test_get_embedding_failure_falls_back(monkeypatch):
    def boom(text, pg_dim=1536):
        raise RuntimeError("down")

    monkeypatch.setattr("core.embeddings.embed_for_pgvector", boom)
    vec = ms.get_embedding("hello")
    assert len(vec) == 1536
    assert pytest.approx(sum(x * x for x in vec), abs=1e-9) == 1.0


def test_get_supabase_returns_none_without_url(monkeypatch):
    monkeypatch.setattr(ms, "_supabase_client", None)
    monkeypatch.setattr(ms, "settings", SimpleNamespace(supabase_url=None))
    assert ms._get_supabase() is None


def test_get_supabase_returns_none_without_key(monkeypatch):
    monkeypatch.setattr(ms, "_supabase_client", None)
    monkeypatch.setattr(ms, "settings", SimpleNamespace(supabase_url="https://supabase.example"))
    for var in ("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY", "SUPABASE_ANON_KEY"):
        monkeypatch.delenv(var, raising=False)
    assert ms._get_supabase() is None


def test_get_supabase_creates_and_caches_client(monkeypatch):
    sentinel = object()
    created = []

    fake_module = types.ModuleType("supabase")
    fake_module.create_client = lambda url, key: created.append((url, key)) or sentinel
    monkeypatch.setitem(sys.modules, "supabase", fake_module)
    monkeypatch.setattr(ms, "_supabase_client", None)
    monkeypatch.setattr(ms, "settings", SimpleNamespace(supabase_url="https://supabase.example"))
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-key")

    assert ms._get_supabase() is sentinel
    assert ms._get_supabase() is sentinel  # cached
    assert created == [("https://supabase.example", "service-key")]


def test_get_supabase_create_failure_returns_none(monkeypatch):
    fake_module = types.ModuleType("supabase")

    def boom(url, key):
        raise RuntimeError("bad config")

    fake_module.create_client = boom
    monkeypatch.setitem(sys.modules, "supabase", fake_module)
    monkeypatch.setattr(ms, "_supabase_client", None)
    monkeypatch.setattr(ms, "settings", SimpleNamespace(supabase_url="https://supabase.example"))
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-key")
    assert ms._get_supabase() is None


# ═══════════════════════════════════════════════════════════════════════
# save_memory (async public API)
# ═══════════════════════════════════════════════════════════════════════


async def test_save_memory_supabase_success(monkeypatch, fake_cascade):
    sb = FakeSupabase(insert_data=[{"id": "mem-1"}])
    monkeypatch.setattr(ms, "_get_supabase", lambda: sb)
    monkeypatch.setattr(ms, "get_embedding", lambda text: [0.1] * 1536)
    result = await ms.save_memory(session_id="s1", summary="sum", user_id="u1")
    assert result == {"success": True, "id": "mem-1"}
    table, record = sb.inserted[0]
    assert table == "ai_memory"
    assert record["session_id"] == "s1"
    assert record["summary"] == "sum"
    assert record["user_id"] == "u1"
    assert fake_cascade.stored == []  # no cascade fallback needed


async def test_save_memory_empty_insert_falls_back_to_cascade(monkeypatch, fake_cascade):
    sb = FakeSupabase(insert_data=[])
    monkeypatch.setattr(ms, "_get_supabase", lambda: sb)
    monkeypatch.setattr(ms, "get_embedding", lambda text: [0.1] * 1536)
    result = await ms.save_memory(session_id="s1", summary="sum", task_type="general")
    assert result == {"success": True, "id": "s1", "backend": "cascade"}
    stored = fake_cascade.stored[0]
    assert stored["file_path"] == "s1:general"
    assert stored["session_id"] == "s1"


async def test_save_memory_supabase_error_falls_back_to_cascade(monkeypatch, fake_cascade):
    sb = FakeSupabase(insert_error=RuntimeError("supabase 500"))
    monkeypatch.setattr(ms, "_get_supabase", lambda: sb)
    monkeypatch.setattr(ms, "get_embedding", lambda text: [0.1] * 1536)
    result = await ms.save_memory(session_id="s2", summary="sum")
    assert result["success"] is True
    assert result["backend"] == "cascade"
    assert len(fake_cascade.stored) == 1


async def test_save_memory_without_supabase_uses_cascade(monkeypatch, fake_cascade):
    monkeypatch.setattr(ms, "_get_supabase", lambda: None)
    result = await ms.save_memory(session_id="s3", summary="sum", agent_type="main")
    assert result == {"success": True, "id": "s3", "backend": "cascade"}
    assert fake_cascade.stored[0]["agent_type"] == "main"


async def test_save_memory_total_failure_reports_error(monkeypatch, fake_cascade):
    monkeypatch.setattr(ms, "_get_supabase", lambda: None)
    fake_cascade.store_error = RuntimeError("disk full")
    result = await ms.save_memory(session_id="s4", summary="sum")
    assert result["success"] is False
    assert "disk full" in result["error"]


# ═══════════════════════════════════════════════════════════════════════
# recall_memories (async public API)
# ═══════════════════════════════════════════════════════════════════════


async def test_recall_memories_supabase_rpc(monkeypatch, fake_cascade):
    sb = FakeSupabase(rpc_data=[{"id": 1, "summary": "match"}])
    monkeypatch.setattr(ms, "_get_supabase", lambda: sb)
    monkeypatch.setattr(ms, "get_embedding", lambda text: [0.2] * 1536)
    out = await ms.recall_memories(task_description="find me", limit=3, user_id="u1")
    assert out == [{"id": 1, "summary": "match"}]
    name, params = sb.rpc_calls[0]
    assert name == "match_ai_memory"
    assert params["match_count"] == 3
    assert params["p_user_id"] == "u1"
    assert fake_cascade.queried == []


async def test_recall_memories_rpc_error_falls_back_to_cascade(monkeypatch, fake_cascade):
    sb = FakeSupabase(rpc_error=RuntimeError("rpc down"))
    monkeypatch.setattr(ms, "_get_supabase", lambda: sb)
    fake_cascade.query_result = [{"file": "a", "score": 0.9}]
    out = await ms.recall_memories(task_description="find me")
    assert out == [{"file": "a", "score": 0.9}]
    assert fake_cascade.queried[0]["prompt"] == "find me"


async def test_recall_memories_without_supabase_uses_cascade(monkeypatch, fake_cascade):
    monkeypatch.setattr(ms, "_get_supabase", lambda: None)
    fake_cascade.query_result = [{"file": "b"}]
    out = await ms.recall_memories(task_description="q", user_id="u9")
    assert out == [{"file": "b"}]
    assert fake_cascade.queried[0]["user_id"] == "u9"


async def test_recall_memories_total_failure_returns_empty(monkeypatch, fake_cascade):
    monkeypatch.setattr(ms, "_get_supabase", lambda: None)
    monkeypatch.setattr(
        ms, "get_embedding", lambda text: (_ for _ in ()).throw(RuntimeError("embed down"))
    )
    assert await ms.recall_memories(task_description="q") == []


# ═══════════════════════════════════════════════════════════════════════
# semantic cache (get / set)
# ═══════════════════════════════════════════════════════════════════════


async def test_semantic_cache_hit(monkeypatch):
    async def fake_recall(**kwargs):
        return [{"task_type": "semantic_cache", "metadata": {"response": "CACHED"}}]

    monkeypatch.setattr(ms, "recall_memories", fake_recall)
    assert await ms.get_semantic_cache("prompt") == "CACHED"


async def test_semantic_cache_miss_wrong_task_type(monkeypatch):
    async def fake_recall(**kwargs):
        return [{"task_type": "general", "metadata": {"response": "R"}}]

    monkeypatch.setattr(ms, "recall_memories", fake_recall)
    assert await ms.get_semantic_cache("prompt") is None


async def test_semantic_cache_miss_without_response(monkeypatch):
    async def fake_recall(**kwargs):
        return [{"task_type": "semantic_cache", "metadata": {}}]

    monkeypatch.setattr(ms, "recall_memories", fake_recall)
    assert await ms.get_semantic_cache("prompt") is None


async def test_semantic_cache_lookup_failure_returns_none(monkeypatch):
    async def boom(**kwargs):
        raise RuntimeError("recall down")

    monkeypatch.setattr(ms, "recall_memories", boom)
    assert await ms.get_semantic_cache("prompt") is None


async def test_set_semantic_cache_stores_response(monkeypatch):
    captured = {}

    async def fake_save(**kwargs):
        captured.update(kwargs)
        return {"success": True}

    monkeypatch.setattr(ms, "save_memory", fake_save)
    await ms.set_semantic_cache("the prompt", "the response", session_id="sess")
    assert captured["session_id"] == "sess"
    assert captured["summary"] == "the prompt"
    assert captured["task_type"] == "semantic_cache"
    assert captured["agent_type"] == "system"
    assert captured["metadata"] == {"response": "the response"}


async def test_set_semantic_cache_failure_is_swallowed(monkeypatch):
    async def boom(**kwargs):
        raise RuntimeError("save down")

    monkeypatch.setattr(ms, "save_memory", boom)
    await ms.set_semantic_cache("p", "r")  # must not raise


# ═══════════════════════════════════════════════════════════════════════
# summarize_and_save_session
# ═══════════════════════════════════════════════════════════════════════


def _install_gateway_stub(monkeypatch, gateway):
    stub = types.ModuleType("core.llm.llm_gateway_with_learning")
    stub.get_llm_gateway = lambda: gateway
    monkeypatch.setitem(sys.modules, "core.llm.llm_gateway_with_learning", stub)


async def test_summarize_uses_llm_dict_response(monkeypatch):
    calls = {}

    class FakeGateway:
        async def acompletion(self, **kwargs):
            calls.update(kwargs)
            return {"text": "LLM SUMMARY"}

    _install_gateway_stub(monkeypatch, FakeGateway())
    saved = {}

    async def fake_save(**kwargs):
        saved.update(kwargs)
        return {"success": True, "id": "x"}

    monkeypatch.setattr(ms, "save_memory", fake_save)
    result = await ms.summarize_and_save_session(
        session_id="s1", messages=[{"role": "user", "content": "hello"}]
    )
    assert result == {"success": True, "id": "x"}
    assert saved["summary"] == "LLM SUMMARY"
    assert saved["metadata"] == {"message_count": 1}
    assert "user: hello" in calls["prompt"]


async def test_summarize_uses_choices_response(monkeypatch):
    class FakeGateway:
        async def acompletion(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="CHOICE SUMMARY"))]
            )

    _install_gateway_stub(monkeypatch, FakeGateway())
    saved = {}

    async def fake_save(**kwargs):
        saved.update(kwargs)
        return {"success": True}

    monkeypatch.setattr(ms, "save_memory", fake_save)
    await ms.summarize_and_save_session(
        session_id="s1", messages=[{"role": "user", "content": "hi"}]
    )
    assert saved["summary"] == "CHOICE SUMMARY"


async def test_summarize_without_gateway_uses_raw_text(monkeypatch):
    _install_gateway_stub(monkeypatch, None)
    saved = {}

    async def fake_save(**kwargs):
        saved.update(kwargs)
        return {"success": True}

    monkeypatch.setattr(ms, "save_memory", fake_save)
    await ms.summarize_and_save_session(
        session_id="s1", messages=[{"role": "user", "content": "raw line"}]
    )
    assert "user: raw line" in saved["summary"]


async def test_summarize_gateway_failure_uses_raw_text(monkeypatch):
    class FakeGateway:
        async def acompletion(self, **kwargs):
            raise RuntimeError("gateway down")

    _install_gateway_stub(monkeypatch, FakeGateway())
    saved = {}

    async def fake_save(**kwargs):
        saved.update(kwargs)
        return {"success": True}

    monkeypatch.setattr(ms, "save_memory", fake_save)
    await ms.summarize_and_save_session(
        session_id="s1", messages=[{"role": "user", "content": "kept"}]
    )
    assert "user: kept" in saved["summary"]


async def test_summarize_truncates_to_last_20_messages(monkeypatch):
    captured = {}

    class FakeGateway:
        async def acompletion(self, **kwargs):
            captured["prompt"] = kwargs["prompt"]
            return {"text": "S"}

    _install_gateway_stub(monkeypatch, FakeGateway())

    async def fake_save(**kwargs):
        return {"success": True}

    monkeypatch.setattr(ms, "save_memory", fake_save)
    messages = [{"role": "user", "content": f"message-{i}"} for i in range(25)]
    await ms.summarize_and_save_session(session_id="s1", messages=messages)
    assert "message-24" in captured["prompt"]  # last message present
    assert "message-4" not in captured["prompt"]  # 25-20=5 -> first four dropped
    assert "message-5" in captured["prompt"]  # boundary: 20th-from-last kept
