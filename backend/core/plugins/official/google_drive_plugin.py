from typing import Any

from .base import BasePlugin


class GoogleDrivePlugin(BasePlugin):
    @property
    def plugin_id(self) -> str:
        return "google_drive"

    async def execute_tool(
        self, tool_name: str, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        return {
            "status": "unavailable",
            "plugin": self.plugin_id,
            "tool": tool_name,
            "reason": "Google Drive authorization/tool execution is not configured for this deployment.",
        }
