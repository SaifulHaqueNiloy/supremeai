import uuid

from loguru import logger

from core.config import settings

from .interfaces import MessagingProvider
from .models import MessageEvent, MessageResult


class MockMessagingAdapter:
    """A mock implementation of MessagingProvider for local development."""

    async def send(self, event: MessageEvent) -> MessageResult:
        logger.info(
            f"MockMessagingAdapter: Sending message to {event.recipient}. Subject: {event.subject}"
        )
        return MessageResult(success=True, message_id=str(uuid.uuid4()), provider="mock")


class MessagingDispatcher:
    """Routes messaging operations to the configured MessagingProvider."""

    _instance = None
    _provider: MessagingProvider | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_provider()
        return cls._instance

    def _initialize_provider(self) -> None:
        if getattr(settings, "appwrite_enabled", False):
            # If we had an AppwriteMessagingAdapter, we would load it here.
            # try:
            #     from core.providers.appwrite.messaging_adapter import AppwriteMessagingAdapter
            #     self._provider = AppwriteMessagingAdapter()
            #     logger.info("MessagingDispatcher initialized with AppwriteMessagingAdapter.")
            #     return
            # except ImportError as e:
            #     logger.warning(f"Could not load AppwriteMessagingAdapter: {e}")
            pass

        # Fallback to local mock adapter
        self._provider = MockMessagingAdapter()
        logger.info("MessagingDispatcher initialized with MockMessagingAdapter.")

    async def send(self, event: MessageEvent) -> MessageResult:
        if not self._provider:
            return MessageResult(
                success=False, provider="none", error="No messaging provider configured"
            )
        return await self._provider.send(event)


messaging_dispatcher = MessagingDispatcher()
