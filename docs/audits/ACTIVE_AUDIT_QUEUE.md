# SupremeAI Active Audit Queue (Max 50 Live Items)

> **Single Source of Truth for Audits:** সমস্ত অডিট ফাইন্ডিংস শুধুমাত্র এই একটি ফাইলে সংরক্ষিত ও আপডেট হবে। নতুন কোনো অডিট ফাইল তৈরি করা সম্পূর্ণ নিষিদ্ধ।
> **50-Item Sliding Window:** এই ফাইলে সর্বোচ্চ ৫০টি সক্রিয়/অমীমাংসিত (Unresolved) ফাইন্ডিংস থাকবে। কাজ সম্পন্ন ও মার্জ হয়ে গেলে তা এখান থেকে স্বয়ংক্রিয়ভাবে রিমুভ হবে।

---

## Active Discovered Gaps & Findings (Sliding Queue)

| # | ID | Category | Target Path / Scope | Issue / Gap Description | Status | Added Date |
|---|---|---|---|---|---|---|
| 1 | GAP-001 | Wiring | `frontend/src/services/controlPlane.ts` | 57 orphan backend route families need frontend UI wiring | `[OPEN]` | 2026-09-18 |
| 2 | GAP-002 | Context | `backend/context/repo_map.py` | Aider-style AST repo-map generator needs implementation | `[OPEN]` | 2026-09-18 |
| 3 | GAP-003 | Memory | `backend/memory/` | 15 fragmented stores need consolidation into canonical 3-tier | `[OPEN]` | 2026-09-18 |
| 4 | GAP-004 | Reliability | `tests/missions/` | Nightly mission suite needs expansion from 5 to 20 missions | `[OPEN]` | 2026-09-18 |
| 5 | GAP-005 | Compute | `scripts/compute/` | Headless GPU dispatcher script for user-directed compute | `[OPEN]` | 2026-09-18 |

---

*Rule: Finished items are pruned upon PR merge. Total active items capped at 50. Never spawn duplicate audit files.*
