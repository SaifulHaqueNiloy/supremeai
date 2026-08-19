"""Admin → Feature Flags endpoints."""
from fastapi import APIRouter, HTTPException

router = APIRouter()

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
