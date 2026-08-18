"""Authentication and rate limiting helpers for the admin dashboard."""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from loguru import logger

from core.config import settings

security = HTTPBearer()
_in_memory_jwt_blacklist: set[str] = set()


def require_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        jwt_secret = settings.jwt_secret
        decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        if decoded.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Forbidden: User does not have admin role.")

        jti = decoded.get("jti")
        if jti:
            import core.services as app_mod

            redis_queue = getattr(app_mod, "redis_queue", None)
            if redis_queue and getattr(redis_queue, "configured", False):
                blocked = redis_queue.get(f"jwt_blacklist:{jti}")
                if blocked is not None:
                    raise HTTPException(status_code=401, detail="Token has been revoked.")
            else:
                if jti in _in_memory_jwt_blacklist:
                    raise HTTPException(status_code=401, detail="Token has been revoked.")
                logger.warning("Redis not configured; falling back to in-memory JWT blacklist check.")

        return decoded
    except Exception as err:
        logger.warning("Admin token validation failed", exc_info=True)
        expected = getattr(settings, "supremeai_api_token", None) or ""
        if expected and secrets.compare_digest(token, expected):
            return {"uid": "admin", "role": "admin"}
        raise HTTPException(status_code=401, detail="Authentication failed.") from err


def validate_sse_token(token: str = Query(..., description="Admin JWT token from query parameter (EventSource-compatible auth)")):
    """SSE/WebSocket-compatible auth — validates JWT from query param instead of Authorization header."""
    try:
        decoded = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if decoded.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Forbidden: User does not have admin role.")
        return decoded
    except HTTPException:
        raise
    except (jwt.PyJWTError, ValueError) as err:
        logger.warning(f"SSE/WebSocket token validation rejected: {err}")
        raise HTTPException(status_code=401, detail="Authentication failed.") from err
    except Exception as err:
        logger.warning(f"Unexpected error during SSE token validation: {err}", exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication failed.") from err


def admin_rate_limit(request: Request):
    import core.services as app_mod

    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:admin:{client_ip}"
    limit = 600
    window = 60

    redis_queue = getattr(app_mod, "redis_queue", None)
    if redis_queue and getattr(redis_queue, "configured", False):
        try:
            current_hits = redis_queue.get(key)
            if current_hits is not None and int(current_hits) >= limit:
                logger.warning(f"Distributed admin rate limit exceeded for {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail="Too many admin requests. Please try again later.",
                )
            redis_queue.set(key, int(current_hits or 0) + 1, ex=window)
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning(f"Admin distributed rate-limit check failed: {exc}")
    return True
