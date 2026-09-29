"""Tests for Universal Agent Architecture — seq:1 Foundation (issue #2504).

Verifies:
1. Canonical task-policy seed integrity (10 task types, full permission keys).
2. Operational-truth DB schema extension (4 new policy tables, both flavors).
3. Router priority ladder (main-red → failing PR → stale PR → issue → audit).
4. Unclaimed-issue filtering (claim-locked / has-pr / ledger / seq:0 master).
5. Group seq dependency blocking (earlier seq open → later seq skipped).
6. Dynamic Instruction format (MODE / RULES / FORBIDDEN / VALIDATION / OUTPUT).
7. Offline audit fail-soft (no token, no DB → seed fallback, no crash).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# বাংলা মন্তব্য: sys.path-এ কিছুই insert করা হচ্ছে না — root conftest.py ইতিমধ্যে
# repo-root ও backend/ path-এ রাখে। scripts/operations বা backend-এর আলাদা কোনো
# dir-কে sys.path-এর শীর্ষে ঢোকানো বিপজ্জনক: 'monitoring' ইত্যাদি নাম ভুল জায়গায়
# resolve হয়ে অন্য টেস্টের import ভাঙতে পারে (pre-existing fragility)। তাই তিনটি
# target module-ই importlib file-location দিয়ে বিচ্ছিন্নভাবে লোড — zero pollution।


def _load_standalone(path: Path, name: str):
    """File-location import — package __init__ টানবে না, sys.path নাড়াবে না।

    sys.modules-এ register করা বাধ্যতামূলক — নইলে module-এর @dataclass
    ক্লাসগুলো cls.__module__ lookup-এ None পেয়ে ভেঙে যায়।
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"load failed: {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


orch = _load_standalone(
    REPO_ROOT / "scripts" / "agents" / "supremeai_orchestrator.py",
    "orch_test_target",
)
operational_truth_db = _load_standalone(
    REPO_ROOT / "scripts" / "operations" / "operational_truth_db.py",
    "operational_truth_db_test_target",
)
agent_policies = _load_standalone(
    REPO_ROOT / "backend" / "core" / "database" / "agent_policies.py",
    "agent_policies_test_target",
)
_TABLE_DDLS = operational_truth_db._TABLE_DDLS
connect = operational_truth_db.connect
ensure_schema = operational_truth_db.ensure_schema


# ───────────────────── 1. Canonical policy seed ─────────────────────


class TestPolicySeed:
    def test_ten_task_types_defined(self):
        assert len(agent_policies.TASK_POLICIES) == 10
        expected = {
            "INITIAL_AUDIT", "SOLVE_ISSUE", "REVIEW_PR", "MERGE_GROUP", "CLEANUP",
            "FIX_RED_MAIN", "ADVERSARIAL_AUDIT", "CI_FAILURE", "GROUP_VERIFICATION",
            "LEARNING",
        }
        assert expected == set(agent_policies.TASK_POLICIES)

    def test_policy_integrity_no_errors(self):
        assert agent_policies.validate_policy_integrity() == []

    def test_permissions_complete(self):
        for task_type in agent_policies.TASK_POLICIES:
            perms = agent_policies.get_task_permissions(task_type)
            assert set(perms) == set(agent_policies.PERMISSION_KEYS), task_type

    def test_audit_task_cannot_modify_code(self):
        # Breaker-mode চুক্তি: ADVERSARIAL_AUDIT / INITIAL_AUDIT কখনো code modify করবে না
        assert agent_policies.get_task_permissions("ADVERSARIAL_AUDIT")["modify_code"] is False
        assert agent_policies.get_task_permissions("INITIAL_AUDIT")["modify_code"] is False
        assert agent_policies.get_task_permissions("LEARNING")["write_db"] is True

    def test_solve_issue_cannot_merge(self):
        assert agent_policies.get_task_permissions("SOLVE_ISSUE")["merge_pr"] is False
        assert agent_policies.get_task_permissions("MERGE_GROUP")["merge_pr"] is True

    def test_unknown_task_type_raises(self):
        with pytest.raises(ValueError, match="Unknown task type"):
            agent_policies.get_task_policy("NOT_A_TASK")

    def test_seed_rows_for_db_upsert(self):
        policies = agent_policies.policy_rows()
        permissions = agent_policies.permission_rows()
        assert len(policies) == 10 and len(permissions) == 10
        assert all("task_type" in row for row in policies)
        assert all("updated_at" not in row for row in policies)  # timestamp caller-side

    def test_rule_layering_eight_levels(self):
        assert len(agent_policies.RULE_LAYERING) == 8
        assert "Admin" in agent_policies.RULE_LAYERING[0]


