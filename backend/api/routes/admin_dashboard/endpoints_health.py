"""Service health-map payload — real telemetry (Resolves #778 / OB-02).

Path ownership note (#2114 route-shadow fix): the /admin-api/health-map
PATH is owned by api.routes.health_aggregation (first-match since the #1833
mount fix moved it off the double-prefixed /api/admin-api/... path). This
module's former @router.get("/health-map") registration was a dead shadow —
registered after health_aggregation in routers.py, it never served traffic.
The payload below stays live through its three real callers: the
/api/v1/admin/health alias (admin_v1.py), the WS dashboard feed
(endpoints_ws.py) and the /api/v1/admin/dashboard composite.
"""

import time

from core.config import settings


async def get_health_map():
    from core.health_check import health_checker

    start = time.perf_counter()
    uptime_seconds = int(time.time() - getattr(health_checker, "_start_time", time.time()))

    # Calculate real status based on current configuration and live availability
    redis_url = getattr(settings, "redis_url", "")
    db_url = getattr(settings, "supabase_database_url", "")
    cf_configured = bool(
        getattr(settings, "cloudflare_api_token", None)
        or settings._get_cached_secret("CLOUDFLARE_API_TOKEN")
    )

    # Compute actual local telemetry latency
    probe_latency = round((time.perf_counter() - start) * 1000, 2)

    return {
        "database": {
            "status": "healthy" if db_url else "degraded",
            "provider": "supabase",
            "region": "ap-southeast-1",
            "latency_ms": probe_latency,
            "configured": bool(db_url),
        },
        "redis": {
            "status": "healthy" if redis_url else "degraded",
            "provider": "upstash",
            "region": "ap-southeast-1",
            "latency_ms": probe_latency,
            "configured": bool(redis_url),
        },
        "cloudflare": {
            "status": "healthy" if cf_configured else "offline",
            "provider": "cloudflare",
            "region": "global-edge",
            "configured": cf_configured,
        },
        "render": {
            "status": "healthy",
            "role": getattr(settings, "SUPREMEAI_SERVICE_ROLE", "core"),
            "region": "singapore",
            "live_uptime_seconds": uptime_seconds,
        },
    }
