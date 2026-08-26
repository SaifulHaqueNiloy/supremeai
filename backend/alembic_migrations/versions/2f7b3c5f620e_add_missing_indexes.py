"""add missing indexes

Revision ID: 2f7b3c5f620e
Revises: cb8d8501f289
Create Date: 2026-08-26 08:56:21.239577

"""

from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f7b3c5f620e"
down_revision: str | Sequence[str] | None = "cb8d8501f289"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing indexes to improve query performance."""

    # ============================================================
    # 1. ARTIFACTS TABLE INDEXES
    # ============================================================

    # Primary lookup by user_id (used in almost every artifact query)
    op.create_index(
        "idx_artifacts_user_id",
        "artifacts",
        ["user_id"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_artifacts_user_id")

    # Conversation listing (list all artifacts for a conversation)
    op.create_index(
        "idx_artifacts_conversation_id",
        "artifacts",
        ["conversation_id"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_artifacts_conversation_id")

    # Sorting by update time (used in list endpoints)
    op.create_index(
        "idx_artifacts_updated_at",
        "artifacts",
        ["updated_at"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_artifacts_updated_at")

    # Composite index for user's artifacts sorted by time (common pattern)
    op.create_index(
        "idx_artifacts_user_updated",
        "artifacts",
        ["user_id", "updated_at"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_artifacts_user_updated")

    # Filter by artifact type
    op.create_index(
        "idx_artifacts_type",
        "artifacts",
        ["artifact_type"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_artifacts_type")

    # Pinned artifacts lookup
    op.create_index(
        "idx_artifacts_pinned",
        "artifacts",
        ["user_id", "is_pinned"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_artifacts_pinned")

    # ============================================================
    # 2. CONVERSATIONS TABLE INDEXES
    # ============================================================

    # User's conversations (most common query)
    op.create_index(
        "idx_conversations_user_id",
        "conversations",
        ["user_id"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_conversations_user_id")

    # Time-based ordering
    op.create_index(
        "idx_conversations_created",
        "conversations",
        ["user_id", "created_at"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_conversations_created")

    # ============================================================
    # 3. MESSAGES TABLE INDEXES
    # ============================================================

    # Messages in a conversation (chat history loading)
    op.create_index(
        "idx_messages_conversation_id",
        "messages",
        ["conversation_id"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_messages_conversation_id")

    # Ordered messages (for pagination)
    op.create_index(
        "idx_messages_conv_created",
        "messages",
        ["conversation_id", "created_at"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_messages_conv_created")

    # ============================================================
    # 4. USERS TABLE INDEXES
    # ============================================================

    # Email lookup (login/auth)
    op.create_index(
        "idx_users_email",
        "users",
        ["email"],
        unique=True,
        if_not_exists=True,
    )
    print("✅ Created index: idx_users_email (unique)")

    # JWT subject lookup (token validation)
    op.create_index(
        "idx_users_sub",
        "users",
        ["sub"],
        if_not_exists=True,
    )
    print("✅ Created index: idx_users_sub")

    # ============================================================
    # 5. USER_PREFERENCES TABLE INDEXES
    # ============================================================

    # Primary lookup
    op.create_index(
        "idx_user_prefs_user_id",
        "user_preferences",
        ["user_id"],
        unique=True,
        if_not_exists=True,
    )
    print("✅ Created index: idx_user_prefs_user_id (unique)")

    # ============================================================
    # 6. KNOWLEDGE_BASE / MEMORY TABLES (if they exist)
    # ============================================================

    try:
        # Semantic search vectors need ivfflat/hnsw index (PostgreSQL with pgvector)
        op.execute("""
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace 
                           WHERE c.relname = 'knowledge_base') THEN
                    CREATE INDEX IF NOT EXISTS idx_knowledge_base_user_embedding 
                        ON knowledge_base USING hnsw (embedding vector_cosine_ops) 
                        WITH (m = 16, ef_construction = 64);
                END IF;
            END $$;
        """)
        print("✅ Created index: idx_knowledge_base_user_embedding (HNSW)")
    except Exception as e:
        print(f"⚠️ Skipped knowledge_base index (table may not exist): {e}")

    try:
        op.create_index(
            "idx_knowledge_base_user_id",
            "knowledge_base",
            ["user_id"],
            if_not_exists=True,
        )
        print("✅ Created index: idx_knowledge_base_user_id")
    except Exception:
        pass

    # ============================================================
    # 7. AUDIT LOG / ACTIVITY TABLES (if they exist)
    # ============================================================

    try:
        # Activity logs filtered by user and time range
        op.create_index(
            "idx_activity_logs_user_time",
            "activity_logs",
            ["user_id", "created_at"],
            if_not_exists=True,
        )
        print("✅ Created index: idx_activity_logs_user_time")
    except Exception:
        pass

    try:
        # Telemetry data
        op.create_index(
            "idx_telemetry_session",
            "telemetry",
            ["session_id", "timestamp"],
            if_not_exists=True,
        )
        print("✅ Created index: idx_telemetry_session")
    except Exception:
        pass

    print("\\n🎉 Migration complete! All critical indexes have been created.")


def downgrade() -> None:
    """Remove the indexes (for rollback)."""

    indexes_to_drop = [
        # Artifacts
        "idx_artifacts_user_id",
        "idx_artifacts_conversation_id",
        "idx_artifacts_updated_at",
        "idx_artifacts_user_updated",
        "idx_artifacts_type",
        "idx_artifacts_pinned",
        # Conversations
        "idx_conversations_user_id",
        "idx_conversations_created",
        # Messages
        "idx_messages_conversation_id",
        "idx_messages_conv_created",
        # Users
        "idx_users_email",
        "idx_users_sub",
        # Preferences
        "idx_user_prefs_user_id",
        # Knowledge base
        "idx_knowledge_base_user_id",
        # Activity/Audit
        "idx_activity_logs_user_time",
        "idx_telemetry_session",
    ]

    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name, tablename=None, if_exists=True)
            print(f"Dropped index: {index_name}")
        except Exception as e:
            print(f"Could not drop {index_name}: {e}")

    print("\\nRollback complete.")
