import time
from collections import OrderedDict
from typing import Optional

from loguru import logger

from ..config import settings
from .interfaces import AutomationProvider
from .models import AutomationEvent, AutomationResult, AutomationStatus


# ── Plan Section 8: Idempotency cache (in-memory LRU) ──────────────────────
# বাংলা: একই event_id দিয়ে দ্বিতীয়বার dispatch করলে prior result ফেরত দেয়।
# এটা in-memory cache — DB persistence পরের phase-এ যাবে (Plan Section 7)।
# আকার bounded (1000 entries) এবং TTL সহ (১ ঘন্টা) — memory leak হবে না।
_IDEMPOTENCY_CACHE_MAX = 1000
_IDEMPOTENCY_TTL_SECONDS = 3600  # 1 ঘন্টা


class _IdempotencyCache:
    """Bounded LRU cache with TTL for idempotent dispatch results।"""

    def __init__(self, max_size: int = _IDEMPOTENCY_CACHE_MAX, ttl: int = _IDEMPOTENCY_TTL_SECONDS):
        self._cache: OrderedDict[str, tuple[AutomationResult, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl

    def get(self, event_id: str) -> Optional[AutomationResult]:
        """event_id থাকলে ও TTL-এর মধ্যে হলে result ফেরত দেয়, নাহলে None।"""
        entry = self._cache.get(event_id)
        if entry is None:
            return None
        result, ts = entry
        if time.time() - ts > self._ttl:
            # expired — remove
            self._cache.pop(event_id, None)
            return None
        # LRU: move to end (most recently used)
        self._cache.move_to_end(event_id)
        return result

    def set(self, event_id: str, result: AutomationResult) -> None:
        """event_id → result সংরক্ষণ। max_size exceed হলে LRU eviction।"""
        self._cache[event_id] = (result, time.time())
        self._cache.move_to_end(event_id)
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)  # evict oldest

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)


class AutomationDispatcher:
    """
    Central dispatcher for all background events.
    Determines which provider to use based on settings and routes the event.
    Core domain logic should only depend on this dispatcher, NEVER on a specific adapter.

    Plan Section 8: idempotency — একই event_id দিয়ে দ্বিতীয়বার dispatch করলে
    prior result ফেরত দেয় (in-memory cache, bounded + TTL)।
    """

    def __init__(self):
        self._provider: AutomationProvider | None = None
        self._idempotency = _IdempotencyCache()
        self._initialize_provider()

    def _initialize_provider(self):
        """
        Dynamically initialize the configured provider.
        """
        if not settings.automation_enabled:
            logger.info("Automation is disabled globally.")
            return

        if settings.n8n_enabled:
            try:
                from ..providers.n8n.adapter import N8nAutomationAdapter

                self._provider = N8nAutomationAdapter()
                logger.info("Initialized n8n automation provider.")
            except ImportError as e:
                logger.error(f"Failed to load n8n provider: {e}")
        else:
            # Fallback or stub provider could be loaded here if needed
            logger.debug("No automation provider enabled.")

    async def dispatch(self, event: AutomationEvent) -> AutomationResult:
        """
        Dispatch the event to the active provider.
        Plan Section 8: idempotency — একই event_id দ্বিতীয়বার এলে cached result ফেরত দেয়।
        """
        # Plan Section 8: idempotency lookup
        cached = self._idempotency.get(event.event_id)
        if cached is not None:
            logger.info(
                f"⚡ Idempotent hit: event {event.event_id} already dispatched — "
                f"returning cached result (status={cached.status.value})"
            )
            return cached

        if not settings.automation_enabled:
            return AutomationResult(
                status=AutomationStatus.SKIPPED,
                provider="none",
                message="Automation is disabled globally.",
                event_id=event.event_id,
            )

        if self._provider is None:
            return AutomationResult(
                status=AutomationStatus.SKIPPED,
                provider="none",
                message="No automation provider configured or available.",
                event_id=event.event_id,
            )

        try:
            result = await self._provider.dispatch(event)
            # Plan Section 7: link event → execution
            if result.event_id is None:
                result.event_id = event.event_id
            # Plan Section 8: cache result for idempotency
            # শুধু DELIVERED বা FAILED cache করি (actual dispatch হওয়া result)
            # SKIPPED cache করি না কারণ সেটা provider unavailable/disabled state
            # — সেই state পরিবর্তন হলে আবার dispatch attempt করা উচিত
            if result.status in (AutomationStatus.DELIVERED, AutomationStatus.FAILED):
                self._idempotency.set(event.event_id, result)
            return result
        except Exception as e:
            logger.exception("Dispatcher caught unhandled exception from provider")
            failed_result = AutomationResult(
                status=AutomationStatus.FAILED,
                provider=self._provider.__class__.__name__ if self._provider else "none",
                message=f"Dispatcher Error: {str(e)}",
                event_id=event.event_id,
            )
            # exception-ও cache করি যাতে একই event বারবার fail না করে
            self._idempotency.set(event.event_id, failed_result)
            return failed_result

    def clear_idempotency_cache(self) -> None:
        """Admin/test এর জন্য cache clear করার method।"""
        self._idempotency.clear()

    def idempotency_cache_size(self) -> int:
        """Cache-এর বর্তমান size (observability)।"""
        return len(self._idempotency)


# Singleton instance to be injected or imported by domain logic
automation_dispatcher = AutomationDispatcher()
