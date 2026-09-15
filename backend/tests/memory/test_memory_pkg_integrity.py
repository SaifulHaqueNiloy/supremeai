"""CI-collected coverage for the backend/memory/ package's small core modules.

বাংলা: memory/ প্যাকেজটি PR CI-র coverage measurement-এর বাইরে ছিল —
ci.yml-এর pytest invocation-এ --cov=memory ছিল না, আর
coverage_policy.yaml-এ memory/**-এর কোনো glob ছিল না (runs/**-এর মতোই
three-layer integrity gap)। এই ফাইল প্যাকেজের ছোট pure মডিউলগুলোর আসল
behavior যাচাই করে:

  - vector_store_config / summary_tree / sqlite_store : pure logic + SQLite CRUD
  - unified_db_manager : multi-store transaction coordinator (fake store inject করে —
    কোনো নেটওয়ার্ক/DB নেই), SQL-injection whitelist সহ
  - hierarchical_tree : in-package memory/test_hierarchical_tree.py-এর functional
    coverage-এর CI-collected twin (ওই ফাইলটি CI matrix কর্তৃক collect হয় না এবং
    repo-র `backend.` import prefix ব্যবহার করে; এখানে backend/ cwd idiom ব্যবহৃত)

mcp_server.py (1272L) ও বাকি store adapter-গুলোর ramp হলো documented follow-up।
"""

import pytest

from memory.hierarchical_tree import HierarchicalMemoryTree, MemoryNode
from memory.sqlite_store import SQLiteMemoryStore
from memory.summary_tree import SummaryTree
from memory.unified_db_manager import (
    _VALID_COLLECTION_PATTERN,
    SQLiteStore,
    UnifiedDBManager,
)
from memory.vector_store_config import VectorStoreConfig, get_vector_store_config

pytestmark = pytest.mark.memory


# ─────────────────────────────────────────────────────────────────────────────
# Fake stores for UnifiedDBManager — কোনো বাহ্যিক DB/vector backend লাগে না।
# ─────────────────────────────────────────────────────────────────────────────
class _FakeSQLite:
    def __init__(self, fail: bool = False):
        self.saved: list[tuple[str, str, dict]] = []
        self.records: dict[tuple[str, str], dict] = {}
        self.fail = fail

    async def save(self, collection: str, record_id: str, data: dict) -> None:
        if self.fail:
            raise RuntimeError("sqlite down")
        self.saved.append((collection, record_id, data))
        self.records[(collection, record_id)] = data

    async def get(self, collection: str, record_id: str):
        return self.records.get((collection, record_id))


class _FakeSupabase:
    def __init__(self):
        self.inserted: list[tuple[str, dict]] = []
        self.records: dict[str, dict[str, dict]] = {}

    async def insert(self, collection: str, record: dict) -> None:
        self.inserted.append((collection, record))
        self.records.setdefault(collection, {})[record["id"]] = record

    async def fetch_by_id(self, collection: str, record_id: str):
        return self.records.get(collection, {}).get(record_id)


class _FakePostgres:
    def __init__(self, fail: bool = False):
        self.queries: list[tuple[str, tuple]] = []
        self.fail = fail

    async def execute_query(self, query: str, *args) -> None:
        if self.fail:
            raise RuntimeError("pg down")
        self.queries.append((query, args))


class _FakeChroma:
    def __init__(self, fail: bool = False):
        self.docs: list[tuple[str, str, dict]] = []
        self.fail = fail

    async def add_document(self, document_id: str, text: str, metadata: dict) -> None:
        if self.fail:
            raise RuntimeError("chroma down")
        self.docs.append((document_id, text, metadata))


def _make_manager(sqlite=None, supabase=None, postgres=None, chroma=None) -> UnifiedDBManager:
    return UnifiedDBManager(
        supabase_store=supabase or _FakeSupabase(),
        sqlite_store=sqlite or _FakeSQLite(),
        chroma_store=chroma or _FakeChroma(),
        postgres_store=postgres or _FakePostgres(),
    )


