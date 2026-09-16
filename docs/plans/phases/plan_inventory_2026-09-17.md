# docs/plans/ Inventory & Governance Report

> Generated: 2026-09-16 by `scripts/governance/lint_plans.py` (report-only mode)  
> Machine cache: `docs/plans/plan_registry.json` · Source of truth: per-file YAML frontmatter

## Totals

- Documents scanned: **156**
- With valid frontmatter: **5**
- Findings: **17 errors / 155 warnings**

## Family distribution (content-derived)

| Family | Documents |
|---|---|
| control-tower-mcp | 33 |
| execution-phases | 30 |
| unclassified | 23 |
| free-tier-federation | 18 |
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

- `docs/plans/HEAD_OF_PLANNING_STRATEGIC_LEVERAGE_2026-09-16.md`, `docs/plans/features/free_tier_scaling_constitution_and_compliance_policy.md`
- `docs/plans/PLAN_004_LETTA_STYLE_MEMORY_DISTILLATION_2026-09-17.md`, `docs/plans/features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md`

## Findings

### `broken-lineage-link` (3)

- [ERROR  ] broken-lineage-link    supremeai-work/docs/plans/CANONICAL_PLANNING_RECONCILIATION_AND_GUARDRAILS_PLAN.md: supersedes target does not exist: Ad-hoc and unverified plan reconciliation proposals
- [ERROR  ] broken-lineage-link    supremeai-work/docs/plans/features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md: supersedes target does not exist: free_tier_missing_services_integration_plan.md
- [ERROR  ] broken-lineage-link    supremeai-work/docs/plans/features/free_tier_scaling_constitution_and_compliance_policy.md: supersedes target does not exist: free_tier_multi_service_scale_master_plan.md

### `invalid-canonical` (2)

- [ERROR  ] invalid-canonical      supremeai-work/docs/plans/features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md: canonical `docs/plans/features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md` must be true|false|candidate
- [ERROR  ] invalid-canonical      supremeai-work/docs/plans/features/free_tier_scaling_constitution_and_compliance_policy.md: canonical `docs/plans/features/free_tier_scaling_constitution_and_compliance_policy.md` must be true|false|candidate

### `invalid-frontmatter` (3)

