"""add missing indexes

Revision ID: 2f7b3c5f620e
Revises: cb8d8501f289
Create Date: 2026-08-26 08:56:21.239577

"""

from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "2f7b3c5f620e"
down_revision: str | Sequence[str] | None = "cb8d8501f289"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    """Return whether an optional table exists on the current database."""
    bind = op.get_bind()
    return inspect(bind).has_table(table_name)


def upgrade() -> None:
    """Add missing indexes to improve query performance.

    Required indexes fail the migration loudly. Indexes on optional tables are
    skipped only when the table itself does not exist; an actual index-creation
    error is never swallowed.
    """

    # ============================================================
    # 1. ARTIFACTS TABLE INDEXES
    # ============================================================

    op.create_index("idx_artifacts_user_id", "artifacts", ["user_id"], if_not_exists=True)
    print("✅ Created index: idx_artifacts_user_id")

    op.create_index("idx_artifacts_conversation_id", "artifacts", ["conversation_id"], if_not_exists=True)
    print("✅ Created index: idx_artifacts_conversation_id")

    op.create_index("idx_artifacts_updated_at", "artifacts", ["updated_at"], if_not_exists=True)
    print("✅ Created index: idx_artifacts_updated_at")

    op.create_index("idx_artifacts_user_updated", "artifacts", ["user_id", "updated_at"], if_not_exists=True)
    print("✅ Created index: idx_artifacts_user_updated")

    op.create_index("idx_artifacts_type", "artifacts", ["artifact_type"], if_not_exists=True)
    print("✅ Created index: idx_artifacts_type")

    op.create_index("idx_artifacts_pinned", "artifacts", ["user_id", "is_pinned"], if_not_exists=True)
    print("✅ Created index: idx_artifacts_pinned")

    # ============================================================
    # 2. CONVERSATIONS TABLE INDEXES
    # ============================================================

    op.create_index("idx_conversations_user_id", "conversations", ["user_id"], if_not_exists=True)
    print("✅ Created index: idx_conversations_user_id")

    op.create_index("idx_conversations_created", "conversations", ["user_id", "created_at"], if_not_exists=True)
    print("✅ Created index: idx_conversations_created")

    # ============================================================
    # 3. MESSAGES TABLE INDEXES
    # ============================================================

    op.create_index("idx_messages_conversation_id", "messages", ["conversation_id"], if_not_exists=True)
    print("✅ Created index: idx_messages_conversation_id")

    op.create_index("idx_messages_conv_created", "messages", ["conversation_id", "created_at"], if_not_exists=True)
    print("✅ Created index: idx_messages_conv_created")

    # ============================================================
    # 4. USERS TABLE INDEXES
    # ============================================================

    op.create_index("idx_users_email", "users", ["email"], unique=True, if_not_exists=True)
    print("✅ Created index: idx_users_email (unique)")

    op.create_index("idx_users_sub", "users", ["sub"], if_not_exists=True)
    print("✅ Created index: idx_users_sub")

    # ============================================================
    # 5. USER_PREFERENCES TABLE INDEXES
    # ============================================================

    op.create_index("idx_user_prefs_user_id", "user_preferences", ["user_id"], unique=True, if_not_exists=True)
    print("✅ Created index: idx_user_prefs_user_id (unique)")

    # ============================================================
    # 6. KNOWLEDGE_BASE / MEMORY TABLES (optional)
    # ============================================================

    if _table_exists("knowledge_base"):
        # pgvector HNSW index. If pgvector/index creation is broken, fail the
        # migration instead of leaving production with an unindexed hot path.
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_knowledge_base_user_embedding
            ON knowledge_base USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
            """
        )
        print("✅ Created index: idx_knowledge_base_user_embedding (HNSW)")

        op.create_index(
            "idx_knowledge_base_user_id",
            "knowledge_base",
            ["user_id"],
            if_not_exists=True,
        )
        print("✅ Created index: idx_knowledge_base_user_id")
    else:
        print("ℹ️ Skipped knowledge_base indexes: table does not exist")

    # ============================================================
    # 7. AUDIT LOG / ACTIVITY TABLES (optional)
    # ============================================================

    if _table_exists("activity_logs"):
        op.create_index(
            "idx_activity_logs_user_time",
            "activity_logs",
            ["user_id", "created_at"],
            if_not_exists=True,
        )
        print("✅ Created index: idx_activity_logs_user_time")
    else:
        print("ℹ️ Skipped activity_logs index: table does not exist")

    if _table_exists("telemetry"):
        op.create_index(
            "idx_telemetry_session",
            "telemetry",
            ["session_id", "timestamp"],
            if_not_exists=True,
        )
        print("✅ Created index: idx_telemetry_session")
    else:
        print("ℹ️ Skipped telemetry index: table does not exist")

    print("\n🎉 Migration complete! All applicable critical indexes have been created.")


def downgrade() -> None:
    """Remove the indexes (for rollback)."""

    indexes_to_drop = [
        "idx_artifacts_user_id",
        "idx_artifacts_conversation_id",
        "idx_artifacts_updated_at",
        "idx_artifacts_user_updated",
        "idx_artifacts_type",
        "idx_artifacts_pinned",
        "idx_conversations_user_id",
        "idx_conversations_created",
        "idx_messages_conversation_id",
        "idx_messages_conv_created",
        "idx_users_email",
        "idx_users_sub",
        "idx_user_prefs_user_id",
        "idx_knowledge_base_user_id",
        "idx_activity_logs_user_time",
        "idx_telemetry_session",
    ]

    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name, tablename=None, if_exists=True)
            print(f"Dropped index: {index_name}")
        except Exception as e:
            print(f"Could not drop {index_name}: {e}")

    print("\nRollback complete.")
