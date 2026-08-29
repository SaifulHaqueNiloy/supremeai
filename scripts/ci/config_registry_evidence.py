#!/usr/bin/env python3
"""Generate an evidence report for runtime configuration registry migration.

This tool intentionally does not mutate the canonical registry. It extracts the
runtime aliases that the existing contract checker understands and reports which
ones are already canonical/aliased. Classification is left for evidence-based
review instead of guessing from variable names.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLASSIFICATION = ROOT / "backend" / "core" / "config_classification.py"


def load_registry():
    spec = importlib.util.spec_from_file_location("supremeai_config_classification", CLASSIFICATION)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {CLASSIFICATION}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module.BY_NAME, module.ALIAS_TO_CANONICAL


def runtime_aliases() -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for path in (ROOT / "backend" / "core").glob("config*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id != "Field":
                continue
            for kw in node.keywords:
                if kw.arg != "validation_alias" or not isinstance(kw.value, ast.Constant):
                    continue
                if not isinstance(kw.value.value, str):
                    continue
                key = kw.value.value
                found.setdefault(key, []).append(str(path.relative_to(ROOT)))
    return found


def main() -> int:
    by_name, aliases = load_registry()
    runtime = runtime_aliases()
    report = []
    for key in sorted(runtime):
        canonical = aliases.get(key, key)
        spec = by_name.get(canonical)
        report.append({
            "key": key,
            "canonical": canonical if spec else None,
            "status": "classified" if spec else "unclassified",
            "evidence": sorted(set(runtime[key])),
            "review_required": spec is None,
        })

    payload = {
        "schema_version": 1,
        "source": "backend/core/config*.py Field(validation_alias=...)",
        "total_runtime_keys": len(report),
        "classified": sum(x["status"] == "classified" for x in report),
        "unclassified": sum(x["status"] == "unclassified" for x in report),
        "keys": report,
    }
    output = ROOT / "config_registry_evidence.json"
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("total_runtime_keys", "classified", "unclassified")}, indent=2))
    print(f"Wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
