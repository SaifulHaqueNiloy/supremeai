"""backend/workers/synaptic_dream.py — Synaptic Memory Dream Cycle Worker.

Governs Memory Consolidation:
- Prunes transient, low-importance ai_memory rows past the retention horizon.
- Reports honest counts (issue #440 doctrine: real work or loud failure — the
  previous implementation returned hardcoded pruned=5 / consolidated=2 without
  touching any store).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from core.logging_config import logger


class DreamCycleReport(BaseModel):
    pruned_count: int = 0
    consolidated_count: int = 0
    duration_ms: float = 0.0
    status: str = "completed"
    message: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class SynapticDreamWorker:
    """Scheduled memory hygiene and consolidation engine."""

    # Rows with importance below this are treated as transient.
    PRUNE_IMPORTANCE_THRESHOLD = 0.2

    def __init__(self, vector_store: Any = None) -> None:
        self.vector_store = vector_store

    async def execute_dream_cycle(
        self,
        tenant_id: str | None = None,
        retention_days: int = 30,
    ) -> DreamCycleReport:
        start_time = time.perf_counter()
        logger.info(f"[SynapticDream] Starting memory dream cycle for tenant={tenant_id or 'all'}")

        pruned = 0
        consolidated = 0
        message = ""

        try:
            cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

            # 1. REAL prune: delete low-importance ai_memory rows past the
            #    retention horizon via the Supabase service client.
            try:
                from database.supabase_client import db

                result = (
                    db.client.table("ai_memory")
                    .delete()
                    .lt("importance_score", self.PRUNE_IMPORTANCE_THRESHOLD)
                    .lt("created_at", cutoff_date.isoformat())
                    .select("id")
                    .execute()
                )
                pruned = len(result.data or [])
                logger.info(
                    f"[SynapticDream] Pruned {pruned} transient records "
                    f"(importance<{self.PRUNE_IMPORTANCE_THRESHOLD}, older than {cutoff_date.date()})"
                )
            except Exception as store_exc:
                # Honest degradation — never invent a count.
                logger.error(f"[SynapticDream] prune store unavailable: {store_exc}")
                return DreamCycleReport(
                    pruned_count=0,
                    consolidated_count=0,
                    duration_ms=(time.perf_counter() - start_time) * 1000.0,
                    status="degraded_no_store",
                    message=f"Memory store unavailable — nothing pruned ({store_exc!r})",
                )

            # 2. Episodic→durable consolidation has no real pass yet. The old
            #    code faked "consolidated=2" every cycle; report 0 honestly
            #    until a real consolidation pass exists.
            consolidated = 0
            message = "episodic consolidation not implemented yet — real prune counts only"

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DreamCycleReport(
                pruned_count=pruned,
                consolidated_count=consolidated,
                duration_ms=elapsed_ms,
                status="completed",
                message=message,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"[SynapticDream] Dream cycle failed: {exc}", exc_info=True)
            return DreamCycleReport(
                pruned_count=pruned,
                consolidated_count=consolidated,
                duration_ms=elapsed_ms,
                status=f"failed: {exc}",
            )


synaptic_dream_worker = SynapticDreamWorker()
