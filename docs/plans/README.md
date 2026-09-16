# SupremeAI Living Architecture Plans Catalog

**Status:** `docs/plans/README.md` — Navigation layer  
**Source of Truth:** `docs/plans/implementation_plan.md` — Execution order

---

## 📜 Governance Layer

| Document | Purpose |
|----------|---------|
| [Plan Lifecycle Policy](./PLAN_LIFECYCLE_POLICY.md) | Status rules (proposed/active/in_progress/complete/superseded) |
| [Plan-to-Code Traceability Matrix](./PLAN_TO_CODE_TRACEABILITY_MATRIX.md) | Evidence-driven verification |
| [PENDING_APPROVALS.md](./PENDING_APPROVALS.md) | High-risk tasks awaiting admin sign-off |
| [implementation_plan.md](./implementation_plan.md) | Tactical priorities & reconciliations |

---

## 🗺️ PLAN STATUS DASHBOARD

### ACTIVE ARCHITECTURE

| Plan | Status | Path |
|------|--------|------|
| **Browser Automation** | active | `architecture/browser_automation.md` ⭐ NEW |
| **Master Plan** | active | `architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md` |
| **Unified FastMCP Control Tower** | active | `architecture/unified_fastmcp_control_tower_multitenant_master_plan_bn.md` ⭐ |
| **Control Plane** | active | `architecture/distributed_infrastructure_central_control_plane_plan.md` |

### IN PROGRESS

| Plan | Status | Progress |
|------|--------|----------|
| AI Model Comparative Matrix | in_progress | Language coverage |
| Verification Engine | in_progress | L1-L3 testing |
| Codebase Modularization | in_progress | 3/5 modules split |

### PROPOSED / REFERENCE

| Plan | Status | Next Review |
|------|--------|-------------|
| [Antihacking Security Framework](features/antihacking_security_defense_framework.md) | proposed | Security Circle |
| [Living Autonomous Intelligence](architecture/living_autonomous_intelligence_synthesis.md) | proposed | AI Evolution |
| Q1 2026 Foundation Execution | proposed | Q1 Sprint |

---

## 📁 SUBFOLDER INDEX

### Architecture (`architecture/`) — System-wide blueprints

```
├── SUPREMEAI_MASTER_PLAN_CANONICAL.md ← Master plan (supersedes UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md)
├── browser_automation.md               ← Canonical browser plan ⭐
├── distributed_infrastructure_central_control_plane_plan.md
├── dynamic_ai_architecture_v5_zero_downtime.md
├── federated_capability_circles_topology.md
└── (13+ other components)
```
[View all architecture plans](architecture/README.md)

### Features (`features/`) — Capability specifications

```
├── Plan_01-24_Dynamic_AI_Agent_System.md
├── autonomous_capability_creation_and_task_execution_plan.md
├── browser_related.md
├── code-related plans
└── (50+ active/canonical plans)
```
[View all feature plans](features/README.md)

### Infrastructure (`infrastructure/`) — Operational foundations

```
├── SUPREMEAI_CONFIGURATION_CONTROL_REGISTRY_V2.md
├── free_tier_federation_master_plan_v4.md
├── supabase_database_schema_and_connection_management_plan.md
└── (10+ operational plans)
```
[View all infrastructure plans](infrastructure/README.md)

### Design (`design/`) — UI/UX experiences

```
├── dashboard_design_mockups.md
├── admin_dashboard_plan.md
├── ux_ui_best_practices_and_interaction_guide.md
└── (12 UI/UX plans)
```
[View all design plans](design/README.md)

### Phases (`phases/`) — Execution milestones

```
├── phase1_foundation.md → phase4_optimization.md ← Current phases
├── project_milestones_and_completion_tracker.md
├── systemic_risk_assessment_and_mitigation.md
└── (19 milestone/risk plans)
```
[View all phase plans](phases/README.md)

---

## 🔄 STATUS-BASED VIEW (NOT PHYSICAL SEPARATION)

Status is tracked **via document headers**, not folder segregation:

```yaml
# In each plan file:
status: active | proposed | in_progress | complete | superseded
```

This enables:
- Evolutionary continuity (no file moves)
- Single canonical location per subject
- History preserved via in-document evolution

---

## 📦 ARCHIVE POLICY

**Superseded versions** are moved to:
- `docs/archive/plans/features/legacy_plan_series_2026_05/` — Legacy Plan 12-15, 17-21
- `docs/archive/plans/` redirect stubs — Versioned files (v2, FINAL, etc.)

**Never deleted** — lineage preserved per AGENTS.md constitutional protection.

---

## 🎯 PLAN NAMING CONVENTION

**One subject = One canonical plan**

✅ **Preferred:**
```
browser_automation.md
external_agent_orchestration.md
configuration_registry.md
```

❌ **Avoid:**
```
browser-plan-v1.md
browser-plan-v2.md
BROWSER_AUTOMATION_FINAL.md
NEW-Browser-Plan.md
```