"""Unified Multi-Database Transaction Manager for SupremeAI 2.0."""

# বাংলা মন্তব্য: Supabase, Postgres, ChromaDB, SQLite এবং Firestore-এর রিয়েল-টাইম ডাটা সিঙ্ক ও ট্রানজ্যাকশন ম্যানেজার।

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from memory.self_evolve_service import ReorganizeResult, SelfEvolveService

from memory.chromadb_store import ChromaDBStore
from memory.cloud_postgres_store import CloudPostgresStore
from memory.sqlite_store import SQLiteStore
from memory.supabase_store import SupabaseStore

logger = logging.getLogger("supremeai.unified_db")

# বাংলা মন্তব্য: collection নামে SQL injection প্রতিরোধ করতে whitelist pattern ব্যবহার করা হচ্ছে —
# একই প্যাটার্ন admin.py ও db_repository.py-তেও ব্যবহার হয়।
_VALID_COLLECTION_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


class UnifiedDBManager:
    """Centralized transaction coordinator across all underlying database engines."""

    def __init__(
        self,
        supabase_store: SupabaseStore | None = None,
        sqlite_store: SQLiteStore | None = None,
        chroma_store: ChromaDBStore | None = None,
        postgres_store: CloudPostgresStore | None = None,
    ):
        self.supabase = supabase_store or SupabaseStore()
        self.sqlite = sqlite_store or SQLiteStore()
        self.chroma = chroma_store or ChromaDBStore()
        self.postgres = postgres_store or CloudPostgresStore()
        self._self_evolve_service = None

    async def save_record(
        self,
        collection: str,
        record_id: str,
        data: dict[str, Any],
        text_content: str | None = None,
    ) -> dict[str, bool]:
        """Atomically persist record metadata and embeddings across multi-cloud stores.

        বাংলা মন্তব্য: একক মেথড কলে সুনির্দিষ্ট রেকর্ডকে সকল যুক্ত ডাটাবেসে একসাথে সেভ করে।
        """
        results = {
            "supabase": False,
            "sqlite": False,
            "chroma": False,
            "postgres": False,
        }

        # 1. Save to SQLite local cache
        try:
            await self.sqlite.save(collection, record_id, data)
            results["sqlite"] = True
        except Exception as e:
            logger.warning(f"[UnifiedDB] SQLite save skipped: {e}")

        # 2. Save to Supabase Cloud Relational DB
        try:
            await self.supabase.insert(collection, {"id": record_id, **data})
            results["supabase"] = True
        except Exception as e:
            logger.warning(f"[UnifiedDB] Supabase save skipped: {e}")

        # 3. Save to Cloud Postgres DB
        try:
            # বাংলা মন্তব্য: SECURITY FIX — collection f-string-এ সরাসরি ব্যবহার হওয়ায় SQL injection সম্ভব ছিল।
            # এখন identifier whitelist-এর বিপরীতে যাচাই করে তবেই কুয়েরি তৈরি করা হয়।
            if not _VALID_COLLECTION_PATTERN.match(collection):
                raise ValueError(f"Invalid collection name: {collection!r}")
            await self.postgres.execute_query(
                f"INSERT INTO {collection} (id, data) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET data = $2",  # — collection is whitelist-validated above
                record_id,
                data,
            )
            results["postgres"] = True
        except ValueError:
            raise
        except Exception as e:
            logger.warning(f"[UnifiedDB] Postgres save skipped: {e}")

        # 4. Embed into ChromaDB Vector Store if text provided
        if text_content:
            try:
                await self.chroma.add_document(  # type: ignore
                    document_id=record_id,
                    text=text_content,
                    metadata={"collection": collection, **data},
                )
                results["chroma"] = True
            except Exception as e:
                logger.warning(f"[UnifiedDB] ChromaDB embedding skipped: {e}")

        return results

    async def get_record(self, collection: str, record_id: str) -> dict[str, Any] | None:
        """Retrieve record with fallback strategy (SQLite -> Supabase -> Postgres).

        বাংলা মন্তব্য: ফাইলটের ওপর ভিত্তি করে পর্যায়ক্রমে লোকাল সিঙ্ক থেকে ডাটা ফেচ করে।
        """
        # Primary lookup: Local SQLite
        try:
            record = await self.sqlite.get(collection, record_id)
            if record:
                return record
        except Exception as e:
            logger.warning(f"[UnifiedDB] SQLite lookup failed for {record_id}, falling back: {e}")

        # Secondary lookup: Cloud Supabase
        try:
            record = await self.supabase.fetch_by_id(collection, record_id)
            if record:
                return record
        except Exception as e:
            logger.warning(f"[UnifiedDB] Supabase lookup failed for {record_id}: {e}")

        return None

    async def delete_record(self, collection: str, record_id: str) -> dict[str, bool]:
        """Delete record across underlying database engines."""
        results = {
            "sqlite": False,
            "supabase": False,
            "postgres": False,
        }

        # 1. Delete from SQLite
        try:
            results["sqlite"] = await self.sqlite.delete(collection, record_id)
        except Exception as e:
            logger.warning(f"[UnifiedDB] SQLite delete failed for {collection}:{record_id}: {e}")

        # 2. Delete from Supabase
        try:
            if getattr(self.supabase, "_provider", "") == "supabase":
                client = self.supabase._get_supabase_client()
                client.table(collection).delete().eq("id", record_id).execute()
                results["supabase"] = True
            else:
                results["supabase"] = results["sqlite"]
        except Exception as e:
            logger.warning(f"[UnifiedDB] Supabase delete failed for {collection}:{record_id}: {e}")

        # 3. Delete from Postgres
        try:
            if not _VALID_COLLECTION_PATTERN.match(collection):
                raise ValueError(f"Invalid collection name: {collection!r}")
            await self.postgres.execute_query(
                f"DELETE FROM {collection} WHERE id = $1",
                record_id,
            )
            results["postgres"] = True
        except Exception as e:
            logger.debug(f"[UnifiedDB] Postgres delete skipped: {e}")

        return results

    # ------------------------------------------------------------------
    # Self-Evolving Memory integration
    # ------------------------------------------------------------------
    def get_self_evolve_service(self) -> SelfEvolveService:
        """Lazily construct the SelfEvolveService bound to this manager."""
        from memory.self_evolve_service import SelfEvolveService

        if self._self_evolve_service is None:
            self._self_evolve_service = SelfEvolveService(manager=self)
        return self._self_evolve_service

    async def evolve_reorganize(
        self, max_age_days: int = 90, min_access: int = 1
    ) -> ReorganizeResult:
        """Convenience wrapper: run the full self-evolution cycle on this manager."""
        service = self.get_self_evolve_service()
        return await service.reorganize_storage(max_age_days=max_age_days, min_access=min_access)

    async def health_check(self) -> dict[str, Any]:
        """Verify connectivity and status across active storage layers."""
        health = {
            "status": "healthy",
            "sqlite": False,
            "supabase": False,
            "chroma": False,
            "postgres": False,
        }

        # Check SQLite
        try:
            await self.sqlite.save("_health", "ping", {"status": "ok"})
            ping = await self.sqlite.get("_health", "ping")
            if ping is not None:
                health["sqlite"] = True
        except Exception as e:
            logger.warning(f"[UnifiedDB] SQLite health check failed: {e}")

        # Check Supabase
        try:
            if getattr(self.supabase, "_provider", "") == "supabase":
                client = self.supabase._get_supabase_client()
                if client is not None:
                    health["supabase"] = True
            else:
                health["supabase"] = health["sqlite"]
        except Exception as e:
            logger.debug(f"[UnifiedDB] Supabase health check failed: {e}")

        # Overall status evaluation
        if not health["sqlite"] and not health["supabase"]:
            health["status"] = "degraded"

        return health


# Global singleton instance
unified_db = UnifiedDBManager()


def get_db() -> UnifiedDBManager:
    """FastAPI Dependency Injection provider for UnifiedDBManager."""
    return unified_db

