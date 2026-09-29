#!/usr/bin/env python3
"""SupremeAI Universal Agent Orchestrator — Dynamic Task Router (issue #2504, seq:1).

বাংলা মন্তব্য:
Universal Agent Architecture-এর Layer 3 — "intelligent router":
  ১. Current-state audit: repo + GitHub (fail-soft) + policy-DB
  ২. Priority ladder: main-red → failing/stale PR → unclaimed issue → audit
  ৩. Smart context selection: শুধু relevant rules + history পাঠায়
  ৪. Dynamic Instruction: standard machine-readable task format
     (MODE / RULES / ACTIONS / FORBIDDEN / VALIDATION / STOP / OUTPUT)

মূল নীতি: "Agent type নয় → Task type। Task chooses capability; model does
not define the task." — একটিই Universal Agent, router কাজ বরাদ্দ করে।

Layered control:
  Layer 1 — AGENTS.md v3 (universal contract)
  Layer 2 — Database (task_policies / task_permissions / agent_task_history)
  Layer 3 — এই script (router)

Usage:
    python scripts/agents/supremeai_orchestrator.py --slot agent-1
    python scripts/agents/supremeai_orchestrator.py --slot agent-1 --json
    python scripts/agents/supremeai_orchestrator.py --slot agent-1 --issue 2504
    python scripts/agents/supremeai_orchestrator.py --slot agent-1 --sqlite data/operational_truth.db
    python scripts/agents/supremeai_orchestrator.py --slot agent-1 --dry-run

Fail-soft চুক্তি: GitHub token না থাকলে GitHub-state সেকশন skip হয় (advisory),
DB না পাওয়া গেলে canonical seed (backend/core/database/agent_policies.py) থেকে
policy পড়া হয় — কোনো ক্ষেত্রেই silent crash নয়, প্রতিটি degrade স্পষ্ট লেখা থাকে।
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_OPERATIONS = REPO_ROOT / "scripts" / "operations"
AGENT_POLICIES_PATH = REPO_ROOT / "backend" / "core" / "database" / "agent_policies.py"
DEFAULT_SQLITE = REPO_ROOT / "data" / "operational_truth.db"

# GitHub API config (fail-soft: token না থাকলে GitHub-state skip)
GITHUB_API = "https://api.github.com"
GITHUB_REPO = os.environ.get("GH_REPO") or "SaifulHaqueNiloy/supremeai"
STALE_PR_HOURS = 48

# Issue priority ladder (ISSUE_PRIORITY_POLICY.md)
PRIORITY_LADDER = ("P0-critical", "P1-high", "P2-medium", "P3-low")


# ────────────────────────── helpers ──────────────────────────


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def _iso(dt: datetime.datetime | None = None) -> str:
    return (dt or _now()).isoformat(timespec="seconds")


def _load_agent_policies_module() -> Any:
    """backend/core/database/agent_policies.py — সরাসরি file-load।

    বাংলা মন্তব্য: core/__init__.py ভারী package-import টানবে — তাই importlib
    spec দিয়ে module-টাকে বিচ্ছিন্নভাবে লোড করা হয় (dependency-free pure data)।
    """
    spec = importlib.util.spec_from_file_location("agent_policies", AGENT_POLICIES_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover — path corruption
        raise RuntimeError(f"agent_policies.py load ব্যর্থ: {AGENT_POLICIES_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(args: list[str]) -> str | None:
    """git command → stdout (fail-soft: None)।"""
    try:
        res = subprocess.run(
            ["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=15
        )
        return res.stdout.strip() if res.returncode == 0 else None
    except (subprocess.TimeoutExpired, OSError):
        return None


def _gh_api(path: str, token: str | None) -> Any:
    """GitHub REST GET (fail-soft raise urllib.error)।"""
    req = urllib.request.Request(
        f"{GITHUB_API}/{path.lstrip('/')}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "supremeai-orchestrator",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ────────────────────────── dataclasses ──────────────────────────


@dataclass
class AuditState:
    """Phase-1 audit-এর ফলাফল — router-এর ইনপুট।"""

    repo_head: str = "unknown"
    repo_branch: str = "unknown"
    repo_dirty: int = 0
    github_available: bool = False
    github_note: str = "GitHub state skip (কোনো token নেই / API unreachable)"
    main_ci: str = "unknown"  # green | red | unknown
    open_prs: list[dict[str, Any]] = field(default_factory=list)
    failing_prs: list[int] = field(default_factory=list)
    stale_prs: list[int] = field(default_factory=list)
    unclaimed_issues: list[dict[str, Any]] = field(default_factory=list)
    policy_source: str = "seed"  # db | seed
    policy_count: int = 0
    history_count: int = 0
    db_note: str = ""


@dataclass
class TaskAssignment:
    """Phase-4 assignment — Dynamic Instruction-এর data source।"""

    mode: str
    task_id: str
    slot: str
    objective: str
    issue_numbers: list[int] = field(default_factory=list)
    group: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    applicable_rules: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    validation: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)
    expected_output: str = ""
    permissions: dict[str, bool] = field(default_factory=dict)


# ────────────────────────── Phase 1: audit ──────────────────────────


def audit_repo_state() -> dict[str, Any]:
    """লোকাল repo state — git fail হলেও 'unknown' মানে চলতে থাকে।"""
    head = _git(["rev-parse", "--short", "HEAD"]) or "unknown"
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"
    status = _git(["status", "--porcelain"]) or ""
    dirty = len([line for line in status.splitlines() if line.strip()])
    return {"head": head, "branch": branch, "dirty": dirty}


def _check_main_ci(token: str | None) -> str:
    """main HEAD-এর check-run conclusion → green/red/unknown (fail-soft)।"""
    if not token:
        return "unknown"
    try:
        commits = _gh_api(f"repos/{GITHUB_REPO}/commits?per_page=1", token)
        if not commits:
            return "unknown"
        sha = commits[0]["sha"]
        runs = _gh_api(f"repos/{GITHUB_REPO}/commits/{sha}/check-runs?per_page=100", token)
        conclusions = [
            r.get("conclusion") for r in runs.get("check_runs", []) if r.get("status") == "completed"
        ]
        # শুধু ব্লকিং-মানের failure দেখি: success/skipped/neutral নয় এমন কিছু থাকলে red
        # (বাংলা মন্তব্য: GitHub API lowercase conclusion দেয় — case-insensitive তুলনা)
        ok_values = {"success", "skipped", "neutral", ""}
        blocking = [c for c in conclusions if str(c or "").lower() not in ok_values]
        if not conclusions:
            return "unknown"
        return "red" if blocking else "green"
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError):
        return "unknown"


def _check_pr_failures(prs: list[dict[str, Any]], token: str | None) -> list[int]:
    """প্রতিটি open PR-এর head check-runs → failing হলে PR নম্বর।"""
    failing: list[int] = []
    if not token:
        return failing
    for pr in prs[:20]:  # rate-limit সুরক্ষা — সর্বোচ্চ ২০টি PR পরীক্ষা
        try:
            sha = pr.get("head", {}).get("sha", "")
            if not sha:
                continue
            runs = _gh_api(f"repos/{GITHUB_REPO}/commits/{sha}/check-runs?per_page=100", token)
            for run in runs.get("check_runs", []):
                if (
                    run.get("status") == "completed"
                    and str(run.get("conclusion") or "").lower() == "failure"
                ):
                    failing.append(pr["number"])
                    break
        except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError):
            continue
    return failing


def audit_github_state(token: str | None) -> dict[str, Any]:
    """GitHub লাইভ state — token না থাকলে advisory skip।"""
    if not token:
        return {
            "available": False,
            "main_ci": "unknown",
            "open_prs": [],
            "failing_prs": [],
            "stale_prs": [],
            "unclaimed_issues": [],
        }
    try:
        prs = _gh_api(f"repos/{GITHUB_REPO}/pulls?state=open&per_page=50", token)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return {
            "available": False,
            "main_ci": "unknown",
            "open_prs": [],
            "failing_prs": [],
            "stale_prs": [],
            "unclaimed_issues": [],
        }

    stale: list[int] = []
    for pr in prs:
        updated = pr.get("updated_at", "")
        try:
            dt = datetime.datetime.fromisoformat(updated.replace("Z", "+00:00"))
            if (_now() - dt).total_seconds() > STALE_PR_HOURS * 3600:
                stale.append(pr["number"])
        except ValueError:
            continue

    try:
        raw_issues = _gh_api(
            f"repos/{GITHUB_REPO}/issues?state=open&per_page=100", token
        )
        unclaimed = []
        for issue in raw_issues:
            if "pull_request" in issue:
                continue
            labels = [lab.get("name", "") for lab in issue.get("labels", [])]
            if "status:in-progress" in labels or "has-pr" in labels:
                continue  # claim-locked বা PR-খোলা issue
            if any(lab.startswith("type:ledger") for lab in labels):
                continue  # auto-generated ledger issue — কাজের টার্গেট নয়
            if "seq:0" in labels:
                continue  # master group tracking issue (seq:0) — coordination, executable কাজ নয়
            unclaimed.append(
                {
                    "number": issue["number"],
                    "title": issue.get("title", ""),
                    "labels": labels,
                    "created_at": issue.get("created_at", ""),
                    "updated_at": issue.get("updated_at", ""),
                }
            )
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        unclaimed = []

    return {
        "available": True,
        "main_ci": _check_main_ci(token),
        "open_prs": prs,
        "failing_prs": _check_pr_failures(prs, token),
        "stale_prs": stale,
        "unclaimed_issues": unclaimed,
    }


def _connect_policy_db(db_url: str | None, sqlite_path: str | None) -> tuple[Any, str] | None:
    """operational_truth_db দিয়ে DB connect (fail-soft: None)।"""
    if SCRIPTS_OPERATIONS not in sys.path:
        sys.path.insert(0, str(SCRIPTS_OPERATIONS))
    try:
        from operational_truth_db import connect, ensure_schema  # noqa: PLC0415

        target_url = db_url or os.environ.get("OPERATIONAL_TRUTH_DB_URL")
        target_sqlite = sqlite_path or (str(DEFAULT_SQLITE) if DEFAULT_SQLITE.exists() else None)
        if not target_url and not target_sqlite:
            return None
        conn, flavor = connect(db_url=target_url, sqlite_path=target_sqlite)
        ensure_schema(conn, flavor)
        return conn, flavor
    except Exception:  # noqa: BLE001 — fail-soft contract: DB নেই → seed fallback
        return None


def load_policies(
    db_url: str | None = None, sqlite_path: str | None = None, dry_run: bool = False
) -> tuple[dict[str, dict[str, Any]], str, str]:
    """Layer-2 policy load: DB override → canonical seed fallback।

    Returns: (policies, source, note)
      source = 'db'    → task_policies টেবিল থেকে
      source = 'seed'  → backend/core/database/agent_policies.py থেকে (fail-soft)
    DB reachable কিন্তু টেবিল খালি হলে canonical seed দিয়ে auto-seed (self-heal)।
    """
    policies_mod = _load_agent_policies_module()
    seed_note = "DB unreachable → canonical seed fallback (fail-soft)"

    handle = _connect_policy_db(db_url, sqlite_path)
    if handle is None:
        return {name: dict(pol) for name, pol in policies_mod.TASK_POLICIES.items()}, "seed", seed_note
    conn, flavor = handle

    if SCRIPTS_OPERATIONS not in sys.path:
        sys.path.insert(0, str(SCRIPTS_OPERATIONS))
    from operational_truth_db import fetch_all, upsert_rows  # noqa: PLC0415

    try:
        rows = fetch_all(conn, flavor, "SELECT * FROM task_policies")
        if not rows and not dry_run:
            # self-heal: খালি টেবিলে canonical seed upsert
            now = _iso()
            seeded_policies = [
                {**row, "updated_at": now} for row in policies_mod.policy_rows()
            ]
            seeded_perms = [
                {**row, "updated_at": now} for row in policies_mod.permission_rows()
            ]
            upsert_rows(conn, flavor, "task_policies", seeded_policies, conflict_cols=["task_type"])
            upsert_rows(
                conn, flavor, "task_permissions", seeded_perms, conflict_cols=["task_type"]
            )
            rows = fetch_all(conn, flavor, "SELECT * FROM task_policies")
        if rows:
            policies: dict[str, dict[str, Any]] = {}
            for row in rows:
                task_type = row.get("task_type", "")
                rules = row.get("rules") or []
                if isinstance(rules, str):
                    try:
                        rules = json.loads(rules)
                    except json.JSONDecodeError:
                        rules = []
                policies[task_type] = {
                    "summary": row.get("summary", ""),
                    "rules": rules,
                    "forbidden_actions": row.get("forbidden_actions") or [],
                    "required_actions": row.get("required_actions") or [],
                    "validation": row.get("validation") or [],
                    "expected_output": row.get("expected_output", ""),
                    # permissions seed থেকেই নেওয়া — permission আলাদা টেবিলে,
                    # কিন্তু instruction-এ একসাথে লাগে (smart context single-fetch)
                    "permissions": policies_mod.get_task_permissions(task_type),
                }
            return policies, "db", f"task_policies টেবিল থেকে {len(rows)}টি policy"
        return (
            {name: dict(pol) for name, pol in policies_mod.TASK_POLICIES.items()},
            "seed",
            seed_note,
        )
    finally:
        conn.close()


def count_history(db_url: str | None = None, sqlite_path: str | None = None) -> int:
    """agent_task_history-র row count (learning-loop observability)।"""
    handle = _connect_policy_db(db_url, sqlite_path)
    if handle is None:
        return 0
    conn, flavor = handle
    if SCRIPTS_OPERATIONS not in sys.path:
        sys.path.insert(0, str(SCRIPTS_OPERATIONS))
    from operational_truth_db import fetch_all  # noqa: PLC0415

    try:
        rows = fetch_all(conn, flavor, "SELECT COUNT(*) AS n FROM agent_task_history")
        return int(rows[0]["n"]) if rows else 0
    except Exception:  # noqa: BLE001 — count হল observability, fail-soft 0
        return 0
    finally:
        conn.close()


def run_audit(
    token: str | None,
    db_url: str | None,
    sqlite_path: str | None,
    dry_run: bool = False,
) -> AuditState:
    """Phase-1 সম্পূর্ণ audit — repo + GitHub + policy-DB।"""
    repo = audit_repo_state()
    gh = audit_github_state(token)
    policies, source, note = load_policies(db_url, sqlite_path, dry_run)

    state = AuditState(
        repo_head=repo["head"],
        repo_branch=repo["branch"],
        repo_dirty=repo["dirty"],
        github_available=gh["available"],
        main_ci=gh["main_ci"],
        open_prs=gh["open_prs"],
        failing_prs=gh["failing_prs"],
        stale_prs=gh["stale_prs"],
        unclaimed_issues=gh["unclaimed_issues"],
        policy_source=source,
        policy_count=len(policies),
        history_count=count_history(db_url, sqlite_path) if not dry_run else 0,
        db_note=note,
    )
    return state


# ────────────────────────── Phase 2/3: prioritize ──────────────────────────


def _issue_priority(issue: dict[str, Any]) -> int:
    """priority ladder index (P0=0 … P3=3, no label=P3)।"""
    labels = issue.get("labels", [])
    for idx, tier in enumerate(PRIORITY_LADDER):
        if tier in labels:
            return idx
    return len(PRIORITY_LADDER)


def _issue_sort_key(issue: dict[str, Any]) -> tuple[int, str]:
    """priority ladder DESC → oldest first (ISSUE_PRIORITY_POLICY.md)।"""
    return (_issue_priority(issue), issue.get("created_at", ""))


def _earlier_seq_open(target: dict[str, Any], all_issues: list[dict[str, Any]]) -> bool:
    """একই group-এর কম seq-নম্বরের open issue থাকলে target blocked (dependency)।"""
    labels = target.get("labels", [])
    group = next((lab[6:] for lab in labels if lab.startswith("group:")), None)
    if not group:
        return False
    target_seq = None
    for lab in labels:
        if lab.startswith("seq:"):
            try:
                target_seq = int(lab[4:])
            except ValueError:
                target_seq = None
    for other in all_issues:
        if other.get("number") == target.get("number"):
            continue
        other_labels = other.get("labels", [])
        other_group = next((lab[6:] for lab in other_labels if lab.startswith("group:")), None)
        if other_group != group:
            continue
        for lab in other_labels:
            if lab.startswith("seq:"):
                try:
                    other_seq = int(lab[4:])
                    if target_seq is not None and other_seq < target_seq:
                        return True
                except ValueError:
                    continue
    return False


def prioritize(state: AuditState, focus_issue: int | None = None) -> tuple[str, dict[str, Any]]:
    """Priority ladder — plan-এর ক্রম:

    ১. main red            → FIX_RED_MAIN (Rank-1 interrupt)
    ২. failing open PR     → CI_FAILURE
    ৩. stale open PR       → REVIEW_PR
    ৪. unclaimed issue     → SOLVE_ISSUE (P0→P3, oldest-first, seq-aware)
    ৫. fallback            → ADVERSARIAL_AUDIT (breaker rotation)

    Returns: (mode, target)
    """
    if focus_issue is not None:
        target = next(
            (i for i in state.unclaimed_issues if i["number"] == focus_issue), None
        )
        if target is None:
            # focused issue ব্যস্ত/নেই — তবু SOLVE_ISSUE মোডে instruction দেওয়া যায়
            target = {"number": focus_issue, "title": "(manual focus)", "labels": []}
        return "SOLVE_ISSUE", target

    if state.github_available:
        if state.main_ci == "red":
            return "FIX_RED_MAIN", {"number": 0, "title": "main CI লাল — Rank-1 interrupt"}
        if state.failing_prs:
            pr_no = state.failing_prs[0]
            return "CI_FAILURE", {"number": pr_no, "title": f"PR #{pr_no} failing checks"}
        if state.stale_prs:
            pr_no = state.stale_prs[0]
            return "REVIEW_PR", {"number": pr_no, "title": f"PR #{pr_no} stale >{STALE_PR_HOURS}h"}

    ready = [
        issue
        for issue in state.unclaimed_issues
        if not _earlier_seq_open(issue, state.unclaimed_issues)
    ]
    if ready:
        return "SOLVE_ISSUE", sorted(ready, key=_issue_sort_key)[0]

    return "ADVERSARIAL_AUDIT", {"number": 0, "title": "breaker rotation (কোনো queue-তে কাজ নেই)"}


# ────────────────────────── Phase 4: instruction ──────────────────────────


def _task_id(slot: str) -> str:
    stamp = _now().strftime("%Y%m%d-%H%M%S")
    safe_slot = re.sub(r"[^a-zA-Z0-9_-]", "-", slot)
    return f"task-{stamp}-{safe_slot}"


def build_assignment(
    mode: str,
    target: dict[str, Any],
    slot: str,
    state: AuditState,
    policies: dict[str, dict[str, Any]],
) -> TaskAssignment:
    """Dynamic Instruction-এর data — smart context selection সহ।

    Smart context: coding-task হলে review_rules পাঠানো হয় না; review-task
    হলে coding rules নয় — শুধু সংশ্লিষ্ট rule-set (plan §Smart Context Selection)।
    """
    policy = policies.get(mode) or {}
    if not policy:
        # অজানা mode — seed fallback module থেকে (defense-in-depth)
        policies_mod = _load_agent_policies_module()
        try:
            policy = dict(policies_mod.get_task_policy(mode))
        except ValueError:
            policy = {"rules": [], "forbidden_actions": [], "required_actions": []}

    labels = target.get("labels", [])
    group = next((lab[6:] for lab in labels if isinstance(lab, str) and lab.startswith("group:")), None)

    applicable = ["AGENTS.md v3 (universal contract — Layer 1)"]
    applicable.extend(f"task_rules:{mode} → {rule}" for rule in policy.get("rules", []))
    if group:
        applicable.append(f"group:{group} (staging rule — sequential merge hold)")

    context = {
        "repository": f"{GITHUB_REPO} @ HEAD {state.repo_head}",
        "branch": state.repo_branch,
        "dirty_files": state.repo_dirty,
        "main_ci": state.main_ci,
        "open_prs": len(state.open_prs),
        "failing_prs": state.failing_prs[:5],
        "stale_prs": state.stale_prs[:5],
        "unclaimed_issues": len(state.unclaimed_issues),
        "policy_source": state.policy_source,
        "history_entries": state.history_count,
    }

    # Universal stop conditions (plan-এর Dynamic Instruction Format)
    stop_conditions = [
        "declared scope-এর বাইরে পরিবর্তন দরকার হলে → STOP, blocker issue খোলো",
        "boot smoke fail করলে → STOP, revert, report",
        "pytest-এ new failure এলে → STOP, revert, report",
    ]
    if mode == "SOLVE_ISSUE":
        stop_conditions.append("কোনো ফাইলে 1+ active importer পাওয়া গেলে (deletion হলে) → skip that file")

    return TaskAssignment(
        mode=mode,
        task_id=_task_id(slot),
        slot=slot,
        objective=f"{target.get('title', '')} (issue #{target.get('number', 0)})".strip(),
        issue_numbers=[target["number"]] if target.get("number") else [],
        group=group,
        context=context,
        applicable_rules=applicable,
        required_actions=list(policy.get("required_actions", [])),
        forbidden_actions=list(policy.get("forbidden_actions", [])),
        validation=list(policy.get("validation", [])),
        stop_conditions=stop_conditions,
        expected_output=policy.get("expected_output", "PR / Issue / Comment (mode অনুযায়ী)"),
        permissions=policy.get("permissions", {}),
    )


def render_instruction(task: TaskAssignment) -> str:
    """Standard Dynamic Instruction Format (machine-readable, plan §format)।"""
    sep = "═" * 45
    lines = [
        "SUPREMEAI AGENT TASK",
        sep,
        "",
        f"MODE: {task.mode}",
        f"TASK_ID: {task.task_id}",
        f"SLOT: {task.slot}",
    ]
    if task.group:
        lines.append(f"GROUP: {task.group}")
    if task.issue_numbers:
        lines.append("ISSUES: " + ", ".join(f"#{n}" for n in task.issue_numbers))
    lines += [
        "",
        "OBJECTIVE:",
        f"  {task.objective}",
        "",
        "CONTEXT:",
    ]
    for key, value in task.context.items():
        lines.append(f"  {key}: {value}")
    lines += ["", "APPLICABLE RULES (priority order):"]
    lines.extend(f"  {idx}. {rule}" for idx, rule in enumerate(task.applicable_rules, 1))
    if task.permissions:
        granted = [k for k, v in task.permissions.items() if v]
        denied = [k for k, v in task.permissions.items() if not v]
        lines += ["", "PERMISSIONS:"]
        lines.append(f"  ✅ {', '.join(granted) if granted else '(none)'}")
        lines.append(f"  ❌ {', '.join(denied) if denied else '(none)'}")
    if task.required_actions:
        lines += ["", "REQUIRED ACTIONS:"]
        lines.extend(f"  {idx}. {action}" for idx, action in enumerate(task.required_actions, 1))
    if task.forbidden_actions:
        lines += ["", "FORBIDDEN ACTIONS:"]
        lines.extend(f"  ❌ {action}" for action in task.forbidden_actions)
    lines += ["", "VALIDATION (৩-স্তর):"]
    lines.extend(f"  - {item}" for item in task.validation)
    lines += ["", "STOP CONDITIONS:"]
    lines.extend(f"  - {item}" for item in task.stop_conditions)
    lines += ["", "EXPECTED OUTPUT:", f"  {task.expected_output}", "", sep]
    return "\n".join(lines)


# ────────────────────────── output ──────────────────────────


def render_audit_summary(state: AuditState) -> str:
    """Phase-1 audit summary — human-readable ছোট রিপোর্ট।"""
    gh = "live" if state.github_available else "offline (advisory)"
    lines = [
        "── AUDIT SUMMARY ──────────────────────────",
        f"repo: {state.repo_head} @ {state.repo_branch} ({state.repo_dirty} dirty)",
        f"github: {gh} · main_ci: {state.main_ci}",
        f"open PRs: {len(state.open_prs)} (failing: {len(state.failing_prs)}, "
        f"stale: {len(state.stale_prs)})",
        f"unclaimed issues: {len(state.unclaimed_issues)}",
        f"policy source: {state.policy_source} ({state.policy_count} task types) · "
        f"history: {state.history_count}",
    ]
    if state.db_note:
        lines.append(f"db: {state.db_note}")
    return "\n".join(lines)


def to_json(state: AuditState, task: TaskAssignment) -> str:
    """Machine-readable JSON output (CI/orchestration integration)।"""
    return json.dumps(
        {
            "audit": {
                "repo_head": state.repo_head,
                "repo_branch": state.repo_branch,
                "repo_dirty": state.repo_dirty,
                "github_available": state.github_available,
                "main_ci": state.main_ci,
                "open_prs": len(state.open_prs),
                "failing_prs": state.failing_prs,
                "stale_prs": state.stale_prs,
                "unclaimed_issues": len(state.unclaimed_issues),
                "policy_source": state.policy_source,
                "policy_count": state.policy_count,
                "history_count": state.history_count,
            },
            "assignment": {
                "mode": task.mode,
                "task_id": task.task_id,
                "slot": task.slot,
                "objective": task.objective,
                "issue_numbers": task.issue_numbers,
                "group": task.group,
                "permissions": task.permissions,
                "required_actions": task.required_actions,
                "forbidden_actions": task.forbidden_actions,
                "expected_output": task.expected_output,
            },
        },
        ensure_ascii=False,
        indent=2,
    )


# ────────────────────────── CLI ──────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SupremeAI Universal Agent Orchestrator — Dynamic Task Router (#2504)"
    )
    parser.add_argument("--slot", required=True, help="agent slot id, e.g. agent-1")
    parser.add_argument("--issue", type=int, default=None, help="নির্দিষ্ট issue-তে focus")
    parser.add_argument("--json", action="store_true", help="machine-readable JSON output")
    parser.add_argument(
        "--dry-run", action="store_true", help="DB seed/write ছাড়া read-only মোড"
    )
    parser.add_argument(
        "--db-url", default=None, help="Postgres URL (OPERATIONAL_TRUTH_DB_URL fallback)"
    )
    parser.add_argument(
        "--sqlite", default=None, help="SQLite mirror path (default: data/operational_truth.db থাকলে)"
    )
    parser.add_argument(
        "--no-github", action="store_true", help="GitHub API skip (offline audit)"
    )
    args = parser.parse_args(argv)

    token = None if args.no_github else (
        os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    )

    # Phase 1 — audit
    state = run_audit(token, args.db_url, args.sqlite, args.dry_run)

    # Phase 2 — policy load (audit-এ লোড হয়েছে; এখানে instruction-এর জন্য আবার)
    policies, _, _ = load_policies(args.db_url, args.sqlite, args.dry_run)

    # Phase 3 — prioritize
    mode, target = prioritize(state, args.issue)

    # Phase 4 — assign + render
    task = build_assignment(mode, target, args.slot, state, policies)

    if args.json:
        print(to_json(state, task))
    else:
        print(render_audit_summary(state))
        print()
        print(render_instruction(task))
    return 0


if __name__ == "__main__":
    sys.exit(main())
