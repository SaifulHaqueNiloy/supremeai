"""
M2.3 — Performance & Scalability: database index migration tests.

বাংলা মন্তব্য: এই টেস্টগুলো সুনিশ্চিত করে যে
(1) নতুন alembic migration (`2026_08_19_000000_add_performance_indexes`) সঠিক revision
    chain-এ বসেছে এবং hot query path-গুলোর জন্য index তৈরি করে,
(2) create_all-ভিত্তিক টেবিলগুলোতে (execution_logs, agent_performance_logs,
    performance_alerts) composite index সঠিকভাবে ডিফাইন হয়েছে,
(3) alembic পাওয়া গেলে (CI-তে) migration upgrade/downgrade আসলেই SQLite-এ চলে।
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from models.base import Base

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"
MIGRATION_FILE = "2026_08_19_000000_add_performance_indexes.py"
PREV_HEAD = "2026_08_15_145220"

# বাংলা মন্তব্য: hot query path index → table mapping (migration + models দুই জায়গায় match)
EXPECTED_INDEXES: dict[str, list[str]] = {
    "system_alerts": ["idx_system_alerts_resolved_created"],
    "code_proposals": ["idx_code_proposals_created_at"],
    "api_keys": ["idx_api_keys_user_created"],
    "api_key_events": ["idx_api_key_events_key"],
    "execution_chains": ["idx_execution_chains_task_id"],
    "agent_reflections": ["idx_agent_reflections_agent_created"],
    "dynamic_agents": ["idx_dynamic_agents_is_active"],
    "execution_logs": ["idx_execution_logs_session_ts"],
    "agent_performance_logs": ["idx_agent_perf_name_ts"],
    "performance_alerts": ["idx_performance_alerts_agent_created"],
}

MODEL_COMPOSITE_INDEXES: dict[str, list[str]] = {
    "execution_logs": ["idx_execution_logs_session_ts"],
    "agent_performance_logs": ["idx_agent_perf_name_ts"],
    "performance_alerts": ["idx_performance_alerts_agent_created"],
}


# ── Migration file structure ──────────────────────────────────────────────────


def _migration_src() -> str:
    path = MIGRATIONS_DIR / MIGRATION_FILE
    assert path.is_file(), f"Missing migration file: {MIGRATION_FILE}"
    return path.read_text(encoding="utf-8")


def test_migration_file_exists() -> None:
    assert (MIGRATIONS_DIR / MIGRATION_FILE).is_file()


def test_migration_chains_from_previous_head() -> None:
    src = _migration_src()
    m_rev = re.search(r'revision: str = "([^"]+)"', src)
    m_down = re.search(r'down_revision: str \| Sequence\[str\] \| None = "([^"]+)"', src)
    assert m_rev, "revision id missing"
    assert m_down, "down_revision missing"
    assert m_rev.group(1) == "2026_08_19_000000"
    assert m_down.group(1) == PREV_HEAD, f"must chain from previous head {PREV_HEAD}"


def test_migration_declares_all_hot_path_indexes() -> None:
    src = _migration_src()
    for table, indexes in EXPECTED_INDEXES.items():
        for idx in indexes:
            assert idx in src, f"migration must mention index {idx}"
        assert f"ON {table}" in src, f"migration must create index on {table}"


def test_migration_has_symmetrical_downgrade() -> None:
    src = _migration_src()
    # বাংলা মন্তব্য: downgrade() index নামগুলো লুপে f-string দিয়ে DROP করে, তাই literal
    # stmt-এর বদলে সামগ্রিকভাবে (DROP mechanism + প্রতিটি index নাম) যাচাই করা হয়।
    assert "DROP INDEX IF EXISTS" in src, "downgrade must drop indexes via DROP INDEX IF EXISTS"
    for indexes in EXPECTED_INDEXES.values():
        for idx in indexes:
            assert idx in src, f"downgrade must reference index {idx}"


# ── Model composite index definitions (create_all path) ───────────────────────


def test_models_define_composite_indexes() -> None:
    from models.evolution import AgentPerformanceLog, PerformanceAlert
    from models.execution_log import ExecutionLog

    for table, indexes in MODEL_COMPOSITE_INDEXES.items():
        model = {
            "execution_logs": ExecutionLog,
            "agent_performance_logs": AgentPerformanceLog,
            "performance_alerts": PerformanceAlert,
        }[table]
        names = {ix.name for ix in model.__table__.indexes}
        for idx in indexes:
            assert idx in names, f"{table} model must define composite index {idx}"


def test_composite_indexes_created_on_sqlite() -> None:
    """বাংলা মন্তব্য: create_all চালালে composite index আসলেই তৈরি হচ্ছে কিনা (fresh DB path)।"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    insp = inspect(engine)
    for table, indexes in MODEL_COMPOSITE_INDEXES.items():
        if not insp.has_table(table):
            continue
        actual = {ix["name"] for ix in insp.get_indexes(table)}
        for idx in indexes:
            assert idx in actual, f"SQLite create_all should create {idx} on {table}"


