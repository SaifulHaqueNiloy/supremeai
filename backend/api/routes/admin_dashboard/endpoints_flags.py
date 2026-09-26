"""Feature-flag admin endpoints backed by the REAL Supabase ``feature_flags``
table (issue #1818 — previously a hardcoded in-process fake list that lost
every change on restart and managed names the runtime never read).

Contract (CommandCenter, frontend/src/commandcenter/data/types.ts):

* ``GET  /admin-api/feature-flags``       → **bare array** of unified flags:
  ``{key, enabled, rollout_percent, environment, updated_at?}``
  (legacy aliases ``name``/``id``/``rollout``/``description`` included so the
  older CICDVisualizer consumer keeps rendering).
* ``POST /admin-api/feature-flags``       → ``{status, message, flag}``
  (payload ``{key|name, enabled, rollout_percent|rollout}`` — idempotent
  upsert matched by ``feature_name``).
* ``PUT  /admin-api/feature-flags/{id}``  → ``{status, message, flag}``
  (``id`` may be the DB row id or the ``feature_name``).

Name unification (acceptance criterion 3): the admin surface manages the SAME
``feature_name`` keys the runtime checker (``core/feature_flags.py``) reads —
``mem0_enabled``, ``graphiti_enabled``, ``browser_use_enabled``,
``e2b_enabled``, ``openhands_enabled``. Every mutation resets the runtime
FeatureFlags cache so gating changes take effect immediately (criterion 2);
rows persist in Supabase so they survive restarts (criterion 2).
"""

from fastapi import HTTPException

from api.routes.admin_dashboard import router
from core.logging_config import logger

# The runtime checker reads exactly these feature_name keys.
_RUNTIME_FLAG_NAMES: dict[str, str] = {
    "mem0_enabled": "Premium Mem0 memory layer (env: SUPREMEAI_MEM0_ENABLED)",
    "graphiti_enabled": "Graphiti temporal knowledge-graph memory (env: SUPREMEAI_GRAPHITI_ENABLED)",
    "browser_use_enabled": "Browser-use premium agent (env: SUPREMEAI_BROWSER_USE_ENABLED)",
    "e2b_enabled": "E2B premium sandbox (env: SUPREMEAI_E2B_ENABLED)",
    "openhands_enabled": "OpenHands premium coding agent (env: SUPREMEAI_OPENHANDS_ENABLED)",
}

# Module-attr parity with the pre-split module (the package __init__ re-exports
# this name). The fake in-process list is GONE — the live rows come from the
# Supabase feature_flags table via get_feature_flags(); this constant only
# documents the runtime-managed names for tooling/tests.
_FEATURE_FLAGS: list[dict] = [
    {"name": name, "description": description} for name, description in _RUNTIME_FLAG_NAMES.items()
]


def _db():
    from database.supabase_client import db

    if not db or not getattr(db, "client", None):
        raise HTTPException(
            status_code=503, detail="Feature-flag store unavailable (DB not configured)"
        )
    return db


def _row_to_flag(row: dict) -> dict:
    name = row.get("feature_name", "")
    rollout = row.get("rollout_percentage")
    if rollout is None:
        rollout = 100
    return {
        "key": name,
        "name": name,  # legacy alias (CICDVisualizer)
        "id": str(row.get("id", name)),
        "enabled": bool(row.get("enabled", False)),
        "rollout_percent": rollout,
        "rollout": rollout,  # legacy alias (CICDVisualizer)
        "description": _RUNTIME_FLAG_NAMES.get(name, row.get("description") or ""),
        "environment": "prod",
        "updated_at": row.get("updated_at"),
    }


def _reset_runtime_cache() -> None:
    """Mutations must reach the runtime gating immediately (criterion 2)."""
    try:
        from core.feature_flags import feature_flags

        feature_flags.reset_cache()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(f"feature-flags: runtime cache reset skipped: {exc}")


@router.get("/feature-flags")
def get_feature_flags():
    db = _db()
    try:
        rows = db.list_feature_flags()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"feature-flags: list failed: {exc}")
        raise HTTPException(status_code=503, detail="Feature-flag store read failed")
    flags = [_row_to_flag(r) for r in rows]
    # The runtime-known names are ALWAYS visible/manageable — even when the
    # table has no row yet (display default OFF until an admin enables them).
    present = {f["key"] for f in flags}
    for name, description in _RUNTIME_FLAG_NAMES.items():
        if name not in present:
            flags.append(
                {
                    "key": name,
                    "name": name,
                    "id": name,
                    "enabled": False,
                    "rollout_percent": 0,
                    "rollout": 0,
                    "description": description,
                    "environment": "prod",
                    "updated_at": None,
                }
            )
    flags.sort(key=lambda f: f["key"])
    return flags


def _upsert(db, name: str, payload: dict) -> dict:
    enabled = payload.get("enabled")
    rollout = payload.get("rollout_percent", payload.get("rollout"))
    if enabled is not None and not isinstance(enabled, bool):
        raise HTTPException(status_code=422, detail="'enabled' must be a boolean")
    if rollout is not None and (not isinstance(rollout, (int, float)) or not 0 <= rollout <= 100):
        raise HTTPException(
            status_code=422, detail="'rollout_percent' must be a number in [0, 100]"
        )
    try:
        row = db.upsert_feature_flag(
            name,
            enabled=enabled if enabled is not None else None,
            rollout_percentage=int(rollout) if rollout is not None else None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"feature-flags: upsert failed for '{name}': {exc}")
        raise HTTPException(status_code=503, detail="Feature-flag store write failed")
    _reset_runtime_cache()
    return _row_to_flag(row)


@router.post("/feature-flags")
def create_feature_flag(payload: dict):
    """Create-or-update one flag (idempotent, matched by feature_name).

    Restricted to the runtime-managed names: creating a name the runtime never
    reads would be a silent no-op pretending to be control (false assurance).
    """
    name = (payload.get("key") or payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Flag 'key' (feature_name) is required")
    if name not in _RUNTIME_FLAG_NAMES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown flag '{name}'. Runtime-managed flags: {sorted(_RUNTIME_FLAG_NAMES)}",
        )
    flag = _upsert(_db(), name, payload)
    return {"status": "success", "message": f"Feature flag '{name}' updated", "flag": flag}


@router.put("/feature-flags/{flag_id}")
def update_feature_flag(flag_id: str, payload: dict):
    """Update one flag by DB row id or feature_name.

    Runtime-known names may also be updated (creates the row if missing).
    Pre-existing legacy rows stay manageable so no data becomes orphaned.
    """
    db = _db()
    name = flag_id
    if flag_id.isdigit():
        try:
            rows = db.list_feature_flags()
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"feature-flags: list failed during id resolution: {exc}")
            raise HTTPException(status_code=503, detail="Feature-flag store read failed")
        match = next((r for r in rows if str(r.get("id")) == flag_id), None)
        if match is None:
            raise HTTPException(status_code=404, detail="Flag not found")
        name = match.get("feature_name", "")
    elif name not in _RUNTIME_FLAG_NAMES:
        # Non-runtime name: only updatable when the row already exists.
        try:
            rows = db.list_feature_flags()
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"feature-flags: list failed during name resolution: {exc}")
            raise HTTPException(status_code=503, detail="Feature-flag store read failed")
        if not any(r.get("feature_name") == name for r in rows):
            raise HTTPException(status_code=404, detail="Flag not found")
    flag = _upsert(db, name, payload)
    return {"status": "success", "message": f"Feature flag '{name}' updated", "flag": flag}
