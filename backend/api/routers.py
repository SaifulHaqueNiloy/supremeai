"""Centralized router registration for SupremeAI API."""

from __future__ import annotations

from fastapi import FastAPI
from loguru import logger

from api import register_router
from core.config import settings


core_routers: list[tuple[str, str]] = [
    ("api.routes.memory", ""),
    ("api.routes.task", ""),
    ("api.routes.markdown", "/api/v1"),
    ("api.routes.simulator", ""),
    ("api.routes.site_actions", ""),
    ("api.routes.llm_gateway", ""),
    ("api.routes.browser", ""),
    ("api.routes.stream", ""),
    ("api.routes.media", ""),
    ("api.routes.graph", ""),
    ("api.routes.marketplace_endpoints", ""),
    ("api.routes.auth", "/api/v1"),
    ("api.routes.onboarding", "/api/v1"),
    ("api.routes.evolution", "/api/v1"),
    ("api.routes.meta_ai", "/api/v1"),
    ("api.routes.localization", "/api/v1"),
    ("api.routes.analytics", "/api/v1"),
    ("api.routes.admin_dashboard", ""),
    ("api.routes.email", ""),
    ("api.routes.github", ""),
    ("api.routes.internal", ""),
    ("api.routes.config", ""),
    ("api.routes.repos", ""),
    ("api.routes.tools_ops", ""),
    ("api.routes.agents", ""),
    ("api.routes.agent", ""),
    ("api.routes.admin", ""),
    ("api.routes.tools_registry", ""),
    ("api.routes.preferences", "/api"),
    ("api.routes.usage_metrics", ""),
    ("api.routes.sso", ""),
    ("api.routes.health", "/api/v1"),
    ("api.routes.api_keys", ""),
    ("api.routes.ci_webhooks", ""),
    ("api.routes.task_workspace", "/api/v1"),
    ("api.routes.websocket_agent", ""),
    ("api.routes.agent_workspace", "/api/v1"),
    ("api.routes.integrations", "/api/v1"),
    ("api.routes.public_config", "/api"),
    ("api.routes.traffic_monitor", ""),
    ("api.routes.agent_action", "/api/v1"),
    ("api.routes.websocket_hitl", ""),
    ("api.routes.syncguard", "/api/v1"),
    ("api.routes.admin_librarian", "/api"),
    ("api.routes.skills", "/api"),
]

optional_routers: list[tuple[str, str]] = [
    # বাংলা মন্তব্য: chromadb নির্ভর হওয়ায় নলেজ বেস রাউটারটিকে অপশনাল হিসেবে রেজিস্টার করা হলো
    ("api.routes.knowledge", ""),
    ("api.routes.dock_actions", "/api"),
    ("api.routes.websocket_voice", ""),
    ("tools.collaborative_editor", "/api/v1"),
    ("tools.image_to_code", ""),
    ("tools.browser_agent", "/api"),
    ("tools.voice_coder", "/api"),
    ("tools.style_learner", "/api"),
    ("tools.diagram_to_architecture", "/api"),
    ("tools.ai_pair_programmer", "/api"),
    ("api.routes.codeflow", ""),
    ("api.routes.feedback", ""),
    ("tools.media.multilingual_tts", "/api"),
    ("api.routes.voice", "/api/voice"),
    ("tools.comment_thread_ai", "/api"),
    ("tools.auto_test_generator", "/api"),
    ("api.routes.tenant_admin", "/api"),
    ("api.routes.mobile_bff", ""),
    ("api.routes.billing_api", ""),
    ("api.routes.metrics", ""),
    ("api.routes.cloud_mesh", ""),
    ("api.routes.events", "/api"),
    ("api.routes.payments", ""),
    ("api.routes.maintenance", "/api/v1"),
    ("api.routes.sandbox_api", ""),
    ("api.routes.pr_review_api", ""),
]


def register_all_routers(app: FastAPI) -> None:
    """Register all core and optional routers on the FastAPI app."""
    for router_path, prefix in core_routers:
        register_router(app, router_path, prefix=prefix, optional=False)

    for router_path, prefix in optional_routers:
        register_router(app, router_path, prefix=prefix, optional=True)

    if settings.encryption_key and settings.encryption_key.get_secret_value():
        register_router(app, "api.routes.byoc_api", "", optional=True)
    else:
        logger.warning("Universal BYOC router not loaded: ENCRYPTION_KEY missing")


__all__ = ["register_all_routers", "core_routers", "optional_routers"]
