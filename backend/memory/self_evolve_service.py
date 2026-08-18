"""Self-Evolving Memory Storage service for SupremeAI 2.0.

বাংলা মন্তব্য: এই সার্ভিসটি সংরক্ষিত মেমরিকে স্বয়ংক্রিয়ভাবে পুনরায় সংগঠিত করে —
সম্পর্কিত মেমরি ক্লাস্টার করে, ডুপ্লিকেট সনাক্ত করে এবং অব্যবহৃত মেমরি নিরাপদে
প্রুন (prune) করে। এটি UnifiedDBManager-এর উপর ভিত্তি করে কাজ করে এবং ChromaDB-এর
ফলব্যাক (TF-IDF) মোডের সাথেও সামঞ্জস্যপূর্ণ।

Algorithms (zero external dependencies):
- Clustering: single-linkage union-find over TF-IDF cosine similarity.
- Duplicates: exact content-hash match + semantic near-duplicate by similarity.
- Deduplication: near-duplicate groups merge into one synthesized memory (BLUEPRINT-MEM-001 §3.1).
- Decay: Ebbinghaus retention curve R = e^(-t/S) where stability S grows with
  access frequency and importance, so hot memories survive far longer than cold ones.
- Pruning: access-frequency + age based, safe-by-default (never deletes fresh data).
- Hierarchical retrieval: IVF-style cluster-centroid probe instead of full vector scan.
"""

from __future__ import annotations

import hashlib
import logging
import math
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

# Ebbinghaus decay defaults (BLUEPRINT-MEM-001 §3.1 / §3.2).
# S (stability) is expressed in days; a never-accessed memory decays on this base curve.
_DEFAULT_STABILITY_DAYS = 30.0
# Below this retention value a memory is considered forgotten and eligible for GC.
_DEFAULT_RETENTION_THRESHOLD = 0.15
# Absolute safety floor: nothing is decay-pruned before this age, whatever the score says.
_DEFAULT_MIN_DECAY_AGE_DAYS = 30
# Cap for synthesized (merged) memory text so repeated merges cannot grow unbounded.
_MAX_SYNTHESIZED_CHARS = 4000


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
    dry_run: bool = False
    scores: dict[str, float] = field(default_factory=dict)


@dataclass
class AccessRecord:
    """Usage telemetry for one memory, used by the decay evaluator."""

    doc_id: str
    access_count: int = 0
    last_accessed: float = 0.0
    created_at: float = 0.0
    importance_score: float = 1.0
    known: bool = False


@dataclass
class DecayScore:
    """Ebbinghaus retention snapshot: R = e^(-t/S)."""

    doc_id: str
    retention: float
    age_days: float
    stability_days: float
    access_count: int
    importance_score: float
    pinned: bool = False
    known: bool = False


@dataclass
class MergeGroup:
    survivor_id: str
    merged_ids: list[str]
    similarity: float


