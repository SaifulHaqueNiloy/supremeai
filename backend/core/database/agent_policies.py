"""Universal Agent task-policy layer — Layer 2 canonical seed (issue #2504, seq:1).

বাংলা মন্তব্য:
Universal Agent Architecture-এর মূল নীতি — "Agent type নয় → Task type।
Task chooses capability; model does not define the task."

এই module-টি Layer 2 (Database: Task Policy) এর **canonical seed truth**:
  - ১০টি task type-এর rules / required-actions / forbidden-actions / permissions
  - DB পৌঁছানো গেলে `task_policies`/`task_permissions` টেবিল থেকে override পড়া হয়,
  - DB unreachable হলে এই seed-ই runtime fallback (fail-soft, অডিটযোগ্য)।

Pure-data module — কোনো I/O বা heavy dependency নেই; scripts/agents/ থেকেও
import করা যায় (backend root sys.path-এ থাকলেই যথেষ্ট)।

Tables (Alembic `univ_agent_0001` + scripts/operations/operational_truth_db.py mirror):
  task_policies        — task_type PK, rules/forbidden/required JSON
  task_permissions     — task_type PK, permission boolean columns
  agent_task_history   — learning-loop ledger (নাম ইচ্ছাকৃত: লাইভ LLM-ledger
                         `task_history`-র সাথে সংঘর্ষ এড়াতে "agent_" prefix)
  router_patterns      — self-improving router-এর শেখা pattern cache
"""

from __future__ import annotations

from typing import Any

# ── ৮-স্তর rule layering (plan: UNIFIED_AGENT_ARCHITECTURE_V2_MERGED.md) ──
RULE_LAYERING: tuple[str, ...] = (
    "1. Admin / Core Governance (highest — override করতে পারে না)",
    "2. AGENTS.md v3 (universal — সব task-এ থাকবে)",
    "3. Security Rules (task-specific)",
    "4. Task Rules (coding/audit/review/breaker)",
    "5. Group Rules (group-specific staging)",
    "6. Issue Rules (acceptance criteria)",
    "7. Repository Context (current architecture)",
    "8. Historical Knowledge (lowest — truth নয়, শুধু reference)",
)

# সব permission key — task_permissions টেবিলের boolean column-গুলোর mirror
PERMISSION_KEYS: tuple[str, ...] = (
    "read_repo",
    "modify_code",
    "create_issue",
    "create_pr",
    "comment",
    "merge_pr",
    "write_db",
)

# ── Canonical task-type policy seed ─────────────────────────────────────────
# বাংলা মন্তব্য: প্রতিটি entry = task_policies + task_permissions row-জোড়া।
# rules/forbidden/required তালিকাগুলো Dynamic Instruction-এ APPLICABLE RULES /
# FORBIDDEN ACTIONS / REQUIRED ACTIONS সেকশনে সরাসরি বসে।

