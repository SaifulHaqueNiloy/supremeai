"""Provider-neutral durable task, artifact, and browser adapter contracts."""
from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .canonical import ExecutionContext
from .security_policy import SandboxMode


class ArtifactKind(StrEnum):
    OUTPUT = "output"
    EVIDENCE = "evidence"
    SCREENSHOT = "screenshot"


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    context: ExecutionContext
    name: str
    content_type: str
    size_bytes: int
    sha256: str
    kind: ArtifactKind


class ArtifactStore(Protocol):
    def put(self, context: ExecutionContext, name: str, content: bytes, kind: ArtifactKind) -> Artifact: ...
    def get(self, context: ExecutionContext, artifact_id: str) -> bytes: ...


class TaskAdapter(Protocol):
    def enqueue(self, context: ExecutionContext, task_type: str, payload: dict) -> str: ...
    def cancel(self, context: ExecutionContext, task_id: str) -> None: ...


class BrowserAdapter(Protocol):
    def open(self, context: ExecutionContext, url: str, mode: SandboxMode = SandboxMode.READ_ONLY) -> str: ...
    def close(self, context: ExecutionContext, session_id: str) -> None: ...


def validate_artifact(name: str, content: bytes, max_bytes: int = 10 * 1024 * 1024) -> tuple[str, int, str]:
    if not name or name.startswith("/") or ".." in name.split("/"):
        raise ValueError("invalid artifact name")
    if len(content) > max_bytes:
        raise ValueError("artifact exceeds size limit")
    content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
    return content_type, len(content), hashlib.sha256(content).hexdigest()
