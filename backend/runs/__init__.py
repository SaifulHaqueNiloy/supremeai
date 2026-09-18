"""Canonical Run fabric (M1 — ecosystem Ph1).

One execution contract: Mission / Agent / Tool / MCP / Browser / Code work is
observable as a **Run** — an execution boundary with a strict lifecycle,
retry classification, budgets, artifacts and an ordered audit event stream.

Doctrine (roadmap M1): *extend, not replace*. The Run tables anchor to the
existing Mission core (``missions/models.py``) and future bridges map
``automation_executions`` / ``execution_logs`` evidence and ``pending_tasks``
approvals onto Runs — no duplicate execution subsystem.

Module map:

- :mod:`runs.state_machine` — pure-stdlib lifecycle state machine (no DB
  coupling, importable anywhere, mirrors ``missions/state_machine.py``).
- :mod:`runs.retry` — retry classification enum + retryability rules.
- :mod:`runs.models` — SQLAlchemy ``Run`` / ``RunEvent`` models on the
  canonical ``models.base.Base``.
"""

from __future__ import annotations

from runs.models import Run, RunEvent
from runs.retry import RetryClass, is_retryable
from runs.state_machine import (
    BLOCKED,
    CANCELLED,
    DEGRADED,
    FAILED,
    FINALIZED,
    PLANNED,
    POLICY_CHECKED,
    REQUESTED,
    RETRYING,
    RUNNING,
    STATES,
    SUCCEEDED,
    TERMINAL_STATES,
    WAITING_APPROVAL,
    IllegalTransition,
    assert_transition,
    is_terminal,
)
from runs.stategraph import (
    END,
    START,
    CompiledGraph,
    NodeExecutionError,
    RecursionLimitExceeded,
    StateGraph,
    StateGraphError,
)

__all__ = [
    "Run",
    "RunEvent",
    "RetryClass",
    "is_retryable",
    # state names
    "REQUESTED",
    "POLICY_CHECKED",
    "PLANNED",
    "RUNNING",
    "WAITING_APPROVAL",
    "RETRYING",
    "DEGRADED",
    "BLOCKED",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
    "FINALIZED",
    "STATES",
    "TERMINAL_STATES",
    "IllegalTransition",
    "assert_transition",
    "is_terminal",
    # stategraph
    "StateGraph",
    "CompiledGraph",
    "StateGraphError",
    "RecursionLimitExceeded",
    "NodeExecutionError",
    "END",
    "START",
]
