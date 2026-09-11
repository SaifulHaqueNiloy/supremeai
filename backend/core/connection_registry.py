"""Central tenant-scoped registry for zero-friction capability connections."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl

from adaptive_engine._store import get_conn, jdump, jload
from core.plugins.mcp_security import MCPSecurityGuard


class ConnectionRecord(BaseModel):
    id: str
    tenant_id: str
    actor_id: str
    url: HttpUrl
    name: str
    connection_type: str = "mcp"
    permission_level: str = "user"
    status: str = "active"
    capabilities: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ConnectionRegistry:
    """Single source of truth for tenant-owned external capabilities."""

    TABLE = "supremeai_connections"

    def __init__(self) -> None:
        with get_conn() as conn:
            conn.execute(
                f"""CREATE TABLE IF NOT EXISTS {self.TABLE} (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    name TEXT NOT NULL,
                    connection_type TEXT NOT NULL,
                    permission_level TEXT NOT NULL DEFAULT 'user',
                    status TEXT NOT NULL,
                    capabilities TEXT NOT NULL DEFAULT '{{}}',
                    metadata TEXT NOT NULL DEFAULT '{{}}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(tenant_id, url)
                )"""
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{self.TABLE}_tenant ON {self.TABLE}(tenant_id)"
            )
            conn.commit()

    @staticmethod
    def _identity(user: dict[str, Any]) -> tuple[str, str, str]:
        tenant_id = str(user.get("tenant_id") or user.get("organization_id") or user.get("id"))
        actor_id = str(user.get("user_id") or user.get("id") or "unknown")
        role = str(user.get("role") or user.get("user_role") or "user").lower()
        if tenant_id in {"None", "unknown"}:
            raise PermissionError("Authenticated tenant context is required")
        return tenant_id, actor_id, role

    def register(
        self,
        *,
        user: dict[str, Any],
        url: str,
        capabilities: list[dict[str, Any]],
        name: str | None = None,
        permission_level: str = "user",
    ) -> ConnectionRecord:
        tenant_id, actor_id, role = self._identity(user)
        if not MCPSecurityGuard.is_safe_url(url, enforce_https=False):
            raise ValueError("URL blocked by SSRF / security policy")
        if permission_level not in {"user", "admin", "system"}:
            raise ValueError("permission_level must be user, admin, or system")
        if permission_level != "user" and role not in {"admin", "owner", "system"}:
            raise PermissionError("Only tenant administrators can escalate authority")

        now = datetime.now(UTC).isoformat()
        record = ConnectionRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            actor_id=actor_id,
            url=url,
            name=name or urlparse(url).hostname or "mcp-server",
            permission_level=permission_level,
            capabilities=capabilities,
            created_at=now,
            updated_at=now,
        )
        with get_conn() as conn:
            conn.execute(
                f"""INSERT INTO {self.TABLE}
                (id, tenant_id, actor_id, url, name, connection_type,
                 permission_level, status, capabilities, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id, url) DO UPDATE SET
                 capabilities=excluded.capabilities, name=excluded.name,
                 updated_at=excluded.updated_at, status='active'""",
                (record.id, record.tenant_id, record.actor_id, str(record.url), record.name,
                 record.connection_type, record.permission_level, record.status,
                 jdump(record.capabilities), jdump(record.metadata), record.created_at, record.updated_at),
            )
            conn.commit()
        return record

    def list_for_tenant(self, user: dict[str, Any]) -> list[ConnectionRecord]:
        tenant_id, _, _ = self._identity(user)
        with get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM {self.TABLE} WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,)
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: Any) -> ConnectionRecord:
        return ConnectionRecord(
            id=row["id"], tenant_id=row["tenant_id"], actor_id=row["actor_id"], url=row["url"],
            name=row["name"], connection_type=row["connection_type"],
            permission_level=row["permission_level"], status=row["status"],
            capabilities=jload(row["capabilities"], []), metadata=jload(row["metadata"], {}),
            created_at=row["created_at"], updated_at=row["updated_at"],
        )


connection_registry = ConnectionRegistry()

__all__ = ["ConnectionRecord", "ConnectionRegistry", "connection_registry"]
