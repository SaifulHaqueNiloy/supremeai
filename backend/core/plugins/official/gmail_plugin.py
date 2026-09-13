from typing import Any

from .base import BasePlugin


class GmailPlugin(BasePlugin):
    @property
    def plugin_id(self) -> str:
        return "gmail"

    async def execute_tool(
        self, tool_name: str, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        raise NotImplementedError("Gmail plugin tools not implemented yet")
