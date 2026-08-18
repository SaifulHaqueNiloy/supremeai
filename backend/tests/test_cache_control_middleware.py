"""
Unit tests for CacheControlMiddleware.
Verifies HTTP response Cache-Control header injection across dynamic, sensitive, and static endpoints.
"""

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from core.middleware.cache_control_middleware import CacheControlMiddleware


async def auth_endpoint(request):
    return JSONResponse({"status": "authenticated"})


async def config_public_endpoint(request):
    return JSONResponse({"app_name": "SupremeAI"})


async def regular_endpoint(request):
    return JSONResponse({"data": 123})


async def custom_cache_endpoint(request):
    res = Response("custom", media_type="text/plain")
    res.headers["Cache-Control"] = "max-age=999"
    return res


app = Starlette(
    routes=[
        Route("/api/v1/auth/login", auth_endpoint, methods=["POST"]),
        Route("/api/v1/preferences/me", auth_endpoint, methods=["GET"]),
        Route("/api/config/public", config_public_endpoint, methods=["GET"]),
        Route("/api/v1/items", regular_endpoint, methods=["GET"]),
        Route("/custom", custom_cache_endpoint, methods=["GET"]),
    ]
)
app.add_middleware(CacheControlMiddleware)


def test_sensitive_auth_endpoint_has_no_store():
    client = TestClient(app)
    res = client.post("/api/v1/auth/login")
    assert res.headers["Cache-Control"] == "no-store, no-cache, must-revalidate, private"
    assert res.headers["Pragma"] == "no-cache"


def test_sensitive_preferences_endpoint_has_no_store():
    client = TestClient(app)
    res = client.get("/api/v1/preferences/me")
    assert res.headers["Cache-Control"] == "no-store, no-cache, must-revalidate, private"


def test_public_config_endpoint_has_public_cache():
    client = TestClient(app)
    res = client.get("/api/config/public")
    assert "public" in res.headers["Cache-Control"]
    assert "max-age=3600" in res.headers["Cache-Control"]


def test_custom_cache_header_preserved():
    client = TestClient(app)
    res = client.get("/custom")
    assert res.headers["Cache-Control"] == "max-age=999"
