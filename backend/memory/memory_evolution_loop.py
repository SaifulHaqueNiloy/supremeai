"""Autonomous Self-Evolving Memory loop (BLUEPRINT-MEM-001, Phase 5 / M5.1).

বাংলা মন্তব্য: এই লুপটি ব্যাকগ্রাউন্ডে নির্দিষ্ট বিরতিতে মেমরি স্টোর পুনর্গঠন করে —
সেম্যান্টিক ক্লাস্টার তৈরি ও persist করে, near-duplicate মেমরি মার্জ করে এবং
Ebbinghaus decay অনুযায়ী "ভুলে যাওয়া" মেমরি garbage-collect করে। পুরোটাই $0 —
কোনো external scheduler বা LLM কল ছাড়াই AgentSupervisor-এর অধীনে চলে।

Safety model:
- Off by default; enabled with `ENABLE_MEMORY_EVOLUTION=true`.
- `dry_run=True` reports what *would* change without deleting anything.
- One cycle at a time (no overlap), and a failed cycle never kills the loop.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from memory.self_evolve_service import (
    _DEFAULT_MIN_DECAY_AGE_DAYS,
    _DEFAULT_RETENTION_THRESHOLD,
    ReorganizeResult,
    SelfEvolveService,
)

logger = logging.getLogger("supremeai.memory_evolution")

# Default cadence: hourly. Memory reorganization is O(n^2) on similarity, so it must
# not run more often than the corpus realistically changes.
_DEFAULT_INTERVAL_SECONDS = 3600
_MIN_INTERVAL_SECONDS = 30


def _env_flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        logger.warning(f"[MemoryEvolution] invalid int for {name}; using default {default}")
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        logger.warning(f"[MemoryEvolution] invalid float for {name}; using default {default}")
        return default


@dataclass
class EvolutionLoopStats:
    """Observable counters for the auto-loop (surfaced over the admin API)."""

    cycles: int = 0
    failures: int = 0
    total_merged: int = 0
    total_decay_pruned: int = 0
    total_pruned: int = 0
    clusters_last_cycle: int = 0
    last_run_at: float | None = None
    last_duration_ms: float = 0.0
    last_error: str | None = None
    last_result: dict[str, Any] = field(default_factory=dict)


class MemoryEvolutionLoop:
    """Schedules `SelfEvolveService.reorganize_storage` as an autonomous background loop."""

    def __init__(
        self,
        service: SelfEvolveService | None = None,
        interval_seconds: int = _DEFAULT_INTERVAL_SECONDS,
        merge_duplicates: bool = True,
        apply_decay: bool = True,
        persist_clusters: bool = True,
        retention_threshold: float = _DEFAULT_RETENTION_THRESHOLD,
        min_decay_age_days: int = _DEFAULT_MIN_DECAY_AGE_DAYS,
        max_age_days: int = 90,
        min_access: int = 1,
        dry_run: bool = False,
    ):
        self._service = service
        self.interval_seconds = max(_MIN_INTERVAL_SECONDS, int(interval_seconds))
        self.merge_duplicates = merge_duplicates
        self.apply_decay = apply_decay
        self.persist_clusters = persist_clusters
        self.retention_threshold = retention_threshold
        self.min_decay_age_days = min_decay_age_days
        self.max_age_days = max_age_days
        self.min_access = min_access
        self.dry_run = dry_run
        self.stats = EvolutionLoopStats()
        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None
        self._cycle_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    @property
    def service(self) -> SelfEvolveService:
        if self._service is None:
            from memory.unified_db_manager import unified_db

            self._service = unified_db.get_self_evolve_service()
        return self._service

    @classmethod
    def from_env(cls, service: SelfEvolveService | None = None) -> MemoryEvolutionLoop:
        """Build a loop from environment configuration (all knobs optional)."""
        return cls(
            service=service,
            interval_seconds=_env_int("MEMORY_EVOLUTION_INTERVAL_SECONDS", _DEFAULT_INTERVAL_SECONDS),
            merge_duplicates=_env_flag("MEMORY_EVOLUTION_MERGE_DUPLICATES", True),
            apply_decay=_env_flag("MEMORY_EVOLUTION_APPLY_DECAY", True),
            persist_clusters=_env_flag("MEMORY_EVOLUTION_PERSIST_CLUSTERS", True),
            retention_threshold=_env_float(
                "MEMORY_EVOLUTION_RETENTION_THRESHOLD", _DEFAULT_RETENTION_THRESHOLD
            ),
            min_decay_age_days=_env_int(
                "MEMORY_EVOLUTION_MIN_DECAY_AGE_DAYS", _DEFAULT_MIN_DECAY_AGE_DAYS
            ),
            max_age_days=_env_int("MEMORY_EVOLUTION_MAX_AGE_DAYS", 90),
            min_access=_env_int("MEMORY_EVOLUTION_MIN_ACCESS", 1),
            dry_run=_env_flag("MEMORY_EVOLUTION_DRY_RUN", False),
        )

    @staticmethod
    def is_enabled() -> bool:
        return _env_flag("ENABLE_MEMORY_EVOLUTION", False)

    # ------------------------------------------------------------------
    # Cycle execution
    # ------------------------------------------------------------------
    async def run_once(self) -> ReorganizeResult:
        """Run exactly one evolution cycle. Never raises — errors land in stats."""
        async with self._cycle_lock:
            started = time.time()
            try:
                if self.dry_run:
                    # Non-destructive preview: inspect only, mutate nothing.
                    clusters = await self.service.cluster_memories()
                    merge_preview = await self.service.deduplicate_memories(dry_run=True)
                    decay_preview = await self.service.prune_decayed_memories(
                        retention_threshold=self.retention_threshold,
                        min_age_days=self.min_decay_age_days,
                        dry_run=True,
                    )
                    result = ReorganizeResult(
                        clusters=len(clusters.clusters),
                        duplicates=len(merge_preview.groups),
                        merged=merge_preview.merged_count,
                        decay_pruned=len(decay_preview.removed_ids),
                        retained=decay_preview.retained,
                        duration_ms=round((time.time() - started) * 1000, 3),
                    )
                else:
                    result = await self.service.reorganize_storage(
                        max_age_days=self.max_age_days,
                        min_access=self.min_access,
                        merge_duplicates=self.merge_duplicates,
                        apply_decay=self.apply_decay,
                        persist_clusters=self.persist_clusters,
                        retention_threshold=self.retention_threshold,
                        min_decay_age_days=self.min_decay_age_days,
                    )
                self.stats.cycles += 1
                self.stats.total_merged += result.merged
                self.stats.total_decay_pruned += result.decay_pruned
                self.stats.total_pruned += result.pruned
                self.stats.clusters_last_cycle = result.clusters
                self.stats.last_run_at = started
                self.stats.last_duration_ms = result.duration_ms
                self.stats.last_error = None
                self.stats.last_result = asdict(result)
                logger.info(
                    f"[MemoryEvolution] cycle #{self.stats.cycles} "
                    f"clusters={result.clusters} merged={result.merged} "
                    f"decay_pruned={result.decay_pruned} pruned={result.pruned} "
                    f"in {result.duration_ms}ms (dry_run={self.dry_run})"
                )
                return result
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.stats.failures += 1
                self.stats.last_run_at = started
                self.stats.last_error = str(exc)[:300]
                logger.warning(f"[MemoryEvolution] cycle failed: {exc}")
                return ReorganizeResult(
                    duration_ms=round((time.time() - started) * 1000, 3)
                )

    async def run_forever(self) -> None:
        """Loop body — compatible with `AgentSupervisor.start_agent` factories."""
        self._stop_event = asyncio.Event()
        logger.info(
            f"[MemoryEvolution] loop started (interval={self.interval_seconds}s, "
            f"dry_run={self.dry_run})"
        )
        while not self._stop_event.is_set():
            await self.run_once()
            try:
                # Sleep interruptibly so shutdown does not wait a full interval.
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
            except TimeoutError:
                continue
        logger.info("[MemoryEvolution] loop stopped.")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> bool:
        """Start the background task. Returns False if already running."""
        if self.running:
            logger.debug("[MemoryEvolution] start ignored — already running.")
            return False
        self._task = asyncio.create_task(self.run_forever(), name="memory-evolution-loop")
        return True

    async def stop(self, timeout: float = 10.0) -> bool:
        """Signal the loop to stop and await teardown."""
        if self._stop_event is not None:
            self._stop_event.set()
        task = self._task
        if task is None:
            return False
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
        except TimeoutError:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug("[MemoryEvolution] loop task cancelled after stop timeout.")
            except Exception as exc:
                logger.warning(f"[MemoryEvolution] loop task errored during cancel: {exc}")
        except asyncio.CancelledError:
            pass
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"[MemoryEvolution] stop encountered: {exc}")
        finally:
            self._task = None
        return True

    def status(self) -> dict[str, Any]:
        """Snapshot for the admin API / health surface."""
        return {
            "running": self.running,
            "enabled_by_env": self.is_enabled(),
            "interval_seconds": self.interval_seconds,
            "dry_run": self.dry_run,
            "config": {
                "merge_duplicates": self.merge_duplicates,
                "apply_decay": self.apply_decay,
                "persist_clusters": self.persist_clusters,
                "retention_threshold": self.retention_threshold,
                "min_decay_age_days": self.min_decay_age_days,
                "max_age_days": self.max_age_days,
                "min_access": self.min_access,
            },
            "stats": asdict(self.stats),
        }


# Global singleton — shared by the API routes and the startup wiring.
memory_evolution_loop = MemoryEvolutionLoop.from_env()


async def start_memory_evolution_loop() -> None:
    """AgentSupervisor entrypoint: run the shared loop forever."""
    await memory_evolution_loop.run_forever()


__all__ = [
    "EvolutionLoopStats",
    "MemoryEvolutionLoop",
    "memory_evolution_loop",
    "start_memory_evolution_loop",
]