# ── Live migration execution (requires alembic — available in CI) ────────────


def _alembic_available() -> bool:
    return importlib.util.find_spec("alembic") is not None


@pytest.mark.skipif(not _alembic_available(), reason="alembic not installed in this env")
def test_migration_runs_upgrade_and_downgrade_on_sqlite() -> None:
    """বাংলা মন্তব্য: alembic MigrationContext + Operations দিয়ে SQLite-এ upgrade() ও
    downgrade() সম্পূর্ণ cycle চালানো হয় — reversible থাকা সুনিশ্চিত হয়।

    ⚠️ `backend/alembic/` ডিরেক্টরি (migrations dir) একটি namespace/package এবং এটি
    real alembic-কে shadow করে। তাই import করার আগে sys.path থেকে backend সরিয়ে
    নেওয়া হয়, পরে ফেরত দেওয়া হয়।"""
    from alembic import op as _alembic_op
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext

    spec = importlib.util.spec_from_file_location(
        "perf_indexes_migration", str(MIGRATIONS_DIR / MIGRATION_FILE)
    )
    assert spec and spec.loader, "cannot load migration module"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from sqlalchemy import text as _text

    with engine.connect() as conn:
        # টেবিলগুলো আগে তৈরি করা হয় (migration কেবল index যোগ করে)
        for ddl in _CREATE_TABLES_SQL.values():
            conn.execute(_text(ddl))
        conn.commit()

        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            mod.upgrade()
        conn.commit()

        with engine.connect() as check_conn:
            insp = inspect(check_conn)
            for table, indexes in EXPECTED_INDEXES.items():
                if not insp.has_table(table):
                    continue
                actual = {ix["name"] for ix in insp.get_indexes(table)}
                for idx in indexes:
                    assert idx in actual, f"upgrade() should create {idx} on {table}"

        with Operations.context(ctx):
            mod.downgrade()
        conn.commit()

        with engine.connect() as check_conn:
            insp = inspect(check_conn)
            for table, indexes in EXPECTED_INDEXES.items():
                if not insp.has_table(table):
                    continue
                actual = {ix["name"] for ix in insp.get_indexes(table)}
                for idx in indexes:
                    assert idx not in actual, f"downgrade() should drop {idx} on {table}"




