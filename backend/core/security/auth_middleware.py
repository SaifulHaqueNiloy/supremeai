"""Authentication Middleware — JWT Auth token validation with fail-closed behavior.

বাংলা: অথেনটিকেশন মিডলওয়্যার — JWT বিয়ারার টোকেন ভ্যালিডেশন, Fail-Closed।
"""

from __future__ import annotations

import hmac
import json
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any

from jose import JWTError
from jose import jwt
from jose.exceptions import ExpiredSignatureError
from loguru import logger

from core.config import settings
from utils.environment import is_test_environment


ASGIScope = dict[str, Any]
ASGISend = Callable[[dict[str, Any]], Awaitable[None]]
ASGIReceive = Callable[[], Awaitable[dict[str, Any]]]
ASGIApp = Callable[[ASGIScope, ASGIReceive, ASGISend], Awaitable[None]]
Headers = list[tuple[bytes, bytes]]


def _get_bearer_token(headers: Headers) -> str | None:
    """Extract an Auth token from the ASGI headers list.

    বাংলা: ASGI হেডার থেকে Bearer টোকেন এক্সট্র্যাক্ট করে।
    """
    for key, value in headers:
        if key.lower() == b"authorization":
            raw = value.decode("utf-8", errors="replace")
            if raw.startswith("Bearer "):
                return raw[7:]
    return None


def _decode_jwt(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    বাংলা: JWT টোকেন ডিকোড এবং ভ্যালিডেট করে।

    Returns:
        Decoded payload dict, or None if invalid/expired.
    """
    if not settings.jwt_secret:
        logger.critical("JWT_SECRET is missing. Rejecting authentication under fail-closed security policy.")
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        return payload
    except ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except JWTError as exc:
        logger.warning(f"JWT token validation failed: {exc}")
        return None


def _is_public_path(path: str) -> bool:
    """Check if a path is public (no auth required).

    বাংলা: পাথটি পাবলিক কিনা চেক করে (কোনো অথের প্রয়োজন নেই)।
    """
    return any(path.startswith(prefix) for prefix in settings.supremeai_public_paths)


async def _send_json_response(
    send: ASGISend,
    status_code: int,
    body: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> None:
    """Send a raw ASGI JSON response.

    বাংলা: কাঁচা ASGI JSON রেসপন্স পাঠায়।
    """
    response_headers: list[tuple[bytes, bytes]] = [
        (b"content-type", b"application/json"),
    ]
    if headers:
        for key, value in headers.items():
            response_headers.append((key.lower().encode(), value.encode()))

    body_bytes = json.dumps(body, separators=(",", ":")).encode("utf-8")
    response_headers.append((b"content-length", str(len(body_bytes)).encode()))

    await send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": response_headers,
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": body_bytes,
        }
    )


class AuthMiddleware:
    """ASGI middleware for JWT-based authentication.

    বাংলা: JWT-ভিত্তিক অথেনটিকেশনের জন্য ASGI মিডলওয়্যার।

    Skips authentication for public paths and test environment.
    Attaches user info (sub, role, tenant_id) to scope on success.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Skip auth for public paths or test environment (only if no api token env is configured)
        # বাংলা মন্তব্য: টেস্ট এনভায়রনমেন্টে অথেন্টিকেশন বাইপাস করা হয়, যদি না সরাসরি API টোকেন চেক করা হচ্ছে।
        import os

        if _is_public_path(path) or (is_test_environment() and not (settings.supremeai_api_token or os.environ.get("SUPREMEAI_API_TOKEN"))):
            await self.app(scope, receive, send)
            return

        headers: Headers = scope.get("headers", [])
        token = _get_bearer_token(headers)

        if not token:
            logger.warning(f"Missing Auth token for path: {path}")
            await _send_json_response(
                send,
                status_code=401,
                body={"detail": "Missing authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
            return

        # API Key validation for system components / testing
        # বাংলা মন্তব্য: ব্যাকএন্ড/সিস্টেম কল ভ্যালিডেশনের জন্য API কী চেক করা হচ্ছে।
        supremeai_api_token = settings.supremeai_api_token or os.environ.get("SUPREMEAI_API_TOKEN")
        if supremeai_api_token and hmac.compare_digest(token.encode("utf-8"), supremeai_api_token.encode("utf-8")):
            scope["user"] = {
                "sub": "system_api_key",
                "role": "admin",
                "tenant_id": None,
            }
            await self.app(scope, receive, send)
            return

        payload = _decode_jwt(token)
        if not payload:
            await _send_json_response(
                send,
                status_code=401,
                body={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
            return

        # Attach user info to scope for downstream handlers
        scope["user"] = {
            "sub": payload.get("sub"),
            "role": payload.get("role", "viewer"),
            "tenant_id": payload.get("tenant_id"),
        }

        await self.app(scope, receive, send)


async def verify_admin_session_fail_closed(request: Any) -> dict[str, Any]:
    """Verify admin session JWT token in a fail-closed manner.

    বাংলা: অ্যাডমিন সেশন JWT টোকেন fail-closed উপায়ে ভ্যালিডেট করে।
    """
    from fastapi import HTTPException

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not auth_header.startswith("Bearer "):
        logger.warning("Malformed Authorization header scheme")
        raise HTTPException(status_code=401, detail="Malformed authorization header")

    token = auth_header[7:]

    # Fail-closed check for JWT secret config
    if not settings.jwt_secret:
        logger.critical("JWT_SECRET is missing. Rejecting authentication under fail-closed security policy.")
        raise HTTPException(status_code=500, detail="Authentication server configuration error")

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
    except ExpiredSignatureError as exc:
        logger.warning(f"Expired JWT token: {exc}")
        raise HTTPException(status_code=401, detail="Token has expired") from exc
    except JWTError as exc:
        logger.warning(f"Invalid JWT token: {exc}")
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    role = payload.get("role")
    if role not in ("admin", "master_admin"):
        logger.warning(f"Access denied: role '{role}' is not authorized for admin session")
        raise HTTPException(status_code=401, detail="Not authorized")

    return payload
