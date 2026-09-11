from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from api.dependencies import get_current_user_token
from core.connection_registry import connection_registry
from core.mcp_client import MCPRegistryClient

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])


class MCPConnectRequest(BaseModel):
    mcp_url: HttpUrl
    name: str | None = None
    permission_level: str = "user"


class MCPPermissionRequest(BaseModel):
    permission_level: str


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
        record = connection_registry.register(
            user=user,
            url=str(req.mcp_url),
            capabilities=tools,
            name=req.name,
            permission_level=req.permission_level,
        )
        return {"status": "success", "connection": record.model_dump(mode="json")}
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe)) from pe
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception:
        # Keep provider URLs, credentials, and internal network details out of responses.
        raise HTTPException(status_code=502, detail="MCP server connection failed")


@router.patch("/connections/{connection_id}/permission")
async def update_mcp_permission(
    connection_id: str,
    req: MCPPermissionRequest,
    user: dict = Depends(get_current_user_token),
):
    """Allow an authorized tenant administrator to change one connection's role."""
    try:
        connection = connection_registry.set_permission(
            user=user,
            connection_id=connection_id,
            permission_level=req.permission_level,
        )
        return {"status": "success", "connection": connection.model_dump(mode="json")}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/connections")
async def list_mcp_connections(
    user: dict = Depends(get_current_user_token),
):
    """List only the authenticated actor's tenant-owned connections."""
    try:
        return {"connections": [
            connection.model_dump(mode="json")
            for connection in connection_registry.list_for_tenant(user)
        ]}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
