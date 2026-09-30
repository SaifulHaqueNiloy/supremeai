# বাংলা মন্তব্য: Issue #2645 — "Fully Intelligent Auto-Merge Engine" চুক্তির
# রিগ্রেশন টেস্ট স্যুট।
"""Regression tests for the intelligent auto-merge engine (#2645).

মূল চুক্তি: মার্জ-ট্রেইন এখন টেক্সট-কনফ্লিক্ট ছাড়াও **সিমান্টিক (AST/সিগনেচার)
কনফ্লিক্ট** ধরবে, AI সেন্টিনেল নিরাপত্তা-স্ক্যান করবে, main-এ মার্জের আগে
ভার্চুয়াল স্টেজিং চালাবে, লিন্ট-ব্যর্থতায় সেলফ-হিলিং করবে এবং ফ্ল্যাকি টেস্টকে
আসল বাগ থেকে আলাদা করবে (pass^k)। সব নির্ণয়ের pure স্তর নেটওয়ার্কমুক্ত —
`--noconftest` সামঞ্জস্যপূর্ণ (#2620/#2630 প্যাটার্ন)।
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

MERGER_PATH = (
    Path(__file__).resolve().parents[3] / "scripts" / "ci" / "smart_priority_merger.py"
)
ROLLUP_PATH = (
    Path(__file__).resolve().parents[3] / "scripts" / "ci" / "merge_train_rollup.py"
)


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"module spec লোড ব্যর্থ: {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mod = _load_module(MERGER_PATH, "smart_priority_merger_under_test_2645")
rollup = _load_module(ROLLUP_PATH, "merge_train_rollup_under_test_2645")


# ── ফিক্সচার হেল্পার ────────────────────────────────────────────────────────────
def _pr(
    files: list[str],
    additions: int = 10,
    deletions: int = 2,
    number: int = 1,
    patches: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "number": number,
        "title": "feat(test): sample",
        "author": {"login": "someone"},
        "labels": [{"name": "queue:hold"}],
        "mergeable": "MERGEABLE",
        "isDraft": False,
        "body": "## Test Evidence\npytest passed (exit=0)",
        "additions": additions,
        "deletions": deletions,
        "files": [
            {"path": p, "patch": (patches or {}).get(p, "")} for p in files
        ],
    }


def _queued(number: int, title: str, files: list[str]) -> Any:
    return rollup.QueuedPR(number=number, title=title, head_branch=f"b{number}", files=files)


# ═══ ১. SemanticRiskClassifier ═══
class TestSemanticRiskClassifier:
    def test_extract_signatures_includes_methods_and_classes(self):
        src = (
            "class Greeter:\n"
            "    def hello(self, name: str) -> str:\n"
            "        return name\n"
            "\n"
            "def top_level(a, b=2):\n"
            "    return a + b\n"
        )
        sigs = mod.SemanticRiskClassifier.extract_python_signatures(src)
        assert sigs["Greeter"] == ""  # বাংলা মন্তব্য: ক্লাস নিজে সিগনেচারবিহীন
        assert "self, name: str" in sigs["Greeter.hello"]
        assert "a, b=2" in sigs["top_level"]

    def test_extract_signatures_broken_source_is_safe(self):
        # বাংলা মন্তব্য: সিনট্যাক্স-ভাঙা সোর্সে কখনো exception নয় — খালি ম্যাপ
        assert mod.SemanticRiskClassifier.extract_python_signatures("def broken(:") == {}
        assert mod.SemanticRiskClassifier.extract_python_signatures("") == {}

    def test_signature_drift_changed_and_removed(self):
        base = mod.SemanticRiskClassifier.extract_python_signatures(
            "def pay(amount):\n    return amount\n"
        )
        head = mod.SemanticRiskClassifier.extract_python_signatures(
            "def pay(amount, currency):\n    return amount\n"
        )
        drift = mod.SemanticRiskClassifier.find_signature_drift(base, head)
        assert drift["changed"] == ["pay"]
        assert drift["removed"] == []

    def test_signature_drift_removed_function(self):
        base = mod.SemanticRiskClassifier.extract_python_signatures(
            "def old_api(x):\n    return x\n"
        )
        head = mod.SemanticRiskClassifier.extract_python_signatures("x = 1\n")
        drift = mod.SemanticRiskClassifier.find_signature_drift(base, head)
        assert drift["removed"] == ["old_api"]
        assert drift["changed"] == []

    def test_parse_signature_ops_added_removed_changed(self):
        patch = (
            "@@ -1,3 +1,4 @@\n"
            "-def greet(name):\n"
            "+def greet(name, excited=False):\n"
            "+def brand_new():\n"
            " ctx_line\n"
        )
        ops = mod.SemanticRiskClassifier.parse_signature_ops_from_patch(patch)
        assert ops["greet"] == "changed"
        assert ops["brand_new"] == "added"

    def test_cross_pr_overlap_detection(self):
        cls = mod.SemanticRiskClassifier
        a = cls.parse_signature_ops_from_patch("+def shared_api(x):\n")
        b = cls.parse_signature_ops_from_patch("-def shared_api(y):\n")
        assert cls.find_cross_pr_function_overlap(a, b) == ["shared_api"]
        c = cls.parse_signature_ops_from_patch("+def different():\n")
        assert cls.find_cross_pr_function_overlap(a, c) == []

    def test_assess_low_for_tiny_docs_change(self):
        level, reasons = mod.SemanticRiskClassifier.assess(
            _pr(["docs/guide.md"], additions=4, deletions=1)
        )
        assert level == "LOW"
        assert reasons == []

    def test_assess_high_for_critical_dir(self):
        level, reasons = mod.SemanticRiskClassifier.assess(
            _pr(["backend/auth/login.py"], additions=30, deletions=5)
        )
        assert level == "HIGH"
        assert any("critical-dir" in r for r in reasons)

    def test_assess_high_for_large_diff(self):
        level, reasons = mod.SemanticRiskClassifier.assess(
            _pr(["frontend/app.js"], additions=500, deletions=50)
        )
        assert level == "HIGH"
        assert any("large-diff" in r for r in reasons)

    def test_assess_medium_for_small_py_change(self):
        level, _ = mod.SemanticRiskClassifier.assess(
            _pr(["scripts/utils.py"], additions=20, deletions=4)
        )
        assert level == "MEDIUM"

    def test_assess_high_on_cross_pr_semantic_conflict(self):
        cls = mod.SemanticRiskClassifier
        patch_a = "-def calc_total(items):\n+def calc_total(items, tax):\n"
        patch_b = "-def calc_total(items):\n+def calc_total(items, discount):\n"
        pr_a = _pr(["scripts/billing.py"], patches={"scripts/billing.py": patch_a}, number=1)
        pr_b = _pr(["scripts/billing.py"], patches={"scripts/billing.py": patch_b}, number=2)
        level, reasons = cls.assess(pr_a, peer_prs=[pr_b])
        assert level == "HIGH"
        assert any("semantic-conflict-suspect" in r for r in reasons)
        # বাংলা মন্তব্য: peer ছাড়া একই PR নিজের সাথে মিলবে না
        level_solo, _ = cls.assess(pr_a)
        assert level_solo != "HIGH" or any("semantic" not in r for r in reasons)


# ═══ ২. AISentinelReviewer ═══
class TestAISentinelReviewer:
    def test_build_prompt_truncates_huge_diff(self):
        huge = "x" * (mod.AISentinelReviewer.MAX_DIFF_CHARS + 5000)
        prompt = mod.AISentinelReviewer.build_prompt("t", huge)
        assert len(prompt) < mod.AISentinelReviewer.MAX_DIFF_CHARS + 2000
        assert "বিশাল diff" in prompt  # বাংলা মন্তব্য: ট্রাংকেশন-মার্কার উপস্থিত

    def test_parse_verdict_plain_json(self):
        v = mod.AISentinelReviewer.parse_verdict(
            '{"verdict": "LGTM", "risk": "low", "issues": [], "note": "ঠিক আছে"}'
        )
        assert v["verdict"] == "LGTM" and v["risk"] == "low"

    def test_parse_verdict_markdown_fenced(self):
        v = mod.AISentinelReviewer.parse_verdict(
            '```json\n{"verdict": "BLOCK", "risk": "high", "issues": ["hardcoded key"], "note": "x"}\n```'
        )
        assert v["verdict"] == "BLOCK" and "hardcoded key" in v["issues"][0]

    def test_parse_verdict_garbage_is_unknown(self):
        assert mod.AISentinelReviewer.parse_verdict("no json at all")["verdict"] == "UNKNOWN"
        assert mod.AISentinelReviewer.parse_verdict("")["verdict"] == "UNKNOWN"
        assert mod.AISentinelReviewer.parse_verdict(
            '{"verdict": "MAYBE"}'
        )["verdict"] == "UNKNOWN"

    def test_kill_switch_disables_review(self, monkeypatch):
        monkeypatch.setenv("MERGE_TRAIN_SENTINEL", "off")
        assert mod.AISentinelReviewer.is_enabled() is False
        v = mod.AISentinelReviewer.review("t", "diff")
        assert v["verdict"] == "DISABLED"
        monkeypatch.delenv("MERGE_TRAIN_SENTINEL", raising=False)
        assert mod.AISentinelReviewer.is_enabled() is True

    def test_review_skipped_without_provider_keys(self, monkeypatch):
        for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
            monkeypatch.delenv(key, raising=False)
        v = mod.AISentinelReviewer.review("t", "diff")
        assert v["verdict"] == "SKIPPED"
        assert v["note"] == "no-provider-key"

    def test_high_risk_fail_closed_without_consensus(self, monkeypatch):
        # বাংলা মন্তব্য: ১টি প্রোভাইডার কনফিগার + LGTM হলেও HIGH-রিস্ক ব্লক হবে
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setattr(
            mod.AISentinelReviewer, "_call_provider",
            staticmethod(lambda p, prompt: '{"verdict": "LGTM", "risk": "low", "issues": []}'),
        )
        v = mod.AISentinelReviewer.review("t", "diff", high_risk=True)
        assert v["verdict"] == "BLOCK"
        assert any("consensus" in i for i in v["issues"])

    def test_high_risk_consensus_passes_with_two_lgtms(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GEMINI_API_KEY", "k2")
        responses = iter([
            '{"verdict": "LGTM", "risk": "low", "issues": []}',
            '{"verdict": "LGTM", "risk": "low", "issues": []}',
        ])
        monkeypatch.setattr(
            mod.AISentinelReviewer, "_call_provider",
            staticmethod(lambda p, prompt: next(responses)),
        )
        v = mod.AISentinelReviewer.review("t", "diff", high_risk=True)
        assert v["verdict"] == "LGTM"
        assert "consensus:" in v["note"]

    def test_any_block_wins_immediately(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GEMINI_API_KEY", "k2")
        responses = iter([
            '{"verdict": "LGTM", "risk": "low", "issues": []}',
            '{"verdict": "BLOCK", "risk": "high", "issues": ["eval() found"], "note": "x"}',
        ])
        monkeypatch.setattr(
            mod.AISentinelReviewer, "_call_provider",
            staticmethod(lambda p, prompt: next(responses)),
        )
        v = mod.AISentinelReviewer.review("t", "diff", high_risk=False)
        assert v["verdict"] == "BLOCK"
        assert "eval() found" in v["issues"][0]

    def test_all_provider_errors_stay_neutral(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setattr(
            mod.AISentinelReviewer, "_call_provider", staticmethod(lambda p, prompt: None)
        )
        v = mod.AISentinelReviewer.review("t", "diff", high_risk=False)
        assert v["verdict"] == "ERROR"


# ═══ ৩. SpeculativeStagingRunner ═══
class TestSpeculativeStagingRunner:
    def test_worktree_command_plan_shape(self):
        plan = mod.SpeculativeStagingRunner.build_worktree_commands(
            "feature-x", wt_path="/tmp/stage"
        )
        assert plan[0][:3] == ["git", "fetch", "origin"]
        assert plan[1][:3] == ["git", "worktree", "add"]
        assert "--detach" in plan[1]
        merge_cmd = plan[2]
        # বাংলা মন্তব্য: ["git", "-C", wt, "merge", "--no-ff", ...] — সূচি ৩ ও ৪
        assert merge_cmd[3:5] == ["merge", "--no-ff"]
        assert merge_cmd[-1] == "origin/feature-x"

    def test_kill_switch(self, monkeypatch):
        monkeypatch.setenv("MERGE_TRAIN_SPECULATIVE", "off")
        ok, msg = mod.SpeculativeStagingRunner.run("any-branch")
        assert ok is True and "disabled" in msg


# ═══ ৪. SelfHealingPatcher ═══
class TestSelfHealingPatcher:
    def test_classify_lint_failure(self):
        log = "backend/tests/x.py:1:1: UP035 `typing.Callable` is deprecated, exit=123"
        assert mod.SelfHealingPatcher.classify_failure(log) == "lint"

    def test_classify_format_failure(self):
        assert mod.SelfHealingPatcher.classify_failure("would reformat 2 files") == "format"

    def test_classify_test_failure_is_not_healable(self):
        # বাংলা মন্তব্য: গভীর টেস্ট-ব্যর্থতা কখনো auto-fix নয় — আসল বাগ
        log = "FAILED tests/test_billing.py::test_calc - AssertionError"
        assert mod.SelfHealingPatcher.classify_failure(log) == "unknown"
        assert mod.SelfHealingPatcher.is_healable(log) is False

    def test_kill_switch(self, monkeypatch):
        monkeypatch.setenv("MERGE_TRAIN_AUTO_HEAL", "off")
        ok, msg = mod.SelfHealingPatcher.heal(1, "b", ["x.py"])
        assert ok is False and "disabled" in msg

    def test_refuses_protected_paths(self, monkeypatch):
        monkeypatch.delenv("MERGE_TRAIN_AUTO_HEAL", raising=False)
        mod.SelfHealingPatcher._attempts.clear()
        mod.SelfHealingPatcher._total_heals = 0
        ok, msg = mod.SelfHealingPatcher.heal(2, "b", [".github/workflows/pr.yml"])
        assert ok is False and "protected-paths-refused" in msg
        # বাংলা মন্তব্য: ব্যর্থ চেষ্টাও বাজেট খরচ করবে না
        assert mod.SelfHealingPatcher._total_heals == 0

    def test_refuses_non_python_targets(self, monkeypatch):
        monkeypatch.delenv("MERGE_TRAIN_AUTO_HEAL", raising=False)
        mod.SelfHealingPatcher._attempts.clear()
        mod.SelfHealingPatcher._total_heals = 0
        ok, msg = mod.SelfHealingPatcher.heal(3, "b", ["docs/readme.md"])
        assert ok is False and msg == "no-python-files"

    def test_budget_limits_attempts(self):
        mod.SelfHealingPatcher._attempts.clear()
        mod.SelfHealingPatcher._total_heals = 0
        pr = 9
        for _ in range(mod.SelfHealingPatcher.MAX_ATTEMPTS_PER_RUN):
            assert mod.SelfHealingPatcher.budget_left(pr) is True
            mod.SelfHealingPatcher._attempts[pr] = mod.SelfHealingPatcher._attempts.get(pr, 0) + 1
        assert mod.SelfHealingPatcher.budget_left(pr) is False
        mod.SelfHealingPatcher._attempts.clear()
        mod.SelfHealingPatcher._total_heals = 0


# ═══ ৫. FlakyTriageEngine ═══
class TestFlakyTriageEngine:
    def test_classify_sequences(self):
        e = mod.FlakyTriageEngine
        assert e.classify_sequence([]) == "stable-fail"
        assert e.classify_sequence([True, True]) == "stable-pass"
        assert e.classify_sequence([False, False]) == "stable-fail"
        assert e.classify_sequence([False, True]) == "flaky-pass^1"
        assert e.classify_sequence([False, True, True]) == "flaky-pass^2"

    def test_parse_pytest_failures(self):
        log = (
            "FAILED tests/test_a.py::test_one - assert 1 == 2\n"
            "ERROR tests/test_b.py::test_two - Exception\n"
            "PASSED tests/test_c.py::test_three\n"
        )
        ids = mod.FlakyTriageEngine.parse_pytest_failures(log)
        assert "tests/test_a.py::test_one" in ids
        assert "tests/test_b.py::test_two" in ids
        assert all("test_three" not in i for i in ids)

    def test_flaky_comment_has_pass_k_evidence(self):
        comment = mod.FlakyTriageEngine.build_flaky_comment(
            ["tests/test_net.py::test_call"], k=2
        )
        assert "pass^2" in comment and "tests/test_net.py::test_call" in comment

    def test_kill_switch(self, monkeypatch):
        monkeypatch.setenv("MERGE_TRAIN_FLAKY_RERUN", "off")
        assert mod.FlakyTriageEngine.schedule_rerun([123]) == 0


# ═══ ৬. Rollup Batching + Auto-Revert Watchdog + Release Notes ═══
class TestRollupIntelligence:
    def test_touches_excluded_dir(self):
        assert rollup.touches_excluded_dir(["backend/auth/login.py"]) is True
        assert rollup.touches_excluded_dir([".github/workflows/pr.yml"]) is True
        assert rollup.touches_excluded_dir(["docs/guide.md"]) is False

    def test_rollup_eligibility_requires_benign_title(self):
        benign = _queued(1, "docs: fix typo in readme", ["docs/a.md"])
        core = _queued(2, "feat(auth): rotate keys", ["backend/auth/x.py"])
        assert rollup.is_rollup_eligible(benign) is True
        assert rollup.is_rollup_eligible(core) is False

    def test_rollup_eligibility_respects_diff_budget(self):
        benign = _queued(3, "chore: cleanup", ["scripts/cleanup.py"])
        assert rollup.is_rollup_eligible(benign, diff_lines=50) is True
        assert rollup.is_rollup_eligible(benign, diff_lines=500) is False

    def test_plan_batches_benign_and_isolates_core(self):
        doc1 = _queued(10, "docs: typo fix", ["docs/a.md"])
        doc2 = _queued(11, "docs: another typo", ["docs/b.md"])
        doc3 = _queued(12, "chore: cleanup notes", ["docs/c.md"])
        doc4 = _queued(13, "docs: more fixes", ["docs/d.md"])
        doc5 = _queued(14, "docs: extra", ["docs/e.md"])
        core = _queued(20, "feat(db): migration", ["backend/alembic_migrations/x.py"])
        plan = rollup.plan_single_flight_vs_rollup(
            [doc1, doc2, doc3, doc4, doc5, core], max_batch=4
        )
        # বাংলা মন্তব্য: ব্যাচে সর্বোচ্চ max_batch সদস্য, কোর সবসময় single-flight
        assert len(plan["rollup_batch"]) == 4
        assert core.number in plan["single_flight"]
        assert doc5.number in plan["deferred"]

    def test_overlapping_benign_prs_deferred(self):
        a = _queued(30, "docs: fix", ["docs/shared.md"])
        b = _queued(31, "docs: fix2", ["docs/shared.md"])
        plan = rollup.plan_single_flight_vs_rollup([a, b])
        assert plan["rollup_batch"] == [30]
        assert 31 in plan["deferred"]

    def test_bengali_release_note_lists_prs(self):
        note = rollup.build_bengali_release_note(
            [_queued(40, "docs: fix typo", []), _queued(41, "chore: cleanup", [])]
        )
        assert "#40" in note and "#41" in note
        assert "রিলিজ নোট" in note
        assert rollup.build_bengali_release_note([]) == "📭 এই ব্যাচে কোনো মার্জ হয়নি।"

    def test_auto_revert_kill_switch(self, monkeypatch):
        monkeypatch.setenv("MERGE_TRAIN_AUTO_REVERT", "off")
        engine = rollup.RollupEngine()
        result = engine.create_auto_revert_pr("deadbeefcafe", "smoke failed")
        assert result["success"] is False
        assert "kill-switch" in result["error"]
