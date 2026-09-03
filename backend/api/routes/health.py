"""
SuperAI Health Check Endpoints
===============================
Comprehensive system health monitoring.

Author: SuperAI Transformation Patch
Version: 1.0.0
"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import text

from core.cache import get_cache
from core.cache.redis_manager import redis_manager
from core.logging_config import logger

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
@router.get("/deep")
async def deep_health_check(response: Response):
    """
    Comprehensive health check endpoint.
    Sets status_code to 503 if any critical dependency is degraded, so orchestrators (Render/K8s) know it's unhealthy.
    """
    db_start = time.time()
    db_status = await _check_database()
    db_latency = round((time.time() - db_start) * 1000, 2)

    redis_start = time.time()
    redis_status = await _check_redis()
    redis_latency = round((time.time() - redis_start) * 1000, 2)

    cache_status = "connected" if redis_manager.is_connected else "disabled"

    overall_status = "healthy"
    if db_status != "healthy":
        overall_status = "degraded"
    if redis_status != "healthy" or cache_status != "connected":
        # Redis is an optional cache/broadcast dependency. Its outage should be
        # observable in deep health, but must not prevent the API from receiving traffic.
        if overall_status == "healthy":
            overall_status = "degraded"

    # Capture subsystem status from agent_supervisor
    from core.agent_supervisor import agent_supervisor

    agents_status = agent_supervisor.get_health()
    all_agents_healthy = all(a["status"] == "running" for a in agents_status.values())
    if not all_agents_healthy:
        overall_status = "degraded"

    if overall_status == "degraded":
        response.status_code = 503

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="3.0.0-superai",
        uptime_seconds=round(time.time() - _start_time, 2),
        services={
            "database": {"status": db_status, "latency_ms": db_latency},
            "redis": {"status": redis_status, "latency_ms": redis_latency},
            "cache": {"status": cache_status},
            "agents": agents_status,
        },
        cache_stats=None,
    )


@router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness probe."""
    db_ok = await _check_database()
    redis_ok = await _check_redis()

    if db_ok != "healthy":
        raise HTTPException(status_code=503, detail="Database not ready")

    return {
        "status": "ok",
        "service": "supremeai-backend",
        "cache": "healthy" if redis_ok == "healthy" else "degraded",
    }


@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe."""
    return {"status": "alive", "alive": True, "timestamp": datetime.now(timezone.utc).isoformat()}


async def _check_database() -> str:
    """Check database connectivity."""
    try:
        from database.session import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "healthy"
    except Exception:
        logger.warning("Database health check failed", exc_info=True)
        return "unhealthy"


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
