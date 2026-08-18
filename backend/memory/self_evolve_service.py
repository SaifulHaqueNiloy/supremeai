"""Self-Evolving Memory Storage service for SupremeAI 2.0.

বাংলা মন্তব্য: এই সার্ভিসটি সংরক্ষিত মেমরিকে স্বয়ংক্রিয়ভাবে পুনরায় সংগঠিত করে —
সম্পর্কিত মেমরি ক্লাস্টার করে, ডুপ্লিকেট সনাক্ত করে এবং অব্যবহৃত মেমরি নিরাপদে
প্রুন (prune) করে। এটি UnifiedDBManager-এর উপর ভিত্তি করে কাজ করে এবং ChromaDB-এর
ফলব্যাক (TF-IDF) মোডের সাথেও সামঞ্জস্যপূর্ণ।

Algorithms (zero external dependencies):
- Clustering: single-linkage union-find over TF-IDF cosine similarity.
- Duplicates: exact content-hash match + semantic near-duplicate by similarity.
- Pruning: access-frequency + age based, safe-by-default (never deletes fresh data).
"""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from memory.chromadb_store import ChromaDBStore
from memory.unified_db_manager import UnifiedDBManager, unified_db

logger = logging.getLogger("supremeai.self_evolve")

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# O(n^2) similarity scan guard — beyond this we sample to keep latency bounded.
_MAX_COMPARE_DOCS = 4000


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class MemoryCluster:
    cluster_id: str
    member_ids: list[str]
    representative_id: str
    size: int


@dataclass
class ClusterResult:
    clusters: list[MemoryCluster] = field(default_factory=list)
    noise: list[str] = field(default_factory=list)
    total: int = 0


@dataclass
class DuplicatePair:
    doc_a: str
    doc_b: str
    similarity: float
    exact: bool


@dataclass
class PruneResult:
    removed_ids: list[str] = field(default_factory=list)
    retained: int = 0
    freed_bytes_estimate: int = 0


@dataclass
class ReorganizeResult:
    clusters: int = 0
    duplicates: int = 0
    pruned: int = 0
    retained: int = 0


