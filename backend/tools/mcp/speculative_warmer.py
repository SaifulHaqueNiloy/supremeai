"""
Speculative Shadow Pre-Warmup Engine
====================================
Anticipates upcoming tool executions (linting, testing, browser navigation, git diffs)
and pre-warms background environments, compiles ASTs, or initializes subprocesses concurrently.
Eliminates sequential tool spin-up delays to deliver zero-perceived latency.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional, Set
from loguru import logger


class SpeculativeWarmer:
    """
    Manages non-blocking speculative execution and resource pre-warmup.
    """

    def __init__(self):
        self._warmup_handlers: Dict[str, Callable] = {}
        self._active_shadow_tasks: Set[asyncio.Task] = set()
        self._warmed_state: Dict[str, Any] = {}

    def register_warmup_hook(self, trigger_keyword: str, handler: Callable) -> None:
        self._warmup_handlers[trigger_keyword.lower()] = handler

    async def check_and_speculate(self, current_stream_text: str) -> list[str]:
        """
        Inspects generated text stream and triggers corresponding shadow warmup tasks.
        """
        lower_stream = current_stream_text.lower()
        triggered = []

        for kw, handler in self._warmup_handlers.items():
            if kw in lower_stream and kw not in self._warmed_state:
                logger.debug(f"[SpeculativeWarmer] Triggering shadow pre-warmup for: {kw}")
                triggered.append(kw)
                task = asyncio.create_task(self._run_shadow_warmup(kw, handler))
                self._active_shadow_tasks.add(task)
                task.add_done_callback(self._active_shadow_tasks.discard)

        return triggered

    async def _run_shadow_warmup(self, key: str, handler: Callable) -> None:
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler()
            else:
                result = handler()
            self._warmed_state[key] = {"status": "ready", "result": result}
            logger.info(f"[SpeculativeWarmer] Shadow pre-warmup '{key}' READY.")
        except Exception as e:
            logger.debug(f"[SpeculativeWarmer] Shadow warmup for '{key}' aborted: {e}")
            self._warmed_state[key] = {"status": "failed", "error": str(e)}

    def consume_warmed_state(self, key: str) -> Optional[Any]:
        """Retrieves and clears warmed resource state if available."""
        state = self._warmed_state.pop(key, None)
        if state and state.get("status") == "ready":
            return state.get("result")
        return None

    async def wait_idle(self) -> None:
        """Waits for any active shadow warmup tasks to finish."""
        if self._active_shadow_tasks:
            await asyncio.gather(*list(self._active_shadow_tasks), return_exceptions=True)

    def clear(self) -> None:
        self._warmed_state.clear()


# Singleton instance
speculative_warmer = SpeculativeWarmer()
