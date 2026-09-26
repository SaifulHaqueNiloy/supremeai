"""
Optimized Vector Store for Free Tier
Reduces memory usage while maintaining search quality.
"""

import asyncio
import uuid
from datetime import UTC
from typing import Any

from supabase import create_client

from core.logging_config import logger


def _coerce_uuid(raw: str) -> str:
    """Return a valid UUID string for any id.

    M0.6 (roadmap M0.6 / PR #303 §10): the ai_memory PK is `id uuid`, but
    AutoRAG writers pass deterministic string ids like
    "user:session:<sha256[:24]>" — the upsert then fails with
    `invalid input syntax for type uuid` and (pre-fix) the exception block
    swallowed it as a debug log, so nothing persisted. uuid5 of the raw id
    keeps the dedupe semantics deterministic: same id -> same uuid.
    """
    try:
        return str(uuid.UUID(raw))
    except (ValueError, AttributeError, TypeError):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, str(raw)))


class FreeTierOptimizedVectorStore:
    """
    Vector store optimized for 512MB memory constraint.

    Strategies:
    1. Batch operations (reduce connection overhead)
    2. Streaming results (don't load all into memory)
    3. Aggressive index tuning
    4. Connection pooling with limits
    """

    BATCH_SIZE = 50  # Smaller batches for less memory
    MAX_RESULTS = 20  # Limit results to save memory
    # Canonical production contract is `ai_memory.embedding vector(384)`
    # (see models/ai_memory.EMBEDDING_DIMENSIONS and core/embeddings._PG_DIM,
    # both enforced by tests/models/test_ai_memory_schema_contract.py).
    # The old value here (1536, OpenAI ada-002) was stale and drifted from
    # every writer — any consumer using it would create dimension-mismatched
    # vectors that pgvector would reject.
    EMBEDDING_DIM = 384

    def __init__(self, supabase_url: str, supabase_key: str):
        self.client = create_client(supabase_url, supabase_key)
        self.table_name = "ai_memory"

        # Connection settings for low memory
        self._connection_pool_size = 2  # Very small pool for free tier

    async def upsert_batch(
        self, embeddings: list[list[float]], payloads: list[dict[str, Any]], ids: list[str]
    ) -> bool:
        """
        Upsert embeddings in small batches to manage memory.

        BUGFIX: supabase-py একটি **sync** ক্লায়েন্ট — আগে `await ...execute()`
        লেখা হচ্ছিল যা প্রতিবার TypeError করত (exc ব্লক তা চুপচাপ গিলে
        `False` ফেরত দিত — অর্থাৎ কোনো মেমরি কখনোই persist হতো না)।
        এখন sync কলগুলো `asyncio.to_thread`-এ পাঠানো হয়।
        """
        try:
            # Process in small batches
            for i in range(0, len(embeddings), self.BATCH_SIZE):
                batch_embeddings = embeddings[i : i + self.BATCH_SIZE]
                batch_payloads = payloads[i : i + self.BATCH_SIZE]
                batch_ids = ids[i : i + self.BATCH_SIZE]

                from datetime import datetime

                now_str = datetime.now(UTC).isoformat()
                records = [
                    {
                        "id": _coerce_uuid(bid),
                        "embedding": emb,
                        "metadata": payload,
                        "created_at": now_str,
                        # M0.6 (roadmap M0.6 / PR #303 §10): promote writer
                        # fields into their first-class columns. Previously
                        # they only lived inside the `metadata` JSONB blob:
                        # row-level queries, RLS scoping and retention cleanup
                        # never saw them (session_id/content effectively
                        # discarded). `metadata` is kept for recall fallback.
                        "content": payload.get("content", ""),
                        "user_id": payload.get("user_id"),
                        "session_id": payload.get("session_id") or "default",
                        "importance_score": payload.get("importance"),
                    }
                    for bid, emb, payload in zip(
                        batch_ids, batch_embeddings, batch_payloads, strict=True
                    )
                ]

                # Insert batch (sync supabase client → offload to worker thread)
                def _upsert(records=records) -> None:
                    self.client.table(self.table_name).upsert(records, on_conflict="id").execute()

                await asyncio.to_thread(_upsert)

                # Small delay to prevent overwhelming free tier DB
                await asyncio.sleep(0.05)

            return True

        except Exception as e:
            logger.debug(f"Batch upsert failed: {e}")
            return False

    async def similarity_search(
        self,
        query_embedding: list[float],
        user_id: str,
        limit: int = MAX_RESULTS,
        filter_metadata: dict | None = None,
    ) -> list[dict]:
        """
        Search with memory-efficient streaming.
        Uses RPC call for vector search (pgvector).

        AUDIT-FIX (#1689 CRITICAL): আগে `user_id: str | None = None` ছিল — যদি
        caller None পাস করত (বা ক্ষেত্র বাদ দিত), RPC match_memories-এ p_user_id
        পাস হতো না, ফলে Supabase সব user-এর record ফেরত দিত — cross-tenant
        data leak. এখন user_id required (positional, no default) এবং
        falsy মান (None/empty) হলে স্পষ্ট ValueError ফেরত দেয় — fail-closed।

        RLS (Row-Level Security) Supabase-এ আলাদাভাবে কনফিগার করা দরকার;
        এই PR application-level enforcement যোগ করে, DB-level RLS পরবর্তী
        migration-এ আসবে।
        """
        # AUDIT-FIX (#1689): Tenant isolation fail-closed guard.
        # কখনোই `None`/empty গ্রহণ করব না — এটাই প্রাথমিক leak vector ছিল।
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            raise ValueError(
                "similarity_search requires a non-empty user_id for tenant isolation "
                "(AUDIT-FIX #1689: cross-tenant data leak prevention). "
                "Pass an explicit user_id, or do not call similarity_search."
            )

        try:
            rpc_params: dict[str, Any] = {
                "query_embedding": query_embedding,
                "match_threshold": 0.7,
                "match_count": min(limit, self.MAX_RESULTS),
                "p_user_id": user_id,  # AUDIT-FIX (#1689): সর্বদা পাঠানো হয়
            }

            # Build query with filters
            query = self.client.rpc("match_memories", rpc_params)

            # Apply additional filters if provided
            if filter_metadata:
                for key, value in filter_metadata.items():
                    query = query.eq(f"metadata->>{key}", value)

            # Execute and get results (sync supabase client → offload to thread
            # যাতে ইভেন্ট লুপ ব্লক না হয়)
            result = await asyncio.to_thread(query.execute)

            # Return only what we need (don't cache large results)
            return [
                {
                    "id": r.get("id"),
                    "content": r.get("metadata", {}).get("content", "")[
                        :500
                    ],  # Truncate string to save memory
                    "score": r.get("similarity", 0),
                    "metadata": r.get("metadata", {}),
                }
                for r in (result.data or [])
            ]

        except Exception as e:
            logger.debug(f"Similarity search failed: {e}")
            return []

    async def delete_old_memories(self, days_old: int = 30, limit: int = 100):
        """Delete old memories to save space (free tier storage limit)."""
        try:
            from datetime import datetime, timedelta

            cutoff = (datetime.now(UTC) - timedelta(days=days_old)).isoformat()

            def _delete_old() -> None:
                (
                    self.client.table(self.table_name)
                    .filter(f"created_at.lt.{cutoff}")
                    .limit(limit)
                    .delete()
                    .execute()
                )

            await asyncio.to_thread(_delete_old)

            return True

        except Exception as e:
            logger.debug(f"Delete failed: {e}")
            return False
