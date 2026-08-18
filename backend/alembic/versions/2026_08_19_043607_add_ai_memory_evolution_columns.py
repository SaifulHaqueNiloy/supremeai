"""add_ai_memory_evolution_columns

বাংলা মন্তব্য: M5.1 — Self-Evolving Memory Storage।
Supabase `ai_memory` (pgvector) টেবিলে cluster/decay কলাম এবং
সংশ্লিষ্ট ইনডেক্স যোগ করা হয়েছে।

Revision ID: 2026_08_19_043607
Revises: 2026_08_19_000000
Create Date: 2026-08-19 04:36:07.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026_08_19_043607"
down_revision: str | Sequence[str] | None = "2026_08_19_000000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add cluster/decay columns and indexes to ai_memory."""
    op.execute(
        """
        ALTER TABLE ai_memory
        ADD COLUMN IF NOT EXISTS cluster_id TEXT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE ai_memory
        ADD COLUMN IF NOT EXISTS access_count INT DEFAULT 1
        """
    )
    op.execute(
        """
        ALTER TABLE ai_memory
        ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMPTZ DEFAULT NOW()
        """
    )
    op.execute(
        """
        ALTER TABLE ai_memory
        ADD COLUMN IF NOT EXISTS importance_score FLOAT DEFAULT 1.0
        """
    )
    op.execute(
        """
        ALTER TABLE ai_memory
        ADD COLUMN IF NOT EXISTS is_synthesized BOOLEAN DEFAULT FALSE
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ai_memory_cluster
        ON ai_memory (cluster_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ai_memory_decay
        ON ai_memory (last_accessed_at, importance_score)
        """
    )


def downgrade() -> None:
    """Drop indexes and columns added in upgrade."""
    op.execute("DROP INDEX IF EXISTS idx_ai_memory_decay")
    op.execute("DROP INDEX IF EXISTS idx_ai_memory_cluster")
    op.execute("ALTER TABLE ai_memory DROP COLUMN IF EXISTS is_synthesized")
    op.execute("ALTER TABLE ai_memory DROP COLUMN IF EXISTS importance_score")
    op.execute("ALTER TABLE ai_memory DROP COLUMN IF EXISTS last_accessed_at")
    op.execute("ALTER TABLE ai_memory DROP COLUMN IF EXISTS access_count")
    op.execute("ALTER TABLE ai_memory DROP COLUMN IF EXISTS cluster_id")
