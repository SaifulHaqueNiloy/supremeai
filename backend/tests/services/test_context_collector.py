"""Tests for services/ingestion/context_collector.py — the Developer Context
Auto-Ingestor.

Covers the git-probing helpers (branch/status/commits/diff), the snapshot
aggregation with memory-tree ingestion, and the periodic collection loop.

Honesty boundaries: REAL git repositories are created in tmp_path and probed
with the real git binary for every happy path (branch name, porcelain status
parsing, oneline log, real diff text). The REAL HierarchicalMemoryTree and
REAL TokenJuice are used, wrapped in recording delegates so call arguments
are asserted without losing real behavior. subprocess.run is monkeypatched
ONLY for error paths (nonzero returncode, timeouts, raised exceptions).
"""

from __future__ import annotations

import asyncio
import pathlib
import subprocess
import time
from types import SimpleNamespace

import backend.services.ingestion.context_collector as ccm
import pytest
from backend.engine.compression.token_juice import TokenJuice
from backend.memory.hierarchical_tree import HierarchicalMemoryTree
from backend.services.ingestion.context_collector import (
    DeveloperContextCollector,
    WorkspaceSnapshot,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

GIT_IDENTITY = ["-c", "user.email=test@example.com", "-c", "user.name=Test"]


def _git(repo, *args):
    return subprocess.run(
        ["git", *GIT_IDENTITY, *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )


def init_repo(tmp_path) -> str:
    """Create a real git repo on branch 'main' with two commits; return root."""
    repo = tmp_path / "workspace"
    repo.mkdir()
    assert _git(repo, "init").returncode == 0
    assert _git(repo, "symbolic-ref", "HEAD", "refs/heads/main").returncode == 0
    (repo / "tracked.txt").write_text("line one\n")
    assert _git(repo, "add", ".").returncode == 0
    assert _git(repo, "commit", "-m", "first commit").returncode == 0
    (repo / "tracked.txt").write_text("line one\nline two\n")
    assert _git(repo, "add", ".").returncode == 0
    assert _git(repo, "commit", "-m", "second commit").returncode == 0
    return str(repo)


def make_modified_files(repo_root: str, count: int) -> None:
    """Commit `count` files, then modify them so porcelain reports ' M'."""
    repo = pathlib.Path(repo_root)
    for i in range(count):
        (repo / f"mod_{i:02d}.py").write_text(f"original {i}\n")
    assert _git(repo, "add", ".").returncode == 0
    assert _git(repo, "commit", "-m", "add mod files").returncode == 0
    for i in range(count):
        (repo / f"mod_{i:02d}.py").write_text(f"change {i}\n")


class RecordingTree:
    """Delegates to a REAL HierarchicalMemoryTree while recording calls."""

    def __init__(self):
        self.real = HierarchicalMemoryTree(root_title="SupremeAI Live Context")
        self.branch_calls: list[dict] = []
        self.leaf_calls: list[dict] = []

    def add_branch(self, **kwargs):
        self.branch_calls.append(kwargs)
        return self.real.add_branch(**kwargs)

    def add_leaf(self, **kwargs):
        self.leaf_calls.append(kwargs)
        return self.real.add_leaf(**kwargs)


class RecordingCompressor:
    """Delegates to a REAL TokenJuice while recording calls."""

    def __init__(self):
        self.real = TokenJuice()
        self.calls: list[dict] = []

    def compress(self, content, content_type=None):
        self.calls.append({"content": content, "content_type": content_type})
        return self.real.compress(content, content_type=content_type)


def fake_run(monkeypatch, *, stdout="", returncode=0, raise_exc=None, record=None):
    def _run(args, **kwargs):
        if record is not None:
            record.append({"args": args, "kwargs": kwargs})
        if raise_exc is not None:
            raise raise_exc
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(ccm.subprocess, "run", _run)
    return _run


# ─────────────────────────────────────────────────────────────────────────────
# WorkspaceSnapshot dataclass
# ─────────────────────────────────────────────────────────────────────────────


class TestWorkspaceSnapshot:
    def test_defaults(self):
        before = time.time()
        snap = WorkspaceSnapshot()
        after = time.time()
        assert before <= snap.timestamp <= after
        assert snap.active_branch == "main"
        assert snap.modified_files == []
        assert snap.untracked_files == []
        assert snap.recent_commits == []
        assert snap.compressed_diff_summary == ""
        assert snap.total_uncommitted_changes == 0

    def test_explicit_fields(self):
        snap = WorkspaceSnapshot(
            active_branch="feature/x",
            modified_files=["a"],
            untracked_files=["b"],
            total_uncommitted_changes=2,
        )
        assert snap.active_branch == "feature/x"
        assert snap.total_uncommitted_changes == 2


# ─────────────────────────────────────────────────────────────────────────────
# __init__ wiring
# ─────────────────────────────────────────────────────────────────────────────


class TestInit:
    def test_explicit_workspace_root(self, tmp_path):
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert c.workspace_root == str(tmp_path)
        assert c._is_running is False
        assert c._last_snapshot is None

    def test_default_workspace_root_is_cwd(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        c = DeveloperContextCollector()
        assert c.workspace_root == str(tmp_path)

    def test_default_components_are_real(self, tmp_path):
        # Type-NAME checks: the module imports the top-level `memory.` /
        # `engine.` aliases which under pytest are distinct class objects
        # from the `backend.`-prefixed aliases (module-aliasing gotcha).
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert type(c.memory_tree).__name__ == "HierarchicalMemoryTree"
        assert type(c.compressor).__name__ == "TokenJuice"

    def test_custom_components_are_kept(self, tmp_path):
        tree = RecordingTree()
        comp = RecordingCompressor()
        c = DeveloperContextCollector(
            workspace_root=str(tmp_path), memory_tree=tree, compressor=comp
        )
        assert c.memory_tree is tree
        assert c.compressor is comp


# ─────────────────────────────────────────────────────────────────────────────
# Git helpers — REAL repo happy paths
# ─────────────────────────────────────────────────────────────────────────────


class TestGitHelpersReal:
    def test_get_git_branch_real_repo(self, tmp_path):
        repo = init_repo(tmp_path)
        c = DeveloperContextCollector(workspace_root=repo)
        assert c.get_git_branch() == "main"

    def test_get_git_status_real_repo(self, tmp_path):
        repo = init_repo(tmp_path)
        (tmp_path / "workspace" / "tracked.txt").write_text("changed\n")
        (tmp_path / "workspace" / "new_thing.txt").write_text("untracked\n")
        c = DeveloperContextCollector(workspace_root=repo)
        modified, untracked = c.get_git_status()
        assert "tracked.txt" in modified
        assert "new_thing.txt" in untracked

    def test_get_recent_commits_real_repo(self, tmp_path):
        repo = init_repo(tmp_path)
        c = DeveloperContextCollector(workspace_root=repo)
        commits = c.get_recent_commits(count=2)
        assert len(commits) == 2
        assert any("second commit" in line for line in commits)
        assert any("first commit" in line for line in commits)

    def test_get_git_diff_summary_real_repo(self, tmp_path):
        repo = init_repo(tmp_path)
        (tmp_path / "workspace" / "tracked.txt").write_text("brand new content\n")
        c = DeveloperContextCollector(workspace_root=repo)
        summary = c.get_git_diff_summary()
        assert isinstance(summary, str)
        assert summary != ""


# ─────────────────────────────────────────────────────────────────────────────
# Git helpers — error and parsing paths (subprocess boundary)
# ─────────────────────────────────────────────────────────────────────────────


class TestGitHelpersErrors:
    def test_branch_nonzero_returncode_is_unknown(self, monkeypatch, tmp_path):
        fake_run(monkeypatch, returncode=1)
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert c.get_git_branch() == "unknown"

    def test_branch_exception_is_unknown(self, monkeypatch, tmp_path):
        fake_run(monkeypatch, raise_exc=subprocess.TimeoutExpired(cmd="git", timeout=3))
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert c.get_git_branch() == "unknown"

    def test_branch_invocation_contract(self, monkeypatch, tmp_path):
        record: list[dict] = []
        fake_run(monkeypatch, stdout="feature/big\n", record=record)
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert c.get_git_branch() == "feature/big"
        assert record[0]["args"] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        assert record[0]["kwargs"]["timeout"] == 3
        assert record[0]["kwargs"]["cwd"] == str(tmp_path)
        assert record[0]["kwargs"]["text"] is True

    def test_status_exception_yields_empty_lists(self, monkeypatch, tmp_path):
        fake_run(monkeypatch, raise_exc=subprocess.TimeoutExpired(cmd="git", timeout=3))
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert c.get_git_status() == ([], [])

    def test_status_nonzero_returncode_yields_empty_lists(self, monkeypatch, tmp_path):
        fake_run(monkeypatch, returncode=128)
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert c.get_git_status() == ([], [])

    def test_status_parsing_matrix(self, monkeypatch, tmp_path):
        fake_run(
            monkeypatch,
            stdout=(
                " M staged_space.py\n"
                "M  staged_only.py\n"
                "?? untracked.py\n"
                "MM both.py\n"
                "R  old_name.py -> new_name.py\n"
                "A  added.py\n"
            ),
        )
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        modified, untracked = c.get_git_status()
        assert modified == [
            "staged_space.py",
            "staged_only.py",
            "both.py",
            "old_name.py -> new_name.py",
            "added.py",
        ]
        assert untracked == ["untracked.py"]

    def test_status_invocation_contract(self, monkeypatch, tmp_path):
        record: list[dict] = []
        fake_run(monkeypatch, stdout="", record=record)
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        c.get_git_status()
        assert record[0]["args"] == ["git", "status", "--porcelain"]
        assert record[0]["kwargs"]["timeout"] == 3

    def test_commits_exception_yields_empty(self, monkeypatch, tmp_path):
        fake_run(monkeypatch, raise_exc=OSError("git missing"))
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert c.get_recent_commits() == []

    def test_commits_nonzero_yields_empty_and_count_used(self, monkeypatch, tmp_path):
        record: list[dict] = []
        fake_run(monkeypatch, returncode=128, record=record)
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert c.get_recent_commits(count=7) == []
        assert record[0]["args"] == ["git", "log", "-n7", "--oneline"]

    def test_commits_blank_lines_skipped(self, monkeypatch, tmp_path):
        fake_run(monkeypatch, stdout="abc123 fix\n\n\ndef456 feat\n")
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert c.get_recent_commits() == ["abc123 fix", "def456 feat"]

    def test_diff_nonzero_or_empty_is_empty_string(self, monkeypatch, tmp_path):
        fake_run(monkeypatch, returncode=1, stdout="ignored")
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        assert c.get_git_diff_summary() == ""
        fake_run(monkeypatch, returncode=0, stdout="")
        assert c.get_git_diff_summary() == ""

    def test_diff_compressor_called_with_git_diff_type(self, monkeypatch, tmp_path):
        comp = RecordingCompressor()
        fake_run(monkeypatch, stdout="diff --git a/x b/x\n")
        c = DeveloperContextCollector(workspace_root=str(tmp_path), compressor=comp)
        result = c.get_git_diff_summary()
        assert comp.calls[0]["content_type"] == "git_diff"
        assert comp.calls[0]["content"] == "diff --git a/x b/x\n"
        assert isinstance(result, str)

    def test_diff_compressor_crash_returns_empty(self, monkeypatch, tmp_path):
        class ExplodingCompressor:
            def compress(self, content, content_type=None):
                raise RuntimeError("compression exploded")

        fake_run(monkeypatch, stdout="diff --git a/x b/x\n")
        c = DeveloperContextCollector(
            workspace_root=str(tmp_path), compressor=ExplodingCompressor()
        )
        assert c.get_git_diff_summary() == ""

    def test_diff_invocation_contract(self, monkeypatch, tmp_path):
        record: list[dict] = []
        fake_run(monkeypatch, stdout="", record=record)
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        c.get_git_diff_summary()
        assert record[0]["args"] == ["git", "diff", "HEAD"]
        assert record[0]["kwargs"]["timeout"] == 5


# ─────────────────────────────────────────────────────────────────────────────
# capture_snapshot — aggregation + memory-tree ingestion (REAL tree)
# ─────────────────────────────────────────────────────────────────────────────


class TestCaptureSnapshot:
    def test_full_snapshot_fields_from_real_repo(self, tmp_path):
        repo = init_repo(tmp_path)
        (tmp_path / "workspace" / "tracked.txt").write_text("dirty\n")
        (tmp_path / "workspace" / "fresh.txt").write_text("new\n")
        tree = RecordingTree()
        c = DeveloperContextCollector(workspace_root=repo, memory_tree=tree)
        snap = c.capture_snapshot()

        assert snap.active_branch == "main"
        assert "tracked.txt" in snap.modified_files
        assert "fresh.txt" in snap.untracked_files
        assert snap.total_uncommitted_changes == 2
        assert len(snap.recent_commits) == 2
        assert snap.compressed_diff_summary != ""
        assert c._last_snapshot is snap  # stored identity

    def test_tree_receives_branch_and_leaf_with_dev_category(self, tmp_path):
        repo = init_repo(tmp_path)
        tree = RecordingTree()
        c = DeveloperContextCollector(workspace_root=repo, memory_tree=tree)
        c.capture_snapshot()

        assert len(tree.branch_calls) == 1
        assert tree.branch_calls[0]["title"] == "Workspace Snapshot (main)"
        assert tree.branch_calls[0]["category"] == "dev"
        assert tree.branch_calls[0]["tags"] == ["git", "workspace", "live_context"]

        assert len(tree.leaf_calls) == 1
        leaf = tree.leaf_calls[0]
        assert leaf["title"].startswith("Active State @ ")
        assert leaf["category"] == "dev"
        assert leaf["tags"] == ["workspace_snapshot"]
        assert leaf["branch_id"] is not None

    def test_leaf_content_shape_and_truncation(self, tmp_path):
        repo = init_repo(tmp_path)
        # 12 files committed then modified → porcelain ' M' → modified list;
        # only first 10 appear in the leaf content, count shows 12.
        make_modified_files(repo, 12)
        tree = RecordingTree()
        c = DeveloperContextCollector(workspace_root=repo, memory_tree=tree)
        snap = c.capture_snapshot()

        assert snap.total_uncommitted_changes == 12
        content = tree.leaf_calls[0]["content"]
        assert content.startswith("Branch: main\n")
        assert "Modified Files (12): " in content
        assert "mod_09.py" in content  # 10th modified file (0-indexed 9)
        assert "mod_10.py" not in content  # truncated at 10
        assert "Recent Commits: " in content
        # diff preview is the first 400 chars of the compressed summary
        assert content.endswith(snap.compressed_diff_summary[:400])

    def test_snapshot_without_git_repo_degrades(self, tmp_path):
        # A directory that is not a git repo: every helper returns its
        # fallback and the snapshot still ingests (production resilience).
        empty = tmp_path / "plain"
        empty.mkdir()
        tree = RecordingTree()
        c = DeveloperContextCollector(workspace_root=str(empty), memory_tree=tree)
        snap = c.capture_snapshot()
        assert snap.active_branch == "unknown"
        assert snap.modified_files == []
        assert snap.untracked_files == []
        assert snap.recent_commits == []
        assert snap.compressed_diff_summary == ""
        assert snap.total_uncommitted_changes == 0
        assert tree.branch_calls[0]["title"] == "Workspace Snapshot (unknown)"

    def test_repeated_capture_updates_last_snapshot(self, tmp_path):
        repo = init_repo(tmp_path)
        c = DeveloperContextCollector(workspace_root=repo)
        first = c.capture_snapshot()
        (tmp_path / "workspace" / "another.txt").write_text("x\n")
        second = c.capture_snapshot()
        assert first is not second
        assert c._last_snapshot is second
        assert second.total_uncommitted_changes == first.total_uncommitted_changes + 1


# ─────────────────────────────────────────────────────────────────────────────
# Periodic loop
# ─────────────────────────────────────────────────────────────────────────────


class TestPeriodicLoop:
    async def test_loop_captures_and_stops_cleanly(self, tmp_path):
        repo = init_repo(tmp_path)
        c = DeveloperContextCollector(workspace_root=repo)
        task = asyncio.create_task(c.run_periodic_collector(interval_seconds=0.01))
        await asyncio.sleep(0.06)
        c.stop()
        await asyncio.wait_for(task, timeout=2.0)  # loop exited
        assert c._is_running is False
        assert c._last_snapshot is not None  # at least one capture happened

    async def test_loop_survives_capture_errors(self, monkeypatch, tmp_path):
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        calls = {"n": 0}

        def flaky_capture():
            calls["n"] += 1
            if calls["n"] <= 2:
                raise RuntimeError("transient snapshot failure")
            return WorkspaceSnapshot()

        async def runner():
            task = asyncio.create_task(c.run_periodic_collector(interval_seconds=0.01))
            await asyncio.sleep(0.08)
            c.stop()
            await asyncio.wait_for(task, timeout=2.0)

        monkeypatch.setattr(c, "capture_snapshot", flaky_capture)
        await runner()  # must not raise despite the two failures
        assert calls["n"] >= 3  # loop kept ticking past the failures

    def test_stop_sets_flag(self, tmp_path):
        c = DeveloperContextCollector(workspace_root=str(tmp_path))
        c._is_running = True
        c.stop()
        assert c._is_running is False
