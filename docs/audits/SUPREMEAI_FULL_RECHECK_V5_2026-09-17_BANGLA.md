# SUPREMEAI পূর্ণ পুনঃপরীক্ষা (Full Recheck) — V5

**তারিখ:** 2026-09-17
**স্কোপ:** main HEAD `ed35eaf6` থেকে রুট-লেভেল পূর্ণ অডিট (backend + frontend + MCP + CI + governance + meta-docs)
**পদ্ধতি:** Live CI diagnosis → লোকাল প্রমাণ → surgical fix → প্রতিটি ফিক্সের পুনঃযাচাই → একক কমিট
**পূর্ববর্তী চক্র:** V3 (`6ef6550e`), V4 (`a3fe8bbe` — সমান্তরাল সাইকেল, এই অডিটে তা-ই ভিত্তি)

---

## ১. এক নজরে (Executive Summary)

| সংকেত | V5-এর আগে | V5-এর পরে |
|---|---|---|
| CI Pipeline (main `ed35eaf6`) | 🔴 FAILURE (Backend Prepare + Tooling Gate) | ফিক্সড — `ruff format` ১ ফাইল (1837/1837 green) |
| Plans governance (`lint_plans.py --check`) | 🔴 586 error | 🟢 **0 error, exit 0** (13 non-blocking warning) |
| Frontend ভুয়া মেট্রিক (zero-hardcoded লঙ্ঘন) | 🔴 4টি সাইট | 🟢 0 — সৎ "—" / নিরপেক্ষ 0 / dynamic-first |
| MCP নীরব no-op ফাঁদ | 🔴 1টি (tool.registry) | 🟢 loud warn + ডকুমেন্টেড ঐচ্ছিক ডিপেন্ডেন্সি |
| Meta-doc মৃত দাবি | 🔴 STATUS.md "None! 100% complete" + README broken link | 🟢 সত্যে সংশোধিত |
| Mission suite (sqlite) | 57/57 | ✅ 57/57 (কোনো রিগ্রেশন নেই) |
| Token budget suite | 26/26 | ✅ 26/26 |
| Contract suites | — | ✅ 19/19 |
| MCP typecheck/build + 5টি টেস্ট | — | ✅ সব পাস |
| Duplicate detector (file_level+import gate) | exit 0 | ✅ exit 0 |
| Frontend production build | 11.55s | ✅ 11.41s |

**পরিবর্তনের পরিমাণ:** 145 ফাইল, +1489/−558 লাইন (এর মধ্যে 139টি docs/plans frontmatter-মাইগ্রেশন; কোড পরিবর্তন মাত্র 6 ফাইল — ন্যূনতম, শূন্য নতুন ডিপেন্ডেন্সি)

---

## ২. P0 — CI লাল: রুট কজ ও ফিক্স (V5-01)

**উপসর্গ:** main-এর সর্বশেষ কমিট `ed35eaf6`-এ CI Pipeline FAILURE।
**প্রভাবিত জব:** `Backend Prepare (immutable dependency cache)` + `Operational Tooling Quality Gate` — ফলে Backend Tests, Frontend Tests, Build Verification, MCP Build, Deploy সব skipped।

**রুট কজ (Live CI log থেকে প্রমাণিত):** V4-এর JWT-revocation ফিক্স (`admin_auth.py`) একটি 121-অক্ষরের লাইন রেখে গিয়েছিল; `ruff format --check backend` (CI, ruff 0.16.4) ৩ লাইনে ভাঙতে চেয়েছিল। লোকাল রেপ্লিকেশন (ruff 0.16.8) হুবহু একই diff দেখিয়েছে — পুরো backend-এ ভুল ফাইল **মাত্র ১টি**।

**ফিক্স:** `ruff format backend/api/routes/admin_auth.py` — শুধুমাত্র ফরম্যাটিং, শূন্য সিমান্টিক পরিবর্তন।

**প্রমাণ:**
- `ruff format --check backend` → "1837 files already formatted" ✅
- CI-র সেন্ট্রালাইজড lint gate (`ruff check backend --select E,W,F,I,N,UP,B,SIM --ignore …`) → "All checks passed!" ✅
- `admin_auth.py` AST parse ✅, সংশ্লিষ্ট টেস্ট স্যুট সবুজ (নিচে §৮)

---

## ৩. P1 — Frontend ভুয়া ডেটা অপসারণ (V5-02) — zero-hardcoded নীতি

