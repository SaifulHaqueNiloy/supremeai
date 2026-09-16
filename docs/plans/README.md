---
id: plans-navigation-catalog
subject: "SupremeAI Living Architecture Plans Catalog"
document_role: architecture
planning_authority: Architecture Governance / Planning Circle
canonical: true
status: active
evidence_state: partial
disposition: retain
last_verified: 2026-09-17
supersedes: []
superseded_by: []
---

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

---

## 📊 Status-Based Plan Catalog (generated)

Scanned 157 documents under /home/z/supremeai-work/docs/plans
  errors:   0
  warnings: 134
  competing plan sets: 1
  first warnings:
  [WARNING] missing-frontmatter    plans/architecture/README.md: no YAML frontmatter — registry cannot classify this plan (inferred family: dynamic-configuration)
  [WARNING] missing-frontmatter    plans/architecture/ai_model_comparative_matrix_bangla.md: no YAML frontmatter — registry cannot classify this plan (inferred family: intelligence-evolution)
  [WARNING] missing-frontmatter    plans/architecture/autonomous_product_verification_engine.md: no YAML frontmatter — registry cannot classify this plan (inferred family: browser-automation)
  [WARNING] missing-frontmatter    plans/architecture/codebase_aligned_master_roadmap.md: no YAML frontmatter — registry cannot classify this plan (inferred family: production-readiness)
  [WARNING] missing-frontmatter    plans/architecture/crown_jewel_complete_system_integration_blueprint.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unified-architecture)
<!-- BEGIN GENERATED PLAN CATALOG (scripts/governance/lint_plans.py --readme; do not hand-edit between markers) -->

### 🟢 ACTIVE (27)