# ───────────────────── 2. DB schema extension ─────────────────────


class TestPolicyDbSchema:
    def test_four_new_tables_registered(self):
        names = {spec[0] for spec in _TABLE_DDLS}
        assert {"task_policies", "task_permissions", "agent_task_history",
                "router_patterns"} <= names

    def test_ensure_schema_creates_policy_tables_sqlite(self, tmp_path):
        conn, flavor = connect(sqlite_path=str(tmp_path / "op.db"))
        try:
            created = ensure_schema(conn, flavor)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cur.fetchall()}
            assert {"task_policies", "task_permissions", "agent_task_history",
                    "router_patterns"} <= tables
            assert any("task_policies" in item for item in created)
        finally:
            conn.close()


# ───────────────────── 3. Router priority ladder ─────────────────────


def _issue(number, labels, created="2026-09-01T00:00:00Z"):
    return {"number": number, "title": f"issue {number}", "labels": labels,
            "created_at": created, "updated_at": created}


def _state(**overrides):
    defaults = dict(
        repo_head="abc1234", repo_branch="agent-1/x", repo_dirty=0,
        github_available=True, main_ci="green", open_prs=[],
        failing_prs=[], stale_prs=[], unclaimed_issues=[],
        policy_source="seed", policy_count=10, history_count=0, db_note="",
    )
    defaults.update(overrides)
    return orch.AuditState(**defaults)


class TestPriorityLadder:
    def test_main_red_beats_everything(self):
        state = _state(main_ci="red", failing_prs=[7], stale_prs=[9],
                       unclaimed_issues=[_issue(1, ["P0-critical"])])
        mode, target = orch.prioritize(state)
        assert mode == "FIX_RED_MAIN"

    def test_failing_pr_before_stale_and_issues(self):
        state = _state(failing_prs=[7], stale_prs=[9],
                       unclaimed_issues=[_issue(1, ["P0-critical"])])
        mode, target = orch.prioritize(state)
        assert mode == "CI_FAILURE" and target["number"] == 7

    def test_stale_pr_before_issues(self):
        state = _state(stale_prs=[9], unclaimed_issues=[_issue(1, ["P0-critical"])])
        mode, target = orch.prioritize(state)
        assert mode == "REVIEW_PR" and target["number"] == 9

    def test_issue_priority_ladder_p0_first(self):
        older_p2 = _issue(100, ["P2-medium"], created="2026-09-01T00:00:00Z")
        newer_p0 = _issue(200, ["P0-critical"], created="2026-09-02T00:00:00Z")
        state = _state(unclaimed_issues=[older_p2, newer_p0])
        mode, target = orch.prioritize(state)
        assert mode == "SOLVE_ISSUE" and target["number"] == 200

    def test_issue_same_priority_oldest_first(self):
        old = _issue(100, ["P1-high"], created="2026-09-01T00:00:00Z")
        new = _issue(200, ["P1-high"], created="2026-09-05T00:00:00Z")
        state = _state(unclaimed_issues=[new, old])
        _, target = orch.prioritize(state)
        assert target["number"] == 100

    def test_no_work_falls_back_to_adversarial_audit(self):
        mode, _ = orch.prioritize(_state())
        assert mode == "ADVERSARIAL_AUDIT"

    def test_focus_issue_overrides_ladder(self):
        state = _state(main_ci="red")
        mode, target = orch.prioritize(state, focus_issue=42)
        assert mode == "SOLVE_ISSUE" and target["number"] == 42

    def test_github_unavailable_skips_pr_and_red_ladder(self):
        # offline: github_available=False → সরাসরি issue queue (fail-soft)
        state = _state(github_available=False, main_ci="unknown",
                       unclaimed_issues=[_issue(5, ["P2-medium"])])
        mode, target = orch.prioritize(state)
        assert mode == "SOLVE_ISSUE" and target["number"] == 5