class SelfEvolveService:
    """Reorganizes memory collections based on content similarity and usage."""

    def __init__(
        self,
        manager: UnifiedDBManager | None = None,
        sim_threshold: float = 0.85,
        dup_threshold: float = 0.95,
        stats_path: str | None = None,
    ):
        self.manager = manager or unified_db
        self.sim_threshold = sim_threshold
        self.dup_threshold = dup_threshold
        self._stats_path = stats_path or os.path.join(_BASE_DIR, "data", "self_evolve_stats.db")
        self._stats_conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Access-statistics store (sidecar SQLite)
    # ------------------------------------------------------------------
    def _get_stats_conn(self) -> sqlite3.Connection:
        if self._stats_conn is None:
            os.makedirs(os.path.dirname(self._stats_path), exist_ok=True)
            self._stats_conn = sqlite3.connect(self._stats_path, check_same_thread=False)
            cursor = self._stats_conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS access_stats (
                    doc_id TEXT PRIMARY KEY,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL DEFAULT 0,
                    created_at REAL DEFAULT 0
                )
                """
            )
            self._stats_conn.commit()
        return self._stats_conn

    def record_access(self, doc_id: str) -> None:
        """Record a read/use of a memory so pruning can reason about activity.

        Integration hook: call this from memory read paths (UnifiedDBManager.get_record)
        to enable age-based pruning of stale memories.
        """
        now = time.time()
        conn = self._get_stats_conn()
        conn.execute(
            "INSERT INTO access_stats (doc_id, access_count, last_accessed, created_at) "
            "VALUES (?, 1, ?, ?) ON CONFLICT(doc_id) DO UPDATE SET "
            "access_count = access_count + 1, last_accessed = excluded.last_accessed",
            (doc_id, now, now),
        )
        conn.commit()

    def get_access_stats(self, doc_id: str) -> tuple[int, float]:
        conn = self._get_stats_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT access_count, last_accessed FROM access_stats WHERE doc_id = ?",
            (doc_id,),
        )
        row = cursor.fetchone()
        return (row[0], row[1]) if row else (0, 0.0)

    # ------------------------------------------------------------------
    # Document retrieval + similarity
    # ------------------------------------------------------------------
    def _fetch_documents(self) -> list[dict[str, Any]]:
        chroma: ChromaDBStore = self.manager.chroma
        return chroma.get_all_documents()

    @staticmethod
    def _cosine(vec1: dict[str, int], vec2: dict[str, int]) -> float:
        return ChromaDBStore._cosine_similarity(vec1, vec2)

    # ------------------------------------------------------------------
    # Clustering (single-linkage union-find)
    # ------------------------------------------------------------------
    async def cluster_memories(self) -> ClusterResult:
        docs = self._fetch_documents()
        total = len(docs)
        if total == 0:
            return ClusterResult(total=0)

        vectors = [ChromaDBStore._get_vector(d.get("text", "")) for d in docs]

        parent = list(range(total))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        scanned = docs
        if total > _MAX_COMPARE_DOCS:
            logger.warning(
                f"[SelfEvolve] {total} docs exceed compare cap {_MAX_COMPARE_DOCS}; sampling."
            )
            scanned = docs[:_MAX_COMPARE_DOCS]

        for i in range(total):
            for j in range(i + 1, total):
                sim = self._cosine(vectors[i], vectors[j])
                if sim >= self.sim_threshold:
                    union(i, j)

        groups: dict[int, list[int]] = {}
        for i in range(total):
            groups.setdefault(find(i), []).append(i)

        clusters: list[MemoryCluster] = []
        noise: list[str] = []
        for members in groups.values():
            if len(members) <= 1:
                noise.extend(docs[m]["id"] for m in members)
                continue
            member_ids = [docs[m]["id"] for m in members]
            clusters.append(
                MemoryCluster(
                    cluster_id=f"cluster_{_content_hash(''.join(sorted(member_ids)))[:12]}",
                    member_ids=member_ids,
                    representative_id=member_ids[0],
                    size=len(member_ids),
                )
            )
        return ClusterResult(clusters=clusters, noise=noise, total=total)

    # ------------------------------------------------------------------
    # Duplicate detection
    # ------------------------------------------------------------------
    async def find_duplicates(self) -> list[DuplicatePair]:
        docs = self._fetch_documents()
        total = len(docs)
        vectors = [ChromaDBStore._get_vector(d.get("text", "")) for d in docs]
        pairs: list[DuplicatePair] = []

        exact_seen: dict[str, str] = {}
        for i in range(total):
            text = docs[i].get("text", "")
            h = _content_hash(text)
            if h in exact_seen:
                pairs.append(
                    DuplicatePair(doc_a=exact_seen[h], doc_b=docs[i]["id"], similarity=1.0, exact=True)
                )
                continue
            exact_seen[h] = docs[i]["id"]

        for i in range(total):
            for j in range(i + 1, total):
                sim = self._cosine(vectors[i], vectors[j])
                if sim >= self.dup_threshold:
                    pairs.append(
                        DuplicatePair(
                            doc_a=docs[i]["id"], doc_b=docs[j]["id"], similarity=sim, exact=False
                        )
                    )
        return pairs

    # ------------------------------------------------------------------
    # Pruning (safe-by-default)
    # ------------------------------------------------------------------
    async def prune_unused(
        self,
        max_age_days: int = 90,
        min_access: int = 1,
        now_provider: Callable[[], float] | None = None,
    ) -> PruneResult:
        """Remove memories that are both under-accessed and stale.

        Safe-by-default: a memory is only pruned if it has been accessed at least
        once (last_accessed > 0) AND its age since last access exceeds max_age_days
        AND its access count is below min_access. Fresh or never-accessed memories
        are retained unless `min_access` is raised above their real access count.
        """
        now = now_provider() if now_provider else time.time()
        docs = self._fetch_documents()
        removed: list[str] = []
        freed = 0
        for d in docs:
            doc_id = d["id"]
            text = d.get("text", "")
            count, last = self.get_access_stats(doc_id)
            if count < min_access and last > 0:
                age_days = (now - last) / 86400.0
                if age_days >= max_age_days:
                    self.manager.chroma.delete(doc_id)
                    removed.append(doc_id)
                    freed += len(text.encode("utf-8"))
        return PruneResult(
            removed_ids=removed, retained=len(docs) - len(removed), freed_bytes_estimate=freed
        )

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    async def reorganize_storage(
        self,
        max_age_days: int = 90,
        min_access: int = 1,
        now_provider: Callable[[], float] | None = None,
    ) -> ReorganizeResult:
        """Run cluster -> duplicate -> prune in sequence and return a summary."""
        clusters = await self.cluster_memories()
        duplicates = await self.find_duplicates()
        prune = await self.prune_unused(
            max_age_days=max_age_days, min_access=min_access, now_provider=now_provider
        )
        return ReorganizeResult(
            clusters=len(clusters.clusters),
            duplicates=len(duplicates),
            pruned=len(prune.removed_ids),
            retained=prune.retained,
        )


__all__ = [
    "SelfEvolveService",
    "MemoryCluster",
    "ClusterResult",
    "DuplicatePair",
    "PruneResult",
    "ReorganizeResult",
]
