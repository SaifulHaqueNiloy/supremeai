from typing import Any

from .base import BasePlugin


class SlackPlugin(BasePlugin):
    @property
    def plugin_id(self) -> str:
        return "slack"

    async def execute_tool(
        self, tool_name: str, params: dict[str, Any], context: dict[str, Any]
    ) -> Any:
        raise NotImplementedError("Slack plugin tools not implemented yet")