- [ERROR  ] invalid-frontmatter    supremeai-work/docs/plans/PLAN_001_ANTHROPIC_PROMPT_CACHING_2026-09-16.md: invalid YAML frontmatter: mapping values are not allowed here
  in "<unicode string>", line 21, column 37:
    last_verified: 2026-09-16 (code-read: gateway.py, cloud_adapter.py,  ... 
 
- [ERROR  ] invalid-frontmatter    supremeai-work/docs/plans/PLAN_002_CLAUDE_STYLE_CONTEXT_COMPACTION_2026-09-16.md: invalid YAML frontmatter: mapping values are not allowed here
  in "<unicode string>", line 22, column 347:
     ... essages L57 unchanged; code-read: websocket_agent.py L469–532, p ... 
- [ERROR  ] invalid-frontmatter    supremeai-work/docs/plans/PLAN_003_AIDER_STYLE_REPO_MAP_2026-09-17.md: invalid YAML frontmatter: mapping values are not allowed here
  in "<unicode string>", line 5, column 194:
     ... AN_LIFECYCLE_POLICY (2026-09-17): single-plan execution, Gate 0– ... 


### `invalid-role` (1)

- [ERROR  ] invalid-role           supremeai-work/docs/plans/CANONICAL_PLANNING_RECONCILIATION_AND_GUARDRAILS_PLAN.md: document_role `policy_and_implementation_governance` not in ['architecture', 'audit', 'implementation', 'policy', 'roadmap']

### `missing-field` (8)

- [ERROR  ] missing-field          supremeai-work/docs/plans/HEAD_OF_PLANNING_STRATEGIC_LEVERAGE_2026-09-16.md: required frontmatter field `document_role` is empty/missing
- [ERROR  ] missing-field          supremeai-work/docs/plans/PLAN_004_LETTA_STYLE_MEMORY_DISTILLATION_2026-09-17.md: required frontmatter field `document_role` is empty/missing
- [ERROR  ] missing-field          supremeai-work/docs/plans/features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md: required frontmatter field `id` is empty/missing
- [ERROR  ] missing-field          supremeai-work/docs/plans/features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md: required frontmatter field `document_role` is empty/missing
- [ERROR  ] missing-field          supremeai-work/docs/plans/features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md: required frontmatter field `planning_authority` is empty/missing
- [ERROR  ] missing-field          supremeai-work/docs/plans/features/free_tier_scaling_constitution_and_compliance_policy.md: required frontmatter field `id` is empty/missing
- [ERROR  ] missing-field          supremeai-work/docs/plans/features/free_tier_scaling_constitution_and_compliance_policy.md: required frontmatter field `document_role` is empty/missing
- [ERROR  ] missing-field          supremeai-work/docs/plans/features/free_tier_scaling_constitution_and_compliance_policy.md: required frontmatter field `planning_authority` is empty/missing

### `missing-frontmatter` (148)

- [WARNING] missing-frontmatter    supremeai-work/docs/plans/CI_PIPELINE_CONSOLIDATION_PLAN_2026-09-15.md: no YAML frontmatter — registry cannot classify this plan (inferred family: ci-cd-pipeline)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/PENDING_APPROVALS.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unclassified)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/PLAN_LIFECYCLE_POLICY.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unclassified)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/PLAN_TO_CODE_TRACEABILITY_MATRIX.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unclassified)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/PLATFORM_OSS_INTEGRATION_PLAN.md: no YAML frontmatter — registry cannot classify this plan (inferred family: execution-phases)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/PR_GUARDIAN_ANALYSIS_PLAN.md: no YAML frontmatter — registry cannot classify this plan (inferred family: control-tower-mcp)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/README.md: no YAML frontmatter — registry cannot classify this plan (inferred family: control-tower-mcp)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/ROADMAP_ECOSYSTEM_ARCHITECTURE_BN.md: no YAML frontmatter — registry cannot classify this plan (inferred family: execution-phases)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unified-architecture)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/UNIFIED_NEXT_ROADMAP_2026-09-15.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unified-architecture)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/README.md: no YAML frontmatter — registry cannot classify this plan (inferred family: dynamic-configuration)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unified-architecture)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/ai_model_comparative_matrix_bangla.md: no YAML frontmatter — registry cannot classify this plan (inferred family: intelligence-evolution)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/autonomous_product_verification_engine.md: no YAML frontmatter — registry cannot classify this plan (inferred family: browser-automation)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/browser_automation.md: no YAML frontmatter — registry cannot classify this plan (inferred family: browser-automation)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/codebase_aligned_master_roadmap.md: no YAML frontmatter — registry cannot classify this plan (inferred family: production-readiness)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/crown_jewel_complete_system_integration_blueprint.md: no YAML frontmatter — registry cannot classify this plan (inferred family: unified-architecture)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/distributed_infrastructure_central_control_plane_plan.md: no YAML frontmatter — registry cannot classify this plan (inferred family: control-tower-mcp)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/dynamic_ai_architecture_v5_zero_downtime.md: no YAML frontmatter — registry cannot classify this plan (inferred family: execution-phases)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/dynamic_configuration_zero_hardcode_roadmap.md: no YAML frontmatter — registry cannot classify this plan (inferred family: dynamic-configuration)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/federated_capability_circles_topology.md: no YAML frontmatter — registry cannot classify this plan (inferred family: control-tower-mcp)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/living_autonomous_intelligence_synthesis.md: no YAML frontmatter — registry cannot classify this plan (inferred family: intelligence-evolution)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/registry_control_in_pipeline_and_dashboard.md: no YAML frontmatter — registry cannot classify this plan (inferred family: ci-cd-pipeline)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/self_learning_ecosystem_transformation_roadmap.md: no YAML frontmatter — registry cannot classify this plan (inferred family: control-tower-mcp)
- [WARNING] missing-frontmatter    supremeai-work/docs/plans/architecture/unified_fastmcp_control_tower_multitenant_master_plan_bn.md: no YAML frontmatter — registry cannot classify this plan (inferred family: control-tower-mcp)
- …and 123 more

### `versioned-filename` (7)

- [WARNING] versioned-filename     supremeai-work/docs/plans/architecture/dynamic_ai_architecture_v5_zero_downtime.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/features/evolution_patch_v3_implementation_plan.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/features/free_tier_production_upgrade_plan_v2.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/infrastructure/SUPREMEAI_CONFIGURATION_CONTROL_REGISTRY_V2.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/infrastructure/free_tier_federation_master_plan_v4.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-work/docs/plans/infrastructure/production_upgrade_implementation_plan_v2.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section

