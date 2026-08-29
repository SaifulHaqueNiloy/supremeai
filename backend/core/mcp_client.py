"""Provides the MCPRegistryClient for connecting to external MCP servers using the Official SDK (V2.1)."""

import json
from typing import Any, Optional

import httpx
from loguru import logger

from core.config import settings
from core.plugins.mcp_security import MCPSecurityGuard


class MCPRegistryClient:
    """
    MCP-Hub: The Real-World Connector.
    Connects to external MCP servers securely.
    """

    def __init__(self):
        # We would typically initialize the official mcp sdk client here
        self.enforce_https = getattr(settings, "env", "development") == "production"

    async def connect_and_discover(self, mcp_url: str) -> list[dict[str, Any]]:
        """
        Connects to an MCP server URL, validates it for SSRF, and discovers tools.
        Uses SSE/HTTP standard as defined by Model Context Protocol.
        """
        logger.info(f"MCP Client: Attempting to connect to {mcp_url}")

        if not MCPSecurityGuard.is_safe_url(mcp_url, enforce_https=self.enforce_https):
            logger.error(f"MCP Security blocked connection to {mcp_url}")
            raise ValueError("URL blocked by SSRF / Security policy")

        # Mocking official MCP SDK v2 behavior
        # In production this would be:
        # async with mcp.ClientSession(mcp_url) as session:
        #    return await session.list_tools()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Assuming the MCP server exposes standard /mcp/tools endpoint
                response = await client.get(f"{mcp_url}/mcp/tools")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("tools", [])
                else:
                    logger.warning(
                        f"Failed to fetch tools from {mcp_url}. Status: {response.status_code}"
                    )
                    return []
        except Exception as e:
            logger.error(f"MCP connection error to {mcp_url}: {e}")
            raise

    async def execute_tool(self, mcp_url: str, tool_name: str, params: dict[str, Any]) -> Any:
        """
        Executes a tool on a remote MCP server.
        """
        if not MCPSecurityGuard.is_safe_url(mcp_url, enforce_https=self.enforce_https):
            raise ValueError("URL blocked by SSRF / Security policy")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{mcp_url}/mcp/tools/{tool_name}/execute", json={"params": params}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to execute MCP tool {tool_name} at {mcp_url}: {e}")
            raise
