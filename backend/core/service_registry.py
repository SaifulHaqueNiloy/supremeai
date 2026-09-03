"""Canonical server-side registry for SupremeAI runtime services."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ServiceDefinition:
    id: str
    display_name: str
    role: str
    base_url_env: str
    health_path: str
    capabilities: tuple[str, ...]
    critical: bool = False

    def public_dict(self) -> dict[str, Any]:
        configured = bool(os.getenv(self.base_url_env))
        return {
            "id": self.id,
            "display_name": self.display_name,
            "role": self.role,
            "capabilities": list(self.capabilities),
            "critical": self.critical,
            "configured": configured,
            "health_path": self.health_path,
        }


SERVICE_REGISTRY: tuple[ServiceDefinition, ...] = (
    ServiceDefinition(
        "core-api", "Core API", "core", "BACKEND_URL", "/api/v1/health/live",
        ("chat", "memory", "artifacts", "orchestration"), True,
    ),
    ServiceDefinition(
        "async-worker", "Async Worker", "worker", "WORKER_URL", "/health",
        ("tasks.submit", "tasks.status", "tasks.cancel"),
    ),
    ServiceDefinition(
        "scraper", "Scraper", "scraper", "SCRAPER_URL", "/health",
        ("browser.research", "browser.scrape", "browser.artifacts"),
    ),
    ServiceDefinition(
        "mcp-control-plane", "MCP Control Plane", "mcp", "MCP_URL", "/health",
        ("mcp.discover", "mcp.call", "infrastructure.health"),
    ),
)


def get_service(service_id: str) -> ServiceDefinition | None:
    return next((service for service in SERVICE_REGISTRY if service.id == service_id), None)


def public_registry() -> list[dict[str, Any]]:
    return [service.public_dict() for service in SERVICE_REGISTRY]


def service_url(service: ServiceDefinition) -> str | None:
    value = os.getenv(service.base_url_env)
    return value.rstrip("/") if value else None


def public_capabilities() -> list[dict[str, Any]]:
    return [
        {"id": capability, "service_id": service.id, "available": bool(service_url(service))}
        for service in SERVICE_REGISTRY
        for capability in service.capabilities
    ]


__all__ = ["SERVICE_REGISTRY", "ServiceDefinition", "get_service", "public_capabilities", "public_registry", "service_url"]
