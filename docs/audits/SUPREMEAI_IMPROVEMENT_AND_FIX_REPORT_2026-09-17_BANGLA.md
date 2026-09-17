# SupremeAI — উন্নতি, ডায়নামিকতা ও ইন্টেলিজেন্স বিশ্লেষণ + ফিক্স রিপোর্ট

**তারিখ:** ২০২৬-০৯-১৭ | **পদ্ধতি:** সরাসরি main ব্রাঞ্চে merge + fix + push (ব্যবহারকারীর নির্দেশ অনুযায়ী)
**সোর্স:** https://github.com/SaifulHaqueNiloy/supremeai | **রেজিস্টার:** `docs/audits/SUPREMEAI_CANONICAL_DEFECT_AND_FAILURE_REGISTER.md`

---

## ভাগ ১ — এই সেশনে যা যা করা হয়েছে (সবই main-এ পুশড)

### ১.১ ঝুলে থাকা ৭টি ব্রাঞ্চ main-এ মার্জ

নিচের ব্রাঞ্চগুলো main থেকে আলাদা ঝুলে ছিল — প্রতিটি পরীক্ষা করে, কনফ্লিক্ট সমাধান করে main-এ মার্জ করা হয়েছে:

| ব্রাঞ্চ | কী আছে |
|---|---|
| `docs/plan-governance-phase-6` | Plan governance Phase ০–৬-এর সম্পূর্ণ সুপারসেট (ক্যানোনিকাল plan registry, `lint_plans.py`, CI governance job) — বাকি ৪টি পুরনো phase ব্রাঞ্চ এর সাবসেট ছিল |
| `fix/skills-install-uninstall-deploy` | Skill install-এ আসল পারসিসটেন্ট স্টেট, uninstall রুট, deploy-blueprint (ERR-H02) |
| `fix/err-m02-ci-stub-gate` | CI-তে report-only stub-trend job (ERR-M02 রাউন্ড ২) |
| `feat/err-b03-activity-timeline` | `/activity` পেজে রিয়েল মিশন ইভেন্ট টাইমলাইন |
| `feat/err-b04-runs-observer` | `/runs` পেজে রিয়েল run observer + step retry |
| `feat/err-b05-user-marketplace` | `/marketplace` পেজে ইউজার-ফেসিং skill marketplace |
| `hotfix/leftrail-truncation` | CommandCenter LeftRail ট্রাঙ্কেশন ফিক্স |

কনফ্লিক্টগুলোর মধ্যে উল্লেখযোগ্য ছিল `App.tsx`-এর রাউটিং (নতুন `MarketplacePage` + `RunsPage` — দুটোই রাখা হয়েছে), ডিফেক্ট রেজিস্টারের স্ট্যাটাস সেল (দুই পক্ষের সঠিক লাইন কম্বাইন), এবং skills.py-র ফরম্যাটিং (সেমান্টিক্যালি একই)।

### ১.২ বাকি OPEN ইস্যুগুলো ফিক্স (সরাসরি main-এ পুশ)

মার্জের পর ডিফেক্ট রেজিস্টার অনুযায়ী বাকি ছিল ৪টি আর্কিটেকচারাল (F01–F04) + ২টি ডিপেন্ডেন্সি (P01–P02) ইস্যু। ফলাফল:

