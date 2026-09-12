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
