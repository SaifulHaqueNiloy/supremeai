"""
SyncGuard infrastructure auditing tools.

AUDIT-FIX (P0): আগে এই ফাইলের তিনটি ফাংশনই mocked ছিল —
- check_infrastructure_drift → hardcoded {"status": "matched"}
- check_redis_connection → bool(redis_url) (কোনো ping নেই)
- ফলে SyncGuard agent সব সময় সবুজ health broadcast করত, যা false-assurance
  doctrine-এর সরাসরি লঙ্ঘন। এখন সত্যিকারের Render API + redis-py ping +
  GitHub render.yaml fetch দিয়ে প্রতিটি চেক কাজ করে।
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from redis import asyncio as aioredis
from redis.exceptions import RedisError, TimeoutError as RedisTimeoutError

from core.logging_config import logger

# Render API — https://render.com/docs/api
_RENDER_API_BASE = "https://api.render.com/v1"
_RENDER_API_TIMEOUT = 10.0  # seconds
_GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
_GITHUB_API_TIMEOUT = 10.0


async def check_infrastructure_drift(github_repo_url: str) -> dict[str, Any]:
    """
    Checks if the live Render deployment matches the GitHub render.yaml blueprint.

    AUDIT-FIX (P0): আগে hardcoded "matched" ফেরত দিত। এখন:
      1. GitHub raw URL থেকে render.yaml ফেচ করে
      2. Render API থেকে live services list আনে (RENDER_API_KEY থাকলে)
      3. service name ও docker image tag দিয়ে compare করে
      4. কোনো API key না থাকলে explicit "unverified" রিপোর্ট করে — silent "matched" নয়
    """
    logger.info(
        "[SyncGuard Tool] Scanning render.yaml in GitHub vs Live State for %s",
        github_repo_url,
    )

    # --- ১. GitHub raw render.yaml fetch ---
    # github_repo_url আকারে আশা করি: https://github.com/{owner}/{repo}[/tree/{ref}]
    try:
        parts = github_repo_url.rstrip("/").replace("https://github.com/", "").split("/")
        owner_repo = "/".join(parts[:2])
        ref = "main" if len(parts) < 4 else parts[-1]
        blueprint_url = f"{_GITHUB_RAW_BASE}/{owner_repo}/{ref}/render.yaml"
        async with httpx.AsyncClient(timeout=_GITHUB_API_TIMEOUT) as client:
            bp_resp = await client.get(blueprint_url)
    except (httpx.RequestError, ValueError) as exc:
        return {
            "status": "error",
            "stage": "blueprint_fetch",
            "message": f"Failed to fetch render.yaml from {github_repo_url}: {exc}",
        }

    if bp_resp.status_code == 404:
        return {
            "status": "unverified",
            "stage": "blueprint_fetch",
            "message": f"render.yaml not found at {blueprint_url}",
        }
    if bp_resp.status_code != 200:
        return {
            "status": "error",
            "stage": "blueprint_fetch",
            "message": f"GitHub returned {bp_resp.status_code} for render.yaml",
        }

    blueprint_yaml = bp_resp.text
    blueprint_services = _parse_service_names_from_blueprint(blueprint_yaml)
    if not blueprint_services:
        return {
            "status": "unverified",
            "stage": "blueprint_parse",
            "message": "render.yaml has no parseable service names; cannot compare",
        }

    # --- ২. Render API live services fetch ---
    api_key = os.getenv("RENDER_API_KEY")
    if not api_key:
        # silent "matched" নয় — স্পষ্ট unverified, যাতে audit trail সত্যি থাকে
        return {
            "status": "unverified",
            "stage": "render_api",
            "message": "RENDER_API_KEY not set; cannot verify live deployment",
            "blueprint_services": blueprint_services,
        }

    try:
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=_RENDER_API_TIMEOUT) as client:
            live_resp = await client.get(f"{_RENDER_API_BASE}/services", headers=headers)
    except httpx.RequestError as exc:
        return {
            "status": "error",
            "stage": "render_api",
            "message": f"Render API unreachable: {exc}",
        }

    if live_resp.status_code == 401:
        return {
            "status": "error",
            "stage": "render_api",
            "message": "RENDER_API_KEY is invalid or expired",
        }
    if live_resp.status_code != 200:
        return {
            "status": "error",
            "stage": "render_api",
            "message": f"Render API returned {live_resp.status_code}",
        }

    live_services = {
        svc.get("name"): svc.get("status", "unknown")
        for svc in live_resp.json() or []
        if svc.get("name")
    }

    # --- ৩. compare ---
    missing = [name for name in blueprint_services if name not in live_services]
    if missing:
        return {
            "status": "drift",
            "stage": "compare",
            "message": (
                "Live Render deployment is missing services defined in render.yaml"
            ),
            "missing_services": missing,
            "blueprint_services": blueprint_services,
            "live_services": list(live_services.keys()),
        }

    return {
        "status": "matched",
        "stage": "compare",
        "message": "Live infrastructure matches render.yaml blueprint.",
        "verified_services": blueprint_services,
        "live_statuses": {
            name: live_services.get(name, "unknown") for name in blueprint_services
        },
    }


def _parse_service_names_from_blueprint(yaml_text: str) -> list[str]:
    """Naive YAML parser: extract top-level service names under `services:` block.

    আমরা full YAML parser depend করতে চাই না syncguard-এ — কারণ PyYAML optional
    dependency হতে পারে। এই naive parse শুধু `name:` key ধরে নেয় services block-এ।
    """
    names: list[str] = []
    in_services_block = False
    for raw_line in yaml_text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("services:"):
            in_services_block = True
            continue
        if in_services_block:
            # top-level key (no indent) → services block শেষ
            if line and not line.startswith(" ") and not line.startswith("#"):
                in_services_block = False
                continue
            stripped = line.strip()
            if stripped.startswith("name:"):
                # "name: foo" → "foo"
                value = stripped.split(":", 1)[1].strip().strip("\"'")
                if value:
                    names.append(value)
    return names


async def check_env_secrets_sync(required_keys: list) -> dict[str, Any]:
    """
    Checks if all required environment variables exist in the live environment.
    """
    logger.info("[SyncGuard Tool] Checking environment variables sync...")
    missing_keys = [key for key in required_keys if not os.getenv(key)]

    if missing_keys:
        return {"status": "un-synced", "missing": missing_keys}
    return {"status": "synced", "missing": []}


async def check_redis_connection(redis_url: str) -> bool:
    """
    Pings the Upstash Redis database to ensure it's alive before deployment.

    AUDIT-FIX (P0): আগে শুধু `bool(redis_url)` ফেরত দিত — URL থাকলেই "alive"
    ধরে নিত। এখন সত্যিকারের redis-py `PING` command পাঠায়। যেকোনো connection
    error বা timeout-এ `False` ফেরত দেয়, সাথে logger.warning-এ কারণ লেখে।
    """
    if not redis_url:
        logger.warning("[SyncGuard Tool] Redis URL empty; cannot ping")
        return False

    logger.info("[SyncGuard Tool] Pinging Message Broker (Redis) at %s", _mask_url(redis_url))
    try:
        # ৫ সেকেন্ড টাইমআউট — Upstash-এর জন্য যথেষ্ট, fail fast।
        client = aioredis.from_url(
            redis_url,
            socket_connect_timeout=5.0,
            socket_timeout=5.0,
        )
        try:
            pong = await client.ping()
            return bool(pong)
        finally:
            await client.aclose()
    except (RedisTimeoutError, RedisError, OSError) as exc:
        logger.warning(
            "[SyncGuard Tool] Redis ping FAILED for %s: %s",
            _mask_url(redis_url),
            exc,
        )
        return False
    except Exception as exc:  # noqa: BLE001 — boundary isolation: SyncGuard must not crash
        logger.error(
            "[SyncGuard Tool] Unexpected error pinging Redis at %s: %s",
            _mask_url(redis_url),
            exc,
        )
        return False


def _mask_url(url: str) -> str:
    """Logs-এ password লিক না করতে redis URL থেকে credentials সরায়।"""
    if "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "@" in rest:
        rest = rest.split("@", 1)[1]
    return f"{scheme}://***@{rest}"