| ID | সমস্যা | কী করা হলো | কমিট |
|---|---|---|---|
| **ERR-P01** ✅ | Storybook v8 + v10 প্যাকেজ সংঘর্ষ | v8-only প্যাকেজ ৫টি রিমুভ (`addon-essentials`, `addon-interactions`, `addon-links`, `blocks`, `test`), `@storybook/react`+`react-vite` → `^10.5.10`; lockfile থেকে ৫৫৪টি stale লাইন বাদ; typecheck গ্রিন | `56058467` |
| **ERR-F01** ⚠️→part | Canonical Run মডেল **ছিল কিন্তু production-এ কোনো কলার নেই** | `observe_automation_run` ব্রিজ আসল dispatch পথে ওয়্যার: `ExecutionRecorder.record_start` এখন run তৈরি করে (REQUESTED→POLICY_CHECKED→PLANNED→RUNNING, event-id-তে idempotent), `record_completion`/`persist_execution` terminal স্টেটে settle করে (DELIVERED→SUCCEEDED, FAILED→FAILED+error, SKIPPED→CANCELLED) — সবই best-effort, পুরনো DB-তে আচরণ অপরিবর্তিত। ৮টি নতুন রিগ্রেশন টেস্ট | `ee60fdb4` |
| **ERR-F03** ✅ | Context assembly অসংগঠিত — token budget নেই | নতুন **M2 Context Engine** (`backend/context_engine/`): deterministic, budgeted, smallest-sufficient-context। user message hard-reserve, system ২৫% cap, memory/knowledge/history priority-driven best-fit fill; provider-ভিত্তিক বাজেট (gemini ৬০০০, groq ৪০০০, অজানা হলে conservative ৩০০০)। `chat.py`-র **দুটো রিয়েল কল সাইটে** ওয়্যারড; প্রম্পট শেপ backward-compatible; ৯ ইউনিট টেস্ট | `e48daaf0` |
| **ERR-F04** ✅ | ফ্রন্টএন্ড মেজর আপগ্রেড ব্লকড | ① react-router-dom `^6→^7.18.4` — ফিউচার-ফ্ল্যাগ props বাদ, typecheck + **৫১৭/৫১৭ টেস্ট** + প্রোডাকশন বিল্ড গ্রিন; ② `react-i18next`/`i18next` **ডেড ডিপেন্ডেন্সি** প্রমাণিত (শূন্য ইমপোর্ট — অ্যাপের নিজস্ব typed `useTranslation` হুক) তাই আপগ্রেডের বদলে রিমুভ; ③ Storybook v10 অ্যালাইনমেন্ট P01-এই হয়ে গেছে | `dfb80110` |
| **ERR-P02** ✅ | react-router মেজর drift | F04-এর ① দেখুন | `dfb80110` |
| **ERR-F02** ❌ (প্ল্যান পিনড) | ১৫+ প্রতিযোগী memory store | পুরো consolidation এক সেশনে করা ঝুঁকিপূর্ণ (লাইভ Supabase ছাড়া ৮+ কল-সাইট স্পর্শ করা যাবে না) — তাই **যাচাইকৃত ইনভেন্টরি + ৫-ধাপের M3 execution blueprint** রেজিস্টারে পিন করা হয়েছে | `fddcdcf5` |

**বোনাস ফিক্স** (`0ed10df2`): ফ্রন্টএন্ডের ২টি pre-existing ফেইলিং টেস্ট ঠিক করা হয়েছে — `aiActions` টেস্ট পুরনো `/api/v1/...` পাথ আশা করছিল (ব্যাকএন্ডের আসল রুট `/admin-api/workspaces/bind-target`), আর `UserDashboard` টেস্ট ইনটেন্ট-ক্যারি-ওভার UX পরিবর্তনের পরে আপডেট হয়নি। এখন স্যুট সম্পূর্ণ সবুজ: **৫১৭/৫১৭**।

---

## ভাগ ২ — প্রজেক্ট কোথায় এখনো উন্নতি দরকার

### ২.১ স্থাপত্য (High Priority)

1. **ERR-F01-এর বাকি অংশ** — `pending_tasks`→`WAITING_APPROVAL` HITL ব্রিজ এখনো test-only; `execution_logs` রাইটার ডরম্যান্ট (`LogBatcherService.emit()` কেউই কল করে না)। ফ্রন্টএন্ডের `RunsPage` এখনো `/api/v1/missions` কনজিউম করে — `/api/v1/runs`-এ মাইগ্রেশন বাকি।
2. **ERR-F02 (M3)** — রেজিস্টারে পিন করা blueprint অনুযায়ী: ক্যানোনিকাল store = Supabase `ai_memory` (vector 384), তারপর অ্যাডাপ্টার → কনজিউমার রি-পয়েন্ট → ডিপ্রিকেশন শিম → ডিলিট।
3. **টেস্ট ডেট** — ৯৬টি skip marker (৫২ ফাইল); এর মধ্যে ৬৮টি অ্যাকশনেবল। টার্গেট <৩০।
4. **চাঙ্ক সাইজ ওয়ার্নিং** — ফ্রন্টএন্ড বিল্ডে ৬০০ kB+ চাঙ্ক; `manualChunks`/dynamic import দিয়ে ভাঙা যায়।

### ২.২ ডায়নামিকতা (যেখানে প্রজেক্ট আরও গতিশীল হতে পারে)

