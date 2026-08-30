"""merge heads

বাংলা মন্তব্য: তিনটা আলাদা migration branch (g2b3c4d5e6f7, tier_s_001,
2026_08_15_145220) একসাথে মার্জ করা হচ্ছে। এই তিনটা branch আলাদাভাবে তৈরি
হয়েছিল, ফলে alembic-এর একাধিক head ছিল -- `alembic upgrade head` চালালে
"Multiple head revisions are present" এরর দিত। এই migration কোনো schema
পরিবর্তন করে না, শুধু history-কে single-head-এ নিয়ে আসে।

Revision ID: h3i4j5k6l7m8
Revises: g2b3c4d5e6f7, tier_s_001, 2026_08_15_145220
Create Date: 2026-08-30
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "h3i4j5k6l7m8"
down_revision: str | Sequence[str] | None = (
    "g2b3c4d5e6f7",
    "tier_s_001",
    "2026_08_15_145220",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """কোনো schema পরিবর্তন নেই -- শুধু branch merge।"""
    pass


def downgrade() -> None:
    """কোনো schema পরিবর্তন নেই -- শুধু branch merge।"""
    pass
