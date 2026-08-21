"""
Thin-Client Token Broker & Security Gate (Keycloak & IAM Pattern).
Provides scoped, ephemeral JWT/HMAC action tokens for Thin Clients (VS Code, Studio)
with Role-Based and Attribute-Based Access Control (RBAC/ABAC).
Ensures zero-leak of master API keys and strict execution sandboxing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from loguru import logger


class ClientRole(str, Enum):
    ANONYMOUS = "anonymous"
    DEVELOPER = "developer"
    ADMIN = "admin"
    AGENT_INTERNAL = "agent_internal"


class ActionScope(str, Enum):
    CODE_READ = "code:read"
    CODE_WRITE = "code:write"
    EXEC_BASH = "exec:bash"
    GIT_COMMIT = "git:commit"
    SCHEMA_MODIFY = "schema:modify"
    WORKFLOW_RUN = "workflow:run"
    ADMIN_ALL = "admin:*"


ROLE_DEFAULT_SCOPES: dict[ClientRole, list[ActionScope]] = {
    ClientRole.ANONYMOUS: [ActionScope.CODE_READ],
    ClientRole.DEVELOPER: [
        ActionScope.CODE_READ,
        ActionScope.CODE_WRITE,
        ActionScope.EXEC_BASH,
        ActionScope.GIT_COMMIT,
        ActionScope.WORKFLOW_RUN,
    ],
    ClientRole.AGENT_INTERNAL: [
        ActionScope.CODE_READ,
        ActionScope.CODE_WRITE,
        ActionScope.EXEC_BASH,
        ActionScope.GIT_COMMIT,
        ActionScope.SCHEMA_MODIFY,
        ActionScope.WORKFLOW_RUN,
    ],
    ClientRole.ADMIN: [ActionScope.ADMIN_ALL],
}


@dataclass
class TokenPayload:
    sub: str
    role: ClientRole
    scopes: list[str]
    exp: int
    iat: int
    jti: str
    metadata: dict[str, Any] = field(default_factory=dict)


class TokenSecurityBroker:
    """
    Token Broker implementing Keycloak-like claims and fine-grained authorization checks.
    """

    def __init__(self, secret_key: str = "supremeai-internal-keycloak-broker-secret-32b"):
        self.secret_key = secret_key.encode("utf-8")

    def _sign(self, data: bytes) -> str:
        sig = hmac.new(self.secret_key, data, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")

    def generate_action_token(
        self,
        user_id: str,
        role: ClientRole = ClientRole.DEVELOPER,
        custom_scopes: list[ActionScope] | None = None,
        ttl_seconds: int = 3600,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        now = int(time.time())
        scopes = [s.value for s in (custom_scopes or ROLE_DEFAULT_SCOPES.get(role, []))]

        payload = {
            "sub": user_id,
            "role": role.value,
            "scopes": scopes,
            "iat": now,
            "exp": now + ttl_seconds,
            "jti": uuid.uuid4().hex,
            "metadata": metadata or {},
        }

        header = {"alg": "HS256", "typ": "JWT"}
        enc_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        enc_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

        signing_input = f"{enc_header}.{enc_payload}".encode("utf-8")
        signature = self._sign(signing_input)

        token = f"{enc_header}.{enc_payload}.{signature}"
        return token

    def verify_token(self, token: str) -> TokenPayload | None:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None

            enc_header, enc_payload, signature = parts
            signing_input = f"{enc_header}.{enc_payload}".encode("utf-8")
            expected_sig = self._sign(signing_input)

            if not hmac.compare_digest(signature, expected_sig):
                logger.warning("Token signature mismatch.")
                return None

            # Add padding back if necessary
            rem = len(enc_payload) % 4
            pad_payload = enc_payload + ("=" * (4 - rem) if rem else "")
            payload_data = json.loads(base64.urlsafe_b64decode(pad_payload).decode("utf-8"))

            now = int(time.time())
            if payload_data.get("exp", 0) < now:
                logger.warning("Token has expired.")
                return None

            return TokenPayload(
                sub=payload_data["sub"],
                role=ClientRole(payload_data.get("role", "developer")),
                scopes=payload_data.get("scopes", []),
                exp=payload_data["exp"],
                iat=payload_data["iat"],
                jti=payload_data["jti"],
                metadata=payload_data.get("metadata", {}),
            )
        except Exception as exc:
            logger.warning(f"Failed to verify token: {exc}")
            return None

    def authorize(self, token: str | None, required_scope: ActionScope) -> bool:
        if not token:
            return False
        payload = self.verify_token(token)
        if not payload:
            return False

        if ActionScope.ADMIN_ALL.value in payload.scopes:
            return True
        return required_scope.value in payload.scopes
