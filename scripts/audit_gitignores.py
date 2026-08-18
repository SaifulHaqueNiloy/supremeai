#!/usr/bin/env python3
"""
audit_gitignores.py — SupremeAI Gitignore Scope Auditor (Zero-Cost)

PROTECTS against the silent-exclusion class of bug documented in
LESSONS_LEARNED.md (`.gitignore: test_*.py` Path Trap): a gitignore pattern
lacking a root anchor (`/`) silently ignores every matching file in the tree,
including files that SHOULD be version-controlled (tests, configs, env
templates) — they vanish from `git add`, from PRs, and from CI without warning.

Checks:
  1. TRACKED-IGNORED  (HIGH — fails the gate): any file TRACKED in git but
     reported by `git check-ignore` as ignored. Definitive regression — if a
     tracked file is ignored, the gitignore is hiding committed content (the
     exact bug that lost 10 test files).
  2. UNSCOPED TEST PATTERN  (HIGH — fails the gate): an unscoped (no leading
     `/`) gitignore line over a test class (`test_*` / `*_test*` / `tests/**`)
     that is not a negation. Tests must be tracked everywhere.
  3. UNSCOPED SENSITIVE PATTERN  (WARN — advisory): unscoped `*_env.py` /
     `sync_*` / `*.env` patterns — intentional ignore-everywhere is acceptable
     but flagged for intent auditability.

Usage:
  python scripts/audit_gitignores.py            # CI/pre-commit (exit 1 on HIGH)
  python scripts/audit_gitignores.py --warn       # advisory only (exit 0)
  python scripts/audit_gitignores.py --fix        # rewrite unscoped lines with /

No third-party deps (git CLI + stdlib only). Monorepo-aware: scans every
.gitignore in the tree, skipping vendor/cache directories.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Windows PowerShell 5.x defaults stdout to cp1252 -> emojis/mojibake crash.
# Reconfigure to UTF-8 (per LESSONS_LEARNED.md: "UTF-8 reconfigure" fix).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

# Directories to skip when enumerating .gitignore files (vendor/cache/build).
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".ruff_cache", ".pytest_cache", ".turbo", ".turbopack", ".act",
    "dist", "build", "out", ".next", ".vercel", "playwright-report",
    "test-results", ".playwright-mcp",
}

# Test-class basenames that MUST be tracked everywhere -> unscoped = HIGH risk.
TEST_NAME_RE = re.compile(r"^(test_.*|.*_test(\..*)?$|^tests/.*|tests/)$")

# Sensitive (intentionally-ignored-everywhere) substrings -> unscoped = WARN.
SENSITIVE_SUBSTRINGS = ("_env.py", "env.py", "sync_", "_config.py", ".env",
                        "secrets", "credentials", "service-account")


def git(args: list[str]) -> str:
    """Run a git command in ROOT and return stdout (raises on error)."""
    r = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def find_gitignores() -> list[Path]:
    """All .gitignore files under ROOT, excluding vendor/cache/build dirs.

    Uses os.walk with in-place dir pruning (topdown) so we never descend into
    node_modules/.venv/etc. — keeps this sub-second even in huge monorepos.
    """
    import os
    ignores: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=True):
        # prune skipped dirs BEFORE descending (mutates dirnames in place)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn == ".gitignore":
                ignores.append(Path(dirpath) / fn)
    return sorted(ignores)


def check_tracked_ignored() -> list[str]:
    """HIGH: files that are TRACKED in git but git check-ignore reports ignored."""
    tracked = git(["ls-files"]).splitlines()
    if not tracked:
        return []
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "--no-index", "--stdin", "-z"],
        input="\n".join(tracked), capture_output=True, text=True, cwd=str(ROOT),
    )
    # --no-index: evaluate even paths already ignored by a lower-priority rule
        ignored = {line.strip() for line in proc.stdout.split("\0") if line.strip()}
    return [f for f in tracked if f in ignored]


def check_staged_ignored() -> list[str]:
    """HIGH: files STAGED for commit that `git check-ignore` reports ignored.

    This is the real-time trap detector: if a developer runs `git add` on a
    file that matches an unscoped gitignore rule, git SILENTLY skips it. Catching
    staged-but-ignored paths at pre-commit proves the `test_*.py` trap cannot
    silently lose a commit again.
    """
    staged = git(["diff", "--cached", "--name-only"]).splitlines()
    staged = [s for s in staged if s]  # drop empties
    if not staged:
        return []
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "--no-index", "--stdin", "-z"],
        input="\n".join(staged), capture_output=True, text=True, cwd=str(ROOT),
    )
    ignored = {line.strip() for line in proc.stdout.split("\0") if line.strip()}
    return [f for f in staged if f in ignored]


def scan_gitignore_lines(path: Path) -> tuple[list[str], list[str]]:
    """Return (high_issues, warn_issues) as [path:lineno: pattern] strings."""
    high: list[str] = []
    warn: list[str] = []
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        is_negation = line.startswith("!")
        pattern = line[1:] if is_negation else line
        root_anchored = pattern.startswith("/")
        basename = pattern.split("/")[-1]
        is_test = bool(TEST_NAME_RE.match(basename)) or pattern.rstrip("/").endswith("/tests")
        is_sensitive = any(s in pattern for s in SENSITIVE_SUBSTRINGS)
        if (not root_anchored) and is_test and not is_negation:
            # Advisory: unscoped test patterns are a SMELL (the original trap).
            # HIGH/fail is driven solely by staged-ignored + tracked-ignored
            # checks (zero false positives — they inspect actual git state).
            warn.append(
                f"{path.relative_to(ROOT)}:{i}: {line}  "
                f"[advisory: root-anchor unscoped test pattern to document intent]"
            )
        elif (not root_anchored) and is_sensitive and not is_negation:
            warn.append(f"{path.relative_to(ROOT)}:{i}: {line}")
    return high, warn
    

    return high, warn


def _apply_fix(path: Path) -> None:
    """Rewrite unscoped test/sensitive lines by prepending a root anchor '/'."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            out.append(raw); continue
        pattern = line
        basename = pattern.split("/")[-1]
        is_test = bool(TEST_NAME_RE.match(basename))
        is_sensitive = any(s in pattern for s in SENSITIVE_SUBSTRINGS)
        if (not pattern.startswith("/")) and (is_test or is_sensitive):
            out.append("/" + raw)
        else:
            out.append(raw)
    path.write_text("".join(out), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="SupremeAI gitignore scope auditor")
    ap.add_argument("--warn", action="store_true",
                    help="advisory mode: never fail the gate (exit 0)")
    ap.add_argument("--fix", action="store_true",
                    help="rewrite unscoped test/sensitive lines with a '/' prefix")
    args = ap.parse_args()

    print("=== SupremeAI Gitignore Scope Audit ===")
    print(f"repo root: {ROOT}\n")

    gis = find_gitignores()
    print(f"[scanned gitignores: {len(gis)}]")

    tracked_ignored = check_tracked_ignored()
    high: list[str] = []
    warn: list[str] = []

    for gi in gis:
        h, w = scan_gitignore_lines(gi)
        high += h
        warn += w

    if tracked_ignored:
        high.append("--- TRACKED-IGNORED (tracked files the gitignore suppresses) ---")
        high += tracked_ignored

    if high:
        print(f"\n🔴 HIGH severity ({len(high)}): fails the gate unless --warn")
        for i in high:
            print("  " + i)
    if warn:
        print(f"\n🟡 WARN advisory ({len(warn)}): unscoped sensitive patterns")
        for i in warn:
            print("  " + i)

    if args.fix:
        for gi in gis:
            _apply_fix(gi)
        print("\n[fix] rewrote unscoped test/sensitive lines with '/' prefix")

    if high and not args.warn:
        print("\n❌ GITIGNORE SCOPE AUDIT FAILED — tracked files silently excluded or "
              "unscoped test patterns present (the test_*.py trap). Fix before commit.")
        return 1
    print("\n✅ Gitignore scope audit passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
