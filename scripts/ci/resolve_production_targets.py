#!/usr/bin/env python3
"""Canonical Production Target Resolution for SupremeAI Live Smoke & Certification (issue #1132).

Provides a single authoritative resolver contract for production targets across:
  - qa-live-smoke.yml (scheduled continuous live-verification)
  - 09-post-deploy-smoke.yml (post-deploy smoke canary & health probe)
  - Release certification (#1096) and secondary service probes (#1100)

Doctrine & Guarantees:
  1. Zero-hardcode: Never invent localhost/placeholder/mock fallback URLs.
  2. Distinct UI vs API: Firebase Hosting is an SPA host; backend API is Render.
     Canary Playwright selectors live on UI origin; API health/ready live on API origin.
     Never silently conflate them unless same-origin fallback is explicitly requested.
  3. Precedence & Provenance:
     - UI Origin:
       1. FRONTEND_PRODUCTION_URL (owner override)
       2. FIREBASE_PROJECT_ID -> https://{project}.web.app
       3. (unresolved if neither is set)
     - API Origin:
       1. PRODUCTION_URL (owner override)
       2. RENDER_CORE_URL (Infisical prod vault or env)
       3. same-origin fallback ONLY IF explicitly enabled AND ui_origin is set
       4. (unresolved if none of above)
  4. Fail-closed Honesty:
     Every row carries timestamped provenance. Unresolved targets remain empty strings
     with descriptive provenance explaining what was missing, preventing false PASSes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ResolvedTargets:
    ui_origin: str
    ui_source: str
    api_origin: str
    api_source: str
    qa_base_url: str
    backend_health_url: str
    health_url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_url(url: str | None) -> str:
    if not url:
        return ""
    cleaned = url.strip()
    return cleaned.rstrip("/")


def resolve_targets(
    *,
    explicit_production_url: str | None = None,
    frontend_production_url: str | None = None,
    firebase_project_id: str | None = None,
    render_core_url: str | None = None,
    allow_same_origin_fallback: bool = False,
) -> ResolvedTargets:
    """Resolve UI and API origins with explicit precedence and provenance."""
    explicit_api = _clean_url(explicit_production_url)
    explicit_frontend = _clean_url(frontend_production_url)
    firebase_proj = (firebase_project_id or "").strip()
    render_core = _clean_url(render_core_url)

    # 1. Resolve UI Origin
    if explicit_frontend:
        ui_origin = explicit_frontend
        ui_source = "FRONTEND_PRODUCTION_URL (owner override)"
    elif firebase_proj:
        ui_origin = f"https://{firebase_proj}.web.app"
        ui_source = f"FIREBASE_PROJECT_ID-derived ({firebase_proj}.web.app) — SPA hosting"
    else:
        ui_origin = ""
        ui_source = "unresolved (neither FRONTEND_PRODUCTION_URL nor FIREBASE_PROJECT_ID configured)"

    # 2. Resolve API Origin
    if explicit_api:
        api_origin = explicit_api
        api_source = "PRODUCTION_URL (owner override)"
    elif render_core:
        api_origin = render_core
        api_source = "RENDER_CORE_URL (Infisical prod)"
    elif allow_same_origin_fallback and ui_origin:
        api_origin = ui_origin
        api_source = "same-origin fallback (UI origin; rewrite chain is the API path)"
    else:
        api_origin = ""
        api_source = "unresolved (neither PRODUCTION_URL nor RENDER_CORE_URL configured)"

    # Aliases for backward compatibility across legacy workflows
    qa_base_url = ui_origin
    backend_health_url = api_origin
    health_url = f"{api_origin}/api/v1/health" if api_origin else ""

    return ResolvedTargets(
        ui_origin=ui_origin,
        ui_source=ui_source,
        api_origin=api_origin,
        api_source=api_source,
        qa_base_url=qa_base_url,
        backend_health_url=backend_health_url,
        health_url=health_url,
    )


def resolve_targets_from_env(
    env: Mapping[str, str] | None = None,
    *,
    allow_same_origin_fallback: bool = False,
) -> ResolvedTargets:
    """Resolve targets from environment variables or supplied mapping."""
    e = os.environ if env is None else env
    explicit_prod = e.get("EXPLICIT_PRODUCTION_URL") or e.get("PRODUCTION_URL")
    frontend_prod = e.get("FRONTEND_PRODUCTION_URL")
    firebase_proj = e.get("FIREBASE_PROJECT_ID") or e.get("FIREBASE_PROJECT")
    render_core = e.get("RENDER_CORE_URL") or e.get("RENDER_CORE")

    return resolve_targets(
        explicit_production_url=explicit_prod,
        frontend_production_url=frontend_prod,
        firebase_project_id=firebase_proj,
        render_core_url=render_core,
        allow_same_origin_fallback=allow_same_origin_fallback,
    )


def write_to_github_env(targets: ResolvedTargets, github_env_path: str) -> None:
    """Write resolved targets and provenance to GITHUB_ENV."""
    if not github_env_path:
        return
    with open(github_env_path, "a", encoding="utf-8") as fh:
        fh.write(f"UI_ORIGIN={targets.ui_origin}\n")
        fh.write(f"UI_ORIGIN_SOURCE={targets.ui_source}\n")
        fh.write(f"API_ORIGIN={targets.api_origin}\n")
        fh.write(f"API_ORIGIN_SOURCE={targets.api_source}\n")
        fh.write(f"QA_BASE_URL={targets.qa_base_url}\n")
        fh.write(f"BACKEND_HEALTH_URL={targets.backend_health_url}\n")
        fh.write(f"TARGET_HEALTH_URL={targets.health_url}\n")


def build_markdown_summary(targets: ResolvedTargets) -> str:
    """Generate Markdown provenance table for GITHUB_STEP_SUMMARY."""
    ui_status = "✅ CONFIGURED" if targets.ui_origin else "⚠️ UNVERIFIED"
    api_status = "✅ CONFIGURED" if targets.api_origin else "⚠️ UNVERIFIED"

    lines = [
        "### 🎯 Production Target Resolution (Canonical Contract)",
        "",
        "| Component | Status | Target Origin | Provenance / Source |",
        "|---|:---:|---|---|",
        f"| **Frontend (UI / SPA)** | {ui_status} | `{targets.ui_origin or '(none)'}` | {targets.ui_source} |",
        f"| **Backend (API Core)** | {api_status} | `{targets.api_origin or '(none)'}` | {targets.api_source} |",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve canonical production UI & API targets with provenance."
    )
    parser.add_argument(
        "--write-github-env",
        action="store_true",
        help="Append resolved targets to the file specified in $GITHUB_ENV",
    )
    parser.add_argument(
        "--github-env-file",
        type=str,
        default=None,
        help="Explicit path to GITHUB_ENV file (defaults to $GITHUB_ENV)",
    )
    parser.add_argument(
        "--write-summary",
        action="store_true",
        help="Append Markdown summary table to $GITHUB_STEP_SUMMARY",
    )
    parser.add_argument(
        "--summary-file",
        type=str,
        default=None,
        help="Explicit path to GITHUB_STEP_SUMMARY file (defaults to $GITHUB_STEP_SUMMARY)",
    )
    parser.add_argument(
        "--allow-same-origin-fallback",
        action="store_true",
        help="Allow API origin to fall back to UI origin if backend URL is unset",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output resolved targets as JSON to stdout",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress human-readable stdout logs",
    )

    args = parser.parse_args(argv)
    targets = resolve_targets_from_env(
        allow_same_origin_fallback=args.allow_same_origin_fallback
    )

    if args.json:
        print(json.dumps(targets.to_dict(), indent=2))
    elif not args.quiet:
        print(f"ui_origin={targets.ui_origin or '(none)'}  source={targets.ui_source}")
        print(f"api_origin={targets.api_origin or '(none)'}  source={targets.api_source}")
        print(f"qa_base_url={targets.qa_base_url or '(none)'}")
        print(f"backend_health_url={targets.backend_health_url or '(none)'}")

    env_file = args.github_env_file or os.environ.get("GITHUB_ENV")
    if (args.write_github_env or args.github_env_file) and env_file:
        write_to_github_env(targets, env_file)

    summary_file = args.summary_file or os.environ.get("GITHUB_STEP_SUMMARY")
    if (args.write_summary or args.summary_file) and summary_file:
        markdown = build_markdown_summary(targets)
        with open(summary_file, "a", encoding="utf-8") as fh:
            fh.write(markdown + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