@dataclass
class MergeResult:
    """Outcome of semantic deduplication (near-duplicates collapsed into one memory)."""

    groups: list[MergeGroup] = field(default_factory=list)
    merged_ids: list[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def merged_count(self) -> int:
        return len(self.merged_ids)


@dataclass
class SearchMatch:
    doc_id: str
    score: float
    text: str
    cluster_id: str | None = None


@dataclass
class HierarchicalSearchResult:
    """Cluster-probe retrieval stats — proves the scan was narrowed, not full."""

    matches: list[SearchMatch] = field(default_factory=list)
    clusters_probed: int = 0
    clusters_total: int = 0
    docs_scanned: int = 0
    docs_total: int = 0
    fallback_full_scan: bool = False


@dataclass
class ReorganizeResult:
    clusters: int = 0
    duplicates: int = 0
    pruned: int = 0
    retained: int = 0
    merged: int = 0
    decay_pruned: int = 0
    clusters_persisted: int = 0
    duration_ms: float = 0.0


class SelfEvolveService:
    """Reorganizes memory collections based on content similarity and usage."""

    def __init__(
        self,
        manager: UnifiedDBManager | None = None,
        sim_threshold: float = 0.85,
        dup_threshold: float = 0.95,
        stats_path: str | None = None,
        stability_days: float = _DEFAULT_STABILITY_DAYS,
    ):
        self.manager = manager or unified_db
        self.sim_threshold = sim_threshold
        self.dup_threshold = dup_threshold
        self.stability_days = stability_days
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
            # বাংলা মন্তব্য: পুরনো DB-তে importance_score কলাম না থাকলে যোগ করা হয় (in-place migration)।
            cursor.execute("PRAGMA table_info(access_stats)")
            columns = {row[1] for row in cursor.fetchall()}
            if "importance_score" not in columns:
                cursor.execute(
                    "ALTER TABLE access_stats ADD COLUMN importance_score REAL DEFAULT 1.0"
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

    def register_memory(self, doc_id: str, importance_score: float = 1.0) -> None:
        """Register a newly written memory without counting it as an access.

        বাংলা মন্তব্য: ডিকে হিসাব করতে মেমরির জন্মসময় (created_at) দরকার। ইনজেশন পাথ
        থেকে এটি কল করলে কখনো-না-পড়া মেমরিও decay curve-এ ধরা পড়ে।
        """
        now = time.time()
        conn = self._get_stats_conn()
        conn.execute(
            "INSERT INTO access_stats (doc_id, access_count, last_accessed, created_at, "
            "importance_score) VALUES (?, 0, 0, ?, ?) ON CONFLICT(doc_id) DO UPDATE SET "
            "importance_score = excluded.importance_score",
            (doc_id, now, importance_score),
        )
        conn.commit()

    def set_importance(self, doc_id: str, importance_score: float) -> None:
        """Set the importance weight that stretches a memory's decay stability."""
        now = time.time()
        conn = self._get_stats_conn()
        conn.execute(
            "INSERT INTO access_stats (doc_id, access_count, last_accessed, created_at, "
            "importance_score) VALUES (?, 0, 0, ?, ?) ON CONFLICT(doc_id) DO UPDATE SET "
            "importance_score = excluded.importance_score",
            (doc_id, now, importance_score),
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

    def get_access_record(self, doc_id: str) -> AccessRecord:
        """Full usage telemetry for one memory (returns known=False when untracked)."""
        conn = self._get_stats_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT access_count, last_accessed, created_at, importance_score "
            "FROM access_stats WHERE doc_id = ?",
            (doc_id,),
        )
        row = cursor.fetchone()
        if not row:
            return AccessRecord(doc_id=doc_id, known=False)
        return AccessRecord(
            doc_id=doc_id,
            access_count=int(row[0] or 0),
            last_accessed=float(row[1] or 0.0),
            created_at=float(row[2] or 0.0),
            importance_score=float(row[3] if row[3] is not None else 1.0),
            known=True,
        )

    def _merge_access_stats(self, survivor_id: str, absorbed_ids: list[str]) -> None:
        """Fold absorbed memories' usage telemetry into the survivor, then drop them."""
        if not absorbed_ids:
            return
        survivor = self.get_access_record(survivor_id)
        total_count = survivor.access_count
        last = survivor.last_accessed
        created = survivor.created_at
        importance = survivor.importance_score
        for doc_id in absorbed_ids:
            record = self.get_access_record(doc_id)
            total_count += record.access_count
            last = max(last, record.last_accessed)
            if record.created_at > 0:
                created = record.created_at if created <= 0 else min(created, record.created_at)
            importance = max(importance, record.importance_score)
        conn = self._get_stats_conn()
        conn.execute(
            "INSERT INTO access_stats (doc_id, access_count, last_accessed, created_at, "
            "importance_score) VALUES (?, ?, ?, ?, ?) ON CONFLICT(doc_id) DO UPDATE SET "
            "access_count = excluded.access_count, last_accessed = excluded.last_accessed, "
            "created_at = excluded.created_at, importance_score = excluded.importance_score",
            (survivor_id, total_count, last, created or time.time(), importance),
        )
        conn.executemany(
            "DELETE FROM access_stats WHERE doc_id = ?", [(d,) for d in absorbed_ids]
        )
        conn.commit()

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

        scanned = total
        if total > _MAX_COMPARE_DOCS:
            logger.warning(
                f"[SelfEvolve] {total} docs exceed compare cap {_MAX_COMPARE_DOCS}; sampling."
            )
            # বাংলা মন্তব্য: BUGFIX — আগে `scanned` হিসাব হলেও লুপে ব্যবহার হতো না, ফলে
            # O(n^2) গার্ড কার্যকর ছিল না। এখন cap-এর বাইরের ডকগুলো noise হিসেবে যায়।
            scanned = _MAX_COMPARE_DOCS

        for i in range(scanned):
            for j in range(i + 1, scanned):
                sim = self._cosine(vectors[i], vectors[j])
                if sim >= self.sim_threshold:
                    union(i, j)

        groups: dict[int, list[int]] = {}
        for i in range(scanned):
            groups.setdefault(find(i), []).append(i)

        clusters: list[MemoryCluster] = []
        noise: list[str] = [docs[i]["id"] for i in range(scanned, total)]
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

    async def assign_cluster_ids(self) -> dict[str, str]:
        """Persist each memory's cluster_id into store metadata (hierarchical retrieval).

        বাংলা মন্তব্য: BLUEPRINT-MEM-001 §৩.২ অনুযায়ী cluster_id মেটাডাটায় লিখে রাখা হয়,
        যাতে রিট্রিভাল পুরো ভেক্টর স্পেস স্ক্যান না করে শুধু প্রাসঙ্গিক ক্লাস্টার প্রোব করে।
        Returns a mapping of doc_id -> cluster_id for every clustered memory.
        """
        result = await self.cluster_memories()
        docs = {d["id"]: d for d in self._fetch_documents()}
        assignments: dict[str, str] = {}
        for cluster in result.clusters:
            for doc_id in cluster.member_ids:
                doc = docs.get(doc_id)
                if doc is None:
                    continue
                metadata = dict(doc.get("metadata") or {})
                if (
                    metadata.get("cluster_id") == cluster.cluster_id
                    and metadata.get("cluster_size") == cluster.size
                ):
                    assignments[doc_id] = cluster.cluster_id
                    continue
                metadata["cluster_id"] = cluster.cluster_id
                metadata["cluster_size"] = cluster.size
                metadata["is_cluster_head"] = doc_id == cluster.representative_id
                try:
                    self.manager.chroma.add_document(
                        doc_id=doc_id, text=doc.get("text", ""), metadata=metadata
                    )
                    # M5.1 Production Bridge: Sync cluster_id and is_synthesized to ai_memory in Postgres
                    from core.persistence import pooled_pg
                    if pooled_pg.is_available():
                        is_head = (doc_id == cluster.representative_id)
                        pooled_pg.execute(
                            "UPDATE ai_memory SET cluster_id = %s, is_synthesized = %s WHERE id::text = %s",
                            (cluster.cluster_id, is_head, doc_id)
                        )
                    assignments[doc_id] = cluster.cluster_id
                except Exception as exc:  # pragma: no cover - store-specific failure
                    logger.warning(f"[SelfEvolve] cluster_id persist failed for {doc_id}: {exc}")
        return assignments

    # ------------------------------------------------------------------
    # Hierarchical retrieval (IVF-style cluster probe)
    # ------------------------------------------------------------------
    async def hierarchical_search(
        self, query: str, n_results: int = 5, cluster_probe: int = 3
    ) -> HierarchicalSearchResult:
        """Search cluster centroids first, then only inside the closest clusters.

        Unclustered memories are treated as single-member clusters, so recall is
        preserved while the scanned vector count stays far below the full corpus.
        """
        docs = self._fetch_documents()
        total = len(docs)
        if total == 0:
            return HierarchicalSearchResult()

        query_vector = ChromaDBStore._get_vector(query)
        buckets: dict[str, list[dict[str, Any]]] = {}
        for doc in docs:
            metadata = doc.get("metadata") or {}
            cluster_id = metadata.get("cluster_id") or f"solo::{doc['id']}"
            buckets.setdefault(cluster_id, []).append(doc)

        centroids: dict[str, dict[str, float]] = {}
        for cluster_id, members in buckets.items():
            centroid: dict[str, float] = {}
            for member in members:
                for token, count in ChromaDBStore._get_vector(member.get("text", "")).items():
                    centroid[token] = centroid.get(token, 0) + count
            centroids[cluster_id] = centroid

        ranked = sorted(
            centroids.items(),
            key=lambda item: self._cosine(query_vector, item[1]),  # type: ignore[arg-type]
            reverse=True,
        )
        probe = max(1, cluster_probe)
        probed = [cluster_id for cluster_id, _ in ranked[:probe]]

        matches: list[SearchMatch] = []
        scanned = 0
        for cluster_id in probed:
            for doc in buckets[cluster_id]:
                scanned += 1
                score = self._cosine(
                    query_vector, ChromaDBStore._get_vector(doc.get("text", ""))
                )
                matches.append(
                    SearchMatch(
                        doc_id=doc["id"],
                        score=score,
                        text=doc.get("text", ""),
                        cluster_id=(doc.get("metadata") or {}).get("cluster_id"),
                    )
                )
        matches.sort(key=lambda m: m.score, reverse=True)
        return HierarchicalSearchResult(
            matches=matches[:n_results],
            clusters_probed=len(probed),
            clusters_total=len(buckets),
            docs_scanned=scanned,
            docs_total=total,
            fallback_full_scan=scanned >= total,
        )

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
    # Semantic deduplication (merge near-duplicates into one memory)
    # ------------------------------------------------------------------
    @staticmethod
    def _synthesize_text(texts: list[str]) -> str:
        """Union of unique sentences across duplicates, order-preserving and length-capped.

        বাংলা মন্তব্য: LLM ছাড়াই ($0) সিন্থেসিস — প্রতিটি ডুপ্লিকেট থেকে শুধু নতুন
        বাক্যগুলো যোগ হয়, ফলে তথ্য না হারিয়ে একটি একক মেমরি তৈরি হয়।
        """
        seen: set[str] = set()
        sentences: list[str] = []
        for text in texts:
            for raw_line in text.replace(". ", ".\n").splitlines():
                sentence = raw_line.strip()
                if not sentence:
                    continue
                key = " ".join(sentence.lower().split())
                if key in seen:
                    continue
                seen.add(key)
                sentences.append(sentence)
        merged = "\n".join(sentences)
        if len(merged) > _MAX_SYNTHESIZED_CHARS:
            merged = merged[:_MAX_SYNTHESIZED_CHARS].rstrip()
        return merged

    async def deduplicate_memories(
        self, threshold: float | None = None, dry_run: bool = False
    ) -> MergeResult:
        """Collapse near-duplicate memories (>= threshold) into one synthesized memory.

        The survivor keeps its original id (so existing references stay valid), absorbs
        the other texts' unique sentences, and inherits their access statistics. Absorbed
        duplicates are deleted from the vector store.
        """
        cutoff = self.dup_threshold if threshold is None else threshold
        docs = self._fetch_documents()
        total = len(docs)
        if total < 2:
            return MergeResult(dry_run=dry_run)

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

        scanned = min(total, _MAX_COMPARE_DOCS)
        # Exact content-hash duplicates first (cheap), then semantic near-duplicates.
        by_hash: dict[str, int] = {}
        for i in range(scanned):
            h = _content_hash(docs[i].get("text", ""))
            if h in by_hash:
                union(by_hash[h], i)
            else:
                by_hash[h] = i
        for i in range(scanned):
            for j in range(i + 1, scanned):
                if self._cosine(vectors[i], vectors[j]) >= cutoff:
                    union(i, j)

        groups: dict[int, list[int]] = {}
        for i in range(scanned):
            groups.setdefault(find(i), []).append(i)

        result = MergeResult(dry_run=dry_run)
        for members in groups.values():
            if len(members) < 2:
                continue
            # Report the strongest pairwise similarity inside the group. Computed after
            # grouping because union-find roots shift while unions are being applied.
            similarity = max(
                self._cosine(vectors[a], vectors[b])
                for idx, a in enumerate(members)
                for b in members[idx + 1 :]
            )
            # Survivor: most-accessed, then longest text, then lowest id (deterministic).
            ranked = sorted(
                members,
                key=lambda idx: (
                    -self.get_access_record(docs[idx]["id"]).access_count,
                    -len(docs[idx].get("text", "")),
                    docs[idx]["id"],
                ),
            )
            survivor_idx = ranked[0]
            survivor_id = docs[survivor_idx]["id"]
            absorbed = [docs[idx]["id"] for idx in ranked[1:]]
            result.groups.append(
                MergeGroup(
                    survivor_id=survivor_id, merged_ids=absorbed, similarity=round(similarity, 4)
                )
            )
            if dry_run:
                continue

            synthesized = self._synthesize_text([docs[idx].get("text", "") for idx in ranked])
            metadata = dict(docs[survivor_idx].get("metadata") or {})
            previously_merged = str(metadata.get("merged_from") or "")
            merged_from = [x for x in previously_merged.split(",") if x] + absorbed
            metadata["is_synthesized"] = True
            # ChromaDB metadata values must be scalars — store the id list as a CSV string.
            metadata["merged_from"] = ",".join(merged_from)
            metadata["merged_count"] = len(merged_from)
            metadata["merged_at"] = time.time()
            try:
                self.manager.chroma.add_document(
                    doc_id=survivor_id, text=synthesized, metadata=metadata
                )
                for doc_id in absorbed:
                    self.manager.chroma.delete(doc_id)
                self._merge_access_stats(survivor_id, absorbed)
                result.merged_ids.extend(absorbed)
            except Exception as exc:  # pragma: no cover - store-specific failure
                logger.warning(f"[SelfEvolve] merge failed for group {survivor_id}: {exc}")
        return result

    # ------------------------------------------------------------------
    # Decay evaluation (Ebbinghaus retention curve)
    # ------------------------------------------------------------------
    def retention_score(
        self,
        doc_id: str,
        now: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DecayScore:
        """Compute R = e^(-t/S) for one memory.

        t = days since last access (or creation if never accessed).
        S = stability_days * (1 + ln(1 + access_count)) * importance_score, so each
        additional read and every importance bump flattens the forgetting curve.
        Untracked memories return retention 1.0 (safe-by-default: never auto-pruned).
        """
        now = time.time() if now is None else now
        record = self.get_access_record(doc_id)
        meta = metadata or {}
        pinned = bool(meta.get("pinned"))
        reference = record.last_accessed or record.created_at
        importance = max(record.importance_score, 0.1)
        stability = self.stability_days * (1.0 + math.log1p(max(record.access_count, 0))) * importance
        if not record.known or reference <= 0:
            return DecayScore(
                doc_id=doc_id,
                retention=1.0,
                age_days=0.0,
                stability_days=stability,
                access_count=record.access_count,
                importance_score=importance,
                pinned=pinned,
                known=record.known,
            )
        age_days = max((now - reference) / 86400.0, 0.0)
        retention = math.exp(-age_days / stability) if stability > 0 else 0.0
        return DecayScore(
            doc_id=doc_id,
            retention=retention,
            age_days=age_days,
            stability_days=stability,
            access_count=record.access_count,
            importance_score=importance,
            pinned=pinned,
            known=True,
        )

    async def decay_report(
        self, now_provider: Callable[[], float] | None = None, limit: int = 50
    ) -> list[DecayScore]:
        """Weakest-retention memories first — the GC candidate queue."""
        now = now_provider() if now_provider else time.time()
        scores = [
            self.retention_score(d["id"], now=now, metadata=d.get("metadata"))
            for d in self._fetch_documents()
        ]
        scores.sort(key=lambda s: s.retention)
        return scores[:limit]

    async def prune_decayed_memories(
        self,
        retention_threshold: float = _DEFAULT_RETENTION_THRESHOLD,
        min_age_days: int = _DEFAULT_MIN_DECAY_AGE_DAYS,
        dry_run: bool = False,
        now_provider: Callable[[], float] | None = None,
    ) -> PruneResult:
        """Garbage-collect forgotten memories using the Ebbinghaus curve.

        A memory is removed only when ALL hold:
        1. retention R < retention_threshold,
        2. age since last touch >= min_age_days (hard safety floor),
        3. it is not pinned and not an untracked/unknown memory.
        """
        now = now_provider() if now_provider else time.time()
        docs = self._fetch_documents()
        removed: list[str] = []
        scores: dict[str, float] = {}
        freed = 0
        for doc in docs:
            doc_id = doc["id"]
            score = self.retention_score(doc_id, now=now, metadata=doc.get("metadata"))
            scores[doc_id] = round(score.retention, 6)
            if score.pinned or not score.known:
                continue
            if score.retention >= retention_threshold or score.age_days < min_age_days:
                continue
            if dry_run:
                removed.append(doc_id)
                freed += len(doc.get("text", "").encode("utf-8"))
                continue
            try:
                self.manager.chroma.delete(doc_id)
                removed.append(doc_id)
                freed += len(doc.get("text", "").encode("utf-8"))
            except Exception as exc:  # pragma: no cover - store-specific failure
                logger.warning(f"[SelfEvolve] decay prune failed for {doc_id}: {exc}")
        return PruneResult(
            removed_ids=removed,
            retained=len(docs) - len(removed),
            freed_bytes_estimate=freed,
            dry_run=dry_run,
            scores=scores,
        )

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
        merge_duplicates: bool = False,
        apply_decay: bool = False,
        persist_clusters: bool = False,
        retention_threshold: float = _DEFAULT_RETENTION_THRESHOLD,
        min_decay_age_days: int = _DEFAULT_MIN_DECAY_AGE_DAYS,
    ) -> ReorganizeResult:
        """Run the full self-evolution cycle and return a summary.

        Destructive stages (merge_duplicates / apply_decay) are opt-in so an
        inspection call can never mutate memory; `MemoryEvolutionLoop` turns them on.
        """
        started = time.perf_counter()
        clusters = await self.cluster_memories()
        duplicates = await self.find_duplicates()

        merged = 0
        if merge_duplicates:
            merge_result = await self.deduplicate_memories()
            merged = merge_result.merged_count

        persisted = 0
        if persist_clusters:
            persisted = len(await self.assign_cluster_ids())

        decay_pruned = 0
        if apply_decay:
            decay_result = await self.prune_decayed_memories(
                retention_threshold=retention_threshold,
                min_age_days=min_decay_age_days,
                now_provider=now_provider,
            )
            decay_pruned = len(decay_result.removed_ids)

        prune = await self.prune_unused(
            max_age_days=max_age_days, min_access=min_access, now_provider=now_provider
        )
        return ReorganizeResult(
            clusters=len(clusters.clusters),
            duplicates=len(duplicates),
            pruned=len(prune.removed_ids),
            retained=prune.retained,
            merged=merged,
            decay_pruned=decay_pruned,
            clusters_persisted=persisted,
            duration_ms=round((time.perf_counter() - started) * 1000, 3),
        )


__all__ = [
    "AccessRecord",
    "ClusterResult",
    "DecayScore",
    "DuplicatePair",
    "HierarchicalSearchResult",
    "MemoryCluster",
    "MergeGroup",
    "MergeResult",
    "PruneResult",
    "ReorganizeResult",
    "SearchMatch",
    "SelfEvolveService",
]
