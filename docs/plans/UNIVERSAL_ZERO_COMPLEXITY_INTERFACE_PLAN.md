# SupremeAI: Universal Zero-Complexity Interface — Final Perfect Plan v3

> Status: **Active implementation baseline** (supersedes `implementation_plan(1).md` and `implementation_plan.md`)
> Source: previous corrected plan + codebase verification + 3 gap fixes.

## What changed vs the previous corrected plan (3 gaps closed)

1. **Path correction:** `SkillCatalog.tsx` lives at `frontend/src/pages/user/SkillCatalog.tsx` (not `components/common/`).
2. **Deploy phase added (Phase 7):** CI test-tier registration in `backend/tests/conftest.py`, router registration in `backend/api/routers.py` (`ALL_ROUTERS`), and cloud deploy — per Rule #1 (Zero Local-Machine Dependency).
3. **Governance phase added (Phase 0):** Spec Kit spec via `/speckit.specify` is required before Class-B/C completion (AGENTS.md Operating Rule).

## Confirmed codebase anchors (verified by inspection)

| Anchor | Path | State |
|---|---|---|
| Customer dashboard | `frontend/src/components/customer/UserDashboard.tsx` | exists — currently renders ALL `WORKSPACE_MODULES` that user enabled |
| Integrations | `frontend/src/pages/user/IntegrationsManager.tsx` | exists — tabs: Plugin Marketplace / MCP / Legacy |
| Skill catalog | `frontend/src/pages/user/SkillCatalog.tsx` | exists |
| Capability Registry | `backend/adaptive_engine/capability_registry.py` (`CapabilityRegistry.list(state, tenant_id, ...)`) | solid |
| Governed executor | `backend/adaptive_engine/governed_executor.py` | exists |
| MCP control plane | `infrastructure/mcp-control-plane/src/` | exists |
| Router registry | `backend/api/routers.py` (`ALL_ROUTERS`) | canonical mount path |
| Auth dependency | `core.security.authentication.rbac.get_current_user_token` | canonical |
| No `/connections` API exists yet | — | to be created (this plan) |

## Core Principles (11)

1. Customer dashboard shows only what they use.
2. Progressive disclosure — new things appear only when the user adds them.
3. Admin sees everything **within authorized scope** (Super/Tenant/Workspace admin tiers).
4. Default = safe, minimal, clean.
5. Advanced settings live on the Settings page, not the main dashboard.
6. Same backend, different scoped views.
7. Capability > Module — users see capabilities, not MCP/GitHub internals.
8. Intent > Technical configuration.
9. Authorization before execution.
10. Reuse before creating.
11. One simple UX, modular backend.

## Corrected Architecture (unchanged from previous plan, re-confirmed)

- **One SPA, one auth, one session** — Customer Experience + Admin Experience are components inside the existing route graph. No architectural split.
- **Role change ≠ privilege escalation** — backend returns authorized contexts; user selects only from those.
- **Execution pipeline:** Intent → Capability Discovery → Capability Registry → Authorization → Policy Engine → MCP Control Plane → Governed Executor → Audit/Memory → human-readable result.
- **Customer UX is capability-focused** (`Connection = HOW`, `Capability = WHAT`).
- **Intent-first Add wizard**, API keys are Advanced-only, universal Manage model, "Explain Why" errors.

## Implementation Phases

### Phase 0 — Governance (Spec Kit) ✅ required gate
- `/speckit.specify` for this feature; do not declare Class-B/C complete without it.

### Phase 1 — Backend modular endpoints (this repo, no protocol jargon exposed)
| Endpoint | Purpose |
|---|---|
| `GET /api/v1/connections/my-workspace` | User-scoped capabilities + workspace state (registry-backed, tenant-filtered) |
| `POST /api/v1/connections/detect` | Protocol/provider detection from a pasted URL (no fetch of secrets) |
| `POST /api/v1/connections/register` | Governed registration of a custom tool (creates registry capability, audit-logged) |
| `POST /api/v1/access/set-mode` | Self-service execution-mode change (validated enum, audit-logged, graceful persistence) |

- All registered in `ALL_ROUTERS` (`is_admin: false`), auth via `get_current_user_token`.

### Phase 2 — Frontend type contracts (`frontend/src/types/contracts/`)
- `connection-contract.ts`, `capability-contract.ts`, `execution-mode.ts`, `index.ts` — shared vocabulary for both experiences.

### Phase 3 — Customer experience
- `UserDashboard.tsx` → state-based rendering (new user / some tools / power user).
- Reuse `IntegrationsManager.tsx` + `MCPConnector.tsx`; new `AddNewWizard.tsx` (intent-first).
- Advanced stuff (modes, permissions) only inside `/settings`.

### Phase 4 — Universal Manage model
- `ManageItem.tsx` (name · status · [Use] [Manage]) reused for tools, connections, automations.
- `CapabilityUnavailableExplainer.tsx` — human-readable "why" + [Request Access].

### Phase 5 — Admin scoped view
- Enhance `pages/admin/AdminShell.tsx` (do NOT create a parallel panel).
- Enforce scope tiers server-side; admin UI renders only backend-authorized data.

### Phase 6 — Acid tests (13)
- Customer (1–6), Admin (7–9), Architecture (10–13) — same list as corrected plan.

### Phase 7 — CI/CD + tests (Gap fix)
- New backend tests under `backend/tests/api/routes/` → auto-classified **Important** tier via existing `("api", "routes")` pattern in `backend/tests/conftest.py` (no manual tier edit needed).
- `tsc --noEmit` for frontend contracts.
- Deploy via existing CI pipeline only (Render/Vercel/Cloudflare). No local tunnels.

## Acid test mapping to code
| Test | Verified by |
|---|---|
| Test 1 (new user) | `UserDashboard` state-based rendering (Phase 3) |
| Test 4 (context switch) | `GET /my-workspace` backend-authoritative payload (Phase 1) |
| Test 5 (no self-promotion) | `/access/set-mode` self-only + admin guard (Phase 1) |
| Test 10 (one-URL connect) | `/connections/detect` + `/connections/register` (Phase 1) |
| Test 11 (capability-first) | `my-workspace` returns capabilities, never protocols |
