# SupremeAI — Enterprise-Grade রোডম্যাপ
**তারিখ:** ২০ আগস্ট, ২০২৬ | ভিত্তি: আপলোড করা কোডবেস সরাসরি বিশ্লেষণ + কয়েক সপ্তাহের আগের audit history

এই ডকুমেন্ট শুধু "কী ভুল আছে" তার তালিকা না — একটা **বাস্তবসম্মত, ধাপে-ধাপে ক্রম**, যাতে প্রতিটা ধাপ আগেরটার উপর ভিত্তি করে দাঁড়ায় এবং প্রতিটা ধাপ শেষে সিস্টেম আরও স্থিতিশীল হয়, আরও ভঙ্গুর না।

---

## এই মুহূর্তে যেখানে দাঁড়িয়ে (সততার সাথে)

**যা ইতিমধ্যে ভালো — এটা শূন্য থেকে শুরু না:**
- Deployment architecture সত্যিই সরল হয়েছে (৩টা স্পষ্ট সার্ভিস: backend, scraper, frontend)
- CI-তে `reusable-*.yml` প্যাটার্ন ব্যবহার করা হয়েছে (reusable-backend, reusable-frontend, reusable-deploy, reusable-audit ইত্যাদি) — এটা genuinely enterprise-grade CI ডিজাইন প্যাটার্ন (DRY, composable)
- Observability-এর একটা ভিত্তি আছে (OpenTelemetry integration, ১৫টা observability/monitoring মডিউল)
- বেশ কিছু আগের security regression (hardcoded Render ID, SSL bypass, leaked secret) ইতিমধ্যে ঠিক হয়ে গেছে

**যা এখনো "hobby-to-enterprise" gap তৈরি করছে:**
- Coverage gate **সম্পূর্ণ সরিয়ে ফেলা হয়েছে** (CI-এর কোথাও `cov-fail-under` নেই আর) — মানে এখন কোনো automated guarantee নেই যে নতুন কোড টেস্ট করা হচ্ছে
- ৩টা প্রতিযোগী "agent system" এখনো একসাথে আছে (৫০ ফাইল `agents/` বনাম ১১ ফাইল `tools/ai_agents/`)
- Module নাম সংঘর্ষ এখনো আছে (`config.py` ৩ বার, `llm_gateway.py` ২ বার, `evolution` ৩ বার)
- মাত্র **১৬টা** route file (মোট ১১০টার মধ্যে) standard `Depends(get_current_user)` প্যাটার্ন ব্যবহার করে — বাকিগুলো হয় ইচ্ছাকৃতভাবে public, নাহলে ভিন্ন/অসংগত auth প্যাটার্ন ব্যবহার করছে, যাচাই করা হয়নি
- ১৭টা top-level markdown ট্র্যাকিং ফাইল — single source of truth নেই

---

## Phase 0 — Freeze & Stabilize (১-২ সপ্তাহ)
**লক্ষ্য: নতুন কিছু যোগ না করে, যা আছে সেটাকে predictable বানানো।**

| # | কাজ | কেন প্রথমে |
|---|---|---|
| 0.1 | নতুন ফিচার PR সাময়িক বন্ধ (bug fix/cleanup ছাড়া) | Enterprise-grade মানে "কম কিন্তু নির্ভরযোগ্য ফিচার" — এখন যোগ করলে cleanup আরও কঠিন হবে |
| 0.2 | CI-কে queue করুন, cancel না — concurrency group ঠিক করা যাতে দ্রুত পরপর push একে অপরকে থামিয়ে না দেয় | আগের audit-এ ২৪ মিনিটে ৬টা cancelled run পাওয়া গেছে — মানে কিছুই আসলে verify হচ্ছে না |
| 0.3 | Coverage gate **আবার চালু করুন** — শুরুতে কম threshold (যেমন ২৫%) দিয়ে, শুধু measure+report করার জন্য, block না করার জন্য | বর্তমানে zero visibility — এটা ছাড়া বাকি সব ধাপ "অন্ধভাবে" করা হবে |
| 0.4 | একটা single `STATUS.md` তৈরি করুন যেটা বাকি ১৭টা ট্র্যাকিং ফাইলের "সত্যিকারের" অবস্থা এক জায়গায় দেখায় | Decision নেওয়ার আগে জানতে হবে আসলে কী অবস্থা |

