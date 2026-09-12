# Constitution implementation — manual tasks

The automated foundation and governance checks are in place. These items require an authorized owner or live provider access and are intentionally not performed by CI:

- Approve the transition from advisory to blocking mode, with a reviewed CI run URL and false-positive decision.
- Assign owners and expiry dates for every real exemption; never merge a permanent exemption.
- Review protected paths and CODEOWNERS for constitution/rules, deployment, auth, billing, and tenant boundaries.
- Connect the organization notification destination (Slack/email) and define escalation ownership.
- Configure durable storage for CI summaries and expose it through the existing CI dashboard API; the current in-memory API is not production persistence.
- Run a production-like backup restore drill and attach evidence to the release record.
- Approve retention/privacy policy for audit artifacts and set repository artifact retention accordingly.
- Review new detector baselines and promote only after human false-positive/negative review.
- Obtain security approval before enabling any autonomous remediation or deployment mutation.

## Reliability assessment handoff (2026-09-13)

Repository-local checks completed for this review:

- Dependency policy: passed; Poetry and `backend/poetry.lock` are the canonical backend dependency pair.
- Route registry: passed; 127 unique importable routers are registered.
- Manual-task report generation: passed; the report is non-secret and does not mutate infrastructure.
- Backend tests: blocked in this sandbox because Poetry and pytest are not installed; CI remains the execution authority.
- Frontend validation: not executed here because the repository's frontend toolchain is managed by the workspace CI/pnpm environment.

These assessment claims still require evidence rather than assumptions:

- Production build reliability and end-to-end Circle completion.
- Actual coverage quality, not only configured thresholds.
- Dependency vulnerability status from a current CI security run.
- Frontend/backend contract consistency in a staging environment.
- Core model-router behavior under provider failures and fallback conditions.
- Memory/personalization correctness with tenant isolation and durable persistence.

Use `scripts/ci/build_manual_task_report.py` to generate a non-secret checklist report. These tasks must not be marked complete from repository-local evidence alone.

## Master implementation plan handoff (2026-09-13)

Completed in this repository during this pass:

- Centralized the 13 previously orphaned feature route modules in `backend/api/routers.py`.
- Removed the direct `workspace_feature_routes` registration from `backend/core/app.py`; route ownership now flows through the central registry.
- Removed the nested `infrastructure/mcp-control-plane/package-lock.json`; the workspace lockfile remains authoritative.

Still requiring staged implementation, live infrastructure, or security approval:

- Build and test the `SupremeKernel` request/response contract and `/api/v1/kernel/dispatch` endpoint; define authentication, tenant scope, policy, rate limits, idempotency, and audit semantics before enabling it.
- Complete circle boundary facades and enforce AST import rules in CI; obtain architecture-owner approval for allowed dependency directions.
- Review and publish the generated living topology graph (`docs/generated/route_topology.mmd`) in an approved internal dashboard; validate that generated output contains no secrets or tenant data.
- Validate the bounded architecture query CLI (`scripts/ci/architecture_query.py`) against approved flow labels and decide whether a developer-facing wrapper/entry point should be published.
- Implement L1-L4 configuration control plane, Redis invalidation, PostgreSQL schema/migrations, admin authorization, rollback semantics, and failure-injection tests.
- Implement dynamic model registry and schema-driven admin UI with provider catalog validation, cost controls, and approval workflow.
- Design and threat-model swarm consensus before production use; define token/cost budgets, prompt-injection defenses, deterministic audit trails, and human escalation.
- Do not implement arbitrary LLM-generated code execution until an approved isolated microVM/sandbox, egress policy, resource limits, artifact cleanup, and security review exist.
- Design the memory dream cycle and proactive watcher with tenant isolation, consent/retention rules, durable queues, idempotency, and false-positive review.
- Run staging OpenAPI, frontend contract, restore, failure-fallback, and browser smoke tests; attach evidence to the release record.

These items are intentionally not marked complete from repository-local edits alone.

## Phase 2-4 verification handoff (2026-09-13)

Repository verification confirms these gaps remain architectural work, not merely missing documentation:

- **Phase 2A — SupremeKernel:** no production-ready `backend/core/kernel/dispatcher.py` contract and no registered `/api/v1/kernel/dispatch` endpoint were found. Do not expose a placeholder dispatch route until authentication, tenant scope, policy, idempotency, rate limits, timeout, and audit behavior are approved.
- **Phase 2C — Circles:** `backend/core/circles/` already contains registry/contracts/bootstrap primitives, but the four requested boundary facades (`governance`, `execution`, `evolution`, `infrastructure`) and an enforced AST import-direction linter are not complete.
- **Phase 3 — Dynamic control plane:** configuration classification and health metadata exist locally, but durable L1-L4 storage, invalidation, migrations, rollback, admin authorization, and schema-driven UI are not implemented.
- **Phase 4 — Swarm and ephemeral tooling:** swarm/debate and sandbox-related code exists in isolated areas, but a governed architect-critic consensus loop and approved ephemeral tool synthesis path are not verified as one secure end-to-end capability.

Repository-local work may add contracts, static validators, tests, and documentation. Production activation, durable persistence, provider credentials, sandbox isolation, threat modeling, and owner/security approval remain manual gates and must not be marked complete from static checks alone.

## Human behavior alignment and continuous learning handoff (2026-09-13)

Completed locally:

- Added `backend/core/behavioral_intelligence/` as a separate subsystem; browser automation behavior remains in `core/human_behavior.py`.
- Added bounded, ephemeral behavioral signal contracts with uncertainty fields and no durable psychological identity fields.
- Added deterministic strategy selection for clarification, concise responses, frustration-aware directness, and safety boundaries.
- Added policy gates that keep behavioral signals advisory and preserve existing action approval/manual-only controls.
- Added privacy-safe learning metadata sanitization that rejects raw prompt/response/content fields.
- No production request path, model weights, training artifact, or user profile was mutated by this local implementation.

Still manual or staged:

- Review and approve the behavioral signal taxonomy, thresholds, language coverage, and risk vocabulary with the architecture/privacy owner.
- Add tenant-scoped durable preference storage only after selecting the production database, consent model, retention period, deletion/export workflow, and RLS/authorization tests.
- Integrate the strategy router into the canonical request path only after end-to-end policy, latency, fallback, and tenant-isolation tests pass.
- Build curated consented seed data; complete de-identification, contamination checks, deduplication, and sampled human review before any training use.
- Extend the existing synthetic and RLHF pipelines with dataset versioning, provenance, evaluator dimensions, and a hard prohibition on mock data for production training.
- Implement the behavioral evaluation benchmark and baseline comparison across coding, multilingual, safety, tool-use, adversarial, and long-context cases.
- Run cloud SFT/DPO experiments and artifact signing/registry promotion; local repository changes cannot validate GPU training or model quality.
- Execute shadow/canary deployment, cost/latency regression checks, rollback drill, and explicit human promotion approval.
- Approve privacy/ethics boundaries for emotional inference, sensitive attributes, training consent, retention, and user-facing transparency.

These tasks must not be marked complete from repository-local evidence alone.