TASK_POLICIES: dict[str, dict[str, Any]] = {
    "INITIAL_AUDIT": {
        "summary": "কোডবেস audit করে issue তৈরি করে",
        "permissions": {
            "read_repo": True,
            "modify_code": False,
            "create_issue": True,
            "create_pr": False,
            "comment": True,
            "merge_pr": False,
            "write_db": False,
        },
        "rules": [
            "Verify First: প্রতিটি finding-এর প্রমাণ সংগ্রহ করো (grep/import/call evidence)",
            "Finding-এ file:line reference + impact বাধ্যতামূলক",
            "Issue তৈরি করবে স্ট্যান্ডার্ড প্রোটোকলে (group/seq/area/type label সহ)",
        ],
        "required_actions": [
            "কোডবেসের লক্ষ্য-এলাকা scan করো",
            "প্রতিটি finding-এর evidence যাচাই করো (Tier-1 reflection)",
            "প্রতিটি finding-এর জন্য GitHub issue খোলো (priority label সহ)",
        ],
        "forbidden_actions": [
            "কোড পরিবর্তন / PR খোলা সম্পূর্ণ নিষিদ্ধ (modify_code=False)",
            "অপ্রমাণিত অনুমান নিয়ে issue তৈরি করা",
        ],
        "validation": [
            "প্রতিটি issue-তে evidence section আছে কিনা",
            "label সেট সম্পূর্ণ (priority + area + type) কিনা",
        ],
        "expected_output": "GitHub issues (P0-critical/P1-high label সহ)",
    },
    "SOLVE_ISSUE": {
        "summary": "issue solve করে PR খোলে",
        "permissions": {
            "read_repo": True,
            "modify_code": True,
            "create_issue": False,
            "create_pr": True,
            "comment": True,
            "merge_pr": False,
            "write_db": False,
        },
        "rules": [
            "Atomic Claim Lock: claim ছাড়া কোড নয় — 'Touching files:' ঘোষণা বাধ্যতামূলক",
            "৩-স্তর যাচাই: (১) Reflection/grep → (২) Boot smoke (import main) → (৩) Pytest",
            "Scope Gate: declared files-এর বাইরে touch নিষিদ্ধ",
        ],
        "required_actions": [
            "atomic_claim.sh দিয়ে issue claim করো",
            "root cause প্রমাণ করো (reproduce → fix)",
            "৩-স্তর verification চালাও ও PR body-তে Test Evidence দাও",
            "PR খুলে সাথে সাথে has-pr label দাও",
        ],
        "forbidden_actions": [
            "টেস্ট delete/skip/fake assertion — সর্বোচ্চ অপরাধ",
            "নিজের PR নিজে approve/merge করা",
            "CI check disable / security weaken",
            "failure hide / unrelated change",
        ],
        "validation": [
            "PR body-তে Test Evidence section (min 40 chars, output marker সহ)",
            "pytest-এ 0 new failure",
            "PR green (pr-gate:passed)",
        ],
        "expected_output": "PR (queue:hold নীতি মেনে sequential merge-এর জন্য)",
    },
    "REVIEW_PR": {
        "summary": "PR review করে 4-Pillar Rubric দিয়ে",
        "permissions": {
            "read_repo": True,
            "modify_code": False,
            "create_issue": True,
            "create_pr": False,
            "comment": True,
            "merge_pr": False,
            "write_db": False,
        },
        "rules": [
            "4-Pillar Rubric: Stability / Real Benefit / Zero Regression / Scope",
            "নিজের PR review নিষিদ্ধ (self-review conflict)",
            "প্রতিটি verdict-এর সাথে evidence (diff line reference)",
        ],
        "required_actions": [
            "PR diff সম্পূর্ণ পড়ো",
            "4-Pillar প্রতিটির জন্য verdict + evidence লেখো",
            "টেস্ট ম্যানিপুলেশন স্ক্যান করো (skip marker/delete/fake)",
        ],
        "forbidden_actions": [
            "কোড পরিবর্তন (comment-only task)",
            "merge করা (merge_pr=False)",
        ],
        "validation": ["comment-এ ৪টি pillar-ই কভার হয়েছে কিনা"],
        "expected_output": "PR review comment (4-Pillar verdict)",
    },
    "MERGE_GROUP": {
        "summary": "গ্রুপ merge করে (verified হলে)",
        "permissions": {
            "read_repo": True,
            "modify_code": False,
            "create_issue": False,
            "create_pr": False,
            "comment": True,
            "merge_pr": True,
            "write_db": False,
        },
        "rules": [
            "বিনা verify মার্জ নিষিদ্ধ — Group Verification pass বাধ্যতামূলক",
            "Predecessor Group Merge Hold: পূর্ববর্তী গ্রুপ সম্পূর্ণ না হলে merge নিষিদ্ধ",
            "Capability Harvest: zero capability loss নিশ্চিত করো",
        ],
        "required_actions": [
            "গ্রুপের সব PR/commit একসাথে যাচাই করো",
            "CI 100% green নিশ্চিত করো",
            "merge-sequence নথিভুক্ত করো",
        ],
        "forbidden_actions": [
            "queue:hold চুক্তি ভাঙা",
            "লাল/অসম্পূর্ণ CI সহ merge",
        ],
        "validation": ["সব grouped PR green + verification comment আছে কিনা"],
        "expected_output": "Merge (verified) + merge record comment",
    },
    "CLEANUP": {
        "summary": "dead code delete করে",
        "permissions": {
            "read_repo": True,
            "modify_code": True,
            "create_issue": False,
            "create_pr": True,
            "comment": True,
            "merge_pr": False,
            "write_db": False,
        },
        "rules": [
            "Verify-first deletion: প্রতিটি ফাইলের 0 importers প্রমাণিত হতে হবে (grep)",
            "Boot smoke + pytest-এ 0 new failure",
            "Batch আকারে ছোট রাখো (atomic review সম্ভব হয়)",
        ],
        "required_actions": [
            "প্রতিটি candidate-এর importer scan করো",
            "৩-স্তর verification চালাও",
            "deleted files list + evidence সহ PR খোলো",
        ],
        "forbidden_actions": [
            "৩-tier verify ছাড়া delete",
            "live/imported ফাইল delete",
        ],
        "validation": ["প্রতিটি deleted file-এর 0 importers প্রমাণ", "boot smoke PASS"],
        "expected_output": "PR (deleted list + 3-tier evidence)",
    },
    "FIX_RED_MAIN": {
        "summary": "main লাল হলে ঠিক করে",
        "permissions": {
            "read_repo": True,
            "modify_code": True,
            "create_issue": False,
            "create_pr": True,
            "comment": True,
            "merge_pr": False,
            "write_db": False,
        },
        "rules": [
            "Root cause খোঁজো — symptom mask করো না",
            "main লাল = সর্বোচ্চ অগ্রাধিকার (Rank-1 interrupt)",
        ],
        "required_actions": [
            "লাল CI-র failing job ও log বিশ্লেষণ করো",
            "root cause প্রমাণ করো",
            "ফিক্স + verification সহ দ্রুত PR খোলো",
        ],
        "forbidden_actions": [
            "CI disable / check bypass",
            "security weaken",
            "failure hide",
        ],
        "validation": ["main CI সবুজ হওয়া"],
        "expected_output": "PR (root-cause evidence সহ)",
    },
    "ADVERSARIAL_AUDIT": {
        "summary": "rule bypass + security gap খোঁজে (Breaker mode)",
        "permissions": {
            "read_repo": True,
            "modify_code": False,
            "create_issue": True,
            "create_pr": False,
            "comment": True,
            "merge_pr": False,
            "write_db": False,
        },
        "rules": [
            "৭টি breaker check: rule_bypass / security_gap / arch_weakness / scope_violation / test_manipulation / merge_bypass / permission_escalation",
            "নিজের সিস্টেম ভাঙার চেষ্টা করো — finding পেলে P0/P1 issue খোলো",
        ],
        "required_actions": [
            "প্রতিটি check vector-এ bypass চেষ্টা করো (read-only)",
            "finding হলে evidence সহ issue তৈরি করো",
        ],
        "forbidden_actions": [
            "কোড পরিবর্তন / PR / merge — শুধু findings",
        ],
        "validation": ["প্রতিটি finding-এ reproducible evidence"],
        "expected_output": "GitHub issues (P0-critical/P1-high)",
    },
    "CI_FAILURE": {
        "summary": "CI fail → root cause খোঁজে",
        "permissions": {
            "read_repo": True,
            "modify_code": True,
            "create_issue": False,
            "create_pr": True,
            "comment": True,
            "merge_pr": False,
            "write_db": False,
        },
        "rules": [
            "CI fail-এর root cause খোঁজো — check disable করবে না",
            "failing test-এর ইতিহাস দেখো (flake vs regression)",
        ],
        "required_actions": [
            "failing job-এর log বিশ্লেষণ",
            "লোকালে reproduce করো",
            "root-cause fix + PR",
        ],
        "forbidden_actions": [
            "check disable / failure hide",
            "skip marker যোগ করে সবুজ করা",
        ],
        "validation": ["সংশ্লিষ্ট CI job সবুজ"],
        "expected_output": "PR (root-cause analysis সহ)",
    },
    "GROUP_VERIFICATION": {
        "summary": "পুরো গ্রুপ একসাথে যাচাই",
        "permissions": {
            "read_repo": True,
            "modify_code": False,
            "create_issue": True,
            "create_pr": False,
            "comment": True,
            "merge_pr": False,
            "write_db": False,
        },
        "rules": [
            "individual PR green ≠ group correct — combined tree-এ যাচাই",
            "group-এর পুরো diff একসাথে audit করো",
        ],
        "required_actions": [
            "গ্রুপের সব পরিবর্তন stacked/combined করে যাচাই করো",
            "cross-PR interaction পরীক্ষা করো",
            "verdict comment দাও",
        ],
        "forbidden_actions": ["কোড পরিবর্তন", "merge করা"],
        "validation": ["combined-tree test result নথিভুক্ত"],
        "expected_output": "Group verification comment",
    },
    "LEARNING": {
        "summary": "task result → knowledge DB",
        "permissions": {
            "read_repo": True,
            "modify_code": False,
            "create_issue": False,
            "create_pr": False,
            "comment": True,
            "merge_pr": False,
            "write_db": True,
        },
        "rules": [
            "শুধু সফল+প্রমাণিত task থেকে knowledge record",
            "problem → root_cause → solution → files → tests পূর্ণ চেইন লেখো",
            "History = intelligence, source-of-truth নয়",
        ],
        "required_actions": [
            "task-এর outcome সংগ্রহ করো",
            "agent_task_history-তে record করো",
            "failed_approaches-ও রেকর্ড করো (একই ভুল দুবার নয়)",
        ],
        "forbidden_actions": [
            "কোড modify / rule change",
            "অপ্রমাণিত success claim",
        ],
        "validation": ["record-এ verification_result পূর্ণ"],
        "expected_output": "agent_task_history row",
    },
}


