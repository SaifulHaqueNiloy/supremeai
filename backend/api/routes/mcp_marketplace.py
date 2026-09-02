from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from api.dependencies import get_current_user_token
from core.mcp_client import MCPRegistryClient

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])


class MCPConnectRequest(BaseModel):
    mcp_url: HttpUrl


@router.post("/discover")
async def discover_mcp_server(
    req: MCPConnectRequest,
    user: dict = Depends(get_current_user_token),
):
    """
    Connects to a user-provided MCP server URL, validates it for SSRF,
    and returns the tools it provides.
    """
    client = MCPRegistryClient()
    try:
        # Convert HttpUrl to string
        tools = await client.connect_and_discover(str(req.mcp_url))
        return {"status": "success", "tools": tools}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to MCP server: {str(e)}")
