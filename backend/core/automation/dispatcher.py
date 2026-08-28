from typing import Optional

from loguru import logger

from ..config import settings
from .interfaces import AutomationProvider
from .models import AutomationEvent, AutomationResult, AutomationStatus


class AutomationDispatcher:
    """
    Central dispatcher for all background events.
    Determines which provider to use based on settings and routes the event.
    Core domain logic should only depend on this dispatcher, NEVER on a specific adapter.
    """

    def __init__(self):
        self._provider: AutomationProvider | None = None
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
        """
        if not settings.automation_enabled:
            return AutomationResult(
                status=AutomationStatus.SKIPPED,
                provider="none",
                message="Automation is disabled globally.",
            )

        if self._provider is None:
            return AutomationResult(
                status=AutomationStatus.SKIPPED,
                provider="none",
                message="No automation provider configured or available.",
            )

        try:
            result = await self._provider.dispatch(event)
            # Plan Section 7: link event → execution
            if result.event_id is None:
                result.event_id = event.event_id
            return result
        except Exception as e:
            logger.exception("Dispatcher caught unhandled exception from provider")
            return AutomationResult(
                status=AutomationStatus.FAILED,
                provider=self._provider.__class__.__name__ if self._provider else "none",
                message=f"Dispatcher Error: {str(e)}",
                event_id=event.event_id,
            )


# Singleton instance to be injected or imported by domain logic
automation_dispatcher = AutomationDispatcher()
