"""add_performance_indexes

বাংলা মন্তব্য: M2.3 — Performance & Scalability। Admin/dashboard/evolution/API-key
hot query paths-এর জন্য missing database indexes যোগ করা হলো।

Coverage:
- system_alerts          → (resolved, created_at DESC)   # admin.py:301 dashboard list
- code_proposals         → (created_at DESC)             # evolution.py:215
- api_keys               → (user_id, created_at DESC)    # get_api_keys_by_user
- api_key_events         → (api_key_id, created_at DESC) # api key event trail
- execution_chains       → (task_id)                     # task → chain lookup
- agent_reflections      → (agent_id, created_at)        # per-agent history
- dynamic_agents         → (is_active)                   # active agent listing
- execution_logs         → (session_id, ts)              # session timeline (partitioned)
- agent_performance_logs → (agent_name, timestamp)       # per-agent time-series
- performance_alerts     → (agent_name, created_at)      # open alert history

Revision ID: 2026_08_19_000000
Revises: 2026_08_15_145220
Create Date: 2026-08-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026_08_19_000000"
down_revision: str | Sequence[str] | None = "2026_08_15_145220"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(bind, table_name: str) -> bool:
    """বাংলা মন্তব্য: create_all-ভিত্তিক টেবিলগুলো (execution_logs, agent_performance_logs ইত্যাদি)
    alembic chain-এ নেই — fresh DB-তে migration আগে চলে, তাই table থাকার গ্যারান্টি নেই।
    inspection দিয়ে যাচাই করে তবেই index তৈরি করা হয় (idempotent + safe)।"""
    try:
        insp = sa.inspect(bind)
        return (table_name in set(insp.get_table_names())) or insp.has_table(table_name)
    except Exception:
        return False


def upgrade() -> None:
    """Upgrade schema — hot query path indexes।"""
    bind = op.get_bind()

    # 1. system_alerts — admin dashboard: ORDER BY created_at DESC LIMIT 100 (admin.py:301)
    if _table_exists(bind, "system_alerts"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_system_alerts_resolved_created "
            "ON system_alerts (resolved, created_at DESC)"
        )

    # 2. code_proposals — evolution listing: ORDER BY created_at DESC (evolution.py:215)
    if _table_exists(bind, "code_proposals"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_code_proposals_created_at "
            "ON code_proposals (created_at DESC)"
        )

    # 3. api_keys — get_api_keys_by_user: WHERE user_id = $1 ORDER BY created_at DESC
    if _table_exists(bind, "api_keys"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_api_keys_user_created "
            "ON api_keys (user_id, created_at DESC)"
        )

    # 4. api_key_events — API key event trail filtered by api_key_id
    if _table_exists(bind, "api_key_events"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_api_key_events_key "
            "ON api_key_events (api_key_id, created_at DESC)"
        )

    # 5. execution_chains — chain-of-thought lookup by task_id
    if _table_exists(bind, "execution_chains"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_execution_chains_task_id "
            "ON execution_chains (task_id)"
        )

    # 6. agent_reflections — per-agent reflection history (FK dynamic_agents.id)
    if _table_exists(bind, "agent_reflections"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_reflections_agent_created "
            "ON agent_reflections (agent_id, created_at)"
        )

    # 7. dynamic_agents — is_active filter (active agent listing)
    if _table_exists(bind, "dynamic_agents"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_dynamic_agents_is_active "
            "ON dynamic_agents (is_active)"
        )

    # 8. execution_logs — session timeline (partitioned by ts; composite per partition)
    #    Note: table created via Base.metadata.create_all, not alembic chain → guarded.
    if _table_exists(bind, "execution_logs"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_execution_logs_session_ts "
            "ON execution_logs (session_id, ts)"
        )

    # 9. agent_performance_logs — per-agent time-series (create_all table → guarded)
    if _table_exists(bind, "agent_performance_logs"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_perf_name_ts "
            "ON agent_performance_logs (agent_name, timestamp)"
        )

    # 10. performance_alerts — per-agent open-alert history (create_all table → guarded)
    if _table_exists(bind, "performance_alerts"):
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_performance_alerts_agent_created "
            "ON performance_alerts (agent_name, created_at)"
        )


def downgrade() -> None:
    """Downgrade schema — index গুলো ফেরত নেওয়া হয় (reversible)।"""
    bind = op.get_bind()
    _INDEXES: list[tuple[str, str]] = [
        ("system_alerts", "idx_system_alerts_resolved_created"),
        ("code_proposals", "idx_code_proposals_created_at"),
        ("api_keys", "idx_api_keys_user_created"),
        ("api_key_events", "idx_api_key_events_key"),
        ("execution_chains", "idx_execution_chains_task_id"),
        ("agent_reflections", "idx_agent_reflections_agent_created"),
        ("dynamic_agents", "idx_dynamic_agents_is_active"),
        ("execution_logs", "idx_execution_logs_session_ts"),
        ("agent_performance_logs", "idx_agent_perf_name_ts"),
        ("performance_alerts", "idx_performance_alerts_agent_created"),
    ]
    for table, index_name in _INDEXES:
        if _table_exists(bind, table):
            op.execute(f"DROP INDEX IF EXISTS {index_name}")
