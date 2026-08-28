import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

from database.session import Base


class AutomationExecution(Base):
    __tablename__ = "automation_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), index=True, nullable=False)
    workflow_key = Column(String(100), index=True, nullable=False)
    provider = Column(String(50), nullable=False)
    status = Column(String(50), default="PENDING", index=True)
    attempt = Column(Integer, default=1)

    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    http_status = Column(Integer, nullable=True)
    external_execution_id = Column(String(100), nullable=True)
    trace_id = Column(String(100), index=True, nullable=True)

    error_code = Column(String(100), nullable=True)
    error_message = Column(String(1024), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
