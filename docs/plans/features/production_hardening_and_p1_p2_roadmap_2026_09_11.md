---
id: production-hardening-p1-p2-roadmap
subject: "SupremeAI — প্রোডাকশন রোডম্যাপ (২০২৬-০৯-১১)"
document_role: roadmap
planning_authority: Architecture Circle
canonical: candidate
status: active
evidence_state: partial
disposition: retain
last_verified: 2026-09-17
supersedes: []
superseded_by: []
related:
  - docs/plans/features/production_readiness_final_stretch_plan_bn.md
  - docs/plans/features/risk_remediation_and_hardening_execution_plan_bn.md
target_scope: supremeai_internal
---

# SupremeAI — প্রোডাকশন রোডম্যাপ (২০২৬-০৯-১১)

> সোর্স: `STATUS.md`, `CHECKPOINT.md`, `AUDIT_REPORT_2026-09-10.md` এবং মেমোরিতে থাকা আগের কাজের ইতিহাস থেকে তৈরি।

## ০. বর্তমান অবস্থা (Snapshot)

| উপাদান | অবস্থা |
| --- | --- |
| Frontend typecheck | ✅ পাস |
| Frontend tests | ✅ ৪২০/৪২০ (৮৩ ফাইল) |
| Backend Python compile | ✅ পাস |
| Backend ruff/poetry | ⚠️ বর্তমান environment-এ ভেরিফাই করা হয়নি |
| CI coverage | Backend ৩০%, Frontend ১৬% (গেট: ৫০%/২০%-এ বাড়ানো হয়েছে) |
| Live services (Render) | ✅ core/worker/scraper/mcp — সব লাইভ |
| ২০২৬-০৯-১০ অডিটের ৭টি P0/P1 আইটেম | ✅ ফিক্স সম্পন্ন (mypy.ini, F821, secret transcript, skipped tests, coverage gate, migration docs) |

## ২. P1 — প্রোডাকশন যাওয়ার আগে জরুরি

- [ ] Root-level lint gap বন্ধ করুন: `tools/`, `scripts/`, `packages/`, `.github/scripts/` এখনো CI lint দিয়ে গার্ড করা হয় না (অডিটে ~১,৫০০ ইস্যু পাওয়া গিয়েছিল, ১৮১টি real F821 বাগ আগে ফিক্স হয়েছে) — একটি root-level ruff CI job যোগ করুন যাতে regression আটকানো যায়।
- [ ] ৬টি skip করা টেস্ট resolve করুন (`docs/SKIPPED_TESTS.md`): billing path বাগ + respx import ফিক্স হয়েছে; বাকি ৩টি (cognitive_router v2.0, grpc_client, test_task_router) ইচ্ছাকৃতভাবে skip করা — এগুলো হয় implement করুন, নয়তো tracked ticket সহ formally defer করুন।
- [ ] Supabase `ai_memory` table setup (Phase C) — এখনো pending, CHECKPOINT.md-এ বহুদিন ধরে carry-forward হচ্ছে।
- [ ] Dual migration system একীভূত করুন — Alembic-কে canonical ঘোষণা করে raw SQL migrations (`backend/database/migrations/legacy`)-কে সম্পূর্ণ archive করুন।

## ৩. P2 — কোয়ালিটি ও হাইজিন

- [ ] Frontend ESLint-এর ১২৬টি warning কমান (প্রধানত `no-explicit-any` ৫৭টি, `no-unused-vars` ৪৮টি) — প্রজেক্টের নিজস্ব নিয়ম "no Any" এর সাথে সরাসরি সাংঘর্ষিক।
- [ ] Knip dead-code inventory (৭২টি unused export, ২৪টি unused dependency) — Core Constitution rule অনুযায়ী delete করার আগে admin approval নিন; একটি approval request ডকুমেন্ট বানান।
- [ ] Coverage থ্রেশহোল্ড বাস্তব সংখ্যার কাছাকাছি বাড়ান (backend বর্তমানে ৩০% রিপোর্ট করছে যদিও গেট ৫০%-এ সেট — এই গ্যাপ মিলিয়ে নিন)।
- [ ] VS Code extension-এর ডুপ্লিকেট mock/টেস্ট framework (jest + vitest একসাথে) পরিষ্কার করুন।
- [ ] Backend-এর blind `except:` ব্লকগুলো (`trio_adapters.py`, `dock_integrations.py`, `pyerrorfix/*` ইত্যাদি) লগিং সহ নির্দিষ্ট exception-এ রূপান্তর করুন।

## ৪. দুই-রিপো ডিপ্লয়মেন্ট চেকলিস্ট

| রিপো | টার্গেট | চেকলিস্ট |
| --- | --- | --- |
| `SaifulHaqueNiloy/supremeai` (staging/AI zone) | Admin Backend Render অ্যাকাউন্ট | ✅ CI green, ✅ secrets registry ভেরিফাই, ⬜ P0 আইটেম ক্লিয়ার হওয়ার পর merge |
| `paykaribazaronline/supremeai` (production) | User Backend Render অ্যাকাউন্ট | ⬜ staging থেকে merge করার আগে CODEOWNERS review, ⬜ schema drift ফাইনাল চেক, ⬜ SSLCommerz/Stripe payment flow শেষবার স্মোক-টেস্ট |

## ৫. পরামর্শকৃত ক্রম

1. P0 সিকিউরিটি আইটেম (key rotation + uncommitted WIP) আজই বন্ধ করুন।
2. P1 আইটেম staging repo-তে সপ্তাহ ধরে সমাধান করুন, প্রতিটি ছোট PR আকারে।
3. staging → production merge-এর আগে P0/P1 সব green হওয়া নিশ্চিত করুন, তারপর production repo-তে push করে Render-এ deploy ট্রিগার করুন।
4. P2 আইটেমগুলো ongoing hygiene ব্যাকলগ হিসেবে চালিয়ে যান, প্রতিটি সেশনে অল্প অল্প করে।