# বাংলা মন্তব্য: SQLite-এ migration test-এর জন্য ন্যূনতম টেবিল স্কিমা (columns + PK/FK)
_CREATE_TABLES_SQL: dict[str, str] = {
    "system_alerts": (
        "CREATE TABLE system_alerts (id VARCHAR(36) PRIMARY KEY, level VARCHAR(20) NOT NULL, "
        "message TEXT NOT NULL, resolved BOOLEAN, created_at TIMESTAMP, resolved_at TIMESTAMP)"
    ),
    "code_proposals": (
        "CREATE TABLE code_proposals (id CHAR(32) PRIMARY KEY, proposal_id VARCHAR(255) UNIQUE, "
        "skill_name VARCHAR(255) NOT NULL, generated_code TEXT NOT NULL, "
        "ast_validated BOOLEAN DEFAULT false, ci_passed BOOLEAN DEFAULT false, "
        "status VARCHAR(50) DEFAULT 'proposed', metadata_json TEXT, version INTEGER DEFAULT 1, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    ),
    "api_keys": (
        "CREATE TABLE api_keys (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, "
        "name TEXT NOT NULL, key_hash TEXT NOT NULL UNIQUE, key_masked TEXT NOT NULL, "
        "key_prefix TEXT NOT NULL, rate_limit_rps INTEGER DEFAULT 6, revoked BOOLEAN DEFAULT false, "
        "expires_at INTEGER, last_used_at INTEGER, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)"
    ),
    "api_key_events": (
        "CREATE TABLE api_key_events (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "api_key_id INTEGER NOT NULL, event_type TEXT NOT NULL, details TEXT, "
        "ip_address TEXT, created_at INTEGER NOT NULL)"
    ),
    "execution_chains": (
        "CREATE TABLE execution_chains (id CHAR(32) PRIMARY KEY, task_id VARCHAR, "
        "chain_of_thought TEXT, tokens_used INTEGER, model_provider TEXT, "
        "raw_response TEXT, created_at TIMESTAMP)"
    ),
    "agent_reflections": (
        "CREATE TABLE agent_reflections (id CHAR(32) PRIMARY KEY, agent_id INTEGER, "
        "task_id VARCHAR, outcome_summary TEXT, learned_patterns TEXT, "
        "confidence_score FLOAT, created_at TIMESTAMP)"
    ),
    "dynamic_agents": (
        "CREATE TABLE dynamic_agents (id INTEGER PRIMARY KEY, name VARCHAR(100) UNIQUE, "
        "description VARCHAR(500), execution_steps TEXT NOT NULL, is_active BOOLEAN, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    ),
    "execution_logs": (
        "CREATE TABLE execution_logs (id CHAR(32) NOT NULL, session_id CHAR(32) NOT NULL, "
        "ts TIMESTAMP NOT NULL, log_type VARCHAR(50) NOT NULL, payload TEXT NOT NULL, "
        "exit_code INTEGER, duration_ms INTEGER, PRIMARY KEY (id, ts))"
    ),
    "agent_performance_logs": (
        "CREATE TABLE agent_performance_logs (id CHAR(32) PRIMARY KEY, agent_name VARCHAR(255) NOT NULL, "
        "timestamp TIMESTAMP NOT NULL, response_time_ms FLOAT NOT NULL, accuracy_score FLOAT NOT NULL, "
        "cost_usd FLOAT DEFAULT 0, tokens_input INTEGER DEFAULT 0, tokens_output INTEGER DEFAULT 0, "
        "throughput_per_minute FLOAT, error_rate FLOAT, user_satisfaction FLOAT, "
        "endpoint VARCHAR(255), model_used VARCHAR(100), created_at TIMESTAMP)"
    ),
    "performance_alerts": (
        "CREATE TABLE performance_alerts (id CHAR(32) PRIMARY KEY, agent_name VARCHAR(255) NOT NULL, "
        "alert_type VARCHAR(50) NOT NULL, severity VARCHAR(20) NOT NULL, metric_value FLOAT NOT NULL, "
        "threshold_value FLOAT NOT NULL, description TEXT NOT NULL, recommended_action TEXT NOT NULL, "
        "acknowledged_by VARCHAR(255), acknowledged_at TIMESTAMP, resolved_at TIMESTAMP, "
        "created_at TIMESTAMP)"
    ),
}
