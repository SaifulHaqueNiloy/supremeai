"""SupremeAI Mission Orchestration core (Task 7-c).

Implements the backend foundation of
``docs/plans/design/mission_orchestration_plan.md`` in a codebase-accurate way:

- A ``Mission`` links a GOAL (the plan's "Requirement") to a STRATEGY (the
  plan's "Exploitation Technique") and tracks ordered PHASES through a strict
  state machine.
- Every state change writes an immutable ``MissionTraceEvent`` (the plan's
  "Mission Trace" / audit linkage) and emits a structured log line carrying
  the ``mission_id`` for forensic accountability.
- A failure-repair loop rotates the mission's strategy across
  ``strategy_options`` (the plan's "Autonomous Improvement" self-correction),
  bounded by ``MAX_REPAIRS``.

Deviations from the plan document (deliberate, documented):
- Persistence is SQLAlchemy on the existing Supabase PostgreSQL database
  (``models.base.Base`` metadata — the same DeclarativeBase every other model
  and the Alembic environment use), NOT Firestore ``active_missions/``: the
  codebase has no Firestore runtime persistence path.
- Agent assignment is a pluggable hook (``MissionService(assigner=...)``); the
  default stub labels the mission ``auto-agent-v1`` and performs NO real LLM
  call. The plan's dashboards (RequirementsDashboard / ExploitationTechnique /
  PhasesOverview / NeuralTerminal) do not exist in this codebase, so the
  semantics are preserved in the generic core instead.
"""


from missions.models import Mission, MissionTraceEvent
from missions.service import MissionNotFound, MissionService
from missions.state_machine import (
    STATES,
    IllegalTransition,
    assert_transition,
)

__all__ = [
    "Mission",
    "MissionNotFound",
    "MissionService",
    "MissionTraceEvent",
    "STATES",
    "IllegalTransition",
    "assert_transition",
]
