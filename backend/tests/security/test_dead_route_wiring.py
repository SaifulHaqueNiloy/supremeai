"""Regression guard: previously-dead admin/health routes must import and be wired.

Audit session (2026-08-30) found two silent dead-route defects:

1. ``core/deployment_fallback_defaults.py`` exported only ``BACKEND_URL_DEFAULT``,
   but ``api/routes/health_aggregation.py`` (registered in ``ALL_ROUTERS``) and
   ``api/routes/service_topology.py`` both imported the nonexistent
   ``ADMIN_URL_DEFAULT`` / ``SCRAPER_URL_DEFAULT`` → ImportError at boot →
   ``health_aggregation`` was silently skipped (optional=True) on every deploy.
2. ``api/routes/service_topology.py`` (admin service health checker + CI-dashboard
   WebSocket health-stream) was additionally never registered in ``ALL_ROUTERS``
   — doubly dead.
3. ``api/routes/__init__.py`` imported ``.llm_gateway`` (module does not exist;
   real module is ``llm_gateway_routes``) → fake warning log on every boot.

These tests lock the fixes in.
"""

from __future__ import annotations

import importlib


class TestDeploymentFallbackDefaults:
    def test_admin_url_default_exported(self):
        from core.deployment_fallback_defaults import ADMIN_URL_DEFAULT  # noqa: F401

    def test_scraper_url_default_exported(self):
        from core.deployment_fallback_defaults import SCRAPER_URL_DEFAULT  # noqa: F401

    def test_defaults_are_strings_no_hardcoded_host(self):
        """Policy: no hardcoded deployment hostnames (CI checker enforced)."""
        from core.deployment_fallback_defaults import (
            ADMIN_URL_DEFAULT,
            BACKEND_URL_DEFAULT,
            SCRAPER_URL_DEFAULT,
        )

        assert isinstance(BACKEND_URL_DEFAULT, str)
        assert isinstance(ADMIN_URL_DEFAULT, str)
        assert isinstance(SCRAPER_URL_DEFAULT, str)
        for value in (BACKEND_URL_DEFAULT, ADMIN_URL_DEFAULT, SCRAPER_URL_DEFAULT):
            if value:
                assert not value.startswith(("http://", "https://")) or "." in value


class TestPreviouslyDeadRoutesImport:
    def test_health_aggregation_module_imports(self):
        module = importlib.import_module("api.routes.health_aggregation")
        assert hasattr(module, "router")

    def test_service_topology_module_imports(self):
        module = importlib.import_module("api.routes.service_topology")
        assert hasattr(module, "router")

    def test_routes_init_imports_llm_gateway_cleanly(self, caplog):
        import api.routes  # noqa: F401  (import must not raise)

        # The stale `.llm_gateway` import previously logged
        # "Router import failed for llm_gateway_router" on every boot.
        assert not any(
            "Router import failed for llm_gateway_router" in rec.message for rec in caplog.records
        )


class TestRouterWiring:
    def test_service_topology_registered_in_all_routers(self):
        from api.routers import ALL_ROUTERS

        entry = next((r for r in ALL_ROUTERS if r["path"] == "api.routes.service_topology"), None)
        assert entry is not None, "service_topology must be registered in ALL_ROUTERS"
        assert entry["is_admin"] is True

    def test_health_aggregation_registered_in_all_routers(self):
        from api.routers import ALL_ROUTERS

        assert any(r["path"] == "api.routes.health_aggregation" for r in ALL_ROUTERS)
