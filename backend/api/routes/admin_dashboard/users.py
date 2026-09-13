"""User & tenant management: user CRUD, tenant usage reset, impersonation."""

import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.routes.admin_auth import admin_rate_limit, require_admin_token
from core.config import settings
from core.logging_config import logger

from ._shared import load_users, save_users

# See observability.py for why the sub-router replicates the original config.
router = APIRouter(
    prefix="/admin-api",
    tags=["admin-dashboard"],
    dependencies=[Depends(require_admin_token), Depends(admin_rate_limit)],
)


# User CRUD model
class UserUpdate(BaseModel):
    username: str
    role: str
    permissions: list[str]


@router.get("/users")
def get_users():
    return load_users()


@router.post("/users")
def create_user(user: UserUpdate):
    users = load_users()
    for u in users:
        if u["username"] == user.username:
            u["role"] = user.role
            u["permissions"] = user.permissions
            save_users(users)
            return {"status": "success", "message": f"User {user.username} updated"}

    users.append({"username": user.username, "role": user.role, "permissions": user.permissions})
    save_users(users)
    return {"status": "success", "message": f"User {user.username} created"}


@router.delete("/users/{username}")
def delete_user(username: str):
    users = load_users()
    new_users = [u for u in users if u["username"] != username]
    if len(new_users) == len(users):
        raise HTTPException(status_code=404, detail="User not found")
    save_users(new_users)
    return {"status": "success", "message": f"User {username} deleted"}


@router.post("/tenants/{tenant_id}/reset")
async def reset_tenant_usage_bridge(tenant_id: str):
    """Reset today's request/token counters for a tenant."""
    import time

    try:
        import core.services as app_mod

        q = getattr(app_mod, "redis_queue", None)
        if q and getattr(q, "configured", False):
            now = int(time.time())
            q.delete(f"rate:{tenant_id}:{now // 86400}:rpd")
            q.delete(f"rate:{tenant_id}:tokens")
            q.delete(f"rate:{tenant_id}:cost")
            return {"status": "success", "message": f"Tenant {tenant_id} usage reset"}
    except Exception as e:
        logger.debug(f"Reset tenant error: {e}")
    return {"status": "success", "message": f"Tenant {tenant_id} usage reset"}


@router.post("/users/impersonate/{username}")
async def impersonate_user(username: str, current_admin: dict = Depends(require_admin_token)):
    users = load_users()
    target = next((u for u in users if u["username"] == username), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    impersonation_token = jwt.encode(
        {
            "uid": target["username"],
            "role": target["role"],
            "impersonator": current_admin.get("uid", "admin"),
            "impersonation": True,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return {
        "status": "success",
        "impersonation_token": impersonation_token,
        "user": target,
    }


class ImpersonateRequest(BaseModel):
    user_id: str
    otp: str | None = None


@router.post("/impersonate")
async def impersonate_by_payload(
    payload: ImpersonateRequest, current_admin: dict = Depends(require_admin_token)
):
    """Impersonate user via JSON payload for CommandCenter."""
    users = load_users()
    target = next(
        (
            u
            for u in users
            if u["username"] == payload.user_id or str(u.get("id")) == payload.user_id
        ),
        None,
    )
    target_username = target["username"] if target else payload.user_id
    target_role = target.get("role", "user") if target else "user"
    token = jwt.encode(
        {
            "uid": target_username,
            "role": target_role,
            "impersonator": current_admin.get("uid", "admin"),
            "impersonation": True,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return {"token": token, "user": target}
