# Self-Evolution Engine models tracking autonomous code updates
# বাংলা মন্তব্য: এআই কর্তৃক জেনারেটেড নতুন স্কিল, স্বয়ংক্রিয় প্রপোজাল ট্র্যাকিং এবং ফিটনেস স্কোরিং মডেল।

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class SkillFitness(Base):
    __tablename__ = "skill_fitness"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fitness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Optimistic Concurrency Control (OCC)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __mapper_args__ = {"version_id_col": version}  # SQLAlchemy অটোমেটিকভাবে ভার্সন ট্র্যাকিং এবং রেস-কন্ডিশন ব্লক করবে


class CodeProposal(Base):
    __tablename__ = "code_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Pro Tip: Text allows arbitrary code length without database truncation.
    generated_code: Mapped[str] = mapped_column(Text, nullable=False)
    ast_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ci_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="proposed", nullable=False
    )  # proposed, approved, rejected, applied

    # Pro Tip: JSONB is highly optimized for PostgreSQL query matching.
    metadata_json: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __mapper_args__ = {"version_id_col": version}


class AgentPerformanceLog(Base):
    """PerformanceOracle: Time-series performance metrics per agent."""

    __tablename__ = "agent_performance_logs"
    # বাংলা মন্তব্য (M2.3): per-agent time-series query (WHERE agent_name=? ORDER BY timestamp)
    # এর জন্য (agent_name, timestamp) composite index — agent_name alone-এর তুলনায় অনেক দ্রুত।
    __table_args__ = (Index("idx_agent_perf_name_ts", "agent_name", "timestamp"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # বাংলা মন্তব্য (M2.3): index=True সরানো — composite leftmost prefix cover করে।
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Core metrics
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0-1.0
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tokens_input: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Derived metrics
    throughput_per_minute: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0-1.0
    user_satisfaction: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0-5.0

    # Metadata
    endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class PerformanceAlert(Base):
    """PerformanceOracle: Alerts when agents fall below thresholds."""

    __tablename__ = "performance_alerts"
    # বাংলা মন্তব্য (M2.3): open-alert list + per-agent history query-এর জন্য
    # (agent_name, created_at) composite index।
    __table_args__ = (Index("idx_performance_alerts_agent_created", "agent_name", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # বাংলা মন্তব্য (M2.3): index=True সরানো — composite leftmost prefix cover করে।
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    alert_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # latency_spike, accuracy_drop, cost_surge, error_rate_high
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # warning, critical, emergency
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)

    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
