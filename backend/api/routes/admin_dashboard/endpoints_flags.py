"""Feature-flag endpoints
(GET/POST /admin-api/feature-flags, PUT /admin-api/feature-flags/{flag_id})."""


from fastapi import HTTPException

from api.routes.admin_dashboard import router


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
