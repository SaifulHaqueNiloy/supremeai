"""Secret scanner for SupremeAI.

Scans source trees for accidentally committed secrets (API keys, private
keys, tokens). Dependency-free, uses only the standard library.
"""

from __future__ import annotations

import os
import re
from typing import Any

# (pattern, human-readable label)
_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key"),
    (re.compile(r"aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}"), "AWS Secret Key"),
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"), "Private Key"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI API Key"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack Token"),
    (re.compile(r"ghp_[A-Za-z0-9]{36,}"), "GitHub PAT"),
    (re.compile(r"(?:password|passwd|secret|token|api_key)\s*[:=]\s*['\"]?[A-Za-z0-9_\\-]{12,}"), "Hardcoded Secret"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "JWT"),
]

_SKIP_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
}


class SecretScanner:
    """Walks a directory tree and reports candidate secret leaks."""

    def __init__(self, max_file_bytes: int = 5_000_000) -> None:
        self.max_file_bytes = max_file_bytes

    def scan_directory(self, path: str = ".", check_git_history: bool = False) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        scanned = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    if os.path.getsize(fpath) > self.max_file_bytes:
                        continue
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                except (OSError, UnicodeDecodeError):
                    continue
                scanned += 1
                for pattern, label in _SECRET_PATTERNS:
                    for match in pattern.finditer(content):
                        findings.append(
                            {
                                "file": os.path.relpath(fpath, path),
                                "type": label,
                                "line": content.count("\n", 0, match.start()) + 1,
                                "match": match.group(0)[:40],
                            }
                        )
        return {
            "status": "leaks_found" if findings else "clean",
            "scanned_files": scanned,
            "findings": findings,
        }


secret_scanner = SecretScanner()
