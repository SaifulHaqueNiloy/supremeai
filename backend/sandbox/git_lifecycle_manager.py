"""
Isolated Git Lifecycle Manager (Gitea & CI/CD Sandbox Pattern).
Enables autonomous agents to create ephemeral sandbox branches, stage diffs,
run automated verification tests, and safely merge or rollback changes.
"""

from __future__ import annotations

import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from loguru import logger


@dataclass
class GitTaskSession:
    session_id: str
    branch_name: str
    original_branch: str
    repo_path: str
    is_active: bool = True


class GitLifecycleManager:
    """
    Manages isolated Git operations for SupremeAI autonomous coding agents.
    Prevents directly polluting or breaking the main repository branch.
    """

    def __init__(self, repo_path: str | Path | None = None):
        self.repo_path = str(repo_path or os.getcwd())

    def _run_git(self, args: list[str]) -> tuple[int, str, str]:
        try:
            res = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as exc:
            return 1, "", str(exc)

    def get_current_branch(self) -> str:
        code, out, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        return out if code == 0 else "main"

    def create_sandbox_branch(self, prefix: str = "supremeai/task") -> GitTaskSession:
        original = self.get_current_branch()
        session_id = uuid.uuid4().hex[:8]
        branch_name = f"{prefix}-{session_id}"

        logger.info(f"Creating isolated Git sandbox branch: {branch_name} (from {original})")
        # In mock or restricted environments without git repo initialized, fallback gracefully
        code, _, err = self._run_git(["checkout", "-b", branch_name])
        if code != 0:
            logger.warning(f"Git checkout -b failed (continuing in simulated session): {err}")

        return GitTaskSession(
            session_id=session_id,
            branch_name=branch_name,
            original_branch=original,
            repo_path=self.repo_path,
        )

    def stage_and_commit(self, session: GitTaskSession, commit_message: str) -> dict[str, Any]:
        self._run_git(["add", "."])
        code, out, err = self._run_git(["commit", "-m", f"[SupremeAI Agent] {commit_message}"])
        return {
            "success": code == 0 or "nothing to commit" in out or "nothing to commit" in err,
            "stdout": out,
            "stderr": err,
        }

    def get_staged_diff(self) -> str:
        _, out, _ = self._run_git(["diff", "HEAD~1"])
        return out

    def rollback_sandbox(self, session: GitTaskSession) -> bool:
        """
        Discards sandbox branch changes and returns safely to original branch.
        """
        logger.info(f"Rolling back sandbox branch: {session.branch_name} -> {session.original_branch}")
        self._run_git(["reset", "--hard", "HEAD"])
        self._run_git(["checkout", session.original_branch])
        self._run_git(["branch", "-D", session.branch_name])
        session.is_active = False
        return True

    def merge_sandbox_to_parent(self, session: GitTaskSession) -> dict[str, Any]:
        """
        Safely switches to parent branch and merges the sandbox changes.
        """
        logger.info(f"Merging validated sandbox branch [{session.branch_name}] into [{session.original_branch}]")
        code, _, err = self._run_git(["checkout", session.original_branch])
        if code != 0:
            return {"success": False, "error": f"Failed checkout to {session.original_branch}: {err}"}

        code_m, out_m, err_m = self._run_git(["merge", "--no-ff", session.branch_name, "-m", f"Merge verified task {session.session_id}"])
        # Clean up temporary branch
        self._run_git(["branch", "-d", session.branch_name])
        session.is_active = False

        return {
            "success": code_m == 0,
            "stdout": out_m,
            "stderr": err_m,
        }
