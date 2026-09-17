# docs/plans/ Inventory & Governance Report

> Generated: 2026-09-17 by `scripts/governance/lint_plans.py` (report-only mode)  
> Machine cache: `docs/plans/plan_registry.json` · Source of truth: per-file YAML frontmatter

## Totals

- Documents scanned: **164**
- With valid frontmatter: **164**
- Findings: **596 errors / 13 warnings**

## Family distribution (content-derived)

| Family | Documents |
|---|---|
| control-tower-mcp | 33 |
| execution-phases | 30 |
| unclassified | 28 |
| free-tier-federation | 20 |
| frontend-product-ux | 15 |
| unified-architecture | 8 |
| browser-automation | 8 |
| ci-cd-pipeline | 7 |
| intelligence-evolution | 5 |
| dynamic-configuration | 4 |
| production-readiness | 3 |
| memory-data-lifecycle | 1 |
| security-defense | 1 |
| deployment-render | 1 |

## Competing plan sets (same subject + role, unlinked)

- `docs/plans/features/free_tier_512mb_memory_pressure_remediation_plan.md`, `docs/plans/features/free_tier_production_upgrade_plan_v2.md`

## Findings

### `broken-lineage-link` (5)

- [ERROR  ] broken-lineage-link    supremeai-recheck/docs/plans/architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md: supersedes target does not exist: docs/archive/plans/architecture/MASTER_PLAN_BANGLA.md
- [ERROR  ] broken-lineage-link    supremeai-recheck/docs/plans/architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md: supersedes target does not exist: docs/archive/plans/architecture/supremeai_master_blueprint_bangla.md
- [ERROR  ] broken-lineage-link    supremeai-recheck/docs/plans/architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md: supersedes target does not exist: docs/archive/plans/architecture/ROADMAP_BANGLA.md
- [ERROR  ] broken-lineage-link    supremeai-recheck/docs/plans/architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md: supersedes target does not exist: docs/archive/plans/architecture/master_plan_strategic_analysis_bn.md
- [ERROR  ] broken-lineage-link    supremeai-recheck/docs/plans/architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md: supersedes target does not exist: docs/archive/plans/architecture/supremeai_project_complete_overview_bangla.md

### `invalid-role` (1)

- [ERROR  ] invalid-role           supremeai-recheck/docs/plans/design/customer_onboarding_flow.md: document_role `design` not in ['architecture', 'audit', 'implementation', 'policy', 'roadmap']

### `missing-field` (590)

- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/README.md: required frontmatter field `id` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/README.md: required frontmatter field `subject` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/README.md: required frontmatter field `document_role` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/README.md: required frontmatter field `planning_authority` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/README.md: required frontmatter field `status` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/ai_model_comparative_matrix_bangla.md: required frontmatter field `id` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/ai_model_comparative_matrix_bangla.md: required frontmatter field `subject` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/ai_model_comparative_matrix_bangla.md: required frontmatter field `document_role` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/ai_model_comparative_matrix_bangla.md: required frontmatter field `planning_authority` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/ai_model_comparative_matrix_bangla.md: required frontmatter field `status` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/autonomous_product_verification_engine.md: required frontmatter field `id` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/autonomous_product_verification_engine.md: required frontmatter field `subject` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/autonomous_product_verification_engine.md: required frontmatter field `document_role` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/autonomous_product_verification_engine.md: required frontmatter field `planning_authority` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/autonomous_product_verification_engine.md: required frontmatter field `status` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/codebase_aligned_master_roadmap.md: required frontmatter field `id` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/codebase_aligned_master_roadmap.md: required frontmatter field `subject` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/codebase_aligned_master_roadmap.md: required frontmatter field `document_role` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/codebase_aligned_master_roadmap.md: required frontmatter field `planning_authority` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/codebase_aligned_master_roadmap.md: required frontmatter field `status` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/crown_jewel_complete_system_integration_blueprint.md: required frontmatter field `id` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/crown_jewel_complete_system_integration_blueprint.md: required frontmatter field `subject` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/crown_jewel_complete_system_integration_blueprint.md: required frontmatter field `document_role` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/crown_jewel_complete_system_integration_blueprint.md: required frontmatter field `planning_authority` is empty/missing
- [ERROR  ] missing-field          supremeai-recheck/docs/plans/architecture/crown_jewel_complete_system_integration_blueprint.md: required frontmatter field `status` is empty/missing
- …and 565 more

### `unverified-claim` (6)

- [WARNING] unverified-claim       supremeai-recheck/docs/plans/architecture/dynamic_ai_architecture_v5_zero_downtime.md: L1244: confident claim without evidence marker — `Runs locally, no API keys needed, 100% uptime`
- [WARNING] unverified-claim       supremeai-recheck/docs/plans/features/antihacking_security_defense_framework.md: L346: confident claim without evidence marker — `- **Availability SLA**: 99.9% uptime guaranteed`
- [WARNING] unverified-claim       supremeai-recheck/docs/plans/features/superai_competitor_playbook.md: L279: confident claim without evidence marker — `└── Our Opportunity: 99.9% Uptime guarantee`
- [WARNING] unverified-claim       supremeai-recheck/docs/plans/implementation_plan.md: L203: confident claim without evidence marker — `Enterprise targets such as 99.99% uptime or sub-100ms P95 are **future targets**, not current guarantees.`
- [WARNING] unverified-claim       supremeai-recheck/docs/plans/phases/phase4_optimization.md: L108: confident claim without evidence marker — `- 99.9% uptime achieved`
- [WARNING] unverified-claim       supremeai-recheck/docs/plans/phases/yearly_strategic_roadmap_2026.md: L50: confident claim without evidence marker — `- **Reliability**: 99.9% uptime`

### `versioned-filename` (7)

- [WARNING] versioned-filename     supremeai-recheck/docs/plans/architecture/dynamic_ai_architecture_v5_zero_downtime.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-recheck/docs/plans/features/evolution_patch_v3_implementation_plan.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-recheck/docs/plans/features/free_tier_federation_master_plan_v4.1_missing_services_analysis.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-recheck/docs/plans/features/free_tier_production_upgrade_plan_v2.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-recheck/docs/plans/infrastructure/SUPREMEAI_CONFIGURATION_CONTROL_REGISTRY_V2.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-recheck/docs/plans/infrastructure/free_tier_federation_master_plan_v4.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section
- [WARNING] versioned-filename     supremeai-recheck/docs/plans/infrastructure/production_upgrade_implementation_plan_v2.md: filename uses banned versioning pattern (_v2/_final/_latest/…); changes belong in this living plan's evolution section

