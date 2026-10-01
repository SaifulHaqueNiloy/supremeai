#!/usr/bin/env python3
"""Check CI failures on main branch — create issues for red workflows.

# বাংলা মন্তব্য: এই স্ক্রিপ্ট main branch-এর সর্বশেষ CI runs চেক করে।
# কোনো workflow fail হলে P1-high issue তৈরি করে।
# Smart Continuous Loop (#2908) এর অংশ — "CI fixer" কম্পোনেন্ট।
#
# Usage:
#     python scripts/ci/check_ci_failures.py [--dry-run]
#     python scripts/ci/check_ci_failures.py --json report.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import subprocess
from typing import Any

REPO = os.environ.get("GH_REPO", "SaifulHaqueNiloy/supremeai")


def get_recent_failed_runs(limit: int = 10) -> list[dict[str, Any]]:
    """Get recent failed CI runs on main branch via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "run", "list", "--repo", REPO, "--branch", "main",
             "--status", "failure", "--limit", str(limit), "--json",
             "databaseId,name,conclusion,event,createdAt,headSha,url"],
            capture_output=True, text=True, timeout=30, check=False,
        )
        if result.returncode != 0:
            print(f"⚠️ gh run list failed: {result.stderr}", file=sys.stderr)
            return []
        runs = json.loads(result.stdout) if result.stdout.strip() else []
        return runs
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"⚠️ CI check failed: {e}", file=sys.stderr)
        return []


def get_existing_ci_issues() -> set[str]:
    """Get fingerprints of existing CI-failure issues to prevent duplicates."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", REPO, "--state", "open",
             "--label", "ci-failure", "--json", "number,title", "--limit", "50"],
            capture_output=True, text=True, timeout=15, check=False,
        )
        if result.returncode != 0:
            return set()
        issues = json.loads(result.stdout) if result.stdout.strip() else []
        # Extract fingerprints from titles
        fingerprints = set()
        for issue in issues:
            title = issue.get("title", "")
            # Fingerprint format: [ci-fail:<sha>]
            if "[ci-fail:" in title:
                fp = title.split("[ci-fail:")[1].split("]")[0]
                fingerprints.add(fp)
        return fingerprints
    except Exception:
        return set()


def create_ci_failure_issue(run: dict[str, Any]) -> int | None:
    """Create a GitHub issue for a CI failure."""
    run_id = run.get("databaseId", "?")
    name = run.get("name", "unknown")
    event = run.get("event", "unknown")
    sha = run.get("headSha", "")[:12]
    url = run.get("url", "")
    created = run.get("createdAt", "")

    # Dedup fingerprint: workflow name + short SHA
    fingerprint = f"{name}:{sha}"
    fp_hash = hashlib.md5(fingerprint.encode()).hexdigest()[:12]

    existing = get_existing_ci_issues()
    if fp_hash in existing:
        print(f"  ⏭️  Skip duplicate: {name} @ {sha} (issue already exists)")
        return None

    title = f"fix(ci): [ci-fail:{fp_hash}] {name} RED on main ({sha})"
    body = f"""## 🔴 CI Failure on Main Branch

| Field | Value |
|---|---|
| **Workflow** | `{name}` |
| **Event** | `{event}` |
| **Commit** | `{sha}` |
| **Run ID** | `{run_id}` |
| **Created** | `{created}` |
| **URL** | {url} |

### Reproduction
```bash
gh run view {run_id} --repo {REPO} --log-failed
```

### Remediation
1. Click the URL above to see the failed step
2. Fix the root cause
3. Push the fix to main
4. Re-run the workflow: `gh run rerun {run_id} --repo {REPO}`

### Fingerprint
`{fingerprint}` → hash `{fp_hash}` (dedup key)

*Auto-filed by `check_ci_failures.py` (#2908 — Smart Continuous Loop)*"""

    gh_token = os.environ.get("GITHUB_TOKEN", "")
    try:
        import urllib.request, urllib.error
        payload = json.dumps({
            "title": title,
            "body": body,
            "labels": ["P1-high", "area:ci", "type:bug", "ci-failure"],
        }).encode()
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/issues",
            data=payload, method="POST",
            headers={
                "Authorization": f"token {gh_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            issue = json.load(r)
            print(f"  ✅ Created issue #{issue['number']}: {title[:60]}")
            return issue["number"]
    except Exception as e:
        print(f"  ❌ Could not create issue: {e}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check CI failures on main")
    parser.add_argument("--dry-run", action="store_true", help="Don't create issues")
    parser.add_argument("--json", type=str, help="Write JSON report to file")
    args = parser.parse_args()

    print(f"🔍 Checking CI failures on {REPO} main branch...")
    failed_runs = get_recent_failed_runs()

    if not failed_runs:
        print("✅ No CI failures found on main. All green!")
        if args.json:
            with open(args.json, "w") as f:
                json.dump({"failed_runs": [], "issues_created": []}, f, indent=2)
        return 0

    print(f"Found {len(failed_runs)} failed run(s):")
    issues_created = []
    for run in failed_runs:
        name = run.get("name", "?")
        sha = run.get("headSha", "")[:12]
        print(f"  ❌ {name} @ {sha}")

        if args.dry_run:
            print(f"     (dry-run: would create issue)")
            continue

        issue_num = create_ci_failure_issue(run)
        if issue_num:
            issues_created.append(issue_num)

    if args.json:
        with open(args.json, "w") as f:
            json.dump({
                "failed_runs": failed_runs,
                "issues_created": issues_created,
                "count": len(failed_runs),
            }, f, indent=2)

    return 1 if issues_created else 0


if __name__ == "__main__":
    sys.exit(main())
