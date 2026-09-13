"""Dashboard configuration: feature flags, roles/permissions, workspaces,
settings, sessions, customers and env config endpoints."""

import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.routes.admin_auth import admin_rate_limit, require_admin_token

from ._shared import _load_json_data, _save_json_data

# See observability.py for why the sub-router replicates the original config.
router = APIRouter(
    prefix="/admin-api",
    tags=["admin-dashboard"],
    dependencies=[Depends(require_admin_token), Depends(admin_rate_limit)],
)


# Environment Configuration Editor
class ConfigUpdate(BaseModel):
    env_vars: dict[str, str]


_FEATURE_FLAGS = [
    {
        "id": "1",
        "name": "new_chat_ui",
        "description": "New chat interface with streaming",
        "enabled": True,
        "rollout": 25,
        "environment": "production",
    },
    {
        "id": "2",
        "name": "rag_v2",
        "description": "Improved RAG retrieval algorithm",
        "enabled": False,
        "rollout": 0,
        "environment": "staging",
    },
    {
        "id": "3",
        "name": "dark_mode",
        "description": "Dark mode toggle for all users",
        "enabled": True,
        "rollout": 100,
        "environment": "production",
    },
]


@router.get("/feature-flags")
def get_feature_flags():
    return {"flags": _FEATURE_FLAGS}


# CI FIX: frontend hooks.ts calls POST /admin-api/feature-flags to create
# new flags. Added POST alias for backward compat (same as GET for now).
@router.post("/feature-flags")
def create_feature_flag(payload: dict):
    """Create or update a feature flag (idempotent — matches by name)."""
    name = payload.get("name", "")
    for f in _FEATURE_FLAGS:
        if f["name"] == name:
            if "enabled" in payload:
                f["enabled"] = payload["enabled"]
            if "rollout" in payload:
                f["rollout"] = payload["rollout"]
            return {"status": "success", "flag": f}
    # New flag
    new_flag = {
        "id": str(len(_FEATURE_FLAGS) + 1),
        "name": name,
        "description": payload.get("description", ""),
        "enabled": payload.get("enabled", False),
        "rollout": payload.get("rollout", 0),
        "environment": payload.get("environment", "production"),
    }
    _FEATURE_FLAGS.append(new_flag)
    return {"status": "success", "flag": new_flag}


@router.put("/feature-flags/{flag_id}")
def update_feature_flag(flag_id: str, payload: dict):
    for f in _FEATURE_FLAGS:
        if f["id"] == flag_id:
            if "enabled" in payload:
                f["enabled"] = payload["enabled"]
            if "rollout" in payload:
                f["rollout"] = payload["rollout"]
            return {"status": "success", "flag": f}
    raise HTTPException(status_code=404, detail="Flag not found")


# ── Additional Admin CRUD Endpoints (Phase 1) ────────────────────────────────

WORKSPACES_FILE = "data/workspaces.json"
SETTINGS_FILE = "data/settings.json"
SESSIONS_FILE = "data/sessions.json"
CUSTOMERS_FILE = "data/customers.json"


@router.get("/roles")
def get_roles():
    return [
        {"id": "1", "name": "God"},
        {"id": "2", "name": "Operator"},
        {"id": "3", "name": "Viewer"},
    ]


@router.get("/permissions")
def get_permissions():
    return [{"id": "1", "name": "all"}, {"id": "2", "name": "read"}, {"id": "3", "name": "write"}]


@router.get("/workspaces")
def get_workspaces():
    return _load_json_data(
        WORKSPACES_FILE,
        [{"id": "ws_1", "name": "Default Workspace", "description": "System default workspace"}],
    )


@router.post("/workspaces")
def create_workspace(workspace: dict):
    workspaces = _load_json_data(WORKSPACES_FILE, [])
    if "id" not in workspace or not workspace["id"]:
        workspace["id"] = f"ws_{secrets.token_hex(4)}"
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
    return _load_json_data(
        SETTINGS_FILE, {"theme": "dark", "notifications_enabled": True, "max_concurrent_tasks": 5}
    )


@router.post("/settings")
def update_settings(payload: dict):
    settings_data = _load_json_data(SETTINGS_FILE, {})
    settings_data.update(payload)
    _save_json_data(SETTINGS_FILE, settings_data)
    return settings_data


@router.get("/sessions")
def get_sessions():
    return _load_json_data(
        SESSIONS_FILE, [{"id": "sess_1", "name": "Initial Boot Session", "status": "active"}]
    )


@router.get("/customers")
def get_customers():
    return _load_json_data(
        CUSTOMERS_FILE,
        [{"id": "cust_1", "name": "Acme Corp", "email": "admin@acme.com", "billing_tier": "pro"}],
    )


# বাংলা মন্তব্ত: AUDIT-018 ফিক্স — Studio Client-এর useAdminApi.ts এবং
# AdminShell.tsx-এর /admin-api/config কল এখন ব্যাকএন্ডে আছে (আগে 404 পেত)।
@router.get("/config")
def get_config():
    """Get environment configuration for the admin dashboard."""
    import os

    config = {}
    for key in ["ENV", "DEBUG", "LOG_LEVEL", "REDIS_URL", "DATABASE_URL"]:
        val = os.environ.get(key, "")
        if val:
            config[key] = val
    return config


@router.post("/config")
def update_config(payload: dict):
    """Update environment configuration (writes to settings.json)."""
    import os

    config = _load_json_data(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "settings.json"), {}
    )
    config.update(payload)
    _save_json_data(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "settings.json"), config
    )
    return {"status": "success", "message": "Configuration updated"}
