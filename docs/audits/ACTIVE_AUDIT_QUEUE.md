# SupremeAI Active Audit Queue (Max 50 Live Items)

> **Single Source of Truth for Audits:** সমস্ত অডিট ফাইন্ডিংস শুধুমাত্র এই একটি ফাইলে সংরক্ষিত ও আপডেট হবে। নতুন কোনো অডিট ফাইল তৈরি করা সম্পূর্ণ নিষিদ্ধ।
> **50-Item Sliding Window:** এই ফাইলে সর্বোচ্চ ৫০টি সক্রিয়/অমীমাংসিত (Unresolved) ফাইন্ডিংস থাকবে। কাজ সম্পন্ন ও মার্জ হয়ে গেলে তা এখান থেকে স্বয়ংক্রিয়ভাবে রিমুভ হবে।

---

## Active Discovered Gaps & Findings (Sliding Queue)

| # | ID | Category | Target Path / Scope | Issue / Gap Description | Status | Added Date |
|---|---|---|---|---|---|---|
| 1 | GAP-001 | Wiring | `frontend/src/services/controlPlane.ts` | 57 orphan backend route families need frontend UI wiring. **STATUS (2026-09-19, issue #480 steps 1-2+5):** generated route→frontend-consumer inventory + classification now exists — `docs/generated/route_consumer_inventory.json` / `.md` (generator `scripts/audit/generate_route_consumer_inventory.py`; allowlist `scripts/audit/api_only_routes.txt`; CI orphan gate `tests/test_route_consumer_contract.py` in ci-advanced-checks.yml). Current scan: 799 routes → 173 user-facing, 320 admin-only, 37 internal, 269 intentionally-API-only across 156 allowlisted families (the actionable wiring debt — owner to prune as wiring lands), 0 unclassified orphans. Steps 3-4 (wiring / deprecation of the 156 families) remain open. | `[OPEN]` | 2026-09-18 |
| 2 | GAP-002 | Context | `backend/context/repo_map.py` | Aider-style AST repo-map generator needs implementation | `[OPEN]` | 2026-09-18 |
| 3 | GAP-003 | Memory | `backend/memory/` | 15 fragmented stores need consolidation into canonical 3-tier | `[OPEN]` | 2026-09-18 |
| 4 | GAP-004 | Reliability | `tests/missions/` | Nightly mission suite needs expansion from 5 to 20 missions | `[OPEN]` | 2026-09-18 |
| 5 | GAP-005 | Compute | `scripts/compute/` | Headless GPU dispatcher script for user-directed compute | `[OPEN]` | 2026-09-18 |
| 6 | ~~GAP-006~~ | Config | `.github/workflows/qa-live-smoke.yml` | **✅ RESOLVED (2026-09-19, Issue #482)** — `PRODUCTION_URL` repo variable set to `https://<render-primary-url>` (2026-09-18T23:26Z); workflow resolve-chain updated so the owner override acts as the API entry while the SPA origin derives from `FIREBASE_PROJECT_ID` (matches real browser chain); fail-closed preflight assertion retained. Live-smoke run verified green with the override. | `[RESOLVED]` | 2026-09-19 |
| 7 | GAP-007 | Memory | `backend/memory/ai_memory` rows | **✅ RESOLVED (2026-09-19, Issue #479)** — full re-embedding sweep executed with `@cf/baai/bge-small-en-v1.5` (384-dim canonical): 588/588 rows re-indexed, 0 failures, dry-run then live run; `CLOUDFLARE_API_TOKEN` provisioned. | `[RESOLVED]` | 2026-09-19 |
| 8 | GAP-008 | Orchestration | `backend/runs/stategraph.py` & `backend/brain/` | Micro StateGraph Engine + Real ReAct Tool Calling & Checkpoint Binding (Self-healing cyclic workflow replacing stubs) | `[RESOLVED]` | 2026-09-19 |
| 9 | GAP-009 | Memory | Render primary+worker env `CLOUDFLARE_API_TOKEN` | **OWNER ACTION REQUIRED** — CF token (`cfut_xuAuJg15Q…`) now returns **401 Invalid API Token** (verified 2026-09-19T06:45Z from outside + same token in both primary & worker env). It was live at the 588/588 re-index sweep earlier the same day. `remote_embed_cf()` reads `os.getenv("CLOUDFLARE_API_TOKEN")` — until rotated, NEW ai_memory rows silently degrade to the hash embedder (no crash; DEGRADED-mode announcement). No working CF token reachable via env.txt/Render API/Infisical (vault unreadable — see #434). Owner: provision a fresh Workers-AI token and update both Render services + Infisical vault. | `[BLOCKED:OWNER]` | 2026-09-19 |

---

## 🗂️ Round-Comment Archive Index (roadmap 1.7, issue #1186)

Per-issue audit comment snapshots previously scattered across `docs/audit_reports/round{14,16,17,19}_comments/` now live in `docs/archive/audit_reports/` (git mv — full history preserved; the canonical content of every snapshot is the GitHub issue thread itself). All issue-IDs covered, in one place:

| Round | Archive path | Issue IDs |
|---|---|---|
| 14 | `docs/archive/audit_reports/round14_comments/` | #430, #431, #432, #434, #437, #438, #442, #444, #445, #446, #448, #454 |
| 16 | `docs/archive/audit_reports/round16_comments/` | #434, #439, #440, #441, #442, #443, #446, #447, #450, #452, #456 |
| 17 | `docs/archive/audit_reports/round17_comments/` | #434, #459, #460 |
| 19 | `docs/archive/audit_reports/round19_comments/` | #434, #441, #449, #453, #457, #458, #465, #468, #472, #474, #475, #476, #478, #479, #480, #481, #482 |

---

*Rule: Finished items are pruned upon PR merge. Total active items capped at 50. Never spawn duplicate audit files.*