class TestUnifiedDBManager:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_save_record_all_stores_succeed(self):
        sqlite, supa, pg, chroma = (
            _FakeSQLite(),
            _FakeSupabase(),
            _FakePostgres(),
            _FakeChroma(),
        )
        mgr = _make_manager(sqlite, supa, pg, chroma)

        results = await mgr.save_record(
            "notes_v2", "rec-1", {"title": "hello"}, text_content="hello world"
        )

        assert results == {"supabase": True, "sqlite": True, "chroma": True, "postgres": True}
        assert sqlite.saved == [("notes_v2", "rec-1", {"title": "hello"})]
        assert supa.inserted[0][1]["id"] == "rec-1"
        assert len(pg.queries) == 1 and "notes_v2" in pg.queries[0][0]
        assert chroma.docs[0][0] == "rec-1"
        assert chroma.docs[0][2]["collection"] == "notes_v2"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_save_record_without_text_skips_chroma(self):
        chroma = _FakeChroma()
        mgr = _make_manager(chroma=chroma)

        results = await mgr.save_record("notes_v2", "rec-2", {"a": 1})

        assert results["chroma"] is False
        assert chroma.docs == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_save_record_invalid_collection_raises_value_error(self):
        """SECURITY: SQL-injection whitelist — invalid collection এ ValueError raise করবে।"""
        pg = _FakePostgres()
        mgr = _make_manager(postgres=pg)

        with pytest.raises(ValueError, match="Invalid collection name"):
            await mgr.save_record("bad-name!", "rec-3", {"a": 1})

        # validation execute_query-র আগে হয় — pg-তে কোনো query গেল না
        assert pg.queries == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_save_record_store_failure_isolated(self):
        """এক store ফেইল করলেও বাকি stores-এর save চেষ্টা হয় (degradation isolation)।"""
        sqlite, pg = _FakeSQLite(fail=True), _FakePostgres(fail=True)
        chroma = _FakeChroma(fail=True)
        mgr = _make_manager(sqlite=sqlite, postgres=pg, chroma=chroma)

        results = await mgr.save_record("notes_v2", "rec-4", {"a": 1}, text_content="t")

        assert results["sqlite"] is False
        assert results["postgres"] is False
        assert results["chroma"] is False
        assert results["supabase"] is True  # healthy store still persisted

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_record_sqlite_hit(self):
        sqlite = _FakeSQLite()
        await sqlite.save("notes_v2", "rec-5", {"v": "local"})
        mgr = _make_manager(sqlite=sqlite)

        assert await mgr.get_record("notes_v2", "rec-5") == {"v": "local"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_record_falls_back_to_supabase(self):
        supa = _FakeSupabase()
        await supa.insert("notes_v2", {"id": "rec-6", "v": "cloud"})
        mgr = _make_manager(sqlite=_FakeSQLite(), supabase=supa)

        assert await mgr.get_record("notes_v2", "rec-6") == {"id": "rec-6", "v": "cloud"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_record_all_miss_returns_none(self):
        mgr = _make_manager()
        assert await mgr.get_record("notes_v2", "missing") is None

    @pytest.mark.unit
    def test_backcompat_alias_and_collection_pattern(self):
        # M0-D (AUDIT F4): back-compat alias আসল ক্লাসটিকেই নির্দেশ করে
        assert SQLiteStore is SQLiteMemoryStore
        assert _VALID_COLLECTION_PATTERN.match("notes_v2")
        assert _VALID_COLLECTION_PATTERN.match("KnowledgeBase_2026")
        assert not _VALID_COLLECTION_PATTERN.match("bad-name")
        assert not _VALID_COLLECTION_PATTERN.match("notes; DROP TABLE users")


class TestSQLiteMemoryStore:
    @pytest.mark.unit
    def test_log_task_and_history_roundtrip(self, tmp_path):
        store = SQLiteMemoryStore(db_path=str(tmp_path / "mem.db"))

        store.log_task("summarize doc", "tool", True, 0.25, "ok")
        store.log_task("crawl web", "agent", False, 1.5, "timeout")

        history = store.get_task_history()
        assert len(history) == 2
        # ⚠️ পাওয়া finding (owner fix candidate): get_task_history()
        # `ORDER BY timestamp DESC` ব্যবহার করে, কিন্তু CURRENT_TIMESTAMP-এর
        # granularity 1 সেকেন্ড — same-second insert-এ "latest first" অর্ডার
        # অনির্দিষ্ট থাকে (deterministic tiebreak চাইলে `id DESC` যোগ করতে হবে)।
        # তাই এখানে order-independent contract যাচাই করা হলো:
        by_desc = {h["task_description"]: h for h in history}
        assert by_desc["crawl web"]["success"] == 0
        assert by_desc["crawl web"]["cost"] == 1.5
        assert by_desc["summarize doc"]["success"] == 1
        assert by_desc["summarize doc"]["cost"] == 0.25

    @pytest.mark.unit
    def test_save_and_get_session_messages(self, tmp_path):
        store = SQLiteMemoryStore(db_path=str(tmp_path / "mem.db"))

        store.save_message("s-1", "user", "hi")
        store.save_message("s-1", "assistant", "hello")
        # INSERT OR IGNORE — একই session id বারবার save করলেও error নেই
        store.save_message("s-1", "user", "again")
        store.save_message("s-2", "user", "other session")

        s1 = store.get_session_messages("s-1")
        assert [m["content"] for m in s1] == ["hi", "hello", "again"]  # id ASC order
        assert {m["role"] for m in s1} == {"user", "assistant"}
        assert [m["content"] for m in store.get_session_messages("s-2")] == ["other session"]

    @pytest.mark.unit
    def test_memory_mode_shares_single_connection(self):
        store = SQLiteMemoryStore(db_path=":memory:")

        store.save_message("s-1", "user", "persist across calls")
        store.log_task("t", "tool", True, 0.0, "ok")

        # :memory: mode-এ একই connection reuse হয় — দ্বিতীয় কলেও আগের ডাটা থাকে
        assert store.get_session_messages("s-1")[0]["content"] == "persist across calls"
        assert len(store.get_task_history()) == 1
        assert store.conn is not None


class TestSummaryTree:
    @pytest.mark.unit
    def test_build_hierarchical_summary(self):
        tree = SummaryTree()
        docs = [f"document text number {i} " * 40 for i in range(3)]

        result = tree.build_hierarchical_summary(docs)

        assert [leaf["id"] for leaf in result["leaves"]] == ["doc-0", "doc-1", "doc-2"]
        for leaf in result["leaves"]:
            assert len(leaf["summary"]) <= 220  # per-leaf truncation
        assert len(result["root"]["summary"]) <= 1000  # root summary budget
        assert "document text number 0" in result["root"]["summary"]

    @pytest.mark.unit
    def test_extract_key_concepts_frequency_sorted_short_tokens_dropped(self):
        tree = SummaryTree()
        text = "agent agent agent memory memory storage run of to the"

        concepts = tree.extract_key_concepts(text)

        assert concepts[0] == "agent"  # highest frequency first
        assert "memory" in concepts
        # ≤3 অক্ষরের token বাদ (of/to/the)
        assert all(len(c) > 3 for c in concepts)

    @pytest.mark.unit
    def test_merge_summaries_respects_budget(self):
        tree = SummaryTree()

        short = tree.merge_summaries(["alpha", "beta"])
        assert short == "alpha\nbeta"

        long_summaries = [f"summary-{i} " + "x" * 150 for i in range(20)]
        merged = tree.merge_summaries(long_summaries)
        assert len(merged) <= 1210  # greedy budget ~1200 + boundary
        assert merged.startswith("summary-0")


class TestVectorStoreConfig:
    @pytest.mark.unit
    def test_defaults(self, monkeypatch):
        for var in ("VECTOR_BACKEND", "QDRANT_URL", "PINECONE_API_KEY"):
            monkeypatch.delenv(var, raising=False)

        cfg = get_vector_store_config()

        assert isinstance(cfg, VectorStoreConfig)
        assert cfg.backend == "chroma"
        assert cfg.qdrant_url is None
        assert cfg.default_collection == "supremeai_default"
        assert cfg.distance == "cosine"

    @pytest.mark.unit
    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("VECTOR_BACKEND", "qdrant")
        monkeypatch.setenv("QDRANT_URL", "https://qdrant.example:6333")
        monkeypatch.setenv("QDRANT_API_KEY", "k-test")
        monkeypatch.setenv("PINECONE_INDEX", "supremeai-prod")

        cfg = get_vector_store_config()

        assert cfg.backend == "qdrant"
        assert cfg.qdrant_url == "https://qdrant.example:6333"
        assert cfg.qdrant_api_key == "k-test"
        assert cfg.pinecone_index == "supremeai-prod"


class TestHierarchicalMemoryTree:
    """in-package memory/test_hierarchical_tree.py-র CI-collected twin।"""

    @pytest.mark.unit
    def test_root_initialization(self):
        tree = HierarchicalMemoryTree(root_title="Test Root")

        assert tree.root.id == "root"
        assert tree.root.level == 2
        assert tree.root.title == "Test Root"
        assert tree.nodes["root"] is tree.root

    @pytest.mark.unit
    def test_branch_leaf_lifecycle_and_rollup(self):
        tree = HierarchicalMemoryTree()

        dev = tree.add_branch(title="Frontend", category="dev", tags=["react"])
        leaf = tree.add_leaf(
            title="Store refactor",
            content="Migrated state to Zustand.",
            branch_id=dev.id,
            category="dev",
        )

        assert dev.id in tree.root.children_ids
        assert leaf.parent_id == dev.id
        assert leaf.level == 0 and dev.level == 1
        # rollup: branch summary-তে leaf title আসে, root পর্যন্ত propagate হয়
        assert "Store refactor" in tree.nodes[dev.id].summary
        assert "Frontend" in tree.root.summary

    @pytest.mark.unit
    def test_long_content_truncated_in_summary(self):
        tree = HierarchicalMemoryTree()
        long_text = "x" * 500

        leaf = tree.add_leaf(title="big", content=long_text)

        assert leaf.summary == "x" * 280 + "..."
        assert leaf.content == long_text  # full content preserved

    @pytest.mark.unit
    def test_leaf_with_unknown_branch_falls_back_to_root(self):
        tree = HierarchicalMemoryTree()

        leaf = tree.add_leaf(title="orphan", content="no parent", branch_id="ghost-id")

        assert leaf.parent_id == "root"
        assert leaf.id in tree.root.children_ids

    @pytest.mark.unit
    def test_rollup_unknown_node_is_noop(self):
        tree = HierarchicalMemoryTree()
        tree.rollup_summaries("ghost-id")  # no raise

    @pytest.mark.unit
    def test_search_by_tag_and_category(self):
        tree = HierarchicalMemoryTree()
        sec = tree.add_branch(title="Security", category="security", tags=["auth"])
        tree.add_leaf(
            title="Gitleaks hook",
            content="blocks api key leaks",
            branch_id=sec.id,
            tags=["git"],
        )

        by_tag = tree.search_by_tag_or_category(tag="git")
        assert [n.title for n in by_tag] == ["Gitleaks hook"]

        by_cat = tree.search_by_tag_or_category(category="SECURITY")  # case-insensitive
        assert sec in by_cat

    @pytest.mark.unit
    def test_search_semantic_weighted(self):
        tree = HierarchicalMemoryTree()
        sec = tree.add_branch(title="Security tokens", category="security", tags=["jwt"])
        tree.add_leaf(title="JWT rotation", content="rotate signing keys", branch_id=sec.id)
        tree.add_leaf(title="Unrelated", content="ui colors", category="ux")

        hits = tree.search_semantic_text("jwt security tokens")
        assert hits[0].id == sec.id  # title(3x)+tag(2x) weighted branch first
        assert all(n.id != "root" for n in hits)  # root never returned

    @pytest.mark.unit
    def test_get_subtree_structure(self):
        tree = HierarchicalMemoryTree()
        b = tree.add_branch(title="Branch A")
        tree.add_leaf(title="Leaf 1", content="c", branch_id=b.id)

        subtree = tree.get_subtree("root")
        assert subtree["id"] == "root" and subtree["level"] == 2
        assert len(subtree["children"]) == 1
        assert subtree["children"][0]["children"][0]["title"] == "Leaf 1"
        assert tree.get_subtree("ghost-id") == {}

    @pytest.mark.unit
    def test_export_to_markdown_vault(self):
        tree = HierarchicalMemoryTree()
        b = tree.add_branch(title="Deploy Pipeline", category="devops", tags=["ci"])
        tree.add_leaf(title="Lifespan healer", content="native worker loop", branch_id=b.id)

        vault = tree.export_to_markdown_vault()

        assert "Index.md" in vault
        assert "devops/Deploy Pipeline.md" in vault
        assert "Lifespan healer" in vault["devops/Deploy Pipeline.md"]
        assert "[[devops/Deploy Pipeline" in vault["Index.md"]

    @pytest.mark.unit
    def test_memory_node_defaults(self):
        node = MemoryNode(title="n")
        assert node.level == 0 and node.category == "general"
        assert node.tags == [] and node.children_ids == []
        assert node.parent_id is None


class TestPackageIntegrity:
    """PR-CI measurement integrity regression guards (three-layer contract)."""

    @pytest.mark.unit
    def test_unified_db_manager_dependency_injection_contract(self):
        """সব store injectible — টেস্ট/ops-এ network ছাড়া instance করা যায়।"""
        mgr = _make_manager()
        assert isinstance(mgr.sqlite, _FakeSQLite)
        assert isinstance(mgr.supabase, _FakeSupabase)
        assert isinstance(mgr.chroma, _FakeChroma)
        assert isinstance(mgr.postgres, _FakePostgres)

    @pytest.mark.unit
    def test_get_db_provider_returns_singleton(self):
        """FastAPI DI provider (get_db) module-level singleton-ই দেয়।"""
        from memory.unified_db_manager import get_db, unified_db

        assert get_db() is unified_db
        assert isinstance(unified_db, UnifiedDBManager)
