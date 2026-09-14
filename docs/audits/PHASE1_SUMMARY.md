# Phase 1 — Agent-System Consolidation: Done This Session

Extract-then-facade, per your standing principle: canonical code moved into `backend/core/agents/`,
old paths kept as thin re-exporting facades so all existing callers (28 files) keep working unchanged.

## New canonical structure
```
backend/core/agents/
├── framework/       # crewai_agents.py, langgraph_agent.py, agent_departments.py,
│                       agent_department.py, task_runner_agent.py (was brain/autonomous_agent.py)
├── live/            # browser_agent.py, computer_agent.py, vision_agent.py, benchmark_agent.py
│                       (was tools/ai_agents/*.py — the previously-documented "real" live system)
└── legacy/          # system_health_agent.py (was agents/autonomous_agent.py)
```

## Facades created (old import paths still work, zero caller changes needed)
- `tools/ai_agents/{browser,computer,vision,benchmark}_agent.py` → re-export from `core.agents.live.*`
- `brain/{crewai_agents,langgraph_agent,agent_departments,agent_department,autonomous_agent}.py` → re-export from `core.agents.framework.*`
- `agents/autonomous_agent.py` → re-export from `core.agents.legacy.system_health_agent`

All 20 files re-checked with `ast.parse` — no syntax errors introduced.

## The two `autonomous_agent.py` files — resolved as agreed, not merged
Confirmed genuinely different classes sharing a filename by accident, so each got its own canonical
name instead of being forced together:
- `agents/autonomous_agent.py` → **`core/agents/legacy/system_health_agent.py`** (system-health monitor: `AutonomousAgent` ABC + `DatabaseHealthAgent`/`MemoryHealthAgent`/`APIHealthAgent`/`SecurityHealthAgent`)
- `brain/autonomous_agent.py` → **`core/agents/framework/task_runner_agent.py`** (task-execution step-runner: `AutonomousAgent` + `StepResult`)

Both old files now carry a comment explaining they are NOT the same class, to stop this confusion recurring.

## ⚠️ New collision found while moving files (not previously flagged) — needs your decision
`brain/agent_department.py` (singular) and `brain/agent_departments.py` (plural) **both define a class
named `AgentDepartment`** — genuinely different classes, not a typo duplicate:
- `agent_departments.py`'s `AgentDepartment` — one class, orchestration-focused (not yet deep-read)
- `agent_department.py`'s `AgentDepartment` — sits alongside `CodingAgent`/`ReviewAgent`/`QAAgent` in the same file

I did **not** guess which should win the name. The `agent_department.py` (singular) facade re-exports
its version as `AgentDepartmentLegacy` to avoid silently shadowing the other one — this keeps both
usable but is a stopgap, not a real fix. **Before Phase 2, this needs a real read of both classes**
to decide: rename one properly, or merge if they turn out to overlap.

## Not done in this session (scoped out, flagged for later)
- The 50 legacy files under `backend/agents/` (subdirs: devops/domain/evolution/governance/ide/infrastructure/monitoring)
  were **not** individually repointed to `core/agents/framework/` base classes — that's a much larger,
  file-by-file job the plan called "legacy/" migration. This session only handled the structural move +
  the two named collisions your review flagged.
- No test run performed in this sandbox (no way to install the full poetry env here) — **please run
  `pytest backend/tests/` locally or in CI before merging** to catch anything the static check missed.
- Nothing pushed — no GitHub write access this session. Delivered as a tarball to apply locally.

## To apply
Extract `phase1_agent_consolidation.tar.gz` over your repo root (paths are relative to repo root,
`backend/...`), review the diff, then run your test suite before committing.
