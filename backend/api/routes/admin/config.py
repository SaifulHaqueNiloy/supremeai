"""Admin → Config, Settings, Workspaces, Sessions & Customers endpoints."""
import os
import secrets as secrets_mod

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.routes.admin._helpers import (
    WORKSPACES_FILE,
    SETTINGS_FILE,
    SESSIONS_FILE,
    CUSTOMERS_FILE,
    _load_json_data,
    _save_json_data,
)

router = APIRouter()


@router.get("/workspaces")
def get_workspaces():
    return _load_json_data(
        WORKSPACES_FILE, [{"id": "ws_1", "name": "Default Workspace", "description": "System default workspace"}]
    )


@router.post("/workspaces")
def create_workspace(workspace: dict):
    workspaces = _load_json_data(WORKSPACES_FILE, [])
    if "id" not in workspace or not workspace["id"]:
        workspace["id"] = f"ws_{secrets_mod.token_hex(4)}"
    workspaces.append(workspace)
    _save_json_data(WORKSPACES_FILE, workspaces)
    return workspace


@router.put("/workspaces/{ws_id}")
def update_workspace(ws_id: str, payload: dict):
    workspaces = _load_json_data(WORKSPACES_FILE, [])
    for ws in workspaces:
        if ws["id"] == ws_id:
            ws.update(payload)
            _save_json_data(WORKSPACES_FILE, workspaces)
            return ws
    raise HTTPException(status_code=404, detail="Workspace not found")


@router.delete("/workspaces/{ws_id}")
def delete_workspace(ws_id: str):
    workspaces = _load_json_data(WORKSPACES_FILE, [])
    new_workspaces = [ws for ws in workspaces if ws["id"] != ws_id]
    if len(new_workspaces) == len(workspaces):
        raise HTTPException(status_code=404, detail="Workspace not found")
    _save_json_data(WORKSPACES_FILE, new_workspaces)
    return {"status": "success", "message": "Workspace deleted"}


@router.get("/settings")
def get_settings():
    return _load_json_data(SETTINGS_FILE, {"theme": "dark", "notifications_enabled": True, "max_concurrent_tasks": 5})


@router.post("/settings")
def update_settings(payload: dict):
    settings_data = _load_json_data(SETTINGS_FILE, {})
    settings_data.update(payload)
    _save_json_data(SETTINGS_FILE, settings_data)
    return settings_data


@router.get("/sessions")
def get_sessions():
    return _load_json_data(SESSIONS_FILE, [{"id": "sess_1", "name": "Initial Boot Session", "status": "active"}])


@router.get("/customers")
def get_customers():
    return _load_json_data(
        CUSTOMERS_FILE, [{"id": "cust_1", "name": "Acme Corp", "email": "admin@acme.com", "billing_tier": "pro"}]
    )


# বাংলা মন্তব্ত: AUDIT-018 ফিক্স — /admin-api/config কল এখন ব্যাকএন্ডে আছে (আগে 404 পেত)।
@router.get("/config")
def get_config():
    """Get environment configuration for the admin dashboard."""
    config = {}
    for key in ["ENV", "DEBUG", "LOG_LEVEL", "REDIS_URL", "DATABASE_URL"]:
        val = os.environ.get(key, "")
        if val:
            config[key] = val
    return config


@router.post("/config")
def update_config(payload: dict):
    """Update environment configuration (writes to settings.json)."""
    settings_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "settings.json")
    config = _load_json_data(settings_path, {})
    config.update(payload)
    _save_json_data(settings_path, config)
    return {"status": "success", "message": "Configuration updated"}
