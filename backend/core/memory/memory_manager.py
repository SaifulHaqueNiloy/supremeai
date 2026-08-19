"""Memory management utilities for SupremeAI.

Provides lightweight memory tracking backed by the standard-library
``tracemalloc`` module plus a background garbage-collection sweeper. No
external dependencies required.
"""

from __future__ import annotations

import gc
import threading
import time
import tracemalloc
from contextlib import contextmanager
from typing import Any


class MemoryManager:
    """Tracks memory usage snapshots and runs periodic cleanup."""

    def __init__(self) -> None:
        self._snapshots: dict[str, Any] = {}
        self._cleanup_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._enabled = False

    def _ensure_tracing(self) -> None:
        if not tracemalloc.is_tracing():
            tracemalloc.start()

    def start(self) -> None:
        self._ensure_tracing()
        self._enabled = True

    @contextmanager
    def track_memory_usage(self, func: Any = None):  # noqa: ANN001
        """Context manager that records a memory delta around a block.

        Usage::

            with memory_manager.track_memory_usage(func):
                do_work()
        """
        self._ensure_tracing()
        before = tracemalloc.take_snapshot()
        try:
            yield
        finally:
            after = tracemalloc.take_snapshot()
            diff = after.compare_to(before, "lineno")
            top = diff[:3] if diff else []
            self._snapshots[f"ctx:{func.__name__ if func else id(self)}"] = top

    def take_memory_snapshot(self, name: str) -> None:
        self._ensure_tracing()
        self._snapshots[name] = tracemalloc.take_snapshot()

    def start_background_cleanup(self, interval_seconds: int = 300) -> None:
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        def _loop() -> None:
            while not self._stop_event.wait(interval_seconds):
                gc.collect()

        self._stop_event.clear()
        self._cleanup_thread = threading.Thread(target=_loop, daemon=True)
        self._cleanup_thread.start()

    def stop_background_cleanup(self) -> None:
        self._stop_event.set()

    def get_memory_stats(self) -> dict[str, Any]:
        current = tracemalloc.get_traced_memory() if tracemalloc.is_tracing() else (0, 0)
        return {
            "current_bytes": current[0],
            "peak_bytes": current[1],
            "snapshots": len(self._snapshots),
            "gc_counts": list(gc.get_count()),
            "enabled": self._enabled,
            "timestamp": time.time(),
        }


memory_manager = MemoryManager()


def track_memory_usage(func: Any = None) -> Any:  # noqa: ANN401
    """Module-level convenience wrapper around ``MemoryManager.track_memory_usage``."""
    return memory_manager.track_memory_usage(func)