কোর দর্শন লঙ্ঘন: ব্যাকএন্ড ডেটা অনুপস্থিত থাকলে **বানোয়াট সংখ্যা** ইউজার/অ্যাডমিনকে দেখানো হচ্ছিল (False-Assurance doctrine-এর সরাসরি লঙ্ঘন)।

| ফাইল:লাইন | আগে (ভুয়া) | পরে (সৎ) |
|---|---|---|
| `frontend/src/components/admin/shared/DynamicPanel.tsx:51` | `metrics?.latency_p50_ms \|\| 42` → বানোয়াট **42ms** | মেট্রিক থাকলে প্রকৃত মান; না থাকলে **"—"** |
| `DynamicPanel.tsx:53` | `requests_per_second \|\| 12` → বানোয়াট **12 RPS** | প্রকৃত মান বা **"—"** |
| `DynamicPanel.tsx:54` | `\|\| 'ollama'` → বানোয়াট প্রোভাইডার দাবি | প্রকৃত তালিকা বা **"—"** |
| `DynamicPanel.tsx:52` | `error_rate \|\| 0` → ডেটা নেই মানে "০% error" (ভুয়া আশ্বাস) | `!= null` চেক; না থাকলে **"—"** |
| `frontend/src/pages/user/CostDashboard.tsx:39` | `total_saved \|\| 42.5` → ব্যবহারকারী $0 সেভ করলেও **$42.50** দেখাত | `?? 0` — প্রকৃত 0-ও সঠিকভাবে 0 |
| `CostDashboard.tsx:40` | `cached_queries \|\| 1280` → বানোয়াট **1280** | `?? 0` |
| `CostDashboard.tsx:41` | `free_tier_pct \|\| 94.2` → বানোয়াট **94.2%** | `?? 0` |
| `CostDashboard.tsx:42` | hardcoded 4-প্রোভাইডার breakdown | `?? {}` — UI খালি অবস্থা দেখায় |
| `CostDashboard.tsx:95` | `monthlyLimit \|\| 100` → limit অজানা হলে **$100 ধরে ভুয়া অ্যালার্ট** | limit সংখ্যা না হলে threshold-চেকই বাদ |

**গুরুত্বপূর্ণ পার্থক্য:** `\|\|` → `??` — `0 \|\| 42.5 = 42.5` (প্রকৃত শূন্যকেও ভুয়া মান দখল করত!), `0 ?? 0 = 0`। প্রতিটি পরিবর্তনে বাংলা কমেন্ট যোগ করা হয়েছে।

**প্রমাণ:** `pnpm build` ✅ (11.41s), কোনো টাইপ-এরর নেই।

**স্ক্যান-পদ্ধতি (পুনরায় ব্যবহারযোগ্য):** `\|\| <অশূন্য-সংখ্যা>` প্যাটার্ন স্ক্যান → ডিভিশন-গার্ড (`|| 1`, `|| 0`) ও সৎ `'unknown'` মার্কার বাদ দিয়ে মাত্র এই ভুয়া ডিসপ্লে-সাইটগুলো পাওয়া গেছে।

---

## ৪. P1 — MCP Control Plane: নীরব no-op ফাঁদ (V5-03)

**আবিষ্কার:** `src/dynamic/tool.registry.ts:35`-এ `@supabase/supabase-js` ঐচ্ছিক dynamic import (`.catch(() => null)`)। অ্যাডাপ্টার (`adapters/supabase/index.ts`) আসলে **pure HTTP/PostgREST-based — শূন্য ডিপেন্ডেন্সি**।

**সিদ্ধান্ত (কোর দর্শন মেনে):** প্যাকেজ **ডিপেন্ডেন্সি হিসেবে যোগ করা হয়নি** — কারণ এটি ইচ্ছাকৃতভাবে optional (zero-cost/lightweight নীতি; env না থাকলে static tools-ই যথেষ্ট)। আসল বগি ছিল **নীরব no-op**: অপারেটর `SUPABASE_URL` + key সেট করলেও প্যাকেজ না থাকলে নীরবে `[]` ফিরত হতো — কেউ জানতই না dynamic tools কেন লোড হচ্ছে না।

**ফিক্স:** env-কনফিগার্ড কিন্তু প্যাকেজ-অনুপস্থিত অবস্থায় এখন **loud `console.warn`** + বাংলা কমেন্ট (স্পষ্ট নির্দেশ: প্যাকেজ ইনস্টল করো বা `SUPABASE_URL` unset করো)।