| Plan | Role | Authority | Family |
|---|---|---|---|
| [`CANONICAL_PLANNING_RECONCILIATION_AND_GUARDRAILS_PLAN`](./CANONICAL_PLANNING_RECONCILIATION_AND_GUARDRAILS_PLAN.md) | policy | Architecture Governance / Planning Circle | unclassified |
| [`CI_PIPELINE_CONSOLIDATION_PLAN_2026-09-15`](./CI_PIPELINE_CONSOLIDATION_PLAN_2026-09-15.md) | implementation | DevEx / CI Circle | ci-cd-pipeline |
| [`HEAD_OF_PLANNING_STRATEGIC_LEVERAGE_2026-09-16`](./HEAD_OF_PLANNING_STRATEGIC_LEVERAGE_2026-09-16.md) | roadmap | C1 (Code & Quality) and cross-circle (C2/C3/C5/C6) per lever | execution-phases |
| [`PENDING_APPROVALS`](./PENDING_APPROVALS.md) | audit | Architecture Governance / Planning Circle | unclassified |
| [`PLAN_001_ANTHROPIC_PROMPT_CACHING_2026-09-16`](./PLAN_001_ANTHROPIC_PROMPT_CACHING_2026-09-16.md) | implementation | C5 (Execution — LLM Gateway) | control-tower-mcp |
| [`PLAN_LIFECYCLE_POLICY`](./PLAN_LIFECYCLE_POLICY.md) | policy | Architecture Governance / Planning Circle | unclassified |
| [`PLAN_TO_CODE_TRACEABILITY_MATRIX`](./PLAN_TO_CODE_TRACEABILITY_MATRIX.md) | audit | Architecture Governance / Planning Circle | unclassified |
| [`PR_GUARDIAN_ANALYSIS_PLAN`](./PR_GUARDIAN_ANALYSIS_PLAN.md) | audit | DevEx / CI Circle | control-tower-mcp |
| [`README`](./README.md) | architecture | Architecture Governance / Planning Circle | control-tower-mcp |
| [`ROADMAP_ECOSYSTEM_ARCHITECTURE_BN`](./ROADMAP_ECOSYSTEM_ARCHITECTURE_BN.md) | roadmap | Architecture Circle | execution-phases |
| [`UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN`](./UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md) | architecture | Architecture Circle | unified-architecture |
| [`UNIFIED_NEXT_ROADMAP_2026-09-15`](./UNIFIED_NEXT_ROADMAP_2026-09-15.md) | roadmap | Planning Circle | unified-architecture |
| [`SUPREMEAI_MASTER_PLAN_CANONICAL`](./architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md) | architecture | Architecture Circle | unified-architecture |
| [`browser_automation`](./architecture/browser_automation.md) | architecture | CircleName.BROWSER | browser-automation |
| [`dynamic_configuration_zero_hardcode_roadmap`](./architecture/dynamic_configuration_zero_hardcode_roadmap.md) | architecture | Architecture Circle | dynamic-configuration |
| [`vendor_independent_integration_architecture_plan`](./architecture/vendor_independent_integration_architecture_plan.md) | architecture | Architecture Circle | execution-phases |
| [`free_tier_512mb_memory_pressure_remediation_plan`](./features/free_tier_512mb_memory_pressure_remediation_plan.md) | implementation | Infrastructure Circle | free-tier-federation |
| [`free_tier_federation_master_plan_v4.1_missing_services_analysis`](./features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md) | audit | Infrastructure Circle | free-tier-federation |
| [`free_tier_production_upgrade_plan_v2`](./features/free_tier_production_upgrade_plan_v2.md) | implementation | Infrastructure Circle | free-tier-federation |
| [`free_tier_scaling_constitution_and_compliance_policy`](./features/free_tier_scaling_constitution_and_compliance_policy.md) | policy | Infrastructure Circle | execution-phases |
| [`production_hardening_and_p1_p2_roadmap_2026_09_11`](./features/production_hardening_and_p1_p2_roadmap_2026_09_11.md) | roadmap | Architecture Circle | control-tower-mcp |
| [`production_readiness_final_stretch_plan_bn`](./features/production_readiness_final_stretch_plan_bn.md) | implementation | Architecture Circle | browser-automation |
| [`risk_remediation_and_hardening_execution_plan_bn`](./features/risk_remediation_and_hardening_execution_plan_bn.md) | implementation | Architecture Circle | control-tower-mcp |
| [`runtime_dynamic_configuration_zero_hardcode_plan`](./features/runtime_dynamic_configuration_zero_hardcode_plan.md) | implementation | Architecture Circle | dynamic-configuration |
| [`implementation_plan`](./implementation_plan.md) | implementation | Architecture Governance / Planning Circle | free-tier-federation |
| [`free_tier_federation_master_plan_v4`](./infrastructure/free_tier_federation_master_plan_v4.md) | architecture | Infrastructure Circle | free-tier-federation |
| [`vision_strategic_positioning`](./vision_strategic_positioning.md) | roadmap | Planning Circle | free-tier-federation |

### 🟡 PROPOSED (queued candidates — not executable) (3)

| Plan | Role | Authority | Family |
|---|---|---|---|
| [`PLAN_002_CLAUDE_STYLE_CONTEXT_COMPACTION_2026-09-16`](./PLAN_002_CLAUDE_STYLE_CONTEXT_COMPACTION_2026-09-16.md) | implementation | Memory Circle + C5 (Execution — LLM Gateway) | free-tier-federation |
| [`PLAN_003_AIDER_STYLE_REPO_MAP_2026-09-17`](./PLAN_003_AIDER_STYLE_REPO_MAP_2026-09-17.md) | implementation | C5 (Execution — LLM Gateway) + Task Circle (backend/services/dynamic_planner.py মালিকানা) | unclassified |
| [`PLAN_004_LETTA_STYLE_MEMORY_DISTILLATION_2026-09-17`](./PLAN_004_LETTA_STYLE_MEMORY_DISTILLATION_2026-09-17.md) | implementation | Memory Circle (backend/core/circles/centers/memory_center.py) + C5 (Execution — LLM Gateway) | free-tier-federation |

### ⛔ BLOCKED (1)

| Plan | Role | Authority | Family |
|---|---|---|---|
| [`PLATFORM_OSS_INTEGRATION_PLAN`](./PLATFORM_OSS_INTEGRATION_PLAN.md) | implementation | Platform Circle | execution-phases |

<!-- END GENERATED PLAN CATALOG -->
