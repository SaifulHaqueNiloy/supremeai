#!/usr/bin/env python3
"""
validate_router_imports.py
==========================
Router Import Smoke-Test — pre-CI gate script.

বাংলা মন্তব্য: এই স্ক্রিপ্টটি প্রতিটি registered router-কে individually import করে।
Full test suite চালানোর আগেই ধরতে পারে:
  - Hallucinated/non-existent modules (যেমন `from core.auth import get_current_user`)
  - Missing optional dependencies (যেমন `import cv2` at top-level)
  - Syntax errors in route files

একটি router import failure CI Bot commit-এ পুরো test suite-কে cascade করে ধ্বংস
করার বদলে এখন এখানেই ধরা পড়বে — clearly, immediately, 2 সেকেন্ডে।

Usage:
    cd backend
    python ../scripts/ci/validate_router_imports.py
    python ../scripts/ci/validate_router_imports.py --strict  # core routers must all pass
"""

from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
from pathlib import Path


# ── Router lists (mirrors backend/api/routers.py) ─────────────────────────────
# বাংলা মন্তব্য: এই লিস্ট api/routers.py-এর সাথে sync রাখা জরুরি।
# ভবিষ্যতে এটি সরাসরি routers.py থেকে dynamic import করা যেতে পারে।
CORE_ROUTERS = [
    "api.routes.memory",
    "api.routes.task",
    "api.routes.markdown",
    "api.routes.simulator",
    "api.routes.site_actions",
    "api.routes.browser",
    "api.routes.stream",
    "api.routes.media",
    "api.routes.graph",
    "api.routes.marketplace_endpoints",
    "api.routes.auth",
    "api.routes.onboarding",
    "api.routes.evolution",
    "api.routes.meta_ai",
    "api.routes.localization",
    "api.routes.analytics",
    "api.routes.admin_dashboard",
    "api.routes.email",
    "api.routes.github",
    "api.routes.internal",
    "api.routes.config",
    "api.routes.repos",
    "api.routes.tools_ops",
    "api.routes.agents",
    "api.routes.agent",
    "api.routes.admin",
    "api.routes.tools_registry",
    "api.routes.preferences",
    "api.routes.usage_metrics",
    "api.routes.sso",
    "api.routes.health",
    "api.routes.api_keys",
    "api.routes.ci_webhooks",
    "api.routes.task_workspace",
    "api.routes.websocket_agent",
    "api.routes.agent_workspace",
    "api.routes.integrations",
    "api.routes.public_config",
    "api.routes.traffic_monitor",
    "api.routes.agent_action",
    "api.routes.websocket_hitl",
    "api.routes.syncguard",
    "api.routes.admin_librarian",
    "api.routes.swarm",
    "api.routes.realtime_dashboard",
]

OPTIONAL_ROUTERS = [
    # বাংলা মন্তব্য: llm_gateway এখন optional — ব্যর্থ হলে warning, test suite crash নয়।
    "api.routes.llm_gateway",
    "api.routes.knowledge",
    "api.routes.dock_actions",
    "api.routes.websocket_voice",
    "tools.collaborative_editor",
    "tools.image_to_code",
    "tools.style_learner",
    "api.routes.codeflow",
    "api.routes.feedback",
    "tools.media.multilingual_tts",
    "api.routes.voice",
    "tools.comment_thread_ai",
    "api.routes.tenant_admin",
    "api.routes.mobile_bff",
    "api.routes.billing_api",
    "api.routes.metrics",
    "api.routes.cloud_mesh",
    "api.routes.events",
    "api.routes.payments",
    "api.routes.maintenance",
    "api.routes.sandbox_api",
    "api.routes.pr_review_api",
    "api.v1.telemetry",
    "api.routes.byoc_api",
]

