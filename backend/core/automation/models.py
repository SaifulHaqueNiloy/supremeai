from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AutomationStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    SKIPPED = "skipped"  # When automation is disabled


class AutomationEvent(BaseModel):
    """
    Vendor-neutral envelope for background events.
    """

    model_config = ConfigDict(extra="forbid")

    workflow_key: str = Field(
        ...,
        description="The unique registry key identifying the target workflow (e.g., 'USER_REGISTERED').",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="The data to be processed by the workflow."
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional tracking metadata (e.g., user_id, trace_id)."
    )


class AutomationResult(BaseModel):
    """
    Standardized response from the automation dispatcher.
    """

    status: AutomationStatus
    provider: str
    message: str
    execution_id: str | None = None
