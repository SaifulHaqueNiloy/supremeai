from typing import Any

from .base import BasePlugin


class GoogleDrivePlugin(BasePlugin):
    @property
    def plugin_id(self) -> str:
        return "google_drive"

    async def execute_tool(
        self, tool_name: str, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        raise NotImplementedError("Google Drive plugin tools not implemented yet")