# ANSI colors for readable terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def try_import(module_path: str) -> tuple[bool, str | None]:
    """
    Attempt to import a module and return (success, error_message).

    বাংলা মন্তব্য: প্রতিটি router isolated subprocess-এ import করা হয়।
    এর ফলে একটি bad import অন্যগুলোকে affect করতে পারে না।
    """
    try:
        result = subprocess.run(
            [
                sys.executable, "-c",
                f"import sys; sys.path.insert(0, '.'); "
                f"import {module_path}; "
                f"assert hasattr(__import__('{module_path}', fromlist=['router']), 'router'), "
                f"'No router attribute in {module_path}'"
            ],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=Path(__file__).parent.parent.parent / "backend",
        )
        if result.returncode == 0:
            return True, None
        error = (result.stderr or result.stdout).strip()
        # বাংলা মন্তব্য: সবচেয়ে relevant লাইনটি বের করা হচ্ছে (শেষ non-empty line)
        relevant = next(
            (line for line in reversed(error.splitlines()) if line.strip()),
            error[:200],
        )
        return False, relevant
    except subprocess.TimeoutExpired:
        return False, f"Import timed out after 15s (possible circular import or blocking call)"
    except Exception as exc:
        return False, str(exc)


def run_validation(strict: bool = False) -> int:
    """
    Run import validation for all routers.

    বাংলা মন্তব্য: --strict মোডে core router failure exit code 1 দেয়।
    সাধারণভাবে optional router failure শুধু warning।
    Returns exit code (0=pass, 1=fail).
    """
    print(f"\n{BOLD}{CYAN}🔍 Router Import Smoke-Test{RESET}")
    print(f"{'=' * 60}")

    core_failures: list[tuple[str, str]] = []
    optional_failures: list[tuple[str, str]] = []

    # Test core routers
    print(f"\n{BOLD}📦 Core Routers ({len(CORE_ROUTERS)} total){RESET}")
    for module in CORE_ROUTERS:
        ok, err = try_import(module)
        if ok:
            print(f"  {GREEN}✅{RESET} {module}")
        else:
            print(f"  {RED}❌{RESET} {module}")
            print(f"     {RED}└─ {err}{RESET}")
            core_failures.append((module, err or "unknown error"))

    # Test optional routers
    print(f"\n{BOLD}🔌 Optional Routers ({len(OPTIONAL_ROUTERS)} total){RESET}")
    for module in OPTIONAL_ROUTERS:
        ok, err = try_import(module)
        if ok:
            print(f"  {GREEN}✅{RESET} {module}")
        else:
            print(f"  {YELLOW}⚠️ {RESET} {module} (optional — will warn, not fail)")
            print(f"     {YELLOW}└─ {err}{RESET}")
            optional_failures.append((module, err or "unknown error"))

    # Summary
    print(f"\n{'=' * 60}")
    print(f"{BOLD}📊 Summary{RESET}")
    total = len(CORE_ROUTERS) + len(OPTIONAL_ROUTERS)
    failed = len(core_failures) + len(optional_failures)
    passed = total - failed
    print(f"  Total routers checked : {total}")
    print(f"  {GREEN}Passed               : {passed}{RESET}")
    if core_failures:
        print(f"  {RED}Core failures        : {len(core_failures)} ← BLOCKS CI{RESET}")
        for mod, err in core_failures:
            print(f"    {RED}• {mod}{RESET}")
            print(f"      {err[:120]}")
    if optional_failures:
        print(f"  {YELLOW}Optional failures    : {len(optional_failures)} (non-blocking){RESET}")
        for mod, err in optional_failures:
            print(f"    {YELLOW}• {mod}{RESET}")

    # Exit logic
    # বাংলা মন্তব্য: core router failure সবসময় CI block করে।
    # optional failure শুধু strict mode-এ block করে।
    if core_failures:
        print(f"\n{RED}{BOLD}❌ GATE FAILED — {len(core_failures)} core router(s) cannot be imported.{RESET}")
        print(f"{RED}   Fix these imports before running the full test suite.{RESET}\n")
        return 1

    if optional_failures and strict:
        print(f"\n{RED}{BOLD}❌ STRICT GATE FAILED — {len(optional_failures)} optional router(s) cannot be imported.{RESET}\n")
        return 1

    if optional_failures:
        print(f"\n{YELLOW}{BOLD}⚠️  PASSED WITH WARNINGS — {len(optional_failures)} optional router(s) unavailable.{RESET}\n")
    else:
        print(f"\n{GREEN}{BOLD}✅ ALL ROUTERS OK — import smoke-test passed.{RESET}\n")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate that all registered API routers can be imported without errors."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail on optional router import errors (default: only fail on core router errors)",
    )
    args = parser.parse_args()
    sys.exit(run_validation(strict=args.strict))


if __name__ == "__main__":
    main()
