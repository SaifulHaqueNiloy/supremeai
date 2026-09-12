"""Governed parallel research orchestration primitives."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ResearchFinding:
    source: str
    claim: str
    evidence: str = ""
    confidence: float = 0.0


@dataclass(frozen=True)
class ResearchResult:
    query: str
    findings: list[ResearchFinding]
    synthesis: str
    scouts_completed: int


Scout = Callable[[str], Awaitable[Sequence[ResearchFinding]]]
Judge = Callable[[str, Sequence[ResearchFinding]], Awaitable[str]]


class ResearchHarness:
    """Planner -> bounded parallel scouts -> judge, with graceful degradation."""

    def __init__(self, *, max_scouts: int = 8, timeout_seconds: float = 30.0) -> None:
        self.max_scouts = max(1, min(max_scouts, 32))
        self.timeout_seconds = max(1.0, timeout_seconds)

    async def run(self, query: str, scouts: Sequence[Scout], judge: Judge) -> ResearchResult:
        if not query.strip():
            raise ValueError("research query must not be empty")
        selected = list(scouts[: self.max_scouts])
        async def call(scout: Scout) -> Sequence[ResearchFinding]:
            try:
                return await asyncio.wait_for(scout(query), timeout=self.timeout_seconds)
            except (Exception, asyncio.TimeoutError):
                return []
        batches = await asyncio.gather(*(call(scout) for scout in selected))
        findings = [finding for batch in batches for finding in batch]
        synthesis = await judge(query, findings) if findings else "No verified findings were produced."
        return ResearchResult(query=query, findings=findings, synthesis=synthesis, scouts_completed=sum(bool(batch) for batch in batches))


__all__ = ["ResearchFinding", "ResearchHarness", "ResearchResult"]
