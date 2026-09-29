"""universal agent policy layer — 4 tables (issue #2504, seq:1 Foundation)

Universal Agent Architecture-এর Layer 2 (Database = Task Policy + Knowledge):
  1. task_policies       — task_type-ভিত্তিক rules/forbidden/required actions
                           (canonical seed: backend/core/database/agent_policies.py)
  2. task_permissions    — per-task permission boolean set (7 capability key)
  3. agent_task_history  — learning-loop ledger (problem → root_cause → solution)
                           নামে "agent_" prefix: লাইভ LLM-call ledger `task_history`
                           (CloudPostgresStore.save_task)-এর সাথে সংঘর্ষ এড়াতে।
  4. router_patterns     — self-improving router-এর শেখা pattern cache

Revision ID: univ_agent_0001
Revises: op_truth_0001
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "univ_agent_0001"
down_revision: str | Sequence[str] | None = "op_truth_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "task_policies",
    "task_permissions",
    "agent_task_history",
    "router_patterns",
)


def _existing_tables_offline_safe(bind) -> set[str]:
    """offline/online দুই মোডেই চলে — existing table নামের সেট বের করে।"""
    try:
        inspector = sa.inspect(bind)
        return set(inspector.get_table_names())
    except Exception:
        return set()


def upgrade() -> None:
    bind = op.get_bind()
    existing = _existing_tables_offline_safe(bind)

    # ── 1. task_policies — task_type-ভিত্তিক কাজের নিয়ম ──
    if "task_policies" not in existing:
        op.create_table(
            "task_policies",
            sa.Column("task_type", sa.String(length=50), primary_key=True),
            sa.Column("summary", sa.Text(), nullable=True),
            # rules / required_actions / forbidden_actions / validation: JSON arrays
            sa.Column("rules", sa.JSON(), nullable=False),
            sa.Column("required_actions", sa.JSON(), nullable=True),
            sa.Column("forbidden_actions", sa.JSON(), nullable=False),
            sa.Column("validation", sa.JSON(), nullable=True),
            sa.Column("expected_output", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    # ── 2. task_permissions — per-task capability set ──
    if "task_permissions" not in existing:
        op.create_table(
            "task_permissions",
            sa.Column("task_type", sa.String(length=50), primary_key=True),
            sa.Column("read_repo", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("modify_code", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("create_issue", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("create_pr", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("comment", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("merge_pr", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("write_db", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    # ── 3. agent_task_history — learning-loop ledger ──
    if "agent_task_history" not in existing:
        op.create_table(
            "agent_task_history",
            sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
            sa.Column("task_type", sa.String(length=50), nullable=False),
            sa.Column("issue_number", sa.Integer(), nullable=True),
            sa.Column("slot_id", sa.String(length=64), nullable=True),
            sa.Column("problem", sa.Text(), nullable=False),
            sa.Column("root_cause", sa.Text(), nullable=True),
            sa.Column("solution", sa.Text(), nullable=True),
            sa.Column("files_changed", sa.JSON(), nullable=True),
            sa.Column("tests_used", sa.JSON(), nullable=True),
            sa.Column("failed_approaches", sa.JSON(), nullable=True),
            sa.Column("verification_result", sa.Text(), nullable=True),
            sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_agent_task_history_type", "agent_task_history", ["task_type"])
        op.create_index("ix_agent_task_history_issue", "agent_task_history", ["issue_number"])
        op.create_index("ix_agent_task_history_created", "agent_task_history", ["created_at"])

    # ── 4. router_patterns — self-improving pattern cache ──
    if "router_patterns" not in existing:
        op.create_table(
            "router_patterns",
            sa.Column("task_type", sa.String(length=50), primary_key=True),
            sa.Column("common_rules_needed", sa.JSON(), nullable=True),
            sa.Column("common_failures", sa.JSON(), nullable=True),
            sa.Column("successful_approaches", sa.JSON(), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    """Policy layer ফেলে দেওয়া — seed data আবার agent_policies.py থেকে
    আসবে, তাই ক্ষতি নেই; তবে learning history (agent_task_history) হারায়।"""
    bind = op.get_bind()
    existing = _existing_tables_offline_safe(bind)
    for table in reversed(_TABLES):
        if table in existing:
            op.drop_table(table)