---

## Phase 1 — Dead Code Elimination (১ সপ্তাহ)
**লক্ষ্য: যা ব্যবহারই হয় না, সেটা সরিয়ে codebase-কে ছোট ও বোধগম্য করা। এই ধাপে ঝুঁকি প্রায় শূন্য (verified zero-usage)।**

| # | কাজ | Verified প্রমাণ |
|---|---|---|
| 1.1 | `evolution/`, `p2p/`, `scout/`, `skills/` (top-level) মুছুন বা `archive/`-এ সরান | বাইরে থেকে import: ০ |
| 1.2 | `agents/` (৫০ ফাইল) থেকে unused ৩টা বাদে বাকি ক্লাস মুছুন, `tools/ai_agents/`-কে official সিস্টেম ঘোষণা করুন | নিজের কোডেই কমেন্ট আছে যে `agents/` ভাঙা ছিল, `tools/ai_agents/`-এ migrate করা হয়েছিল |
| 1.3 | `engine/`, `byoc/`, `adaptive_engine/` deep-dive করে কোন অংশ genuinely বাকি অংশের সাথে যুক্ত, কোনটা orphan তা আলাদা করুন | আংশিক ব্যবহৃত (১-৩টা বাইরের কল) |
| 1.4 | Root-এ ১৭টা markdown ফাইল → পড়ে দেখুন কোনগুলো একই তথ্য repeat করছে, ৩-৪টায় নামিয়ে আনুন (`ARCHITECTURE.md`, `ROADMAP.md`, `DECISION_LOG.md`, বাকিগুলো archive) | Content overlap এখনো verify করা হয়নি — প্রথম কাজ |

---

## Phase 2 — Structural Cleanup (২ সপ্তাহ)
**লক্ষ্য: নাম-সংঘর্ষ ও অস্পষ্ট গঠন ঠিক করা, যাতে নতুন কেউ (মানুষ বা AI) কোডে বিভ্রান্ত না হয়।**

| # | কাজ |
|---|---|
| 2.1 | `config.py` (৩ জায়গা) → unique নাম দিন (`core/config.py` থাকুক, বাকিগুলো `route_config.py`, `admin_config_routes.py` ইত্যাদি) |
| 2.2 | `llm_gateway.py` (২ জায়গা) → একইভাবে unique নাম |
| 2.3 | `evolution` (৩ জায়গা) → একটাকে canonical রেখে বাকিগুলো merge বা rename — এটাই ছিল mypy-এর "duplicate module" সমস্যার আসল কারণ, যেটা CI-তে skip করে রাখা হয়েছিল |
| 2.4 | `config/` বনাম `configs/` — একটাকে অন্যটায় merge বা স্পষ্ট নাম দিন (যেমন `agent_config/` ও `ml_training_data/`) |
| 2.5 | `core/tier8/`-এর নাম কী বোঝায় ডকুমেন্ট করুন বা বোধগম্য নামে rename করুন |

---

## Phase 3 — Security & Auth Consistency Audit (২ সপ্তাহ)
**লক্ষ্য: "প্রতিটা এন্ডপয়েন্ট কেন protected বা public তা স্পষ্টভাবে জানা যায়" — অনুমান না।**

| # | কাজ |
|---|---|
| 3.1 | ১১০টা route file-এর প্রতিটা audit করে ৩ ভাগে ভাগ করুন: (a) ইচ্ছাকৃত public, (b) standard `Depends(get_current_user)` ব্যবহার করা উচিত, (c) admin-only guard দরকার |
| 3.2 | যেসব endpoint custom/অসংগত auth check ব্যবহার করছে, সেগুলো standard dependency-তে migrate করুন |
| 3.3 | Secret rotation checklist তৈরি করুন — আগের audit-এ leaked secret পাওয়া গিয়েছিল (এখন সম্ভবত ঠিক হয়েছে, কিন্তু git history-তে এখনো থাকতে পারে) — `git log -p` দিয়ে scan করে দেখা উচিত |
| 3.4 | Rate-limiting ও honeypot middleware-এর মতো সুরক্ষা layer-গুলো প্রতিটা route-এ সমানভাবে প্রযোজ্য হচ্ছে কিনা যাচাই |

