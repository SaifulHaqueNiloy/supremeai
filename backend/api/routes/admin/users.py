"""Admin → Users endpoints."""
import json

import jwt
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from core.config import settings
from api.routes.admin._helpers import UserUpdate, load_users, save_users
from api.routes.admin_auth import admin_rate_limit, require_admin_token

router = APIRouter()


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


@router.get("/roles")
def get_roles():
    return [{"id": "1", "name": "God"}, {"id": "2", "name": "Operator"}, {"id": "3", "name": "Viewer"}]


@router.get("/permissions")
def get_permissions():
    return [{"id": "1", "name": "all"}, {"id": "2", "name": "read"}, {"id": "3", "name": "write"}]
