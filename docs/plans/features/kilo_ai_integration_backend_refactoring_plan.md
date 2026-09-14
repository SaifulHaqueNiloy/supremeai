# Kilo AI Integration and Backend Refactoring Plan

This plan has been updated based on your feedback. We will discard the "Trio Pipeline" concept and instead implement a **Swarm Intelligence / Collective AI Logic**, alongside the backend architecture refactoring.

## User Review Required

> [!WARNING]
> This plan changes the core logic of the VS Code Extension to act as a "Swarm Aggregator". It also involves moving several core backend files into new directories (`services`, `monitoring`, `database`, `middleware`, `errors`) and updating their imports via "shim" files to prevent breaking changes. Please review the proposed changes below.

## Proposed Changes

### 1. VS Code Extension: Swarm Intelligence Integration
Instead of a fixed Trio Pipeline, SupremeAI will dynamically detect all other AI agents on the user's device and integrate them.

**The Logic:**
- **0 Agents detected:** SupremeAI uses its own standalone brain.
- **1 Agent detected:** SupremeAI + That 1 Agent.
- **100 Agents detected:** SupremeAI + Those 100 Agents (Swarm Mode).

#### [MODIFY] [`agentDetector.ts`](file:///F:/supremeai backup/tools/vscode-extension/src/agentDetector.ts)
- **IDE Detection:** Detect which IDE the user is currently running (e.g., VS Code, Cursor, Windsurf, WebStorm, Antigravity).
- **Agent Detection:** Update the detection logic to scan for *all* known AI extensions (Copilot, Tabnine, Cody, Blackbox, Kilo, Cline, etc.).
- Remove the hardcoded "Trio" roles (Writer, Reviewer, Checker).
- Return a full list of detected agents (and the host IDE) to feed into the Swarm engine.

#### [MODIFY] [`CrossAiObserverService.ts`](file:///F:/supremeai backup/tools/vscode-extension/src/services/CrossAiObserverService.ts)
- Copy the enhanced observer service from the Kilo worktree into the main repo.
- Ensure it aggregates data from all detected agents to create the collective intelligence feedback loop.

#### [MODIFY] `package.json` & `extension.ts`
- Remove the `supremeai.trioPipeline` command.
- Add commands for the new Swarm Intelligence features.
- Rebuild the `.vsix` package and install it locally.

---

### 2. Backend Architecture Refactoring
Executing the `backend-arch-refactor` plan to modularize the `backend/core/` directory.

#### [MODIFY] Scripts and Utility cleanup
- Move root level utility scripts (`fix_bare_yields.py`, `fetch_logs.py`, etc.) to the `scripts/` directory.
- Delete unused files (`test.py`, `f`).

#### [NEW] Services Sub-packages
Move core services into `backend/services/` with backward-compatible shim files in `backend/core/`:
- `billing_plans.py` → `backend/services/billing/billing_plans.py`
- `email_service.py` → `backend/services/email/email_service.py`
- `cloud_storage.py` → `backend/services/storage/cloud_storage.py`
- `gcp_firestore.py` → `backend/services/storage/gcp_firestore.py`
- `llm_router.py` → `backend/services/llm/llm_router.py`

#### [NEW] Database, Monitoring, Errors, and Middleware
Organize remaining core components into appropriate domains:
- **Errors:** `error_bus.py`, `error_handler.py`, etc. → `backend/core/errors/`
- **Database:** `db_repository.py`, `pgbouncer_pool.py`, `tenant_db.py` → `backend/database/`
- **Monitoring:** `logging.py`, `metrics.py`, etc. → `backend/monitoring/`
- **Middleware:** `cors_policy.py`, `rate_limiter.py` → `backend/middleware/`

### 3. Clean up `.kilo` Configuration
#### [DELETE] `kilo.jsonc` and `agent-manager.json`
- Safely remove Kilo's internal tracking files that are no longer needed. The worktree will be kept temporarily until the merge is verified.

## Verification Plan

### Automated Tests
- Run backend linting (`ruff check .`) to ensure no import paths are broken.
- Verify `python -c "import backend.core.llm_router"` still works via the shim.

### Manual Verification
- Install the newly built VS Code extension.
- Verify that it correctly detects other AI agents (or the lack thereof) and adjusts its "Swarm Intelligence" mode accordingly.
