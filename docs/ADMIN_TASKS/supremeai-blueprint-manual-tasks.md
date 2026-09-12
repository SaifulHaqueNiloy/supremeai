# SupremeAI blueprint implementation handoff

The repository now provides a governed intelligence router, bounded execution budgets, evidence-based verification, and a non-secret manual-task registry. These controls intentionally keep irreversible actions proposal-only.

## Manual tasks

- Rotate any previously exposed Render API key and GitHub PAT; verify revocation.
- Verify production secrets in the managed cloud secret store; do not commit them.
- Provision and verify the durable `ai_memory` schema using canonical cloud migrations.
- Connect and authorize GitHub, Supabase, Render, and notification providers with least privilege.
- Review and approve generated PRs, migrations, configuration changes, deployments, rotations, and production mutations.
- Configure cloud schedules for memory consolidation and risk watchers with alerts and resource limits.
- Run staging smoke tests, restore drills, and canary checks after CI passes.
- Approve retention/privacy policy for audit artifacts and autonomous remediation boundaries.

Evidence should be attached to the release or audit record. No secret, token, provider authorization, production deployment, destructive migration, or direct default-branch mutation is performed by this implementation.