1. **কনফিগ-ড্রিভেন UI** — `runs/state_machine.py`-র স্টেট/ট্রানজিশন ফ্রন্টএন্ডে (`RunsPage.tsx` `STATE_BADGE`, `availableActions`) ডুপ্লিকেট; একটি `/api/v1/meta/state-machine` এন্ডপয়েন্ট থাকলে UI ব্যাকএন্ড থেকেই নেবে — নতুন স্টেট যোগ করলে ফ্রন্টএন্ড কোড বদলাতে হবে না।
2. **Skill manifest hot-reload** — skill catalog আজ ফাইল থেকে পড়ে; ডিরেক্টরি ওয়াচ (watchdog) + cache invalidation হলে deploy-blueprint সাথে সাথে UI-তে দেখা যাবে।
3. **Provider budgets এনভায়রনমেন্ট-ড্রিভেন** — `PROVIDER_TOKEN_BUDGETS` কোড-হার্ডকোডেড; এটি DB/config-চালিত করলে নতুন provider যোগ করা কোড-চেঞ্জ ছাড়াই হবে (Zero-Hardcoding Mandate অনুযায়ী)।
4. **LLM গেটওয়ে রাউটিং পলিসি ডায়নামিক** — fallback chain আজ স্ট্যাটিক; provider health/latency-ভিত্তিক ওজন থাকলে auto-adaptive হবে।

### ২.৩ স্মার্ট/ইন্টেলিজেন্স (AI-চালিত উন্নতি)

1. **Context Engine-কে স্মার্ট করা (M2-এর পরের ধাপ)** — এখন priority কলার দেয়; পরে এটি relevance-scored embedding retrieval দিয়ে প্রতিস্থাপন করা যায় — প্রতি প্রশ্নে সবচেয়ে প্রাসঙ্গিক memory/knowledge নিজে থেকেই বাছবে; বাজেট রিপোর্ট থেকে token-savings মেট্রিকও আসবে।
2. **Run-ফেব্রিক থেকে ফেইলিওর প্যাটার্ন শেখা** — canonical `Run` + ৮-ক্লাস retry classification এখন ডেটা জমা হচ্ছে; একটি পিরিয়ডিক অ্যানালাইজার দিয়ে "কোন workflow_key কোন provider-এ বেশি fail করে" শিখে dispatcher-এর routing/retry পলিসি নিজেই টিউন করা সম্ভব।
3. **Predictive auto-healer** — AutoHealer আজ probe-চালিত; run-ফেব্রিকের ইভেন্ট স্ট্রিমে ব্যর্থতার পূর্ব-সংকেত (error_code ক্লাস্টার) থাকলে ব্যর্থের *আগে* remediation ট্রিগার করা যায়।
4. **Marketplace-এ পার্সোনালাইজড রিকমেন্ডেশন** — ইনস্টল হিস্টরি + workspace-এর capability gap থেকে ইউজারকে skill সাজেস্ট করা।

---

## ভাগ ৩ — যাচাইয়ের প্রমাণ (এই সেশনের)

| যাচাই | ফলাফল |
|---|---|
| Backend: `tests/core/automation/` (১১ টেস্ট) | ✅ ১১/১১ |
| Backend: `tests/runs/` ইউনিট অংশ (১১৩) | ✅ ১১৩ পাস (১৭টি asyncpg/Postgres এনভায়রনমেন্ট এরর — স্যান্ডবক্সে Postgres নেই, আমাদের পরিবর্তনের আগেও ছিল) |
| Backend: `tests/context_engine/` (৯ নতুন) | ✅ ৯/৯ |
| Backend: `tests/api/test_api_chat.py` | ✅ ৪/৪ (প্রম্পট শেপ backward-compatible প্রমাণিত) |
| Backend: `ruff check` + `ruff format` | ✅ পরিষ্কার |
| Frontend: `tsc --noEmit` | ✅ পরিষ্কার |
| Frontend: সম্পূর্ণ vitest স্যুট | ✅ **৫১৭/৫১৭** (আগে ৫১৫/৫১৭) |
| Frontend: `vite build` (প্রোডাকশন) | ✅ সফল |
| ৮টি কমিট সরাসরি main-এ পুশড | ✅ `9678bfeb…fddcdcf5` |

---

## ভাগ ৪ — পরবর্তী সেশনের জন্য সুপারিশ (অগ্রাধিকার ক্রমে)

1. **M3 ব্লুপ্রিন্ট চালু** (রেজিস্টারের ERR-F02 এন্ট্রি) — ধাপ ১–২ (protocol + Postgres/Supabase অ্যাডাপ্টার) লো-রিস্ক দিয়ে শুরু।
2. **F01 ফলো-আপ** — HITL `pending_tasks`→run ব্রিজ + `RunsPage`-কে `/api/v1/runs`-এ রি-পয়েন্ট।
3. **স্কিপড টেস্ট ট্রায়াজ** — ৯৬ → <৩০।
4. **Context Engine v2** — embedding-relevance scoring + token-savings মেট্রিক।
5. **State-machine meta API** — UI-কে ডায়নামিক করতে।