**MCP ভার্সন-ড্রিফট প্রসঙ্গে (F-14 পুনঃমূল্যায়ন):** `typescript ^7.0.2` / `zod ^4.5.4` (installed: 7.0.2 / 4.6.4, নিজস্ব package-lock) — **ত্রুটি নয়**; typecheck+build+৫টি টেস্ট-স্যুট সবুজ। রুট frontend-এর `^5.9.3` থেকে আলাদা হওয়া সত্ত্বেও workspace-isolated। **ঝুঁকিপূর্ণ ভার্সন-চেঞ্জ করা হয়নি** ("nothing break" অগ্রাধিকার)।

**প্রমাণ:** `npm run typecheck` ✅, `npm run build` ✅, test:smoke / service-circles / timestamps / client-registry / access — সব exit 0 ✅

---

## ৫. P1 — Plans Governance: 586 → 0 (V5-04)

**ভাঙান (রেজিস্ট্রি-বিশ্লেষণ):** 177 doc-এর মধ্যে **119টি legacy doc** (features/ 61, phases/ 22, design/ 15, infrastructure/ 11, architecture/ 10) প্রায় সম্পূর্ণ frontmatter ছাড়া — `missing-field` 585 + `invalid-role` 1 + `missing-frontmatter` 1 = 586 error।

**মাইগ্রেশন নীতি (evidence-based, প্রতিটি ফাইলে নোট-কমেন্ট সহ):**
- `document_role`: ডিরেক্টরি+filename-নিয়ম (architecture/→architecture, phases/→roadmap, features/Plan_*→architecture, *_analysis→audit, ইত্যাদি)
- `planning_authority`: `Architecture Governance / Planning Circle` (কমপ্লায়েন্ট doc-দের মতোই একক মালিকানা)
- `status`: **`historical`** (ডিফল্ট) — ন্যূনতম-সৎ দাবি: এগুলো canonical-governance-পূর্ব legacy নথি; unverified `active`/`complete` দাবি **ইচ্ছাকৃতভাবে এড়ানো** হয়েছে (unverified-claim doctrine)। রেজিস্ট্রির `superseded_by` লিংক থাকলে `superseded`; README ক্যাটালগ `active`।
- `target_scope`: `supremeai_internal` (1 doc-এ missing ছিল)
- `id`/`subject`: রেজিস্ট্রি-ডেরাইভড ভ্যালু (stable, idempotent)

**সার্জিক্যাল পদ্ধতি:** existing frontmatter-এর একটিও বাইট পরিবর্তন হয়নি — শুধু closing `---`-এর আগে missing ফিল্ড + migration-নোট কমেন্ট ঢোকানো হয়েছে। 40টি doc-এ প্রথম পাসে YAML-unsafe colon ঢুকে গিয়েছিল (`subject: Plan 1: ...`) — repair পাসে quote/sanitize করে **সব ক্লিন**।

**অন্যান্য ফিক্স:** `design/customer_onboarding_flow.md` `document_role: design` (invalid) → `architecture`; `phases/plan_inventory_report.md` (generated report, no frontmatter) → পূর্ণ ফ্রন্টম্যাটার।

**প্রমাণ:** `lint_plans.py --check` → **errors: 0, exit=0** ✅; `plan_registry.json` রিজেনারেট (555+/537− লাইন, 177 doc এখন সম্পূর্ণ শ্রেণীযোগ্য)। অবশিষ্ট **13টি non-blocking warning** (7 versioned-filename, 6 unverified-claim) — পরবর্তী lifecycle review-র জন্য নথিভুক্ত।

---

## ৬. P2 — Meta-doc মৃত দাবি সংশোধন (V5-05)

| ফাইল:লাইন | মৃত দাবি (আগে) | সত্য (পরে) |
|---|---|---|
| `STATUS.md:110` | "High-Priority Pending Tasks: **None!** All … 100% complete and verified" — অথচ CI লাল, 586 governance error | প্রকৃত pending তালিকা: governance residual warnings, frontend `: any` (~65), dead-file sweep (~85), zero-hardcoded enforcement |
| `README.md:68` | `[MASTER_PLAN.md](MASTER_PLAN.md)` — **ফাইলটি নেই** (broken link) | `docs/plans/architecture/SUPREMEAI_MASTER_PLAN_CANONICAL.md` (canonical, রেজিস্ট্রি-নিশ্চিত) |

---

