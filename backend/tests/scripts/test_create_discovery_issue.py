"""Unit tests for scripts/agents/create_discovery_issue.py."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from scripts.agents.create_discovery_issue import (
    create_discovery_issue,
    format_discovery_body,
)


def test_format_discovery_body_contains_parent():
    body = format_discovery_body(
        parent_issue=123,
        description="Found test bug",
        role="coder",
        severity="medium",
    )
    assert "#123" in body
    assert "Found test bug" in body
    assert "coder" in body


def test_create_discovery_issue_dry_run():
    res = create_discovery_issue(
        parent_issue=123,
        title="fix(test): sample discovery",
        body="details",
        role="ci",
        severity="high",
        dry_run=True,
    )
    assert res.is_dry_run is True
    assert res.success is True
    assert "type:discovery" in res.labels
    assert "discovered-by:ci" in res.labels
    assert "high" in res.labels


def test_create_discovery_issue_label_fallback(monkeypatch):
    """Verify that if initial gh issue create fails due to a missing label, it retries with fallback."""
    calls = []

    def mock_run(cmd, **kwargs):
        calls.append(cmd)
        if len(calls) == 1:
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=cmd,
                output="",
                stderr="could not add label: 'type:unknown' not found",
            )
        # Second call succeeds
        mock_res = MagicMock()
        mock_res.stdout = "https://github.com/SaifulHaqueNiloy/supremeai/issues/9988\n"
        return mock_res

    monkeypatch.setattr(subprocess, "run", mock_run)

    res = create_discovery_issue(
        parent_issue=456,
        title="fix(test): fallback test",
        body="details",
        role="coder",
        severity="medium",
        dry_run=False,
    )

    assert len(calls) == 2
    assert res.success is True
    assert res.new_issue_number == 9988
    assert res.labels == ["status:unclaimed", "medium"]
