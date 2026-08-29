from typing import Any

from .base import BasePlugin


class NotionPlugin(BasePlugin):
    @property
    def plugin_id(self) -> str:
        return "notion"

    async def execute_tool(
        self, tool_name: str, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        raise NotImplementedError("Notion plugin tools not implemented yet")
