"""Centralized router registration for SupremeAI API."""

from __future__ import annotations

from fastapi import Depends, FastAPI
from loguru import logger

from api import register_router
from api.deps import get_current_user_token
from core.config import settings

# Unified declarative registry of all routers.
# Format: {"path": str, "prefix": str, "is_admin": bool, "is_critical": bool}
# Deduplicated and cleaned up according to Phase 2 API Cleanup.
ALL_ROUTERS = [
    # ---- Core & User Routes ----
    {"path": "api.routes.memory", "prefix": "", "is_admin": False, "is_critical": False},
    {
        "path": "api.routes.unified_memory_api",
        "prefix": "",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.task", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.markdown", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {"path": "api.routes.simulator", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.stream", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.media", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.graph", "prefix": "", "is_admin": False, "is_critical": False},
    {
        "path": "api.routes.marketplace_endpoints",
        "prefix": "",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.auth", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {"path": "api.routes.onboarding", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {
        "path": "api.routes.localization",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.analytics", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {"path": "api.routes.email", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.github", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.config", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.economics", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {"path": "api.routes.cognitive", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {
        "path": "api.routes.cache_predictions",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    {
        "path": "api.routes.digital_twin",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.healing", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {"path": "api.routes.repos", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.agents", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.agent", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.tools_registry", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.skills", "prefix": "/api", "is_admin": False, "is_critical": False},
    {"path": "api.routes.files", "prefix": "/api", "is_admin": False, "is_critical": False},
    {"path": "api.routes.usage_metrics", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.sso", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.api_keys", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.ci_webhooks", "prefix": "", "is_admin": False, "is_critical": False},
    {
        "path": "api.routes.task_workspace",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.websocket_agent", "prefix": "", "is_admin": False, "is_critical": False},
    {
        "path": "api.routes.agent_workspace",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    {
        "path": "api.routes.integrations",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.admin_v1", "prefix": "", "is_admin": False, "is_critical": False},
    {
        "path": "api.routes.agent_action",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.websocket_hitl", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.syncguard", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {
        "path": "api.routes.session_stream",
        "prefix": "/api",
        "is_admin": False,
        "is_critical": False,
    },
    {
        "path": "api.routes.swarm",
        "prefix": "/api/v1/swarm",
        "is_admin": False,
        "is_critical": False,
    },
    {
        "path": "api.routes.realtime_dashboard",
        "prefix": "",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.ci_dashboard_api", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.living_engine", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.scraper", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {"path": "api.routes.kaggle", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.dock_actions", "prefix": "/api", "is_admin": False, "is_critical": False},
    {"path": "api.routes.websocket_voice", "prefix": "", "is_admin": False, "is_critical": False},
    {
        "path": "tools.collaborative_editor",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "tools.code.image_to_code", "prefix": "", "is_admin": False, "is_critical": False},
    {
        "path": "tools.learning.style_learner",
        "prefix": "/api",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.codeflow", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.feedback", "prefix": "", "is_admin": False, "is_critical": False},
    {
        "path": "tools.media.multilingual_tts",
        "prefix": "/api",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.voice", "prefix": "/api/voice", "is_admin": False, "is_critical": False},
    {"path": "tools.comment_thread_ai", "prefix": "/api", "is_admin": False, "is_critical": False},
    {"path": "api.routes.mobile_bff", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.payments", "prefix": "", "is_admin": False, "is_critical": False},
    {
        "path": "api.routes.maintenance",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.sandbox_api", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.routes.pr_review_api", "prefix": "", "is_admin": False, "is_critical": False},
    {"path": "api.v1.telemetry", "prefix": "/api", "is_admin": False, "is_critical": False},
    {
        "path": "tools.social.telegram_bot",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.keys", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {
        "path": "api.routes.conversations",
        "prefix": "/api/v1",
        "is_admin": False,
        "is_critical": False,
    },
    # ---- Critical Routes ----
    {"path": "api.routes.llm_gateway", "prefix": "", "is_admin": False, "is_critical": True},
    {"path": "api.routes.knowledge", "prefix": "/api", "is_admin": False, "is_critical": True},
    {"path": "api.routes.billing_api", "prefix": "", "is_admin": False, "is_critical": True},
    # ---- Admin & Health Routes ----
    {
        "path": "api.routes.health_aggregation",
        "prefix": "/api",
        "is_admin": False,
        "is_critical": False,
    },
    {"path": "api.routes.health", "prefix": "/api/v1", "is_admin": False, "is_critical": False},
    {"path": "api.routes.public_config", "prefix": "/api", "is_admin": False, "is_critical": False},
    {"path": "api.routes.preferences", "prefix": "/api", "is_admin": False, "is_critical": False},
    {"path": "api.routes.simulator_admin", "prefix": "", "is_admin": True, "is_critical": False},
    {"path": "api.routes.site_actions", "prefix": "", "is_admin": True, "is_critical": False},
    {"path": "api.routes.browser_routes", "prefix": "", "is_admin": True, "is_critical": False},
    {"path": "api.routes.evolution", "prefix": "/api/v1", "is_admin": True, "is_critical": False},
    {"path": "api.routes.meta_ai", "prefix": "/api/v1", "is_admin": True, "is_critical": False},
    {"path": "api.routes.admin_dashboard", "prefix": "", "is_admin": True, "is_critical": False},
    {"path": "api.routes.internal", "prefix": "", "is_admin": True, "is_critical": False},
    {"path": "api.routes.admin", "prefix": "", "is_admin": True, "is_critical": False},
    {"path": "api.routes.traffic_monitor", "prefix": "", "is_admin": True, "is_critical": False},
    {
        "path": "api.routes.admin_librarian",
        "prefix": "/api",
        "is_admin": True,
        "is_critical": False,
    },
    {"path": "api.routes.tenant_admin", "prefix": "/api", "is_admin": True, "is_critical": False},
    {"path": "api.routes.metrics", "prefix": "", "is_admin": True, "is_critical": False},
    {"path": "api.routes.cloud_mesh", "prefix": "", "is_admin": True, "is_critical": False},
    {"path": "api.routes.tools_ops", "prefix": "", "is_admin": True, "is_critical": False},
    {"path": "api.routes.execution_policies", "prefix": "", "is_admin": True, "is_critical": False},
    {"path": "api.routes.living_brain", "prefix": "", "is_admin": True, "is_critical": False},
]


def register_all_routers(app: FastAPI) -> None:
    """Register all unified routers on the FastAPI app."""
    for router_def in ALL_ROUTERS:
        path = router_def["path"]
        prefix = router_def["prefix"]
        is_admin = router_def["is_admin"]
        is_critical = router_def["is_critical"]

        deps = [Depends(get_current_user_token)] if is_admin else None

        if is_critical:
            logger.info(f"Loading critical router: {path}")
            register_router(app, path, prefix=prefix, optional=False, dependencies=deps)
        else:
            register_router(app, path, prefix=prefix, optional=True, dependencies=deps)

    # BYOC Router logic remains unchanged
    if settings.encryption_key and settings.encryption_key.get_secret_value():
        register_router(app, "api.routes.byoc_api", "", optional=True)
    else:
        logger.warning("Universal BYOC router not loaded: ENCRYPTION_KEY missing")


def include_user_routers(app: FastAPI) -> None:
    """For compatibility/tests - registers non-admin routers."""
    for router_def in ALL_ROUTERS:
        if not router_def["is_admin"]:
            register_router(app, router_def["path"], prefix=router_def["prefix"], optional=True)


def include_admin_routers(app: FastAPI) -> None:
    """For compatibility/tests - registers admin routers."""
    for router_def in ALL_ROUTERS:
        if router_def["is_admin"]:
            deps = [Depends(get_current_user_token)]
            register_router(
                app,
                router_def["path"],
                prefix=router_def["prefix"],
                optional=True,
                dependencies=deps,
            )


__all__ = [
    "ALL_ROUTERS",
    "include_admin_routers",
    "include_user_routers",
    "register_all_routers",
]
