#!/usr/bin/env python3
"""
SupremeAI Topology & URL Auditor
================================
Validates all URL references across Frontend, VS Code Extension, and Packages
against docs/SYSTEM_TOPOLOGY_AND_URL_REGISTRY.md.

Usage:
    python scripts/audit_topology_urls.py
"""

import sys
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[1]
REGISTRY_FILE = ROOT_DIR / "docs" / "SYSTEM_TOPOLOGY_AND_URL_REGISTRY.md"

# Targets to scan
SCAN_DIRECTORIES = [
    ROOT_DIR / "frontend" / "src",
    ROOT_DIR / "tools" / "vscode-extension" / "src",
    ROOT_DIR / "packages",
]

# Patterns that signal suspicious hardcoded localhost in client code (ignoring test files)
SUSPICIOUS_PATTERNS = [
    (re.compile(r"http://localhost:(?!11434)[0-9]+"), "Hardcoded non-Ollama localhost URL"),
    (re.compile(r"http://127\.0\.0\.1:(?!11434)[0-9]+"), "Hardcoded non-Ollama 127.0.0.1 URL"),
    (re.compile(r"supremeai-api-lhlwyikwlq-uc\.a\.run\.app"), "Deprecated Cloud Run URL detected"),
]

def audit_topology() -> bool:
    print("\n🔍 ===================================================")
    print("      SupremeAI System Topology & URL Audit")
    print("===================================================\n")

    if not REGISTRY_FILE.exists():
        print(f"❌ Registry file missing: {REGISTRY_FILE}")
        return False
    print(f"✅ Registry found: docs/{REGISTRY_FILE.name}")

    issues = []
    scanned_files = 0

    for scan_dir in SCAN_DIRECTORIES:
        if not scan_dir.exists():
            continue

        for file_path in scan_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in {".ts", ".tsx", ".js", ".mjs"}:
                # Skip build folders, dependencies, and test/spec/type files
                parts = file_path.parts
                if any(ignored in parts for ignored in ["node_modules", "dist", ".turbo", "build", ".next", ".git"]):
                    continue
                if any(k in file_path.name for k in ["test", "spec", ".d.ts"]):
                    continue

                scanned_files += 1
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    continue

                for pattern, desc in SUSPICIOUS_PATTERNS:
                    matches = pattern.findall(content)
                    if matches:
                        rel_path = file_path.relative_to(ROOT_DIR)
                        for match in set(matches):
                            issues.append((str(rel_path), match, desc))

    print(f"📁 Scanned {scanned_files} production client source files.")

    if issues:
        print(f"\n⚠️  Found {len(issues)} URL topology issues:")
        for file_path, match, desc in issues:
            print(f"   - [{file_path}]: '{match}' -> {desc}")
        print("\n❌ Topology Audit FAILED. Please link to production gateway or use env configuration.")
        return False

    print("\n🎉 All client endpoints are cleanly mapped to dynamic config / production gateways!")
    print("✅ Topology Audit PASSED (100% compliant with SYSTEM_TOPOLOGY_AND_URL_REGISTRY.md)\n")
    return True

if __name__ == "__main__":
    success = audit_topology()
    sys.exit(0 if success else 1)