## ৭. V3/V4 ফিক্সের রিগ্রেশন-যাচাই (সব অক্ষত ✅)

| আইটেম | যাচাই |
|---|---|
| V3: mission-reliability-gate sqlite `DATABASE_URL` | `scheduled-deep-audit.yml:273` — অক্ষত ✅ |
| V3: duplicate_detector `EXEMPT_FILE_LEVEL_PAIRS` | detector exit 0 ✅ |
| V3: token_budget env-aware fail-closed | 26/26 ✅ |
| V4: gateway production MagicMock অপসারণ | `gateway.py` — শুধু কমেন্ট, কোনো mock নেই ✅ |
| V4: admin JWT revocation → canonical store | এই চক্রের 83-টেস্ট স্যুটে অন্তর্ভুক্ত, সবুজ ✅ (সাথে এর ফরম্যাট-বাগই P0 ফিক্স) |
| V4: SSRF guard hole | `a3fe8bbe`-এ বন্ধ; এই চক্রে কোনো নেটওয়ার্ক-কোড স্পর্শ করা হয়নি ✅ |

---

## ৮. যাচাই-ম্যাট্রিক্স (সম্পূর্ণ, লোকাল প্রমাণসহ)

```
DATABASE_URL="sqlite+aiosqlite:///./test.db" pytest tests/missions/ tests/core/test_token_budget.py
  → 83 passed in 21.51s ✅
pytest tests/api/test_app_contract.py + capability + service_wiring + module_operational
  → 19 passed ✅
ruff format --check backend        → 1837 files formatted ✅
ruff check backend (CI gate সেট)   → All checks passed ✅
ruff check tools scripts packages .github/scripts --select E9,F821,F822,F823 → All checks passed ✅
lint_plans.py --check              → 0 errors, exit 0 ✅
duplicate_detector --fail-on-critical (file_level+import) → exit 0 ✅
frontend pnpm build                → ✓ built in 11.41s ✅
mcp npm run typecheck && build     → ✅
mcp 5 টেস্ট-স্ক্রিপ্ট               → সব PASS ✅
```

---

## ৯. এই চক্রে যা ইচ্ছাকৃতভাবে করা হয়নি (সুস্পষ্ট সীমা)

1. **MCP ts/zod ভার্সন-ডাউনগ্রেড** — কাজ করা lockfile ভাঙার ঝুঁকি > কসমেটিক সামঞ্জস্য। নথিভুক্ত, পরে সিদ্ধান্ত।
2. **~85 dead file sweep + 65 `: any`** — বড় রিফ্যাক্টর; একক চক্রে নয়, আলাদা অভিযান দরকার (প্রতিটি ফাইলের import-graph প্রমাণ দরকার)।
3. **Nightly-gate failure নোটিফিকেশন** — শূন্য-খরচ সমাধান (GitHub-নেটিভ) প্রস্তাবিত; এই চক্রে স্কোপ-ক্রিপ এড়াতে বাদ।
4. **13টি governance warning** (versioned-filename/unverified-claim) — blocking নয়; ফাইল-রিনেম = ইতিহাস-হারানোর ঝুঁকি, lifecycle review-র জন্য ছাড়া।

---

## ১০. পরবর্তী চক্রের জন্য সুপারিশ (অগ্রাধিকার-ক্রমে)

1. **CI re-run পর্যবেক্ষণ** — এই কমিটে Backend Prepare/Tooling Gate সবুজ নিশ্চিত করা।
2. **Frontend `: any` ব্যাচ-1** (~20 সাইট, সর্বোচ্চ-ট্রাফিক অ্যাডমিন প্যানেল আগে)।
3. **Dead-file sweep অভিযান** — import-graph প্রমাণসহ 3 ব্যাচে (~30 ফাইল/ব্যাচ)।
4. **Nightly notification** — শূন্য-খরচ GitHub-native রুট।
5. **Plans warning ব্যাচ** — versioned-filename রিনেম + unverified-claim-এ evidence marker।

---

*V5 অডিট সম্পন্ন — প্রতিটি দাবি লোকাল কমান্ড-আউটপুট দিয়ে প্রমাণিত। কোর দর্শন রক্ষা: শূন্য নতুন ডিপেন্ডেন্সি, শূন্য নতুন infra, শূন্য hardcoded ভুয়া ডেটা, ন্যূনতম কোড-পরিবর্তন (6 ফাইল), সম্পূর্ণ রিগ্রেশন-নেগেটিভ।*
