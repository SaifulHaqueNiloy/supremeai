# STATUS_PROOF.md (generated — do not hand-edit)

**Verdict: PASS** — প্রতিটি machine-checkable দাবি tree-বাস্তবের সাথে মিলেছে।

generated_by: `scripts/ci/generate_status_proof.py` (stdlib-only, deterministic)
honesty_contract: tree-pure — কোনো timestamp/sha/runtime ডেটা নেই (diff-gate বৈধ রাখতে);
runtime/live প্রমাণ Actions run summary-তে (ইচ্ছাকৃতভাবে কমিট হয় না)।

## Machine-verified claims (STATUS.md `STATUS-PROOF:CHECK` block)

- ✅ `frontend_e2e_specs=4` → tree reality: **4**
- ✅ `frontend_test_files=104` → tree reality: **104**
- ✅ `missions_tests=62` → tree reality: **62**
- ✅ `registered_routes=762` → tree reality: **762**

## STATUS.md referenced repo paths

- [x] `docs/generated/STATUS_PROOF.md` — exists

## Deployment verification chain (static inventory)

- ✅ `.github/workflows/ci-deploy-production.yml` — reusable deploy (workflow_call); fail-closed gate markers present
- ✅ `.github/workflows/09-post-deploy-smoke.yml` — post-deploy Playwright canary (workflow_run); fail-closed gate markers present
- ✅ `.github/workflows/qa-live-smoke.yml` — scheduled live probe (schedule + workflow_dispatch); fail-closed gate markers present

Live/runtime evidence: CI Pipeline summaries, `QA — Live Production Smoke` run summaries
(fail-closed যতক্ষণ না `vars.PRODUCTION_URL` কনফিগার করা হয়)।