---

## Phase 4 — Testing & Observability Maturity (৩-৪ সপ্তাহ)
**লক্ষ্য: "deploy করার আগে জানা যায় এটা কাজ করবে কিনা" — এটাই enterprise-grade-এর মূল সংজ্ঞা।**

| # | কাজ |
|---|---|
| 4.1 | Coverage gate ধাপে ধাপে বাড়ান: ২৫% → ৪০% → ৬০% → লক্ষ্য ৮০%+ (এক লাফে না — প্রতি ধাপে ১-২ সপ্তাহ গ্যাপ) |
| 4.2 | সবচেয়ে ঝুঁকিপূর্ণ পথ (auth, payment/billing, admin actions) আগে টেস্ট কভার করুন, generic CRUD পরে |
| 4.3 | OpenTelemetry integration সম্পূর্ণ করুন — request tracing, error rate dashboard, latency percentile |
| 4.4 | একটা "smoke test after deploy" pipeline নিশ্চিত করুন যেটা প্রতিটা প্রোডাকশন deploy-এর পর আসলে `/health` এবং কয়েকটা core endpoint সত্যিই কাজ করছে কিনা check করে |

---

## Phase 5 — Documentation & Governance (চলমান, সমান্তরালে)
**লক্ষ্য: জ্ঞান কোডে বা ছড়ানো ডকুমেন্টে আটকে না থেকে, একটা predictable জায়গায় থাকা।**

| # | কাজ |
|---|---|
| 5.1 | একটা single `ARCHITECTURE.md` — এই রোডম্যাপে যা ম্যাপ করা হলো সেটাই ভিত্তি ধরে, বাস্তব অবস্থা প্রতিফলিত করে (কল্পিত না) |
| 5.2 | প্রতিটা বড় merge-এর আগে একটা ছোট checklist (`DEPLOYMENT_CHECKLIST.md` ইতিমধ্যে আছে — এটা বাস্তবসম্মত ও ছোট রাখুন, বিশাল হয়ে গেলে কেউ পড়বে না) |
| 5.3 | `KNOWN_ISSUES.md`/`FAILING_TESTS.md`-এর মতো ট্র্যাকিং ডকুমেন্ট নিয়মিত (সাপ্তাহিক) refresh করার একটা habit — না হলে এগুলো নিজেই stale হয়ে বিভ্রান্তির উৎস হয়ে যায় (আগের audit-এ এটাই ঘটেছিল) |

---

## কেন এই ক্রম

- **Phase 0-2 আগে কারণ:** এগুলো ছাড়া Phase 3-5-এ যা করবেন সেটাও বিভ্রান্তির উপর দাঁড়াবে (কোন `config.py` ঠিক করছেন? কোন `agents` সিস্টেম টেস্ট করছেন?)
- **Dead code delete করা রিফ্যাক্টরের আগে, কারণ:** কম কোড মানে কম জায়গায় bug লুকানোর সুযোগ — প্রতিটা পরের ধাপ দ্রুত হবে
- **Security Phase 3-এ, শেষে না:** কারণ Phase 1-2-এ ফাইল সরানো/rename করলে auth-related import path-ও বদলাবে — একসাথে দুইবার কাজ এড়ানোর জন্য security audit তার পরেই

---

## বাস্তবসম্মত সময়রেখা
মোট **~১০-১২ সপ্তাহ** যদি একটানা focus করা যায় (Phase 5 বাদে, যেটা চলমান থাকবে)। এটা এক ব্যক্তির (বা AI-সহায়তায় একজনের) জন্য realistic — একসাথে সব ধাপ শুরু করলে ঠিক সেই একই সমস্যা আবার হবে যেটা এখন আছে।

---

**পরের পদক্ষেপ:** Phase 0.2 (CI queue/concurrency fix) আর 0.3 (coverage gate ফিরিয়ে আনা) — এই দুটো আজই শুরু করা যায়, ঝুঁকি নেই, আর বাকি সব ধাপের ভিত্তি তৈরি করে। শুরু করব?
