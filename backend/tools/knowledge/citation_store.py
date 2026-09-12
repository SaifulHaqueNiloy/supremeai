"""Tenant-scoped, provider-neutral citation records for research outputs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Iterable
from urllib.parse import urlparse


@dataclass(frozen=True)
class Citation:
    id: str
    tenant_id: str
    claim_id: str
    url: str
    title: str = ""
    excerpt: str = ""
    confidence_score: float = 0.0
    created_at: str = ""


class CitationStore:
    """In-process adapter with a stable interface for a durable store later."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], list[Citation]] = {}
        self._lock = RLock()

    def add(self, *, tenant_id: str, claim_id: str, url: str, title: str = "", excerpt: str = "", confidence_score: float = 0.0) -> Citation:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("citation URL must be an absolute HTTP(S) URL")
        citation = Citation(
            id=f"cite_{len(self._items.get((tenant_id, claim_id), [])) + 1}",
            tenant_id=tenant_id,
            claim_id=claim_id,
            url=url,
            title=title,
            excerpt=excerpt,
            confidence_score=max(0.0, min(1.0, confidence_score)),
            created_at=datetime.now(UTC).isoformat(),
        )
        with self._lock:
            self._items.setdefault((tenant_id, claim_id), []).append(citation)
        return citation

    def for_claim(self, *, tenant_id: str, claim_id: str) -> list[dict]:
        with self._lock:
            return [asdict(item) for item in self._items.get((tenant_id, claim_id), [])]

    def claims(self, *, tenant_id: str, claim_ids: Iterable[str]) -> dict[str, list[dict]]:
        return {claim_id: self.for_claim(tenant_id=tenant_id, claim_id=claim_id) for claim_id in claim_ids}


citation_store = CitationStore()

__all__ = ["Citation", "CitationStore", "citation_store"]
