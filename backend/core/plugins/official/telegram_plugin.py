from typing import Any

from .base import BasePlugin


class TelegramPlugin(BasePlugin):
    @property
    def plugin_id(self) -> str:
        return "telegram"

    async def execute_tool(
        self, tool_name: str, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        raise NotImplementedError("Telegram plugin tools not implemented yet")
