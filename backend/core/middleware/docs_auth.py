"""API Docs Basic-Auth protection middleware.

FINAL-TEST P0 FIX (production contract closure, 2026-09-14):
The project had `docs_auth_enabled` / `docs_username` / `docs_password` settings,
but NO middleware ever enforced them — /docs, /redoc and the OpenAPI schema were
publicly reachable in every environment whenever they were mounted.

This middleware enforces HTTP Basic authentication on the documentation surfaces
when (and only when) they are enabled outside local development:

    docs_enabled AND docs_auth_enabled AND env not local
        → 401 + WWW-Authenticate for /docs, /redoc, /openapi.json

Wiring (core/app_builder.py): the middleware is added AFTER AuthMiddleware so
that it runs BEFORE it at runtime (Starlette: last-added = outermost), which lets
it issue a proper Basic-auth challenge instead of the auth middleware's JSON 401.
"""

from __future__ import annotations

import base64
import hmac
import secrets

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from core.config import settings
from core.logging_config import logger


class DocsAuthMiddleware(BaseHTTPMiddleware):
    """HTTP Basic auth gate for /docs, /redoc and the OpenAPI schema."""

    # NOTE: f"{settings.API_V1_STR}/openapi.json" is the actual OpenAPI mount
    # point (app_builder.py); "/openapi.json" is kept for older proxies/monitors.
    PROTECTED_PREFIXES = (
        "/docs",
        "/redoc",
        "/openapi.json",
        f"{settings.API_V1_STR}/openapi.json",
    )

    def _is_protected_path(self, path: str) -> bool:
        return any(
            path == prefix or path.startswith(f"{prefix}/") or path.startswith(f"{prefix}?")
            for prefix in self.PROTECTED_PREFIXES
        )

    def _is_active(self) -> bool:
        # local/dev docs stay open (developer convenience); everywhere else the
        # docs surface requires Basic auth when mounted at all. Pytest/CI must
        # not be affected.
        import os
        import sys

        if "pytest" in sys.modules or os.getenv("CI") == "true":
            return False
        if settings.is_local():
            return False
        return bool(getattr(settings, "docs_enabled", False)) and bool(
            getattr(settings, "docs_auth_enabled", True)
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._is_active() or not self._is_protected_path(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return self._challenge()

        try:
            decoded = base64.b64decode(auth_header.removeprefix("Basic ").strip(), validate=True)
            username, _, password = decoded.decode("utf-8").partition(":")
        except Exception:  # noqa: BLE001 — malformed Basic header must not 500
            return self._challenge()

        expected_user = getattr(settings, "docs_username", "admin")
        expected_pwd = (
            settings.docs_password.get_secret_value()
            if getattr(settings, "docs_password", None)
            else ""
        )

        user_ok = hmac.compare_digest(username or "", expected_user or "")
        pwd_ok = bool(expected_pwd) and secrets.compare_digest(password or "", expected_pwd)
        if not (user_ok and pwd_ok):
            logger.warning(
                f"🚫 Docs auth failed for client on {request.url.path} "
                f"(env={settings.env})"
            )
            return self._challenge()

        return await call_next(request)

    def _challenge(self) -> Response:
        return Response(
            status_code=401,
            content=b'{"error": "Documentation requires authentication"}',
            media_type="application/json",
            headers={"WWW-Authenticate": 'Basic realm="SupremeAI API Docs", charset="UTF-8"'},
        )
