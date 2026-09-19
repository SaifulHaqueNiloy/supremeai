"""Unit tests for the per-group backend test planner (issue #470).

বাংলা: planner হলো #470-এর গ্রুপ-লেভেল সিদ্ধান্ত ইঞ্জিন। এই টেস্টগুলো
coverage-gate চুক্তি (PR #343 incident — fail-closed gate) লঙ্ঘন না করে
planner-এর সিদ্ধান্ত টেবিল লক করে: source/core-trigger/unknown → FULL,
test-only+cache-disabled → FULL, test-only+cache-enabled → SCOPED,
previous-failure → force include। fail-safe (exception/empty diff) → FULL।
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLANNER_PATH = REPO_ROOT / "scripts" / "ci" / "plan_backend_test_groups.py"

_spec = importlib.util.spec_from_file_location("plan_backend_test_groups", PLANNER_PATH)
planner = importlib.util.module_from_spec(_spec)
sys.modules["plan_backend_test_groups"] = planner
_spec.loader.exec_module(planner)


# ── FULL-mode contracts (coverage gate must never collapse) ─────────────────


def test_backend_source_change_is_full() -> None:
    plan = planner.classify(["backend/services/voice_service.py"])
    assert plan["mode"] == "full"
    assert plan["groups"] == set(planner.ALL_GROUP_KEYS)
    assert plan["reason"] == "backend-source-change-coverage-gate"


def test_core_trigger_change_is_full() -> None:
    for trigger in (
        "backend/pyproject.toml",
        "backend/poetry.lock",
        "backend/tests/conftest.py",
        "backend/core/config.py",
        "backend/main.py",
        ".github/workflows/ci.yml",
        ".github/actions/setup-backend/action.yml",
        "scripts/ci/coverage_policy.yaml",
    ):
        plan = planner.classify([trigger])
        assert plan["mode"] == "full", trigger
        assert plan["reason"] == "core-trigger-files", trigger


def test_migrations_change_is_full() -> None:
    plan = planner.classify(["backend/migrations/versions/0007_add_index.py"])
    assert plan["mode"] == "full"
    assert plan["reason"] == "core-trigger-files"


def test_empty_diff_is_full() -> None:
    plan = planner.classify([])
    assert plan["mode"] == "full"
    assert plan["reason"] == "empty-or-unusable-diff"


def test_unmapped_test_path_failsafe_full() -> None:
    plan = planner.classify(["backend/tests/some_new_dir/test_thing.py"])
    assert plan["mode"] == "full"
    assert plan["reason"].startswith("unmapped-test-path")


def test_tests_root_conftest_is_full() -> None:
    plan = planner.classify(["backend/tests/conftest.py"])
    assert plan["mode"] == "full"
    assert plan["reason"] == "core-trigger-files"


def test_scripts_change_v1_is_full() -> None:
    plan = planner.classify(["scripts/ci/build_release_evidence.py"])
    assert plan["mode"] == "full"


def test_mixed_source_and_test_is_full() -> None:
    plan = planner.classify(["backend/tests/api/test_health.py", "backend/api/routes/health.py"])
    assert plan["mode"] == "full"


# ── Scoped mode (armed, gated behind CI_COVERAGE_CACHE_ENABLED) ─────────────


def test_test_only_change_scoped_when_cache_enabled(monkeypatch) -> None:
    monkeypatch.setenv("CI_COVERAGE_CACHE_ENABLED", "true")
    plan = planner.classify(["backend/tests/api/test_health.py"])
    assert plan["mode"] == "scoped"
    assert plan["groups"] == {"fast"}


def test_test_only_change_full_when_cache_disabled(monkeypatch) -> None:
    monkeypatch.delenv("CI_COVERAGE_CACHE_ENABLED", raising=False)
    plan = planner.classify(["backend/tests/api/test_health.py"])
    assert plan["mode"] == "full"
    assert plan["groups"] == set(planner.ALL_GROUP_KEYS)


def test_scoped_mapping_directories(monkeypatch) -> None:
    monkeypatch.setenv("CI_COVERAGE_CACHE_ENABLED", "true")
    cases = {
        "backend/tests/agents/test_runner.py": {"services"},
        "backend/tests/brain/test_planner.py": {"core_support"},
        "backend/tests/llm/test_client.py": {"core_support"},
        "backend/tests/missions/test_mission.py": {"services"},
        "backend/tests/core/security/test_auth.py": {"fast"},
        "backend/tests/core/test_rate_limit_other.py": {"core_unit"},
        "backend/tests/runs/test_fabric.py": {"fast"},
    }
    for path, expected in cases.items():
        plan = planner.classify([path])
        assert plan["mode"] == "scoped", path
        assert plan["groups"] == expected, path


def test_fast_owned_core_files_map_to_fast(monkeypatch) -> None:
    monkeypatch.setenv("CI_COVERAGE_CACHE_ENABLED", "true")
    plan = planner.classify(["backend/tests/core/test_core_rate_limiter.py"])
    assert plan["groups"] == {"fast"}
    plan = planner.classify(["backend/tests/core/test_multi_tenant_isolation.py"])
    assert plan["groups"] == {"fast"}


def test_root_level_test_files_map_to_services(monkeypatch) -> None:
    monkeypatch.setenv("CI_COVERAGE_CACHE_ENABLED", "true")
    plan = planner.classify(["backend/tests/test_smoke_new.py"])
    assert plan["groups"] == {"services"}


# ── Previous-failure memory ─────────────────────────────────────────────────


def test_previous_failure_forces_group(monkeypatch) -> None:
    monkeypatch.delenv("CI_COVERAGE_CACHE_ENABLED", raising=False)
    plan = planner.classify(["backend/tests/api/test_health.py"])
    plan = planner.apply_previous_group_failures(plan, ["services"])
    assert plan["groups"] == set(planner.ALL_GROUP_KEYS)
    assert "previous-failure:services" in plan["reason"]


def test_previous_failure_unknown_group_ignored() -> None:
    plan = planner.classify(["backend/services/x.py"])
    before = set(plan["groups"])
    plan = planner.apply_previous_group_failures(plan, ["nonexistent_group"])
    assert plan["groups"] == before


def test_previous_failure_only_in_scoped_mode_adds_group(monkeypatch) -> None:
    monkeypatch.setenv("CI_COVERAGE_CACHE_ENABLED", "true")
    plan = planner.classify(["backend/tests/api/test_health.py"])
    plan = planner.apply_previous_group_failures(plan, ["core_support"])
    assert plan["groups"] == {"fast", "core_support"}


# ── Matrix JSON contract (consumed by ci.yml fromJSON) ──────────────────────


def test_build_matrix_json_full_contains_all_four_groups() -> None:
    data = json.loads(planner.build_matrix_json(list(planner.ALL_GROUP_KEYS)))
    names = [entry["group"] for entry in data["include"]]
    assert names == ["fast", "core-unit", "core-support", "services"]
    for entry in data["include"]:
        assert "paths" in entry and entry["paths"]


def test_matrix_paths_keep_pytest_ignore_flags() -> None:
    data = json.loads(planner.build_matrix_json(["core_unit"]))
    paths = data["include"][0]["paths"]
    assert "--ignore=tests/core/security" in paths


def test_group_test_dirs_cover_known_backend_test_dirs() -> None:
    """Every stable backend/tests subdir is owned by exactly one group;
    integration/e2e/load-style dirs intentionally stay unmapped (they
    fail-safe to FULL). Guards against group-table drift."""
    tests_root = REPO_ROOT / "backend" / "tests"
    unmapped_ok = {
        "e2e",
        "integration",
        "load",
        "context",
        "context_engine",
        "factories",
        "hitl",
        "models",
        "__pycache__",
    }
    unmapped_files_ok = {"cloud_db_load_test.py", "conftest.py"}
    for entry in tests_root.iterdir():
        if entry.name in unmapped_ok or entry.name in unmapped_files_ok:
            continue
        if entry.is_file():
            continue  # root-level test files map via test_* rule (services)
        owners = [key for key, dirs in planner.GROUP_TEST_DIRS.items() if entry.name in dirs]
        assert len(owners) == 1, f"{entry.name} owned by {owners}"


# ── End-to-end main() with explicit changed files (CI invocation shape) ─────


def _read_output(text: str, key: str) -> str:
    return next(line.split("=", 1)[1] for line in text.splitlines() if line.startswith(f"{key}="))


def test_main_full_mode_outputs(tmp_path, monkeypatch) -> None:
    output_file = tmp_path / "github_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.delenv("CI_COVERAGE_CACHE_ENABLED", raising=False)
    rc = planner.main_inprocess(
        is_main=False,
        force_overall=False,
        changed_files=["backend/services/voice_service.py"],
    )
    assert rc == 0
    text = output_file.read_text(encoding="utf-8")
    assert "run_fast=true" in text
    assert "run_core_unit=true" in text
    assert "run_core_support=true" in text
    assert "run_services=true" in text
    assert "plan_mode=full" in text
    data = json.loads(_read_output(text, "matrix_json"))
    assert len(data["include"]) == 4


def test_main_scoped_mode_outputs(tmp_path, monkeypatch) -> None:
    output_file = tmp_path / "github_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("CI_COVERAGE_CACHE_ENABLED", "true")
    rc = planner.main_inprocess(
        is_main=False,
        force_overall=False,
        changed_files=["backend/tests/agents/test_runner.py"],
    )
    assert rc == 0
    text = output_file.read_text(encoding="utf-8")
    assert "plan_mode=scoped" in text
    assert "run_services=true" in text
    assert "run_fast=false" in text
    data = json.loads(_read_output(text, "matrix_json"))
    assert [entry["group"] for entry in data["include"]] == ["services"]


def test_main_is_main_forces_full(tmp_path, monkeypatch) -> None:
    output_file = tmp_path / "github_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("CI_COVERAGE_CACHE_ENABLED", "true")
    rc = planner.main_inprocess(is_main=True, force_overall=False, changed_files=None)
    assert rc == 0
    text = output_file.read_text(encoding="utf-8")
    assert "plan_mode=full" in text
    assert "reason=main-branch-or-forced-overall" in text


def test_main_exception_failsafe_full(tmp_path, monkeypatch) -> None:
    output_file = tmp_path / "github_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    rc = planner.main_inprocess(
        is_main=False,
        force_overall=False,
        changed_files=["backend/tests/api/test_health.py"],
        boom=True,
    )
    assert rc == 0
    text = output_file.read_text(encoding="utf-8")
    assert "plan_mode=full" in text
    assert "failsafe" in text