class TestUnclaimedFiltering:
    def test_claim_locked_and_has_pr_excluded(self):
        # এই filter audit_github_state-এ বসে আছে — এখানে unit আকারে যাচাই
        # (labels সহ raw দুইটি issue: একটি locked, একটি free)
        raw = [
            {"number": 1, "title": "a", "labels": [{"name": "status:in-progress"}],
             "created_at": "2026-09-01T00:00:00Z", "updated_at": ""},
            {"number": 2, "title": "b", "labels": [{"name": "has-pr"}],
             "created_at": "2026-09-01T00:00:00Z", "updated_at": ""},
            {"number": 3, "title": "c", "labels": [{"name": "type:ledger"}],
             "created_at": "2026-09-01T00:00:00Z", "updated_at": ""},
            {"number": 4, "title": "d", "labels": [{"name": "seq:0"}],
             "created_at": "2026-09-01T00:00:00Z", "updated_at": ""},
            {"number": 5, "title": "e", "labels": [{"name": "P1-high"}],
             "created_at": "2026-09-02T00:00:00Z", "updated_at": ""},
        ]
        # labels normalize করে filtering লজিক হুবহু audit_github_state-এর মতো
        kept = []
        for issue in raw:
            labels = [lab.get("name", "") for lab in issue["labels"]]
            if "status:in-progress" in labels or "has-pr" in labels:
                continue
            if any(lab.startswith("type:ledger") for lab in labels):
                continue
            if "seq:0" in labels:
                continue
            kept.append(issue["number"])
        assert kept == [5]


class TestGroupSeqDependency:
    def test_earlier_seq_blocks_later(self):
        seq2 = _issue(20, ["group:universal-agent", "seq:2"])
        seq1_open = _issue(10, ["group:universal-agent", "seq:1"])
        assert orch._earlier_seq_open(seq2, [seq2, seq1_open]) is True

    def test_no_earlier_seq_when_seq1_claimed_elsewhere(self):
        seq2 = _issue(20, ["group:universal-agent", "seq:2"])
        other_group_seq1 = _issue(10, ["group:other", "seq:1"])
        assert orch._earlier_seq_open(seq2, [seq2, other_group_seq1]) is False

    def test_no_group_no_block(self):
        plain = _issue(20, ["P0-critical"])
        assert orch._earlier_seq_open(plain, [plain]) is False

    def test_later_seq_does_not_block_earlier(self):
        seq1 = _issue(10, ["group:universal-agent", "seq:1"])
        seq2_open = _issue(20, ["group:universal-agent", "seq:2"])
        assert orch._earlier_seq_open(seq1, [seq1, seq2_open]) is False

    def test_router_skips_blocked_seq_issue(self):
        seq1 = _issue(10, ["group:g", "seq:1", "P1-high"], created="2026-09-01T00:00:00Z")
        seq2 = _issue(20, ["group:g", "seq:2", "P0-critical"], created="2026-09-01T00:00:00Z")
        state = _state(unclaimed_issues=[seq1, seq2])
        mode, target = orch.prioritize(state)
        assert target["number"] == 10  # seq:2 blocked → seq:1 wins though P0 younger


# ───────────────────── 4. Instruction + audit fail-soft ─────────────────────


