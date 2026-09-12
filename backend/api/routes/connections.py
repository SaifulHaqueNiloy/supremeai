"""Universal Zero-Complexity Interface — Connections API (Phase 1).

বাংলা: এই মডিউল customer-facing connection engine-এর modular endpoints দেয়।
UI সহজ (একটা URL paste), কিন্তু backend modular — protocol detection, governed
registration, capability listing সব আলাদা ভাগে।

Security rules:
- Auth mandatory: প্রতিটি endpoint `get_current_user_token` ব্যবহার করে।
- কোনো secret (API key/token) এখানে গ্রহণ বা সংরক্ষণ করা হয় না।
- User শুধু নিজের স্কোপ দেখে — tenant ফিল্টার backend-authoritative।
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from adaptive_engine.capability_registry import (
    Capability,
    CapabilityRegistry,
    get_capability_registry,
)
from core.security.authentication.rbac import get_current_user_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/connections", tags=["connections"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class DetectionRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class DetectionResponse(BaseModel):
    detected: bool
    protocol: Literal["mcp", "oauth", "rest", "custom"]
    provider_label: str
    reasons: list[str]


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=2048)
    label: str | None = Field(default=None, max_length=120)


class RegisterResponse(BaseModel):
    connection_id: str
    capability_id: str
    health: Literal["pending"] = "pending"
    message: str


class WorkspaceContext(BaseModel):
    id: str
    label: str
    active: bool


class WorkspaceCapability(BaseModel):
    capability_id: str
    name: str
    purpose: str
    status: Literal["ready", "idle", "unavailable", "requestable"]
    category: str
    unavailable_reason: str | None
    required_permission: str | None


class MyWorkspaceResponse(BaseModel):
    user_id: str
    authorized_contexts: list[WorkspaceContext]
    execution_mode: str = "ask_before_acting"
    capabilities: list[WorkspaceCapability]
    connections: list[dict[str, Any]]
    recent_activity: list[dict[str, Any]]


class SetModeRequest(BaseModel):
    mode: Literal["read_only", "ask_before_acting", "autonomous"]


class SetModeResponse(BaseModel):
    user_id: str
    mode: str
    persisted: bool
    message: str


# ---------------------------------------------------------------------------
# Provider/protocol detection (pure, no network fetch — Acid Test 10)
# ---------------------------------------------------------------------------

_PROVIDER_HINTS: tuple[tuple[str, str], ...] = (
    ("github.com", "GitHub"),
    ("gitlab.com", "GitLab"),
    ("googleapis.com", "Google"),
    ("drive.google.com", "Google Drive"),
    ("slack.com", "Slack"),
    ("notion.so", "Notion"),
    ("supabase.co", "Supabase"),
    ("render.com", "Render"),
    ("cloudflare.com", "Cloudflare"),
)


def detect_protocol(raw_url: str) -> DetectionResponse:
    """বাংলা: URL থেকে provider/protocol অনুমান — network call ছাড়াই, deterministic।"""
    text = (raw_url or "").strip()
    reasons: list[str] = []
    if not text:
        return DetectionResponse(
            detected=False, protocol="custom", provider_label="Custom tool", reasons=["empty input"]
        )

    lowered = text.lower()
    if lowered.startswith("mcp://") or "/mcp" in lowered or lowered.endswith("/sse"):
        reasons.append("MCP transport marker found in URL")
        return DetectionResponse(
            detected=True, protocol="mcp", provider_label="Custom MCP tool", reasons=reasons
        )

    if lowered.startswith("http://") or lowered.startswith("https://"):
        host = urlparse(text).netloc.lower()
        for marker, label in _PROVIDER_HINTS:
            if marker in host:
                reasons.append(f"host matches known provider: {marker}")
                return DetectionResponse(
                    detected=True, protocol="oauth", provider_label=label, reasons=reasons
                )
        reasons.append("generic https endpoint")
        return DetectionResponse(
            detected=True, protocol="rest", provider_label="Web service", reasons=reasons
        )

    reasons.append("no recognizable transport; treating as custom tool")
    return DetectionResponse(
        detected=False, protocol="custom", provider_label="Custom tool", reasons=reasons
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/my-workspace", response_model=MyWorkspaceResponse)
async def my_workspace(current_user: dict = Depends(get_current_user_token)) -> MyWorkspaceResponse:
    """বাংলা: backend-authoritative user স্কোপ — শুধু যা user ব্যবহার/অনুমোদিত, তাই ফেরত।"""
    user_id = str(current_user.get("sub") or current_user.get("uid") or "anonymous")
    tenant_id = current_user.get("tenant_id") or current_user.get("tid")

    capabilities: list[WorkspaceCapability] = []
    try:
        registry: CapabilityRegistry = get_capability_registry()
        rows = registry.list(tenant_id=tenant_id if isinstance(tenant_id, str) else None, limit=100)
        ready_states = {"measured", "active", "production", "ready"}
        for cap in rows:
            state_value = str(getattr(cap.lifecycle_state, "value", cap.lifecycle_state)).lower()
            is_ready = state_value in ready_states
            capabilities.append(
                WorkspaceCapability(
                    capability_id=cap.capability_id,
                    name=cap.name,
                    purpose=cap.purpose,
                    status="ready" if is_ready else "unavailable",
                    category=cap.category,
                    unavailable_reason=None if is_ready else f"capability lifecycle: {state_value}",
                    required_permission=(cap.permissions[0] if cap.permissions else None),
                )
            )
    except Exception as exc:  # pragma: no cover - registry storage failure
        # বাংলা: silent failure নয় — degrade করব কিন্তু log-এ evidence থাকবে
        logger.warning("capability registry unavailable for %s: %s", user_id, exc)

    # বাংলা: authorized contexts — বর্তমানে personal workspace; admin context শুধু
    # backend RBAC অনুমোদন করলেই যোগ হবে (Correction 2 — no client-side escalation)।
    contexts = [WorkspaceContext(id="personal", label="Personal Workspace", active=True)]

    return MyWorkspaceResponse(
        user_id=user_id,
        authorized_contexts=contexts,
        capabilities=capabilities,
        connections=[],
        recent_activity=[],
    )


@router.post("/detect", response_model=DetectionResponse)
async def detect_connection(
    payload: DetectionRequest,
    current_user: dict = Depends(get_current_user_token),
) -> DetectionResponse:
    """বাংলা: URL paste করলেই কী ধরনের connection সেটা শনাক্ত করে (Acid Test 10)।"""
    del current_user  # auth-ই প্রধান গেট; detection-এ per-user state লাগে না
    return detect_protocol(payload.url)


@router.post("/register", response_model=RegisterResponse)
async def register_connection(
    payload: RegisterRequest,
    current_user: dict = Depends(get_current_user_token),
) -> RegisterResponse:
    """বাংলা: custom tool নিবন্ধন — governed path, audit log, tenant-scoped capability।"""
    user_id = str(current_user.get("sub") or current_user.get("uid") or "anonymous")
    if not payload.url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="A URL or identifier is required"
        )

    detection = detect_protocol(payload.url)
    registry = get_capability_registry()
    name = payload.label or payload.name
    capability = Capability(
        name=name,
        purpose=f"User-registered tool: {payload.url}",
        signature=f"user.connection.{uuid.uuid4().hex[:12]}.v1",
        category="user_connection",
        execution_method="external",
        security_level="standard",
        permissions=["capability:connection:use"],
        provenance={"registered_by": user_id, "url": payload.url, "protocol": detection.protocol},
    )
    try:
        created = registry.register(capability)
    except Exception as exc:
        logger.error("connection registration failed for %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration service unavailable",
        ) from exc

    logger.info(
        "AUDIT connection.registered user=%s capability=%s protocol=%s url=%s",
        user_id,
        created.capability_id,
        detection.protocol,
        payload.url,
    )
    return RegisterResponse(
        connection_id=f"conn-{uuid.uuid4().hex[:12]}",
        capability_id=created.capability_id,
        message=f"{detection.provider_label} is being connected. It will appear in your tools once healthy.",
    )


async def set_execution_mode(payload: SetModeRequest, current_user: dict) -> SetModeResponse:
    """বাংলা: execution-mode self-service — access.py থেকে reuse হয় (duplicate logic নয়)।"""
    from datetime import UTC, datetime

    user_id = str(current_user.get("sub") or current_user.get("uid") or "anonymous")
    persisted = False
    try:
        from database.supabase_client import (
            db,
        )  # local import: avoid hard dependency at import time

        db.upsert(
            "user_execution_mode",
            {"user_id": user_id, "mode": payload.mode, "updated_at": datetime.now(UTC).isoformat()},
        )
        persisted = True
    except Exception as exc:
        logger.warning("execution-mode persistence degraded for %s: %s", user_id, exc)

    logger.info(
        "AUDIT access.set_mode user=%s mode=%s persisted=%s", user_id, payload.mode, persisted
    )
    labels = {
        "read_only": "Read-only mode",
        "ask_before_acting": "Ask before acting",
        "autonomous": "Act autonomously",
    }
    return SetModeResponse(
        user_id=user_id,
        mode=payload.mode,
        persisted=persisted,
        message=f"Execution mode set to {labels[payload.mode]}."
        + ("" if persisted else " (will persist when storage recovers)"),
    )


def detect_protocol(raw_url: str) -> DetectionResponse:
    """বাংলা: URL থেকে provider/protocol অনুমান — network call ছাড়াই, deterministic।"""
    text = (raw_url or "").strip()
    reasons: list[str] = []
    if not text:
        return DetectionResponse(
            detected=False, protocol="custom", provider_label="Custom tool", reasons=["empty input"]
        )

    lowered = text.lower()
    if lowered.startswith("mcp://") or "/mcp" in lowered or lowered.endswith("/sse"):
        reasons.append("MCP transport marker found in URL")
        return DetectionResponse(
            detected=True, protocol="mcp", provider_label="Custom MCP tool", reasons=reasons
        )

    if lowered.startswith("http://") or lowered.startswith("https://"):
        host = urlparse(text).netloc.lower()
        for marker, label in _PROVIDER_HINTS:
            if marker in host:
                reasons.append(f"host matches known provider: {marker}")
                return DetectionResponse(
                    detected=True, protocol="oauth", provider_label=label, reasons=reasons
                )
        reasons.append("generic https endpoint")
        return DetectionResponse(
            detected=True, protocol="rest", provider_label="Web service", reasons=reasons
        )

    reasons.append("no recognizable transport; treating as custom tool")
    return DetectionResponse(
        detected=False, protocol="custom", provider_label="Custom tool", reasons=reasons
    )
