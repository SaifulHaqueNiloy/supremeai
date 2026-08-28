"""
SuperAI Health Check Endpoints
===============================
Comprehensive system health monitoring.

Author: SuperAI Transformation Patch
Version: 1.0.0
"""

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import text

from core.cache import get_cache
from core.cache.redis_manager import redis_manager

router = APIRouter()


class HealthStatus(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    services: dict
    cache_stats: dict | None = None


_start_time = time.time()


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    LIVE-001 FIX: Return 200 with degraded status instead of crashing.
    The health endpoint should ALWAYS return 200 with diagnostic info,
    so monitoring tools can read the status. Only /ready should 503.
    """
    db_status = await _check_database()
    redis_status = await _check_redis()
    cache_status = "connected" if redis_manager.is_connected else "disabled"

    overall_status = "healthy"
    if db_status != "healthy":
        overall_status = "degraded"
    if redis_status != "healthy" or cache_status != "connected":
        if overall_status == "healthy":
            overall_status = "degraded"

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        version="3.0.0-superai",
        uptime_seconds=round(time.time() - _start_time, 2),
        services={
            "database": db_status,
            "redis": redis_status,
            "cache": cache_status,
        },
        cache_stats=None,
    )


@router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness probe."""
    db_ok = await _check_database()
    if db_ok != "healthy":
        raise HTTPException(status_code=503, detail="Database not ready")
    return {"status": "ok", "service": "supremeai-backend"}


@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe."""
    return {"status": "alive", "alive": True, "timestamp": datetime.utcnow().isoformat()}


async def _check_database() -> str:
    """Check database connectivity."""
    try:
        from database.session import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return f"unhealthy: {str(e)}"


async def _check_redis() -> str:
    """Check Redis connectivity."""
    try:
        cache = get_cache()
        if cache._redis:
            await cache._redis.ping()
            return "healthy"
        return "not_configured"
    except Exception as e:
        return f"unhealthy: {str(e)}"
