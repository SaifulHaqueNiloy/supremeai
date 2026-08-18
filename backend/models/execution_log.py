import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class LogType(enum.StrEnum):
    shell_cmd = "shell_cmd"
    shell_stdout = "shell_stdout"
    shell_stderr = "shell_stderr"
    file_write = "file_write"
    file_delete = "file_delete"
    dom_action = "dom_action"
    reasoning_token = "reasoning_token"


class ExecutionLog(Base):
    """
    ExecutionLog table is heavily inserted into (up to 100s of times per second).
    It uses PostgreSQL partitioning by RANGE on the 'ts' column (monthly).
    """

    __tablename__ = "execution_logs"
    # বাংলা মন্তব্য (M2.3): session_timeline query (WHERE session_id=? ORDER BY ts) কমposite index
    # session_id alone-এর চেয়ে অনেক সস্তা — partition-প্রতি (session_id, ts) index তৈরি হয়।
    __table_args__ = (
        Index("idx_execution_logs_session_ts", "session_id", "ts"),
        {"postgresql_partition_by": "RANGE (ts)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Partitions require the partition key to be part of the PK in some dialects, but let's stick to standard SQLAlchemy partitioned tables.
    # বাংলা মন্তব্য (M2.3): index=True সরানো হয়েছে — composite (session_id, ts) leftmost prefix হিসাবে session_id lookup cover করে।
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, default=lambda: datetime.now(UTC))

    log_type: Mapped[LogType] = mapped_column(Enum(LogType, name="log_type_enum", create_type=True), nullable=False)

    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
