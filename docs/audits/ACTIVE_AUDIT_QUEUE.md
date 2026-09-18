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
| 6 | GAP-006 | Config | **OWNER ACTION REQUIRED** | `PRODUCTION_URL` repo variable not set — QA Live Smoke always fail-closed. Run: `gh variable set PRODUCTION_URL --body "https://supremeai-primary-node.onrender.com" -R SaifulHaqueNiloy/supremeai` (PAT lacks Actions:write — must be owner) | `[BLOCKED:OWNER]` | 2026-09-19 |
| 7 | GAP-007 | Memory | `backend/memory/ai_memory` rows | Existing hash-vector rows in ai_memory need re-embedding after CLOUDFLARE_API_TOKEN is set. Run: `REINDEX_DRY_RUN=true python scripts/maintenance/reindex_ai_memory_embeddings.py` then without dry-run. | `[PENDING:CF-TOKEN]` | 2026-09-19 |
| 8 | GAP-008 | Orchestration | `backend/runs/stategraph.py` & `backend/brain/` | Micro StateGraph Engine + Real ReAct Tool Calling & Checkpoint Binding (Self-healing cyclic workflow replacing stubs) | `[RESOLVED]` | 2026-09-19 |

---

*Rule: Finished items are pruned upon PR merge. Total active items capped at 50. Never spawn duplicate audit files.*
