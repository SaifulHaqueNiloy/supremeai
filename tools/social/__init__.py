"""Social tools module for SupremeAI."""

from .email_agent import EmailAgent
from .telegram_bot import TelegramBot

__all__ = [
    "EmailAgent",
    "TelegramBot"
]