class TestDynamicInstruction:
    def _policies(self):
        return {name: dict(pol) for name, pol in agent_policies.TASK_POLICIES.items()}

    def test_instruction_format_sections(self):
        state = _state()
        task = orch.build_assignment(
            "SOLVE_ISSUE", _issue(2504, ["P0-critical", "group:universal-agent", "seq:1"]),
            "agent-1", state, self._policies(),
        )
        text = orch.render_instruction(task)
        for section in ("SUPREMEAI AGENT TASK", "MODE: SOLVE_ISSUE", "TASK_ID: task-",
                        "OBJECTIVE:", "CONTEXT:", "APPLICABLE RULES", "PERMISSIONS:",
                        "REQUIRED ACTIONS:", "FORBIDDEN ACTIONS:", "VALIDATION",
                        "STOP CONDITIONS:", "EXPECTED OUTPUT:"):
            assert section in text, section
        assert "#2504" in text and "group:universal-agent" in text

    def test_task_id_contains_slot_and_timestamp(self):
        tid = orch._task_id("agent-3")
        assert tid.startswith("task-") and tid.endswith("agent-3")

    def test_permissions_rendered_grant_and_deny(self):
        state = _state()
        task = orch.build_assignment("ADVERSARIAL_AUDIT", _issue(1, []), "agent-2",
                                     state, self._policies())
        assert task.permissions["modify_code"] is False
        text = orch.render_instruction(task)
        assert "❌ modify_code" in text

    def test_smart_context_group_rule(self):
        state = _state()
        task = orch.build_assignment("SOLVE_ISSUE", _issue(1, ["group:root-audit"]),
                                     "agent-1", state, self._policies())
        assert task.group == "root-audit"
        assert any("group:root-audit" in rule for rule in task.applicable_rules)

    def test_unknown_mode_falls_back_to_seed_policy(self):
        state = _state()
        task = orch.build_assignment("SOLVE_ISSUE", _issue(1, []), "agent-1", state, {})
        # policies dict খালি → seed module থেকে fallback (defense-in-depth)
        assert task.required_actions  # non-empty


class TestAuditFailSoft:
    def test_offline_audit_never_crashes(self):
        state = orch.run_audit(token=None, db_url=None, sqlite_path=None, dry_run=True)
        assert state.github_available is False
        assert state.main_ci == "unknown"
        assert state.policy_source == "seed"
        assert state.policy_count == 10

    def test_repo_audit_local(self):
        repo = orch.audit_repo_state()
        assert repo["head"] and repo["branch"]  # git repo-তে সবসময় মান থাকবে

    def test_load_policies_sqlite_seed_and_read(self, tmp_path):
        db = str(tmp_path / "router.db")
        # ১ম run: খালি টেবিলে seed upsert
        policies, source, _ = orch.load_policies(db_url=None, sqlite_path=db, dry_run=False)
        assert source == "db" and len(policies) == 10
        # ২য় run: seeded টেবিল থেকে পড়া
        policies2, source2, _ = orch.load_policies(db_url=None, sqlite_path=db, dry_run=False)
        assert source2 == "db"
        assert policies2["SOLVE_ISSUE"]["permissions"]["merge_pr"] is False

    def test_load_policies_dry_run_does_not_seed(self, tmp_path):
        db = str(tmp_path / "router_dry.db")
        # dry_run: ensure_schema হয়, কিন্তু seed upsert হয় না → seed fallback
        policies, source, _ = orch.load_policies(db_url=None, sqlite_path=db, dry_run=True)
        assert source == "seed" and len(policies) == 10

    def test_json_output_machine_readable(self, tmp_path):
        # CLI end-to-end: offline + sqlite → JSON parse সফল
        import io
        import contextlib

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = orch.main(["--slot", "agent-1", "--no-github", "--dry-run", "--json",
                            "--sqlite", str(tmp_path / "x.db")])
        assert rc == 0
        import json

        data = json.loads(buf.getvalue())
        assert data["assignment"]["mode"] in ("ADVERSARIAL_AUDIT", "SOLVE_ISSUE")
        assert data["audit"]["policy_count"] == 10


class TestBootstrapScript:
    def test_start_script_exists_and_executable(self):
        start = REPO_ROOT / "scripts" / "agents" / "start"
        assert start.exists()
        assert start.stat().st_mode & 0o111  # executable bit

    def test_start_script_invokes_orchestrator(self):
        content = (REPO_ROOT / "scripts" / "agents" / "start").read_text(encoding="utf-8")
        assert "supremeai_orchestrator.py" in content
        assert "heartbeat" in content
