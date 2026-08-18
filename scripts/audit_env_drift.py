#!/usr/bin/env python3
"""
SupremeAI Environment & Secret Drift Auditor
============================================
Scans the entire codebase for environment variable lookups (os.getenv, import.meta.env, process.env)
and verifies them against docs/ENV_AND_SECRET_REGISTRY.md and .env.example to prevent runtime crashes.

Usage:
    python scripts/audit_env_drift.py
"""

import sys
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[1]
REGISTRY_FILE = ROOT_DIR / "docs" / "ENV_AND_SECRET_REGISTRY.md"
ENV_EXAMPLE = ROOT_DIR / ".env.example"

# Regex patterns for finding env references
PY_ENV_PATTERNS = [
    re.compile(r'os\.getenv\(["\']([A-Z0-9_]+)["\']'),
    re.compile(r'os\.environ\.get\(["\']([A-Z0-9_]+)["\']'),
    re.compile(r'os\.environ\[["\']([A-Z0-9_]+)["\']\]'),
    re.compile(r'validation_alias=["\']([A-Z0-9_]+)["\']'),
]

TS_ENV_PATTERNS = [
    re.compile(r'import\.meta\.env\.([A-Z0-9_]+)'),
    re.compile(r'process\.env\.([A-Z0-9_]+)'),
]

# Standard runtime or framework env vars that don't need registry
WHITELIST = {
    "PATH", "PYTHONPATH", "NODE_ENV", "PORT", "PWD", "HOME", "USER", "CI",
    "BASE_URL", "MODE", "PROD", "DEV", "SSR", "VITE_USER_NODE_ENV", "npm_package_version"
}

def load_registered_keys() -> set[str]:
    registered = set(WHITELIST)
    
    # Load from docs/ENV_AND_SECRET_REGISTRY.md
    if REGISTRY_FILE.exists():
        content = REGISTRY_FILE.read_text(encoding="utf-8", errors="ignore")
        for match in re.findall(r'`([A-Z0-9_]+)`', content):
            registered.add(match)
            
    # Load from .env.example and .env
    for env_f in [ENV_EXAMPLE, ROOT_DIR / ".env"]:
        if env_f.exists():
            content = env_f.read_text(encoding="utf-8", errors="ignore")
            for match in re.findall(r'^([A-Z0-9_]+)=', content, re.MULTILINE):
                registered.add(match)

    # Load from backend core config definitions
    config_files = [
        ROOT_DIR / "backend" / "core" / "config.py",
        ROOT_DIR / "backend" / "core" / "config_fields.py",
        ROOT_DIR / "backend" / "core" / "config_secrets.py",
        ROOT_DIR / "backend" / "core" / "config_validation.py",
    ]
    for cfg in config_files:
        if cfg.exists():
            content = cfg.read_text(encoding="utf-8", errors="ignore")
            for match in re.findall(r'validation_alias=["\']([A-Z0-9_]+)["\']', content):
                registered.add(match)
            for match in re.findall(r'([a-zA-Z0-9_]+):\s*(?:str|int|bool|float|list|dict|Optional)', content):
                registered.add(match.upper())

    return registered

def audit_env_drift() -> bool:
    print("\n🔍 ===================================================")
    print("      SupremeAI Environment Drift Auditor")
    print("===================================================\n")

    registered_keys = load_registered_keys()
    print(f"✅ Loaded {len(registered_keys)} registered keys from Registry and .env.example")

    found_keys: dict[str, list[str]] = {}
    scanned_files = 0

    import os

    TARGET_DIRS = [
        ROOT_DIR / "backend",
        ROOT_DIR / "frontend" / "src",
        ROOT_DIR / "tools" / "vscode-extension" / "src",
        ROOT_DIR / "packages",
        ROOT_DIR / "scripts",
    ]

    IGNORE_DIRS = {
        "node_modules", "dist", ".turbo", "build", ".next", ".git",
        ".pytest_cache", ".venv", "venv", ".venv_ci", ".venv_probe", "site-packages",
        "__pycache__", "htmlcov", "coverage"
    }

    for target in TARGET_DIRS:
        if not target.exists():
            continue
        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and "venv" not in d.lower()]
            for f in files:
                file_path = Path(root) / f
                suffix = file_path.suffix.lower()
                if suffix == ".py":
                    scanned_files += 1
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        for pattern in PY_ENV_PATTERNS:
                            for key in pattern.findall(content):
                                rel = str(file_path.relative_to(ROOT_DIR))
                                found_keys.setdefault(key, []).append(rel)
                    except Exception:
                        pass
                elif suffix in {".ts", ".tsx", ".js", ".mjs"}:
                    scanned_files += 1
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        for pattern in TS_ENV_PATTERNS:
                            for key in pattern.findall(content):
                                rel = str(file_path.relative_to(ROOT_DIR))
                                found_keys.setdefault(key, []).append(rel)
                    except Exception:
                        pass

    print(f"📁 Scanned {scanned_files} codebase files. Found {len(found_keys)} distinct env keys in use.")

    # Check for unregistered ghost keys, categorized by severity
    critical_unregistered: dict[str, list[str]] = {}
    script_dev_flags: dict[str, list[str]] = {}

    for key, files in found_keys.items():
        if key in registered_keys:
            continue
            
        is_script_or_test = all(
            any(k in f for k in ["scripts", "tests", "test_", "mock", "spec"])
            for f in files
        )
        if is_script_or_test:
            script_dev_flags[key] = files
        else:
            critical_unregistered[key] = files

    if critical_unregistered:
        print(f"\n🚨 Found {len(critical_unregistered)} CRITICAL Unregistered Production Variables:")
        for key, files in sorted(critical_unregistered.items()):
            print(f"   - `{key}` in {files[0]}")
        print("\n❌ Environment Drift Audit FAILED. Please register them in docs/ENV_AND_SECRET_REGISTRY.md")
        return False

    if script_dev_flags:
        print(f"\nℹ️  Detected {len(script_dev_flags)} script/testing developer flags (non-blocking).")

    print("\n🎉 All critical production environment variables are 100% documented and registered!")
    print("✅ Environment Drift Audit PASSED.\n")
    return True

if __name__ == "__main__":
    success = audit_env_drift()
    sys.exit(0 if success else 1)
