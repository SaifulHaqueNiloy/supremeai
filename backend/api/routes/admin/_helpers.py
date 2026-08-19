"""Admin sub-package helpers — shared utilities, models and data-file I/O.

এই ফাইলে shared Pydantic models, JSON CRUD helpers এবং
env-lock logic রাখা হয়েছে যা একাধিক admin sub-module ব্যবহার করে।
"""
import hashlib
import json
import os
from typing import Any

from loguru import logger
from pydantic import BaseModel

from core.error_bus import with_error_bus

# ─── Constants ───────────────────────────────────────────────────────────────

USERS_FILE = "data/users.json"
COST_CAPS_FILE = "data/cost_caps.json"
WORKSPACES_FILE = "data/workspaces.json"
SETTINGS_FILE = "data/settings.json"
SESSIONS_FILE = "data/sessions.json"
CUSTOMERS_FILE = "data/customers.json"


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class UserUpdate(BaseModel):
    username: str
    role: str
    permissions: list[str]


class ConfigUpdate(BaseModel):
    env_vars: dict[str, str]


# ─── Generic JSON I/O ─────────────────────────────────────────────────────────

@with_error_bus("_load_json_data")
def _load_json_data(file_path: str, default_data: Any) -> Any:
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_data


def _save_json_data(file_path: str, data: Any):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ─── User I/O ────────────────────────────────────────────────────────────────

@with_error_bus("load_users")
def load_users() -> list[dict[str, Any]]:
    if not os.path.exists(USERS_FILE):
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        default_users = [
            {"username": "admin", "role": "God", "permissions": ["all"]},
            {"username": "operator1", "role": "Operator", "permissions": ["read", "write"]},
            {"username": "viewer1", "role": "Viewer", "permissions": ["read"]},
        ]
        with open(USERS_FILE, "w") as f:
            json.dump(default_users, f, indent=4)
        return default_users
    try:
        with open(USERS_FILE) as f:
            return json.load(f)
    except Exception:
        logger.exception("Unhandled exception loading users")
        return []


def save_users(users: list[dict[str, Any]]):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


# ─── Cost Caps I/O ────────────────────────────────────────────────────────────

def load_cost_caps() -> dict[str, Any]:
    if not os.path.exists(COST_CAPS_FILE):
        os.makedirs(os.path.dirname(COST_CAPS_FILE), exist_ok=True)
        default = {"default_cap": 10.0, "per_tenant": {}}
        with open(COST_CAPS_FILE, "w") as f:
            json.dump(default, f, indent=4)
        return default
    with open(COST_CAPS_FILE) as f:
        return json.load(f)


def save_cost_caps(caps: dict[str, Any]):
    with open(COST_CAPS_FILE, "w") as f:
        json.dump(caps, f, indent=4)


# ─── Env ETag & Lock ─────────────────────────────────────────────────────────

def get_env_etag(redis_key: str = "config:env_etag") -> str:
    import core.services as app_mod

    redis_queue = getattr(app_mod, "redis_queue", None)
    if redis_queue and getattr(redis_queue, "configured", False):
        cached = redis_queue.get(redis_key)
        if cached:
            return cached
    if os.path.exists(".env"):
        try:
            with open(".env", "rb") as f:
                etag = hashlib.md5(f.read(), usedforsecurity=False).hexdigest()  # nosec B324
            if redis_queue and getattr(redis_queue, "configured", False):
                redis_queue.set(redis_key, etag, ex=300)
            return etag
        except Exception as exc:
            logger.debug(f"Failed to compute .env etag: {exc}")
    return "empty-env"


# বাংলা মন্তব্য: মাল্টি-ইনস্ট্যান্স রেস কন্ডিশন এড়ানোর জন্য রেডিস-ব্যাকড লক ও ফাইল-লকের ফিজিবল কম্বিনেশন
@with_error_bus("_acquire_env_lock")
def _acquire_env_lock(lock_path: str = ".env.lock") -> bool:
    import core.services as app_mod

    redis_queue = getattr(app_mod, "redis_queue", None)
    if redis_queue and getattr(redis_queue, "configured", False):
        try:
            return redis_queue.set_nx("lock:env_write", "locked", ex=10)
        except Exception as exc:
            logger.debug(f"Redis env lock acquisition failed, falling back to file lock: {exc}")
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.close(fd)
        return True
    except FileExistsError:
        return False
    except Exception:
        logger.exception("Unhandled exception")
        return False


def _release_env_lock(lock_path: str = ".env.lock"):
    import core.services as app_mod

    redis_queue = getattr(app_mod, "redis_queue", None)
    if redis_queue and getattr(redis_queue, "configured", False):
        try:
            redis_queue._request("DEL", "lock:env_write")
        except Exception as exc:
            logger.exception(f"Lock release via redis failed: {exc}")
    try:
        os.remove(lock_path)
    except Exception as exc:
        logger.exception(f"Lock file removal failed for {lock_path}: {exc}")
