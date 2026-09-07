from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class SocialPlatform(StrEnum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class DraftStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    PAUSED = "paused"


@dataclass
class SocialDraft:
    tenant_id: str
    author_id: str
    platform: SocialPlatform
    body: str
    media_urls: tuple[str, ...] = ()
    scheduled_for: datetime | None = None
    id: str = field(default_factory=lambda: f"social_{uuid4().hex}")
    status: DraftStatus = DraftStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    approved_by: str | None = None
    published_at: datetime | None = None
    audit: list[dict[str, Any]] = field(default_factory=list)


class SocialGrowthCircle:
    """Approval-first social operations; no credentials or passwords are handled here."""

    def __init__(self) -> None:
        self._drafts: dict[str, SocialDraft] = {}
        self._paused_tenants: set[str] = set()

    def create_draft(self, draft: SocialDraft) -> SocialDraft:
        if draft.tenant_id in self._paused_tenants:
            raise PermissionError("Social publishing is paused for this tenant")
        if not draft.body.strip():
            raise ValueError("Social draft body is required")
        draft.audit.append({"event": "draft.created", "actor_id": draft.author_id})
        self._drafts[draft.id] = draft
        return draft

    def list_drafts(self, tenant_id: str) -> list[SocialDraft]:
        return [draft for draft in self._drafts.values() if draft.tenant_id == tenant_id]

    def approve(self, draft_id: str, tenant_id: str, approver_id: str) -> SocialDraft:
        draft = self._owned(draft_id, tenant_id)
        if draft.status is not DraftStatus.DRAFT:
            raise ValueError("Only draft content can be approved")
        draft.status = DraftStatus.APPROVED
        draft.approved_by = approver_id
        draft.audit.append({"event": "draft.approved", "actor_id": approver_id})
        return draft

    def pause(self, tenant_id: str) -> None:
        self._paused_tenants.add(tenant_id)
        for draft in self.list_drafts(tenant_id):
            if draft.status in {DraftStatus.DRAFT, DraftStatus.APPROVED}:
                draft.status = DraftStatus.PAUSED

    def resume(self, tenant_id: str) -> None:
        self._paused_tenants.discard(tenant_id)

    def _owned(self, draft_id: str, tenant_id: str) -> SocialDraft:
        draft = self._drafts.get(draft_id)
        if draft is None or draft.tenant_id != tenant_id:
            raise KeyError("Social draft not found")
        return draft


social_growth_circle = SocialGrowthCircle()
