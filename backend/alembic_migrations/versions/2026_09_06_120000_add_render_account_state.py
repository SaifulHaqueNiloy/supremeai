"""add persistent Render account state and preflight audit events"""

import sqlalchemy as sa
from alembic import op

revision = "2026_09_06_120000"
down_revision = "h3i4j5k6l7m8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "render_account_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("account_key", sa.String(120), nullable=False, unique=True),
        sa.Column("role", sa.String(80), nullable=False),
        sa.Column("plan", sa.String(40), nullable=False, server_default="unknown"),
        sa.Column("status", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("reason", sa.String(120), nullable=True),
        sa.Column("usage_minutes", sa.Float(), nullable=True),
        sa.Column("usage_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recheck_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_render_account_states_status_recheck", "render_account_states", ["status", "recheck_at"]
    )
    op.create_table(
        "render_preflight_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("account_key", sa.String(120), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(120), nullable=True),
        sa.Column("usage_minutes", sa.Float(), nullable=True),
        sa.Column(
            "observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("metadata", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_render_preflight_events_account_observed",
        "render_preflight_events",
        ["account_key", "observed_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_render_preflight_events_account_observed", table_name="render_preflight_events"
    )
    op.drop_table("render_preflight_events")
    op.drop_index("ix_render_account_states_status_recheck", table_name="render_account_states")
    op.drop_table("render_account_states")