def get_task_policy(task_type: str) -> dict[str, Any]:
    """একটি task type-এর সম্পূর্ণ policy (rules+permissions+forbidden...)।"""
    try:
        policy = TASK_POLICIES[task_type]
    except KeyError:
        valid = ", ".join(TASK_POLICIES)
        raise ValueError(f"Unknown task type '{task_type}'. Valid: {valid}") from None
    return {**policy, "task_type": task_type}


def get_task_permissions(task_type: str) -> dict[str, bool]:
    """একটি task type-এর permission সেট (7 boolean key)।"""
    return dict(get_task_policy(task_type)["permissions"])


def policy_rows() -> list[dict[str, Any]]:
    """task_policies টেবিলের seed rows (DB upsert-এর জন্য)।"""
    rows: list[dict[str, Any]] = []
    for task_type, policy in TASK_POLICIES.items():
        rows.append(
            {
                "task_type": task_type,
                "summary": policy["summary"],
                "rules": policy["rules"],
                "required_actions": policy["required_actions"],
                "forbidden_actions": policy["forbidden_actions"],
                "validation": policy["validation"],
                "expected_output": policy["expected_output"],
            }
        )
    return rows


def permission_rows() -> list[dict[str, Any]]:
    """task_permissions টেবিলের seed rows (DB upsert-এর জন্য)।"""
    rows: list[dict[str, Any]] = []
    for task_type, policy in TASK_POLICIES.items():
        row: dict[str, Any] = {"task_type": task_type}
        row.update(policy["permissions"])
        rows.append(row)
    return rows


def validate_policy_integrity() -> list[str]:
    """Seed-এর self-check — সব task type-এর permission key সম্পূর্ণ কিনা।

    Returns: ত্রুটির তালিকা (খালি = ঠিক আছে)।
    """
    errors: list[str] = []
    for task_type, policy in TASK_POLICIES.items():
        perms = policy["permissions"]
        missing = [k for k in PERMISSION_KEYS if k not in perms]
        extra = [k for k in perms if k not in PERMISSION_KEYS]
        if missing:
            errors.append(f"{task_type}: missing permission keys {missing}")
        if extra:
            errors.append(f"{task_type}: unknown permission keys {extra}")
        for section in ("rules", "required_actions", "forbidden_actions"):
            if not policy.get(section):
                errors.append(f"{task_type}: empty '{section}'")
    return errors
