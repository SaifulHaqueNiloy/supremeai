# SupremeAI Active Audit Queue (Max 50 Live Items)

> **Single Source of Truth for Audits:** সমস্ত অডিট ফাইন্ডিংস শুধুমাত্র এই একটি ফাইলে সংরক্ষিত ও আপডেট হবে। নতুন কোনো অডিট ফাইল তৈরি করা সম্পূর্ণ নিষিদ্ধ।
> **50-Item Sliding Window:** এই ফাইলে সর্বোচ্চ ৫০টি সক্রিয়/অমীমাংসিত (Unresolved) ফাইন্ডিংস থাকবে। কাজ সম্পন্ন ও মার্জ হয়ে গেলে তা এখান থেকে স্বয়ংক্রিয়ভাবে রিমুভ হবে।

---

## Active Discovered Gaps & Findings (Sliding Queue)

| # | ID | Category | Target Path / Scope | Issue / Gap Description | Status | Added Date |
|---|---|---|---|---|---|---|
| 1 | GAP-001 | Wiring | `frontend/src/services/controlPlane.ts` | 57 orphan backend route families need frontend UI wiring | `[OPEN]` | 2026-09-18 |
| 2 | GAP-002 | Context | `backend/context/repo_map.py` | Aider-style AST repo-map generator needs implementation | `[OPEN]` | 2026-09-18 |
| 3 | GAP-003 | Memory | `backend/memory/` | 15 fragmented stores need consolidation into canonical 3-tier | `[OPEN]` | 2026-09-18 |
| 4 | GAP-004 | Reliability | `tests/missions/` | Nightly mission suite needs expansion from 5 to 20 missions | `[OPEN]` | 2026-09-18 |
| 5 | GAP-005 | Compute | `scripts/compute/` | Headless GPU dispatcher script for user-directed compute | `[OPEN]` | 2026-09-18 |
| 6 | ~~GAP-006~~ | Config | `.github/workflows/qa-live-smoke.yml` | **✅ RESOLVED (2026-09-19, Issue #482)** — `PRODUCTION_URL` repo variable set to `https://supremeai-primary-node.onrender.com` (2026-09-18T23:26Z); workflow resolve-chain updated so the owner override acts as the API entry while the SPA origin derives from `FIREBASE_PROJECT_ID` (matches real browser chain); fail-closed preflight assertion retained. Live-smoke run verified green with the override. | `[RESOLVED]` | 2026-09-19 |
| 7 | GAP-007 | Memory | `backend/memory/ai_memory` rows | **✅ RESOLVED (2026-09-19, Issue #479)** — full re-embedding sweep executed with `@cf/baai/bge-small-en-v1.5` (384-dim canonical): 588/588 rows re-indexed, 0 failures, dry-run then live run; `CLOUDFLARE_API_TOKEN` provisioned. | `[RESOLVED]` | 2026-09-19 |
| 8 | GAP-008 | Orchestration | `backend/runs/stategraph.py` & `backend/brain/` | Micro StateGraph Engine + Real ReAct Tool Calling & Checkpoint Binding (Self-healing cyclic workflow replacing stubs) | `[RESOLVED]` | 2026-09-19 |

---

*Rule: Finished items are pruned upon PR merge. Total active items capped at 50. Never spawn duplicate audit files.*
