---
target_scope: supremeai_internal
# [V5 audit 2026-09-17] Legacy doc migrated to canonical governance schema; defaults are conservative (historical/derived role) — refine on next lifecycle review.
id: auto:plan_inventory_2026-09-17
subject: docs/plans/ Inventory & Governance Report
document_role: roadmap
planning_authority: Architecture Governance / Planning Circle
status: historical

---

# docs/plans/ Inventory & Governance Report

> Generated: 2026-09-16 by `scripts/governance/lint_plans.py` (report-only mode)  
> Machine cache: `docs/plans/plan_registry.json` · Source of truth: per-file YAML frontmatter

## Totals

- Documents scanned: **157**
- With valid frontmatter: **31**
- Findings: **0 errors / 134 warnings**

## Family distribution (content-derived)

| Family | Documents |
|---|---|
| control-tower-mcp | 33 |
| execution-phases | 30 |
| unclassified | 23 |
| free-tier-federation | 19 |
| frontend-product-ux | 15 |
| ci-cd-pipeline | 8 |
| unified-architecture | 8 |
| browser-automation | 7 |
| intelligence-evolution | 5 |
| dynamic-configuration | 4 |
| production-readiness | 3 |
| security-defense | 1 |
| deployment-render | 1 |

## Competing plan sets (same subject + role, unlinked)

- `docs/plans/features/free_tier_512mb_memory_pressure_remediation_plan.md`, `docs/plans/features/free_tier_production_upgrade_plan_v2.md`

## Findings

### `missing-frontmatter` (126)

- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/README.md: no YAML frontmatter — registry cannot classify this plan (inferred family: dynamic-configuration)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/ai_model_comparative_matrix_bangla.md: no YAML frontmatter — registry cannot classify this plan (inferred family: intelligence-evolution)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/autonomous_product_verification_engine.md: no YAML frontmatter — registry cannot classify this plan (inferred family: browser-automation)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/codebase_aligned_master_roadmap.md: no YAML frontmatter — registry cannot classify this plan (inferred family: production-readiness)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/crown_jewel_complete_system_integration_blueprint.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unified-architecture)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/distributed_infrastructure_central_control_plane_plan.md: no YAML frontmatter — registry cannot classify this plan (inferred family: control-tower-mcp)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/dynamic_ai_architecture_v5_zero_downtime.md: no YAML frontmatter — registry cannot classify this plan (inferred family: execution-phases)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/federated_capability_circles_topology.md: no YAML frontmatter — registry cannot classify this plan (inferred family: control-tower-mcp)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/living_autonomous_intelligence_synthesis.md: no YAML frontmatter — registry cannot classify this plan (inferred family: intelligence-evolution)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/registry_control_in_pipeline_and_dashboard.md: no YAML frontmatter — registry cannot classify this plan (inferred family: ci-cd-pipeline)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/self_learning_ecosystem_transformation_roadmap.md: no YAML frontmatter — registry cannot classify this plan (inferred family: control-tower-mcp)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/unified_fastmcp_control_tower_multitenant_master_plan_bn.md: no YAML frontmatter — registry cannot classify this plan (inferred family: control-tower-mcp)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/visual_component_integration_topology.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unified-architecture)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/README.md: no YAML frontmatter — registry cannot classify this plan (inferred family: frontend-product-ux)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/admin_dashboard_plan.md: no YAML frontmatter — registry cannot classify this plan (inferred family: execution-phases)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/admin_dashboard_visual_and_api_gap_analysis.md: no YAML frontmatter — registry cannot classify this plan (inferred family: frontend-product-ux)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/ai_providers_tab_plan.md: no YAML frontmatter — registry cannot classify this plan (inferred family: dynamic-configuration)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/autonomous_ui_architect_agent_system_prompt.md: no YAML frontmatter — registry cannot classify this plan (inferred family: frontend-product-ux)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/complete_frontend_master_plan_bn.md: no YAML frontmatter — registry cannot classify this plan (inferred family: execution-phases)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/dashboard_design_mockups.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unclassified)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/dashboard_tab_design_plan.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unclassified)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/intelligent_chat_plan.md: no YAML frontmatter — registry cannot classify this plan (inferred family: frontend-product-ux)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/knowledge_acquisition_plan.md: no YAML frontmatter — registry cannot classify this plan (inferred family: frontend-product-ux)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/mission_orchestration_plan.md: no YAML frontmatter — registry cannot classify this plan (inferred family: frontend-product-ux)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/design/single_frontend_role_based_auth_migration_roadmap.md: no YAML frontmatter — registry cannot classify this plan (inferred family: frontend-product-ux)
- …and 101 more

### `unverified-claim` (1)

- [WARNING] unverified-claim       supremeai-work/docs/plans/implementation_plan.md: L202: confident claim without evidence marker — `Enterprise targets such as 99.99% uptime or sub-100ms P95 are **future targets**, not current guarantees.`

### `versioned-filename` (7)

- [WARNING] versioned-filename     supremeai-work/docs/plans/architecture/dynamic_ai_architecture_v5_zero_downtime.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/features/evolution_patch_v3_implementation_plan.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/features/free_tier_production_upgrade_plan_v2.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/infrastructure/SUPREMEAI_CONFIGURATION_CONTROL_REGISTRY_V2.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/infrastructure/free_tier_federation_master_plan_v4.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/infrastructure/production_upgrade_implementation_plan_v2.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
