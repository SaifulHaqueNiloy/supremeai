#!/usr/bin/env python3
"""Aggregate machine-readable security reports for the fast CI security gate.

The helper is intentionally small and offline. Individual scanners remain the
source of truth; this command only normalizes their blocking status so CI has a
single fail-closed decision point.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BLOCKING_LEVELS = {"critical", "high"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def severities(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_l = str(key).lower()
            if key_l in {"severity", "level", "priority"} and isinstance(child, str):
                found.append(child.lower())
            else:
                found.extend(severities(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(severities(child))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path, default=Path("ci-reports/security-gate.json"))
    args = parser.parse_args()

    reports: list[dict[str, Any]] = []
    blocking: list[dict[str, str]] = []
    missing: list[str] = []

    for path in args.report:
        if not path.is_file():
            missing.append(str(path))
            continue
        try:
            data = load(path)
        except (OSError, json.JSONDecodeError) as exc:
            blocking.append({"report": str(path), "reason": f"unreadable report: {exc}"})
            continue
        levels = sorted(set(severities(data)) & BLOCKING_LEVELS)
        reports.append({"report": str(path), "blocking_severities": levels})
        for level in levels:
            blocking.append({"report": str(path), "severity": level})

    # A missing report is a gate failure: a scanner that silently produced no
    # evidence must never become an accidental bypass of the aggregate gate.
    for path in missing:
        blocking.append({"report": path, "reason": "required report missing"})

    result = {
        "status": "fail" if blocking else "pass",
        "reports": reports,
        "missing_reports": missing,
        "blocking_findings": blocking,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
