"""Opt-in, tenant-scoped memory context injection."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


class MemoryRetriever(Protocol):
    def search(self, *, tenant_id: str, query: str, limit: int) -> Sequence[str]: ...


@dataclass(frozen=True)
class MemoryInjectionPolicy:
    enabled: bool = False
    limit: int = 5
    max_chars: int = 4000


class AutoRAGInjector:
    def __init__(self, retriever: MemoryRetriever) -> None:
        self.retriever = retriever

    def inject(self, *, tenant_id: str, prompt: str, policy: MemoryInjectionPolicy) -> str:
        if not policy.enabled:
            return prompt
        memories = self.retriever.search(tenant_id=tenant_id, query=prompt, limit=max(0, min(policy.limit, 20)))
        context = "\n".join(f"- {memory}" for memory in memories)[: max(0, policy.max_chars)]
        if not context:
            return prompt
        return f"Relevant approved memory (tenant-scoped):\n{context}\n\nUser request:\n{prompt}"


__all__ = ["AutoRAGInjector", "MemoryInjectionPolicy", "MemoryRetriever"]
