# SupremeAI কোডবেস — সম্পূর্ণ ফাইল বিশ্লেষণ ও রিফ্যাক্টরিং রিপোর্ট

> **রিপোজিটরি:** https://github.com/paykaribazaronline/supremeai/  
> **কমিট (বিশ্লেষণ বেস):** `61c9a49`  
> **তৈরির তারিখ:** 2026-09-07 08:17 (Asia/Dhaka)  
> **পদ্ধতি:** ১৫টি ডোমেইন-ভিত্তিক প্যারালাল AI এজেন্ট প্রতিটি ফাইলের কন্টেন্ট সরাসরি পড়ে বিশ্লেষণ করেছে (নাম দেখে নয় — আসল কোড/কনটেন্ট বুঝে)।

---

## ১. এক্সিকিউটিভ সামারি

এই রিপোর্টে রিপোজিটরির **প্রতিটি ফাইলের** জন্য ৬টি তথ্য দেওয়া হয়েছে: বর্তমান নাম, বর্তমান অবস্থান, কন্টেন্ট সারাংশ (ফাইলটি আসলে কী করে), সাজেস্টেড নাম, সাজেস্টেড অবস্থান এবং কারণ। মূল লক্ষ্য — **নামকরণ ও আসল মেকানিজমের অমিল (Semantic Mismatch)** দূর করে কোডবেসের ওপর আস্থা পুনরুদ্ধার করা এবং 'ডেড কোড' বলে মনে হওয়া ফাইলগুলোর আসল উপযোগিতা পরিষ্কার করা।

### গ্লোবাল পরিসংখ্যান

| মেট্রিক | সংখ্যা |
|---|---|
| মোট বিশ্লেষিত ফাইল (তালিকাভুক্ত) | **2,755** |
| সফলভাবে বিশ্লেষিত | **2,755** |
| অনুপস্থিত/স্কিপ | 0 |
| রিনেম প্রস্তাব (নাম পরিবর্তন) | **505** |
| স্থানান্তর প্রস্তাব (অবস্থান পরিবর্তন) | **446** |
| ⚠️ সেমান্টিক মিসম্যাচ চিহ্নিত | **137** |
| ডিলিট/আর্কাইভ প্রার্থী (ডেড কোড, ডুপ্লিকেট, এককালীন স্ক্রিপ্ট) | **~169** |

### সবচেয়ে গুরুত্বপূর্ণ ১২টি ফাইন্ডিং (ক্রস-ব্যাচ)

1. **⚠️ নাম vs কাজের বড় অমিল:** `messaging/events.py` আসলে Firebase Auth init; `immune_system.py` আসলে AST security scanner; `bandwidth_optimizer` আসলে prompt compressor; `ai_federation_protocol` আসলে in-memory skill registry; `brain/api_router.py` আসলে HTTP রাউটার নয় — in-process handler registry; `admin/god.py` আসলে একটি সাধারণ approval guard।
2. **⚠️ ব্র্যান্ড/সায়েন্স-ফিকশন প্রিফিক্স মহামারি:** `tier8/`, `tier_s_`, `supreme_`, `superai_`, `nexus`, `quantum`, `genesis`, `morphic`, `prophet`, `mage`, `god` — এদের অধিকাংশের ভেতরে সাধারণ, বাস্তব কাজ লুকিয়ে আছে (যেমন tier8 প্যাকেজটি আসলে meta-agent coordination)।
3. **ডুপ্লিকেট ইমপ্লিমেন্টেশন ক্লাস্টার:** ৫টি ক্যাশ, ২টি AST scanner, ৩টি InputSanitizer, ২টি swarm orchestrator, ২টি agent-evolution engine, ৩টি প্যারালাল env-validator, ৩টি রাউটার রেজিস্ট্রি, ৪-ওয়ে ডুপ্লিকেট চ্যাট/স্ট্রিম এন্ডপয়েন্ট, ৪+ মডেল-রাউটিং লেয়ার, ৩টি i18n ব্যবস্থা, ২টি থিম সিস্টেম।
4. **ডেপ্রিকেশন শিম জমা:** ১৩+ অভিন্ন ২৫-লাইনের শিম (batch 01) + আরও কয়েকটি (rate_limiter, router, tenant_db...) — মাইগ্রেশন শেষ হলে সব ডিলিট করতে হবে; `logging_config` সবার শেষে (প্রায় সর্বত্র ইমপোর্টেড)।
5. **আনওয়্যার্ড ফিচার-ব্লক:** সম্পূর্ণ `frontend/src/commandcenter/` ট্রি (৭৪ ফাইল, 'AETHEL Command Center')-এর কোনো বাইরের ইমপোর্টার/রুট নেই; ১৭+ অরফান কম্পোনেন্ট; stories/ ডিরেক্টরির ২০টি ফাইলই স্টক টেমপ্লেট।
6. **ভাঙা মাইগ্রেশন চেইন:** Alembic-এ ডুপ্লিকেট revision ID `a1b2c3d4e5f6` + ৫টি হাতে-লেখা placeholder ID; সমান্তরাল দুটি মাইগ্রেশন সিস্টেম (alembic বনাম database/migrations/*.sql, ১১–১৪ নম্বরের মধ্যে গ্যাপ)।
7. **সিকিউরিটি রিস্ক:** ৬টি Infisical স্ক্রিপ্টে একই clientId/clientSecret হার্ডকোডেড; `usePlugins`-এ খালি Bearer টোকেন; `bangla_ai_connector`-এ example.com হার্ডকোড; ৩টি হার্ডকোডেড Cloud Run URL।
8. **কম্পাইল-ব্রেকিং বাগ:** `plugins/MCPConnector.tsx`-এ `'Authorization': Bearer` সিনট্যাক্স এরর — ফাইলটি কম্পাইলই হয় না; `unified_db_manager.py`-এ ভাঙা `SQLiteStore` ইমপোর্ট; `middleware/db_optimization_middleware.py` ইমপোর্ট করলেই ক্র্যাশ।
9. **ভুয়া/ভাঙা অ্যাসেট:** `docs/supremeai_roadmap.png` আসলে ১৩১-বাইট Git LFS পয়েন্টার; রুটে ৩টি ১৩০-বাইট placeholder PNG + ০-বাইট flowchart.png; `reports/knowledge_cards_v2_lifecycle.json` ভাঙা JSON।
10. **টেস্ট মিসলোকেশন:** `backend/tests/core/`-এ api.routes/memory/services/brain/tools/database-এর টেস্ট সব পার্ক করা; ৭টি Playwright e2e স্পেক ভুলে `backend/tests/e2e/`-এ; pytest import-conflict ঝুঁকিতে ডুপ্লিকেট basename `test_swarm_orchestrator.py`; ডেড টেস্ট ফাইল যেগুলো CI কখনো কালেক্টই করে না।
11. **প্ল্যাটফর্ম-মিক্স:** VS Code extension ডিরেক্টরিতে ৭টি Java (Spring Boot + Firestore) ফাইল — Python backend-এর ডুপ্লিকেট; frontend-এ Next.js-লেফটওভার `src/app/page.tsx` (Vite অ্যাপে অরাউটেড)।
12. **স্টেল কনফিগ:** root tsconfig/.knip অস্তিত্বহীন `./src` রেফার করে; playwright testDir `./tests/e2e` নেই; package.json docker স্ক্রিপ্ট অস্তিত্বহীন docker-compose.yml রেফার করে; ৬টি AI-ignore ফাইল byte-identical ডুপ্লিকেট।

---

## ২. ডোমেইন-ভিত্তিক সামারি (১৫টি দল)

| ব্যাচ | ডোমেইন (দল) | ফাইল | রিনেম | স্থানান্তর | ⚠️ মিসম্যাচ |
|---|---|---|---|---|---|
| ০১ | Backend Core (অংশ ক) | 173 | 24 | 11 | 6 |
| ০২ | Backend Core (অংশ খ) | 172 | 21 | 10 | 11 |
| ০৩ | Backend API ও Services | 202 | 47 | 21 | 11 |
| ০৪ | Backend Tests (অংশ ক) | 186 | 46 | 44 | 8 |
| ০৫ | Backend Tests (অংশ খ) | 185 | 22 | 24 | 8 |
| ০৬ | Backend Tools ও Scripts | 152 | 25 | 26 | 6 |
| ০৭ | Agent, Brain, Memory ও Evolution সিস্টেম | 138 | 22 | 21 | 19 |
| ০৮ | Backend Models, Database ও অবশিষ্ট মডিউল | 255 | 23 | 15 | 8 |
| ০৯ | Frontend Components ও Stories | 210 | 60 | 47 | 12 |
| ১০ | Frontend Pages, Store ও Services | 172 | 48 | 6 | 11 |
| ১১ | Frontend Infrastructure (hooks, lib, utils, contexts) | 105 | 27 | 26 | 2 |
| ১২ | Repository Scripts (CI, DevOps, Analysis) | 257 | 31 | 87 | 0 |
| ১৩ | Tools, Packages ও Extensions | 239 | 32 | 26 | 8 |
| ১৪ | Docs, Specs, Reports ও Infrastructure Config | 241 | 58 | 57 | 27 |
| ১৫ | Repository Root ফাইল | 68 | 19 | 25 | 0 |
| — | **মোট** | **2755** | **505** | **446** | **137** |

---

## ৩. প্রস্তাবিত ফেজড মাইগ্রেশন প্ল্যান

রিনেম/স্থানান্তর একসাথে করলে ইমপোর্ট-ব্রেকেজ হবে। নিচের ক্রমে গেলে ঝুঁকি সর্বনিম্ন থাকবে:

### Phase 0 — ম্যাপিং ও ডকস্ট্রিং (রিস্ক: শূন্য, ১–২ দিন)

- এই রিপোর্টের টেবিল অনুযায়ী প্রতিটি মিসম্যাচ ফাইলের শুরুতে **এক-লাইনের docstring** যোগ করুন: `"""Production role: <আসল কাজ>. Legacy name: <পুরনো নাম>. See refactor report batch NN."""`
- ফল: নতুন ডেভেলপার/AI অডিট আর নাম দেখে বিভ্রান্ত হবে না, অথচ কোনো ইমপোর্ট ভাঙবে না।

### Phase 1 — ডেড কোড অপসারণ (রিস্ক: কম, ২–৩ দিন)

- ~169টি ডিলিট/আর্কাইভ প্রার্থী: deprecation শিমগুলো (শেষে logging_config), one-off fix_*/hotfix_* রুট স্ক্রিপ্ট, স্টক Storybook stories/, অরফান কম্পোনেন্ট, placeholder PNG, byte-identical AI-ignore ডুপ্লিকেট।
- প্রতিটি ডিলিটের আগে importer-যাচাই (grep) জরুরি — টেবিলের 'কারণ' কলামে যাচাইকৃত তথ্য আছে।

### Phase 2 — ডুপ্লিকেট কনসোলিডেশন (রিস্ক: মাঝারি, ১ সপ্তাহ)

- প্রতি ডুপ্লিকেট ক্লাস্টারে **ক্যানোনিকাল একটি** রাখুন (রিপোর্টে প্রতি ক্লাস্টারের ক্যানোনিকাল চিহ্নিত): ক্যাশ ×৫→১, InputSanitizer ×৩→১, রাউটার রেজিস্ট্রি ×৩→১ (routers.py), চ্যাট এন্ডপয়েন্ট ×৪→১, মডেল-রাউটার ×৪→১, থিম সিস্টেম ×২→১, i18n ×৩→১।
- Alembic চেইন ফিক্স: ডুপ্লিকেট revision ID সংশোধন এই ফেজেই করুন — নইলে নতুন মাইগ্রেশনই চলবে না।

### Phase 3 — রিনেম (রিস্ক: মাঝারি, ১–২ সপ্তাহ)

- 505টি রিনেম প্রস্তাব — প্রতিটির সাথে codemod (grep+sed বা IDE refactor) দিয়ে সব ইমপোর্ট আপডেট।
- ক্রম: (ক) পাবলিক API সারফেস নয় এমন internal module, (খ) tests, (গ) সবশেষে widely-imported মডিউল।
- প্রতি PR-এ এক ডোমেইন (এক ব্যাচ) — কখনোই সব একসাথে নয়।

### Phase 4 — স্থানান্তর ও ডিরেক্টরি রি-স্ট্রাকচার (রিস্ক: উঁচু, ২–৩ সপ্তাহ)

- 446টি স্থানান্তর: tests মিরর-স্ট্রাকচার (unit/integration/e2e), feature-first frontend (features/<feature>/), frontend commandcenter → admin-console (আগে wire-আপ সিদ্ধান্ত নিন: রুট যোগ করবেন নাকি আর্কাইভ), backend tools → services/llm/ ইত্যাদি।
- git mv ব্যবহার করুন (history সংরক্ষণ) এবং প্রতিটি মুভের পরে CI সবুজ নিশ্চিত করুন।

---

## ৪. নামকরণ কনভেনশন (ভবিষ্যতের জন্য স্ট্যান্ডার্ড)

| ধরন | কনভেনশন | উদাহরণ |
|---|---|---|
| Python মডিউল | snake_case, কাজ-নির্দেশক | `agent_skill_coordination.py` |
| Python টেস্ট | `test_<মূল মডিউল>.py` | `test_meta_agent_services.py` |
| React কম্পোনেন্ট (.tsx) | PascalCase = এক্সপোর্টেড নাম | `AdminBrowserPanel.tsx` |
| TS util/store/hook | kebab-case / use প্রিফিক্স | `api-bridge.ts`, `useWorkspaceSettings.ts` |
| Shell স্ক্রিপ্ট | kebab-case | `system-health-check.sh` |
| Docs | kebab-case, টপিক-নির্দেশক | `system-architecture-blueprint.md` |
| নিষিদ্ধ শব্দ | tier, nexus, quantum, genesis, apex, omega, oracle, titan, god, supreme, master, evolution (ব্যবহার করলে শুধু আসল ML evolution-এ) | — |

---

## ৫. ঝুঁকি ম্যাট্রিক্স (রিফ্যাক্টরিং চলাকালীন)

| ঝুঁকি | প্রভাবিত এলাকা | প্রশমন |
|---|---|---|
| ইমপোর্ট-ব্রেকেজ | রিনেম/মুভ চলাকালীন সব ব্যাচ | প্রতি পরিবর্তনে grep-ভিত্তিক importer যাচাই + CI |
| Alembic চেইন ভাঙা | backend/alembic_migrations | Phase 2-এ revision ID ফিক্স না করে নতুন মাইগ্রেশন নয় |
| হার্ডকোডেড পাথ/সিক্রেট | scripts/ (Windows F:\, c:\Users\n\), Infisical creds | ডিলিট/আর্কাইভ করুন; সিক্রেট রোটেট করুন |
| ডুপ্লিকেট basename (pytest conflict) | test_swarm_orchestrator.py ×২ | মুভের সময় __init__.py/unique নাম নিশ্চিত করুন |
| আনওয়্যার্ড ফিচার | frontend commandcenter (৭৪ ফাইল) | রি-স্ট্রাকচারের আগে wire বা archive সিদ্ধান্ত |
| পারফরম্যান্স | logging_config সবশেষে মাইগ্রেট | শিম রাখুন যতক্ষণ সব কলসাইট আপডেট হয় |

---

## ৬. বিস্তারিত ফাইল-বাই-ফাইল বিশ্লেষণ (১৫টি ব্যাচ)

নিচের প্রতিটি ব্যাচ-সেকশনে প্রতিটি ফাইলের সম্পূর্ণ রেকর্ড আছে। কলাম সংকেত: **কন্টেন্ট সারাংশ** = ফাইলটি আসলে যা করে; **⚠️** = নাম ও কাজের সেমান্টিক মিসম্যাচ; **অপরিবর্তিত ✅** = বর্তমান নাম/অবস্থান ঠিক আছে।

**সূচি:**
- [ব্যাচ ০১ — Backend Core (অংশ ক)](#ব্যাচ-০১)
- [ব্যাচ ০২ — Backend Core (অংশ খ)](#ব্যাচ-০২)
- [ব্যাচ ০৩ — Backend API ও Services](#ব্যাচ-০৩)
- [ব্যাচ ০৪ — Backend Tests (অংশ ক)](#ব্যাচ-০৪)
- [ব্যাচ ০৫ — Backend Tests (অংশ খ)](#ব্যাচ-০৫)
- [ব্যাচ ০৬ — Backend Tools ও Scripts](#ব্যাচ-০৬)
- [ব্যাচ ০৭ — Agent, Brain, Memory ও Evolution সিস্টেম](#ব্যাচ-০৭)
- [ব্যাচ ০৮ — Backend Models, Database ও অবশিষ্ট মডিউল](#ব্যাচ-০৮)
- [ব্যাচ ০৯ — Frontend Components ও Stories](#ব্যাচ-০৯)
- [ব্যাচ ১০ — Frontend Pages, Store ও Services](#ব্যাচ-১০)
- [ব্যাচ ১১ — Frontend Infrastructure (hooks, lib, utils, contexts)](#ব্যাচ-১১)
- [ব্যাচ ১২ — Repository Scripts (CI, DevOps, Analysis)](#ব্যাচ-১২)
- [ব্যাচ ১৩ — Tools, Packages ও Extensions](#ব্যাচ-১৩)
- [ব্যাচ ১৪ — Docs, Specs, Reports ও Infrastructure Config](#ব্যাচ-১৪)
- [ব্যাচ ১৫ — Repository Root ফাইল](#ব্যাচ-১৫)

---

## ব্যাচ ০১ — Backend Core (অংশ ক)
**ব্যাচ:** 01 | **তালিকাভুক্ত:** 173 | **বিশ্লেষিত:** 173 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 22 | **স্থানান্তর প্রস্তাব:** 10 | **⚠️ সেমান্টিক মিসম্যাচ:** 6

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| RETRY_HANDLER_DOCS.md | backend/core/RETRY_HANDLER_DOCS.md | retry_handler ডেকোরেটরের বাংলা ডকুমেন্টেশন (ব্যাকঅফ, জিটার, বাজেট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টার্গেট মডিউলের পাশেই ডক রাখা যুক্তিযুক্ত |
| _INDEX.md | backend/core/_INDEX.md | backend/core ফোল্ডারের AI-রিডেবল ফাইল ইনডেক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নেভিগেশন ইনডেক্স, নাম ও অবস্থান ঠিক |
| __init__.py | backend/core/__init__.py | কোর প্যাকেজ init — রোডম্যাপ কম্পোনেন্ট এক্সপোর্ট, guarded imports | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ ইনিশিয়ালাইজার, নাম উপযুক্ত |
| wcag_compliance.py | backend/core/accessibility/wcag_compliance.py | WCAG 2.1 AA কমপ্লায়েন্স চেক (কনট্রাস্ট, HTML, ARIA) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| adaptive_optimizer.py | backend/core/adaptive_optimizer.py | বেঞ্চমার্ক ফলাফল থেকে অটো-টিউনিং ও স্ট্র্যাটেজি অ্যাডাপটেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম কনটেন্টের সাথে মেলে |
| admin_god.py | backend/core/admin_god.py | god-mode প্রিভিলেজড কন্ট্রোল + immutable audit log + RBAC | admin_god_mode.py | অপরিবর্তিত ✅ | "god_mode" ফিচারনাম স্পষ্ট করতে |
| admin_routes.py | backend/core/admin_routes.py | অ্যাডমিন API: TOTP/JWT/Firebase লগইন, ফ্রি-টিয়ার, GCP স্ট্যাট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| advanced_reasoning.py | backend/core/advanced_reasoning.py | বহু-প্রকার রিজনিং ইঞ্জিন (ডিডাক্টিভ, ইনডাক্টিভ, কজাল ইত্যাদি) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_factory.py | backend/core/agent_factory.py | LLM দিয়ে Python-স্ক্রিপ্ট এজেন্ট জেনারেট করে DB-তে রেজিস্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_registry.json | backend/core/agent_registry.json | প্রি-কনফিগারড এজেন্ট ডেফিনিশন (guardian, research_assistant) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডেটা ফাইল, নাম ঠিক |
| agent_supervisor.py | backend/core/agent_supervisor.py | ব্যাকগ্রাউন্ড এজেন্টের lifecycle, হেলথ মনিটর, অটো-রিস্টার্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agents/__init__.py | backend/core/agents/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| framework/__init__.py | backend/core/agents/framework/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_department.py | backend/core/agents/framework/agent_department.py | CodingAgent/ReviewAgent — role-prompt ভিত্তিক এজেন্ট (singular টুইন) | (মার্জ) agent_departments.py | অপরিবর্তিত ✅ | singular/plural নিকট-ডুপ্লিকেট, একত্রিত করুন |
| agent_departments.py | backend/core/agents/framework/agent_departments.py | AgentDepartment — ৬ রোলের prompt executor (RACE/CLEAR ইত্যাদি) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিকাল ফাইল, নাম ঠিক |
| crewai_agents.py | backend/core/agents/framework/crewai_agents.py | হোমমেড CrewAgent/SupremeCrew ইমিটেশন — CrewAI লাইব্রেরি নয় | simple_crew_agents.py | অপরিবর্তিত ✅ | নাম ভুল লাইব্রেরি বোঝায় |
| langgraph_agent.py | backend/core/agents/framework/langgraph_agent.py | SupremeOrchestrator — টাস্ক রাউটিং, VPN রোটেশন; LangGraph নেই | autonomous_task_orchestrator.py | অপরিবর্তিত ✅ | ⚠️ নামে LangGraph, কোডে সম্পূর্ণ অসম্পৃক্ত |
| task_runner_agent.py | backend/core/agents/framework/task_runner_agent.py | AutonomousAgent — প্ল্যান তৈরি ও স্টেপ-বাই-স্টেপ এক্সিকিউশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| legacy/__init__.py | backend/core/agents/legacy/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| system_health_agent.py | backend/core/agents/legacy/system_health_agent.py | ব্যাকগ্রাউন্ড সিস্টেম হেলথ মনিটরিং এজেন্ট বেস ক্লাস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | legacy অবস্থানে নাম ঠিক |
| live/__init__.py | backend/core/agents/live/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| benchmark_agent.py | backend/core/agents/live/benchmark_agent.py | প্রোভাইডারজুড়ে বেঞ্চমার্ক প্রম্পট চালিয়ে লেটেন্সি/কস্ট মাপে | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| browser_agent.py | backend/core/agents/live/browser_agent.py | Playwright ব্রাউজার নিয়ন্ত্রণ + fallback স্ক্র্যাপার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| computer_agent.py | backend/core/agents/live/computer_agent.py | লোকাল কমান্ড এক্সিকিউশন ও ফাইল অপারেশন (সেফগার্ডসহ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vision_agent.py | backend/core/agents/live/vision_agent.py | EasyOCR দিয়ে ছবি থেকে টেক্সট এক্সট্র্যাকশন ও স্ট্রাকচার | ocr_agent.py | অপরিবর্তিত ✅ | মূল কাজ OCR, নাম বিস্তৃত |
| vector_store.py | backend/core/ai_memory/vector_store.py | ফ্রি-টিয়ার অপ্টিমাইজড Supabase pgvector স্টোর (ব্যাচ, স্ট্রিমিং) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| app.py | backend/core/app.py | FastAPI অ্যাপ ইনস্ট্যান্স + রাউটার রেজিস্ট্রেশন + রুট এন্ডপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| app_builder.py | backend/core/app_builder.py | create_app() — মিডলওয়্যার চেইন, Sentry, DI কনফিগারেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| automation/__init__.py | backend/core/automation/__init__.py | অটোমেশন অ্যাবস্ট্র্যাকশন লেয়ার প্যাকেজ docstring | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| dispatcher.py | backend/core/automation/dispatcher.py | ইভেন্ট প্রোভাইডার নির্বাচন ও idempotent dispatch | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| execution_recorder.py | backend/core/automation/execution_recorder.py | dispatch lifecycle-এর best-effort DB পার্সিস্টেন্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| idempotency.py | backend/core/automation/idempotency.py | LRU+TTL ভিত্তিক idempotency স্টোর প্রোটোকল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| interfaces.py | backend/core/automation/interfaces.py | AutomationProvider প্রোটোকল কনট্র্যাক্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| models.py | backend/core/automation/models.py | AutomationEvent/Result/Status Pydantic মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| registry.py | backend/core/automation/registry.py | মেটাডেটা-ড্রিভেন workflow রেজিস্ট্রি (timeout, retry, policy) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| autonoguard_engine.py | backend/core/autonoguard_engine.py | সিকিউরিটি গভর্নেন্স: JIT OTP, AST স্ক্যান, self-healing, IP churn | security_governance_engine.py | অপরিবর্তিত ✅ | ⚠️ আবিষ্কৃত শব্দ; কাজ সিকিউরিটি গভর্নেন্স |
| base.py | backend/core/base.py | শুধু BaseSkill অ্যাবস্ট্র্যাক্ট ক্লাস — সব স্কিলের কনট্র্যাক্ট | skill_base.py | backend/core/skills/ | base.py অতি-জেনেরিক; স্কিল ডোমেইনে সরান |
| billing_plans.py | backend/core/billing_plans.py | Deprecated shim → services.billing.billing_plans | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; importer মাইগ্রেশন শেষে মুছুন |
| brand_compliance.py | backend/core/brand_compliance.py | রেসপন্স থেকে প্রোভাইডার ব্র্যান্ড উল্লেখ স্যানিটাইজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| README.md | backend/core/cache/README.md | ক্যাশ প্যাকেজের কম্পোনেন্ট বর্ণনা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ ডক, অবস্থান ঠিক |
| cache/__init__.py | backend/core/cache/__init__.py | ক্যাশ প্যাকেজ init + SimpleCacheProxy helper | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| autocache_proxy.py | backend/core/cache/autocache_proxy.py | প্রম্পট ক্যাটাগরি অনুযায়ী dynamic TTL ক্যাশ প্রক্সি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| multi_layer_cache.py | backend/core/cache/multi_layer_cache.py | ৫-স্তরের ক্যাশ অর্কেস্ট্রেশন (Redis+semantic+LRU) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| predictive_cache_engine.py | backend/core/cache/predictive_cache_engine.py | Markov chain দিয়ে পরবর্তী কুয়েরি প্রেডিকশন/প্রিওয়ার্ম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| query_cache.py | backend/core/cache/query_cache.py | LLM কুয়েরি ক্যাশ — exact + semantic dedup, Redis | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| redis_manager.py | backend/core/cache/redis_manager.py | SecureRedisManager — async Redis ইন্টারফেস, fail-closed | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| semantic_cache.py | backend/core/cache/semantic_cache.py | ভেক্টর-ভিত্তিক semantic ক্যাশ, DB-driven থ্রেশহোল্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cache_manager.py | backend/core/cache_manager.py | FreeTierCacheManager — Upstash কমান্ড-বাজেট সেভিং ক্যাশ | free_tier_cache_manager.py | backend/core/cache/ | cache/ প্যাকেজে সরান; redis_manager-এর সাথে ওভারল্যাপ |
| circuit_breaker.py | backend/core/circuit_breaker.py | CircuitBreaker রেজিলিয়েন্স প্যাটার্ন (root কপি) | অপরিবর্তিত ✅ | backend/core/resilience/ | resilience/circuit_breaker.py-র সাথে ডুপ্লিকেট, একত্র করুন |
| cloud_storage.py | backend/core/cloud_storage.py | Deprecated shim → services.storage.cloud_storage | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| code_validator.py | backend/core/code_validator.py | AI-জেনারেটেড Python/পাথ/URL ভ্যালিডেশন গেটকিপার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| competitive_kit.py | backend/core/competitive_kit.py | ১৫৪৯-লাইন মনোলিথ: personality, safety, citation, context, router | ৬টি স্বতন্ত্র মডিউলে বিভক্ত করুন | অপরিবর্তিত ✅ | মাল্টি-রেসপন্সিবিলিটি গ্র্যাব-ব্যাগ |
| config.py | backend/core/config.py | কেন্দ্রীয় Pydantic Settings — fail-fast, zero-hardcode | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | DO NOT MOVE সতর্কতা; নাম ঠিক |
| routing_policy.json | backend/core/config/routing_policy.json | LLM মডেল রাউটিং পলিসি (কমপ্লেক্সিটি→প্রায়োরিটি) | অপরিবর্তিত ✅ | backend/core/llm/ | LLM ডোমেইন অ্যাসেট; llm_gateway পাথ আপডেটসহ |
| config_cache.py | backend/core/config_cache.py | TTL ভিত্তিক in-memory ডায়নামিক কনফিগ ক্যাশ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| config_classification.py | backend/core/config_classification.py | ক্যানোনিকাল env-var মেটাডেটা রেজিস্ট্রি (১৮৭৭ লাইন specs) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম অর্থবহ; ডেটা-ভারী তবে এক দায়িত্ব |
| config_control_plane.py | backend/core/config_control_plane.py | কনফিগ হেলথ স্ন্যাপশট facade (শুধু presence, ভ্যালু নয়) | config_health.py | অপরিবর্তিত ✅ | "control plane" বাড়াবাড়ি; কাজ হেলথ রিপোর্ট |
| config_fields.py | backend/core/config_fields.py | Settings-এর Pydantic ফিল্ড ডিক্লারেশন mixin | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| config_proxy.py | backend/core/config_proxy.py | টেন্যান্ট-স্পেসিফিক ডায়নামিক কনফিগ রিট্রিভাল+ক্যাশ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| config_secrets.py | backend/core/config_secrets.py | সিক্রেট লোডিং mixin — ভল্ট, ব্যাচ, lazy লোড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| config_validation.py | backend/core/config_validation.py | Settings ভ্যালিডেটর/নরমালাইজার mixin | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| config_validator.py | backend/core/config_validator.py | স্টার্টআপে env-var স্কিমা ভ্যালিডেশন (fail-fast) | env_schema_validator.py | অপরিবর্তিত ✅ | config_validation/env_validator-এর সাথে বিভ্রান্তিকর |
| constants.py | backend/core/constants.py | টাইমআউট/রেটলিমিট কনফিগ ক্লাস + proxy-নির্ভর গেটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| container_auditor.py | backend/core/container_auditor.py | Docker কন্টেইনার মেমরি অডিট; ৯৫%-এ kill-chain | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| context_manager.py | backend/core/context_manager.py | কনভার্সেশন কনটেক্সট + Qdrant লং-টার্ম মেমরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cors_policy.py | backend/core/cors_policy.py | Deprecated shim → middleware.cors_policy | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| cost_guard.py | backend/core/cost_guard.py | টেন্যান্ট/টিয়ার বাজেট প্রি-ফ্লাইট এনফোর্সমেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| connection_manager.py | backend/core/database/connection_manager.py | তিন পুলের (ORM/asyncpg/psycopg2) ইউনিফায়েড facade | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| db.py | backend/core/db.py | SQLAlchemy async ইঞ্জিন, পুল টিউনিং, DeclarativeBase | database_engine.py | backend/core/database/ | db.py জেনেরিক; database/ সাবপ্যাকেজে যথার্থ |
| db_repository.py | backend/core/db_repository.py | Deprecated shim → database.db_repository | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| db_ssl.py | backend/core/db_ssl.py | Supabase-এর জন্য SSL কনটেক্সট বিল্ডার (verify-full) | অপরিবর্তিত ✅ | backend/core/database/ | DB-সম্পর্কিত ফাইল database/ প্যাকেজে থাকা স্বাভাবিক |
| decision_engine.py | backend/core/decision_engine.py | রিস্ক অ্যাসেসমেন্ট ভিত্তিক অটোনোমাস ডিসিশন রাউটিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| production_deploy.py | backend/core/deployment/production_deploy.py | ব্লু-গ্রিন ডিপ্লয়, রোলব্যাক, হেলথচেক ডিপ্লয় সিস্টেম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| deployment_fallback_defaults.py | backend/core/deployment_fallback_defaults.py | /config/public-এর নন-সিক্রেট ডিফল্ট ভ্যালু | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| email_service.py | backend/core/email_service.py | Deprecated shim → services.email.email_service | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| embeddings.py | backend/core/embeddings.py | লোকাল/রিমোট এমবেডিং ইঞ্জিন (MiniLM→OpenAI ফলব্যাক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| enum_guard.py | backend/core/enum_guard.py | টাইপ-সেফ enum পার্সিং, সাইলেন্ট ফলব্যাক বন্ধ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| env_validator.py | backend/core/env_validator.py | env-var রেজিস্ট্রি স্টার্টআপ ভ্যালিডেটর (config_validator-এর ডুপ্লিকেট) | (একত্রিত) config_validator.py | অপরিবর্তিত ✅ | দুটি সমান্তরাল env-ভ্যালিডেটর — মার্জ করুন |
| error_bus.py | backend/core/error_bus.py | Deprecated shim → core.errors.error_bus | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| error_handler.py | backend/core/error_handler.py | Deprecated shim → core.errors.error_handler | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| error_pattern_db.py | backend/core/error_pattern_db.py | Deprecated shim → core.errors.error_pattern_db | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| error_remediation.py | backend/core/error_remediation.py | Deprecated shim → core.errors.error_remediation | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| errors/__init__.py | backend/core/errors/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| error_bus.py | backend/core/errors/error_bus.py | with_error_bus ডেকোরেটর — ব্যতিক্রম event-bus-এ emit | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| error_handler.py | backend/core/errors/error_handler.py | safe_http_error/safe_error_response — trace_id সহ সেফ এরর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| error_pattern_db.py | backend/core/errors/error_pattern_db.py | এরর প্যাটার্ন পার্সিস্টেন্স (Postgres+SQLite ফলব্যাক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| error_remediation.py | backend/core/errors/error_remediation.py | Qdrant ভিত্তিক ফিক্স-লুকআপ + লোকাল ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| evolution_module.py | backend/core/evolution_module.py | জেনেটিক অ্যালগরিদম (mutation/crossover/selection) স্ট্র্যাটেজি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | "evolution" এখানে আক্ষরিক GA — নাম সঠিক |
| exceptions.py | backend/core/exceptions.py | SupremeAIException হায়ারার্কি — structured error ফ্রেমওয়ার্ক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| factory.py | backend/core/factory.py | SupremeAIFactory — সব কম্পোনেন্ট প্রি-ওয়্যার করে ইনস্ট্যান্স | system_factory.py | অপরিবর্তিত ✅ | factory.py অতি-জেনেরিক নাম |
| factual_verifier.py | backend/core/factual_verifier.py | RAG/web/গণিত দিয়ে ফ্যাক্ট যাচাই | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| failure_fingerprint.py | backend/core/failure_fingerprint.py | এরর মেসেজ নরমালাইজ করে SHA-256 ফিঙ্গারপ্রিন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| feature_flags.py | backend/core/feature_flags.py | env-first, DB-fallback ফিচার-ফ্ল্যাগ চেকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| feedback_loop.py | backend/core/feedback_loop.py | ইউজার ফিডব্যাক ইভেন্ট রেকর্ডিং ও মেট্রিক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| gcp_firestore.py | backend/core/gcp_firestore.py | Deprecated shim → services.storage.gcp_firestore | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| generation_monitor.py | backend/core/generation_monitor.py | AI আউটপুট QA — কনফিডেন্স, ফ্যাক্ট-ক্লেইম, অ্যাট্রিবিউশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| grpc_client.py | backend/core/grpc_client.py | Worker সার্ভিসের gRPC ক্লায়েন্ট (টাস্ক/স্ট্যাটাস/অডিট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| health/__init__.py | backend/core/health/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| health_monitor.py | backend/core/health/health_monitor.py | Prometheus মেট্রিক্সসহ সিস্টেম হেলথ মনিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| health_probes.py | backend/core/health/health_probes.py | Redis/DB/external API প্রোব ফাংশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| proactive_healer.py | backend/core/health/proactive_healer.py | L1–L5 টিয়ারড অটো-হিলিং অ্যাকশন রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | self_healer-এর সাথে ওভারল্যাপ তবে ভূমিকা ভিন্ন |
| self_healer.py | backend/core/health/self_healer.py | কোরোউটিন গার্ড — timeout/cancel ক্যাচ করে event emit | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| uptime_tracker.py | backend/core/health/uptime_tracker.py | SQLite-ভিত্তিক আপটাইম পার্সিস্টেন্স (24h/7d/30d) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| health_check.py | backend/core/health_check.py | ComprehensiveHealthChecker — সাবসিস্টেম হেলথ এগ্রিগেশন | comprehensive_health_check.py | backend/core/health/ | health/ প্যাকেজে সরান; নাম স্পষ্ট করুন |
| health_routes.py | backend/core/health_routes.py | /health /ready /live রাউটার | অপরিবর্তিত ✅ | backend/core/health/ | হেলথ রাউট health/ প্যাকেজেই যথার্থ |
| human_behavior.py | backend/core/human_behavior.py | মানুষ-সদৃশ মাউস/টাইপিং সিমুলেশন (বট-বাইপাস) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| idempotency_middleware.py | backend/core/idempotency_middleware.py | Deprecated shim → middleware.idempotency_middleware | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| immune_system.py | backend/core/immune_system.py | AI-জেনারেটেড কোডের AST সিকিউরিটি স্ক্যানার/গেটকিপার | ast_security_scanner.py | অপরিবর্তিত ✅ | ⚠️ বায়োলজিক্যাল রূপক; কাজ AST সিকিউরিটি স্ক্যান |
| integration_layer.py | backend/core/integration_layer.py | SupremeAIIntegrator — ফুল রিকোয়েস্ট লাইফসাইকেল পাইপলাইন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| integrations/__init__.py | backend/core/integrations/__init__.py | রেজিস্ট্রি থেকে রি-এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| registry.py | backend/core/integrations/registry.py | optional ইন্টিগ্রেশনের মেটাডেটা রেজিস্ট্রি (শুধু রিপোর্ট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| intelligent_cache.py | backend/core/intelligent_cache.py | Redis ক্যাশ — semantic dedup + কস্ট ট্র্যাকিং (৪র্থ ক্যাশ ইমপ্ল) | (একত্রিত) cache/ প্যাকেজে | backend/core/cache/ | ⚠️ "intelligent" শূন্য শব্দ; cache/ ইমপ্লের ডুপ্লিকেশন |
| intelligent_silent_catcher.py | backend/core/intelligent_silent_catcher.py | গ্লোবাল sys.excepthook — unhandled crash ক্যাচ করে | global_crash_catcher.py | অপরিবর্তিত ✅ | ⚠️ "intelligent" অপ্রয়োজনীয়; কাজ crash হুক |
| intent.py | backend/core/intent.py | কীওয়ার্ড-ভিত্তিক IntentClassifier + TaskType enum | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| intent_router.py | backend/core/intent_router.py | লিগ্যাসি sync রাউটার + v2 facade রি-এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | legacy facade; caller মাইগ্রেশনের পরে মুছুন |
| intent_router_v2.py | backend/core/intent_router_v2.py | ক্যানোনিকাল LLM-gatekeeper ইন্টেন্ট রাউটার (regex ফলব্যাক) | intent_router.py | অপরিবর্তিত ✅ | _v2 suffix অস্থায়ী; legacy মুছে নাম পুনরুদ্ধার |
| kaggle_orchestrator.py | backend/core/kaggle_orchestrator.py | ৬ কাগল অ্যাকাউন্টে হেভি কম্পিউট অফলোড কোয়োটা ম্যানেজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| knowledge_base.py | backend/core/knowledge_base.py | memory_vault.json ফাইল-ব্যাকড নলেজ স্টোর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| language_router.py | backend/core/language_router.py | ভাষা ডিটেকশন করে প্রোভাইডার/মডেল ম্যাপিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ld_client.py | backend/core/ld_client.py | LaunchDarkly AI ক্লায়েন্ট init + observability প্লাগিন | launchdarkly_client.py | অপরিবর্তিত ✅ | "ld" অস্পষ্ট সংক্ষেপণ |
| lifespan.py | backend/core/lifespan.py | FastAPI lifespan — সব ইনফ্রা startup/shutdown অর্কেস্ট্রেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | DO NOT MOVE; নাম ঠিক |
| llm/__init__.py | backend/core/llm/__init__.py | LLM প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| advanced_model_router.py | backend/core/llm/advanced_model_router.py | ৫ রাউটার কনসোলিডেটেড — complexity/কস্ট/পারফ মডেল নির্বাচন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| distributed_budget.py | backend/core/llm/distributed_budget.py | Redis INCR-ভিত্তিক মাল্টি-ওয়ার্কার দৈনিক টোকেন বাজেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| free_tier_tracker.py | backend/core/llm/free_tier_tracker.py | প্রোভাইডার-ভিত্তিক RPM/TPM/RPD কোয়োটা ট্র্যাকিং+পজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| interfaces.py | backend/core/llm/interfaces.py | ModelProvider প্রোটোকল (generate/stream/health) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| llm_gateway.py | backend/core/llm/llm_gateway.py | মূল LLM গেটওয়ে — fallback chain, ক্যাশ, কস্ট গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| llm_gateway_with_learning.py | backend/core/llm/llm_gateway_with_learning.py | Deprecated র‍্যাপার → unified_learning ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | deprecated; caller মাইগ্রেশনের পরে মুছুন |
| provider_router.py | backend/core/llm/provider_router.py | লেটেন্সি-অ্যাওয়ার weighted round-robin প্রোভাইডার নির্বাচন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| providers/__init__.py | backend/core/llm/providers/__init__.py | অ্যাডাপ্টার রি-এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cloud_adapter.py | backend/core/llm/providers/cloud_adapter.py | LiteLLM র‍্যাপিং ক্লাউড প্রোভাইডার অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ollama_adapter.py | backend/core/llm/providers/ollama_adapter.py | লোকাল Ollama অ্যাডাপ্টার, প্রাইভেসি বাউন্ডারি এনফোর্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| telemetry.py | backend/core/llm/telemetry.py | প্রতি LLM কলের structured JSON টেলিমেট্রি লগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| token_budget.py | backend/core/llm/token_budget.py | টোকেন এস্টিমেশন, প্রম্পট ট্রাংকেশন, বাজেট এনফোর্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| token_deductor.py | backend/core/llm/token_deductor.py | টোকেন ডিডাকশন + ডাবল-স্পেন্ডিং প্রিভেনশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| llm_router.py | backend/core/llm_router.py | Deprecated shim → services.llm.llm_router | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| localization/__init__.py | backend/core/localization/__init__.py | BhashaBot/VoiceDidi রি-এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bhasha_bot.py | backend/core/localization/bhasha_bot.py | EN↔BN↔Banglish প্রসঙ্গ-সচেতন অনুবাদ ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্রোডাক্ট নাম, অবস্থান যথার্থ |
| voice_didi.py | backend/core/localization/voice_didi.py | বাংলা ভয়েস কমান্ড প্রসেসর (স্বল্প-শিক্ষিত ব্যবহারকারীর জন্য) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্রোডাক্ট নাম, অবস্থান যথার্থ |
| log_batcher.py | backend/core/log_batcher.py | Deprecated shim → monitoring.log_batcher | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| logging.py | backend/core/logging.py | Deprecated shim → monitoring.logging | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| logging_config.py | backend/core/logging_config.py | Deprecated shim → monitoring.logging_config (বহু ইম্পোর্ট হয়) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; সর্বাধিক ইম্পোর্টেড — ধীরে মাইগ্রেট |
| maintenance_pipeline.py | backend/core/maintenance_pipeline.py | হেলথ মনিটরিং + এরর-ইভেন্ট-চালিত অটো রিমিডিয়েশন লুপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| markdown_indexer.py | backend/core/markdown_indexer.py | মার্কডাউন হেডিং-চাংক ইনডেক্স + সেমান্টিক সার্চ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_allowlist.py | backend/core/mcp_allowlist.py | MCP সার্ভার/টুল হোয়াইটলিস্ট ও ভ্যালিডেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_client.py | backend/core/mcp_client.py | MCP সার্ভার কানেক্ট/ডিসকভারি ক্লায়েন্ট (SSRF গার্ড) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| memory_manager.py | backend/core/memory_manager.py | FreeTierMemoryManager — 512MB RAM মনিটর ও GC | process_memory_manager.py | অপরিবর্তিত ✅ | AI-মেমরি নয়, প্রসেস RAM ম্যানেজার |
| messaging/__init__.py | backend/core/messaging/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| adapters.py | backend/core/messaging/adapters.py | Telegram/Email-কে MessagingProvider অ্যাডাপ্টারে র‍্যাপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| event_bus.py | backend/core/messaging/event_bus.py | ইন-প্রসেস ErrorEventBus — structured এরর, DLQ সহ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ব্যাপক ইম্পোর্টেড; সরানো ঝুঁকিপূর্ণ |
| events.py | backend/core/messaging/events.py | প্রকৃতপক্ষে Firebase Admin Auth init (get_firebase_auth) | firebase_auth.py | অপরিবর্তিত ✅ | ⚠️ নাম events, কনটেন্ট Firebase auth — সম্পূর্ণ অমিল |
| gcp_pubsub_queue.py | backend/core/messaging/gcp_pubsub_queue.py | GCP Pub/Sub টাস্ক কিউ + SQLite লোকাল ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| interfaces.py | backend/core/messaging/interfaces.py | MessagingProvider প্রোটোকল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| models.py | backend/core/messaging/models.py | MessageEvent/MessageResult Pydantic মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| nats_messaging.py | backend/core/messaging/nats_messaging.py | NATS JetStream ক্লায়েন্ট — KV registry, persistent কিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pubsub.py | backend/core/messaging/pubsub.py | ইন-মেমরি asyncio PubSub (backpressure সহ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| service.py | backend/core/messaging/service.py | MockMessagingAdapter + MessagingDispatcher (provider নির্বাচন) | dispatcher.py | অপরিবর্তিত ✅ | service.py জেনেরিক; মূল কাজ dispatch |
| upstash_redis_queue.py | backend/core/messaging/upstash_redis_queue.py | Upstash REST ভিত্তিক কিউ ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| metrics.py | backend/core/metrics.py | Deprecated shim → monitoring.metrics | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| metrics_collector.py | backend/core/metrics_collector.py | Deprecated shim → monitoring.metrics_collector | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | shim; মাইগ্রেশন শেষে মুছুন |
| microvm_sandbox.py | backend/core/microvm_sandbox.py | Docker স্যান্ডবক্স এক্সিকিউটর — path whitelist, AST গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| db_optimization_middleware.py | backend/core/middleware/db_optimization_middleware.py | ARCHIVED/BROKEN — ৪টি broken import; ওয়্যার নিষিদ্ধ | (মুছুন বা আর্কাইভ) | backend/_archive/middleware/ | ডেড কোড — ইম্পোর্ট করলেই crash, শুধু ডিজাইন টেমপ্লেট |
| health_aware_middleware.py | backend/core/middleware/health_aware_middleware.py | সিস্টেম হেলথ অনুযায়ী রিকোয়েস্ট হ্যান্ডলিং অ্যাডজাস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| security.py | backend/core/middleware/security.py | সিকিউরিটি হেডার + SQLi রিকোয়েস্ট ভ্যালিডেশন মিডলওয়্যার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| models/__init__.py | backend/core/models/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| shared_workspace.py | backend/core/models/shared_workspace.py | মাল্টি-টেন্যান্ট ওয়ার্কস্পেস RBAC/কলাবোরেশন মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| monitoring.py | backend/core/monitoring.py | অ্যাডভান্সড মেট্রিক্স/অ্যালার্ট/মনিটরিং লেয়ার | অপরিবর্তিত ✅ | backend/monitoring/ | root monitoring.py ও monitoring/ প্যাকেজ একত্র করুন |
| observability/__init__.py | backend/core/observability/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| audit_logger.py | backend/core/observability/audit_logger.py | Tamper-evident অডিট ট্রেইল (write-behind Postgres) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| interfaces.py | backend/core/observability/interfaces.py | AIObservabilityProvider প্রোটোকল + PrivacyMode | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| log_batcher.py | backend/core/observability/log_batcher.py | অ্যাসিনক লগ ব্যাচার — DB-তে ব্যাচ ফ্লাশ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | monitoring.log_batcher-এর সাথে নাম দ্ব্যর্থতা রয়েছে |
| observability_middleware.py | backend/core/observability/observability_middleware.py | রিকোয়েস্ট ট্রেসিং/মেট্রিক্স ASGI মিডলওয়্যার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| posthog_client.py | backend/core/observability/posthog_client.py | PostHog অ্যানালিটিক্স ক্লায়েন্ট (mock ফলব্যাক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **১৩+ ডেপ্রিকেশন shim** (billing_plans, cloud_storage, cors_policy, db_repository, email_service, error_* root, gcp_firestore, idempotency_middleware, llm_router, log_batcher, logging, logging_config, metrics, metrics_collector) — সব ২৫-লাইনের অভিন্ন টেমপ্লেট; importer মাইগ্রেশন শেষে এক ধাপে মুছে ফেলাই সবচেয়ে বড় ক্লিনআপ। বিশেষ সতর্কতা: `core.logging_config` প্রায় প্রতিটি মডিউল ইম্পোর্ট করে — সবার শেষে মাইগ্রেট করুন।
- **ক্যাশ ইমপ্লমেন্টেশন ৫টি**: cache_manager.py, cache/multi_layer_cache.py, cache/query_cache.py, cache/semantic_cache.py, intelligent_cache.py — আংশিক ওভারল্যাপিং; cache/ প্যাকেজে একত্রীকরণ অপরিহার্য।
- **ডুপ্লিকেট ইনফ্রা**: circuit_breaker (root + resilience/), env ভ্যালিডেটর ৩টি (config_validation, config_validator, env_validator), হেলথ সিস্টেম ৪ স্তরে (health_check.py, health/, health_routes.py, monitoring.py), log_batcher ৩ অবস্থানে (shim + monitoring target + observability/)।
- **agents/framework-এ singular/plural টুইন**: agent_department.py বনাম agent_departments.py — প্রায় ডুপ্লিকেট role-prompt ইমপ্ল; একটি মুছে অন্যটিতে মার্জ করুন।
- **সেমান্টিক মিসম্যাচ হটস্পট**: messaging/events.py-তে Firebase auth (সবচেয়ে বড় অমিল), langgraph_agent.py-তে LangGraph নেই, immune_system.py আসলে AST স্ক্যানার, intelligent_* ও autonoguard জাতীয় রঙিন নাম mundane কোডে।
- **মনোলিথ**: competitive_kit.py (১৫৪৯ লাইন, ৬টি স্বাধীন ফিচার) ও config_classification.py (১৮৭৭ লাইন, তবে একক দায়িত্বের ডেটা) — প্রথমটি বিভক্ত করা জরুরি।
- **ডেড কোড**: middleware/db_optimization_middleware.py আর্কাইভড ঘোষিত, ইম্পোর্ট করলেই crash — archive/ এ সরান বা মুছুন।
- ইতিবাচক: automation/, llm/, messaging/, cache/, observability/ সাবপ্যাকেজগুলোর নামকরণ মোটামুটি শৃঙ্খলাবদ্ধ — সংশোধনের প্রধান কাজ root-level ফাইলগুলোতে।


---

## ব্যাচ ০২ — Backend Core (অংশ খ)
**ব্যাচ:** 02 | **তালিকাভুক্ত:** 172 | **বিশ্লেষিত:** 172 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 15 | **স্থানান্তর প্রস্তাব:** 10 | **⚠️ সেমান্টিক মিসম্যাচ:** 11

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| __init__.py | backend/core/observability/providers/__init__.py | LangfuseAdapter re-export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| langfuse_adapter.py | backend/core/observability/providers/langfuse_adapter.py | LLM ট্রেস/ইভালুয়েশন Langfuse অ্যাডাপ্টার, প্রাইভেসি মোড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| telemetry.py | backend/core/observability/telemetry.py | OpenTelemetry ট্রেসিং সেটআপ ও স্প্যান হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| economic_optimizer.py | backend/core/optimization/economic_optimizer.py | বাজেট-সচেতন মডেল কস্ট রাউটিং (EconomicRouter) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্লাস EconomicRouter-এর সাথে সামঞ্জস্য |
| optimized_async_cache.py | backend/core/optimization/optimized_async_cache.py | অ্যাসিঙ্ক LRU+TTL ক্যাশ, সিঙ্গেলটন ফ্যাক্টরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| optimized_redis_client.py | backend/core/optimization/optimized_redis_client.py | পুলড Redis ক্লায়েন্ট + সার্কিট ব্রেকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| performance_optimizer.py | backend/core/optimization/performance_optimizer.py | LRU ক্যাশ, কুয়েরি অপটিমাইজার, পুল ম্যানেজার, মেট্রিক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনটেন্ট নামের সাথে মেলে |
| __init__.py | backend/core/orchestration/__init__.py | SwarmOrchestrator re-export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_orchestrator.py | backend/core/orchestration/agent_orchestrator.py | সেমান্টিক রাউটার + এজেন্ট টাস্ক অর্কেস্ট্রেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | মিশ্র দায়িত্ব, তবু নাম যথেষ্ট |
| cloud_sandbox_orchestrator.py | backend/core/orchestration/cloud_sandbox_orchestrator.py | RunPod/Modal স্যান্ডবক্স লাইফসাইকেল ম্যানেজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| crew_departments.py | backend/core/orchestration/crew_departments.py | ৯টি স্পেশালাইজড সোয়ার্ম এজেন্ট রোল ক্লাস | swarm_agent_roles.py | অপরিবর্তিত ✅ | CrewAI জার্গন; কনটেন্ট এজেন্ট রোল |
| master_cognitive_orchestrator.py | backend/core/orchestration/master_cognitive_orchestrator.py | repair/synthesis/audit/evolution পাইপলাইন ডিসপ্যাচ | cognitive_pipeline_dispatcher.py | অপরিবর্তিত ✅ | ⚠️ "Master Cognitive" অতিরঞ্জিত; কাজ শুধু ডিসপ্যাচ |
| orchestrator.py | backend/core/orchestration/orchestrator.py | পিরিয়ডিক ফিটনেস স্কোরিং শিডিউলার + হেলথ রাউটার | periodic_task_scheduler.py | অপরিবর্তিত ✅ | জেনেরিক "orchestrator" নাম অস্পষ্ট |
| swarm_orchestrator.py | backend/core/orchestration/swarm_orchestrator.py | সিকোয়েন্সিয়াল মাল্টি-এজেন্ট DAG রানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| trio_pipeline.py | backend/core/orchestration/trio_pipeline.py | Gemini→Kilo→Cline ৩-স্টেজ কোড পাইপলাইন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| otp_router.py | backend/core/otp_router.py | OTP ডেলিভারি চ্যানেল রাউটার (Discord/email) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| output_validator.py | backend/core/output_validator.py | মাল্টি-LLM কোড কনসেনসাস + কনফিডেন্স স্কোরিং | multi_model_code_consensus.py | অপরিবর্তিত ✅ | "output validator" নাম কনটেন্ট লুকায় |
| performance_enhancer.py | backend/core/performance_enhancer.py | সেলফ-হিলিং সহ পারফরম্যান্স অপটিমাইজার | performance_self_healer.py | অপরিবর্তিত ✅ | optimization/performance_optimizer-এর সাথে নামসংঘর্ষ |
| permission_cache.py | backend/core/permission_cache.py | টিয়ার্ড (L1/L2) পারমিশন ক্যাশ, fail-closed | অপরিবর্তিত ✅ | backend/core/security/permission_cache.py | RBAC/সিকিউরিটি ডোমেইনের সাথে গ্রুপিং |
| __init__.py | backend/core/persistence/__init__.py | প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pooled_pg.py | backend/core/persistence/pooled_pg.py | সিঙ্ক psycopg2 পুল (সেকেন্ডারি সাবসিস্টেম) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| write_behind.py | backend/core/persistence/write_behind.py | ব্যাচড write-behind PG রাইট বাফার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pgbouncer_pool.py | backend/core/pgbouncer_pool.py | ডিপ্রিকেটেড shim → database.pgbouncer_pool | শিম মুছে ফেলুন 🗑️ | অপরিবর্তিত ✅ | মাইগ্রেশন সম্পন্ন, shim অপ্রয়োজনীয় |
| playwright_manager.py | backend/core/playwright_manager.py | গ্লোবাল হেডলেস Chromium লাইফসাইকেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/plugins/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| capability_resolver.py | backend/core/plugins/capability_resolver.py | ইউজার প্লাগইন টুল ক্যাপাবিলিটি রেজোলভ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| lifecycle_manager.py | backend/core/plugins/lifecycle_manager.py | প্লাগইন ইনস্টল/আনইনস্টল লাইফসাইকেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| manifest_registry.py | backend/core/plugins/manifest_registry.py | প্লাগইন ম্যানিফেস্ট DB CRUD + সিডিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_security.py | backend/core/plugins/mcp_security.py | MCP URL-এর SSRF/প্রাইভেট-IP গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্লাগইন-স্কোপড, নাম ঠিক |
| __init__.py | backend/core/plugins/official/__init__.py | অফিসিয়াল প্লাগইন re-export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| base.py | backend/core/plugins/official/base.py | BasePlugin অ্যাবস্ট্রাক্ট বেস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| github_plugin.py | backend/core/plugins/official/github_plugin.py | GitHub প্লাগইন (মক টুল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| gmail_plugin.py | backend/core/plugins/official/gmail_plugin.py | Gmail স্টাব — শুধু NotImplementedError | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্লেসহোল্ডার, নাম ঠিক |
| google_drive_plugin.py | backend/core/plugins/official/google_drive_plugin.py | Drive স্টাব — NotImplementedError | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্লেসহোল্ডার, নাম ঠিক |
| notion_plugin.py | backend/core/plugins/official/notion_plugin.py | Notion স্টাব — NotImplementedError | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্লেসহোল্ডার, নাম ঠিক |
| slack_plugin.py | backend/core/plugins/official/slack_plugin.py | Slack স্টাব — NotImplementedError | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্লেসহোল্ডার, নাম ঠিক |
| telegram_plugin.py | backend/core/plugins/official/telegram_plugin.py | Telegram স্টাব — NotImplementedError | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্লেসহোল্ডার, নাম ঠিক |
| permission_manager.py | backend/core/plugins/permission_manager.py | প্লাগইন ক্যাপাবিলিটি অথরাইজেশন চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| security_scanner.py | backend/core/plugins/security_scanner.py | কমিউনিটি ম্যানিফেস্ট সিকিউরিটি স্ক্যান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্লাগইন-স্কোপড, নাম ঠিক |
| seed_manifests.py | backend/core/plugins/seed_manifests.py | অফিসিয়াল প্লাগইন ম্যানিফেস্ট ডেটা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| prompt_handler.py | backend/core/prompt_handler.py | প্রম্পট নরমালাইজ/টোকেন এস্টিমেট/কমপ্রেস হেল্পার | prompt_utils.py | অপরিবর্তিত ✅ | "handler" নয়, এগুলো ইউটিলিটি ফাংশন |
| ai_handshake_prompt.py | backend/core/prompts/ai_handshake_prompt.py | ইন্টার-এজেন্ট ডিসকভারি প্রম্পট টেমপ্লেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| provider_rate_limiter.py | backend/core/provider_rate_limiter.py | 429 ডিটেকশন + মাল্টি-প্রোভাইডার ফলব্যাক চেইন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/providers/appwrite/__init__.py | প্যাকেজ মার্কার কমেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| adapter.py | backend/core/providers/appwrite/adapter.py | Appwrite স্টোরেজ অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/providers/n8n/__init__.py | প্যাকেজ ডকস্ট্রিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| adapter.py | backend/core/providers/n8n/adapter.py | n8n অটোমেশন অ্যাডাপ্টার, HMAC+রিট্রাই | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/queue/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| task_queue.py | backend/core/queue/task_queue.py | Redis-ব্যাকড ডিস্ট্রিবিউটেড টাস্ক কিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| task_queue_enhanced.py | backend/core/queue/task_queue_enhanced.py | ইভেন্ট-ভিত্তিক ইন-প্রসেস অ্যাসিঙ্ক টাস্ক কিউ | async_task_queue.py | অপরিবর্তিত ✅ | "_enhanced" সাফিক্স অর্থহীন সংস্করণ-নাম |
| task_router.py | backend/core/queue/task_router.py | কিওয়ার্ড-ভিত্তিক টাস্ক→এক্সিকিউটর রাউটিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/rag/__init__.py | প্যাকেজ কমেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| hybrid_retriever.py | backend/core/rag/hybrid_retriever.py | ডেন্স+BM25 RRF হাইব্রিড রিট্রিভাল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sparse_bm25.py | backend/core/rag/sparse_bm25.py | বাংলা টোকেনাইজারসহ BM25 ইনডেক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rate_limit.py | backend/core/rate_limit.py | Redis টোকেন-বাকেট রেট লিমিট মিডলওয়্যার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rate_limit_quota.py | backend/core/rate_limit_quota.py | প্রতি-ইউজার ডেইলি কোটা লিমিটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rate_limiter.py | backend/core/rate_limiter.py | ডিপ্রিকেটেড shim → middleware.rate_limiter | শিম মুছে ফেলুন 🗑️ | অপরিবর্তিত ✅ | মাইগ্রেশন সম্পন্ন, shim অপ্রয়োজনীয় |
| reliability_controller.py | backend/core/reliability_controller.py | ফেইলিউর ফিঙ্গারপ্রিন্ট + হেলথ স্কোর ট্র্যাকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| repo_manager.py | backend/core/repo_manager.py | গিট ক্লোন + ওয়ার্কস্পেস আইসোলেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| request_context.py | backend/core/request_context.py | correlation-id ContextVar মিডলওয়্যার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/resilience/__init__.py | রেজিলিয়েন্স এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_remediation.py | backend/core/resilience/auto_remediation.py | CodeQL অ্যালার্ট ডিটেক্ট→প্যাচ জেনারেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| chaos_engine.py | backend/core/resilience/chaos_engine.py | অপ-ইন ফল্ট ইনজেকশন (chaos টেস্টিং) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনটেন্ট সত্যিই chaos testing |
| circuit_breaker.py | backend/core/resilience/circuit_breaker.py | সেন্ট্রাল সার্কিট ব্রেকার প্যাটার্ন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| circuit_breaker_manager.py | backend/core/resilience/circuit_breaker_manager.py | শেয়ারড সার্কিট ব্রেকার সিঙ্গেলটন রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| predictive_circuit_breaker.py | backend/core/resilience/predictive_circuit_breaker.py | অ্যানোমালি-ভিত্তিক প্রোঅ্যাক্টিভ ব্রেকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| predictive_metrics.py | backend/core/resilience/predictive_metrics.py | EWMA স্লাইডিং-উইন্ডো লেটেন্সি/এরর মেট্রিক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| safety_rollback_manager.py | backend/core/resilience/safety_rollback_manager.py | ব্যাকআপ, চেকসাম, রোলব্যাক ম্যানেজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| retry_budget.py | backend/core/retry_budget.py | টোকেন-বাকেট রিট্রাই বাজেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| retry_handler.py | backend/core/retry_handler.py | ব্যাকঅফ+জিটার রিট্রাই ডেকোরেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| router.py | backend/core/router.py | ডিপ্রিকেটেড shim → UnifiedRouter | শিম মুছে ফেলুন 🗑️ | অপরিবর্তিত ✅ | ডিপ্রিকেটেড, নামও বিভ্রান্তিকর |
| rules_mutator.py | backend/core/rules_mutator.py | Redis IP ব্লকলিস্ট ব্লক/রিলিজ | ip_blocklist_manager.py | backend/core/security/ip_blocklist_manager.py | ⚠️ "RulesMutator/Shapeshifter" নামে আসল কাজ লুকায় |
| schema_exporter.py | backend/core/schema_exporter.py | OpenAPI স্কিমা এক্সপোর্ট CLI | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| schema_validator.py | backend/core/schema_validator.py | Pydantic স্কিমা রেজিস্ট্রি+ভ্যালিডেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| search.py | backend/core/search.py | DuckDuckGo ফ্রি ওয়েব সার্চ হেল্পার | web_search.py | অপরিবর্তিত ✅ | "search" অতি জেনেরিক; কনটেন্ট DDG |
| __init__.py | backend/core/security/__init__.py | এক্সপোর্ট + JWT/API-key হেল্পার লজিক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ৩৯৮ লাইন লজিক __init__-এ — ভাঙার সুযোগ |
| api_key_limiter.py | backend/core/security/api_key_limiter.py | প্রতি API-key স্লাইডিং-উইন্ডো লিমিট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| api_key_middleware.py | backend/core/security/api_key_middleware.py | API key অথ মিডলওয়্যার + XFF IP | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডিপ্রিকেটেড shim ইমপোর্ট করছে (পরিষ্কার দরকার) |
| compliance_bot.py | backend/core/security/audit/compliance_bot.py | GDPR/DSA কমপ্লায়েন্স চেকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| security_auditor.py | backend/core/security/audit/security_auditor.py | ডিপেন্ডেন্সি/কনফিগ ভালনারেবিলিটি অডিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| audit_logger.py | backend/core/security/audit_logger.py | Redis সিকিউরিটি ইভেন্ট লগার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auth_middleware.py | backend/core/security/authentication/auth_middleware.py | JWT ASGI অথ মিডলওয়্যার, fail-closed | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rbac.py | backend/core/security/authentication/rbac.py | রোল/পারমিশন ম্যাট্রিক্স (RBAC) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| autonoguard_middleware.py | backend/core/security/autonoguard_middleware.py | AutonoGuard ইঞ্জিন FastAPI এনফোর্সমেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্রোডাক্ট-নাম, কনটেন্ট মেলে |
| cryptographic_ledger.py | backend/core/security/cryptographic_ledger.py | SHA-256 হ্যাশ-চেইন অডিট ট্রেইল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| enhanced_ast_scanner.py | backend/core/security/enhanced_ast_scanner.py | AST কোড ভালনারেবিলিটি স্ক্যানার | code_vulnerability_scanner.py | অপরিবর্তিত ✅ | ⚠️ "_enhanced" অর্থহীন; sandbox scanner-এর সাথে বিভ্রান্তি |
| governance_policy.py | backend/core/security/governance_policy.py | সেলফ-ইভোলিউশন অ্যালোলিস্ট/ডেনাইলিস্ট পলিসি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sql_prevention.py | backend/core/security/injections/sql_prevention.py | SQLi প্রতিরোধ টুলকিট + অডিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| input_sanitizer.py | backend/core/security/input_sanitizer.py | PII মাস্কিং + অস্পষ্টতা ডিটেকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ৩টি InputSanitizer ক্লাসের একটি — ডুপ্লিকেট |
| behavioral_analyzer.py | backend/core/security/intelligence/behavioral_analyzer.py | ইউজার বিহেভিয়ার অ্যানোমালি ডিটেকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| guardian_ai.py | backend/core/security/intelligence/guardian_ai.py | LLM I/O গেটকিপার — PII+প্রম্পট-ইনজেকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| optimized_behavioral_analyzer.py | backend/core/security/intelligence/optimized_behavioral_analyzer.py | behavioral_analyzer-এর deque-অপটিমাইজড কপি | merge → behavioral_analyzer.py | অপরিবর্তিত ✅ | "_optimized" ডুপ্লিকেট — একত্রিত করুন |
| origin_validator.py | backend/core/security/origin_validator.py | ট্রাস্টেড-অরিজিন CORS মিডলওয়্যার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| honeypot.py | backend/core/security/protection/honeypot.py | অ্যাটাক-সিগনেচার হানিপট মিডলওয়্যার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| prompt_firewall.py | backend/core/security/protection/prompt_firewall.py | কনস্টিটিউশনাল AI প্রম্পট ফায়ারওয়াল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ssrf_protection.py | backend/core/security/protection/ssrf_protection.py | সেন্ট্রালাইজড SSRF ভ্যালিডেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rate_limiter.py | backend/core/security/rate_limiter.py | Redis ZSET+Lua স্লাইডিং-উইন্ডো লিমিটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | রুট shim-এর সাথে নামঘেঁষা — shim মুছলেই সমাধান |
| resource_guard.py | backend/core/security/resource_guard.py | পাথ-ট্রাভার্সাল ব্লক, হোয়াইটলিস্ট রুট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ast_scanner.py | backend/core/security/scanning/ast_scanner.py | স্যান্ডবক্স প্রি-এক্সিকিউশন AST ব্লকলিস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | enhanced_ast_scanner রিনেম হলে বিভ্রান্তি শেষ |
| secret_scanner.py | backend/core/security/scanning/secret_scanner.py | gitleaks+AI হার্ডকোডেড সিক্রেট স্ক্যান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| secret_vault.py | backend/core/security/secret_vault.py | Infisical ক্লাউড সিক্রেট ভল্ট ক্লায়েন্ট | cloud_secret_vault.py | অপরিবর্তিত ✅ | security_vault-এর সাথে নাম-বিভ্রান্তি দূর |
| secure_credential_store.py | backend/core/security/secure_credential_store.py | RotatingFernet এনক্রিপশন স্টোর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| security_pipeline.py | backend/core/security/security_pipeline.py | কন্ডিশনাল মিডলওয়্যার রেজিস্ট্রি + হেডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| security_vault.py | backend/core/security/security_vault.py | Fernet কী লোড, fail-fast পলিসি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | secret_vault রিনেম হলে যথেষ্ট |
| tool_gateway.py | backend/core/security/tool_gateway.py | টুল এক্সিকিউশন পলিসি ডিসিশন গেটওয়ে | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ws_auth.py | backend/core/security/ws_auth.py | WebSocket টোকেন অথেনটিকেশন হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| self_benchmark.py | backend/core/self_benchmark.py | পারফ/অ্যাকুরেসি/স্ট্রেস সেলফ-বেঞ্চমার্ক ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/self_evolution/__init__.py | ইভোলিউশন কম্পোনেন্ট এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| defense_system.py | backend/core/self_evolution/adversarial_defense/defense_system.py | FGSM/PGD অ্যাডভারসারিয়াল ডিফেন্স (torch) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ML রিসার্চ কোড; প্রোডাকশন-ব্যবহার যাচাই দরকার |
| agent_breeder.py | backend/core/self_evolution/agent_breeder.py | জেনেটিক এজেন্ট ব্রিডিং (crossover/mutation) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_skill_creator.py | backend/core/self_evolution/auto_skill_creator.py | অটোনোমাস স্কিল জেনারেশন+ভ্যালিডেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | sys.path হ্যাক পরিষ্কার দরকার |
| ewc.py | backend/core/self_evolution/continual_learning/ewc.py | Elastic Weight Consolidation (torch) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| daily_learner.py | backend/core/self_evolution/daily_learner.py | দৈনিক স্বয়ংক্রিয় লার্নিং লুপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/self_evolution/digital_twin/__init__.py | DigitalTwinWorldModel ফ্যাসাদ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| remediation_engine.py | backend/core/self_evolution/digital_twin/remediation_engine.py | ফেইলিউর ডিটেকশন+অটো রেমিডিয়েশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| simulator.py | backend/core/self_evolution/digital_twin/simulator.py | সিস্টেম চেঞ্জ/ফেইলিউর ইমপ্যাক্ট সিমুলেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| topology.py | backend/core/self_evolution/digital_twin/topology.py | সার্ভিস টপোলজি ম্যাপার (SQLite) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| evolution_engine.py | backend/core/self_evolution/evolution_engine.py | টাস্ক আউটকাম লার্নিং, স্কিল প্রস্তাব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| evolution_react_agent.py | backend/core/self_evolution/evolution_react_agent.py | ReAct+Reflexion লুপে স্কিল কোডজেন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| fed_learning.py | backend/core/self_evolution/federated_learning/fed_learning.py | ডিপ্রিকেটেড shim → UnifiedLearningEngine | শিম মুছে ফেলুন 🗑️ | অপরিবর্তিত ✅ | ২১ লাইনের ডিপ্রিকেটেড র‍্যাপার |
| fitness_engine.py | backend/core/self_evolution/fitness_engine.py | স্কিল ফিটনেস স্কোরিং+প্রুনিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| integration.py | backend/core/self_evolution/neural_symbolic/integration.py | নিউরাল+সিম্বলিক রিজনিং (torch/sympy) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ML রিসার্চ কোড; নাম গ্রহণযোগ্য |
| performance_oracle.py | backend/core/self_evolution/performance_oracle.py | এজেন্ট মেট্রিক্স→weakest-link সাজেশন | performance_advisor.py | অপরিবর্তিত ✅ | ⚠️ "Oracle" ফানফুড নাম; কাজ অ্যাডভাইজরি |
| self_evolution_agent.py | backend/core/self_evolution/self_evolution_agent.py | স্কিল ফিটনেস মনিটর, রিফ্যাক্টর ট্রিগার লুপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| self_updater.py | backend/core/self_evolution/self_updater.py | রানটাইম হটফিক্স/মাল্টি-ফাইল প্যাচার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| skill_graph.py | backend/core/self_evolution/skill_graph.py | networkx স্কিল DAG, টাইপ-কম্প্যাটিবিলিটি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sentinel_agent.py | backend/core/sentinel_agent.py | এন্ডপয়েন্ট হেলথ মনিটর ব্যাকগ্রাউন্ড এজেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| services.py | backend/core/services.py | লেজি সার্ভিস রেজিস্ট্রি সিঙ্গেলটন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| shutdown.py | backend/core/shutdown.py | গ্রেসফুল শাটডাউন সিকোয়েন্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| skill_manager.py | backend/core/skill_manager.py | রানটাইম স্কিল রেজিস্ট্রি/ডিসপ্যাচ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/skills/__init__.py | স্কিল এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| base.py | backend/core/skills/base.py | BaseSkill মিনিমাল বেস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| core_skills.py | backend/core/skills/core_skills.py | LLM-ভিত্তিক বিল্ট-ইন স্কিলসমূহ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| integrations.py | backend/core/skills/integrations.py | Slack/Notion/GitHub সিঙ্ক স্কিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/startup/__init__.py | প্যাকেজ ডকস্ট্রিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agents.py | backend/core/startup/agents.py | ব্যাকগ্রাউন্ড এজেন্ট স্টার্টআপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| api_key_tables.py | backend/core/startup/api_key_tables.py | api_keys টেবিল DDL | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| services.py | backend/core/startup/services.py | DB পুল/ট্রেসিং/ক্যাশ ইনিট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| startup_validator.py | backend/core/startup_validator.py | স্টার্টআপে env/কনফিগ ভ্যালিডেশন | অপরিবর্তিত ✅ | backend/core/startup/startup_validator.py | startup প্যাকেজের সাথে কো-লোকেশন |
| interfaces.py | backend/core/storage/interfaces.py | StorageProvider প্রোটোকল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| local_adapter.py | backend/core/storage/local_adapter.py | লোকাল ফাইলসিস্টেম স্টোরেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| models.py | backend/core/storage/models.py | স্টোরেজ পাইড্যান্টিক মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| service.py | backend/core/storage/service.py | StorageDispatcher সিঙ্গেলটন রাউটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| swarm_pubsub.py | backend/core/swarm_pubsub.py | Redis পাবসাব ইভেন্ট স্ট্রিম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| target_registry.py | backend/core/target_registry.py | রিপো/প্ল্যাটফর্ম টার্গেট রেজিস্ট্রি+স্কোপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| task_contract.py | backend/core/task_contract.py | ইউনিভার্সাল টাস্ক ডেটাক্লাস/এনাম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/telemetry/__init__.py | observability.telemetry re-export shim | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টেস্ট-কম্প্যাট শিম — পরে একত্রিত করা যায় |
| system_telemetry.py | backend/core/telemetry/system_telemetry.py | psutil CPU/মেমরি ব্রডকাস্ট লুপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tenant_db.py | backend/core/tenant_db.py | ডিপ্রিকেটেড shim → database.tenant_db | শিম মুছে ফেলুন 🗑️ | অপরিবর্তিত ✅ | মাইগ্রেশন সম্পন্ন, shim অপ্রয়োজনীয় |
| test_retry_handler.py | backend/core/test_retry_handler.py | retry_handler ডেমো/টেস্ট স্ক্রিপ্ট | অপরিবর্তিত ✅ | backend/tests/test_retry_handler.py | টেস্ট ফাইল core প্যাকেজে ভুল স্থানে |
| qa_suite.py | backend/core/testing/qa_suite.py | ইন-অ্যাপ QA স্যুট (selenium/locust) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | pytest ইনফ্রার সাথে ডুপ্লিকেশন — মূল্যায়ন দরকার |
| __init__.py | backend/core/tier8/__init__.py | Tier-8 মেটা-এজেন্ট এক্সপোর্ট | অপরিবর্তিত ✅ | backend/core/meta_agents/__init__.py | ⚠️ "tier8" সাই-ফাই টিয়ার নাম |
| agent_evolution_engine.py | backend/core/tier8/agent_evolution_engine.py | GA-স্টাইল এজেন্ট জিনোম ইভোলিউশন | agent_capability_evolution.py | backend/core/meta_agents/agent_capability_evolution.py | ⚠️ agent_breeder-এর সাথে কার্যত ডুপ্লিকেট |
| self_improvement_agent.py | backend/core/tier8/self_improvement_agent.py | কোডবেস রিফ্যাক্টর প্রোপোজাল এজেন্ট | অপরিবর্তিত ✅ | backend/core/meta_agents/self_improvement_agent.py | ⚠️ tier8 প্যাকেজ নাম বদলাতে হবে |
| skill_marketplace_curator.py | backend/core/tier8/skill_marketplace_curator.py | স্কিল মার্কেটপ্লেস লিস্টিং/রেটিং | অপরিবর্তিত ✅ | backend/core/meta_agents/skill_marketplace_curator.py | ⚠️ tier8 প্যাকেজ নাম বদলাতে হবে |
| swarm_coordination_agent.py | backend/core/tier8/swarm_coordination_agent.py | কনসেনসাস-ভোটিং সোয়ার্ম অর্কেস্ট্রেটর | অপরিবর্তিত ✅ | backend/core/meta_agents/swarm_coordination_agent.py | ⚠️ orchestration/swarm_orchestrator ডুপ্লিকেট |
| tier8_integration.py | backend/core/tier8/tier8_integration.py | Tier-8 এজেন্ট লাইফসাইকেল ওয়্যারিং | meta_agents_integration.py | backend/core/meta_agents/meta_agents_integration.py | ⚠️ নামে "tier8" — প্যাকেজ রিনেমে অপ্রচলিত |
| type_sync_bus.py | backend/core/type_sync_bus.py | NATS টাইপ-রিজেন ইভেন্ট বাস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| unified_learning.py | backend/core/unified_learning.py | ৮+ লার্নিং ইঞ্জিনের একীভূত ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| unified_memory.py | backend/core/unified_memory.py | মেমরি সিস্টেম ফ্যাসাদ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| unified_router.py | backend/core/unified_router.py | ২৫+ রাউটারের একীভূত মডেল রাউটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| universal_rules.py | backend/core/universal_rules.py | এজেন্ট কনস্টিটিউশনাল রুলস লোডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম গ্র্যান্ডিওজ তবে কনটেন্ট মেলে |
| upload_validator.py | backend/core/upload_validator.py | আপলোড সাইজ/এক্সটেনশন/MIME চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| user_profiler.py | backend/core/user_profiler.py | ইউজার মোড/প্রোফাইল ট্র্যাকিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/utils/__init__.py | lazy_import re-export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| background_tasks.py | backend/core/utils/background_tasks.py | asyncio টাস্ক GC-প্রতিরোধ ট্র্যাকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| firestore_helpers.py | backend/core/utils/firestore_helpers.py | Firestore ক্লায়েন্ট + SQLite ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| lazy_loader.py | backend/core/utils/lazy_loader.py | অপশনাল প্যাকেজ লেজি ইমপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| time_utils.py | backend/core/utils/time_utils.py | UTC-aware টাইম হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/core/zero_cost_architecture/__init__.py | zero-cost কম্পোনেন্ট re-export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ নাম মার্কেটিং-ধর্মী, তবে প্রতিষ্ঠিত |
| swarm_orchestrator_integration.py | backend/core/zero_cost_architecture/swarm_orchestrator_integration.py | ZeroCostSwarmOrchestrator র‍্যাপার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম কনটেন্ট বর্ণনা করে |
| zero_cost_patch_phase1_4.py | backend/core/zero_cost_architecture/zero_cost_patch_phase1_4.py | কিউ+ব্রেকার+Redis+লার্নিং মনোলিথ (২২৪৩ লাইন) | resilient_task_infrastructure.py | অপরিবর্তিত ✅ | ⚠️ "patch_phase1_4" প্যাচ-ফাইল নাম; ভাঙা দরকার |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **৫টি ডিপ্রিকেটেড shim** (pgbouncer_pool, rate_limiter, router, tenant_db, fed_learning) এখনো বসবাস করছে; `security/api_key_middleware.py` এখনো ডিপ্রিকেটেড `core.rate_limiter` shim থেকে import করছে — importer মাইগ্রেশনের পর shim মুছে ফেলা সর্বোচ্চ অগ্রাধিকার।
- **ডুপ্লিকেট ইমপ্লিমেন্টেশন ক্লাস্টার:** ২টি PerformanceOptimizer ক্লাস (optimization/performance_optimizer বনাম performance_enhancer — `get_performance_optimizer()` ফাংশনও দুই জায়গায়), ২টি AST স্ক্যানার, ২টি behavioral analyzer, ৩টি InputSanitizer ক্লাস, ২টি swarm অর্কেস্ট্রেটর, ২টি agent-evolution ইঞ্জিন (agent_breeder বনাম tier8/agent_evolution_engine), ২টি LRU ক্যাশ — একত্রীকরণ ছাড়া রিনেম-ই যথেষ্ট নয়।
- **tier8 প্যাকেজ ব্যাচের বৃহত্তম সেমান্টিক-মিসম্যাচ হটস্পট** — "Tier 8 Meta-Self" নামে ৪টি এজেন্ট; `core/meta_agents/`-এ রিনেম/রিলোকেট প্রস্তাব করা হয়েছে।
- **সংস্করণ-সাফিক্স অ্যান্টি-প্যাটার্ন:** `_enhanced` (task_queue_enhanced, enhanced_ast_scanner), `_optimized` (optimized_behavioral_analyzer) — প্রকৃত পার্থক্য নামে বোঝা যায় না।
- **ভুল স্থানে টেস্ট:** `core/test_retry_handler.py` প্রোডাকশন প্যাকেজের ভেতরে ডেমো-টেস্ট; `backend/tests/`-এ সরাতে হবে।
- **লজিক-ভারী `__init__`:** `security/__init__.py`-এ ৩৯৮ লাইনের JWT/API-key হেল্পার — আলাদা `tokens.py` মডিউলে ভাঙা উচিত।
- **রেট-লিমিটার বিশৃঙ্খলা:** rate_limit.py, rate_limit_quota.py, security/rate_limiter.py, provider_rate_limiter.py + ডিপ্রিকেটেড rate_limiter.py shim — ৫টি মডিউলে বিভক্ত; shim মুছলে বিভ্রান্তি অনেক কমবে।
- **বিশাল "প্যাচ" মনোলিথ:** `zero_cost_patch_phase1_4.py` (২২৪৩ লাইন) ৪টি ফেজের কোড এক ফাইলে; ফেজ-প্রতি মডিউলে ভাঙা এবং প্যাচ-নাম বাদ দেওয়া প্রয়োজন।


---

## ব্যাচ ০৩ — Backend API ও Services
**ব্যাচ:** 03 | **তালিকাভুক্ত:** 202 | **বিশ্লেষিত:** 202 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 47 | **স্থানান্তর প্রস্তাব:** 8 | **⚠️ সেমান্টিক মিসম্যাচ:** 11

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| __init__.py | backend/api | লেজি রাউটার রেজিস্ট্রেশন হেল্পার + error-bus | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| dependencies.py | backend/api | লিগ্যাসি DI: JWT verify, tenant db, fitness | (ডিলিট — deps.py-তে merge) | — | deps.py এটি replace করেছে; ডুপ্লিকেট DI |
| deps.py | backend/api | সক্রিয় DI: user token, tenant db, fitness engine | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| errors.py | backend/api | স্ট্যান্ডার্ড এরর envelope + global handler | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| middleware.py | backend/api | ৬টি মিডলওয়্যার: correlation, tenant, chaos, idempotency | অপরিবর্তিত ✅ | backend/api/middleware/ | একাধিক middleware; প্যাকেজে বিভক্ত হোক |
| query_timing.py | backend/api/middleware | ASGI রেসপন্স-টাইম ট্র্যাকিং + percentile | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; টেইল কমেন্ট অপসারণ করুন |
| routers.py | backend/api | declarative ALL_ROUTERS রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| server.py | backend/api | লিগ্যাসি standalone FastAPI অ্যাপ (/api/v1/process) | (লিগ্যাসি — merge/ডিলিট) | — | মূল অ্যাপ entrypoint-এর সাথে ডুপ্লিকেট |
| __init__.py | backend/api/routes | ৫৪৫-লাইন try/except রাউটার ইমপোর্ট রেজিস্ট্রি | (ডিলিট — routers.py-তে merge) | — | routers.py-এর সাথে ডুপ্লিকেট রেজিস্ট্রি |
| admin.py | backend/api/routes | admin ops: rules, fixes, alerts, backup, cost (৯২৫ লাইন) | admin/ প্যাকেজে বিভক্ত | backend/api/admin/ | god-router; ডোমেইনভিত্তিক ভাগ দরকার |
| admin_auth.py | backend/api/routes | admin token verify + rate-limit dependency | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও দায়িত্ব স্পষ্ট |
| admin_dashboard.py | backend/api/routes | ৬২ হ্যান্ডলার: users, config, backup, flags, deploy-gate (১৩৩০ লাইন) | dashboard.py (ভাগ করে) | backend/api/admin/ | বহু দায়িত্ব; admin প্যাকেজে বিভাজন |
| admin_librarian.py | backend/api/routes | skill quarantine queue approval/reject | skill_approval_admin.py | অপরিবর্তিত ✅ | ⚠️ 'librarian' রূপক; কাজ skill approval |
| admin_v1.py | backend/api/routes | মাত্র ১ এন্ডপয়েন্ট: list agents v1 | (ডিলিট — agents.py-তে merge) | — | একক এন্ডপয়েন্ট; ডুপ্লিকেট |
| advanced_router.py | backend/api/routes | prompt→সেরা মডেল নির্বাচন এন্ডপয়েন্ট | model_router.py | অপরিবর্তিত ✅ | ⚠️ 'advanced' অস্পষ্ট; মডেল-নির্বাচন |
| agent.py | backend/api/routes | /api/v1/agents টাস্ক এক্সিকিউশন | (merge — agents.py) | — | agents.py-এর সাথে দায়িত্ব ওভারল্যাপ |
| agent_action.py | backend/api/routes | জেনেরিক agent action runner এন্ডপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_tasks.py | backend/api/routes | agent/swarm execute + latency summary | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_workspace.py | backend/api/routes | agent কমান্ড, মেমরি লার্ন, PR, টার্মিনাল WS | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agents.py | backend/api/routes | agent list/status + research search/summarize | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | research এন্ডপয়েন্ট deep_research-এ সরানো ভালো |
| analytics.py | backend/api/routes | রিপোর্ট, churn প্রেডিকশন, বিজনেস মেট্রিক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| api_keys.py | backend/api/routes | API key CRUD, rotate, usage, quota, bulk-delete | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| approval_manager.py | backend/api/routes | /api/v1/hitl skill approve/reject | hitl_approvals.py | অপরিবর্তিত ✅ | 'manager' অস্পষ্ট; hitl পরিভাষায় সামঞ্জস্য |
| artifacts.py | backend/api/routes | artifact CRUD + mermaid/react preview HTML | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| async_task_router.py | backend/api/routes | async task status/stats এন্ডপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auth.py | backend/api/routes | login/register/refresh/me/logout + JWT হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| billing_api.py | backend/api/routes | wallet, transaction, stripe+sslcommerz webhook | billing/ প্যাকেজ (wallet.py, webhooks.py) | backend/api/routes/billing/ | payments.py-এর সাথে ডুপ্লিকেট checkout/webhook |
| branch_conversations.py | backend/api/routes | conversation branch/merge ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| browser.py | backend/api/routes | browser agent নিয়ন্ত্রণ+session+scrape proxy (৭৫ হ্যান্ডলার) | browser/ প্যাকেজে বিভক্ত | backend/api/browser/ | ৮৩৬ লাইন; browser_routes-এর সাথে ওভারল্যাপ |
| browser_routes.py | backend/api/routes | AI action, security scan, screenshot, sessions | browser_integration.py | backend/api/browser/ | 'routes' সাফিক্স; browser.py-তে একীভূত |
| byoc_api.py | backend/api/routes | BYOC credential save + container deploy status | byoc.py | অপরিবর্তিত ✅ | '_api' সাফিক্স অপ্রয়োজনীয় |
| cache_predictions.py | backend/api/routes | ক্যাশ-প্রিফেচ প্রেডিকশন এন্ডপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cdc_webhooks.py | backend/api/routes | CDC ইভেন্ট webhook → vector-db delete | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| chat.py | backend/api/routes | chat completion + stream + learning stats | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | canonical রাখুন; task.py/stream.py এখানে merge |
| chat_export.py | backend/api/routes | conversation md/pdf/docx এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| chat_search.py | backend/api/routes | কথোপকথন সার্চ (title+message relevance) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| chat_upload.py | backend/api/routes | ইমেজ অ্যাটাচমেন্ট upload/serve/delete | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ci_dashboard_api.py | backend/api/routes | CI মেট্রিক্স ড্যাশবোর্ড + history + WS | ci_dashboard.py | অপরিবর্তিত ✅ | '_api' সাফিক্স অপ্রয়োজনীয় |
| ci_webhooks.py | backend/api/routes | CI রেজাল্ট webhook গ্রহণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cloud_mesh.py | backend/api/routes | kill-switch, defcon, ক্যাশ পার্জ, key rotate | cloud_ops.py | অপরিবর্তিত ✅ | ⚠️ 'mesh/defcon' রূপক; ক্লাউড অ্যাডমিন অপারেশন |
| codeflow.py | backend/api/routes | কোড-ফ্লো গ্রাফ বিশ্লেষণ এন্ডপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cognitive.py | backend/api/routes | বাজেট-সচেতন cognitive মডেল রাউটিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | brain.cognitive_router-এর সাথে সামঞ্জস্য |
| __init__.py | backend/api/routes/commandcenter | command-center health/metrics/events aggregate | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| build.py | backend/api/routes/commandcenter | router/provider/skill/memory summary ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | commandcenter গ্রুপিংয়ে উপযুক্ত |
| money.py | backend/api/routes/commandcenter | cost/usage/budget/ROI ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | commandcenter গ্রুপিংয়ে উপযুক্ত |
| observe.py | backend/api/routes/commandcenter | metrics/logs/events/ci/health/traffic ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | commandcenter গ্রুপিংয়ে উপযুক্ত |
| operate.py | backend/api/routes/commandcenter | agents/swarm/tasks/sessions/tenants ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | commandcenter গ্রুপিংয়ে উপযুক্ত |
| overview.py | backend/api/routes/commandcenter | aggregate overview ড্যাশবোর্ড ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | commandcenter গ্রুপিংয়ে উপযুক্ত |
| secure.py | backend/api/routes/commandcenter | threats/audit/approvals/rules/secrets ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | commandcenter গ্রুপিংয়ে উপযুক্ত |
| system.py | backend/api/routes/commandcenter | config/flags/backup/deploy-gate নিয়ন্ত্রণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | commandcenter গ্রুপিংয়ে উপযুক্ত |
| config_routes.py | backend/api/routes | public + admin কনফিগ CRUD | config.py | অপরিবর্তিত ✅ | '_routes' সাফিক্স অপ্রয়োজনীয় |
| conversations.py | backend/api/routes | conversation + message CRUD | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| deep_research.py | backend/api/routes | মাল্টি-স্টেপ রিসার্চ পাইপলাইন + history | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| dock_actions.py | backend/api/routes | dock integration trigger + github push→SSE | dock_integrations.py | অপরিবর্তিত ✅ | ⚠️ 'dock' বিমূর্ত; ইন্টিগ্রেশন ট্রিগার |
| ecosystem.py | backend/api/routes | capability/task/resource registry + MCP manifest | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ecosystem_admin.py | backend/api/routes | capability lifecycle, proposal, opportunity admin | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| email.py | backend/api/routes | Gmail/IMAP অ্যাকাউন্ট সংযোগ auth | email_connections.py | অপরিবর্তিত ✅ | শুধু মেইল-অ্যাকাউন্ট সংযোগ, পাঠানো নয় |
| events.py | backend/api/routes | SSE ড্যাশবোর্ড ইভেন্ট স্ট্রিম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| evolution.py | backend/api/routes | skill breeding/quarantine/proposal/swarm blueprint | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | evolution-engine ডোমেইনের সাথে সঙ্গতিপূর্ণ |
| execution_policies.py | backend/api/routes | এক্সিকিউশন পলিসি get/update | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| feedback.py | backend/api/routes | ফিডব্যাক ইনজেস্ট → sqlite persistence | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| files.py | backend/api/routes | টেনান্ট ওয়ার্কস্পেস ফাইল read/write | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| github.py | backend/api/routes | repo connect/improve/push/commits (GitHubAgent) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| global_memory.py | backend/api/routes | গ্লোবাল মেমরি CRUD/search/sync | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| graph.py | backend/api/routes | skill graph + learning path ভিজ্যুয়ালাইজেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| healing.py | backend/api/routes | স্টাব: হার্ডকোডেড predictions/stats রিটার্ন | (ডিলিট — স্টাব) | — | হার্ডকোডেড ডামি রেসপন্স; বাস্তবায়ন নেই |
| health.py | backend/api/routes | health/readiness/liveness প্রোব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| health_aggregation.py | backend/api/routes | সব সার্ভিসের aggregate health/uptime/dependency | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| hitl_admin.py | backend/api/routes | Firestore HITL pending approvals approve/reject | (merge — approval_manager.py) | — | HITL approval ডুপ্লিকেট |
| hybrid_search.py | backend/api/routes | RAG ইনডেক্সিং + হাইব্রিড সার্চ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ide_trio.py | backend/api/routes | ৩-এজেন্ট কোডজেন+রিভিউ পাইপলাইন চালায় | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | services/ide_trio-এর সাথে সামঞ্জস্য |
| integrations.py | backend/api/routes | GitHub OAuth link + callback | github_oauth.py | অপরিবর্তিত ✅ | ফাইলে শুধু GitHub OAuth আছে |
| internal.py | backend/api/routes | internal admin: evolution trigger, system alerts | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| internet_monitor.py | backend/api/routes | ইন্টারনেট মনিটর admin এন্ডপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| kaggle.py | backend/api/routes | Kaggle callback, job submit/status/stats | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| keys.py | backend/api/routes | ইউজার প্রোভাইডার API key encrypt/CRUD | provider_keys.py | অপরিবর্তিত ✅ | api_keys.py-এর সাথে বিভ্রান্তিকর |
| knowledge.py | backend/api/routes | company knowledge QA + scribe + seed | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| living_brain.py | backend/api/routes | learning-engine status/metrics ড্যাশবোর্ড | learning_dashboard.py | অপরিবর্তিত ✅ | ⚠️ 'living brain' রূপক; লার্নিং মেট্রিক্স |
| living_engine.py | backend/api/routes | /solve এন্ডপয়েন্ট — মাল্টি-ডোমেইন সলভার | solve_api.py | অপরিবর্তিত ✅ | ⚠️ 'living engine' রূপক; সলভার API |
| llm_gateway_routes.py | backend/api/routes | gateway health/state/circuit-reset/fallback | llm_gateway.py | অপরিবর্তিত ✅ | '_routes' সাফিক্স অপ্রয়োজনীয় |
| localization.py | backend/api/routes | অনুবাদ + বাংলা ভয়েস কমান্ড (BhashaBot) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| maintenance.py | backend/api/routes | maintenance pipeline status এন্ডপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| markdown.py | backend/api/routes | markdown export jobs, compare, share, history | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| marketplace_endpoints.py | backend/api/routes | মার্কেটপ্লেস search/install + catalog sources | marketplace.py | অপরিবর্তিত ✅ | '_endpoints' সাফিক্স অপ্রয়োজনীয় |
| mcp_marketplace.py | backend/api/routes | MCP সার্ভার discover/connect | mcp_connect.py | অপরিবর্তিত ✅ | marketplace নয়; MCP সার্ভার কানেক্ট |
| media.py | backend/api/routes | প্রেসাইনড মিডিয়া upload URL তৈরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| memory.py | backend/api/routes | checkpoint/chunk/vector recall + conversations | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| meta_ai.py | backend/api/routes | agent breeding pool + performance/weakest-link | agent_breeding.py | অপরিবর্তিত ✅ | ⚠️ 'meta-ai/layer-6' বিমূর্ত; ব্রিডিং |
| metrics.py | backend/api/routes | মেট্রিক্স ইঞ্জিন + realtime + chaos trigger | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mobile_bff.py | backend/api/routes | মোবাইল BFF: AI রিকোয়েস্ট proxy | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| n8n_webhooks.py | backend/api/routes | n8n workflow callback receiver | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| onboarding.py | backend/api/routes | onboarding complete/status/plan/signal | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| payments.py | backend/api/routes | stripe checkout + webhook + plans | (merge — billing/ প্যাকেজ) | backend/api/routes/billing/ | billing_api.py-এর সাথে ডুপ্লিকেট |
| plugin_submissions.py | backend/api/routes | কমিউনিটি প্লাগইন সাবমিশন গ্রহণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| plugins.py | backend/api/routes | প্লাগইন install/uninstall/list | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pr_review_api.py | backend/api/routes | GitHub PR review webhook + status | pr_review.py | অপরিবর্তিত ✅ | '_api' সাফিক্স অপ্রয়োজনীয় |
| preferences.py | backend/api/routes | ইউজার প্রেফারেন্স get/upsert/stream | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| prompt_templates.py | backend/api/routes | প্রম্পট টেমপ্লেট CRUD/use/seed | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| public_config.py | backend/api/routes | পাবলিক config + branding এন্ডপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| realtime_dashboard.py | backend/api/routes | WS ড্যাশবোর্ড ব্রডকাস্ট ম্যানেজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| reasoning.py | backend/api/routes | quick/ToT/debate reasoning + stream | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| repos.py | backend/api/routes | ওয়ার্কস্পেস repo ক্যাটালগ CRUD | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sandbox_api.py | backend/api/routes | Docker sandbox create/execute/logs/destroy | sandbox.py | অপরিবর্তিত ✅ | '_api' সাফিক্স অপ্রয়োজনীয় |
| scheduled_tasks.py | backend/api/routes | শিডিউলড টাস্ক CRUD/run/history | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| scraper.py | backend/api/routes | scraper মাইক্রোসার্ভিসে proxy রাউট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| selector_healing.py | backend/api/routes | CSS selector healing logs/decision/audit | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| service_topology.py | backend/api/routes | সার্ভিস topology probe + WS health স্ট্রিম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| session_stream.py | backend/api/routes | সেশন ইভেন্ট স্ট্রিম + buffer + autosave | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| session_takeover.py | backend/api/routes | admin সেশন takeover + screencast WS | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| share.py | backend/api/routes | পাবলিক share লিংক generate/view/revoke | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| simulator.py | backend/api/routes | মোবাইল ডিভাইস সিমুলেটর profile/app/session | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম দায়িত্ব প্রতিফলিত করে |
| simulator_admin.py | backend/api/routes | সিমুলেটর usage/quota admin | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| site_actions.py | backend/api/routes | সেভড সাইট অ্যাকশন CRUD + selector test | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| skills.py | backend/api/routes | skill catalog/search/install | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| slash_commands.py | backend/api/routes | slash কমান্ড registry + হ্যান্ডলার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sso.py | backend/api/routes | OIDC/SAML SSO login/callback/logout | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| stream.py | backend/api/routes | লিগ্যাসি SSE chat stream (brain.ModelRouter) | (ডিলিট — stream_chat_sse-তে merge) | — | stream_chat_sse.py-এর সাথে ডুপ্লিকেট |
| stream_chat_sse.py | backend/api/routes | নিরাপদ SSE chat streaming (SafeSSEGenerator) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| stream_hitl_sse.py | backend/api/routes | HITL ইভেন্ট SSE স্ট্রিম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| stream_voice_sse.py | backend/api/routes | ভয়েস TTS SSE স্ট্রিম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| syncguard.py | backend/api/routes | sync-guard audit trigger এন্ডপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| task.py | backend/api/routes | task execute + completion + chat stream (৪৭৯ লাইন) | (ভাগ — chat.py + stream_chat_sse) | — | chat/stream-এর সাথে ডুপ্লিকেট এন্ডপয়েন্ট |
| task_workspace.py | backend/api/routes | workspace task execute + quota | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | task.py/agent_workspace-এর সাথে নাম-ঘনিষ্ঠতা সতর্কতা |
| tenant_admin.py | backend/api/routes | টেনান্ট CRUD/limits/usage/tier-defaults | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tier_s_routes.py | backend/api/routes | ১২টি রাউটারের রেজিস্ট্রি হেল্পার | (merge — routers.py) | — | ⚠️ 'Tier-S' বিমূর্ত; তৃতীয় রেজিস্ট্রি |
| tools_ops.py | backend/api/routes | smell/vuln check + deploy compose/helm | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tools_registry.py | backend/api/routes | টুল registry CRUD | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| traffic_monitor.py | backend/api/routes | লাইভ ট্রাফিক admin view | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| unified_memory_api.py | backend/api/routes | long-term memory store/query | unified_memory.py | অপরিবর্তিত ✅ | '_api' সাফিক্স অপ্রয়োজনীয় |
| usage_metrics.py | backend/api/routes | ব্যবহার মেট্রিক্স upsert/query | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| voice.py | backend/api/routes | TTS ভয়েস list + audio stream | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| webhooks_ai.py | backend/api/routes | টেলিগ্রাম alert webhook + callback | telegram_webhooks.py | অপরিবর্তিত ✅ | ⚠️ নাম অস্পষ্ট; শুধুই টেলিগ্রাম |
| websocket_agent.py | backend/api/routes | agent WS chat + preference analysis | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| websocket_hitl.py | backend/api/routes | HITL WS এন্ডপয়েন্ট + token verify | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| websocket_voice.py | backend/api/routes | ভয়েস WS: STT + intent হ্যান্ডলিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| workspaces_route.py | backend/api/routes | workspace-এ target repo bind/list | workspaces.py | অপরিবর্তিত ✅ | '_route' সাফিক্স অপ্রয়োজনীয় |
| zero_cost.py | backend/api/routes | zero-cost orchestrator health/metrics/recommendation | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | core মডিউলের সাথে সামঞ্জস্যপূর্ণ নাম |
| __init__.py | backend/api/v1 | telemetry router export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| telemetry.py | backend/api/v1 | system/cache/db/ai টেলিমেট্রি + frontend error report | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/services | global httpx client holder (lifespan-initialized) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_healer.py | backend/services | ইস্যু ডিটেকশন + circuit breaker + retry self-heal | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/services/billing | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ মার্কার হিসেবে উপযুক্ত |
| billing_plans.py | backend/services/billing | checkout request + subscription plan মডেল | plans.py | অপরিবর্তিত ✅ | প্যাকেজ প্রিফিক্স পুনরাবৃত্ত |
| Dockerfile | backend/services/browser | ব্রাউজার মাইক্রোসার্ভিস কনটেইনার ইমেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডিপ্লয়মেন্ট অ্যাসেট, নাম উপযুক্ত |
| main.py | backend/services/browser | aiohttp playwright scrape/screenshot মাইক্রোসার্ভিস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্বাধীন সার্ভিস entrypoint, উপযুক্ত |
| requirements.txt | backend/services/browser | ব্রাউজার সার্ভিস ডিপেন্ডেন্সি তালিকা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডিপ্লয়মেন্ট অ্যাসেট, নাম উপযুক্ত |
| config_service.py | backend/services | DB config পড়া + Redis ক্যাশ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| diagram_parser_service.py | backend/services | mermaid/plantuml/drawio পার্সার + vision analyzer | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম দায়িত্ব প্রতিফলিত করে |
| __init__.py | backend/services/dynamic_ai | প্যাকেজ ডকস্ট্রিং মাত্র | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ মার্কার হিসেবে উপযুক্ত |
| circuit_breaker.py | backend/services/dynamic_ai | প্রোভাইডার circuit breaker manager | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| learning_engine.py | backend/services/dynamic_ai | অ্যাডাপটিভ প্যারামিটার লার্নিং ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| local_fallback.py | backend/services/dynamic_ai | Ollama লোকাল মডেল fallback | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| orchestrator.py | backend/services/dynamic_ai | প্রোভাইডার-নিরপেক্ষ টেক্সট জেনারেশন অর্কেস্ট্রেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| provider_registry.py | backend/services/dynamic_ai | প্রোভাইডার কনফিগ/status/health registry | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | llm/providers.py-এর সাথে ওভারল্যাপ পর্যালোচনা করুন |
| dynamic_planner.py | backend/services | TaskNode/TaskDAG ডাইনামিক প্ল্যানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/services/email | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ মার্কার হিসেবে উপযুক্ত |
| email_service.py | backend/services/email | ইমেইল পাঠানোর সার্ভিস (SMTP) | mailer.py | অপরিবর্তিত ✅ | email/email_service পুনরাবৃত্ত নাম |
| escrow_service.py | backend/services | মার্কেটপ্লেস escrow hold/release/dispute | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ডোমেইন-বহি ফিচার নোট করুন |
| __init__.py | backend/services/hitl | HITLEngine + ledger export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| engine.py | backend/services/hitl | HITLEngine: human-approval ফ্লো | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ প্রেক্ষাপটে নাম উপযুক্ত |
| hitl_ledger.py | backend/services/hitl | ক্রিপ্টোগ্রাফিক HITL audit ledger | ledger.py | অপরিবর্তিত ✅ | প্যাকেজ প্রিফিক্স পুনরাবৃত্ত |
| __init__.py | backend/services/ide_trio | পাইপলাইন ক্লাস export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cline_checker.py | backend/services/ide_trio | stage-3: Cline ভেরিফিকেশন চেকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| gemini_writer.py | backend/services/ide_trio | stage-1: Gemini কোড রাইটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| kilo_reviewer.py | backend/services/ide_trio | stage-2: Kilo কোড রিভিউয়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/services/ingestion | collector export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| context_collector.py | backend/services/ingestion | workspace/git স্ন্যাপশট কালেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_context_collector.py | backend/services/ingestion | context_collector-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | backend/tests/services/ | টেস্ট ফাইল services ডিরেক্টরিতে নয় |
| intelligent_cache.py | backend/services | ডিপ্রিকেটেড lazy re-export shim (৩০ লাইন) | (ডিলিট — deprecated shim) | — | core.intelligent_cache canonical; shim অপ্রয়োজনীয় |
| intent_deciphering.py | backend/services | ইউজার intent শ্রেণিবিন্যাস সার্ভিস | intent_classifier.py | অপরিবর্তিত ✅ | ⚠️ 'deciphering' কল্পিত; কাজ classification |
| internet_monitor_service.py | backend/services | ইন্টারনেট আপডেট মনিটর সার্ভিস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| knowledge_qa.py | backend/services | knowledge QA + citation সার্ভিস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| living_engine.py | backend/services | মাল্টি-ডোমেইন (dev/business/ux) সলভার অর্কেস্ট্রেটর | multi_domain_solver.py | অপরিবর্তিত ✅ | ⚠️ 'living engine' রূপক নাম |
| __init__.py | backend/services/llm | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ মার্কার হিসেবে উপযুক্ত |
| llm_router.py | backend/services/llm | LLMRouter + LLMGateway + HF swarm + budget (৯৫৬ লাইন) | router.py + gateway.py-তে বিভক্ত | অপরিবর্তিত ✅ | বহু দায়িত্ব; gateway/rotator আলাদা হোক |
| providers.py | backend/services/llm | ৮টি LLM প্রোভাইডার client + BengaliNormalizer | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; BengaliNormalizer অন্যত্র সরানো ভালো |
| memory_service.py | backend/services | cascade মেমরি + vector + semantic cache + analyzer | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | বহু দায়িত্ব; ভবিষ্যতে বিভাজন বিবেচ্য |
| minio_client.py | backend/services | MinIO S3 অবজেক্ট স্টোরেজ ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| project_context_service.py | backend/services | প্রজেক্ট কনটেক্সট এন্ট্রি সংরক্ষণ/পুনরুদ্ধার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rider_tracker.py | backend/services | রাইডার লোকেশন ট্র্যাকিং + রুট অপটিমাইজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; রাইড-শেয়ারিং ডোমেইন অপ্রত্যাশিত |
| sandbox_service.py | backend/services | Docker কনটেইনারে আইসোলেটেড কোড এক্সিকিউশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Dockerfile | backend/services/scraper | scraper মাইক্রোসার্ভিস কনটেইনার ইমেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডিপ্লয়মেন্ট অ্যাসেট, নাম উপযুক্ত |
| __init__.py | backend/services/scraper | প্যাকেজ ডকস্ট্রিং (মাইক্রোসার্ভিস বর্ণনা) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ মার্কার হিসেবে উপযুক্ত |
| browser_agent.py | backend/services/scraper | Playwright ব্রাউজ/recipe অটোমেশন এজেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| main.py | backend/services/scraper | FastAPI scraper মাইক্রোসার্ভিস অ্যাপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্বাধীন সার্ভিস entrypoint, উপযুক্ত |
| requirements.txt | backend/services/scraper | scraper সার্ভিস ডিপেন্ডেন্সি তালিকা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডিপ্লয়মেন্ট অ্যাসেট, নাম উপযুক্ত |
| security.py | backend/services/scraper | SSRF-safe URL যাচাই হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| conftest.py | backend/services/scraper/tests | scraper টেস্ট fixtures | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | মাইক্রোসার্ভিসের নিজস্ব টেস্ট, গ্রহণযোগ্য |
| test_scraper_service.py | backend/services/scraper/tests | SSRF/কনকারেন্সি টেস্ট স্যুইট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | মাইক্রোসার্ভিসের নিজস্ব টেস্ট, গ্রহণযোগ্য |
| web_scraper.py | backend/services/scraper | httpx+bs4 হালকা পেজ ফেচার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| self_correction.py | backend/services | আউটপুট ভেরিফিকেশন + self-fix সার্ভিস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| smart_model_router.py | backend/services | ক্ষুদ্র SmartRouter — llm_router-এর ডুপ্লিকেট | (ডিলিট — services/llm-এ merge) | — | llm_router.py-এর সাথে ডুপ্লিকেট রাউটিং |
| __init__.py | backend/services/storage | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ মার্কার হিসেবে উপযুক্ত |
| cloud_storage.py | backend/services/storage | CloudStorageManager: বহিরাগত স্টোরেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| gcp_firestore.py | backend/services/storage | Firestore+SQLite verification queue | verification_queue.py | backend/services/ | স্টোরেজ নয়; verification queue কম্পোনেন্ট |
| tool_forge.py | backend/services | ডাইনামিক টুল সিন্থেসিস + সিকিউরিটি চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম দায়িত্ব প্রতিফলিত করে |
| video_to_code_pipeline.py | backend/services | ভিডিও→ফ্রেম→UI কোড জেনারেশন পাইপলাইন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vision_service.py | backend/services | স্টাব: হার্ডকোডেড ইমেজ অ্যানালাইসিস রিটার্ন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক, তবে বাস্তব বাস্তবায়ন দরকার |
| voice_service.py | backend/services | স্টাব: হার্ডকোডেড STT/TTS রেসপন্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক, তবে বাস্তব বাস্তবায়ন দরকার |
| Dockerfile | backend/services/worker | worker মাইক্রোসার্ভিস কনটেইনার ইমেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডিপ্লয়মেন্ট অ্যাসেট, নাম উপযুক্ত |
| main.py | backend/services/worker | Redis queue পোল করে ব্যাকগ্রাউন্ড টাস্ক চালায় | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্বাধীন worker entrypoint, উপযুক্ত |
| requirements.txt | backend/services/worker | worker সার্ভিস ডিপেন্ডেন্সি তালিকা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডিপ্লয়মেন্ট অ্যাসেট, নাম উপযুক্ত |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **৩টি রাউটার রেজিস্ট্রি সমান্তরালভাবে চলছে** — `routes/__init__.py` (try/except বয়লারপ্লেট), `routers.py` (declarative), `tier_s_routes.py`; প্রথম ও শেষটি merge/ডিলিট প্রার্থী।
- **চ্যাট/স্ট্রিমিং এন্ডপয়েন্ট ৪ জায়গায় ডুপ্লিকেট** — `chat.py`, `task.py`, `stream.py`, `stream_chat_sse.py` প্রত্যেকটিতে completion/stream আছে; একটি canonical রাখা জরুরি।
- **মডেল-রাউটিং ৪+ স্তরে বিক্ষিপ্ত** — `services/llm/llm_router.py`, `smart_model_router.py`, `dynamic_ai/` (orchestrator+provider_registry), `routes/advanced_router.py` ও `cognitive.py`; একীকরণ প্রয়োজন।
- **God-router জোড়া** — `admin.py` (৯২৫ লাইন) ও `admin_dashboard.py` (১৩৩০ লাইন); `backend/api/admin/` প্যাকেজে ভাগ করার সবচেয়ে বড় maintainability-লাভ।
- **সাফিক্স অসামঞ্জস্য** — `_api`/`_routes`/`_endpoints`/`_route` সাফিক্স ১০+ ফাইলে এলোমেলোভাবে ব্যবহৃত; সব থেকে সরানো যায়।
- **ডেড/স্টাব কোড** — `healing.py`, `vision_service.py`, `voice_service.py` হার্ডকোডেড ফেক ডেটা দেয়; `intelligent_cache.py` deprecated shim; `dependencies.py` vs `deps.py` ও `admin_v1.py` ডুপ্লিকেট।
- **⚠️ সেমান্টিক মিসম্যাচ হটস্পট** — `living_brain/living_engine`, `meta_ai`, `tier_s_routes`, `cloud_mesh`, `webhooks_ai`, `admin_librarian`, `intent_deciphering` — মার্কেটিং-ধাঁচের নামে সাধারণ CRUD/রাউটিং কোড।
- **প্ল্যাটফর্ম-বহিরাগত ডোমেইন** — `rider_tracker.py` (রাইড-শেয়ারিং) ও `escrow_service.py` (মার্কেটপ্লেস) AI-প্ল্যাটফর্মের প্রেক্ষাপটে অপ্রত্যাশিত; উৎস/ব্যবহার যাচাই করুন।


---

## ব্যাচ ০৪ — Backend Tests (অংশ ক)
**ব্যাচ:** 04 | **তালিকাভুক্ত:** 186 | **বিশ্লেষিত:** 186 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 46 | **স্থানান্তর প্রস্তাব:** 44 | **⚠️ সেমান্টিক মিসম্যাচ:** 8

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| test_platform_learner.py | backend/tests/adaptive_engine/test_platform_learner.py | platform_learner-এর doc-learning, HTTP failure, concurrency টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_agent_department.py | backend/tests/agents/test_agent_department.py | brain.agent_department এর coder/review/QA রুটিং টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | মডিউল-সঙ্গত; plural ফাইলের সাথে বিভ্রান্তি সম্ভব |
| test_agent_departments.py | backend/tests/agents/test_agent_departments.py | brain.agent_departments-এর role execution ও fallback টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_agent_factory.py | backend/tests/agents/test_agent_factory.py | core.agent_factory DynamicAgentFactory-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত; ক্যানোনিকল টেস্ট |
| test_agent_orchestrator.py | backend/tests/agents/test_agent_orchestrator.py | core.orchestration.agent_orchestrator সার্কিট ব্রেকার ও রাউটিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_agents.py | backend/tests/agents/test_agents.py | এজেন্ট CRUD/স্ট্যাটাস/API-key সার্ভিসের ১১২৪ লাইনের সাইট | test_agent_management_service.py | অপরিবর্তিত ✅ | জেনেরিক নাম; কনটেন্ট ম্যানেজমেন্ট সার্ভিস |
| test_agents_churn_prophet.py | backend/tests/agents/test_agents_churn_prophet.py | churn_prophet-এর behavior score, সেগমেন্ট, retention টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ⚠️ "prophet" অতিরঞ্জিত; তবে মডিউল-সঙ্গত |
| test_agents_insight_mage.py | backend/tests/agents/test_agents_insight_mage.py | insight_mage-এর trend/anomaly detection টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ⚠️ "mage" অতিরঞ্জিত; তবে মডিউল-সঙ্গত |
| test_agents_skill_ingestor.py | backend/tests/agents/test_agents_skill_ingestor.py | skill_ingestor-এর AST safety ও path traversal টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_agents_skill_librarian.py | backend/tests/agents/test_agents_skill_librarian.py | skill_librarian, skill_gc, morphic_adapter টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_agents_unified.py | backend/tests/agents/test_agents_unified.py | backend.agents প্যাকেজ export ও কনস্ট্রাক্ট স্মোক টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_autonomous_agent.py | backend/tests/agents/test_autonomous_agent.py | brain.autonomous_agent plan/execute/reflect লুপ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_compliance_bot.py | backend/tests/agents/test_compliance_bot.py | core.security.audit.compliance_bot consent/violation মডেল টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম উপযুক্ত; এজেন্ট-ঘেঁষা অবস্থান গ্রহণযোগ্য |
| test_email_agent.py | backend/tests/agents/test_email_agent.py | tools.social.email_agent Gmail/OTP fail-closed টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_ephemeral_executor.py | backend/tests/agents/test_ephemeral_executor.py | agents.ephemeral_executor security scanner ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিকল; api কপি এখানে একীভূত হোক |
| test_github_agent.py | backend/tests/agents/test_github_agent.py | tools.devops.github_agent connect/analyze/PR টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_headless_terminal_agent.py | backend/tests/agents/test_headless_terminal_agent.py | headless_terminal_agent কমান্ড ব্লক/টাইমআউট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_marketplace_agent.py | backend/tests/agents/test_marketplace_agent.py | tools.social.marketplace_agent search/install টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_parallel_agent_executor.py | backend/tests/agents/test_parallel_agent_executor.py | tools.parallel_agent_executor-এর parallel execution টেস্ট | অপরিবর্তিত ✅ | backend/tests/tools/ | মডিউল tools-এ; executor এজেন্ট নয় |
| test_sentinel_agent.py | backend/tests/agents/test_sentinel_agent.py | core.sentinel_agent monitoring, singleton, cancellation টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_telegram_bot.py | backend/tests/agents/test_telegram_bot.py | tools.social.telegram_bot v1 handler-এর ২৭টি টেস্ট | অপরিবর্তিত ✅ | backend/tests/tools/ | টেলিগ্রাম বট tools মডিউল; agents নয় |
| test_telegram_bot_v2.py | backend/tests/agents/test_telegram_bot_v2.py | telegram_bot v2 command/callback + security টেস্ট | test_telegram_bot_security.py | backend/tests/tools/ | "v2" অস্থায়ী প্রত্যয়; tools মডিউল |
| test_vision_agent.py | backend/tests/agents/test_vision_agent.py | tools.ai_agents.vision_agent OCR/PDF/chart টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_mlops_scripts.py | backend/tests/ai/test_mlops_scripts.py | MLOps স্ক্রিপ্ট (bias/drift/injection) importlib টেস্ট | অপরিবর্তিত ✅ | backend/tests/scripts/ | স্ক্রিপ্ট টেস্ট tests/scripts-এ মিরর হওয়া উচিত |
| test_admin.py | backend/tests/api/test_admin.py | admin fixes ও quick-actions এন্ডপয়েন্ট auth টেস্ট | test_admin_fixes_endpoints.py | অপরিবর্তিত ✅ | জেনেরিক নাম; test_admin_routes-এর সাথে বিভ্রান্তি |
| test_admin_routes.py | backend/tests/api/test_admin_routes.py | core.admin_routes TOTP, credentials, guard টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_api.py | backend/tests/api/test_api.py | core.app health ও task-execute admin-block টেস্ট | test_app_health_tasks.py | অপরিবর্তিত ✅ | জেনেরিক নাম; test_task_endpoints-এর সাথে ওভারল্যাপ |
| test_api_bootstrap.py | backend/tests/api/test_api_bootstrap.py | api/__init__ register_router সফল/fail পাথ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_api_chat.py | backend/tests/api/test_api_chat.py | api.routes.chat completion, cache, SSE stream টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_api_config_routes.py | backend/tests/api/test_api_config_routes.py | api.routes.config_routes CRUD ও wrapper টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_api_health.py | backend/tests/api/test_api_health.py | core.health_routes live/ready/config-public টেস্ট | test_health_routes.py | backend/tests/core/ | core মডিউল টেস্ট করে; test_health.py-এর সাথে বিভ্রান্তি |
| test_api_key_middleware.py | backend/tests/api/test_api_key_middleware.py | core.security.api_key_middleware dispatch টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম মডিউল-সঙ্গত; API-কনটেক্সটে অবস্থান ঠিক |
| test_api_keys.py | backend/tests/api/test_api_keys.py | api.routes.api_keys generate/hash/rate-limit টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_api_new_endpoints.py | backend/tests/api/test_api_new_endpoints.py | email/github/marketplace/config এন্ডপয়েন্ট টেস্ট | test_tool_endpoints.py | অপরিবর্তিত ✅ | "new" অস্থায়ী শব্দ; কনটেন্ট tool এন্ডপয়েন্ট |
| test_api_router.py | backend/tests/api/test_api_router.py | brain.api_router register/dispatch/capability টেস্ট | অপরিবর্তিত ✅ | backend/tests/brain/ | brain মডিউল; api ডিরেক্টরিতে ভুল স্থান |
| test_api_v1_routes.py | backend/tests/api/test_api_v1_routes.py | v1 রুট রেজিস্ট্রেশন ও prefix টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_auth_routes.py | backend/tests/api/test_auth_routes.py | api.routes.auth JWT, login, /me এন্ডপয়েন্ট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_billing_api_integration.py | backend/tests/api/test_billing_api_integration.py | billing wallet/history/checkout অনন্য অ্যাক্সেস টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_byoc_endpoints.py | backend/tests/api/test_byoc_endpoints.py | byoc_api credential upload/deployment টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_e2e_chat.py | backend/tests/api/test_e2e_chat.py | প্রম্পট নরমালাইজ/সিকিউরিটি টেস্ট; প্লেরাইট e2e নয় | test_chat_pipeline_guards.py | backend/tests/integration/ | ⚠️ নামে e2e কিন্তু কনটেন্ট ইউনিট/ইন্টিগ্রেশন |
| test_ephemeral_executor.py | backend/tests/api/test_ephemeral_executor.py | agents.ephemeral_executor cleanup/sandbox লাইফসাইকেল টেস্ট | test_ephemeral_executor_lifecycle.py | backend/tests/agents/ | agents মডিউল; agents-এর টেস্টের সাথে সহাবস্থান |
| test_ephemeral_lifecycle.py | backend/tests/api/test_ephemeral_lifecycle.py | finally-block ফাইল পার্জের একক টেস্ট | test_ephemeral_executor_lifecycle.py-এ একীভূত | backend/tests/agents/ | একক টেস্ট; লাইফসাইকেল ফাইলে বিলীন হোক |
| test_feedback.py | backend/tests/api/test_feedback.py | api.routes.feedback ingest validation টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_files_endpoint.py | backend/tests/api/test_files_endpoint.py | /api/files read/write ও traversal ব্লক টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_graph_routes.py | backend/tests/api/test_graph_routes.py | skill-graph/learning-path dry-run রুট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_health.py | backend/tests/api/test_health.py | api.routes.health live/ready রুট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_new_endpoints_sprint5.py | backend/tests/api/test_new_endpoints_sprint5.py | onboarding flow ও smell-check এন্ডপয়েন্ট টেস্ট | test_onboarding_smell_endpoints.py | অপরিবর্তিত ✅ | "sprint5" অস্থায়ী; কনটেন্ট অনুযায়ী নাম |
| test_phase4_api_server.py | backend/tests/api/test_phase4_api_server.py | api.server root/process/health/evolution এন্ডপয়েন্ট টেস্ট | test_api_server.py | অপরিবর্তিত ✅ | "phase4" অস্থায়ী নাম |
| test_resource_catalog.py | backend/tests/api/test_resource_catalog.py | resource_catalog search ও DB-driven sources টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_route_rbac_matrix.py | backend/tests/api/test_route_rbac_matrix.py | রুট-ভিত্তিক admin RBAC গার্ড ম্যাট্রিক্স টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_session_takeover.py | backend/tests/api/test_session_takeover.py | takeover token verify ও replay ব্লক টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_task_endpoints.py | backend/tests/api/test_task_endpoints.py | /tasks এন্ডপয়েন্ট execute/stream/failure টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_task_router.py | backend/tests/api/test_task_router.py | cost-guard লজিক; পুরো মডিউল level skip করা | test_task_router_cost_guard.py-এ একীভূত/বাদ | অপরিবর্তিত ✅ | ⚠️ হ্যালুসিনেটেড সারফেস; ডেড টেস্ট ক্যান্ডিডেট |
| test_workspaces_route.py | backend/tests/api/test_workspaces_route.py | workspaces bind/list target repository টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_economic_optimizer.py | backend/tests/brain/test_economic_optimizer.py | brain.economic_optimizer route optimize টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_cloud_connector.py | backend/tests/byoc/test_cloud_connector.py | byoc.cloud_connector ping/credential crypto টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_container_orchestrator.py | backend/tests/byoc/test_container_orchestrator.py | container_orchestrator deploy/rollback টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_resource_manager.py | backend/tests/byoc/test_resource_manager.py | byoc.resource_manager status/list টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cloud_db_load_test.py | backend/tests/cloud_db_load_test.py | Supabase pgvector লোড/লেটেন্সি টেস্ট স্যুইট | অপরিবর্তিত ✅ | backend/tests/load/ | লোড টেস্ট; tests/load-এ স্থানান্তর উপযুক্ত |
| conftest.py | backend/tests/conftest.py | রুট fixtures: client, db_session, sample data, assertions | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| conftest.py | backend/tests/core/conftest.py | core টেস্টের pytest_asyncio কনফিগ (৭ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_uptime_tracker_observability.py | backend/tests/core/health/test_uptime_tracker_observability.py | core.health uptime tracker failure-logging টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_swarm_orchestrator.py | backend/tests/core/orchestration/test_swarm_orchestrator.py | swarm_orchestrator intent/DAG/circuit-breaker টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_trio_pipeline.py | backend/tests/core/orchestration/test_trio_pipeline.py | trio_pipeline success/writer-failure/review ফ্লো টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_admin_dashboard_full.py | backend/tests/core/test_admin_dashboard_full.py | api.routes.admin_dashboard এর ৪১টি কম্প্রিহেনসিভ টেস্ট | test_admin_dashboard.py | backend/tests/api/ | api.routes মডিউল; "full" অস্থায়ী প্রত্যয় |
| test_admin_god.py | backend/tests/core/test_admin_god.py | core.admin_god audit-log, context, RBAC টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ⚠️ "god" অতিরঞ্জিত; মডিউল-সঙ্গত তাই অক্ষত |
| test_admin_god_security.py | backend/tests/core/test_admin_god_security.py | admin_god security; ৮টি টেস্ট test_admin_god-এর কপি | test_admin_god.py-এ একীভূত | backend/tests/core/ | ⚠️ ডুপ্লিকেট কভারেজ; একটি ফাইলে বিলীন |
| test_advanced_wiring.py | backend/tests/core/test_advanced_wiring.py | i18n/health/email/markdown ক্রস-মডিউল wiring টেস্ট | test_cross_module_wiring.py | backend/tests/integration/ | "advanced" অস্পষ্ট; আন্তঃমডিউল ইন্টিগ্রেশন |
| test_agent_factory.py | backend/tests/core/test_agent_factory.py | agent_factory + task_router ইন্টিগ্রেশন টেস্ট | test_agent_factory_integration.py | backend/tests/agents/ | agents-এর ইউনিট টেস্টের সাথে ডুপ্লিকেট ঝুঁকি |
| test_agent_supervisor_shutdown.py | backend/tests/core/test_agent_supervisor_shutdown.py | AgentSupervisor graceful shutdown রিগ্রেশন টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_approval_manager.py | backend/tests/core/test_approval_manager.py | api.routes.approval_manager + code_validator টেস্ট | অপরিবর্তিত ✅ | backend/tests/api/ | মডিউল api.routes-এ; core অবস্থান অমিল |
| test_audit_logger.py | backend/tests/core/test_audit_logger.py | core.security.audit_logger log_security_event টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_auth_jit_otp_flow.py | backend/tests/core/test_auth_jit_otp_flow.py | core.otp_router JIT OTP flow ইন্টিগ্রেশন টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_auth_middleware.py | backend/tests/core/test_auth_middleware.py | core.security auth_middleware bearer/JWT/admin টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_auth_security_extension.py | backend/tests/core/test_auth_security_extension.py | auth_middleware edge-case (JWT/public-path) টেস্ট | test_auth_middleware_edge_cases.py | অপরিবর্তিত ✅ | "extension" অস্পষ্ট; কনটেন্ট edge-case |
| test_automation.py | backend/tests/core/test_automation.py | automation dispatcher ও n8n adapter টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_automation_idempotency_coverage.py | backend/tests/core/test_automation_idempotency_coverage.py | core.automation.idempotency memory/Redis backend টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_autonoguard_engine.py | backend/tests/core/test_autonoguard_engine.py | autonoguard_engine churn/OTP/sensitive-ops টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_autonoguard_middleware.py | backend/tests/core/test_autonoguard_middleware.py | autonoguard middleware identity/OTP/blocking টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_billing_system.py | backend/tests/core/test_billing_system.py | api.routes.billing_api wallet/webhook ফ্লো টেস্ট | test_billing_wallet.py | backend/tests/api/ | billing API ও wallet মডিউল; core নয় |
| test_billing_zero_cost.py | backend/tests/core/test_billing_zero_cost.py | core.billing_plans zero-cost/free-tier পলিসি টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_brain.py | backend/tests/core/test_brain.py | brain.model_router/langgraph_agent orchestration ফ্লো টেস্ট | test_brain_orchestration_flow.py | backend/tests/brain/ | brain প্যাকেজ টেস্ট; নাম অতি সাধারণ |
| test_browser_credentials.py | backend/tests/core/test_browser_credentials.py | browser credential routes + secure store টেস্ট | test_browser_credential_routes.py | backend/tests/api/ | api.routes.browser টেস্ট; core অবস্থান অমিল |
| test_cache_manager_coverage.py | backend/tests/core/test_cache_manager_coverage.py | core.cache_manager L1/Redis/compression কভারেজ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_cache_optimization.py | backend/tests/core/test_cache_optimization.py | core.cache.* multi-layer/semantic/idempotency টেস্ট | test_cache_modules.py | অপরিবর্তিত ✅ | একাধিক cache মডিউল; "optimization" অস্পষ্ট |
| test_cloud_sandbox.py | backend/tests/core/test_cloud_sandbox.py | cloud_sandbox_orchestrator provider/TOTP টেস্ট | test_cloud_sandbox_orchestrator.py | backend/tests/core/orchestration/ | মডিউল অনুযায়ী নাম ও orchestration সাবডির |
| test_code_validator.py | backend/tests/core/test_code_validator.py | core.code_validator syntax/hallucination/autofix টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_config.py | backend/tests/core/test_config.py | core.config env-override/validation ক্যানোনিকল টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিকল; ছোট config ফাইলগুলো এখানে বিলীন হোক |
| test_config_additional.py | backend/tests/core/test_config_additional.py | config-এর CORS parsing + secret ভ্যালিডেশন ২ টেস্ট | test_config.py-এ একীভূত | backend/tests/core/ | "additional" অস্থায়ী নাম; ডুপ্লিকেট টেস্ট |
| test_config_cache.py | backend/tests/core/test_config_cache.py | core.config_cache refresh/fallback/invalidate টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_config_proxy.py | backend/tests/core/test_config_proxy.py | core.config_proxy DB-লোড/caching টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_config_validation.py | backend/tests/core/test_config_validation.py | JWT secret validation + pool dispose টেস্ট | test_config.py-এ একীভূত | backend/tests/core/ | test_config/comprehensive-এর সাথে ডুপ্লিকেট |
| test_constants.py | backend/tests/core/test_constants.py | core.constants proxy-নির্ভর মান টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_container_auditor.py | backend/tests/core/test_container_auditor.py | container_auditor stats/audit-cycle কভারেজ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_context_and_actions.py | backend/tests/core/test_context_and_actions.py | api.routes.task history/response formatting টেস্ট | test_task_context_formatting.py | backend/tests/api/ | api.routes.task টেস্ট; core অবস্থান অমিল |
| test_core.py | backend/tests/core/test_core.py | intent/router/god/schema মিশ্র grab-bag টেস্ট | test_core_mixed_smoke.py | অপরিবর্তিত ✅ | grab-bag; test_core_smoke-এর সাথে ওভারল্যাপ |
| test_core_circuit_breaker.py | backend/tests/core/test_core_circuit_breaker.py | core.circuit_breaker state-machine কভারেজ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_config.py | backend/tests/core/test_core_config.py | core.config settings field ৭টি টেস্ট | test_config.py-এ একীভূত | backend/tests/core/ | test_config.py-র সাথে প্রায় ডুপ্লিকেট |
| test_core_config_comprehensive.py | backend/tests/core/test_core_config_comprehensive.py | core.config-এর ৩৪টি বিস্তৃত টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম গ্রহণযোগ্য; বৃহৎ স্কোপ |
| test_core_decision_engine.py | backend/tests/core/test_core_decision_engine.py | core.decision_engine confidence/risk রাউটিং টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_enum_guard.py | backend/tests/core/test_core_enum_guard.py | core.enum_guard parse/fallback ক্যানোনিকল টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিকল; test_enum_guard এখানে বিলীন হোক |
| test_core_error_handling.py | backend/tests/core/test_core_error_handling.py | error_pattern_db/remediation/monitor কম্পোজিট টেস্ট | test_error_handling_composite.py | অপরিবর্তিত ✅ | কম্পোজিট; individual টেস্ট ফাইলের সাথে ওভারল্যাপ |
| test_core_exceptions.py | backend/tests/core/test_core_exceptions.py | core.exceptions hierarchy/alias টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_exceptions_and_pipeline.py | backend/tests/core/test_core_exceptions_and_pipeline.py | exceptions hierarchy + security_pipeline middleware টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম কনটেন্ট-সঙ্গত |
| test_core_feature_flags.py | backend/tests/core/test_core_feature_flags.py | core feature_flags env/DB/rollout টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_feedback.py | backend/tests/core/test_core_feedback.py | core.feedback_loop record/metrics টেস্ট | test_feedback_loop.py-এ একীভূত | backend/tests/core/ | test_feedback_loop.py-র সাথে ডুপ্লিকেট |
| test_core_health_check.py | backend/tests/core/test_core_health_check.py | core.health_check-এর ৩০টি কম্প্রিহেনসিভ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_immune_system.py | backend/tests/core/test_core_immune_system.py | core.immune_system AST scanner ক্যানোনিকল টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিকল; scanner টেস্ট এখানে বিলীন হোক |
| test_core_knowledge_qa.py | backend/tests/core/test_core_knowledge_qa.py | backend.skills vector search/RPC QA টেস্ট | test_skills_vector_search.py | backend/tests/unit/skills/ | skills মডিউল টেস্ট; core-এ ভুল স্থান |
| test_core_language_router.py | backend/tests/core/test_core_language_router.py | language_router + intent_router routing টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_output_validator.py | backend/tests/core/test_core_output_validator.py | core.output_validator validator/consensus ক্যানোনিকল টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিকল; অন্য দুই কপি এখানে বিলীন হোক |
| test_core_rate_limiter.py | backend/tests/core/test_core_rate_limiter.py | core.rate_limiter memory/async/middleware টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_retry_budget.py | backend/tests/core/test_core_retry_budget.py | core.retry_budget token-bucket টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_retry_handler.py | backend/tests/core/test_core_retry_handler.py | core.retry_handler sync/async backoff টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_sandbox.py | backend/tests/core/test_core_sandbox.py | microvm/file-gate/auditor কম্পোজিট sandbox টেস্ট | test_sandbox_composite.py | অপরিবর্তিত ✅ | কম্পোজিট; microvm/container টেস্টের সাথে ওভারল্যাপ |
| test_core_schema_validator.py | backend/tests/core/test_core_schema_validator.py | core.schema_validator register/retry টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_smoke.py | backend/tests/core/test_core_smoke.py | logging/config/llm_gateway বেসিক স্মোক টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_target_registry.py | backend/tests/core/test_core_target_registry.py | core.target_registry permission-scope টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_task_contract.py | backend/tests/core/test_core_task_contract.py | core.task_contract state-machine/contract টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_universal_rules.py | backend/tests/core/test_core_universal_rules.py | core.universal_rules চেক/ক্লাসিফিকেশন টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_cost_guard.py | backend/tests/core/test_cost_guard.py | core.cost_guard budget allow/block ক্যানোনিকল টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিকল; coverage কপি এখানে বিলীন হোক |
| test_cost_guard_coverage_full.py | backend/tests/core/test_cost_guard_coverage_full.py | core.cost_guard-এর বাজেট/স্পেন্ড কভারেজ টেস্ট | test_cost_guard.py-এ একীভূত | backend/tests/core/ | ডুপ্লিকেট; "_coverage_full" অস্থায়ী প্রত্যয় |
| test_coverage_gaps.py | backend/tests/core/test_coverage_gaps.py | decision_engine init/decide ২টি মৌলিক টেস্ট | test_decision_engine_basic.py | অপরিবর্তিত ✅ | ⚠️ প্রসেস-নাম; test_core_decision_engine ডুপ্লিকেট |
| test_database_async_proxy.py | backend/tests/core/test_database_async_proxy.py | database.supabase_client dynamic async proxy টেস্ট | অপরিবর্তিত ✅ | backend/tests/database/ | database প্যাকেজ টেস্ট; core অবস্থান অমিল |
| test_db_coverage.py | backend/tests/core/test_db_coverage.py | core.db engine/session/health কভারেজ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_db_repository.py | backend/tests/core/test_db_repository.py | core.db_repository primary/fallback fetch টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_dependency_guards.py | backend/tests/core/test_dependency_guards.py | ভারী dependency unguarded-import CI গার্ড টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_docker_sandbox.py | backend/tests/core/test_docker_sandbox.py | tools.devops.docker_sandbox execution firewall টেস্ট | অপরিবর্তিত ✅ | backend/tests/tools/ | tools.devops মডিউল; core অবস্থান অমিল |
| test_e2e.py | backend/tests/core/test_e2e.py | vscode/mobile/voice এন্ড-টু-এন্ড ফ্লো টেস্ট | অপরিবর্তিত ✅ | backend/tests/e2e/ | e2e টেস্ট tests/e2e-তে থাকা উচিত |
| test_e2e_media.py | backend/tests/core/test_e2e_media.py | media upload-URL জেনারেশন e2e টেস্ট | অপরিবর্তিত ✅ | backend/tests/e2e/ | e2e টেস্ট tests/e2e-তে থাকা উচিত |
| test_embeddings_coverage.py | backend/tests/core/test_embeddings_coverage.py | core.embeddings hashing/cache/vector কভারেজ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_enum_guard.py | backend/tests/core/test_enum_guard.py | core.enum_guard-এর ৩টি সংক্ষিপ্ত টেস্ট | test_core_enum_guard.py-এ একীভূত | backend/tests/core/ | ডুপ্লিকেট কভারেজ; এক ফাইলে বিলীন |
| test_env_validator_coverage.py | backend/tests/core/test_env_validator_coverage.py | core.env_validator scoring/format কভারেজ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_episodic_memory.py | backend/tests/core/test_episodic_memory.py | memory.episodic_memory store/recall/summarize টেস্ট | অপরিবর্তিত ✅ | backend/tests/memory/ | memory প্যাকেজ মিরর করা উচিত |
| test_error_pattern_db.py | backend/tests/core/test_error_pattern_db.py | core.error_pattern_db logging/pattern টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_error_remediation.py | backend/tests/core/test_error_remediation.py | core.error_remediation qdrant lookup টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_evolution_engine.py | backend/tests/core/test_evolution_engine.py | core.self_evolution.evolution_engine daily-run টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_evolution_pipeline.py | backend/tests/core/test_evolution_pipeline.py | auto_skill_creator + skills installer পাইপলাইন টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_evolution_self_improvement.py | backend/tests/core/test_evolution_self_improvement.py | self_evolution_agent fitness/prune/refactor টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_evolution_unified.py | backend/tests/core/test_evolution_unified.py | self_evolution মডিউল import/construct স্মোক টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_factual_verifier.py | backend/tests/core/test_factual_verifier.py | core.factual_verifier safe-eval math টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_feedback_loop.py | backend/tests/core/test_feedback_loop.py | core.feedback_loop record/metrics/handle ক্যানোনিকল টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিকল; test_core_feedback এখানে বিলীন হোক |
| test_gcp_firestore.py | backend/tests/core/test_gcp_firestore.py | core.gcp_firestore queue ops ফেক-ক্লায়েন্ট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_gcp_integration.py | backend/tests/core/test_gcp_integration.py | brain/core/tools GCP ক্রস-মডিউল ইন্টিগ্রেশন টেস্ট | অপরিবর্তিত ✅ | backend/tests/integration/ | আন্তঃমডিউল ইন্টিগ্রেশন; integration ডিরেক্টরি উপযুক্ত |
| test_grpc_client.py | backend/tests/core/test_grpc_client.py | core.grpc_client submit/status/audit টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_hallucination_guard.py | backend/tests/core/test_hallucination_guard.py | ৬টি security/validator মডিউলের কম্পোজিট টেস্ট | বিদ্যমান পৃথক টেস্টে একীভূত | একীভূত (ফাইল বিলুপ্ত) | প্রতিটি মডিউলের নিজস্ব টেস্ট আছে; ডুপ্লিকেট |
| test_hotfix_regressions.py | backend/tests/core/test_hotfix_regressions.py | config secret ও rate_limit রিগ্রেশন ৩ টেস্ট | test_config_rate_limit_regressions.py | অপরিবর্তিত ✅ | "hotfix" অস্থায়ী নাম |
| test_human_behavior.py | backend/tests/core/test_human_behavior.py | core.human_behavior mouse/type সিমুলেশন টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_idempotency_middleware.py | backend/tests/core/test_idempotency_middleware.py | core.idempotency_middleware scope/key টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_immune_system.py | backend/tests/core/test_immune_system.py | auto_remediation + rules_mutator টেস্ট (immune নয়) | test_auto_remediation_rules.py | অপরিবর্তিত ✅ | ⚠️ নাম immune_system কিন্তু কনটেন্ট ভিন্ন মডিউল |
| test_immune_system_scanner.py | backend/tests/core/test_immune_system_scanner.py | core.immune_system banned-import/eval টেস্ট | test_core_immune_system.py-এ একীভূত | backend/tests/core/ | ডুপ্লিকেট কভারেজ; ক্যানোনিকল ফাইলে বিলীন |
| test_input_sanitizer.py | backend/tests/core/test_input_sanitizer.py | core.security.input_sanitizer PII/scope টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_integration_phase3.py | backend/tests/core/test_integration_phase3.py | llm_gateway self-healer integration ১ টেস্ট | test_llm_gateway_self_healing.py | অপরিবর্তিত ✅ | "phase3" অস্থায়ী নাম |
| test_intelligent_cache_coverage.py | backend/tests/core/test_intelligent_cache_coverage.py | core.intelligent_cache redis/circuit কভারেজ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_intent.py | backend/tests/core/test_intent.py | core.intent IntentClassifier classification টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_knowledge_base.py | backend/tests/core/test_knowledge_base.py | core.knowledge_base memory save/get টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_lifespan.py | backend/tests/core/test_lifespan.py | FastAPI lifespan startup/shutdown টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_llm_gateway_consolidation.py | backend/tests/core/test_llm_gateway_consolidation.py | gateway/router shared circuit-breaker টেস্ট | test_llm_gateway_resilience.py | অপরিবর্তিত ✅ | "consolidation" প্রসেস-শব্দ; কনটেন্ট resilience |
| test_log_batcher.py | backend/tests/core/test_log_batcher.py | core.log_batcher flush/requeue টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_long_term_memory.py | backend/tests/core/test_long_term_memory.py | memory.long_term_memory remember/context টেস্ট | অপরিবর্তিত ✅ | backend/tests/memory/ | memory প্যাকেজ মিরর করা উচিত |
| test_main_entrypoint_guards.py | backend/tests/core/test_main_entrypoint_guards.py | main.py signal/worker/reload guard টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_maintenance_pipeline.py | backend/tests/core/test_maintenance_pipeline.py | maintenance_pipeline health/auto-remediate টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_markdown_export.py | backend/tests/core/test_markdown_export.py | markdown export/history/share এন্ডপয়েন্ট টেস্ট | অপরিবর্তিত ✅ | backend/tests/api/ | markdown API রুট টেস্ট; api-তে স্থানান্তর |
| test_mcp_allowlist.py | backend/tests/core/test_mcp_allowlist.py | core.mcp_allowlist server/tool validation টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_mcp_client.py | backend/tests/core/test_mcp_client.py | core.mcp_client fallback/tag-filter টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_mcp_servers_integration.py | backend/tests/core/test_mcp_servers_integration.py | tools.mcp.* ৪ সার্ভারের ১১৭টি টেস্ট | অপরিবর্তিত ✅ | backend/tests/tools/ | tools.mcp মডিউল টেস্ট; tools-এ মিরর |
| test_media_r2.py | backend/tests/core/test_media_r2.py | R2 storage client + media upload-url টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান মোটামুটি উপযুক্ত |
| test_memory_manager.py | backend/tests/core/test_memory_manager.py | core.memory_manager aggressive cleanup টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_memory_service.py | backend/tests/core/test_memory_service.py | services.memory_service CascadeMemory + vectorize টেস্ট | অপরিবর্তিত ✅ | backend/tests/services/ | services প্যাকেজ মিরর করা উচিত |
| test_microvm_sandbox.py | backend/tests/core/test_microvm_sandbox.py | core.microvm_sandbox validation/docker/execute টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_models_evolution.py | backend/tests/core/test_models_evolution.py | models.evolution SkillFitness/CodeProposal টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম মডিউল-সঙ্গত; অবস্থান গ্রহণযোগ্য |
| test_multi_tenant_isolation.py | backend/tests/core/test_multi_tenant_isolation.py | core.tenant_db isolation/mock-mode টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_multicloud.py | backend/tests/core/test_multicloud.py | brain.parallel_cloud_router weight/health টেস্ট | test_parallel_cloud_router.py | backend/tests/brain/ | brain মডিউল; "multicloud" অস্পষ্ট |
| test_nats_messaging.py | backend/tests/core/test_nats_messaging.py | core.messaging.nats_messaging pub/sub/kv টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_orchestrators_crew.py | backend/tests/core/test_orchestrators_crew.py | crew_departments agents + shared workspace টেস্ট | test_crew_departments.py | backend/tests/core/orchestration/ | orchestration সাবডিরে মিরর; মডিউল-সঙ্গত নাম |
| test_origin_validator.py | backend/tests/core/test_origin_validator.py | core.security.origin_validator origin/role টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_output_validator.py | backend/tests/core/test_output_validator.py | output_validator consensus/scorer টেস্ট (কপি ১) | test_core_output_validator.py-এ একীভূত | backend/tests/core/ | একই মডিউলের তৃতীয় টেস্ট ফাইল; ডুপ্লিকেট |
| test_output_validator_coverage.py | backend/tests/core/test_output_validator_coverage.py | output_validator consensus/scorer টেস্ট (কপি ২) | test_core_output_validator.py-এ একীভূত | backend/tests/core/ | ডুপ্লিকেট কভারেজ ফাইল |
| test_payments.py | backend/tests/core/test_payments.py | payment plans/checkout/webhook এন্ডপয়েন্ট টেস্ট | test_payment_endpoints.py | backend/tests/api/ | পেমেন্ট API রুট টেস্ট; core নয় |
| test_pgbouncer_pool.py | backend/tests/core/test_pgbouncer_pool.py | core.pgbouncer_pool singleton/acquire টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_playwright_manager.py | backend/tests/core/test_playwright_manager.py | core.playwright_manager browser lifecycle টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_predictive_resilience.py | backend/tests/core/test_predictive_resilience.py | core.resilience predictive metrics/breaker টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_prompt_handler.py | backend/tests/core/test_prompt_handler.py | core.prompt_handler normalize/tokenize টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_provider_router.py | backend/tests/core/test_provider_router.py | core.llm.provider_router circuit/weight টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_pubsub.py | backend/tests/core/test_pubsub.py | core.swarm_pubsub broadcast/error-isolation টেস্ট | test_swarm_pubsub.py | অপরিবর্তিত ✅ | মডিউল নাম swarm_pubsub; নাম-মিল উন্নত হোক |
| test_query_cache_coverage.py | backend/tests/core/test_query_cache_coverage.py | core.cache.query_cache hit/miss/redis কভারেজ টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **ডুপ্লিকেট টেস্ট ফাইল ক্লাস্টার (সবচেয়ে বড় সমস্যা):** একই মডিউলের ২-৩টি করে টেস্ট ফাইল — `core.output_validator` (৩টি: test_core_output_validator, test_output_validator, test_output_validator_coverage), `core.config` (৫টি: test_config, test_core_config, test_core_config_comprehensive, test_config_additional, test_config_validation), `core.feedback_loop` (২টি), `core.enum_guard` (২টি), `core.cost_guard` (২টি), `core.immune_system` (৩টি), `core.agent_factory` (২টি), `ephemeral_executor` (৩টি: agents + api + lifecycle)। প্রতিটি ক্লাস্টারে একটি ক্যানোনিকল ফাইল রেখে বাকিগুলো একীভূত করার সুপারিশ।
- **ডেড টেস্ট ক্যান্ডিডেট:** `api/test_task_router.py` পুরো ফাইল module-level `pytest.skip("Hallucinated config surface...")` দিয়ে বন্ধ; `core/test_immune_system.py`-এর একটি টেস্ট `@pytest.mark.skip`। এগুলো হয় মুছে ফেলা বা বাস্তব মডিউলের সাথে পুনর্লিখন দরকার।
- **ভুল অবস্থান (mislocation) প্যাটার্ন:** `tests/core/`-এ এমন অনেক ফাইল আছে যারা `api.routes.*` (billing, payments, admin_dashboard, approval_manager, browser, markdown, task-context), `memory.*`, `services.*`, `brain.*`, `tools.*` বা `database.*` মডিউল টেস্ট করে — মডিউল-মিররিং অনুযায়ী সংশ্লিষ্ট ডিরেক্টরিতে (tests/api, tests/memory, tests/services, tests/brain, tests/tools, tests/e2e, tests/integration) সরানোর প্রস্তাব।
- **অস্থায়ী/প্রসেস-ভিত্তিক নাম (temporal naming):** `test_new_endpoints_sprint5.py`, `test_phase4_api_server.py`, `test_integration_phase3.py`, `test_hotfix_regressions.py`, `test_api_new_endpoints.py`, `test_advanced_wiring.py`, `*_coverage_full.py` — স্প্রিন্ট/ফেজ/হটফিক্স নাম সময়ের সাথে অর্থহীন হয়; কনটেন্ট-ভিত্তিক নাম দেওয়া হয়েছে।
- **সেমান্টিক-মিসম্যাচ হটস্পট:** `admin_god` (সাধারণ admin CRUD-এ "god"), `churn_prophet`, `insight_mage` (সাধারণ স্ট্যাটাসে prophet/mage) — টেস্ট নাম মডিউল অনুসরণ করায় অপরিবর্তিত রাখা হয়েছে, তবে মূল মডিউলের নাম পরিবর্তনের প্রস্তাব ব্যাচ ০১/০২/০৭-এর সাথে সমন্বয় করা উচিত। `test_immune_system.py` ব্যতিক্রম — নামই ভুল (কনটেন্ট auto_remediation/rules_mutator)।
- **বিভ্রান্তিকর নিকট-নাম জোড়া:** `test_agent_department.py` vs `test_agent_departments.py` (আলাদা মডিউল!), `api/test_health.py` vs `api/test_api_health.py` (ভিন্ন মডিউল), `api/test_admin.py` vs `api/test_admin_routes.py`, `core/test_e2e.py` vs `core/test_e2e_media.py`। রিনেমের মাধ্যমে এই অস্পষ্টতা দূর করা হয়েছে।
- **`test_core.py` ও `test_agents.py` grab-bag:** একাধিক আনসম্বদ্ধ মডিউলের টেস্ট এক ফাইলে (যথাক্রমে ১২৫L ও ১১২৪L) — বিভাজন বা কনটেন্ট-সঙ্গত নামকরণ প্রয়োজন।
- **মোট সুপারিশ:** ৪৬টি রিনেম, ৪৪টি স্থানান্তর/একীভূতকরণ, ৮টি ⚠️ সেমান্টিক মিসম্যাচ; বাকি ~১০০+ ফাইলের নাম-অবস্থান ইতোমধ্যে উপযুক্ত (বিশেষত byoc/, brain/, adaptive_engine/, core/orchestration/, core/health/ পুরোপুরি মিররড)।


---

## ব্যাচ ০৫ — Backend Tests (অংশ খ)
**ব্যাচ:** 05 | **তালিকাভুক্ত:** 185 | **বিশ্লেষিত:** 185 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 22 | **স্থানান্তর প্রস্তাব:** 24 | **⚠️ সেমান্টিক মিসম্যাচ:** 8

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| test_rbac.py | backend/tests/core/test_rbac.py | RBAC রোল-পারমিশন ম্যাট্রিক্স, authorize, scopes ও expiry যাচাই | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_redis_cache.py | backend/tests/core/test_redis_cache.py | SecureRedisManager init, অপারেশন, idempotency lock, multi-level cache | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_reliability_plane.py | backend/tests/core/test_reliability_plane.py | Failure fingerprint, retry budget, startup validator, reliability controller | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_retry_handler_coverage.py | backend/tests/core/test_retry_handler_coverage.py | Sync/async retry, jitter, callback ও budget-সংযুক্ত retry | test_retry_with_budget.py | অপরিবর্তিত ✅ | "_coverage" সাফিক্স অস্পষ্ট; test_core_retry_handler-এর সাথে ওভারল্যাপ |
| test_rules_mutator.py | backend/tests/core/test_rules_mutator.py | Redis-ভিত্তিক IP block/unblock ও blocked-check | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম মডিউলের সাথে মেলে (unit_light কপি দ্রষ্টব্য) |
| test_schema_validator.py | backend/tests/core/test_schema_validator.py | Pydantic schema validator ও নেস্টেড মডেল ভ্যালিডেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_secret_vault.py | backend/tests/core/test_secret_vault.py | ProductionSecretVault init, fallback, cache, fetch, connections | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_security.py | backend/tests/core/test_security.py | JWT secret persistence, CORS validation, rate-limit fail-mode | test_security_config.py | অপরিবর্তিত ✅ | জেনেরিক নাম; test_security_regression-এর সাথে JWT ওভারল্যাপ |
| test_security_firewall.py | backend/tests/core/test_security_firewall.py | PromptFirewall ভ্যালিডেশন, Bengali enforcement, constitutional filter | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_security_regression.py | backend/tests/core/test_security_regression.py | Production JWT secret ও auth middleware invalid-token regression | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_security_vault.py | backend/tests/core/test_security_vault.py | Token encrypt/decrypt (Fernet) ও empty-invalid এজ কেস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_self_evolution_agent.py | backend/tests/core/test_self_evolution_agent.py | Skill fitness evaluate, pruning, refactor trigger, lifecycle | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_self_healer.py | backend/tests/core/test_self_healer.py | AutoHealer fix proposal, dangerous code rejection, impact score | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_skill_execution_pipeline.py | backend/tests/core/test_skill_execution_pipeline.py | FakeSkill দিয়ে SkillExecutionPipeline এক্সিকিউশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_skill_manager.py | backend/tests/core/test_skill_manager.py | Unsafe-code block, DB load, MCP discovery fallback | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_sliding_window_memory.py | backend/tests/core/test_sliding_window_memory.py | Chunk persist, recall, context budget, checkpoint resume | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_startup_validator.py | backend/tests/core/test_startup_validator.py | Startup validator empty app-name fail ও pass পাথ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_stealth_networking.py | backend/tests/core/test_stealth_networking.py | Proxy rotation, stealth HTTP headers, sandbox Docker requirement | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম মডিউলের সাথে মেলে |
| test_stream.py | backend/tests/core/test_stream.py | Streaming endpoint auth (token ছাড়া/সহ) FastAPI টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_swarm_orchestrator.py | backend/tests/core/test_swarm_orchestrator.py | SwarmOrchestrator agent init ও task execution | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম উপযুক্ত (duplicate basename দ্রষ্টব্য) |
| test_swarm_pubsub.py | backend/tests/core/test_swarm_pubsub.py | SwarmPubSub init, subscribe, broadcast, halt flag, singleton | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_swarm_pubsub_extended.py | backend/tests/core/test_swarm_pubsub_extended.py | Halt set/clear, JSON broadcast, subscribe stream, singleton | test_swarm_pubsub.py-এ মার্জ | অপরিবর্তিত ✅ | একই মডিউলের বিভক্ত কভারেজ; একত্র করুন |
| test_target_registry.py | backend/tests/core/test_target_registry.py | Target register/unregister, read-only permission guard | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_tier8.py | backend/tests/core/test_tier8.py | Tier-8 meta-agent services init ও ServiceRegistry ইন্টিগ্রেশন | test_meta_agent_services.py | অপরিবর্তিত ✅ | ⚠️ "tier8" বিমূর্ত; মডিউল রিনেমের সাথে সিঙ্ক করুন |
| test_tier8_evolution.py | backend/tests/core/test_tier8_evolution.py | AutoHealer mutation guardrail, failure fingerprint, model trainer | test_auto_healer_mutation.py | backend/tests/services/ | ⚠️ tier8 নাম অমিল; AutoHealer services মডিউল |
| test_token_budget.py | backend/tests/core/test_token_budget.py | Token estimation, truncation, budget exhaustion emission | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_token_deductor.py | backend/tests/core/test_token_deductor.py | Distributed lock fail-closed, deduct success, insufficient funds | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_universal_rules.py | backend/tests/core/test_universal_rules.py | Rules load/save/apply, atomic write, cost boundary | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_universal_rules_extended.py | backend/tests/core/test_universal_rules_extended.py | Provider selection, task classification, PII, rule validation | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | extended মডিউলের মিরর, উপযুক্ত |
| test_upload_validator.py | backend/tests/core/test_upload_validator.py | Upload validator: extension, size, type রিজেকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_voice_stream.py | backend/tests/core/test_voice_stream.py | Voice streaming: text requirement, audio/mpeg response | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| accessibility.spec.ts | backend/tests/e2e/accessibility.spec.ts | Playwright+axe: homepage ও admin dashboard WCAG accessibility | অপরিবর্তিত ✅ | e2e/ (repo root) | Frontend UI টেস্ট backend/tests-এ বসানো অগোছালো |
| active-monitor.spec.ts | backend/tests/e2e/active-monitor.spec.ts | Production monitor: admin dashboard client-side error শিকার | অপরিবর্তিত ✅ | e2e/ (repo root) | Frontend e2e backend/tests-এ অন্তর্ভুক্ত |
| admin-dashboard.spec.ts | backend/tests/e2e/admin-dashboard.spec.ts | Dashboard load, Java Worker widget, orchestration chat command | অপরিবর্তিত ✅ | e2e/ (repo root) | Frontend e2e; describe-এ "Nexus" ব্র্যান্ডিং অপ্রয়োজনীয় |
| admin-login.spec.ts | backend/tests/e2e/admin-login.spec.ts | Admin login validation ও invalid credentials flow | অপরিবর্তিত ✅ | e2e/ (repo root) | Frontend e2e backend/tests-এ অন্তর্ভুক্ত |
| chat.spec.ts | backend/tests/e2e/chat.spec.ts | Chat UI message send flow | অপরিবর্তিত ✅ | e2e/ (repo root) | Frontend e2e backend/tests-এ অন্তর্ভুক্ত |
| user-login.spec.ts | backend/tests/e2e/user-login.spec.ts | User login validation, invalid credentials, register navigation | অপরিবর্তিত ✅ | e2e/ (repo root) | Frontend e2e backend/tests-এ অন্তর্ভুক্ত |
| visual.spec.ts | backend/tests/e2e/visual.spec.ts | Visual regression snapshot: homepage ও ConsentMatrixModal | অপরিবর্তিত ✅ | e2e/ (repo root) | Frontend visual test backend/tests-এ অন্তর্ভুক্ত |
| test_cost_optimizer.py | backend/tests/engine/test_cost_optimizer.py | Complexity classifier ও CostOptimizer routing/callback | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_smart_router.py | backend/tests/engine/test_smart_router.py | Smart router model selection | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_tree_of_thought.py | backend/tests/engine/test_tree_of_thought.py | Tree-of-thought reasoning ফ্লো | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_vector_db.py | backend/tests/engine/test_vector_db.py | Vector DB save ও similar-experience search | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_hitl_engine.py | backend/tests/hitl/test_hitl_engine.py | HITL: risk, approval queue, API, concurrency, audit, performance | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (বড় ফাইল, ভাগযোগ্য) |
| test_integration_suite.py | backend/tests/integration/test_integration_suite.py | Agent journey, memory, security, DB, performance ইন্টিগ্রেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_learning.py | backend/tests/learning/test_learning.py | Experience record/retrieve ও outcome analyzer classification | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_pattern_and_hypothesis.py | backend/tests/learning/test_pattern_and_hypothesis.py | Pattern detector, evidence analyzer, hypothesis conversion | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_advanced_model_router.py | backend/tests/llm/test_advanced_model_router.py | Advanced router: complexity, models, routing, budget | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_advanced_model_router_regression.py | backend/tests/llm/test_advanced_model_router_regression.py | Router regression: tier0 tools, scoring, deterministic routing | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (বেস ফাইলের সাথে ওভারল্যাপ দ্রষ্টব্য) |
| locustfile.py | backend/tests/load/locustfile.py | Locust load test: skills fetch, auth token, wait time | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | Locust কনভেনশন অনুযায়ী নাম আদর্শ |
| test_memory_service.py | backend/tests/memory/test_memory_service.py | CascadeMemoryService sqlite/pgvector fallback ও insert | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_anti_hacking.py | backend/tests/middleware/test_anti_hacking.py | Mismatch OTP, subnet caution, cooldown suppression | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_middleware_anti_hacking.py | backend/tests/middleware/test_middleware_anti_hacking.py | Admin dispatch context match/mismatch, enforce mode, redis edge | test_anti_hacking_admin_context.py | অপরিবর্তিত ✅ | ডিরেক্টরি-প্রিফিক্স রিডান্ড্যান্সি; ফোকাস স্পষ্ট করুন |
| test_cost_auditor.py | backend/tests/monitoring/test_cost_auditor.py | CostAuditor init ও no-history report | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_master_cognitive_orchestrator.py | backend/tests/orchestration/test_master_cognitive_orchestrator.py | Pipelines: healing, synthesis, audit, governed evolution | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_credit_system.py | backend/tests/p2p_tests/test_credit_system.py | Credit ledger earn/spend/balance, opt-in/out, broker match | অপরিবর্তিত ✅ | backend/tests/p2p/ | "p2p_tests" সাফিক্স অপ্রয়োজনীয় |
| test_secure_tunnel.py | backend/tests/p2p_tests/test_secure_tunnel.py | SecureTunnel create/terminate lifecycle | অপরিবর্তিত ✅ | backend/tests/p2p/ | একই ডিরেক্টরি রিনেম কারণ |
| test_hybrid_retriever.py | backend/tests/rag/test_hybrid_retriever.py | BM25 sparse, RRF fusion, hybrid fallback | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_budget_guard.py | backend/tests/runtime/test_budget_guard.py | Pre-execution pass, exhaustion rejection, limit breach | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_planner.py | backend/tests/runtime/test_planner.py | Planner multi-step plan creation | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_task_runtime.py | backend/tests/runtime/test_task_runtime.py | Runtime execution success ও strict verification failure | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_knowledge_extractor.py | backend/tests/scout_tests/test_knowledge_extractor.py | KnowledgeExtractor init ও extract (ST ছাড়া/সহ) | অপরিবর্তিত ✅ | backend/tests/scout/ | "scout_tests" সাফিক্স অপ্রয়োজনীয় |
| test_web_crawler_agent.py | backend/tests/scout_tests/test_web_crawler_agent.py | Approved-domain enforcement ও crawl টেস্ট | অপরিবর্তিত ✅ | backend/tests/scout/ | একই ডিরেক্টরি রিনেম কারণ |
| test_billing_fraud_detector.py | backend/tests/scripts/test_billing_fraud_detector.py | FraudDetector init, ledger scan, anomaly, alert | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_billing_quota_enforcer.py | backend/tests/scripts/test_billing_quota_enforcer.py | Pricing tiers, wallet, quota enforcement, suspension | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_billing_usage_reporter.py | backend/tests/scripts/test_billing_usage_reporter.py | Tenant listing, firestore usage, report generation | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_auth.py | backend/tests/security/test_auth.py | MockAuthService: registration, password rules, tokens, roles | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_cross_tenant_isolation.py | backend/tests/security/test_cross_tenant_isolation.py | WS auth, RBAC, object ownership, memory scoping | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_database_readiness_regression.py | backend/tests/security/test_database_readiness_regression.py | DB URL resolution, lazy engine, health check regression | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_dead_route_wiring.py | backend/tests/security/test_dead_route_wiring.py | Dead route defaults ও router wiring imports | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_hitl_state_machine.py | backend/tests/security/test_hitl_state_machine.py | HITL: replay, tamper, expiry, concurrency guard | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_patch_v4_render_log_fixes.py | backend/tests/security/test_patch_v4_render_log_fixes.py | Pooled PG DDL, writer DSN, HITL router, lazy singleton regression | test_pooled_pg_hitl_admin_regression.py | অপরিবর্তিত ✅ | প্যাচ-সংখ্যা নাম দীর্ঘমেয়াদে অর্থহীন |
| test_refresh_path_regression.py | backend/tests/security/test_refresh_path_regression.py | Refresh path public classification ও fail-closed validation | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_sql_prevention.py | backend/tests/security/test_sql_prevention.py | Input sanitizer, parameterized builder, inspector, SQL auditor | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_tool_policy_gateway.py | backend/tests/security/test_tool_policy_gateway.py | Risk levels, admin gate, budget block, audited execution | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_learning_engine_shim.py | backend/tests/services/dynamic_ai/test_learning_engine_shim.py | Learning engine shim delegation ও orchestrator wiring | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_diagram_parser_service.py | backend/tests/services/test_diagram_parser_service.py | Mermaid/PlantUML/draw.io parsing ও infra conversion | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_dynamic_planner.py | backend/tests/services/test_dynamic_planner.py | Task DAG topo-sort, cycle detection, pipeline planning | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_economic_router.py | backend/tests/services/test_economic_router.py | Cost estimation, viable providers, budget routing | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_email_service.py | backend/tests/services/test_email_service.py | EmailService settings, API key, Resend integration | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_escrow_service.py | backend/tests/services/test_escrow_service.py | Escrow status, lifecycle ও service operations | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_expert_router.py | backend/tests/services/test_expert_router.py | MoE prompt classification, model chain, gateway integration | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_factory_wiring.py | backend/tests/services/test_factory_wiring.py | Factory production instance wiring ও safe process | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_generation_monitor.py | backend/tests/services/test_generation_monitor.py | Confidence tokens, factual claims, attribution, consistency | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_graph_service.py | backend/tests/services/test_graph_service.py | Graph service dry-run ও real connection | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_health_monitor.py | backend/tests/services/test_health_monitor.py | System metrics, readiness/liveness, prometheus recording | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_health_monitor_routes.py | backend/tests/services/test_health_monitor_routes.py | /health endpoint JSON, keys, degraded status | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_integration_layer.py | backend/tests/services/test_integration_layer.py | SupremeAIIntegrator init, process flows, shutdown | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_intent_deciphering.py | backend/tests/services/test_intent_deciphering.py | Intent separation, latent constraints, Bengali, memory recall | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_intent_router.py | backend/tests/services/test_intent_router.py | Keyword routing, firebase precedence, confirmation requirement | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_knowledge_qa.py | backend/tests/services/test_knowledge_qa.py | Citation model ও KnowledgeQAService | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_language_router.py | backend/tests/services/test_language_router.py | Language detection ও provider routing override | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম উপযুক্ত (unit_light কপি দ্রষ্টব্য) |
| test_living_engine.py | backend/tests/services/test_living_engine.py | Bengali demands: bugfix, performance, RBAC, synthesis | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম মডিউলের মিরর |
| test_llm_router.py | backend/tests/services/test_llm_router.py | LLM router: token budget, normalizer, capabilities, routing | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_minio_client.py | backend/tests/services/test_minio_client.py | MinIO upload, download, presigned URL, list | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_model_router_unit.py | backend/tests/services/test_model_router_unit.py | Circuit breaker states, response cache TTL, openai helper | test_model_router_resilience.py | অপরিবর্তিত ✅ | "_unit" সাফিক্স অর্থহীন; রেজিলিয়েন্স ফোকাস |
| test_monitoring.py | backend/tests/services/test_monitoring.py | Docker sandbox security, cost auditor, plan sorter স্মোক | test_monitoring_tools.py | অপরিবর্তিত ✅ | মিশ্র টুল স্মোক; নাম বিস্তৃত |
| test_otp_router.py | backend/tests/services/test_otp_router.py | OTP helpers, channel preference, delivery, fallback | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_performance_aware_router.py | backend/tests/services/test_performance_aware_router.py | Provider health, latency score, routing fallback | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_phase2_intelligence.py | backend/tests/services/test_phase2_intelligence.py | Reasoning modes, dev/business/UX adapters, pattern recognition | test_advanced_reasoning_adapters.py | অপরিবর্তিত ✅ | ⚠️ ফেজ-নম্বর নাম অস্থায়ী; কনটেন্ট বর্ণনা করুন |
| test_phase3_evolution.py | backend/tests/services/test_phase3_evolution.py | Auto-tuner, strategy optimizer, rollback, scaling, evolution | test_evolution_components.py | অপরিবর্তিত ✅ | ⚠️ ফেজ-নম্বর নাম অস্থায়ী |
| test_phase3_intelligence.py | backend/tests/services/test_phase3_intelligence.py | Synthetic data pipeline, EWC loss, voice/vision services | test_synthetic_voice_vision.py | অপরিবর্তিত ✅ | ⚠️ ফেজ-নম্বর নাম অস্থায়ী |
| test_project_context_service.py | backend/tests/services/test_project_context_service.py | Ignore rules, definition/route extraction | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_provider_rate_limiter.py | backend/tests/services/test_provider_rate_limiter.py | Intelligent rate limiter request ও cloud DB quick test | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_rider_tracker.py | backend/tests/services/test_rider_tracker.py | Rider tracker init, event metrics, aggregation | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_sandbox_service.py | backend/tests/services/test_sandbox_service.py | Sandbox create/execute/destroy/list/get lifecycle | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_self_benchmark.py | backend/tests/services/test_self_benchmark.py | Self-benchmark engine run ও adaptive optimizer cycle | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_self_correction.py | backend/tests/services/test_self_correction.py | Pre-execution simulation, audit invariants, self-healing | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_services_internet_monitor.py | backend/tests/services/test_services_internet_monitor.py | Internet monitor lifecycle, status, updates, global instance | test_internet_monitor.py | অপরিবর্তিত ✅ | "services_" প্রিফিক্স রিডান্ড্যান্ট |
| test_task_and_evolution_governance.py | backend/tests/services/test_task_and_evolution_governance.py | Task contract lifecycle ও change proposal promotion/rejection | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_task_router.py | backend/tests/services/test_task_router.py | TaskRouter requirement processing ও swarm LLM router | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_tool_forge.py | backend/tests/services/test_tool_forge.py | Tool synthesis ও RCE/file-IO blocking | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_video_to_code_pipeline.py | backend/tests/services/test_video_to_code_pipeline.py | Frame extraction, UI component, format enum | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_adversarial_security.py | backend/tests/test_adversarial_security.py | EphemeralExecutor/SkillIngestor path traversal ও AST safety | অপরিবর্তিত ✅ | backend/tests/security/ | Adversarial security টেস্ট security ডিরেক্টরিতে যায় |
| test_doc_summarizer_run.py | backend/tests/test_doc_summarizer_run.py | Doc summarizer benchmark ম্যানুয়াল রানার (pytest নয়) | run_doc_summarizer_benchmark.py | backend/scripts/ | কোনো test_ ফাংশন নেই; স্ক্রিপ্ট হওয়া উচিত |
| test_canary_and_evolution_bridge.py | backend/tests/test_evolution/test_canary_and_evolution_bridge.py | Evolution bridge proposal ও canary rollout/rollback | অপরিবর্তিত ✅ | backend/tests/evolution/ | ডিরেক্টরির "test_" প্রিফিক্স অসামঞ্জস্য |
| test_fitness_and_benchmark.py | backend/tests/test_evolution/test_fitness_and_benchmark.py | Fitness evaluator, benchmark promote/reject, integrity gate | অপরিবর্তিত ✅ | backend/tests/evolution/ | একই ডিরেক্টরি কারণ |
| test_governed_self_evolution_closed_loop.py | backend/tests/test_evolution/test_governed_self_evolution_closed_loop.py | Governed 21-state closed loop ও negative security rejection | অপরিবর্তিত ✅ | backend/tests/evolution/ | একই ডিরেক্টরি কারণ |
| test_file_gate_run.py | backend/tests/test_file_gate_run.py | FileIsolationGate ম্যানুয়াল গেট টেস্ট রানার | run_file_gate_test.py | backend/scripts/ | pytest-অসংগ্রহযোগ্য ম্যানুয়াল স্ক্রিপ্ট |
| test_ide_trio_smoke.py | backend/tests/test_ide_trio_smoke.py | IDE trio adapters smoke main() রানার | run_ide_trio_smoke.py | backend/scripts/ | pytest টেস্ট নেই; স্মোক স্ক্রিপ্ট |
| test_live_morphic_run.py | backend/tests/test_live_morphic_run.py | Knowledge QA execute_tool RAG/RBAC matrix ম্যানুয়াল রান | run_knowledge_qa_matrix.py | backend/scripts/ | ⚠️ "morphic" বিমূর্ত; pytest টেস্টও নেই |
| test_rls_policy_coverage.py | backend/tests/test_rls_policy_coverage.py | RLS static source check: group-B tables, migration-18 | অপরিবর্তিত ✅ | backend/tests/security/ | RLS isolation security ডিরেক্টরিতে প্রাসঙ্গিক |
| test_skill_pipeline.py | backend/tests/test_skill_pipeline.py | Malicious skill ingestion rejected (SkillIngestor) | অপরিবর্তিত ✅ | backend/tests/security/ | Adversarial ingestion security টেস্ট |
| test_cognitive_router.py | backend/tests/test_strategic_patches/test_cognitive_router.py | TaskDecomposer, CognitiveRouter, execution engine | অপরিবর্তিত ✅ | backend/tests/core/ | প্যাচ-ভিত্তিক ডিরেক্টরি নাম অস্থায়ী |
| test_tenant_di.py | backend/tests/test_tenant_di.py | get_tenant_db dependency DI টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম সংক্ষিপ্ত কিন্তু স্পষ্ট |
| test_agent_tools.py | backend/tests/tools/test_agent_tools.py | Agent tools কার্যকারিতা টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_auto_coverage_improver.py | backend/tests/tools/test_auto_coverage_improver.py | Auto coverage improver টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_auto_test_generator.py | backend/tests/tools/test_auto_test_generator.py | Auto test generator টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_browser_agent.py | backend/tests/tools/test_browser_agent.py | Browser agent automation টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_cloud_sandbox_full.py | backend/tests/tools/test_cloud_sandbox_full.py | Cloud sandbox full lifecycle টেস্ট | test_cloud_sandbox.py | অপরিবর্তিত ✅ | "_full" সাফিক্স অস্পষ্ট; orchestrator টেস্টের সাথে সামঞ্জস্য |
| test_cloud_sandbox_orchestrator.py | backend/tests/tools/test_cloud_sandbox_orchestrator.py | Sandbox orchestrator orchestration টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_code_smell_detector.py | backend/tests/tools/test_code_smell_detector.py | Code smell detector টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_cot_reasoner.py | backend/tests/tools/test_cot_reasoner.py | Chain-of-thought reasoner টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_coverage_auditor.py | backend/tests/tools/test_coverage_auditor.py | Coverage auditor টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_diagram_to_terraform.py | backend/tests/tools/test_diagram_to_terraform.py | Diagram→Terraform রূপান্তর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_freebuff_client.py | backend/tests/tools/test_freebuff_client.py | FreeBuff client টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_headless_agent_registry.py | backend/tests/tools/test_headless_agent_registry.py | Headless agent registry টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_image_to_code_react.py | backend/tests/tools/test_image_to_code_react.py | Image→React code generation টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_knowledge_base_indexer.py | backend/tests/tools/test_knowledge_base_indexer.py | Knowledge base indexer টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_local_code_executor.py | backend/tests/tools/test_local_code_executor.py | Local code executor টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_meta_architect_coverage_full.py | backend/tests/tools/test_meta_architect_coverage_full.py | Meta architect বিস্তৃত coverage টেস্ট | test_meta_architect.py | অপরিবর্তিত ✅ | "_coverage_full" সাফিক্স রিডান্ড্যান্ট |
| test_multilingual_tts.py | backend/tests/tools/test_multilingual_tts.py | Multilingual TTS টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_new_tools_sprint5.py | backend/tests/tools/test_new_tools_sprint5.py | Sprint-5 নতুন টুল ব্যাচ টেস্ট | প্রতি-টুল আলাদা test_*.py | অপরিবর্তিত ✅ | ⚠️ স্প্রিন্ট নাম অস্থায়ী; বিভাজন দরকার |
| test_plan_sorter.py | backend/tests/tools/test_plan_sorter.py | Plan sorter টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_pr_reviewer_webhook.py | backend/tests/tools/test_pr_reviewer_webhook.py | PR reviewer webhook টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_preference_memory.py | backend/tests/tools/test_preference_memory.py | Preference memory টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_resource_catalog.py | backend/tests/tools/test_resource_catalog.py | Resource catalog টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_sprint_c_tools.py | backend/tests/tools/test_sprint_c_tools.py | Sprint-C টুল ব্যাচ টেস্ট | প্রতি-টুল আলাদা test_*.py | অপরিবর্তিত ✅ | ⚠️ স্প্রিন্ট নাম অস্থায়ী; বিভাজন দরকার |
| test_style_learner_ast.py | backend/tests/tools/test_style_learner_ast.py | AST-based style learner টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_viral_referral_engine.py | backend/tests/tools/test_viral_referral_engine.py | Viral referral engine টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_vpn_switcher_rotator.py | backend/tests/tools/test_vpn_switcher_rotator.py | VPN switcher/rotator টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_api_endpoints.py | backend/tests/unit/test_api_endpoints.py | REST API endpoints suite (health, auth, agents...) | অপরিবর্তিত ✅ | backend/tests/integration/api/ | ফাইল নিজেই pytestmark integration ঘোষণা করে |
| conftest.py | backend/tests/unit_light/conftest.py | DB engine/session/cleanup fixtures | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনভেনশন অনুযায়ী উপযুক্ত |
| test_security.py | backend/tests/unit_light/services/scraper/test_security.py | Scraper URL safety: scheme, private IP, hostname | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | scraper সাবডিরেক্টরিতে মিরর উপযুক্ত |
| test_web_scraper.py | backend/tests/unit_light/services/scraper/test_web_scraper.py | fetch_page: SSRF block, HTML parse, request error | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_intelligent_cache_shim.py | backend/tests/unit_light/services/test_intelligent_cache_shim.py | Intelligent cache shim delegation ও warn-once | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_core_skills.py | backend/tests/unit_light/test_core_skills.py | BaseSkill naming, execute gateway, experience persistence | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_deprecated_shims.py | backend/tests/unit_light/test_deprecated_shims.py | Deprecated shim delegation, dir, warn-once | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_feature_flags.py | backend/tests/unit_light/test_feature_flags.py | Feature flag env/DB source, rollout, cache, status | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_human_behavior.py | backend/tests/unit_light/test_human_behavior.py | Bezier mouse movement ও natural typing | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_intent.py | backend/tests/unit_light/test_intent.py | Intent classification: coding, translation, admin, fallback | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_language_router.py | backend/tests/unit_light/test_language_router.py | Multi-script detection ও route fallback | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম উপযুক্ত (services কপির সাথে ডুপ্লিকেট দ্রষ্টব্য) |
| test_ld_client.py | backend/tests/unit_light/test_ld_client.py | LaunchDarkly client unsupported-platform fallback | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_messaging_models.py | backend/tests/unit_light/test_messaging_models.py | Message event/result models ও provider protocol | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_rate_limit_quota.py | backend/tests/unit_light/test_rate_limit_quota.py | Daily quota tiers, admin bypass, fail-open | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_router.py | backend/tests/unit_light/test_router.py | Deprecated router shim warning ও delegation | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_rules_mutator.py | backend/tests/unit_light/test_rules_mutator.py | Redis unavailable/blocked paths | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম উপযুক্ত (core কপির সাথে ডুপ্লিকেট দ্রষ্টব্য) |
| test_search.py | backend/tests/unit_light/test_search.py | Web search unavailable/error/normalize ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_security_api_key_limiter.py | backend/tests/unit_light/test_security_api_key_limiter.py | API key limiter: fail-open, 429, redis error | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_security_rate_limiter.py | backend/tests/unit_light/test_security_rate_limiter.py | Evalsha/eval fallback, reset time | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_upload_validator.py | backend/tests/unit_light/test_upload_validator.py | Extension, mime, size edge cases | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম উপযুক্ত (core কপির সাথে ডুপ্লিকেট দ্রষ্টব্য) |
| test_user_profiler.py | backend/tests/unit_light/test_user_profiler.py | User profiler classification ও history update | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_utils.py | backend/tests/unit_light/test_utils.py | UTC time helpers, lazy import, tracked tasks | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_api_tracker.py | backend/tests/utils/test_api_tracker.py | APITracker record ও singleton tracker | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_branding.py | backend/tests/utils/test_branding.py | Branding normalize ও display names | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_environment.py | backend/tests/utils/test_environment.py | Test-environment detect, admin/autofix authorization | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_json_helpers.py | backend/tests/utils/test_json_helpers.py | json_response/success/error helper | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_text_helpers.py | backend/tests/utils/test_text_helpers.py | strip_markdown_code_block টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_time_utils.py | backend/tests/utils/test_time_utils.py | utc_now, utc_expiry, ensure_aware | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_timestamps.py | backend/tests/utils/test_timestamps.py | utils.timestamps utc_now/iso/timestamp | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম উপযুক্ত (time_utils-এর সাথে সদৃশতা দ্রষ্টব্য) |
| test_utils.py | backend/tests/utils/test_utils.py | String/date/security/data utils মিশ্র টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | grab-bag; ভবিষ্যতে ভাগের সুযোগ |
| test_uuid_gen.py | backend/tests/utils/test_uuid_gen.py | UUIDv7 generation ও type behavior | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_verifier.py | backend/tests/verification/test_verifier.py | Verifier AST validation ও empty output rejection | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_celery_app.py | backend/tests/workers/test_celery_app.py | Celery app exposure টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_nightly_auditor.py | backend/tests/workers/test_nightly_auditor.py | Auditor init, DB optional, threshold constant | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_nightly_auditor_audit.py | backend/tests/workers/test_nightly_auditor_audit.py | Audit execution: safe pass, breach/error/fuzz lock | test_nightly_auditor.py-এ মার্জ | অপরিবর্তিত ✅ | একই auditor-এর বিভক্ত কভারেজ; একত্র করুন |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **Frontend e2e ভুল জায়গায়:** backend/tests/e2e/-এর ৭টি Playwright spec সম্পূর্ণ frontend UI টেস্ট; repo-root e2e/ (বা frontend/e2e/) -এ সরানো উচিত।
- **Dead test candidates:** test_doc_summarizer_run.py, test_file_gate_run.py, test_ide_trio_smoke.py, test_live_morphic_run.py — কোনো pytest-সংগ্রহযোগ্য test_ ফাংশন নেই; CI-তে আসলে চলে না, backend/scripts/-এ যাওয়া উচিত।
- **Duplicate coverage clusters:** rules_mutator, upload_validator, language_router (core বনাম unit_light), anti-hacking middleware-এর দুই ফাইল, cost auditor (monitoring বনাম services/test_monitoring), token budget (core বনাম services/test_llm_router), advanced_model_router বনাম তার _regression সংস্করণ।
- **Semantic-mismatch hotspots:** tier8, phase2/phase3 (স্প্রিন্ট-ধাঁচ), sprint5/sprint_c, morphic — বিমূর্ত/সাময়িক নাম দীর্ঘমেয়াদে বিভ্রান্তিকর; কনটেন্ট-ভিত্তিক নামকরণ দরকার।
- **Duplicate basename ঝুঁকি:** test_swarm_orchestrator.py একই নামে tests/core/ ও tests/core/orchestration/ দুই জায়গায় — rootdir কনফিগ ছাড়া pytest import conflict হতে পারে।
- **Mark-vs-location অসামঞ্জস্য:** tests/unit/test_api_endpoints.py নিজেকে `pytest.mark.integration` ঘোষণা করে কিন্তু unit/ ডিরেক্টরিতে বসানো।
- **Stale documentation:** test_tier8_evolution.py-এর হেডার বলে LOCATION হলো backend/tests/, কিন্তু প্রকৃত অবস্থান backend/tests/core/।
- **utils-এ সদৃশ মডিউল:** time_utils বনাম timestamps দুটি আলাদা UTC-helper মডিউলের টেস্ট পাশাপাশি — মূল কোড একত্রকরণের সুযোগ।


---

## ব্যাচ ০৬ — Backend Tools ও Scripts
**ব্যাচ:** 06 | **তালিকাভুক্ত:** ১৫২ | **বিশ্লেষিত:** ১৫২ | **অনুপস্থিত/স্কিপ:** ০ | **রিনেম প্রস্তাব:** ১৭ | **স্থানান্তর প্রস্তাব:** ১৮ | **⚠️ সেমান্টিক মিসম্যাচ:** ৬

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| __init__.py | backend/scripts/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_find_blindspots.py | backend/scripts/auto_find_blindspots.py | কভারেজ/TODO/সিকিউরিটি স্ক্যান করে কোয়ালিটি-গেট রিপোর্ট | code_quality_gate.py | অপরিবর্তিত ✅ | blindspots অস্পষ্ট; আসলে কোয়ালিটি-গেট স্ক্যানার |
| auto_test_gen.py | backend/scripts/auto_test_gen.py | coverage.xml গ্যাপ থেকে LLM দিয়ে pytest জেনারেট+ভেরিফাই | coverage_gap_test_generator.py | অপরিবর্তিত ✅ | tools/code/auto_test_generator-এর সাথে ওভারল্যাপ |
| __init__.py | backend/scripts/benchmark/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| load_test_phase3.py | backend/scripts/benchmark/load_test_phase3.py | LLM গেটওয়েতে ১০০০ ট্রানজেকশন লোড সিমুলেশন | llm_gateway_load_test.py | অপরিবর্তিত ✅ | phase3 অস্থায়ী স্প্রিন্ট-নাম |
| __init__.py | backend/scripts/dev/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| update_imports.py | backend/scripts/dev/update_imports.py | রি-অর্গানাইজেশনের পর ইমপোর্ট পাথ বাল্ক-রিরাইট ম্যাপ | অপরিবর্তিত ✅ | backend/scripts/migrations/ | ওয়ান-অফ মাইগ্রেশন কোডেমড |
| ai_log_analyzer.py | backend/scripts/devops/ai_log_analyzer.py | Render লগ থেকে এরর সংগ্রহ করে AI বিশ্লেষণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| find_router_error.py | backend/scripts/find_router_error.py | সব রাউটার রেজিস্টার করে ইমপোর্ট-এরর ডায়াগনোজ | router_import_smoke_test.py | অপরিবর্তিত ✅ | রাউটার স্মোক-টেস্ট; নাম অনানুষ্ঠানিক |
| kaggle_shadow_node.ipynb | backend/scripts/kaggle_shadow_node.ipynb | কাগলে Groq+ngrok ফ্রি শ্যাডো API নোড নোটবুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্বচ্ছ অপস নোটবুক |
| load_seed_data.py | backend/scripts/load_seed_data.py | GCS/S3/লোকাল থেকে সিড-ডেটা লোডার ক্লাস | seed_data_loader.py | backend/database/ | পুনঃব্যবহারযোগ্য লোডার, স্ক্রিপ্ট নয় |
| migrate_embeddings.py | backend/scripts/migrate_embeddings.py | Supabase ai_memory রি-এমবেড (ওয়ান-অফ) | অপরিবর্তিত ✅ | backend/scripts/migrations/ | ওয়ান-অফ ডেটা মাইগ্রেশন |
| migrate_files_to_db.py | backend/scripts/migrate_files_to_db.py | ক্যানোনিকাল XML/skill→Supabase মাইগ্রেশন | অপরিবর্তিত ✅ | backend/scripts/migrations/ | মাইগ্রেশন ফোল্ডারে থাকা স্বাভাবিক |
| migrate_llm_routers.py | backend/scripts/migrate_llm_routers.py | LLM রাউটার কনসোলিডেশন ভ্যালিডেটর | অপরিবর্তিত ✅ | backend/scripts/migrations/ | মাইগ্রেশন ভেরিফিকেশন স্ক্রিপ্ট |
| 001_create_core_tables.sql | backend/scripts/migrations/001_create_core_tables.sql | skills/rules/agent_configs টেবিল DDL | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| refactor_remediation.py | backend/scripts/refactor/refactor_remediation.py | auto_remediation.py-তে রেজেক্স প্যাচ, হার্ডকোডেড c:\ পাথ | ডিলিট প্রস্তাব | — | ডেড ওয়ান-অফ প্যাচ, নন-পোর্টেবল পাথ |
| refactor_swarm.py | backend/scripts/refactor/refactor_swarm.py | swarm_orchestrator.py রেজেক্স প্যাচ, c:\ পাথ | ডিলিট প্রস্তাব | — | ডেড ওয়ান-অফ প্যাচ, নন-পোর্টেবল পাথ |
| refactor_logging.py | backend/scripts/refactor_logging.py | বাল্ক logging→loguru রিরাইট, F:\ হার্ডকোড | ডিলিট প্রস্তাব | — | ডেড কোডেমড, হার্ডকোডেড ড্রাইভ-পাথ |
| refactor_root_cause.py | backend/scripts/refactor_root_cause.py | except-ব্লকে error-bus emit ইনজেক্ট কোডেমড | error_bus_codemod.py | backend/scripts/refactor/ | নাম অস্পষ্ট; refactor/ ফোল্ডারে সামঞ্জস্য |
| run_chaos_experiment.py | backend/scripts/run_chaos_experiment.py | কেয়াস ড্রিল চালিয়ে রেজিলিয়েন্স রিপোর্ট তৈরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| run_dependency_check.py | backend/scripts/run_dependency_check.py | DependencyManagerAgent দিয়ে pip/npm অডিট রান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| seed_ecosystem.py | backend/scripts/seed_ecosystem.py | ক্যাপাবিলিটি রেজিস্ট্রি+সোর্স পলিসি সিড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| seed_tools_registry.py | backend/scripts/seed_tools_registry.py | tools_registry টেবিলে ৭৬ টুলের মেটাডেটা সিড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; মেটাডেটা পাথ পুরনো (tools/*.py) |
| self_healing_tests.py | backend/scripts/self_healing_tests.py | HealingState স্টাব, সব স্টেপ no-op | ডিলিট প্রস্তাব | — | অসম্পূর্ণ স্টাব, আসল লজিক নেই |
| self_test_and_improve.py | backend/scripts/self_test_and_improve.py | সেলফ-বেঞ্চমার্ক+অ্যাডাপটিভ অপটিমাইজার লুপ রানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| store_ci_roadmap_to_memory.py | backend/scripts/store_ci_roadmap_to_memory.py | CI ট্রায়াজ রোডম্যাপ CascadeMemory-তে ইনজেক্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| superai_free_tier_monitor.py | backend/scripts/superai_free_tier_monitor.py | ফ্রি-টিয়ার লিমিট মনিটর ড্যাশবোর্ড+অ্যালার্ট CLI | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ১৩৭৫ লাইন মনোলিথ ভাঙা উচিত |
| sync_knowledge.py | backend/scripts/sync_knowledge.py | coldstart knowledge JSON→CascadeMemory সিঙ্ক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| validate_openapi.py | backend/scripts/validate_openapi.py | OpenAPI স্কিমা জেনারেট+ভ্যালিডেট, ফাইল লেখে | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/tools/__init__.py | LazyModule প্রক্সি, পুরনো ফ্ল্যাট নাম ম্যাপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কম্প্যাট শিম; মাইগ্রেশন শেষে সরানো উচিত |
| _bootstrap.py | backend/tools/_bootstrap.py | sys.path বুটস্ট্র্যাপ হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_tools.py | backend/tools/agent_tools.py | এজেন্টের ৩টি রিয়েল টুল: DB/ওয়েব সার্চ ইত্যাদি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/tools/ai_agents/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| browser_agent.py | backend/tools/ai_agents/browser_agent.py | ফ্যাসাড→core.agents.live.browser_agent | ডিলিট প্রস্তাব | — | ডেপ্রিকেটেড ৩-লাইন শিম |
| vision_agent.py | backend/tools/ai_agents/vision_agent.py | ফ্যাসাড→core.agents.live.vision_agent | ডিলিট প্রস্তাব | — | ডেপ্রিকেটেড ৩-লাইন শিম |
| ai_federation_protocol.py | backend/tools/ai_federation_protocol.py | ইন-মেমরি স্কিল রেজিস্ট্রি+টাস্ক ডেলিগেশন | agent_skill_registry.py | অপরিবর্তিত ✅ | ⚠️ federation বাড়াবাড়ি; আসলে লোকাল রেজিস্ট্রি |
| __init__.py | backend/tools/analytics/__init__.py | ChurnProphet+InsightMage রি-এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| churn_prophet.py | backend/tools/analytics/churn_prophet.py | agents/churn_prophet-এর কম্প্যাট র‍্যাপার | ডিলিট প্রস্তাব | — | ⚠️ prophet ফ্যান্টাসি নাম; ডুপ্লিকেট র‍্যাপার |
| insight_mage.py | backend/tools/analytics/insight_mage.py | agents/insight_mage-এর কম্প্যাট র‍্যাপার | ডিলিট প্রস্তাব | — | ⚠️ mage ফ্যান্টাসি নাম; ডুপ্লিকেট র‍্যাপার |
| api_gateway.py | backend/tools/api_gateway.py | /api/v1/gateway প্রক্সি রাউটার+Make.com ওয়েবহুক | gateway.py | backend/api/routes/ | FastAPI রাউটার, টুল নয় |
| bandwidth_optimizer.py | backend/tools/bandwidth_optimizer.py | প্রম্পট কমপ্রেসর+ছোট রেসপন্স ক্যাশ | prompt_compressor.py | অপরিবর্তিত ✅ | ⚠️ bandwidth নাম বিভ্রান্তিক; অব্যবহৃত |
| __init__.py | backend/tools/billing/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cost_auditor.py | backend/tools/billing/cost_auditor.py | SQLite টাস্ক-কস্ট অডিট রিপোর্ট (md/png) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| monthly_cost_reporter.py | backend/tools/billing/monthly_cost_reporter.py | মাসিক কস্ট রিপোর্ট তৈরি+টেলিগ্রাম অ্যালার্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/tools/browser/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ai_web_extractor.py | backend/tools/browser/ai_web_extractor.py | পেজ ফেচ করে LLM দিয়ে ডেটা এক্সট্র্যাকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| browser_stealth.py | backend/tools/browser/browser_stealth.py | স্টেলথ Playwright ব্রাউজার, UA রোটেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_tools.py | backend/tools/browser/mcp_tools.py | MCP ব্রাউজার-টুল স্কিমা রেজিস্ট্রি (pydantic) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| playwright_browser_agent.py | backend/tools/browser/playwright_browser_agent.py | ফুল Playwright এজেন্ট: কুকি, ক্রেডেনশিয়াল, মেমরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| stealth_http_client.py | backend/tools/browser/stealth_http_client.py | প্রক্সি-রোটেটেড স্টেলথ httpx ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| web_fallback_agent.py | backend/tools/browser/web_fallback_agent.py | API না থাকলে Playwright ফলব্যাক অটোমেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| web_scraper.py | backend/tools/browser/web_scraper.py | SSRF-সেফ ফেচ+BeautifulSoup টেক্সট এক্সট্র্যাক্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| checkpoint_manager.py | backend/tools/checkpoint_manager.py | টাস্ক চেকপয়েন্ট PG/Firestore সেভ-রিজিউম | অপরিবর্তিত ✅ | backend/memory/ | পারসিস্টেন্স ইনফ্রা, tools-এ বিচ্ছিন্ন |
| cli.py | backend/tools/cli.py | typer CLI হেডলেস এজেন্ট ইন্টারফেস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; তবে কোনো ইমপোর্টার নেই |
| __init__.py | backend/tools/code/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ai_pair_programmer.py | backend/tools/code/ai_pair_programmer.py | /pair রাউটার+LLM issue-সমাধান পাইপলাইন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; রাউটার-in-tools প্যাটার্ন চলছে |
| auto_pr_pipeline.py | backend/tools/code/auto_pr_pipeline.py | Guardian-ভেরিফায়েড রিয়েল GitHub PR পাইপলাইন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_test_generator.py | backend/tools/code/auto_test_generator.py | pytest/vitest/flutter টেস্ট জেনারেটর+/test-gen রাউটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; scripts/auto_test_gen-এর সাথে ওভারল্যাপ |
| code_smell_detector.py | backend/tools/code/code_smell_detector.py | radon/pylint/AST কমপ্লেক্সিটি+ডুপ্লিকেশন ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cot_reasoner.py | backend/tools/code/cot_reasoner.py | Chain-of-Thought রিজনার+সেফ ম্যাথ ইভাল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| dependency_manager_agent.py | backend/tools/code/dependency_manager_agent.py | pip/npm আউটডেটেড+ভালনারেবিলিটি স্ক্যান, অটো-PR | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| diagram_to_architecture.py | backend/tools/code/diagram_to_architecture.py | ডায়াগ্রাম→Terraform/K8s/Schema কোড জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| fuzz_sandbox.py | backend/tools/code/fuzz_sandbox.py | AST গেটকিপার+১০০ অ্যাটাক পেলোড ফাজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্যান্ডবক্স ফাজ-টেস্টিং, নাম সঠিক |
| image_to_code.py | backend/tools/code/image_to_code.py | স্ক্রিনশট→React/Tailwind কোড জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| local_code_executor.py | backend/tools/code/local_code_executor.py | Docker/সাবপ্রসেস লোকাল কোড এক্সিকিউশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| lsp_bridge.py | backend/tools/code/lsp_bridge.py | VS Code এক্সটেনশনের ইনলাইন কমপ্লিশন ব্রিজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pr_reviewer.py | backend/tools/code/pr_reviewer.py | PR রিভিউ: সিকিউরিটি/স্টাইল/স্মেল+GitHub কমেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pre_commit_ai.py | backend/tools/code/pre_commit_ai.py | স্টেজড ফাইল বিশ্লেষণ+অটোফিক্স গিট হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| safe_executor.py | backend/tools/code/safe_executor.py | RestrictedPython সেফ এক্সিকিউশন এনভায়রনমেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| voice_coder.py | backend/tools/code/voice_coder.py | ভয়েস কমান্ড→কোড জেনারেশন+/voice রাউটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| collaborative_editor.py | backend/tools/collaborative_editor.py | WebSocket+Redis পাব/সাব কোলাবরেটিভ এডিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; রাউটার-in-tools প্যাটার্ন চলছে |
| comment_thread_ai.py | backend/tools/comment_thread_ai.py | GitHub কমেন্ট থ্রেড AI সামারি/রিপ্লাই/স্টেল ডিটেক্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| conversation_manager.py | backend/tools/conversation_manager.py | ইন-মেমরি কনভার্সেশন হিস্ট্রি/সামারি ম্যানেজার | অপরিবর্তিত ✅ | backend/memory/ | কথোপকথন-স্টেট, memory ডোমেইনে যাওয়া উচিত |
| __init__.py | backend/tools/creative/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| audio_engineering_agent.py | backend/tools/creative/audio_engineering_agent.py | অডিও মিক্স/মাস্টার জব অর্কেস্ট্রেটর (BaseSkill) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| brand_identity_agent.py | backend/tools/creative/brand_identity_agent.py | ব্র্যান্ড কিট তৈরির অর্কেস্ট্রেটর (BaseSkill) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| creative_agents_registry.py | backend/tools/creative/creative_agents_registry.py | ৪ ক্রিয়েটিভ এজেন্ট স্কিল-ম্যানেজারে রেজিস্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| game_design_agent.py | backend/tools/creative/game_design_agent.py | গেম ডিজাইন ডকুমেন্ট জেনারেটর (BaseSkill) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| video_production_agent.py | backend/tools/creative/video_production_agent.py | ভিডিও প্রোডাকশন জব অর্কেস্ট্রেটর (BaseSkill) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/tools/devops/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_coverage_improver.py | backend/tools/devops/auto_coverage_improver.py | কভারেজ গ্যাপে অটো টেস্ট জেনারেশন অর্কেস্ট্রেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| coverage_auditor.py | backend/tools/devops/coverage_auditor.py | coverage xml/json গ্যাপ পার্সার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| docker_sandbox.py | backend/tools/devops/docker_sandbox.py | Docker কনটেইনারে স্যান্ডবক্সড কমান্ড এক্সিকিউশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| gcp_cloud_functions.py | backend/tools/devops/gcp_cloud_functions.py | GCP Cloud Functions HTTP ট্রিগার ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| github_agent.py | backend/tools/devops/github_agent.py | DB টোকেন ডিক্রিপ্ট+অটোনোমাস PR তৈরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| on_premise_deployer.py | backend/tools/devops/on_premise_deployer.py | এয়ার-গ্যাপড docker-compose+Helm জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ensemble_router.py | backend/tools/ensemble_router.py | ফ্রি-মডেল এনসেম্বল রাউটিং+কোটা রোটেশন | অপরিবর্তিত ✅ | backend/services/llm/ | LLM রাউটিং ইঞ্জিন; অব্যবহৃত ডেড ক্যান্ডিডেট |
| freebuff_client.py | backend/tools/freebuff_client.py | এক্সটার্নাল freebuff CLI-তে টাস্ক ডেলিগেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| graph_service.py | backend/tools/graph_service.py | Neo4j স্কিল-গ্রাফ সিঙ্ক+পাথ কোয়েরি (dry-run) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| headless_agent_registry.py | backend/tools/headless_agent_registry.py | CLI এজেন্ট (gemini-cli ইত্যাদি) কনফিগ রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| health_checker.py | backend/tools/health_checker.py | ডিপেন্ডেন্সি/.env/DB হেলথ চেক+টেলিগ্রাম অ্যালার্ট | environment_health_checker.py | backend/core/health/ | core health_check-এর সাথে নামসংঘর্ষ এড়াতে |
| README.md | backend/tools/knowledge/README.md | knowledge প্যাকেজের ডকুমেন্টেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/tools/knowledge/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| codebase_exporter.py | backend/tools/knowledge/codebase_exporter.py | ignore-রুলসহ কোডবেস স্ট্রাকচার এক্সপোর্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| git_knowledge_extractor.py | backend/tools/knowledge/git_knowledge_extractor.py | গিট হিস্ট্রি→error-fix প্যাটার্ন SQLite-এ সংরক্ষণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ডুপ্লিকেট ডকস্ট্রিং ব্লক আছে |
| knowledge_base_indexer.py | backend/tools/knowledge/knowledge_base_indexer.py | seed_data মডিউল→ChromaDB ভেক্টর ইনডেক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; tools/seed_data নেই — ডেড পাথ |
| local_search_rag.py | backend/tools/knowledge/local_search_rag.py | লোকাল RAG: ওয়েব ব্রাউজ+ChromaDB/TF-IDF ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pdf_to_sdk.py | backend/tools/knowledge/pdf_to_sdk.py | PDF→API স্পেক→SDK স্ক্যাফোল্ড জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| repo_deep_indexer.py | backend/tools/knowledge/repo_deep_indexer.py | AST দিয়ে রিপোর ক্লাস/ফাংশন ইনডেক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| langchain_agent_example.py | backend/tools/langchain_agent_example.py | LaunchDarkly+LangChain ইন্টিগ্রেশন উদাহরণ | langchain_launchdarkly_agent.py | backend/examples/ | উদাহরণ ফাইল, examples-এ থাকা উচিত |
| __init__.py | backend/tools/learning/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_knowledge_store.py | backend/tools/learning/agent_knowledge_store.py | এজেন্ট-শেখা নলেজ Firestore/SQLite-এ সংরক্ষণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| domain_adapter.py | backend/tools/learning/domain_adapter.py | legal/medical/finance ডোমেইন প্রম্পট কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| model_trainer.py | backend/tools/learning/model_trainer.py | RunPod/Modal/লোকাল LoRA ফাইন-টিউন ট্রিগার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rlhf_pipeline.py | backend/tools/learning/rlhf_pipeline.py | প্রেফারেন্স লগ সংগ্রহ+Firestore সিঙ্ক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| skill_recommender.py | backend/tools/learning/skill_recommender.py | কোলাবরেটিভ ফিল্টারিং+হিউরিস্টিক স্কিল রেকমেন্ডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| style_learner.py | backend/tools/learning/style_learner.py | রিপো কোডিং-স্টাইল শেখা+/style রাউটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/tools/localization/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bangla_ai_connector.py | backend/tools/localization/bangla_ai_connector.py | অটো-জেনারেটেড বাংলা AI কানেক্টর স্টাব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | example.com হার্ডকোড — ডেড স্টাব |
| bangla_nlp.py | backend/tools/localization/bangla_nlp.py | বাংলা টেক্সট ডিটেকশন/স্টপওয়ার্ড ইউটিলিটি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bangla_voice.py | backend/tools/localization/bangla_voice.py | বাংলা Whisper STT+Coqui TTS র‍্যাপার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bengali_ocr_converter.py | backend/tools/localization/bengali_ocr_converter.py | Google Vision বাংলা OCR→টেক্সট/এক্সেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| local_ocr_extractor.py | backend/tools/localization/local_ocr_extractor.py | EasyOCR এক্সট্র্যাক্ট+টেবিল পার্স+এক্সেল এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/tools/mcp/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_cloud_deploy.py | backend/tools/mcp/mcp_cloud_deploy.py | MCP সার্ভার: Render/Railway/Oracle ডিপ্লয়+লগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_github_cicd.py | backend/tools/mcp/mcp_github_cicd.py | MCP সার্ভার: GitHub PR/issue/CI অপারেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_ide_trio.py | backend/tools/mcp/mcp_ide_trio.py | MCP সার্ভার: Gemini→Kilo→Cline পাইপলাইন ট্রিগার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_observability.py | backend/tools/mcp/mcp_observability.py | MCP সার্ভার: Sentry ইস্যু+লোকাল লগ ফেচ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_server.py | backend/tools/mcp/mcp_server.py | MCP সার্ভার: knowledge-graph স্কিল টুল | mcp_knowledge_graph.py | অপরিবর্তিত ✅ | জেনেরিক নাম ভাই-সার্ভারদের সাথে অস্পষ্ট |
| mcp_supabase.py | backend/tools/mcp/mcp_supabase.py | MCP সার্ভার: Supabase SQL/মাইগ্রেশন এক্সিকিউশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_workspace.py | backend/tools/mcp/mcp_workspace.py | MCP সার্ভার: ওয়ার্কস্পেস আইসোলেশন+ফাইল অপারেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/tools/media/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| image_generator.py | backend/tools/media/image_generator.py | HuggingFace SDXL ইমেজ জেনারেশন ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| multilingual_tts.py | backend/tools/media/multilingual_tts.py | ElevenLabs মাল্টিলিঙ্গুয়াল TTS+/tts রাউটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| music_generator.py | backend/tools/media/music_generator.py | LLM মিউজিক-প্রম্পট জেনারেটর (আসল অডিও নেই) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; প্লেসহোল্ডার — রিয়েল জেনারেশন নেই |
| presentation_generator.py | backend/tools/media/presentation_generator.py | LLM স্লাইড-আউটলাইন JSON জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| threed_model_generator.py | backend/tools/media/threed_model_generator.py | LLM 3D-মডেল প্রম্পট জেনারেটর (প্লেসহোল্ডার) | three_d_model_generator.py | অপরিবর্তিত ✅ | threed বানান অস্বাভাবিক |
| video_generator.py | backend/tools/media/video_generator.py | Runway/Kling ভিডিও API ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| voice.py | backend/tools/media/voice.py | Whisper/HF ভিত্তিক STT+TTS VoiceInterface | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| meta_architect.py | backend/tools/meta_architect.py | কোডবেস মেট্রিক্স+আর্কিটেকচার সাজেশন জেনারেটর | architecture_analyzer.py | অপরিবর্তিত ✅ | ⚠️ meta বাড়াবাড়ি; আসলে অ্যানালাইজার |
| offline_mode.py | backend/tools/offline_mode.py | Ollama অফলাইন ফলব্যাক+ক্লাউড সিঙ্ক কিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; তবে অব্যবহৃত ডেড ক্যান্ডিডেট |
| parallel_agent_executor.py | backend/tools/parallel_agent_executor.py | Redis পাব/সাবে সমান্তরাল এজেন্ট এক্সিকিউশন | অপরিবর্তিত ✅ | backend/core/orchestration/ | অর্কেস্ট্রেশন ইনফ্রা, tools নয় |
| plan_sorter.py | backend/tools/plan_sorter.py | অ্যাডমিন প্ল্যান md ফাইল কীওয়ার্ডে বাছাই/কপি | অপরিবর্তিত ✅ | backend/scripts/ | ফাইল-ব্যবস্থাপনা স্ক্রিপ্ট, টুল নয় |
| preference_memory.py | backend/tools/preference_memory.py | ইউজার প্রেফারেন্স স্টোর+প্রম্পট মডিফায়ার | অপরিবর্তিত ✅ | backend/memory/ | ইউজার মেমরি, memory ডোমেইনে যাওয়া উচিত |
| repo_discovery_agent.py | backend/tools/repo_discovery_agent.py | GitHub REST রিপো সার্চ (টোকেন ফলব্যাক ডেটাসেট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| resource_catalog.py | backend/tools/resource_catalog.py | awesome-list/GitHub/libraries.io ক্যাটালগ সার্চ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/tools/security_tools/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| multi_account_rotator.py | backend/tools/security_tools/multi_account_rotator.py | মাল্টি-প্রোভাইডার LLM API কী/অ্যাকাউন্ট রোটেশন | api_key_rotator.py | backend/services/llm/ | LLM কী-রোটেশন, security_tools-এ অপ্রাসঙ্গিক |
| proxy_manager.py | backend/tools/security_tools/proxy_manager.py | রাউন্ড-রবিন প্রক্সি রোটেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vpn_switcher.py | backend/tools/security_tools/vpn_switcher.py | VPN এন্ডপয়েন্ট রোটেটর+হিস্ট্রি ট্র্যাকিং | vpn_rotator.py | অপরিবর্তিত ✅ | ক্লাস VPNRotator-এর সাথে সামঞ্জস্য |
| vulnerability_predictor.py | backend/tools/security_tools/vulnerability_predictor.py | AST/CWE প্যাটার্ন-ভিত্তিক SAST স্ক্যানার | vulnerability_scanner.py | অপরিবর্তিত ✅ | ⚠️ predictor নয় — প্যাটার্ন স্ক্যানার |
| seed_database.py | backend/tools/seed_database.py | LocalSearchRAG নলেজ SQLite FTS-এ সিড | অপরিবর্তিত ✅ | backend/scripts/ | সিডিং স্ক্রিপ্ট; scripts-এ ভাই-ফাইল আছে |
| self_planner.py | backend/tools/self_planner.py | networkx DAG টাস্ক প্ল্যানার (মক ফলব্যাক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/tools/social/__init__.py | খালি প্যাকেজ মার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| email_agent.py | backend/tools/social/email_agent.py | রিয়েল IMAP যাচাই+OTP, OAuth fail-closed | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| marketplace_agent.py | backend/tools/social/marketplace_agent.py | PyPI/npm রেজিস্ট্রিতে রিয়েল প্যাকেজ সার্চ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| teldrive_storage.py | backend/tools/social/teldrive_storage.py | টেলিগ্রাম ক্লাউডে AES এনক্রিপ্টেড স্টোরেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| telegram_bot.py | backend/tools/social/telegram_bot.py | প্রোডাকশন টেলিগ্রাম বট হ্যান্ডলার+ওয়েবহুক রাউটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ১৩৯২ লাইন মনোলিথ ভাঙা উচিত |
| telegram_security.py | backend/tools/social/telegram_security.py | TOTP 2FA+প্রম্পট-ইনজেকশন গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| viral_referral_engine.py | backend/tools/social/viral_referral_engine.py | রেফারেল কোড/রিওয়ার্ড টিয়ার+ফ্রড চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sso_integrator.py | backend/tools/sso_integrator.py | SAML SSO (OneLogin)+JWT অথ ফ্লো | অপরিবর্তিত ✅ | backend/core/security/authentication/ | অথ ডোমেইন, security প্যাকেজে থাকা স্বাভাবিক |
| tenant_rate_limiter.py | backend/tools/tenant_rate_limiter.py | Redis পার-টেন্যান্ট রেট লিমিট+Stripe বিলিং টিয়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; core-এ rate_limiter শিম আছে বলে রাখা হলো |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **ডেড কোড ক্লাস্টার (ডিলিট প্রস্তাব ৮টি):** `refactor/refactor_remediation.py`, `refactor/refactor_swarm.py`, `refactor_logging.py` তিনটিই হার্ডকোডেড Windows (`c:\Users\n\`, `F:\`) পাথসহ ওয়ান-অফ রেজেক্স প্যাচ — পোর্টেবল নয়, পুনরায় চালানো অর্থহীন; `self_healing_tests.py` সম্পূর্ণ no-op স্টাব; `ai_agents/browser_agent.py` ও `vision_agent.py` ৩-লাইনের ডেপ্রিকেটেড ফ্যাসাড; `analytics/churn_prophet.py` ও `insight_mage.py` agents/ প্যাকেজের ডুপ্লিকেট র‍্যাপার।
- **অব্যবহৃত (unwired) টুলস:** `ensemble_router`, `offline_mode`, `ai_federation_protocol`, `bandwidth_optimizer`, `conversation_manager`, `meta_architect`, `cli.py` — কোনো প্রোডাকশন ইমপোর্টার নেই, শুধু টেস্ট বা সেলফ-রেফারেন্স; ওয়্যারিং না করে আর্কাইভ করা যায়।
- **রাউটার-in-tools অ্যান্টি-প্যাটার্ন:** `api_gateway`, `auto_test_generator`, `style_learner`, `image_to_code`, `voice_coder`, `collaborative_editor`, `comment_thread_ai`, `multilingual_tts` — FastAPI `APIRouter` tools/ প্যাকেজে এমবেড করা; `api_gateway.py` সবচেয়ে স্পষ্ট মিসলোকেশন (api/routes/ এ যাওয়া উচিত)।
- **নেমিং-ডোমেইন বিভ্রান্তি:** `bandwidth_optimizer` আসলে প্রম্পট-কমপ্রেসর; `vulnerability_predictor` ML নয়, প্যাটার্ন-স্ক্যানার; `ai_federation_protocol` মাত্র ইন-মেমরি ডিকশনারি রেজিস্ট্রি; `meta_architect` আসলে মেট্রিক্স-অ্যানালাইজার — এই ৪টি + prophet/mage র‍্যাপার দুটিই ⚠️ হটস্পট।
- **security_tools/ প্যাকেজ মিশ্র ডোমেইন:** `multi_account_rotator` (৯৫৯ লাইন) আসলে LLM API-কী রোটেশন — services/llm/ এ যাওয়া উচিত; `proxy_manager`/`vpn_switcher` স্ক্র্যাপিং-অ্যানোনিমিটি; প্যাকেজ নাম "security" দুই অর্থেই বিভ্রান্তিকর।
- **স্ক্রিপ্টস-এ মিশ্র ধরন:** বাস্তব one-off মাইগ্রেশন (`migrate_*`, `update_imports`) আর পুনঃব্যবহারযোগ্য লোডার (`load_seed_data.py`-এর `SeedDataLoader` ক্লাস) একসাথে; migrations/ সাবফোল্ডার ব্যবহার করলে ৫টি ফাইল গুছি যায়; `tools/seed_database.py` scripts/seed_* পরিবারের সাথে মেলে।
- **ভাঙা/অস্থির নির্ভরতা:** `knowledge_base_indexer` যে `tools/seed_data/` ইনডেক্স করে সে ডিরেক্টরিই নেই; `seed_tools_registry`-র মেটাডেটা পুরনো ফ্ল্যাট `tools/*.py` পাথ নির্দেশ করে; `bangla_ai_connector` example.com হার্ডকোড; `git_knowledge_extractor`-এ ডুপ্লিকেট ডকস্ট্রিং ব্লক।
- **মনোলিথ:** `telegram_bot.py` (১৩৯২ লাইন) ও `superai_free_tier_monitor.py` (১৩৭৫ লাইন) — দুটোই নামে ঠিক কিন্তু কমান্ড/চেকার-ভিত্তিক স্প্লিট দরকার; `tools/__init__.py`-এর LazyModule শিম মাইগ্রেশন শেষে অপসারণযোগ্য।


---

## ব্যাচ ০৭ — Agent, Brain, Memory ও Evolution সিস্টেম
**ব্যাচ:** 07 | **তালিকাভুক্ত:** 138 | **বিশ্লেষিত:** 138 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 11 | **স্থানান্তর প্রস্তাব:** 10 | **⚠️ সেমান্টিক মিসম্যাচ:** 19

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| __init__.py | backend/agents/__init__.py | এজেন্ট প্যাকেজ init — ১৩+ এজেন্ট ক্লাস re-export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| autonomous_agent.py | backend/agents/autonomous_agent.py | system_health_agent-এর ডিপ্রিকেটেড facade shim | মুছে ফেলুন ❌ (shim) | — | ⚠️ নামে autonomous, কিন্তু health-monitor facade |
| base_pydantic_agent.py | backend/agents/base_pydantic_agent.py | PydanticAI বেস এজেন্ট, MCP টুল রেজিস্ট্রেশনসহ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| churn_prophet.py | backend/agents/churn_prophet.py | Firestore থেকে churn-ঝুঁকি স্কোরিং ও retention স্ট্র্যাটেজি | churn_risk_agent.py | অপরিবর্তিত ✅ | ⚠️ "prophet" ফাঁকা; কাজ churn-ঝুঁকি স্কোরিং |
| __init__.py | backend/agents/devops/__init__.py | কমেন্ট-অনলি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cloud_watchman.py | backend/agents/devops/cloud_watchman.py | Firebase/Vercel/GCP কোটা-বিলিং-এরর মনিটর ও অ্যালার্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cost_sage.py | backend/agents/devops/cost_sage.py | API খরচ ট্র্যাকিং, বাজেট ম্যানেজার ও অপ্টিমাইজেশন সাজেশন | api_cost_tracking_agent.py | অপরিবর্তিত ✅ | ⚠️ "sage" অস্পষ্ট; কাজ API-খরচ ট্র্যাকিং |
| __init__.py | backend/agents/domain/__init__.py | ডকস্ট্রিং-অনলি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bangla_nlp_agent.py | backend/agents/domain/bangla_nlp_agent.py | বাংলা ট্রান্সলিটারেশন, সেন্টিমেন্ট ও টেক্সট প্রসেসিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ephemeral_executor.py | backend/agents/ephemeral_executor.py | ডকার-স্যান্ডবক্সড এককালীন স্কিল এক্সিকিউশন, কোটা+AST স্ক্যান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/agents/evolution_agents/__init__.py | ডকস্ট্রিং-অনলি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| adversarial_defense_agent.py | backend/agents/evolution_agents/adversarial_defense_agent.py | প্রম্পট-ইনজেকশন/জেইলব্রেক ডিটেকশন ও প্রতিরক্ষা | অপরিবর্তিত ✅ | backend/agents/security/ | নিরাপত্তা-এজেন্ট গ্রুপিং স্পষ্ট হয় |
| federated_learning_agent.py | backend/agents/evolution_agents/federated_learning_agent.py | Deprecated shim — unified_learning ইঞ্জিনে ডেলিগেট | মুছে ফেলুন ❌ (shim) | — | ⚠️ shim, শুধু deprecation warning |
| meta_learning_agent.py | backend/agents/evolution_agents/meta_learning_agent.py | Deprecated shim — unified_learning ইঞ্জিনে ডেলিগেট | মুছে ফেলুন ❌ (shim) | — | ⚠️ shim, শুধু deprecation warning |
| multi_agent_collaboration_agent.py | backend/agents/evolution_agents/multi_agent_collaboration_agent.py | ক্যাপাবিলিটি ডিসকভারি, টাস্ক বিভাজন ও ফলাফল একত্রীকরণ | অপরিবর্তিত ✅ | backend/agents/coordination/ | coordination গ্রুপিং evolution_agents-চেয়ে স্পষ্ট |
| __init__.py | backend/agents/governance/__init__.py | ডকস্ট্রিং-অনলি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bias_detection_agent.py | backend/agents/governance/bias_detection_agent.py | রেগেক্স-ভিত্তিক বায়াস শনাক্তকরণ ও মিটিগেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ethics_monitor_agent.py | backend/agents/governance/ethics_monitor_agent.py | AI সিদ্ধান্তের নীতিগত (ethics) মূল্যায়ন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| explainability_agent.py | backend/agents/governance/explainability_agent.py | AI সিদ্ধান্তের ব্যাখ্যা তৈরি ও সংরক্ষণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| governance_agent.py | backend/agents/governance/governance_agent.py | অ্যাক্সেস কন্ট্রোল, পলিসি ও সিদ্ধান্ত ওভারসাইট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| headless_terminal_agent.py | backend/agents/headless_terminal_agent.py | NL→শেল কমান্ড ইন্টারপ্রেটার, সেফটি চেক ও subprocess exec | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/agents/ide/__init__.py | init — trio adapter exports | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| trio_adapters.py | backend/agents/ide/trio_adapters.py | Gemini-লেখক/Kilo-রিভিউয়ার/Cline-চেকার পাইপলাইন অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/agents/infrastructure/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_scaling_agent.py | backend/agents/infrastructure/auto_scaling_agent.py | চাহিদা অনুযায়ী রিসোর্স স্কেলিং সুপারিশ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cost_optimization_agent.py | backend/agents/infrastructure/cost_optimization_agent.py | খরচ মেট্রিক, সঞ্চয়-সুযোগ ও বাজেট অ্যালার্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (cost_sage-এর সাথে ওভারল্যাপ) |
| disaster_recovery_agent.py | backend/agents/infrastructure/disaster_recovery_agent.py | অটো zip-ব্যাকআপ ও রিকভারি প্রসিডিউর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| performance_tuning_agent.py | backend/agents/infrastructure/performance_tuning_agent.py | psutil মেট্রিক ভিত্তিক পারফরম্যান্স টিউনিং সুপারিশ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (performance_guardian-এর সাথে ওভারল্যাপ) |
| insight_mage.py | backend/agents/insight_mage.py | ট্রেন্ড/অ্যানোমালি ডিটেকশন ও LLM NL-রিপোর্ট জেনারেশন | analytics_insight_agent.py | অপরিবর্তিত ✅ | ⚠️ "mage" অর্থহীন; কাজ অ্যানালিটিক্স রিপোর্ট |
| internet_monitor_agent.py | backend/agents/internet_monitor_agent.py | GitHub trending ও AI আপডেট মনিটর, Redis-এ সংরক্ষণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/agents/monitoring/__init__.py | ডকস্ট্রিং-অনলি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| competitor_analysis_agent.py | backend/agents/monitoring/competitor_analysis_agent.py | প্রতিযোগীর রিলিজ/ফিচার ট্র্যাকিং ও গ্যাপ বিশ্লেষণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| compliance_monitor_agent.py | backend/agents/monitoring/compliance_monitor_agent.py | GDPR/HIPAA-সহ কমপ্লায়েন্স রুল স্ক্যান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| predictive_analytics_agent.py | backend/agents/monitoring/predictive_analytics_agent.py | exponential-smoothing টাইম-সিরিজ ফোরকাস্টিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| technology_radar_agent.py | backend/agents/monitoring/technology_radar_agent.py | উদীয়মান প্রযুক্তি ট্র্যাকিং ও অ্যাডপশন সুপারিশ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| morphic_adapter.py | backend/agents/morphic_adapter.py | Gemini দিয়ে raw কোড → execute_tool কনট্র্যাক্টে রি-রাইট | tool_contract_adapter.py | backend/skills/lifecycle/ | ⚠️ "morphic" অস্পষ্ট; skill-পাইপলাইনের অংশ |
| performance_guardian.py | backend/agents/performance_guardian.py | সিস্টেম মেট্রিক, অ্যানোমালি, বটলনেক ও স্কেলিং পরামর্শ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sentinel_agent.py | backend/agents/sentinel_agent.py | হার্টবিট মনিটর, z-score অ্যানোমালি, Discord অ্যালার্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (AnomalyDetector ডুপ্লিকেট) |
| skill_gc.py | backend/agents/skill_gc.py | অব্যবহৃত স্কিল গ্রেস-পিরিয়ডে আর্কাইভ/পার্জ | অপরিবর্তিত ✅ | backend/skills/lifecycle/ | skill লাইফসাইকেল এক প্যাকেজে |
| skill_ingestor.py | backend/agents/skill_ingestor.py | zip ডাউনলোড, AST সেফটি, স্যান্ডবক্স কোয়ারেন্টাইন টেস্ট | অপরিবর্তিত ✅ | backend/skills/lifecycle/ | skill লাইফসাইকেল এক প্যাকেজে |
| skill_librarian.py | backend/agents/skill_librarian.py | অ্যাডমিন অনুমোদনে স্কিল স্থানান্তর ও Discord নোটিফিকেশন | অপরিবর্তিত ✅ | backend/skills/lifecycle/ | skill লাইফসাইকেল এক প্যাকেজে |
| __init__.py | backend/agents/syncguard/__init__.py | ডকস্ট্রিং-অনলি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| config.yaml | backend/agents/syncguard/config.yaml | SyncGuard এজেন্ট পারসোনা/রোল কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| syncguard_agent.py | backend/agents/syncguard/syncguard_agent.py | ইনফ্রা/env/Redis সিঙ্ক অডিট, SYNC_OK/FAILED | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tools.py | backend/agents/syncguard/tools.py | অডিট টুল — infra-drift mock, env ও Redis চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (drift-check mock) |
| accessibility_agent.py | backend/agents/ux/accessibility_agent.py | HTML/WCAG অ্যাক্সেসিবিলিটি স্ক্যান ও রিপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vulnerability_prophet.py | backend/agents/vulnerability_prophet.py | হিউরিস্টিক+LLM ভালনারেবিলিটি স্ক্যান, APIRouter আছে | vulnerability_scanner_agent.py | backend/agents/security/ | ⚠️ "prophet" অস্পষ্ট; আসলে স্ক্যানার, security-গ্রুপ |
| __init__.py | backend/brain/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_department.py | backend/brain/agent_department.py | facade shim — core.agents.framework.agent_department | মুছে ফেলুন ❌ (shim) | — | ⚠️ agent_departments-এর সাথে নাম-সংঘর্ষ |
| agent_departments.py | backend/brain/agent_departments.py | facade shim — agent_departments re-export | মুছে ফেলুন ❌ (shim) | — | ⚠️ singleton/plural টুইন shim |
| api_router.py | backend/brain/api_router.py | in-process ক্যাপাবিলিটি হ্যান্ডলার রেজিস্ট্রি/ডিসপ্যাচ | capability_dispatcher.py | অপরিবর্তিত ✅ | ⚠️ "api_router" বিভ্রান্তিকর — HTTP রাউটার নয় |
| autonomous_agent.py | backend/brain/autonomous_agent.py | facade shim — task_runner_agent re-export | মুছে ফেলুন ❌ (shim) | — | ⚠️ shim; agents/-এর হোমোনিমের সাথে বিভ্রান্তি |
| __init__.py | backend/brain/causal/__init__.py | causal সাবপ্যাকেজ exports | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| discovery.py | backend/brain/causal/discovery.py | টেলিমেট্রি থেকে causal DAG ডিসকভারি (correlation fallback) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| interventions.py | backend/brain/causal/interventions.py | ডিপ্লয়/কনফিগ/স্কেলিং ইন্টারভেনশন লগিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| root_cause.py | backend/brain/causal/root_cause.py | causal গ্রাফ থেকে root cause রিপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cognitive_router.py | backend/brain/cognitive_router.py | কীওয়ার্ড-হিউরিস্টিক প্রোভাইডার/মডেল রাউটার | heuristic_model_router.py | অপরিবর্তিত ✅ | ⚠️ "cognitive" ফাঁকা; সাধারণ হিউরিস্টিক রাউট |
| economic_optimizer.py | backend/brain/economic_optimizer.py | বাজেট-সচেতন প্রোভাইডার টায়ার নির্বাচন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| expert_router.py | backend/brain/expert_router.py | facade — core advanced_model_router-এ MoE ব্রিজ | মুছে ফেলুন ❌ (merge) | — | core advanced router-এ merge করুন |
| gcp_router.py | backend/brain/gcp_router.py | GCP Cloud Run নোডে HTTP টাস্ক রাউটিং ও হেলথচেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| langgraph_agent.py | backend/brain/langgraph_agent.py | ৩-লাইনের facade shim — langgraph re-export | মুছে ফেলুন ❌ (shim) | — | ⚠️ নাম ইঙ্গিত দেয় LangGraph ইমপ্ল, বাস্তবে shim |
| mcp_client.py | backend/brain/mcp_client.py | stdio JSON-RPC MCP ক্লায়েন্ট, টুল ডিসকভারি/কল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| model_registry.py | backend/brain/model_registry.py | স্ট্যাটিক মডেল ক্যাটালগ — টায়ার, দাম, কনটেক্সট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| model_router.py | backend/brain/model_router.py | LLMGateway-এর compat facade, circuit breaker+streaming | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| parallel_cloud_router.py | backend/brain/parallel_cloud_router.py | GCP/Railway/Render-এ ওজন-ভিত্তিক ট্রাফিক বিভাজন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| performance_aware_router.py | backend/brain/performance_aware_router.py | latency/cost স্কোরিং রাউটার + facade ডুপ্লিকেট | মুছে ফেলুন ❌ (merge) | — | advanced router-এ স্কোরিং লজিক merge করুন |
| reasoning_orchestrator.py | backend/brain/reasoning_orchestrator.py | কীওয়ার্ড-ভিত্তিক cot/tot মোড নির্বাচন ও প্রম্পট enrich | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| supreme_learning_engine.py | backend/brain/supreme_learning_engine.py | Deprecated shim — unified_learning ডেলিগেট | মুছে ফেলুন ❌ (shim) | — | ⚠️ shim; "supreme" ব্র্যান্ডিং অপ্রয়োজনীয় |
| task_execution_engine.py | backend/brain/task_execution_engine.py | DAG-নির্ভর টাস্ক এক্সিকিউশন, প্যারালাল/সিকোয়েন্সিয়াল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| user_digital_twin.py | backend/brain/user_digital_twin.py | ইউজার স্টাইল-DNA ও প্রেফারেন্স প্রোফাইলার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Dockerfile.test | backend/ecosystem/Dockerfile.test | standalone ecosystem অ্যাপের টেস্ট Dockerfile | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/ecosystem/__init__.py | ecosystem প্যাকেজ exports (১৩ মডিউল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| _store.py | backend/ecosystem/_store.py | শেয়ার্ড SQLite (WAL) স্টোর হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| approval_workflow.py | backend/ecosystem/approval_workflow.py | হাই-রিস্ক প্রসপোজাল অ্যাপ্রুভাল স্টেট-মেশিন, কুলডাউন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| capability_registry.py | backend/ecosystem/capability_registry.py | ক্যাপাবিলিটি লাইফসাইকেল রেজিস্ট্রি (SQLite) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| correlation.py | backend/ecosystem/correlation.py | করিলেশন-ID কনটেক্সট, ডিস্ট্রিবিউটেড ট্রেসিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| deployment_tracker.py | backend/ecosystem/deployment_tracker.py | ডিপ্লয়মেন্ট লাইফসাইকেল স্টেট-মেশিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| governance.py | backend/ecosystem/governance.py | রিস্ক ক্লাসিফিকেশন, বাজেট এনফোর্সমেন্ট, অথরাইজেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| health_model.py | backend/ecosystem/health_model.py | ইউনিফায়েড হেলথ এগ্রিগেশন মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| learning_loop.py | backend/ecosystem/learning_loop.py | self-evolution স্টেজ-মেশিন (signal→proposal→capability) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_skeleton.py | backend/ecosystem/mcp_skeleton.py | MCP OBSERVE/ANALYZE/ACT অপ ইন্টারফেস, গেটেড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| resource_registry.py | backend/ecosystem/resource_registry.py | প্রোভাইডার-অ্যাগনস্টিক রিসোর্স রেজিস্ট্রি ও অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| seed_ecosystem.py | backend/ecosystem/seed_ecosystem.py | ইডেম্পোটেন্ট ডেমো-ডাটা সিডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| source_governance.py | backend/ecosystem/source_governance.py | এক্সটার্নাল সোর্স পলিসি গেট (allowlist/block) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| standalone_app.py | backend/ecosystem/standalone_app.py | ৪৭-endpoint standalone FastAPI অ্যাপ + stdlib auth | অপরিবর্তিত ✅ | backend/ecosystem/app/ (বিভাজন) | ১৪৬৪ লাইনের মনোলিথ — auth/admin/public ভাগ করুন |
| task_engine.py | backend/ecosystem/task_engine.py | ইউজার টাস্ক স্টেট-মেশিন, রিট্রাই/টাইমআউট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| users.py | backend/ecosystem/users.py | stdlib PBKDF2+JWT ইউজার/সেশন স্টোর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/engine/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/engine/compression/__init__.py | compression সাবপ্যাকেজ exports | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_token_juice.py | backend/engine/compression/test_token_juice.py | কম্প্রেসরের ইউনিট টেস্ট (সোর্সের পাশে colocated) | test_context_compressor.py | backend/tests/engine/ | colocated টেস্ট tests/-এ যাবে |
| token_juice.py | backend/engine/compression/token_juice.py | ডিটারমিনিস্টিক টুল-আউটপুট/কনটেক্সট কম্প্রেসর | context_compressor.py | অপরিবর্তিত ✅ | ⚠️ "TokenJuice" ব্র্যান্ড-নাম; কাজ কনটেক্সট কম্প্রেশন |
| cost_optimizer.py | backend/engine/cost_optimizer.py | complexity-ভিত্তিক সস্তা রুট ল্যাডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; economic_optimizer-এর সাথে ওভারল্যাপ |
| debate_engine.py | backend/engine/debate_engine.py | propose/judge/rethink মাল্টি-এজেন্ট ডিবেট কনসেনসাস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| embedding.py | backend/engine/embedding.py | লোকাল-ফার্স্ট এমবেডিং সার্ভিস (MiniLM) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| forge_compiler.py | backend/engine/forge_compiler.py | React Flow DAG → টপোলজিক্যাল এক্সিকিউশন অর্ডার | dag_execution_sorter.py | অপরিবর্তিত ✅ | ⚠️ "forge compiler" অস্পষ্ট; আসলে DAG সর্টার |
| memory_middleware.py | backend/engine/memory_middleware.py | ভেক্টর-মেমরি থেকে প্রম্পটে RAG কনটেক্সট ইনজেকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| self_reflection.py | backend/engine/self_reflection.py | LLM-চালিত পোস্ট-টাস্ক সেলফ-ক্রিটিক লুপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| smart_router.py | backend/engine/smart_router.py | ইনটেন্ট ক্লাসিফিকেশন → মডেল ম্যাপিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (রাউটার-স্প্রল নোট) |
| tool_forge.py | backend/engine/tool_forge.py | AST-স্ক্যান সহ ডাইনামিক টুল সিন্থেসিস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tree_of_thought.py | backend/engine/tree_of_thought.py | ToT মাল্টি-ব্রাঞ্চ রিজনিং ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vector_db.py | backend/engine/vector_db.py | experience-মেমরি adapter (Pinecone-shaped legacy) | experience_memory_adapter.py | অপরিবর্তিত ✅ | ⚠️ ভেক্টর DB নয় — memory_service অ্যাডাপ্টার |
| worker_node.py | backend/engine/worker_node.py | NATS এজ-ওয়ার্কার — হার্টবিট ও টাস্ক সাবস্ক্রিপশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| worker_registry.py | backend/engine/worker_registry.py | NATS KV-তে ওয়ার্কার মনিটর ও স্মার্ট রাউটিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/evolution/__init__.py | core.self_evolution + লোকাল মডিউল re-export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| advanced_evolution_engine.py | backend/evolution/advanced_evolution_engine.py | স্টাব — improvements×১.১৫ "gain" রিটার্ন করে | মুছে ফেলুন ❌ (স্টাব) | — | ⚠️ ইঞ্জিন নাম, কিন্তু ভুয়া ফিক্সড গেইন |
| artifact_integrity.py | backend/evolution/artifact_integrity.py | ডিপ্লয়ের আগে SHA-256 আর্টিফ্যাক্ট হ্যাশ গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_evolution_controller.py | backend/evolution/auto_evolution_controller.py | monitor/tune/consolidate লুপের মাস্টার অর্কেস্ট্রেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_tuner.py | backend/evolution/auto_tuner.py | বেয়েসিয়ান/অ্যানিলিং/জেনেটিক হাইপারপ্যারাম টিউনিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| benchmark_runner.py | backend/evolution/benchmark_runner.py | baseline বনাম candidate বেঞ্চমার্ক ও প্রমোশন সিদ্ধান্ত | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| canary_manager.py | backend/evolution/canary_manager.py | ক্যানারি রোলআউট কন্ট্রোলার ও অটো-রোলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| change_proposal.py | backend/evolution/change_proposal.py | সেলফ-মডিফিকেশন প্রসপোজাল লাইফসাইকেল গভর্নেন্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| fitness_evaluator.py | backend/evolution/fitness_evaluator.py | ওয়েটেড মাল্টি-ফ্যাক্টর ফিটনেস স্কোরিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| memory_consolidator.py | backend/evolution/memory_consolidator.py | HOT→FROZEN টায়ার্ড মেমরি-ব্লক ম্যানেজার, dedup | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| performance_monitor.py | backend/evolution/performance_monitor.py | মেট্রিক, z-score অ্যানোমালি ও মাল্টি-সেভারিটি অ্যালার্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ৩য় পারফরম্যান্স-মনিটর ডুপ্লিকেট |
| strategy_optimizer.py | backend/evolution/strategy_optimizer.py | UCB/epsilon-greedy স্ট্র্যাটেজি নির্বাচন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/memory/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| checkpoint_resume.py | backend/memory/checkpoint_resume.py | CheckpointManager-এর পাতলা wrapper | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; পাতলা wrapper মার্জযোগ্য |
| chromadb_store.py | backend/memory/chromadb_store.py | ChromaDB ভেক্টর স্টোর + TF-IDF ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cloud_postgres_store.py | backend/memory/cloud_postgres_store.py | প্রোডাকশন Postgres স্টোর, স্কিমা ভেরিফাই | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| episodic_memory.py | backend/memory/episodic_memory.py | টাস্ক-এপিসোড স্টোর + সিমিলারিটি সার্চ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| hierarchical_tree.py | backend/memory/hierarchical_tree.py | ৩-স্তরের হায়ারার্কিক্যাল মেমরি ট্রি, রোলআপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| long_term_memory.py | backend/memory/long_term_memory.py | Supabase-এ এমবেডিংসহ long-term learnings | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mcp_server.py | backend/memory/mcp_server.py | সম্পূর্ণ মেমরি সিস্টেমের MCP সার্ভার (stdio/SSE) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rag_pipeline.py | backend/memory/rag_pipeline.py | চাংক/ইনজেস্ট/রিট্রিভ + HyDE সার্চ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sliding_window.py | backend/memory/sliding_window.py | টোকেন-উইন্ডো কনটেক্সট মেমরি, SQLite সংরক্ষণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sqlite_store.py | backend/memory/sqlite_store.py | SQLite সেশন/টাস্ক/ট্রানজ্যাকশন স্টোর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (ক্লাস SQLiteMemoryStore) |
| summary_tree.py | backend/memory/summary_tree.py | নিভ হায়ারার্কিক্যাল সামারি হেল্পার (স্টাব-মানের) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; hierarchical_tree-তে merge বিবেচ্য |
| supabase_store.py | backend/memory/supabase_store.py | Supabase/pgvector স্টোর, SQLite ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_hierarchical_tree.py | backend/memory/test_hierarchical_tree.py | HierarchicalMemoryTree ইউনিট টেস্ট (colocated) | অপরিবর্তিত ✅ | backend/tests/memory/ | colocated টেস্ট tests/-এ যাবে |
| unified_db_manager.py | backend/memory/unified_db_manager.py | ৪-store মাল্টি-DB রাইট কোঅর্ডিনেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ভাঙা SQLiteStore ইমপোর্ট সংশোধন করুন |
| vector_store_config.py | backend/memory/vector_store_config.py | ভেক্টর ব্যাকএন্ড env কনফিগ ডেটাক্লাস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/skills/__init__.py | core.skills ফ্যাকেড + provisioner/registry re-export | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| core_doc_summarizer.py | backend/skills/core_doc_summarizer.py | Gemini ডক-সামারাইজার স্কিল, circuit breaker সহ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| core_knowledge_qa.py | backend/skills/core_knowledge_qa.py | পারমিশন-সচেতন RAG QA স্কিল (Supabase pgvector) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| core_doc_summarizer.json | backend/skills/manifests/core_doc_summarizer.json | স্কিল ম্যানিফেস্ট — RBAC, বাজেট, অডিট ফিল্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| core_knowledge_qa.json | backend/skills/manifests/core_knowledge_qa.json | স্কিল ম্যানিফেস্ট — RBAC, বাজেট, অডিট ফিল্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| provisioner.py | backend/skills/provisioner.py | স্কিল ডিপেন্ডেন্সি অটো-ইনস্টলার (pip/system CLI) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| skill_registry.py | backend/skills/skill_registry.py | manifest ডিসকভারি ও স্কিল রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **রাউটার-স্প্রল (সবচেয়ে বড় সমস্যা):** brain/-এ ৭টি রাউটার (model_router, cognitive_router, expert_router, performance_aware_router, gcp_router, parallel_cloud_router, api_router) + engine/smart_router, engine/cost_optimizer, brain/economic_optimizer — মডেল-নির্বাচন লজিক ৬+ জায়গায় ছড়ানো; expert_router ও performance_aware_router facade-merge, cognitive_router রিনেম প্রস্তাবিত।
- **Phase-1 consolidation shim-জঞ্জাল:** ১১টি shim/stub — brain/agent_department vs agent_departments (একই ক্লাসনাম, ভিন্ন ক্লাস), autonomous_agent নামে ২টি ভিন্ন facade (agents/-এ health-monitor, brain/-এ task-runner), langgraph_agent, expert_router, performance_aware_router, ৩টি learning shim (federated/meta/supreme) — migration শেষে সবই delete-প্রস্তাবিত।
- **evolution/-এ ফ্যান্টাসি বনাম বাস্তবতা:** advanced_evolution_engine ভুয়া ×1.15 gain রিটার্ন করা স্টাব (⚠️ হটস্পট), বাকি পাইপলাইন (change_proposal → benchmark → canary → artifact_integrity → rollback) আসলে ভালোভাবে ডিজাইন করা self-modification গভর্নেন্স — প্যাকেজটি নাম বদলে self_modification/ রাখা যেত।
- **স্কিল পাইপলাইন ৩ ডিরেক্টরিতে বিভক্ত:** ingestor/librarian/gc/morphic_adapter agents/-তে, registry/provisioner/manifests skills/-তে, manifest স্কিমা schemas/-তে — backend/skills/lifecycle/ প্রস্তাব; evolution_agents/ প্যাকেজ ২টি shim মুছে গেলে খালি হয়ে যায়, ভেঙে security/ ও coordination/-এ দিন।
- **cost/performance মনিটরিং ট্রিপলিকেট:** cost (cost_sage + cost_optimization_agent + cost_optimizer + economic_optimizer) এবং performance (performance_guardian + performance_tuning_agent + evolution/performance_monitor) — প্রতিটির AnomalyDetector-সহ লজিক ডুপ্লিকেট; merge দরকার।
- **ভাঙা ইমপোর্ট (bug):** memory/unified_db_manager.py `from memory.sqlite_store import SQLiteStore` — sqlite_store.py-তে ক্লাসটি নেই (আসল নাম SQLiteMemoryStore) → ইমপোর্ট-টাইম failure।
- **মনোলিথ:** ecosystem/standalone_app.py ১৪৬৪ লাইনে ৪৭ endpoint (auth+public+admin) — backend/ecosystem/app/ প্যাকেজে ভাগ; memory/mcp_server.py (৯৪৯ লাইন) সুসংগত তাই রাখা হলো।
- **colocated tests:** engine/compression/test_token_juice.py ও memory/test_hierarchical_tree.py backend/tests/-এ সরানো দরকার; memory/ ও ecosystem/ প্যাকেজের নামকরণ সামগ্রিকভাবে সবচেয়ে সুশৃঙ্খল — প্রায় সব ফাইলই নাম-অনুযায়ী কাজ করে।


---

## ব্যাচ ০৮ — Backend Models, Database ও অবশিষ্ট মডিউল
**ব্যাচ:** 08 | **তালিকাভুক্ত:** 255 | **বিশ্লেষিত:** 255 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 23 | **স্থানান্তর প্রস্তাব:** 15 | **⚠️ সেমান্টিক মিসম্যাচ:** 8

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| API-swagger.yaml | backend/API-swagger.yaml | OpenAPI 3.1 স্পেসিফিকেশন, FastAPI থেকে জেনারেটেড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড স্পেক; নাম-অবস্থান উপযুক্ত |
| COVERAGE_90_PLAN.md | backend/COVERAGE_90_PLAN.md | কভারেজ পরিকল্পনা-ডক; লক্ষ্য আপগ্রেডে ১০০% | TEST_COVERAGE_PLAN.md-এ মার্জ | অপরিবর্তিত ✅ | নামে ৯০ কিন্তু লক্ষ্য ১০০; ডুপ্লিকেট প্ল্যান ডক |
| Dockerfile | backend/Dockerfile | Poetry মাল্টি-স্টেজ প্রোডাকশন ইমেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Dockerfile.ci | backend/Dockerfile.ci | CI ইমেজ — torch/whisper ভারী ডিপেন্ডেন্সি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| README.md | backend/README.md | root README-তে পয়েন্টার-শুধু নোট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| TEST_COVERAGE_PLAN.md | backend/TEST_COVERAGE_PLAN.md | ১০০% টেস্ট কভারেজ বাস্তবায়ন পরিকল্পনা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত; মার্জ-টার্গেট |
| _INDEX.md | backend/_INDEX.md | AI-ন্যাভিগেশন ফাইল ইনডেক্স ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/__init__.py | প্যাকেজ ডকস্ট্রিং + get_settings রি-এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| action.yml | backend/action.yml | pyerrorfix GitHub Action মেটাডেটা/ইনপুট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/adapters/__init__.py | ডোমেইন অ্যাডাপ্টার প্যাকেজ ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| base_adapter.py | backend/adapters/base_adapter.py | BaseAdapter ABC + AdaptationResult + পারফ ট্র্যাকিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| business_adapter.py | backend/adapters/business_adapter.py | বিজনেস/ফাইন্যান্স অ্যানালিটিক্স ডোমেইন অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| dev_adapter.py | backend/adapters/dev_adapter.py | কোডিং/ডিবাগিং/রিফ্যাক্টর ডোমেইন অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ux_adapter.py | backend/adapters/ux_adapter.py | UI/UX ডিজাইন + WCAG অডিট অ্যাডাপ্টার (৪৮১ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/adaptive_engine/__init__.py | অ্যাডাপটিভ ইঞ্জিন প্যাকেজ init + engine info | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| experience_db.py | backend/adaptive_engine/experience_db.py | ChromaDB/pgvector এক্সপেরিয়েন্স স্টোর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| intent_parser.py | backend/adaptive_engine/intent_parser.py | ইউজার-ইনটেন্ট → AppSpecification JSON পার্সার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| learning_loop.py | backend/adaptive_engine/learning_loop.py | EWC-ভিত্তিক continual learning লুপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| platform_learner.py | backend/adaptive_engine/platform_learner.py | প্ল্যাটফর্ম ডক থেকে অ্যাডাপটেশন শেখা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| registry.py | backend/adaptive_engine/registry.py | PlatformProfile/PlatformRegistry রেজিস্ট্রি | platform_registry.py | অপরিবর্তিত ✅ | জেনেরিক নাম; ক্লাস PlatformRegistry |
| self_improving_agent.py | backend/adaptive_engine/self_improving_agent.py | ARCHIVED/SUPERSEDED হেডারযুক্ত পুরোনো এজেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড ডেড কোড — ডিলিট প্রস্তাব |
| supabase_vector_backend.py | backend/adaptive_engine/supabase_vector_backend.py | Supabase pgvector ভেক্টর ব্যাকএন্ড (ফ্রি-টায়ার) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/admin/__init__.py | অ্যাডমিন প্যাকেজ init + capabilities লিস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| god.py | backend/admin/god.py | কনস্টিটিউশনাল রাইট-অ্যাপ্রোভাল এনফোর্সমেন্ট লেয়ার | constitutional_approval_guard.py | অপরিবর্তিত ✅ | ⚠️ "god" আসলে অ্যাপ্রোভাল/গভর্নেন্স গার্ড |
| test_god.py | backend/admin/test_god.py | AdminGodLayer-এর ২৮০-লাইন ইউনিট টেস্ট | test_admin_approval_layer.py | backend/tests/admin/ | ⚠️ god-নাম অনুসরণ; টেস্ট tests/-এ যাবে |
| README | backend/alembic_migrations/README | জেনেরিক alembic কনফিগ নোট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/alembic_migrations/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| env.py | backend/alembic_migrations/env.py | alembic অনলাইন/অফলাইন মাইগ্রেশন env | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| script.py.mako | backend/alembic_migrations/script.py.mako | নতুন মাইগ্রেশন ফাইল টেমপ্লেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | alembic কনভেনশন — রিনেম নিষেধ |
| 001_initial_schema.sql | backend/alembic_migrations/versions/001_initial_schema.sql | সুপারসিডেড হিস্টোরিকাল SQL স্কিমা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | হিস্টোরিকাল; alembic .sql চালায় না; হেডার-সতর্কতা আছে |
| 2026_08_15_145220_add_system_alerts.py | backend/alembic_migrations/versions/2026_08_15_145220_add_system_alerts.py | system_alerts টেবিল তৈরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 2f7b3c5f620e_add_missing_indexes.py | backend/alembic_migrations/versions/2f7b3c5f620e_add_missing_indexes.py | মিসিং ইনডেক্স যোগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 358bcbe79a4a_add_idempotency.py | backend/alembic_migrations/versions/358bcbe79a4a_add_idempotency.py | আইডেম্পোটেন্সি টেবিল/কনস্ট্রেইন্ট যোগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 664fe16e33ca_add_ci_reports_table.py | backend/alembic_migrations/versions/664fe16e33ca_add_ci_reports_table.py | ci_reports টেবিল তৈরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| __init__.py | backend/alembic_migrations/versions/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| a1b2c3d4e5f6_add_automation_executions_table.py | backend/alembic_migrations/versions/a1b2c3d4e5f6_add_automation_executions_table.py | automation_executions টেবিল যোগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | রিভিশন-ID ডুপ্লিকেট — alembic চেইন ভাঙা |
| a1b2c3d4e5f6_add_patch_telemetry_table.py | backend/alembic_migrations/versions/a1b2c3d4e5f6_add_patch_telemetry_table.py | patch_telemetry টেবিল যোগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | একই রিভিশন-ID ডুপ্লিকেট — সংঘর্ষ |
| cb8d8501f289_merge_heads.py | backend/alembic_migrations/versions/cb8d8501f289_merge_heads.py | দুই মাইগ্রেশন হেড মার্জ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cfe7c95dbee2_add_sentinel_morphic_schema.py | backend/alembic_migrations/versions/cfe7c95dbee2_add_sentinel_morphic_schema.py | ৪৩+ টেবিলের বিশাল স্কিমা (১৮৪৯ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ⚠️ sentinel/morphic সাই-ফাই শব্দ, মূলত সাধারণ স্কিমা |
| ed9761fee64f_create_system_config.py | backend/alembic_migrations/versions/ed9761fee64f_create_system_config.py | system_config টেবিল তৈরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| f1a2b3c4d5e6_add_api_key_scopes_and_conv_ctx_unique.py | backend/alembic_migrations/versions/f1a2b3c4d5e6_add_api_key_scopes_and_conv_ctx_unique.py | scopes কলাম + ইউনিক ইনডেক্স যোগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| g2b3c4d5e6f7_reconcile_task_history_and_baseline.py | backend/alembic_migrations/versions/g2b3c4d5e6f7_reconcile_task_history_and_baseline.py | task_history রিকনসাইল + প্রোড ড্রিফট ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| h3i4j5k6l7m8_merge_heads.py | backend/alembic_migrations/versions/h3i4j5k6l7m8_merge_heads.py | তিন ব্রাঞ্চের হেড মার্জ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| j9k0l1m2n3o4_add_missing_live_model_tables.py | backend/alembic_migrations/versions/j9k0l1m2n3o4_add_missing_live_model_tables.py | লাইভ-মডেল ORM টেবিলগুলো যোগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| k1l2m3n4o5p6_fix_downgrade_upgrade_table_swap.py | backend/alembic_migrations/versions/k1l2m3n4o5p6_fix_downgrade_upgrade_table_swap.py | cfe7c95dbee2-এর ডাউনগ্রেড ত্রুটি সংশোধন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | corrective মাইগ্রেশন; নাম পরিবর্তন বর্ণনা করে |
| tier_s_features.py | backend/alembic_migrations/versions/tier_s_features.py | Tier-S ফিচারের টেবিল/কলাম যোগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ⚠️ tier_s অস্পষ্ট স্প্রিন্ট-নাম; রিনেম ঝুঁকিপূর্ণ |
| analyze_coverage.py | backend/analyze_coverage.py | coverage.json বিশ্লেষণ, টেস্ট-প্রায়োরিটি তালিকা | অপরিবর্তিত ✅ | backend/scripts/ | রুট-লেভেল dev স্ক্রিপ্ট scripts/-এ যাবে |
| audit_check.py | backend/audit_check.py | হার্ডকোডেড Windows-পাথ ওয়ান-অফ অডিট স্ক্রিপ্ট | অপরিবর্তিত ✅ | backend/scripts/ বা ডিলিট | c:\Users\n\ পাথ-নির্ভর ওয়ান-অফ কোড |
| autonomous_browser.py | backend/browser/autonomous_browser.py | লক্ষ্য-ভিত্তিক অটোনোমাস ব্রাউজার এজেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| browsing_memory.py | backend/browser/browsing_memory.py | সাইট-বিহেভিয়ার প্যাটার্ন মেমরি ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| semantic_dom.py | backend/browser/semantic_dom.py | এমবেডিং-ভিত্তিক সেমান্টিক DOM ম্যাচিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| swarm_browser.py | backend/browser/swarm_browser.py | প্যারালাল মাল্টি-এজেন্ট ব্রাউজার সোয়ার্ম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনটেন্ট সত্যিই swarm — নাম মেলে |
| vision_grounding.py | backend/browser/vision_grounding.py | ভিশন-ভিত্তিক এলিমেন্ট গ্রাউন্ডিং ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/byoc/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cloud_connector.py | backend/byoc/cloud_connector.py | GCP সার্ভিস-অ্যাকাউন্ট ক্রেডেনশিয়াল এনক্রিপ্ট/ভ্যালিডেট | gcp_credential_manager.py | অপরিবর্তিত ✅ | শুধুই GCP ক্রেডেনশিয়াল ম্যানেজার; নাম অতি-সাধারণ |
| container_orchestrator.py | backend/byoc/container_orchestrator.py | Cloud Run-এ স্কিল কনটেইনার ডিপ্লয় (Terraform) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| resource_manager.py | backend/byoc/resource_manager.py | ৯-লাইনের মক কোটা স্টাব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ফাঁকা স্টাব — ডিলিট প্রস্তাব |
| __init__.py | backend/config/__init__.py | Settings রি-এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| byoc_limits.json | backend/config/byoc_limits.json | BYOC কনটেইনার কোটা লিমিট (টায়ারভিত্তিক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| constitutional_rules.json | backend/config/constitutional_rules.json | কনসেনসাস/হ্যালুসিনেশন পেনাল্টি স্কোরিং কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pricing_tiers.json | backend/config/pricing_tiers.json | প্রাইসিং টায়ার ও ক্রেডিট কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| routing_policy.json | backend/config/routing_policy.json | complexity-ভিত্তিক মডেল রাউটিং পলিসি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| settings.py | backend/config/settings.py | দ্বিতীয় Settings সিস্টেম (env-ভিত্তিক) | core/config.py-এ মার্জ | অপরিবর্তিত ✅ | core/config.py-র সমান্তরাল ডুপ্লিকেট সেটিংস |
| conftest.py | backend/conftest.py | রুট pytest ফিক্সচার: env/redis/API মক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | pytest rootdir conftest — অবস্থান সঠিক |
| __init__.py | backend/database/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| schema_contract.yaml | backend/database/contracts/schema_contract.yaml | ক্যানোনিকাল প্রোডাকশন স্কিমা কনট্র্যাক্ট (CI-চেকড) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| db_repository.py | backend/database/db_repository.py | Firebase→Supabase ফেইলওভার SmartDataRepository | smart_data_repository.py | অপরিবর্তিত ✅ | জেনেরিক ফাইলনাম; ক্লাস SmartDataRepository |
| 01_initial_setup.sql | backend/database/migrations/01_initial_setup.sql | github_repos/system_config/feature_flags স্কিমা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 02_phase2_setup.sql | backend/database/migrations/02_phase2_setup.sql | audit_logs/tools_registry/dynamic_skills টেবিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 03_user_preferences_and_metrics.sql | backend/database/migrations/03_user_preferences_and_metrics.sql | ইউজার-প্রেফারেন্স ও ইউসেজ মেট্রিক্স টেবিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 04_schema_upgrade.sql | backend/database/migrations/04_schema_upgrade.sql | অ্যাডমিন-প্ল্যান অনুযায়ী স্কিমা আপগ্রেড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 05_seed_github_repos.sql | backend/database/migrations/05_seed_github_repos.sql | github_repos সিড ডেটা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 06_referral_system.sql | backend/database/migrations/06_referral_system.sql | রেফারেল কোড/স্ট্যাটাস টেবিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 07_tenant_config.sql | backend/database/migrations/07_tenant_config.sql | টেন্যান্ট লিমিট/বিলিং টায়ার টেবিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 08_sso_configs.sql | backend/database/migrations/08_sso_configs.sql | টেন্যান্ট SSO প্রোভাইডার কনফিগ টেবিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 09_offline_sync_logs.sql | backend/database/migrations/09_offline_sync_logs.sql | অফলাইন অ্যাকশন কিউ/সিঙ্ক টেবিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 10_tenant_sso_offline.sql | backend/database/migrations/10_tenant_sso_offline.sql | টেন্যান্ট লিমিট পুনর্নির্মাণ (৭→১০ রিনেম) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 15_add_user_indexes.sql | backend/database/migrations/15_add_user_indexes.sql | user_id/conversation_id ইনডেক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 16_add_match_experiences_rpc.sql | backend/database/migrations/16_add_match_experiences_rpc.sql | pgvector সিমিলারিটি RPC ফাংশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 17_enable_rls.sql | backend/database/migrations/17_enable_rls.sql | সব টেবিলে RLS + পলিসি সক্রিয় | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| 18_fix_missing_rls_policies.sql | backend/database/migrations/18_fix_missing_rls_policies.sql | মিসিং RLS পলিসি (deny-all বাগ) সংশোধন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম পরিবর্তন বর্ণনা করে |
| multi_db_router.py | backend/database/multi_db_router.py | মাল্টি-DB রাউটার + ট্রানজেকশনাল আউটবক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pgbouncer_pool.py | backend/database/pgbouncer_pool.py | PgBouncer-নিরাপদ asyncpg পুল (আসল ইমপ্ল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | রিয়েল ইমপ্ল; core-এ শুধু shim |
| session.py | backend/database/session.py | অ্যাসিঙ্ক ইঞ্জিন/সেশন ফ্যাক্টরি + হেলথ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| storage_client.py | backend/database/storage_client.py | Supabase/S3 অবজেক্ট-স্টোরেজ ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ইমপোর্টার-শূন্য — ডিলিট বা storage/-এ মার্জ |
| supabase_client.py | backend/database/supabase_client.py | SupabaseDB গড-ক্লায়েন্ট (১০৬২ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; মনোলিথ — ভাঙার প্রস্তাব |
| tenant_db.py | backend/database/tenant_db.py | টেন্যান্ট-আইসোলেটেড Firestore ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | রিয়েল ইমপ্ল; core-এ shim আছে |
| Current Agents & future plan in the Project.md | backend/docker/Current Agents & future plan in the Project.md | এজেন্ট ইনভেন্টরি + ভবিষ্যৎ পরিকল্পনা নোট | agents-overview.md | backend/docs/ | স্পেস-যুক্ত ফাইলনাম; পুরোনো চ্যাট-ডাম্প ডক |
| swarm-worker.Dockerfile | backend/docker/swarm-worker.Dockerfile | NATS-ভিত্তিক এজে ওয়ার্কার ইমেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LATEST-PUSH-SUMMARY.md | backend/docs/autogen/LATEST-PUSH-SUMMARY.md | অটো-জেনারেটেড পুশ সামারি (LLM ফেইল কনটেন্ট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড আর্টিফ্যাক্ট |
| changelog_full.md | backend/docs/autogen/changes/changelog_full.md | অটো-জেনারেটেড কেন্দ্রীয় চেঞ্জলগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড আর্টিফ্যাক্ট |
| PUSH-SUMMARY-22eff1f7cf.md | backend/docs/autogen/summaries/PUSH-SUMMARY-22eff1f7cf.md | পুশ সামারি — LATEST ফাইলের ডুপ্লিকেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডুপ্লিকেট অটোজেন সামারি — ক্লিনআপ করুন |
| retry_integration_example.py | backend/docs/examples/retry_integration_example.py | রিট্রাই-হ্যান্ডলার ইন্টিগ্রেশন উদাহরণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sample_buggy.py | backend/examples/sample_buggy.py | pyerrorfix ডিটেক্টর পরীক্ষার ইচ্ছাকৃত-ত্রুটি ফিক্সচার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| hardcoded_llm.json | backend/hardcoded_llm.json | হার্ডকোডেড LLM প্যারামের স্ক্যান-আউটপুট তালিকা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | f:/ পাথ-সহ ওয়ান-অফ আর্টিফ্যাক্ট — ডিলিট |
| __init__.py | backend/integrations/__init__.py | ওপেন-সোর্স ইন্টিগ্রেশন লেয়ার প্যাকেজ ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| _flags.py | backend/integrations/_flags.py | ফিচার-ফ্ল্যাগ + optional-import হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| browser_use_adapter.py | backend/integrations/browser_use_adapter.py | browser-use ধাঁচের এজেন্টিক ব্রাউজ অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| e2b_adapter.py | backend/integrations/e2b_adapter.py | E2B ধাঁচের সিকিউর কোড-এক্সিকিউশন স্যান্ডবক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| graphiti_adapter.py | backend/integrations/graphiti_adapter.py | Graphiti ধাঁচের টেম্পোরাল নলেজ-গ্রাফ মেমরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mem0_adapter.py | backend/integrations/mem0_adapter.py | mem0 ধাঁচের সেলফ-লার্নিং মেমরি অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| openhands_adapter.py | backend/integrations/openhands_adapter.py | OpenHands ধাঁচের অটোনোমাস কোডিং-এজেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| issues_summary.md | backend/issues_summary.md | Render লগের সমস্যা-সারাংশ ইনসিডেন্ট ডক | render-issues.md | backend/docs/incidents/ | ইনসিডেন্ট ডক docs/-এ সরবে |
| __init__.py | backend/learning/__init__.py | কন্টিনিউয়াল লার্নিং প্যাকেজ ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| evidence_analyzer.py | backend/learning/evidence_analyzer.py | প্যাটার্ন যাচাইয়ের স্ট্যাটিস্টিক্যাল এভিডেন্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| evolution_bridge.py | backend/learning/evolution_bridge.py | LearningInsight → ChangeProposal ব্রিজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| experience.py | backend/learning/experience.py | এক্সপেরিয়েন্স লেজার/রেকর্ড প্রিমিটিভ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| hypothesis_engine.py | backend/learning/hypothesis_engine.py | ইমপ্রুভমেন্ট হাইপোথিসিস ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| outcome_analyzer.py | backend/learning/outcome_analyzer.py | টাস্ক-আউটকাম শ্রেণিবিন্যাস + ইনসাইট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pattern_detector.py | backend/learning/pattern_detector.py | ক্যানোনিকাল ট্যাক্সোনমি প্যাটার্ন ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; recognizer-এর সাথে ওভারল্যাপ ঝুঁকি |
| pattern_recognizer.py | backend/learning/pattern_recognizer.py | সিকোয়েন্স/টেম্পোরাল/সেমান্টিক প্যাটার্ন রিকগনিশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| main.py | backend/main.py | ENV বুটস্ট্র্যাপ + সিগন্যাল + uvicorn লঞ্চ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিকাল এন্ট্রি-পয়েন্ট |
| __init__.py | backend/middleware/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| anti_hacking.py | backend/middleware/anti_hacking.py | কনটেক্সট-সচেতন অ্যান্টি-হ্যাক চেক (অ্যালার্ট-অনলি) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| chaos_injector.py | backend/middleware/chaos_injector.py | লোকাল কেয়াস ডিলে/ড্রপ ইনজেক্টর মিডলওয়্যার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cors_policy.py | backend/middleware/cors_policy.py | পোর্টাল-ভিত্তিক CORS অরিজিন রেজলভার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| idempotency.py | backend/middleware/idempotency.py | idempotency_middleware রি-এক্সপোর্ট shim | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ৫-লাইনের re-export shim — ডিলিট প্রস্তাব |
| idempotency_middleware.py | backend/middleware/idempotency_middleware.py | Redis-ভিত্তিক আইডেম্পোটেন্সি মিডলওয়্যার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rate_limiter.py | backend/middleware/rate_limiter.py | Redis + in-memory স্লাইডিং-উইন্ডো লিমিটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | রিয়েল ইমপ্ল; core-এ shim আছে |
| tenant_rate_limiter.py | backend/middleware/tenant_rate_limiter.py | Upstash/Redis টেন্যান্ট রেট-লিমিট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/models/__init__.py | মডেল প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| admin.py | backend/models/admin.py | অ্যাডমিন অথেন্টিকেশন Pydantic স্কিমা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_session.py | backend/models/agent_session.py | AgentSession ORM মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ai_memory.py | backend/models/ai_memory.py | pgvector AIMemory ORM (HNSW ইনডেক্স) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| analytics.py | backend/models/analytics.py | AutoReport/ChurnPrediction/RetentionAction ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| api_key.py | backend/models/api_key.py | API-key DAO — raw asyncpg অ্যাক্সেস লেয়ার | api_key_repository.py | backend/repositories/ | models/ নয় — DAO repositories/-এ যাবে |
| automation_execution.py | backend/models/automation_execution.py | AutomationExecution + Attempt ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| base.py | backend/models/base.py | DeclarativeBase + টাইমস্ট্যাম্প/সফট-ডিলিট মিক্সিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| byoc_payloads.py | backend/models/byoc_payloads.py | BYOC ক্রেডেনশিয়াল/ডিপ্লয় Pydantic পেলোড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ci_report.py | backend/models/ci_report.py | CIReport Pydantic পেলোড + asyncpg DAO মিশ্রিত | ci_report_repository.py | backend/repositories/ | DAO+মডেল মিশ্রণ — repositories/-এ |
| deployment_logs.py | backend/models/deployment_logs.py | DeploymentJob BaseModel | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| dynamic_agent.py | backend/models/dynamic_agent.py | AI-জেনারেটেড এজেন্ট রেজিস্ট্রি ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| error_remediation.py | backend/models/error_remediation.py | রিট্রাই+সার্কিট-ব্রেকার ডেমো (__main__ সহ) | retry_circuit_breaker_demo.py | backend/examples/ | ⚠️ নাম বড় দাবি; বাস্তবে টিউটোরিয়াল ডেমো |
| evolution.py | backend/models/evolution.py | SkillFitness/CodeProposal/পারফ-মেট্রিক ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| execution_log.py | backend/models/execution_log.py | মাসিক-পার্টিশনড ExecutionLog ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| execution_policy.py | backend/models/execution_policy.py | ExecutionPolicy ORM মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| handoff_event.py | backend/models/handoff_event.py | HandoffEvent ORM মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| integration.py | backend/models/integration.py | Integration ORM মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| local_model_handler.py | backend/models/local_model_handler.py | Ollama/HF লোকাল ইনফারেন্স হ্যান্ডলার সার্ভিস | অপরিবর্তিত ✅ | backend/services/ | সার্ভিস-শ্রেণি; models/ নয় |
| localization.py | backend/models/localization.py | TranslationCache/VoiceSession ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| meta_ai.py | backend/models/meta_ai.py | AgentGenome/Offspring/ব্রিডিং ORM (সেলফ-ইভোলিউশন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম কনটেন্টের সাথে মেলে |
| morphic.py | backend/models/morphic.py | AgentReflection/DynamicCapability/Chain ORM | agent_reflections.py | অপরিবর্তিত ✅ | ⚠️ "morphic" অস্পষ্ট; বাস্তবে রিফ্লেকশন-মেমরি |
| patch_telemetry.py | backend/models/patch_telemetry.py | অটো-প্যাচ Accept/Reject ফিডব্যাক ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pending_tasks.py | backend/models/pending_tasks.py | PendingTask মডেল + SQLite approval-state DAO | অপরিবর্তিত ✅ | backend/repositories/ | স্টোর+স্টেট-মেশিন — repositories/-এ |
| plugin_manifest.py | backend/models/plugin_manifest.py | PluginManifest ORM মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| selector_healing_event.py | backend/models/selector_healing_event.py | SelectorHealingEvent ORM মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sentinel.py | backend/models/sentinel.py | ডিপেন্ডেন্সি/এন্ডপয়েন্ট/ইনসিডেন্ট ট্র্যাকিং ORM | dependency_vulnerability.py | অপরিবর্তিত ✅ | ⚠️ "sentinel" বাস্তবে ভালনারেবিলিটি ট্র্যাকার |
| shared_workspace.py | backend/models/shared_workspace.py | SharedWorkspace BaseModel | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| system_alert.py | backend/models/system_alert.py | SystemAlert ORM মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| system_config.py | backend/models/system_config.py | key-value SystemConfig ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| target_platform_credential.py | backend/models/target_platform_credential.py | টার্গেট-প্ল্যাটফর্ম ক্রেডেনশিয়াল ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| transaction_ledger.py | backend/models/transaction_ledger.py | wallet.py-র TransactionLedgerEntry-র ডুপ্লিকেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ইমপোর্টার-শূন্য ডুপ্লিকেট — ডিলিট প্রস্তাব |
| user_plugin_installation.py | backend/models/user_plugin_installation.py | UserPluginInstallation ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| voice_interaction.py | backend/models/voice_interaction.py | ভয়েস ইন্টারঅ্যাকশন লগ BaseModel | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| wallet.py | backend/models/wallet.py | UserWallet + TransactionLedgerEntry ORM | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/monitoring/__init__.py | init_observability + track_exception ইঞ্জিন কোড | observability.py (এক্সট্র্যাক্ট) | অপরিবর্তিত ✅ | __init__-এ ৮৫-লাইন ইঞ্জিন — আলাদা মডিউল |
| behavioral_guard.py | backend/monitoring/behavioral_guard.py | এজেন্ট বিহেভিয়ারাল অ্যানোমালি ডিটেকশন গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| causal_debugger.py | backend/monitoring/causal_debugger.py | ট্রেসব্যাক পার্স করে রুট-কজ/রেমিডিয়েশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| log_batcher.py | backend/monitoring/log_batcher.py | ব্যাচড অ্যাসিঙ্ক লগ সিঙ্ক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| logging.py | backend/monitoring/logging.py | loguru get_logger পাতলা র‍্যাপার (১৬ লাইন) | logging_config.py-এ মার্জ | অপরিবর্তিত ✅ | লগিং জোড়া এক মডিউলে একত্রীকরণ |
| logging_config.py | backend/monitoring/logging_config.py | স্ট্রাকচার্ড লগিং + করিলেশন-ID সেটআপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| metrics.py | backend/monitoring/metrics.py | counter/timed মেট্রিক ডেকোরেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| metrics_collector.py | backend/monitoring/metrics_collector.py | কম্প্রিহেনসিভ অ্যাপ/সিস্টেম মেট্রিক্স কালেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| openapi.json | backend/openapi.json | জেনারেটেড OpenAPI স্পেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড আর্টিফ্যাক্ট |
| __init__.py | backend/p2p/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| credit_system.py | backend/p2p/credit_system.py | মক CreditLedger + ResourceBroker ডুপ্লিকেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ফাঁকা স্টাব; ডুপ্লিকেট ক্লাস — ডিলিট |
| resource_broker.py | backend/p2p/resource_broker.py | P2P রিসোর্স ম্যাচমেকিং/জিরো-ট্রাস্ট ব্রোকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| secure_tunnel.py | backend/p2p/secure_tunnel.py | ৯-লাইনের মক টানেল স্টাব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | মক স্টাব, বাস্তব ইমপ্ল নেই — ডিলিট |
| __init__.py | backend/pipelines/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| code_to_db_sync.py | backend/pipelines/code_to_db_sync.py | কোড-টু-DB আউটবক্স সিঙ্ক ডেমন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| synthetic_data_pipeline.py | backend/pipelines/synthetic_data_pipeline.py | EpisodicMemory থেকে ফাইন-টিউন JSONL এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| poetry.lock | backend/poetry.lock | Poetry লকফাইল (অটো-জেনারেটেড) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড; রিনেম অনুচিত |
| __init__.py | backend/pyerrorfix/__init__.py | pyerrorfix প্যাকেজ ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __main__.py | backend/pyerrorfix/__main__.py | python -m pyerrorfix এন্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনভেনশন-নাম |
| cli.py | backend/pyerrorfix/cli.py | argparse CLI — analyze/catalog কমান্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/pyerrorfix/core/__init__.py | কোর এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| catalog.py | backend/pyerrorfix/core/catalog.py | ১১০৭-লাইন এরর ট্যাক্সোনমি ক্যাটালগ (data) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| issue.py | backend/pyerrorfix/core/issue.py | Issue/Severity/Category/ScanResult কনট্র্যাক্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| reporter.py | backend/pyerrorfix/core/reporter.py | console/JSON/SARIF/Markdown রিপোর্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| scanner.py | backend/pyerrorfix/core/scanner.py | ডিটেক্টর+ফিক্সার অর্কেস্ট্রেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/pyerrorfix/detectors/__init__.py | ডিটেক্টর এক্সপোর্ট + রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| asyncio_err.py | backend/pyerrorfix/detectors/asyncio_err.py | never-awaited/cancel-error ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | _err সাফিক্স stdlib-সংঘর্ষ এড়ায় |
| auth_security.py | backend/pyerrorfix/detectors/auth_security.py | JWT/auth ভুল ব্যবহার ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| base.py | backend/pyerrorfix/detectors/base.py | BaseDetector AST ভিজিটর + হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| concurrency.py | backend/pyerrorfix/detectors/concurrency.py | শেয়ার্ড-মিউটেবল-স্টেট ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| core_python.py | backend/pyerrorfix/detectors/core_python.py | NameError/UnboundLocal/None-অ্যাক্সেস ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| database.py | backend/pyerrorfix/detectors/database.py | SQLAlchemy/ORM ভুল-ব্যবহার ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| deprecation.py | backend/pyerrorfix/detectors/deprecation.py | imp./distutils ইত্যাদি ডিপ্রিকেটেড API ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| files.py | backend/pyerrorfix/detectors/files.py | FileNotFoundError/Permission হিউরিস্টিক ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| imports.py | backend/pyerrorfix/detectors/imports.py | missing/circular import ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| infra_deploy.py | backend/pyerrorfix/detectors/infra_deploy.py | Dockerfile/gunicorn/uvicorn কনফিগ ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| linter_quality.py | backend/pyerrorfix/detectors/linter_quality.py | B905/naming সহ linter-স্টাইল ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| logging_err.py | backend/pyerrorfix/detectors/logging_err.py | f-string লগিং/broad-except ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| network_io.py | backend/pyerrorfix/detectors/network_io.py | socket/subprocess I/O হিউরিস্টিক ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| resources.py | backend/pyerrorfix/detectors/resources.py | রিসোর্স-লিক (open/socket) ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| security.py | backend/pyerrorfix/detectors/security.py | হার্ডকোডেড সিক্রেট/SQLi ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| syntax.py | backend/pyerrorfix/detectors/syntax.py | compile()-ভিত্তিক Syntax/Indentation ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| testing.py | backend/pyerrorfix/detectors/testing.py | assert-in-prod/টেস্ট-স্মেল ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| typing_err.py | backend/pyerrorfix/detectors/typing_err.py | Optional-অ্যাক্সেস টাইপিং ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| web_api.py | backend/pyerrorfix/detectors/web_api.py | FastAPI/Pydantic ভুল-ব্যবহার ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/pyerrorfix/fixers/__init__.py | ফিক্সার রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| await_fixer.py | backend/pyerrorfix/fixers/await_fixer.py | মিসিং await যোগ করার ফিক্সার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| base.py | backend/pyerrorfix/fixers/base.py | BaseFixer + রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| except_fixer.py | backend/pyerrorfix/fixers/except_fixer.py | bare except → Exception ফিক্সার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| fstring_log_fixer.py | backend/pyerrorfix/fixers/fstring_log_fixer.py | f-string লগ → lazy %s ফিক্সার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| import_fixer.py | backend/pyerrorfix/fixers/import_fixer.py | unused-import রিমুভ + isort-lite | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| with_fixer.py | backend/pyerrorfix/fixers/with_fixer.py | bare open() → with-block ফিক্সার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pyerrorfix_config.py | backend/pyerrorfix/pyerrorfix_config.py | কনফিগ লোডার (rule→severity ম্যাপ) | config.py | অপরিবর্তিত ✅ | প্যাকেজ-স্টাটার (pyerrorfix.pyerrorfix_config) দূর |
| default.json | backend/pyerrorfix/rules/default.json | ডিফল্ট রুল এনেবল/সেভেরিটি সেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pyproject.toml | backend/pyproject.toml | Poetry ডিপেন্ডেন্সি + pytest/ruff কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/reports/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| chaos_report.md | backend/reports/chaos_report.md | জেনারেটেড কেয়াস-ইঞ্জিনিয়ারিং রিপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড আর্টিফ্যাক্ট |
| optimization_engine.py | backend/reports/optimization_engine.py | ৯-লাইনের মক স্টাব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ফাঁকা স্টাব; reports/-এ engine-নাম অর্থহীন — ডিলিট |
| __init__.py | backend/runtime/__init__.py | ক্যানোনিকাল রানটাইম প্যাকেজ ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| budget_guard.py | backend/runtime/budget_guard.py | হার্ড বাজেট এনফোর্সমেন্ট গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| planner.py | backend/runtime/planner.py | PlanStep/Plan + CanonicalPlanner | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| task_context.py | backend/runtime/task_context.py | টাস্ক কনটেক্সট + এক্সিকিউশন-ট্রেস ট্র্যাকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| task_executor.py | backend/runtime/task_executor.py | ক্যানোনিকাল টাস্ক এক্সিকিউটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| task_result.py | backend/runtime/task_result.py | TaskResult/ভেরিফিকেশন-সামারি অবজেক্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| task_runtime.py | backend/runtime/task_runtime.py | কন্ট্রোল-প্লেন অর্কেস্ট্রেটর (planner→executor) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/sandbox/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| docker_sandbox.py | backend/sandbox/docker_sandbox.py | Docker-ভিত্তিক কোড এক্সিকিউশন স্যান্ডবক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| file_isolation_gate.py | backend/sandbox/file_isolation_gate.py | আপলোড ফাইল আইসোলেটেড-রান + ক্লিনআপ গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/scaling/__init__.py | স্কেলিং প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| distributed_manager.py | backend/scaling/distributed_manager.py | মাল্টি-নোড ক্লাস্টার + অটোস্কেল ম্যানেজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/schemas/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| skill_index.py | backend/schemas/skill_index.py | অ্যাটমিক-রাইট SkillIndexManager (ফাইল ম্যানেজার) | skill_index_manager.py | backend/services/ | স্কিমা নয় — ম্যানেজার সার্ভিস |
| skill_manifest.py | backend/schemas/skill_manifest.py | SkillManifest গভর্নেন্স/পারমিশন Pydantic মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/scout/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| knowledge_extractor.py | backend/scout/knowledge_extractor.py | MiniLM এমবেডিং এক্সট্র্যাক্টর (পাতলা) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; graceful degradation আছে |
| web_crawler_agent.py | backend/scout/web_crawler_agent.py | ১৩-লাইনের ডোমেইন-গার্ড স্টাব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | খালি CrawlResult রিটার্ন — ডিলিট প্রস্তাব |
| seed_db_configs.py | backend/seed_db_configs.py | system_config টেবিলে ডিফল্ট কনফিগ সিড | seed_system_config.py | backend/scripts/ | স্ক্রিপ্ট scripts/-এ; নামে টেবিল স্পষ্ট হোক |
| __init__.py | backend/storage/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| asset_manager.py | backend/storage/asset_manager.py | Firebase-প্রাইমারি/Supabase-ব্যাকআপ অ্যাসেট স্টোর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| r2_storage_client.py | backend/storage/r2_storage_client.py | Cloudflare R2 প্রিসাইন্ড-URL ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_capabilities.py | backend/test_capabilities.py | ক্যাপাবিলিটি রেজলভার ম্যানুয়াল ভেরিফায়ার | verify_capabilities.py | backend/scripts/ | test_ নাম pytest-ভ্রান্তি ডেয়; স্ক্রিপ্ট |
| test_db.py | backend/test_db.py | SELECT 1 দিয়ে DB কানেক্টিভিটি চেক | check_db_connection.py | backend/scripts/ | test_ নাম ভ্রান্তিজনক; ম্যানুয়াল স্ক্রিপ্ট |
| update_md.py | backend/update_md.py | pytest ফলাফল থেকে coverage-প্ল্যান টেবিল আপডেট | update_coverage_md.py | backend/scripts/ | ওয়ান-অফ; Windows-পাথ নির্ভর স্ক্রিপ্ট |
| __init__.py | backend/utils/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| api_tracker.py | backend/utils/api_tracker.py | APICallRecord/APITracker ইউসেজ ট্র্যাকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| branding.py | backend/utils/branding.py | প্রোভাইডার/মডেল ID → SupremeAI ব্র্যান্ডেড নাম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| environment.py | backend/utils/environment.py | টেস্ট-এনভ ও অ্যাডমিন-অথরাইজেশন চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| firestore_helpers.py | backend/utils/firestore_helpers.py | কেন্দ্রীয় Firestore ক্লায়েন্ট ফ্যাক্টরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| http_client.py | backend/utils/http_client.py | শেয়ার্ড httpx ক্লায়েন্ট + safe_fetch/safe_api_call | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| json_helpers.py | backend/utils/json_helpers.py | MCP টুল-রেসপন্স JSON হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| platform_detect.py | backend/utils/platform_detect.py | Render/Vercel/Firebase/Local প্ল্যাটফর্ম ডিটেকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| text_helpers.py | backend/utils/text_helpers.py | markdown code-block স্ট্রিপার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| timestamps.py | backend/utils/timestamps.py | UTC now/iso/timestamp হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| uuid_gen.py | backend/utils/uuid_gen.py | UUIDv7 SQLAlchemy TypeDecorator + জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/verification/__init__.py | ভেরিফিকেশন প্যাকেজ ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| verifier.py | backend/verification/verifier.py | ডিটারমিনিস্টিক ভেরিফিকেশন ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | backend/workers/__init__.py | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| celery_app.py | backend/workers/celery_app.py | core থেকে celery_app রি-এক্সপোর্ট এন্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | Celery CLI কনভেনশন — প্রয়োজনীয় |
| chaos_worker.py | backend/workers/chaos_worker.py | নাইটলি সেলফ-টেস্ট কেয়াস অডিটর + ব্রেকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| command_center.py | backend/ws/command_center.py | /ws/command-center/health GET — শুধু হেলথ পিং | health.py | অপরিবর্তিত ✅ | ⚠️ ৮-লাইনের হেলথ রাউট; নাম অতিরঞ্জিত |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **ভাঙা Alembic চেইন:** `a1b2c3d4e5f6` রিভিশন-ID দুটি ফাইলে (add_automation_executions_table ও add_patch_telemetry_table) ডুপ্লিকেট — `alembic upgrade` এই দুই হেড আলাদা করতে পারবে না; এছাড়া ৫+ হাতে-লেখা placeholder-ID (f1a2b3c4d5e6, g2b3c4d5e6f7, h3i4j5k6l7m8, j9k0l1m2n3o4, k1l2m3n4o5p6) এবং versions/-এ নন-alembic `001_initial_schema.sql`।
- **দুটি সমান্তরাল মাইগ্রেশন সিস্টেম:** `database/migrations/*.sql` (হাতে-চালানো, নাম্বারিং গ্যাপ ১১–১৪) আলাদা `alembic_migrations/`-এর বিপরীতে — এক পাইপলাইনে একত্রীকরণ জরুরি; `schema_contract.yaml` + CI চেক ইতিমধ্যে drift-এর সমাধান দেখাচ্ছে।
- **দুটি Settings সিস্টেম:** `core/config.py` (main.py ব্যবহৃত) ও `config/settings.py` (core/factory.py ব্যবহৃত) — মার্জ না করলে কনফিগ-ড্রিফট অনিবার্য।
- **models/ প্যাকেজ ভূমিকা-মিশ্রণ:** ORM টেবিল + Pydantic পেলোড + raw-asyncpg DAO (api_key, ci_report, pending_tasks) + ইনফারেন্স সার্ভিস (local_model_handler) একসাথে — DAOগুলো `repositories/`-এ সরানো উচিত।
- **ডেড/স্টাব ক্লাস্টার (১১+ ফাইল):** p2p/credit_system, p2p/secure_tunnel, reports/optimization_engine, byoc/resource_manager, scout/web_crawler_agent, models/transaction_ledger (importer-শূন্য ডুপ্লিকেট), database/storage_client (importer-শূন্য), middleware/idempotency (shim), adaptive_engine/self_improving_agent (ARCHIVED), hardcoded_llm.json — সবই ডিলিট প্রার্থী।
- **শেখা-ডোমেইন বিভাজন:** `adaptive_engine/` ও `learning/` দুটি সমান্তরাল লার্নিং-স্ট্যাক; experience দুই জায়গায় (experience_db vs experience.py), pattern_detector বনাম pattern_recognizer ওভারল্যাপ — একত্রীকরণ বা সীমানা-ডকুমেন্টেশন দরকার।
- **স্টোরেজ ত্রিমূর্তি:** database/storage_client.py (অব্যবহৃত), storage/asset_manager.py, storage/r2_storage_client.py — এক storage ডোমেইনে মার্জ করুন; রুটের test_*.py দুটি pytest-কালেকশন ঝুঁকি তৈরি করে।
- **সেমান্টিক-মিসম্যাচ হটস্পট:** admin/god.py, models/sentinel.py, models/morphic.py, ws/command_center.py, tier_s_features.py — সাই-ফাই/অতিরঞ্জিত নামের নিচে সাধারণ CRUD/গার্ড/হেলথ কোড।


---

## ব্যাচ ০৯ — Frontend Components ও Stories
**ব্যাচ:** 09 | **তালিকাভুক্ত:** 210 | **বিশ্লেষিত:** 210 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 60 | **স্থানান্তর প্রস্তাব:** 10 | **⚠️ সেমান্টিক মিসম্যাচ:** 12

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| BanglaHint.test.tsx | frontend/src/components/BanglaHint.test.tsx | BanglaHint টুলটিপের vitest ইউনিট টেস্ট | অপরিবর্তিত ✅ | frontend/src/components/ui/ | শেয়ার্ড UI—BanglaHint-এর সাথে ui/-এ সরুন |
| BanglaHint.tsx | frontend/src/components/BanglaHint.tsx | বাংলা টুলটিপসহ হেল্প আইকন বাটন (শেয়ার্ড UI) | অপরিবর্তিত ✅ | frontend/src/components/ui/ | শেয়ার্ড লিফ UI—ui/ ডিরেক্টরিতে থাকা উচিত |
| DashboardErrorBoundary.tsx | frontend/src/components/DashboardErrorBoundary.tsx | সাধারণ error boundary ফলব্যাকসহ—কোথাও ইমপোর্ট নেই | মুছে ফেলুন ❌ | — | admin/DashboardErrorBoundary-ই ব্যবহৃত, এটি ডেড কপি |
| ErrorBoundary.tsx | frontend/src/components/ErrorBoundary.tsx | error boundary + useErrorHandler হুক—অব্যবহৃত | মুছে ফেলুন/একীভূত ❌ | — | GlobalErrorBoundary অ্যাপে ব্যবহৃত; দ্বৈত boundary অপ্রয়োজনীয় |
| FixPreviewModal.tsx | frontend/src/components/FixPreviewModal.tsx | SelfHealer প্রস্তাবিত ফিক্সের diff প্রিভিউ মোডাল—অব্যবহৃত | অপরিবর্তিত ✅ | frontend/src/components/admin/ | OneClickPatch-এর সঙ্গী—admin ফিচারের সাথে রাখুন |
| GlobalErrorBoundary.tsx | frontend/src/components/GlobalErrorBoundary.tsx | অ্যাপ-লেভেল boundary, টেলিমেট্রি এন্ডপয়েন্টে এরর রিপোর্ট করে | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (main.tsx-এ ব্যবহৃত) |
| Header.tsx | frontend/src/components/Header.tsx | লিগ্যাসি ব্র্যান্ডিং হেডার (SUPREMEAI লোগো)—কোনো ইমপোর্ট নেই | মুছে ফেলুন ❌ | — | core/Header-ই ক্যানোনিক্যাল; এটি ডেড ডুপ্লিকেট |
| LiveSujonBackground.tsx | frontend/src/components/LiveSujonBackground.tsx | agent-state অনুযায়ী WebGL2 শেডার ব্যাকগ্রাউন্ড—অব্যবহৃত | মুছে ফেলুন ❌ | — | ⚠️ ব্যক্তিনাম "Sujon" টেক-শব্দ; ফাইলটিই আর ইমপোর্ট হয় না |
| OnboardingWizard.tsx | frontend/src/components/Onboarding/OnboardingWizard.tsx | ৩-স্টেপ onboarding উইজার্ড (API key→মডেল→প্রথম চ্যাট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| StepApiKey.tsx | frontend/src/components/Onboarding/StepApiKey.tsx | উইজার্ড স্টেপ ১—OpenRouter API key ইনপুট ফর্ম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| StepFirstChat.tsx | frontend/src/components/Onboarding/StepFirstChat.tsx | উইজার্ড স্টেপ ৩—প্রথম প্রম্পট নিয়ে /studio-তে পাঠায় | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| StepModelSelect.tsx | frontend/src/components/Onboarding/StepModelSelect.tsx | উইজার্ড স্টেপ ২—ডিফল্ট মডেল কার্ড সিলেকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| OperatorStudio.tsx | frontend/src/components/OperatorStudio.tsx | প্রিসেট/ফিড ট্যাব + CodeEditor + ChatPanel কম্পোজিশন—অব্যবহৃত | মুছে ফেলুন ❌ | — | কোনো পেজ ইমপোর্ট করে না; AIStudio এখন মূল পথ |
| SupremeComponents.tsx | frontend/src/components/SupremeComponents.tsx | SupremeCard/Button/Header মাল্টি-এক্সপোর্ট—ui/ এর ডুপ্লিকেট, অব্যবহৃত | মুছে ফেলুন/স্প্লিট ❌ | — | ⚠️ ব্র্যান্ড-উপসর্গ কম্পোনেন্ট ui/Button, ui/Card-এর প্রতিলিপি |
| SwarmMap.tsx | frontend/src/components/SwarmMap.tsx | ReactFlow-এ লাইভ swarm গ্রাফ ভিজ্যুয়ালাইজেশন (App-এ lazy) | অপরিবর্তিত ✅ | frontend/src/components/swarm/ | swarm/HoldToKillButton, SwarmHealthDashboard-এর পাশে থাকুক |
| AdminAlertsTab.tsx | frontend/src/components/admin/AdminAlertsTab.tsx | /admin-api/events থেকে সিস্টেম অ্যালার্ট লিস্ট ও resolve | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AdminConsole.tsx | frontend/src/components/admin/AdminConsole.tsx | admin লগইন/authenticated ভিউ সুইচার (৫০+ props ড্রিল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; props-drilling রিফ্যাক্টর আলাদা কাজ |
| AdminDashboardHome.tsx | frontend/src/components/admin/AdminDashboardHome.tsx | admin হোম গ্রিড—লাইভ মেট্রিক্স/হেলথ/CI উইজেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AethelCoreStyles.css | frontend/src/components/admin/AethelCoreStyles.css | sci-fi গ্লাসমরফিজম/HUD CSS ক্লাস সেট | admin-hud.css | অপরিবর্তিত ✅ | ⚠️ "Aethel" বিমূর্ত সাই-ফাই শব্দ; কনটেন্ট সাধারণ HUD স্টাইল |
| AethelNode.tsx | frontend/src/components/admin/AethelNode.tsx | ReactFlow-এর কাস্টম glow/tooltip ফ্লো-নোড | SciFiFlowNode.tsx | অপরিবর্তিত ✅ | ⚠️ "Aethel" নামে কোনো অর্থ নেই; CSS ক্লাসের সাথে রিনেম করুন |
| AuditLogsPanel.tsx | frontend/src/components/admin/AuditLogsPanel.tsx | /admin-api/audit-logs প্যানেল—ফিল্টারযোগ্য অডিট এন্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| BackupRestore.tsx | frontend/src/components/admin/BackupRestore.tsx | ব্যাকআপ তালিকা, ম্যানুয়াল ব্যাকআপ ট্রিগার, মেইনটেনেন্স মোড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CICDVisualizer.tsx | frontend/src/components/admin/CICDVisualizer.tsx | ফিচার-ফ্ল্যাগ টগল + CI গেট স্ট্যাটাস + CIDashboard লিংক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম মোটামুটি ঠিক; ভিতরে ফিচার-ফ্ল্যাগ অংশও আছে |
| CommandCenter.tsx | frontend/src/components/admin/CommandCenter.tsx | ReactFlow টপোলজি ম্যাপ + চ্যাট + টার্মিনাল + ভয়েস (৫২৩ লাইন) | TopologyCockpit.tsx | অপরিবর্তিত ✅ | ⚠️ "CommandCenter" বিমূর্ত; admin/Dashboard-এর হেডিংও Command Center—বিভ্রান্তিকর |
| ConfigEditor.tsx | frontend/src/components/admin/ConfigEditor.tsx | /admin-api/config KV এডিটর—draft মার্জ করে সেভ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CostAuditor.tsx | frontend/src/components/admin/CostAuditor.tsx | বাজেট/খরচ ব্রেকডাউন + ৮০% বাজেট অ্যালার্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Dashboard.tsx | frontend/src/components/admin/Dashboard.tsx | admin ওভারভিউ KPI পেজ—হেডিং "Command Center" | AdminOverview.tsx | অপরিবর্তিত ✅ | জেনেরিক "Dashboard" নাম AdminDashboardHome-এর সাথে দ্ব্যর্থক |
| DashboardErrorBoundary.tsx | frontend/src/components/admin/DashboardErrorBoundary.tsx | sci-fi ফলব্যাকসহ admin error boundary (অভ্যন্তরীণ নাম ErrorBoundary) | AdminErrorBoundary.tsx | অপরিবর্তিত ✅ | ফাইলনাম এক্সপোর্টেড কম্পোনেন্টের সাথে মেলে না |
| EnhancedSkillMarketplace.tsx | frontend/src/components/admin/EnhancedSkillMarketplace.tsx | স্কিল সার্চ/ইনস্টল মার্কেটপ্লেস + SkillGraph | SkillMarketplace.tsx | অপরিবর্তিত ✅ | "Enhanced" উপসর্গ অর্থহীন—ভার্সন-তাগ নাম নয় |
| GitHubCIWidget.tsx | frontend/src/components/admin/GitHubCIWidget.tsx | GitHub CI pipeline রান স্ট্যাটাস উইজেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| GithubIntegration.tsx | frontend/src/components/admin/GithubIntegration.tsx | রিপো/কমিট ব্রাউজার—GitHub API কোয়েরি প্যানেল | GitHubIntegration.tsx | অপরিবর্তিত ✅ | ক্যাপিটালাইজেশন GitHubCIWidget-এর সাথে অসামঞ্জস্য |
| HealthBanner.tsx | frontend/src/components/admin/HealthBanner.tsx | degraded হলে পুরো-প্রস্থ সতর্ক ব্যানার দেখায় | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| HealthMap.tsx | frontend/src/components/admin/HealthMap.tsx | GCP/Railway/Render/Cloudflare প্রোভাইডার হেলথ গ্রিড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| HealthReportWidget.tsx | frontend/src/components/admin/HealthReportWidget.tsx | সার্ভিস-ভিত্তিক হেলথ/latency রিপোর্ট উইজেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| InteractiveChatTab.tsx | frontend/src/components/admin/InteractiveChatTab.tsx | টার্মিনাল+ব্রাউজার প্যানেলসহ ইউনিফাইড চ্যাট ট্যাব (৫০১ লাইন) | অপরিবর্তিত ✅ | frontend/src/components/chat/ | admin/ থাকলেও AIStudio (user) পেজ ব্যবহার করে |
| LibrarianQueue.tsx | frontend/src/components/admin/LibrarianQueue.tsx | librarian কোয়ারেন্টাইন স্কিল approve/reject কিউ | SkillQuarantineQueue.tsx | অপরিবর্তিত ✅ | "Librarian" মেটাফর অস্পষ্ট—স্কিল রিভিউ কিউ এটি |
| LiveLogs.tsx | frontend/src/components/admin/LiveLogs.tsx | web worker-এ ফিল্টার করা রিয়েল-টাইম লগ স্ট্রিম প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| MemoryBrowser.tsx | frontend/src/components/admin/MemoryBrowser.tsx | /api/memory/conversations RAG কনভার্সেশন ব্রাউজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ModelRouter.tsx | frontend/src/components/admin/ModelRouter.tsx | প্রোভাইডার স্ট্যাটাস + override/AB-test রাউটিং কন্ট্রোল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| OneClickPatch.tsx | frontend/src/components/admin/OneClickPatch.tsx | SelfHealer প্যাচ প্রস্তাব apply/reject কন্ট্রোল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| RealTimeMetricsPanel.tsx | frontend/src/components/admin/RealTimeMetricsPanel.tsx | recharts-এ RPS/p50/p95 লাইভ এরিয়া চার্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ScreencastViewer.tsx | frontend/src/components/admin/ScreencastViewer.tsx | WebSocket JPEG ফ্রেম + takeover ইনপুট ক্যানভাস ভিউয়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SystemUptimeWidget.tsx | frontend/src/components/admin/SystemUptimeWidget.tsx | render/frontend আপটাইম কাউন্টার উইজেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| VisualRulesBuilder.tsx | frontend/src/components/admin/VisualRulesBuilder.tsx | rules-engine নিয়ম CRUD + টেস্ট বিল্ডার (optimistic save) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AdminAuthenticated.tsx | frontend/src/components/admin/auth/AdminAuthenticated.tsx | admin sub-tab রাউটিং শেল (AuthenticatedView এক্সপোর্ট) | AuthenticatedView.tsx | অপরিবর্তিত ✅ | ফাইলনাম এক্সপোর্ট AuthenticatedView-এর সাথে অমিল |
| AdminLogin.tsx | frontend/src/components/admin/auth/AdminLogin.tsx | TOTP/OTP + lockout সহ admin লগইন (LoginView এক্সপোর্ট) | LoginView.tsx | অপরিবর্তিত ✅ | ফাইলনাম এক্সপোর্ট LoginView-এর সাথে অমিল |
| ConsentMatrixModal.tsx | frontend/src/components/admin/auth/ConsentMatrixModal.tsx | HITL ক্রিটিক্যাল অ্যাকশন অনুমোদন মোডাল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| UserManager.tsx | frontend/src/components/admin/auth/UserManager.tsx | admin ইউজার CRUD + pagination (react-query) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CIDashboard.tsx | frontend/src/components/admin/ci/CIDashboard.tsx | WebSocket CI ড্যাশবোর্ড, ট্রেন্ড/স্কোর/এক্সপোর্ট (১২৭২ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ভেতরের Badge/EmptyState ui/ ডুপ্লিকেট—স্প্লিট করুন |
| utils.ts | frontend/src/components/admin/ci/utils.ts | convertToCSV—শুধু একটি CSV হেল্পার | csv.ts | অপরিবর্তিত ✅ | জেনেরিক "utils" নাম—কনটেন্ট অনুযায়ী নাম দিন |
| CrownJewelBrowser.tsx | frontend/src/components/admin/data/CrownJewelBrowser.tsx | ট্যাব/বুকমার্ক/হিস্টরিসহ এমবেডেড AI ব্রাউজার (১১৬৮ লাইন) | AdminBrowserPanel.tsx | frontend/src/components/admin/ | ⚠️ "CrownJewel" বিমূর্ত; কনটেন্ট সাধারণ ব্রাউজার; data/ ফোল্ডারও ভুল |
| index.ts | frontend/src/components/admin/index.ts | admin কম্পোনেন্ট ব্যারেল এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CloudOrchestrator.tsx | frontend/src/components/admin/infra/CloudOrchestrator.tsx | ক্লাউড প্রোভাইডার হেলথ+মেট্রিক্স কার্ড গ্রিড | CloudProviderHealth.tsx | অপরিবর্তিত ✅ | ⚠️ "Orchestrator" অতিরঞ্জিত—কনটেন্ট শুধু হেলথ/মেট্রিক্স ভিউ |
| DeploymentModal.tsx | frontend/src/components/admin/infra/DeploymentModal.tsx | ডিপ্লয় টার্গেট/স্ট্যাটাস/লগ মোডাল (mutation+polling) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ObservabilityDashboard.tsx | frontend/src/components/admin/infra/ObservabilityDashboard.tsx | latency/error চার্ট + অ্যালার্ট—ডেটা হার্ডকোডেড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; মক ডেটা লাইভ API দিয়ে বদলাতে হবে |
| ServiceHealthMetrics.tsx | frontend/src/components/admin/infra/ServiceHealthMetrics.tsx | জাভা ওয়ার্কার হেলথ মেট্রিক্স + ১৮-ট্যাব কুইক নেভ | WorkerMetricsPanel.tsx | অপরিবর্তিত ✅ | জেনেরিক নাম—আসল কাজ worker মেট্রিক্স+নেভিগেশন |
| ServiceHealthMonitor.tsx | frontend/src/components/admin/infra/ServiceHealthMonitor.tsx | সার্ভিস রেজিস্ট্রিসহ বিস্তৃত হেলথ মনিটর (৬৬৪ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| RateLimitManager.tsx | frontend/src/components/admin/security/RateLimitManager.tsx | টেন্যান্ট rate-limit/billing-tier এডিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| RulesEnginePanel.tsx | frontend/src/components/admin/security/RulesEnginePanel.tsx | অটো-রিমিডিয়েশন/threshold নিয়ম স্লাইডার প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SecurityDashboard.tsx | frontend/src/components/admin/security/SecurityDashboard.tsx | security টাস্ক + মেমরি/জম্বি মেট্রিক্স ড্যাশবোর্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; কনটেন্ট runtime memory ফোকাসড |
| ThreatDetection.tsx | frontend/src/components/admin/security/ThreatDetection.tsx | security-scan ফাইন্ডিং সিভিউরিটি লিস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ActionCard.tsx | frontend/src/components/admin/shared/ActionCard.tsx | AI রেসপন্স (কোড/ইমেজ) রেন্ডার + save/preview/deploy অ্যাকশন | ChatActionCard.tsx | অপরিবর্তিত ✅ | ui/ActionCard-এর সাথে নামসংঘর্ষ—দুটি সম্পূর্ণ ভিন্ন |
| AdminSubTabContent.tsx | frontend/src/components/admin/shared/AdminSubTabContent.tsx | sub-tab id→কম্পোনেন্ট MODULE_MAP রাউটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AdminTopNav.tsx | frontend/src/components/admin/shared/AdminTopNav.tsx | লোগো/অপারেটর/স্ট্যাটাস টপ নেভিগেশন বার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| DynamicPanel.tsx | frontend/src/components/admin/shared/DynamicPanel.tsx | Threats/Observability/Costs সাইড প্যানেল রেন্ডারার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ArtifactsPanel.tsx | frontend/src/components/artifacts/ArtifactsPanel.tsx | HTML/React/SVG/mermaid আর্টিফ্যাক্ট ট্যাব প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| WaveformVisualizer.tsx | frontend/src/components/audio/WaveformVisualizer.tsx | AnalyserNode থেকে canvas অডিও ওয়েভফর্ম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ServiceHealthBar.tsx | frontend/src/components/auth/ServiceHealthBar.tsx | লগইন পেজের public সার্ভিস হেলথ স্ট্যাটাস বার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| BranchButton.tsx | frontend/src/components/branch/BranchButton.tsx | কনভার্সেশন ব্রাঞ্চ তৈরির ড্রপডাউন বাটন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ChatInterface.tsx | frontend/src/components/chat/ChatInterface.tsx | মূল এজেন্ট চ্যাট—voice/artifacts/share/search ইন্টিগ্রেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ImageUploadButton.tsx | frontend/src/components/chat/ImageUploadButton.tsx | ২০MB-লিমিট চ্যাট ইমেজ আপলোড বাটন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| TypingIndicator.tsx | frontend/src/components/chat/TypingIndicator.tsx | "চিন্তা করছে" টাইপিং ডট অ্যানিমেশন বাবল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| UnifiedChatBubble.tsx | frontend/src/components/chat/UnifiedChatBubble.tsx | user/system চ্যাট বাবল + action বাটন পার্সার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| index.ts | frontend/src/components/chat/index.ts | chat কম্পোনেন্ট ব্যারেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SlashCommandMenu.tsx | frontend/src/components/commands/SlashCommandMenu.tsx | /-কমান্ড অটোকমপ্লিট মেনু (ক্যাটাগরি+আইকন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Skeleton.test.tsx | frontend/src/components/common/Skeleton.test.tsx | common/Skeleton টেস্ট—কম্পোনেন্টটি অব্যবহৃত | মুছে ফেলুন ❌ | — | কম্পোনেন্ট কেউ ইমপোর্ট করে না; ui/Skeleton ক্যানোনিক্যাল |
| Skeleton.tsx | frontend/src/components/common/Skeleton.tsx | Skeleton+WorkspaceSkeleton—ui/Skeleton-এর ডুপ্লিকেট | মুছে ফেলুন/একীভূত ❌ | — | ৩টি স্কেলিটন ইমপ্লিমেন্টেশনের একটি; ui/-তে একীভূত করুন |
| AuthGuards.tsx | frontend/src/components/core/AuthGuards.tsx | ProtectedRoute/GuestRoute রাউট গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| GlobalConfigInitializer.tsx | frontend/src/components/core/GlobalConfigInitializer.tsx | স্টার্টআপে public config ফেচ+ডেডলাইন ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Header.test.tsx | frontend/src/components/core/Header.test.tsx | core/Header-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Header.tsx | frontend/src/components/core/Header.tsx | সার্চ/থিম/রোল-টগলসহ ওয়ার্কস্পেস হেডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; শুধু অব্যবহৃত dashboard/DashboardLayout ব্যবহার করে |
| Sidebar.tsx | frontend/src/components/core/Sidebar.tsx | ৭-আইটেম নেভ সাইডবার (ওয়ার্কস্পেস লিংক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ব্যবহারকারী dashboard/DashboardLayout-ও অব্যবহৃত |
| BrowserPreview.tsx | frontend/src/components/customer/BrowserPreview.tsx | CORS-প্রক্সিড ডিভাইস ভিউপোর্ট প্রিভিউ (desktop/tablet/mobile) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ChatPanel.test.tsx | frontend/src/components/customer/ChatPanel.test.tsx | ChatPanel-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ChatPanel.tsx | frontend/src/components/customer/ChatPanel.tsx | OperatorStudio-র সরু চ্যাট সাইড-প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CodeEditor.tsx | frontend/src/components/customer/CodeEditor.tsx | Monaco এডিটর + ভাষা সিলেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| HomeFeed.tsx | frontend/src/components/customer/HomeFeed.tsx | ডিফল্ট উইজেট ফিড (store-ভিত্তিক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| MobileSimulator.tsx | frontend/src/components/customer/MobileSimulator.tsx | iPhone/Pixel/iPad সিমুলেটর iframe (প্রক্সি URL) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| QuickPresets.test.tsx | frontend/src/components/customer/QuickPresets.test.tsx | QuickPresets-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| QuickPresets.tsx | frontend/src/components/customer/QuickPresets.tsx | ক্যাটাগরিভিত্তিক প্রম্পট প্রিসেট বাটন গ্রিড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| UserDashboard.test.tsx | frontend/src/components/customer/UserDashboard.test.tsx | UserDashboard-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| UserDashboard.tsx | frontend/src/components/customer/UserDashboard.tsx | গ্রিটিং + বেন্টো-গ্রিড ইউজার হোম পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| index.ts | frontend/src/components/customer/index.ts | customer কম্পোনেন্ট ব্যারেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ActionDock.tsx | frontend/src/components/dashboard/ActionDock.tsx | dnd-kit ড্র্যাগেবল বটম ইন্টিগ্রেশন ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; DynamicActionDock/LivingActionDock ডুপ্লিকেট ক্লাস্টার |
| AgentStatePill.tsx | frontend/src/components/dashboard/AgentStatePill.tsx | agent-state→রঙ/লেবেল স্ট্যাটাস পিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AutomationQueuePage.tsx | frontend/src/components/dashboard/AutomationQueuePage.tsx | /api/browser/tasks অটোমেশন কিউ তৈরি/মনিটর পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ConnectedPlatformsVault.tsx | frontend/src/components/dashboard/ConnectedPlatformsVault.tsx | প্ল্যাটফর্ম ক্রেডেনশিয়াল ভল্ট UI—হার্ডকোডেড মক ডেটা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ডেমো ডেটা লাইভ API-তে বদলাতে হবে |
| DashboardLayout.tsx | frontend/src/components/dashboard/DashboardLayout.tsx | core/Header+Sidebar র‍্যাপ করা লেআউট—অব্যবহৃত | মুছে ফেলুন ❌ | — | layout/DashboardLayout-এর নামসংঘর্ষ + কোনো ইমপোর্ট নেই |
| ExecutionShell.tsx | frontend/src/components/dashboard/ExecutionShell.tsx | ভার্চুয়ালাইজড ANSI এক্সিকিউশন লগ টার্মিনাল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| FileTreePanel.tsx | frontend/src/components/dashboard/FileTreePanel.tsx | সেশন ফাইল-ট্রি এক্সপান্ডেবল প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| GuardrailsPage.tsx | frontend/src/components/dashboard/GuardrailsPage.tsx | এক্সিকিউশন পলিসি (timeout/budget/retry) এডিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| HITLModal.tsx | frontend/src/components/dashboard/HITLModal.tsx | human-in-the-loop অ্যাকশন কনফার্মেশন মোডাল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Header.tsx | frontend/src/components/dashboard/Header.tsx | i18n সার্চ/ভাষা হেডার—কোনো ইমপোর্ট নেই | মুছে ফেলুন ❌ | — | তৃতীয় Header ডুপ্লিকেট; core/Header ক্যানোনিক্যাল |
| HealingLogPanel.tsx | frontend/src/components/dashboard/HealingLogPanel.tsx | selector-healing ইভেন্ট তালিকা + approve/reject | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| HumanInTheLoopProtocol.tsx | frontend/src/components/dashboard/HumanInTheLoopProtocol.tsx | ৭-স্টেপ OTP অনুমোদন প্রোটোকল উইজার্ড—অব্যবহৃত | মুছে ফেলুন ❌ | — | ⚠️ "Protocol" অতিরঞ্জিত; HITLModal-ই ব্যবহৃত বিকল্প |
| KnowledgePage.tsx | frontend/src/components/dashboard/KnowledgePage.tsx | /api/knowledge সার্চ+সিড পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LiveSimulator.tsx | frontend/src/components/dashboard/LiveSimulator.tsx | ইন্টিগ্রেশন DAG ট্রান্সফরমেশন SVG ম্যাপ (Magic Window) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LiveTelemetryChart.test.tsx | frontend/src/components/dashboard/LiveTelemetryChart.test.tsx | LiveTelemetryChart টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LiveTelemetryChart.tsx | frontend/src/components/dashboard/LiveTelemetryChart.tsx | throughput/latency এরিয়া চার্ট (SpotlightCard) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LivingActionDock.tsx | frontend/src/components/dashboard/LivingActionDock.tsx | dnd-kit droppable ইন্টিগ্রেশন টার্গেট + স্ট্যাটাস ভ্যারিয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; তিনটি dock-এর একটি—একীকরণ প্রয়োজন |
| LivingDashboardShell.tsx | frontend/src/components/dashboard/LivingDashboardShell.tsx | চ্যাট+Magic Window ড্যাশবোর্ড শেল (guest ব্যানারসহ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LlmGatewayPage.tsx | frontend/src/components/dashboard/LlmGatewayPage.tsx | LLM ফলব্যাক চেইন/মডেল সুইচ/রুল এডিটর পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| QuickActionsPanel.test.tsx | frontend/src/components/dashboard/QuickActionsPanel.test.tsx | QuickActionsPanel টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| QuickActionsPanel.tsx | frontend/src/components/dashboard/QuickActionsPanel.tsx | self-healer/forge/deploy কুইক অ্যাকশন কার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ReasoningLog.tsx | frontend/src/components/dashboard/ReasoningLog.tsx | কলাপ্সেবল agent reasoning চেইন প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SandboxViewport.tsx | frontend/src/components/dashboard/SandboxViewport.tsx | SSE screencast base64 ফ্রেম canvas রেন্ডারার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SecretsPage.tsx | frontend/src/components/dashboard/SecretsPage.tsx | API key তৈরি/রিভোক/ম্যাস্কড তালিকা পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SessionDetailPage.tsx | frontend/src/components/dashboard/SessionDetailPage.tsx | সেশন ককপিট—SSE কানেক্ট+ফাইলট্রি/শেল/রিজনিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SessionsPage.tsx | frontend/src/components/dashboard/SessionsPage.tsx | সেশন কম্পোজার+তালিকা (Devin-স্টাইল হোম) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SettingsPage.tsx | frontend/src/components/dashboard/SettingsPage.tsx | /api/preferences ইউজার প্রেফারেন্স এডিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Sidebar.tsx | frontend/src/components/dashboard/Sidebar.tsx | ৫-আইটেম নেভ সাইডবার—কোনো ইমপোর্ট নেই | মুছে ফেলুন ❌ | — | core/Sidebar-এর ডুপ্লিকেট; ব্যবহারের প্রমাণ নেই |
| SidebarSettings.tsx | frontend/src/components/dashboard/SidebarSettings.tsx | Sessions/Vault/Integrations সাইডবার ট্যাব প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SiteActionsPage.tsx | frontend/src/components/dashboard/SiteActionsPage.tsx | সাইট অ্যাকশন (selector/strategy) CRUD টেবিল পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SujonCoreCockpit.tsx | frontend/src/components/dashboard/SujonCoreCockpit.tsx | WebSocket লগ/শেল/ফাইল ককপিট—অব্যবহৃত | মুছে ফেলুন ❌ | — | ⚠️ "Sujon Core" বিমূর্ত; SessionDetailPage-ই ব্যবহৃত সমতুল্য |
| UsagePage.tsx | frontend/src/components/dashboard/UsagePage.tsx | /metrics/usage ইউসেজ চার্ট+টোটাল পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| VaultPage.tsx | frontend/src/components/dashboard/VaultPage.tsx | ব্রাউজার ক্রেডেনশিয়াল ভল্ট—oauth/cookie/manual ইমপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sessionStore.ts | frontend/src/components/dashboard/sessionStore.ts | সেশন CRUD—localStorage+API সিঙ্ক (নন-কম্পোনেন্ট) | session-store.ts | frontend/src/store/ | kebab-case নিয়ম + store ফোল্ডারে স্থানান্তর |
| useHashRoute.ts | frontend/src/components/dashboard/useHashRoute.ts | hash-ভিত্তিক লাইটওয়েট রাউটিং হুক | অপরিবর্তিত ✅ | frontend/src/hooks/ | হুক components/-এ নয়—hooks/ ডিরেক্টরিতে যাবে |
| DynamicActionDock.tsx | frontend/src/components/dock/DynamicActionDock.tsx | সাধারণ ইন্টিগ্রেশন টগল বাটন গ্রুপ—অব্যবহৃত | মুছে ফেলুন/একীভূত ❌ | — | ActionDock/LivingActionDock-ই ব্যবহৃত; এটি ডেড ভ্যারিয়েন্ট |
| AiAssistantBar.tsx | frontend/src/components/editor/AiAssistantBar.tsx | IDE কুইক অ্যাকশন টুলবার (explain/review/heal) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AiOutputPanel.tsx | frontend/src/components/editor/AiOutputPanel.tsx | AI অ্যাকশন আউটপুট মোডাল প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| EditorTabs.tsx | frontend/src/components/editor/EditorTabs.tsx | IDE ওপেন-ফাইল ট্যাব স্ট্রিপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| FileExplorer.tsx | frontend/src/components/editor/FileExplorer.tsx | WebContainer fs থেকে ফাইল-ট্রি ব্রাউজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| JitOtpDialogHost.tsx | frontend/src/components/editor/JitOtpDialogHost.tsx | JIT OTP prompt-এর React মোডাল হোস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| desktopPrompt.ts | frontend/src/components/editor/desktopPrompt.ts | prompt/confirm সিঙ্গেলটন DialogQueue (নন-কম্পোনেন্ট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | kebab-case ঠিক; JitOtpDialogHost-এর সাথে colocated |
| monacoAi.ts | frontend/src/components/editor/monacoAi.ts | Monaco inline-completion+context-menu AI সেটআপ | monaco-ai.ts | অপরিবর্তিত ✅ | নন-কম্পোনেন্ট TS ফাইল kebab-case হবে |
| ExportMenu.tsx | frontend/src/components/export/ExportMenu.tsx | md/pdf/word কনভার্সেশন এক্সপোর্ট ড্রপডাউন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SkillGraph.tsx | frontend/src/components/graph/SkillGraph.tsx | /api/v1/graph/skills ReactFlow সার্কুলার গ্রাফ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CommandBar.tsx | frontend/src/components/layout/CommandBar.tsx | ⌘K কমান্ড প্যালেট (Raycast-স্টাইল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| DashboardLayout.tsx | frontend/src/components/layout/DashboardLayout.tsx | header/sidebar স্লট লেআউট (AdminAuthenticated ব্যবহার করে) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিক্যাল লেআউট; dashboard/-এর ডুপ্লিকেটটি মুছুন |
| MainLayout.tsx | frontend/src/components/layout/MainLayout.tsx | pro-mode ব্রাউজার/টার্মিনাল শেল—অব্যবহৃত | মুছে ফেলুন ❌ | — | কোনো পেজ ইমপোর্ট করে না; WorkspaceLayout ব্যবহৃত |
| NavRail.test.tsx | frontend/src/components/layout/NavRail.test.tsx | NavRail টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| NavRail.tsx | frontend/src/components/layout/NavRail.tsx | হোভার-এক্সপ্যান্ড আইকন নেভ রেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Shell.tsx | frontend/src/components/layout/Shell.tsx | জেনেরিক sidebar/header শেল—কোনো ইমপোর্ট নেই | মুছে ফেলুন ❌ | — | অব্যবহৃত প্রিমিটিভ; দরকার হলে ui/-তে নিন |
| WorkspaceLayout.tsx | frontend/src/components/layout/WorkspaceLayout.tsx | NAV_GROUP সাইডবার+ডক+HITLModal মূল শেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| MemoryPanel.tsx | frontend/src/components/memory/MemoryPanel.tsx | fact/preference/instruction মেমরি CRUD+সার্চ (৪৮৭ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AgentNode.jsx | frontend/src/components/nodes/AgentNode.jsx | ReactFlow এজেন্ট নোড—health/latency ব্যাজ | AgentNode.tsx | অপরিবর্তিত ✅ | TS প্রজেক্টে .jsx নয়—টাইপসহ .tsx-এ কনভার্ট |
| SkillNode.jsx | frontend/src/components/nodes/SkillNode.jsx | ReactFlow স্কিল নোড (পিল-আকৃতি) | SkillNode.tsx | অপরিবর্তিত ✅ | TS প্রজেক্টে .jsx নয়—টাইপসহ .tsx-এ কনভার্ট |
| MCPConnector.tsx | frontend/src/components/plugins/MCPConnector.tsx | MCP সার্ভার discover ফর্ম—`Bearer` সিনট্যাক্স ত্রুটিযুক্ত | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | অ্যানোমালি: ফাইল কম্পাইলই হয় না—ফিক্স বা মুছুন |
| ThinkingPanel.tsx | frontend/src/components/reasoning/ThinkingPanel.tsx | রিজনিং স্টেপ+confidence স্কোর কলাপ্সেবল প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| DeepResearchPanel.tsx | frontend/src/components/research/DeepResearchPanel.tsx | মাল্টি-স্টেপ রিসার্চ রানার+রিপোর্ট+হিস্টরি (৬৪৮ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ScheduledTasksPanel.tsx | frontend/src/components/schedule/ScheduledTasksPanel.tsx | cron শিডিউল টাস্ক CRUD+এক্সিকিউশন হিস্টরি (৬৪৮ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ChatSearchDialog.tsx | frontend/src/components/search/ChatSearchDialog.tsx | কনভার্সেশন সার্চ ডায়ালগ—হাইলাইট+স্কোর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ShareDialog.tsx | frontend/src/components/share/ShareDialog.tsx | শেয়ার লিংক তৈরি—expiry/public অপশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LiveSimulator.tsx | frontend/src/components/simulator/LiveSimulator.tsx | প্লেসহোল্ডার "Visualization placeholder"—অব্যবহৃত | মুছে ফেলুন ❌ | — | dashboard/LiveSimulator-এর ডেড ডুপ্লিকেট |
| sujon-utils.ts | frontend/src/components/sujon-utils.ts | SujonState ইভেন্ট+WebGL শেডার সোর্স | agent-state-shaders.ts | frontend/src/lib/ | ⚠️ "sujon" ব্যক্তিনাম; আসলে state-event+GLSL ইউটিলিটি |
| index.tsx | frontend/src/components/sujon/index.tsx | useSujonMetrics হুক+SujonWidget (Sujon Core উইজেট) | SujonWidget.tsx | frontend/src/components/widgets/ | ⚠️ ব্যক্তিনাম-ভিত্তিক ফোল্ডার; widgets/ EvolutionForgeWidget-এর পাশে |
| HoldToKillButton.tsx | frontend/src/components/swarm/HoldToKillButton.tsx | ২-সেকেন্ড hold করে circuit-breaker ট্রিগার বাটন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম অদ্ভুত হলেও কাজ নির্ভুলভাবে বোঝায় |
| SwarmHealthDashboard.tsx | frontend/src/components/swarm/SwarmHealthDashboard.tsx | swarm মেট্রিক্স+সার্কিট-ব্রেকার কন্ট্রোল ড্যাশবোর্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| PromptTemplateLibrary.tsx | frontend/src/components/templates/PromptTemplateLibrary.tsx | প্রম্পট টেমপ্লেট CRUD+ভ্যারিয়েবল+বুকমার্ক (৬৬০ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ActionCard.test.tsx | frontend/src/components/ui/ActionCard.test.tsx | ui/ActionCard টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ActionCard.tsx | frontend/src/components/ui/ActionCard.tsx | আইকন+টাইটেল ক্লিকেবল অ্যাকশন কার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (admin কপিটি রিনেম হবে) |
| Badge.test.tsx | frontend/src/components/ui/Badge.test.tsx | Badge টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Badge.tsx | frontend/src/components/ui/Badge.tsx | ৬-ভ্যারিয়েন্ট স্ট্যাটাস ব্যাজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Breadcrumb.test.tsx | frontend/src/components/ui/Breadcrumb.test.tsx | Breadcrumb টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Breadcrumb.tsx | frontend/src/components/ui/Breadcrumb.tsx | crumb তালিকা নেভিগেশন (শেষ আইটেম active) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Button.stories.tsx | frontend/src/components/ui/Button.stories.tsx | Button-এর Storybook স্টোরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Button.test.tsx | frontend/src/components/ui/Button.test.tsx | Button টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Button.tsx | frontend/src/components/ui/Button.tsx | ৪-ভ্যারিয়েন্ট ফরওয়ার্ডেড বাটন (ডিজাইন টোকেন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Card.stories.tsx | frontend/src/components/ui/Card.stories.tsx | Card পরিবারের Storybook স্টোরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Card.test.tsx | frontend/src/components/ui/Card.test.tsx | Card সাব-কম্পোনেন্ট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Card.tsx | frontend/src/components/ui/Card.tsx | Card/Header/Title/Content কম্পোজেবল কার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| EmptyState.test.tsx | frontend/src/components/ui/EmptyState.test.tsx | EmptyState টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| EmptyState.tsx | frontend/src/components/ui/EmptyState.tsx | আইকন+CTA খালি-স্টেট কম্পোনেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Input.stories.tsx | frontend/src/components/ui/Input.stories.tsx | Input-এর Storybook স্টোরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Input.test.tsx | frontend/src/components/ui/Input.test.tsx | Input টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Input.tsx | frontend/src/components/ui/Input.tsx | label/error/helperText ফর্ম ইনপুট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| PageHeader.test.tsx | frontend/src/components/ui/PageHeader.test.tsx | PageHeader টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| PageHeader.tsx | frontend/src/components/ui/PageHeader.tsx | eyebrow+title+breadcrumb পেজ হিরো | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Skeleton.test.tsx | frontend/src/components/ui/Skeleton.test.tsx | ui/Skeleton টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Skeleton.tsx | frontend/src/components/ui/Skeleton.tsx | মিনিমাল pulse স্কেলিটন (ক্যানোনিক্যাল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত; common/-এর কপি মুছুন |
| SkeletonLoader.test.tsx | frontend/src/components/ui/SkeletonLoader.test.tsx | SkeletonLoader টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SkeletonLoader.tsx | frontend/src/components/ui/SkeletonLoader.tsx | শিমার-ইফেক্ট card/text/avatar স্কেলিটন | Skeleton.tsx-এ একীভূত | অপরিবর্তিত ✅ | তৃতীয় স্কেলিটন ইমপ্লিমেন্টেশন—ui/Skeleton-এ variant করুন |
| SpotlightCard.test.tsx | frontend/src/components/ui/SpotlightCard.test.tsx | SpotlightCard টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SpotlightCard.tsx | frontend/src/components/ui/SpotlightCard.tsx | মাউস-ফলো স্পটলাইট গ্লো কার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| StatCard.test.tsx | frontend/src/components/ui/StatCard.test.tsx | StatCard টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| StatCard.tsx | frontend/src/components/ui/StatCard.tsx | sparkline+delta স্ট্যাট কার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| index.test.tsx | frontend/src/components/ui/index.test.tsx | ব্যারেল এক্সপোর্ট সম্পূর্ণতা টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| index.ts | frontend/src/components/ui/index.ts | ui ব্যারেল—chat বাবল+BanglaHintও লিক করে | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ক্রস-ডোমেইন রি-এক্সপোর্ট পরিষ্কার করুন |
| EvolutionForgeWidget.tsx | frontend/src/components/widgets/EvolutionForgeWidget.tsx | নতুন স্কিল synthesis ফর্ম (budget চেকসহ) | SkillSynthesisWidget.tsx | অপরিবর্তিত ✅ | ⚠️ "Evolution Forge" সাই-ফাই ব্র্যান্ড—কনটেন্ট সাধারণ ফর্ম |
| Configure.mdx | frontend/src/stories/Configure.mdx | Storybook টেমপ্লেট ডক্স পেজ (স্টক) | মুছে ফেলুন ❌ | — | Storybook ডেমো টেমপ্লেট—প্রজেক্টের কোনো কাজে নেই |
| accessibility.png | frontend/src/stories/assets/accessibility.png | Storybook ডেমো অ্যাসেট (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| accessibility.svg | frontend/src/stories/assets/accessibility.svg | Storybook ডেমো অ্যাসেট (SVG) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| addon-library.png | frontend/src/stories/assets/addon-library.png | Storybook ডেমো অ্যাসেট (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| assets.png | frontend/src/stories/assets/assets.png | Storybook ডেমো অ্যাসেট (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| avif-test-image.avif | frontend/src/stories/assets/avif-test-image.avif | AVIF টেস্ট ইমেজ (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| context.png | frontend/src/stories/assets/context.png | Storybook ডেমো অ্যাসেট (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| discord.svg | frontend/src/stories/assets/discord.svg | Storybook ডেমো অ্যাসেট (SVG) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| docs.png | frontend/src/stories/assets/docs.png | Storybook ডেমো অ্যাসেট (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| figma-plugin.png | frontend/src/stories/assets/figma-plugin.png | Storybook ডেমো অ্যাসেট (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| github.svg | frontend/src/stories/assets/github.svg | Storybook ডেমো অ্যাসেট (SVG) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| share.png | frontend/src/stories/assets/share.png | Storybook ডেমো অ্যাসেট (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| styling.png | frontend/src/stories/assets/styling.png | Storybook ডেমো অ্যাসেট (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| testing.png | frontend/src/stories/assets/testing.png | Storybook ডেমো অ্যাসেট (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| theming.png | frontend/src/stories/assets/theming.png | Storybook ডেমো অ্যাসেট (বাইনারি) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| tutorials.svg | frontend/src/stories/assets/tutorials.svg | Storybook ডেমো অ্যাসেট (SVG) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| youtube.svg | frontend/src/stories/assets/youtube.svg | Storybook ডেমো অ্যাসেট (SVG) | মুছে ফেলুন ❌ | — | স্টক Storybook অ্যাসেট—অ্যাপে অব্যবহৃত |
| button.css | frontend/src/stories/button.css | Storybook ডেমো বাটন CSS (স্টক) | মুছে ফেলুন ❌ | — | Storybook টিউটোরিয়াল টেমপ্লেট—অব্যবহৃত |
| header.css | frontend/src/stories/header.css | Storybook ডেমো হেডার CSS (স্টক) | মুছে ফেলুন ❌ | — | Storybook টিউটোরিয়াল টেমপ্লেট—অব্যবহৃত |
| page.css | frontend/src/stories/page.css | Storybook ডেমো পেজ CSS (স্টক) | মুছে ফেলুন ❌ | — | Storybook টিউটোরিয়াল টেমপ্লেট—অব্যবহৃত |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **হেডার/সাইডবার/লেআউট ত্রিমুখী ডুপ্লিকেশন:** Header.tsx ×৩ (root/core/dashboard) ও Sidebar.tsx ×২ (core/dashboard) — শুধু core/ জোড়া ব্যবহৃত; root ও dashboard কপি + dashboard/DashboardLayout, layout/MainLayout, layout/Shell সম্পূর্ণ অব্যবহৃত — মুছে ফেলার প্রধান ক্যান্ডিডেট।
- **ট্রিপল-স্কেলিটন ও ডক ক্লাস্টার:** ui/Skeleton, common/Skeleton, ui/SkeletonLoader এবং ActionDock, dock/DynamicActionDock, dashboard/LivingActionDock — প্রতিটি ক্লাস্টারে ১টি ক্যানোনিক্যাল রেখে বাকিগুলো একীভূত/অপসারণ করুন।
- **নাম-এক্সপোর্ট অমিল:** admin/auth/AdminLogin→LoginView, AdminAuthenticated→AuthenticatedView, admin/DashboardErrorBoundary→(অভ্যন্তরীণ ErrorBoundary), admin/shared/ActionCard ↔ ui/ActionCard সংঘর্ষ — ফাইলনাম এক্সপোর্টের সাথে মেলান।
- **⚠️ সেমান্টিক মিসম্যাচ হটস্পট:** "Sujon" ব্যক্তিনাম (LiveSujonBackground, sujon-utils, sujon/, SujonCoreCockpit), "Aethel" (AethelNode, AethelCoreStyles.css), "CrownJewel" (আসলে একটি এমবেডেড ব্রাউজার), "CommandCenter" (admin/Dashboard.tsx-এর হেডিংও Command Center — দ্ব্যর্থক)।
- **স্টক Storybook টেমপ্লেট বয়ে যাচ্ছে:** stories/ ডিরেক্টরির ২০টি ফাইলই (Configure.mdx, ১৬ অ্যাসেট, ৩ CSS) টিউটোরিয়াল ডেমো — আসল স্টোরিগুলো ui/*.stories.tsx-এ; পুরো stories/ মুছে দিন।
- **ব্রোকেন/ডেড কোড:** plugins/MCPConnector.tsx-এ `'Authorization': Bearer` সিনট্যাক্স এরর (কম্পাইল হয় না); root ErrorBoundary, FixPreviewModal, HumanInTheLoopProtocol, SujonCoreCockpit, OperatorStudio, SupremeComponents, SwarmMap ব্যতীত বেশ কিছু কম্পোনেন্টের কোনো ইমপোর্টার নেই।
- **নন-কম্পোনেন্ট ফাইল components/-এ:** dashboard/sessionStore.ts → store/, dashboard/useHashRoute.ts → hooks/, sujon-utils.ts → lib/ — ফিচার-ফার্স্ট স্ট্রাকচারে সরানো দরকার।
- **মনোলিথ কম্পোনেন্ট:** CIDashboard (১২৭২L), CrownJewelBrowser (১১৬৮L) — ভেতরে ui/ ডুপ্লিকেট প্রিমিটিভসহ; স্প্লিট করার সুপারিশ।


---

## ব্যাচ ১০ — Frontend Pages, Store ও Services
**ব্যাচ:** 10 | **তালিকাভুক্ত:** 172 | **বিশ্লেষিত:** 172 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 48 | **স্থানান্তর প্রস্তাব:** 6 | **⚠️ সেমান্টিক মিসম্যাচ:** 11

*(পাথ কলামগুলো frontend/src-এর সাপেক্ষে; ‡ = মুছে ফেলুন/একীভূত প্রস্তাব)*

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| TODO.md | commandcenter/TODO.md | AETHEL Command Center ইমপ্লিমেন্টেশন চেকলিস্ট (P0–P3) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডকুমেন্টেশন, নাম উপযুক্ত |
| hooks.ts | commandcenter/data/hooks.ts | ~৫০টি React Query হুক+cmdKeys — অ্যাডমিন API লেয়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| types.ts | commandcenter/data/types.ts | কনসোল ডোমেইন টাইপ: Metrics, Tenant, CIReport, Backup | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CommandPalette.tsx | commandcenter/kit/CommandPalette.tsx | ⌘K ফাজি-সার্চ কমান্ড প্যালেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ConfigForm.tsx | commandcenter/kit/ConfigForm.tsx | মাস্কড কনফিগ-এন্ট্রি ফর্ম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ConfirmModal.tsx | commandcenter/kit/ConfirmModal.tsx | কনফার্মেশন মোডাল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| DataTable.tsx | commandcenter/kit/DataTable.tsx | জেনেরিক কলাম-ভিত্তিক ডেটা টেবিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| EmptyState.test.tsx | commandcenter/kit/EmptyState.test.tsx | EmptyState-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| EmptyState.tsx | commandcenter/kit/EmptyState.tsx | খালি/ডিগ্রেডেড অবস্থার প্লেসহোল্ডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| GaugeRing.test.tsx | commandcenter/kit/GaugeRing.test.tsx | GaugeRing-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| GaugeRing.tsx | commandcenter/kit/GaugeRing.tsx | SVG সার্কুলার গেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| HealthStrip.test.tsx | commandcenter/kit/HealthStrip.test.tsx | HealthStrip-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| HealthStrip.tsx | commandcenter/kit/HealthStrip.tsx | নোড হেলথ-স্ট্যাটাস স্ট্রিপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| JsonViewer.test.tsx | commandcenter/kit/JsonViewer.test.tsx | JsonViewer-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| JsonViewer.tsx | commandcenter/kit/JsonViewer.tsx | ট্রি-ভিউ JSON ভিউয়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| KpiTile.test.tsx | commandcenter/kit/KpiTile.test.tsx | KpiTile-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| KpiTile.tsx | commandcenter/kit/KpiTile.tsx | KPI ডিসপ্লে টাইল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LogStream.tsx | commandcenter/kit/LogStream.tsx | লাইভ লগ-স্ট্রিম ভিউয়ার (টেস্টহীন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| MetricStrip.test.tsx | commandcenter/kit/MetricStrip.test.tsx | MetricStrip-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| MetricStrip.tsx | commandcenter/kit/MetricStrip.tsx | মেট্রিক স্ট্রিপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Sparkline.test.tsx | commandcenter/kit/Sparkline.test.tsx | Sparkline-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| Sparkline.tsx | commandcenter/kit/Sparkline.tsx | খাঁটি SVG স্পার্কলাইন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| StatusPill.test.tsx | commandcenter/kit/StatusPill.test.tsx | StatusPill-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| StatusPill.tsx | commandcenter/kit/StatusPill.tsx | স্টেটাস-লেভেল পিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Timeline.test.tsx | commandcenter/kit/Timeline.test.tsx | Timeline-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| Timeline.tsx | commandcenter/kit/Timeline.tsx | ইভেন্ট টাইমলাইন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ToastStack.test.tsx | commandcenter/kit/ToastStack.test.tsx | ToastStack-এর ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| ToastStack.tsx | commandcenter/kit/ToastStack.tsx | টোস্ট নোটিফিকেশন স্ট্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| index.ts | commandcenter/kit/index.ts | kit ব্যারেল এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| MemoryKnowledge.tsx | commandcenter/modules/build/MemoryKnowledge.tsx | মেমরি/নলেজ স্ট্যাটস প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ModelRouter.tsx | commandcenter/modules/build/ModelRouter.tsx | মডেল-রাউটার কনফিগ প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Providers.tsx | commandcenter/modules/build/Providers.tsx | প্রোভাইডার হেলথ প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Skills.tsx | commandcenter/modules/build/Skills.tsx | স্কিল লিস্ট প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CommandDeck.tsx | commandcenter/modules/deck/CommandDeck.tsx | হোম ওভারভিউ: KPI+ডিপ্লয়-গেট+ব্যাকআপ+সিকিউরিটি | OpsOverview.tsx | অপরিবর্তিত ✅ | ⚠️ commandcenter/ডেক ব্র্যান্ডিং বাহুল্য |
| InfraTopology.tsx | commandcenter/modules/deck/InfraTopology.tsx | GCP/Railway/Render হেলথ টপোলজি ম্যাপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CostAuditor.tsx | commandcenter/modules/money/CostAuditor.tsx | কস্ট অডিট প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ROISavings.tsx | commandcenter/modules/money/ROISavings.tsx | ROI সামারি প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| UsageBilling.tsx | commandcenter/modules/money/UsageBilling.tsx | ইউসেজ/বিলিং প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CICDPipelines.tsx | commandcenter/modules/observe/CICDPipelines.tsx | CI পাইপলাইন ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| EventsExplorer.tsx | commandcenter/modules/observe/EventsExplorer.tsx | ইভেন্ট এক্সপ্লোরার প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| HealthMap.tsx | commandcenter/modules/observe/HealthMap.tsx | সার্ভিস হেলথ ম্যাপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LiveLogs.tsx | commandcenter/modules/observe/LiveLogs.tsx | লাইভ লগ ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LiveMetrics.tsx | commandcenter/modules/observe/LiveMetrics.tsx | লাইভ মেট্রিক্স ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| TrafficMonitor.tsx | commandcenter/modules/observe/TrafficMonitor.tsx | ট্রাফিক প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Agents.tsx | commandcenter/modules/operate/Agents.tsx | এজেন্ট হেলথ লিস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Sessions.tsx | commandcenter/modules/operate/Sessions.tsx | সেশন লিস্ট প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Swarm.tsx | commandcenter/modules/operate/Swarm.tsx | সোয়ার্ম টপোলজি ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| TasksQueues.tsx | commandcenter/modules/operate/TasksQueues.tsx | টাস্ক/কিউ প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| TenantsUsers.tsx | commandcenter/modules/operate/TenantsUsers.tsx | টেনান্ট/ইউজার ম্যানেজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ApprovalQueue.tsx | commandcenter/modules/secure/ApprovalQueue.tsx | HITL অ্যাপ্রোভাল কিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AuditExplorer.tsx | commandcenter/modules/secure/AuditExplorer.tsx | অডিট লগ এক্সপ্লোরার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| RateLimits.tsx | commandcenter/modules/secure/RateLimits.tsx | রেট-লিমিট প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| RulesPolicy.tsx | commandcenter/modules/secure/RulesPolicy.tsx | রুল/পলিসি এডিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SecretsHealth.tsx | commandcenter/modules/secure/SecretsHealth.tsx | সিক্রেট হেলথ প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Threats.tsx | commandcenter/modules/secure/Threats.tsx | থ্রেট-স্ক্যান প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Backups.tsx | commandcenter/modules/system/Backups.tsx | ব্যাকআপ/রিস্টোর প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ConfigEditor.tsx | commandcenter/modules/system/ConfigEditor.tsx | কনফিগ এডিটর প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| DeployGate.tsx | commandcenter/modules/system/DeployGate.tsx | ডিপ্লয়-গেট কন্ট্রোল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| FeatureFlags.tsx | commandcenter/modules/system/FeatureFlags.tsx | ফিচার-ফ্ল্যাগ টগলার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| Workspaces.tsx | commandcenter/modules/system/Workspaces.tsx | ওয়ার্কস্পেস লিস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CommandCenterRealtimeProvider.tsx | commandcenter/realtime/CommandCenterRealtimeProvider.tsx | WS+SSE→React Query ইনভ্যালিডেশন প্রোভাইডার | ConsoleRealtimeProvider.tsx | অপরিবর্তিত ✅ | ⚠️ commandcenter বাজওয়ার্ড; সাধারণ প্রোভাইডার |
| channelRegistry.ts | commandcenter/realtime/channelRegistry.ts | চ্যানেল→query-key ম্যাপিং রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sseBridges.ts | commandcenter/realtime/sseBridges.ts | SSE ইভেন্ট ব্রিজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| websocketManager.ts | commandcenter/realtime/websocketManager.ts | কনসোল WS ম্যানেজার (shared base এক্সটেন্ড) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| BottomDeck.tsx | commandcenter/shell/BottomDeck.tsx | নিচের মেট্রিক ডেক বার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CommandBar.tsx | commandcenter/shell/CommandBar.tsx | টপ কমান্ড বার+প্যালেট ট্রিগার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CommandCenterApp.tsx | commandcenter/shell/CommandCenterApp.tsx | কনসোল অ্যাপ রুট (শেল কম্পোজিশন) | ConsoleApp.tsx | অপরিবর্তিত ✅ | ⚠️ commandcenter বাজওয়ার্ড; mundane শেল |
| LeftRail.tsx | commandcenter/shell/LeftRail.tsx | বাম নেভিগেশন রেল+ব্যাজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| WorkspaceViewport.tsx | commandcenter/shell/WorkspaceViewport.tsx | lazy MODULE_MAP মডিউল-রাউটার (২৯ প্যানেল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| WorkspaceViewport.test.tsx | commandcenter/shell/__tests__/WorkspaceViewport.test.tsx | WorkspaceViewport-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| index.ts | commandcenter/shell/index.ts | shell ব্যারেল এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useCommandCenterStore.test.ts | commandcenter/state/__tests__/useCommandCenterStore.test.ts | কনসোল স্টোরের টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| useCommandCenterStore.ts | commandcenter/state/useCommandCenterStore.ts | WS স্ট্যাটাস+অ্যাক্টিভ-মডিউল UI স্টেট | use-console-store.ts | অপরিবর্তিত ✅ | ⚠️ commandcenter বাজওয়ার্ড; সাধারণ স্টেট |
| tokens.css | commandcenter/styles/tokens.css | ৪-থিম ডিজাইন টোকেন (AETHEL ব্র্যান্ডিং) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ফাইলনাম নিরপেক্ষ |
| BillingPage.tsx | pages/BillingPage.tsx | সাবস্ক্রিপশন/বিলিং পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ErrorPage.tsx | pages/ErrorPage.tsx | রুট-লেভেল এরর বাউন্ডারি পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ProfilePage.tsx | pages/ProfilePage.tsx | প্রোফাইল+সেটিংস (unified-store টগলসহ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| PromptTemplatePage.tsx | pages/PromptTemplatePage.tsx | প্রম্পট টেমপ্লেট ম্যানেজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SharedConversationPage.tsx | pages/SharedConversationPage.tsx | পাবলিক শেয়ার্ড কনভার্সেশন ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AdminShell.tsx | pages/admin/AdminShell.tsx | অ্যাডমিন রুট: লগইন+OTP+AdminConsole হোস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LoginPage.tsx | pages/auth/LoginPage.tsx | লগইন ফর্ম (App.tsx-রাউটেড) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LoginScreen.tsx | pages/auth/LoginScreen.tsx | লগইন ডুপ্লিকেট — রাউট/ইমপোর্টার নেই | মুছে ফেলুন ‡ | অপরিবর্তিত ✅ | অরাউটেড ডুপ্লিকেট, LoginPage ক্যানোনিক্যাল |
| RegisterPage.tsx | pages/auth/RegisterPage.tsx | রেজিস্ট্রেশন ফর্ম (রাউটেড) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| RegisterScreen.tsx | pages/auth/RegisterScreen.tsx | রেজিস্ট্রেশন ডুপ্লিকেট — ইমপোর্টার নেই | মুছে ফেলুন ‡ | অপরিবর্তিত ✅ | অরাউটেড ডুপ্লিকেট, RegisterPage ক্যানোনিক্যাল |
| AIStudio.tsx | pages/user/AIStudio.tsx | চ্যাট+প্রিভিউ+মোবাইল-সিম প্লেগ্রাউন্ড (স্টাব রেসপন্স) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AgentWorkspace.tsx | pages/user/AgentWorkspace.tsx | Monaco+xterm+WebContainer কোডজেন ওয়ার্কস্পেস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ArchitectTower.tsx | pages/user/ArchitectTower.tsx | অ্যাডমিন pending-fixes তালিকা+OneClickPatch | AdminFixesPanel.tsx | pages/admin/ | ⚠️ গ্র্যান্ডিওজ নাম+ভুল ডিরেক্টরি |
| CostDashboard.tsx | pages/user/CostDashboard.tsx | কস্ট/ইউসেজ ড্যাশবোর্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| DebateOverlay.tsx | pages/user/EvolutionForge/DebateOverlay.tsx | এজেন্ট ডিবেট লগ ওভারলে | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| EvolutionForge.tsx | pages/user/EvolutionForge/EvolutionForge.tsx | ReactFlow এজেন্ট/টাস্ক গ্রাফ এডিটর+অটোসেভ | AgentFlowEditor.tsx | অপরিবর্তিত ✅ | ⚠️ evolution/forge বাজওয়ার্ড; ফ্লো-এডিটর |
| ForgeSidebar.tsx | pages/user/EvolutionForge/ForgeSidebar.tsx | উপলব্ধ-নোড প্যালেট সাইডবার | FlowSidebar.tsx | অপরিবর্তিত ✅ | forge নামের সাথে সংগতি |
| useForgeAutosave.ts | pages/user/EvolutionForge/hooks/useForgeAutosave.ts | গ্রাফ অটোসেভ হুক | use-flow-autosave.ts | অপরিবর্তিত ✅ | হুক kebab-case কনভেনশন |
| AgentNode.tsx | pages/user/EvolutionForge/nodes/AgentNode.tsx | ReactFlow কাস্টম এজেন্ট নোড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| TaskNode.tsx | pages/user/EvolutionForge/nodes/TaskNode.tsx | ReactFlow কাস্টম টাস্ক নোড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| IdeWorkspace.tsx | pages/user/IdeWorkspace.tsx | Monaco IDE: ট্রি, ট্যাব, টার্মিনাল, AI বার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| IntegrationsManager.tsx | pages/user/IntegrationsManager.tsx | ইন্টিগ্রেশন কনফিগ প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SkillCatalog.tsx | pages/user/SkillCatalog.tsx | স্কিল ক্যাটালগ+ইনস্টল UI | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| InstallModal.tsx | pages/user/plugins/InstallModal.tsx | প্লাগইন ইনস্টল কনফার্মেশন মোডাল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| PluginCard.tsx | pages/user/plugins/PluginCard.tsx | প্লাগইন কার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| PluginMarketplace.tsx | pages/user/plugins/PluginMarketplace.tsx | প্লাগইন মার্কেটপ্লেস পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| adminService.test.ts | services/adminService.test.ts | adminService-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| adminService.ts | services/adminService.ts | অ্যাডমিন ইউজার/টেনান্ট API ক্লায়েন্ট | admin-service.ts | অপরিবর্তিত ✅ | নন-কম্পোনেন্ট TS kebab-case |
| adminTokenStore.test.ts | services/adminTokenStore.test.ts | adminTokenStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| adminTokenStore.ts | services/adminTokenStore.ts | অ্যাডমিন JWT স্টোরেজ+ডিকোড হেল্পার | admin-token-store.ts | lib/ | টোকেন ইউটিল — lib/-ই সঠিক |
| agentService.test.ts | services/agentService.test.ts | agentService-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| agentService.ts | services/agentService.ts | এজেন্ট টাস্ক তৈরি/ট্র্যাকিং API | agent-service.ts | অপরিবর্তিত ✅ | নন-কম্পোনেন্ট TS kebab-case |
| aiActions.test.ts | services/aiActions.test.ts | useAiActions হুকের টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| aiActions.ts | services/aiActions.ts | useAiActions হুক: কোড এক্সপ্লেইন/ফিক্স/অপ্টিমাইজ | use-ai-actions.ts | hooks/ | হুক services-এ নয় |
| microserviceMonitor.test.ts | services/api/microserviceMonitor.test.ts | microserviceMonitor-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| microserviceMonitor.ts | services/api/microserviceMonitor.ts | Java worker হেলথ ফেচ | microservice-monitor.ts | অপরিবর্তিত ✅ | kebab-case; অবস্থান সঠিক |
| apiClient.test.ts | services/apiClient.test.ts | apiClient-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| apiClient.ts | services/apiClient.ts | কোর ফেচ ক্লায়েন্ট: কিউ, CSRF, টাইমআউট, টোকেন | api-client.ts | services/api/ | API ক্লায়েন্ট services/api/-তে |
| AudioPlaybackService.ts | services/audio/AudioPlaybackService.ts | অডিও প্লেব্যাক ক্লাস | audio-playback.ts | অপরিবর্তিত ✅ | নন-কম্পোনেন্ট TS kebab-case |
| AudioRecorderService.ts | services/audio/AudioRecorderService.ts | মাইক রেকর্ডিং ক্লাস | audio-recorder.ts | অপরিবর্তিত ✅ | নন-কম্পোনেন্ট TS kebab-case |
| authService.test.ts | services/authService.test.ts | authService-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| authService.ts | services/authService.ts | লগইন/রেজিস্টার API কল | auth-service.ts | অপরিবর্তিত ✅ | নন-কম্পোনেন্ট TS kebab-case |
| chatService.test.ts | services/chatService.test.ts | chatService-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| chatService.ts | services/chatService.ts | চ্যাট স্ট্রিম API; getAethelResponse হেল্পার | chat-service.ts | অপরিবর্তিত ✅ | kebab-case; Aethel ফাংশননাম পর্যালোচনীয় |
| ciReportService.test.ts | services/ciReportService.test.ts | ciReportService-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| ciReportService.ts | services/ciReportService.ts | CI রিপোর্ট ফেচ ক্লায়েন্ট | ci-report-service.ts | অপরিবর্তিত ✅ | নন-কম্পোনেন্ট TS kebab-case |
| costOptimizer.service.test.ts | services/costOptimizer.service.test.ts | costOptimizer-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| costOptimizer.service.ts | services/costOptimizer.service.ts | রেট-লিমিট+ডিডুপ+ক্যাশ রিকোয়েস্ট লেয়ার | request-optimizer.service.ts | অপরিবর্তিত ✅ | কনটেন্ট রিকোয়েস্ট-অপটিমাইজার; নাম অসঙ্গত |
| heartbeat.test.ts | services/heartbeat.test.ts | heartbeat-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| heartbeat.ts | services/heartbeat.ts | অ্যান্টি-স্লিপ কিপ-অ্যালাইভ পিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| queryClient.test.ts | services/queryClient.test.ts | queryClient-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| queryClient.ts | services/queryClient.ts | React Query ক্লায়েন্ট+স্মার্ট রিট্রাই | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| WebSocketManager.ts | services/realtime/WebSocketManager.ts | WS ম্যানেজার ক্লোন — ইমপোর্টারশূন্য | মুছে ফেলুন ‡ | অপরিবর্তিত ✅ | commandcenter/websocketManager সক্রিয় ক্লোন |
| sandbox.ts | services/sandbox.ts | স্যান্ডবক্স কোড-এক্সিকিউশন ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| skillsService.test.ts | services/skillsService.test.ts | skillsService-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| skillsService.ts | services/skillsService.ts | স্কিল ক্যাটালগ/ইনস্টল/হেলথ API | skills-service.ts | অপরিবর্তিত ✅ | নন-কম্পোনেন্ট TS kebab-case |
| storageApi.test.ts | services/storageApi.test.ts | storageApi-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| storageApi.ts | services/storageApi.ts | R2 ফাইল-আপলোড ক্লায়েন্ট | storage-api.ts | services/api/ | API ক্লায়েন্ট services/api/-তে |
| supremeShared.test.ts | services/supremeShared.test.ts | supremeShared-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| supremeShared.ts | services/supremeShared.ts | Electron প্ল্যাটফর্ম+shared-services বুটস্ট্র্যাপ | desktop-services.ts | অপরিবর্তিত ✅ | ⚠️ supreme বাজওয়ার্ড; vague নাম |
| test_budget_check.test.ts | services/test_budget_check.test.ts | apiClient-এর 402 বাজেট-গার্ড টেস্ট | budget-guard.test.ts | অপরিবর্তিত ✅ | অস্পষ্ট নাম+test_ প্রিফিক্স |
| _legacy_stores.md | store/_legacy_stores.md | R13 লিগ্যাসি-স্টোর মাইগ্রেশন প্ল্যান ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডকুমেন্টেশন, উপযুক্ত |
| adminStore.test.ts | store/adminStore.test.ts | adminStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| adminStore.ts | store/adminStore.ts | অ্যাডমিন লগইন+TOTP+প্রোভিশনিং স্টেট | admin-store.ts | অপরিবর্তিত ✅ | store kebab-case কনভেনশন |
| authStore.test.ts | store/authStore.test.ts | authStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| authStore.ts | store/authStore.ts | ইউজার অথ স্টেট+টোকেন পারসিস্টেন্স | auth-store.ts | অপরিবর্তিত ✅ | store kebab-case কনভেনশন |
| chatStore.test.ts | store/chatStore.test.ts | chatStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| chatStore.ts | store/chatStore.ts | চ্যাট মেসেজ স্টেট | chat-store.ts | অপরিবর্তিত ✅ | store kebab-case কনভেনশন |
| customerStore.test.ts | store/customerStore.test.ts | customerStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| customerStore.ts | store/customerStore.ts | কাস্টমার স্টেট (persisted) | customer-store.ts | অপরিবর্তিত ✅ | store kebab-case কনভেনশন |
| dashboardStore.test.ts | store/dashboardStore.test.ts | dashboardStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| dashboardStore.ts | store/dashboardStore.ts | ড্যাশবোর্ড UI স্টেট | dashboard-store.ts | অপরিবর্তিত ✅ | store kebab-case কনভেনশন |
| index.test.ts | store/index.test.ts | store index-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| index.ts | store/index.ts | R13 ইউনিফাইড-স্টোর ফ্ল্যাগ টগল/এন্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| localFirstDb.ts | store/localFirstDb.ts | Dexie IndexedDB+ব্যাকগ্রাউন্ড সিংক (আনওয়্যার্ড) | local-first-db.ts | services/ | DB লেয়ার, store নয়; kebab-case |
| sessionCockpitStore.ts | store/sessionCockpitStore.ts | সেশন লগ/ফাইলট্রি/রিজনিং স্টেট (ককপিট UI) | agent-session-store.ts | অপরিবর্তিত ✅ | ⚠️ cockpit বাজওয়ার্ড; kebab-case |
| apiSlice.ts | store/slices/apiSlice.ts | ১-লাইন নাল রিটার্নিং স্টাব | মুছে ফেলুন ‡ | অপরিবর্তিত ✅ | ডেড স্ক্যাফোল্ড স্লাইস |
| migration_map.test.ts | store/slices/migration_map.test.ts | migration_map-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| migration_map.ts | store/slices/migration_map.ts | লিগ্যাসি→ইউনিফাইড স্লাইস নাম-ম্যাপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| slices.test.ts | store/slices/slices.test.ts | নাল-স্লাইস স্টাব টেস্ট | মুছে ফেলুন ‡ | অপরিবর্তিত ✅ | স্টাবগুলোর সাথে অপ্রাসঙ্গিক |
| uiSlice.ts | store/slices/uiSlice.ts | ১-লাইন নাল রিটার্নিং স্টাব | মুছে ফেলুন ‡ | অপরিবর্তিত ✅ | ডেড স্ক্যাফোল্ড স্লাইস |
| userSlice.ts | store/slices/userSlice.ts | ১-লাইন নাল রিটার্নিং স্টাব | মুছে ফেলুন ‡ | অপরিবর্তিত ✅ | ডেড স্ক্যাফোল্ড স্লাইস |
| workspaceSlice.ts | store/slices/workspaceSlice.ts | ১-লাইন নাল রিটার্নিং স্টাব | মুছে ফেলুন ‡ | অপরিবর্তিত ✅ | ডেড স্ক্যাফোল্ড স্লাইস |
| themeStore.test.ts | store/themeStore.test.ts | themeStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| themeStore.ts | store/themeStore.ts | থিম স্টেট | theme-store.ts | অপরিবর্তিত ✅ | store kebab-case কনভেনশন |
| tierSStore.test.ts | store/tierSStore.test.ts | tierSStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| tierSStore.ts | store/tierSStore.ts | রিজনিং-স্টেপ+আর্টিফ্যাক্ট স্টেট (Tier S চ্যাট) | reasoning-store.ts | অপরিবর্তিত ✅ | ⚠️ "Tier S" বাজওয়ার্ড; kebab-case |
| unifiedStore.ts | store/unifiedStore.ts | R13 ইউনিফাইড স্টোর: হেলথ, অ্যালার্ট, ডিপ্লয় | unified-store.ts | অপরিবর্তিত ✅ | store kebab-case কনভেনশন |
| useIdeStore.test.ts | store/useIdeStore.test.ts | useIdeStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| useIdeStore.ts | store/useIdeStore.ts | IDE ফাইল/ট্যাব/WebContainer স্টেট | use-ide-store.ts | অপরিবর্তিত ✅ | store kebab-case কনভেনশন |
| useStore.test.ts | store/useStore.test.ts | useStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| useStore.ts | store/useStore.ts | লিগ্যাসি রুট স্টোর (SupremeState: ইভোলিউশন+কনফিগ) | app-store.ts | অপরিবর্তিত ✅ | ⚠️ vague+supreme; R13-এ মার্জ হবে |
| useSupremeStore.test.ts | store/useSupremeStore.test.ts | useSupremeStore-এর টেস্ট | মুছে ফেলুন ‡ | অপরিবর্তিত ✅ | স্ক্যাফোল্ডের সাথে ডিলিট |
| useSupremeStore.ts | store/useSupremeStore.ts | নাল-স্লাইস কম্পোজ স্ক্যাফোল্ড | মুছে ফেলুন ‡ | অপরিবর্তিত ✅ | ⚠️ supreme; ডেড স্ক্যাফোল্ড |
| useWorkspaceSettingsStore.test.ts | store/useWorkspaceSettingsStore.test.ts | useWorkspaceSettingsStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| useWorkspaceSettingsStore.ts | store/useWorkspaceSettingsStore.ts | ডক ইন্টিগ্রেশন সেটিংস স্টেট | use-workspace-settings-store.ts | অপরিবর্তিত ✅ | store kebab-case কনভেনশন |
| useWorkspaceStore.test.ts | store/useWorkspaceStore.test.ts | useWorkspaceStore-এর টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সোর্স-সংলগ্ন টেস্ট |
| useWorkspaceStore.ts | store/useWorkspaceStore.ts | ওয়ার্কস্পেস+নোটিফিকেশন স্টেট | use-workspace-store.ts | অপরিবর্তিত ✅ | store kebab-case কনভেনশন |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **commandcenter/ = "AETHEL Command Center"** — আসলে একটি নিয়মিত অ্যাডমিন অপারেশন্স কনসোল (kit + ৩১ মডিউল + shell + realtime + data)। পুরো ডিরেক্টরি এক কমিটে `admin-console/`-এ রিনেম করা উচিত; ভেতরের কোড সুগঠিত ও টেস্টকভার্ড, শুধু ব্র্যান্ডিং বাহুল্য।
- **অ্যানোমালি:** সম্পূর্ণ commandcenter ট্রি-র (৭৪ ফাইল) কোনো বাইরের ইমপোর্টার/রুট নেই — App.tsx বা routes-এ হুক করা হয়নি; ওয়্যারিং না করে রাখলে বিশাল ডেড-কোড ব্লক।
- **R13 স্টোর মাইগ্রেশন চলছে:** `_legacy_stores.md` অনুযায়ী ১২টি লিগ্যাসি স্টোর unifiedStore-এ মাইগ্রেট হবে; useSupremeStore + ৪টি নাল-স্লাইস এখনই ডিলিটযোগ্য, বাকি ১২টি Phase-2 shim-এ যাবে।
- **ডুপ্লিকেট জোড়া:** auth-এ Login/Register × Page/Screen (Screen দুটি অরাউটেড) এবং services/realtime/WebSocketManager vs commandcenter/realtime/websocketManager — দুটোই `@supremeai/shared-services`-এর BaseWebSocketManager এক্সটেন্ড করে; services কপিটি ইমপোর্টারশূন্য।
- **মিসলোকেশন:** aiActions (হুক) → hooks/, localFirstDb (Dexie DB) → services/, adminTokenStore → lib/, apiClient+storageApi → services/api/।
- **বাজওয়ার্ড পরিবার (⚠️×১১):** commandcenter ×4, supreme ×3 (useStore, useSupremeStore, supremeShared), Tier S, cockpit, ArchitectTower, EvolutionForge; Aethel ব্র্যান্ডিং TODO.md/tokens.css/chatService.getAethelResponse-এও আছে।
- **টেস্ট সংস্কৃতি ভালো:** kit-এর ১৪টির মধ্যে ১৩ কম্পোনেন্ট টেস্টেড, services/store-এর প্রায় সব মডিউলে সংলগ্ন .test.ts আছে (LogStream ও kit/JITOTPModal টেস্টহীন — TODO.md-তে উল্লিখিত JITOTPModal ফাইলটি আসলে অনুপস্থিত)।
- **ঐচ্ছিক:** `store/` → `stores/` প্ল্যাটার ডিরেক্টরি-রিনেম এবং EvolutionForge/ → flow-editor/ ফোল্ডার-রিনেম একসাথে করা যেতে পারে।


---

## ব্যাচ ১১ — Frontend Infrastructure (hooks, lib, utils, contexts)
**ব্যাচ:** 11 | **তালিকাভুক্ত:** 105 | **বিশ্লেষিত:** 105 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 26 | **স্থানান্তর প্রস্তাব:** 7 | **⚠️ সেমান্টিক মিসম্যাচ:** 3

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| README.md | frontend/README.md | স্টক Vite+React টেমপ্লেট ডকুমেন্টেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | বয়লারপ্লেট; বাস্তব ডক _INDEX.md-তেই |
| _INDEX.md | frontend/_INDEX.md | বাংলা AI-ফ্রেন্ডলি ফোল্ডার ইনডেক্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| commandcenter.spec.ts | frontend/e2e/ | কমান্ড সেন্টার Playwright স্মোক টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| multiworkspace.spec.ts | frontend/e2e/ | মাল্টি-ওয়ার্কস্পেস ফ্লিট ক্যানভাস স্মোক টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| eslint.config.js | frontend/ | ফ্ল্যাট ESLint কনফিগ (TS+hooks+storybook) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| fix_tsc.py | frontend/ | v1 TS-এরর অটো-ফিক্স কোডমড (one-off) | মুছে ফেলুন | — | v2 সাপারসেডেড; root কোডমড অনুচিত |
| fix_tsc_v2.py | frontend/ | v2 TS-এরর অটো-ফিক্স কোডমড | অপরিবর্তিত ✅ | frontend/scripts/ | one-off কোডমড scripts/-এ রাখুন |
| get_errors.py | frontend/ | lint-results.json এরর পার্সার | get_lint_errors.py | frontend/scripts/ | নাম অস্পষ্ট; স্ক্রিপ্ট scripts/-এ যাবে |
| index.html | frontend/ | Vite এন্ট্রি HTML (CSP+SEO মেটা) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| knip.json | frontend/ | knip ডেড-এক্সপোর্ট স্ক্যানার কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| package.json | frontend/ | ডিপ ও স্ক্রিপ্ট (ডুয়াল-পোর্টাল build) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | অ্যানোমালি: storybook 8+10, reactflow+xyflow ডুপ্লিকেট |
| admin.html | frontend/public/ | অ্যাডমিন পোর্টালে রিডাইরেক্ট পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| customer.html | frontend/public/ | ইউজার স্টুডিওতে রিডাইরেক্ট পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| design-system-preview.html | frontend/public/ | ডিজাইন টোকেন প্রিভিউ স্ট্যাটিক পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডেভ-অনলি প্রিভিউ, রাখা যেতে পারে |
| favicon.svg | frontend/public/ | ফেভিকন অ্যাসেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | অ্যাসেট, colocate ঠিক আছে |
| icons.svg | frontend/public/ | আইকন স্প্রাইট অ্যাসেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | অ্যাসেট, colocate ঠিক আছে |
| manifest.json | frontend/public/ | PWA ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ভাঙা আইকন পাথ (favicon.ico/logo-*.png) ফিক্স |
| sw.js | frontend/public/ | সার্ভিস ওয়ার্কার প্রিক্যাশ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| analyze_stores.py | frontend/scripts/ | zustand স্টোর অডিট (Windows পাথ হার্ডকোড) | মুছে ফেলুন | — | F:/ হার্ডকোডেড অচল dry-run স্ক্রিপ্ট |
| bundle-check.sh | frontend/scripts/ | gzip বান্ডল সাইজ গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| App.css | frontend/src/ | Vite টেমপ্লেট counter/hero CSS | মুছে ফেলুন | — | কোনো ইমপোর্টার নেই, টেমপ্লেট অবশেষ |
| App.test.tsx | frontend/src/ | App ইন্টিগ্রেশন স্মোক টেস্ট (vitest) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| App.tsx | frontend/src/ | রুট রাউটার+প্রোভাইডার+lazy পেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| page.tsx | frontend/src/app/ | Next.js-স্টাইল ecosystem ড্যাশবোর্ড শেল | মুছে ফেলুন | — | Vite অ্যাপে অরাউটেড নেক্সট অবশেষ, ইমপোর্টারহীন |
| hero.png | frontend/src/assets/ | হিরো ইমেজ | মুছে ফেলুন | — | অব্যবহৃত অ্যাসেট |
| react.svg | frontend/src/assets/ | রিঅ্যাক্ট লোগো | মুছে ফেলুন | — | টেমপ্লেট অ্যাসেট, অব্যবহৃত |
| vite.svg | frontend/src/assets/ | Vite লোগো | মুছে ফেলুন | — | টেমপ্লেট অ্যাসেট, অব্যবহৃত |
| commandRegistry.test.ts | frontend/src/config/ | কমান্ড রেজিস্ট্রি ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | colocate টেস্ট প্যাটার্ন ঠিক |
| commandRegistry.ts | frontend/src/config/ | ইউনিফাইড কমান্ড প্যালেট রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| constants.ts | frontend/src/config/ | AppDefaults env ফলব্যাক ফ্ল্যাগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ছোট ডায়নামিক কনফিগ |
| ThemeConstants.ts | frontend/src/contexts/ | Theme টাইপ+সাইকেল অর্ডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ThemeContext.ts | frontend/src/contexts/ | থিম React context ডেফিনিশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ThemeProvider.tsx | frontend/src/contexts/ | থিম প্রোভাইডার (localStorage+REST sync) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ThemeSyncProvider-এর সাথে একীভূত করুন |
| ToastContext.ts | frontend/src/contexts/ | টোস্ট context+global ref | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ToastProvider.tsx | frontend/src/contexts/ | টোস্ট প্রোভাইডার+ইনলাইন UI | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useTheme.ts | frontend/src/contexts/ | থিম consumer হুক | অপরিবর্তিত ✅ | src/hooks/ | হুক src/hooks/ কনভেনশন |
| useToast.ts | frontend/src/contexts/ | টোস্ট consumer হুক | অপরিবর্তিত ✅ | src/hooks/ | হুক src/hooks/ কনভেনশন |
| ErrorBoundary.tsx | frontend/src/core/ | সেলফ-হিলিং এরর বাউন্ডারি | মুছে ফেলুন | — | ইমপোর্টারহীন; GlobalErrorBoundary ইতিমধ্যে আছে |
| stateManagement.ts | frontend/src/core/ | SelfHealingStateManager সিঙ্গলটন | selfHealingStateManager.ts | অপরিবর্তিত ✅ | নাম অস্পষ্টভাবে জেনেরিক |
| firebase.ts | frontend/src/ | Firebase init+auth হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useTranslation.test.ts | frontend/src/hooks/__tests__/ | ট্রান্সলেশন হুক টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | __tests__ প্যাটার্ন ঠিক |
| index.ts | frontend/src/hooks/ | বারেল এক্সপোর্ট (৬/২০ হুক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | পার্শিয়াল বারেল সম্পূর্ণ করুন |
| useAdminApi.ts | frontend/src/hooks/ | ১৭টি admin react-query হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useAuth.ts | frontend/src/hooks/ | Firebase auth+customerStore হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useBudgetCheck.ts | frontend/src/hooks/ | বাজেট গার্ড (402) হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useChat.ts | frontend/src/hooks/ | চ্যাট সেন্ড/স্ট্রিম হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useDashboardActions.ts | frontend/src/hooks/ | TODO-স্টাব ফেক প্রমিজ হুক | মুছে ফেলুন | — | ফাংশনহীন স্টাব, ইমপ্লিমেন্ট না হলে বাদ |
| useDashboardData.ts | frontend/src/hooks/ | metrics/cost/health কুয়েরি হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useDynamicDock.ts | frontend/src/hooks/ | ড্র্যাগ-ড্রপ→agent action হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useErrorHandler.ts | frontend/src/hooks/ | সেন্ট্রালাইজড এরর হ্যান্ডলিং হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useEventBus.test.ts | frontend/src/hooks/ | eventBus হুক টেস্ট (colocate) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টেস্ট-প্লেসমেন্ট কনসিসটেন্সি নোট |
| useEventBus.ts | frontend/src/hooks/ | eventBus সাবস্ক্রিপশন হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useIframeConsole.ts | frontend/src/hooks/ | iframe কনসোল ট্র্যাপ হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useLogParserWorker.ts | frontend/src/hooks/ | log worker র‍্যাপার+main-thread ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| usePlugins.ts | frontend/src/hooks/ | প্লাগিন মার্কেটপ্লেস ফেচ হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | খালি Bearer টোকেন বাগ নোট |
| useServerStream.ts | frontend/src/hooks/ | SSE টাস্ক স্ট্রিম+হেল্থ প্রোব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useSwarmGraph.ts | frontend/src/hooks/ | xyflow সোয়ার্ম গ্রাফ ডেল্টা পোলিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useSwarmStream.ts | frontend/src/hooks/ | SwarmHealthContext consumer হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useTranslation.ts | frontend/src/hooks/ | কাস্টম ট্রান্সলেশন হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | i18n/useI18n-এর সাথে ডুপ্লিকেশন একীভূত করুন |
| useWebSocket.ts | frontend/src/hooks/ | জেনেরিক WebSocket ক্লায়েন্ট হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| useWorkspaceSettings.ts | frontend/src/hooks/ | zustand persisted UI সেটিংস স্টোর | workspaceSettingsStore.ts | src/store/ | এটি হুক নয়, স্টোর; store/-এ যাবে |
| I18nContext.ts | frontend/src/i18n/ | i18n context ডেফিনিশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| I18nProvider.tsx | frontend/src/i18n/ | ফাইল I18nProvider, এক্সপোর্ট TranslationProvider | এক্সপোর্ট I18nProvider করুন | অপরিবর্তিত ✅ | ফাইল-এক্সপোর্ট নাম অমিল |
| config.ts | frontend/src/i18n/ | locales তালিকা+নাম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| translations.ts | frontend/src/i18n/ | en/bn/es/zh ডিকশনারি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | লোকেলসহ colocate ঠিক আছে |
| useI18n.ts | frontend/src/i18n/ | i18n consumer হুক | অপরিবর্তিত ✅ | src/hooks/ | হুক src/hooks/ কনভেনশন |
| index.css | frontend/src/ | ৭৭৭L থিম টোকেন (Tailwind v4 @theme) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | এন্ট্রি স্টাইলশিট, নাম ঠিক |
| cache.manager.ts | frontend/src/lib/ | Upstash Redis ক্যাশ+compression | অপরিবর্তিত ✅ | backend বা shared প্যাকেজ | সার্ভার-সাইড Redis ব্রাউজার বান্ডেলে অনুপযুক্ত |
| componentEventBus.ts | frontend/src/lib/ | টাইপড ক্রস-কম্পোনেন্ট ইভেন্ট বাস | component-event-bus.ts | অপরিবর্তিত ✅ | lib kebab-case কনভেনশন |
| api.ts | frontend/src/lib/ecosystem/ | ৪৮-endpoint ecosystem API ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| types.ts | frontend/src/lib/ecosystem/ | ব্যাকএন্ড মডেল টাইপ মিরর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| etag.ts | frontend/src/lib/ | ETag হেল্পার ফাংশন | মুছে ফেলুন | — | ইমপোর্টারহীন ডেড কোড |
| llm.router.ts | frontend/src/lib/ | free-tier LLM রাউটার (মক SDK) | মুছে ফেলুন | — | মক SDK+ইমপোর্টারহীন; LLM রাউটিং ব্যাকএন্ডের কাজ |
| modelBranding.ts | frontend/src/lib/ | প্রোভাইডার→SupremeAI লেবেল ম্যাপ | model-branding.ts | অপরিবর্তিত ✅ | lib kebab-case কনভেনশন |
| secureSse.ts | frontend/src/lib/ | fetch-event-source SSE র‍্যাপার | secure-sse.ts | অপরিবর্তিত ✅ | lib kebab-case কনভেনশন |
| supabase.client.ts | frontend/src/lib/ | Supabase ক্লায়েন্ট (NEXT_PUBLIC লেগেসি) | মুছে ফেলুন | — | ইমপোর্টারহীন; অথ Firebase-ভিত্তিক |
| main.tsx | frontend/src/ | অ্যাপ এন্ট্রি (SW+Firebase+প্রোভাইডার) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| MockSwarmProvider.tsx | frontend/src/providers/ | "Mock" নামেও রিয়েল API পোলার; unwired ⚠️ | SwarmHealthProvider.tsx | src/contexts/ | নাম-কনটেন্ট অমিল; contexts/-এ মার্জ |
| SwarmHealthContext.ts | frontend/src/providers/ | সোয়ার্ম হেল্থ context ডেফ | অপরিবর্তিত ✅ | src/contexts/ | providers/ ও contexts/ একত্র করুন |
| ThemeSyncContext.ts | frontend/src/providers/ | SSE থিম context ডেফ | মুছে ফেলুন | — | ডুপ্লিকেট থিম সিস্টেম; ThemeProvider-এ একীভূত |
| ThemeSyncProvider.tsx | frontend/src/providers/ | SSE থিম সিঙ্ক প্রোভাইডার | মুছে ফেলুন | — | ThemeProvider-এর সাথে ফাংশনাল ডুপ্লিকেট |
| useThemeSync.ts | frontend/src/providers/ | অব্যবহৃত consumer হুক | মুছে ফেলুন | — | কোনো কনজিউমার নেই |
| tierSRoutes.tsx | frontend/src/routes/ | share/prompt-library lazy ইউজার রুট | extraRoutes.tsx | অপরিবর্তিত ✅ | ⚠️ "Tier-S" দৈনন্দিন রুটে অতি-উদ্দীপক |
| supremeShared.ts | frontend/src/shared/ | env CONFIG হেল্পার | মুছে ফেলুন | — | ⚠️ supreme ব্রান্ডিং; ইমপোর্টারহীন (utils/api.ts-ই ব্যবহৃত) |
| setup.ts | frontend/src/test/ | vitest সেটআপ (localStorage/EventSource মক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| types.ts | frontend/src/ | admin API টাইপ (Skill/HealthMap/AdminUser) | admin.ts | src/types/ | রুট-লেভেল বিক্ষিপ্ত টাইপ types/-এ যাবে |
| chat.ts | frontend/src/types/ | ইউনিফাইড চ্যাট মেসেজ টাইপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| customer.ts | frontend/src/types/ | user/project/widget টাইপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| schema.ts | frontend/src/types/ | "OpenAPI-জেনারেটেড" দাবি, একটি স্টাব ইন্টারফেস | apiResponse.ts | অপরিবর্তিত ✅ | schema নাম বিভ্রান্তিকর |
| swarm.ts | frontend/src/types/ | সোয়ার্ম মেট্রিক্স/context টাইপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| api.test.ts | frontend/src/utils/ | getApiBaseUrl রেজলিউশন টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| api.ts | frontend/src/utils/ | বেস-URL+ফ্রন্টএন্ড সার্কিট ব্রেকার+রিট্রাই | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| apiInterceptor.ts | frontend/src/utils/ | গ্লোবাল fetch ইন্টারসেপ্টর+JSON গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cn.test.ts | frontend/src/utils/ | cn ইউটিল টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cn.ts | frontend/src/utils/ | clsx+tailwind-merge হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ইন্ডাস্ট্রি-স্ট্যান্ডার্ড নাম |
| deviceFingerprint.test.ts | frontend/src/utils/ | ফিঙ্গারপ্রিন্ট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| deviceFingerprint.ts | frontend/src/utils/ | SHA-256 জিরো-কস্ট ডিভাইস ফিঙ্গারপ্রিন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vite-env.d.ts | frontend/src/ | Vite env টাইপ ডিক্লারেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| logParser.worker.ts | frontend/src/workers/ | লগ পার্স/সার্চ ওয়েব ওয়ার্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tailwind.config.js | frontend/ | Tailwind v3-স্টাইল JS কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | v4 @theme ব্যবহৃত; অপ্রচলিত হলে বাদ |
| tsconfig.app.json | frontend/ | অ্যাপ TS কনফিগ (@/* paths) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tsconfig.json | frontend/ | সলিউশন রুফ TS কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tsconfig.node.json | frontend/ | vite.config TS কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vite.config.ts | frontend/ | ডুয়াল-পোর্টাল প্রক্সি+build-info প্লাগিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vitest.config.ts | frontend/ | ভাইটেস্ট কনফিগ+কভারেজ থ্রেশহোল্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- ১৬টি ফাইল মুছে ফেলার প্রস্তাব: টেমপ্লেট অবশেষ (App.css, react.svg, vite.svg, hero.png), Next.js-লেফটওভার app/page.tsx, মৃত lib (etag, llm.router, supabase.client), ডুপ্লিকেট core/ErrorBoundary, স্টাব useDashboardActions, root কোডমড fix_tsc.py + analyze_stores.py, ThemeSync ট্রায়ো, supremeShared.ts।
- দুটি সমান্তরাল থিম সিস্টেম: contexts/ThemeProvider (localStorage+REST) বনাম providers/ThemeSyncProvider (SSE) — ThemeSync ট্রায়ো মুছে ThemeProvider-এ একীভূত করুন; useThemeSync-এর কোনো কনজিউমারই নেই।
- providers/ ও contexts/ দুটি ডিরেক্টরি একই দায়িত্ব পালন করছে — একটিতে মার্জ করুন; এছাড়া MockSwarmProvider কেউ ইমপোর্টই করে না (unwired), অথচ "Mock" নাম দিয়ে রিয়েল API কল করে।
- তিনটি i18n ব্যবস্থা সহাবস্থান করছে: hooks/useTranslation, i18n/useI18n+I18nProvider, এবং package.json-এর অব্যবহৃত react-i18next/i18next ডিপ — একটি বেছে বাকি বাদ দিন।
- lib/ নামকরণ অসামঞ্জস্যপূর্ণ: camelCase (componentEventBus, modelBranding, secureSse) বনাম kebab (cache.manager, llm.router) — kebab-case-এ স্ট্যান্ডার্ডাইজ প্রস্তাব।
- lib/cache.manager.ts ব্রাউজার বান্ডেলে @upstash/redis (সার্ভার-সাইড) টেনে আনে — services/costOptimizer.service একমাত্র ইমপোর্টার; backend/shared প্যাকেজে সরান।
- PWA ম্যানিফেস্ট ভাঙা: manifest.json রেফারেন্স /favicon.ico, logo-192.png, logo-512.png — public/-এ এগুলো নেই (শুধু favicon.svg, icons.svg)।
- package.json ডিপ-সংঘর্ষ: Storybook 8.6 + 10.5 অ্যাডন মিশ্রিত, reactflow v11 + @xyflow/react v12 ডুপ্লিকেট, react-i18next অব্যবহৃত — এক ভার্সনে নামিয়ে আনুন।


---

## ব্যাচ ১২ — Repository Scripts (CI, DevOps, Analysis)
**ব্যাচ:** 12 | **তালিকাভুক্ত:** 257 | **বিশ্লেষিত:** 257 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 31 | **স্থানান্তর প্রস্তাব:** 87 (আসল মুভ ২৪ + আর্কাইভ/ডিলিট ৬৩) | **⚠️ সেমান্টিক মিসম্যাচ:** 13

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| _INDEX.md | scripts/_INDEX.md | scripts-এর AI-ইনডেক্স ডক; একটি রেফারেন্স স্টেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_capability_registry_sync.py | scripts/advanced_analysis/ | AST দিয়ে এজেন্ট-ক্লাস আবিষ্কার, রেজিস্ট্রি ক্রস-চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| api_contract_diff.py | scripts/advanced_analysis/ | ব্যাকএন্ড রুট বনাম ফ্রন্টএন্ড কল মিসম্যাচ ডিফ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bengali_i18n_completeness_checker.py | scripts/advanced_analysis/ | en/bn অনুবাদ কী তুলনায় গ্যাপ খোঁজে | i18n_completeness_checker.py | অপরিবর্তিত ✅ | নাম দীর্ঘ; ভাষা-নিরপেক্ষ সংক্ষিপ্ত রূপ |
| circular_import_mapper.py | scripts/advanced_analysis/ | import গ্রাফ + Tarjan SCC সার্কুলার-ডিপেন্ডেন্সি রিপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| config_single_source_enforcer.py | scripts/advanced_analysis/ | Settings-whitelist বনাম হার্ডকোডেড কনফিগ স্ক্যান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| db_model_drift_checker.py | scripts/advanced_analysis/ | ORM মডেল বনাম Alembic/SQL স্কিমা-ড্রিফট চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| dead_code_verified_finder.py | scripts/advanced_analysis/ | import-গ্রাফ BFS রিচেবিলিটিতে ডেড কোড শনাক্ত | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (ক্যানোনিকাল) |
| dependency_freshness_radar.py | scripts/advanced_analysis/ | লকফাইল/git থেকে ডিপেন্ডেন্সি বয়স রিপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| duplicate_detector.py | scripts/advanced_analysis/ | মাল্টি-ইঞ্জিন exact/near/structural ডুপ্লিকেট ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (ক্যানোনিকাল) |
| duplicate_logic_detector.py | scripts/advanced_analysis/ | AST-স্ট্রাকচারাল ডুপ্লিকেট ফাংশন/ক্লাস খোঁজে | অপরিবর্তিত ✅ | scripts/_archive/ | duplicate_detector-এর সাবসেট; একীভূত করুন |
| endpoint_timeout_auditor.py | scripts/advanced_analysis/ | রুট-হ্যান্ডলারে external-call timeout অডিট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| env_var_reconciler.py | scripts/advanced_analysis/ | env var ghost/orphan declaration-মিল যাচাই | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| error_handling_consistency_checker.py | scripts/advanced_analysis/ | রুট-হ্যান্ডলারে error-handling সামঞ্জস্য AST চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| hardcode_config_scanner.py | scripts/advanced_analysis/ | হার্ডকোডেড ডোমেইন স্ক্যানার (১০২ লাইন) | অপরিবর্তিত ✅ | scripts/_archive/ | ci/check_hardcoded_deployment_config-এর ডুপ্লিকেট |
| importer_graph.py | scripts/advanced_analysis/ | AST-ভিত্তিক নির্ভুল importer-count গ্রাফ ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| llm_cost_projector.py | scripts/advanced_analysis/ | কোডবেস বিশ্লেষণে মাসিক LLM খরচ প্রজেকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| migration_safety_diff.py | scripts/advanced_analysis/ | বিস্তারিত Alembic মাইগ্রেশন ঝুঁকি-ডিফ টুল | অপরিবর্তিত ✅ | scripts/_archive/ | scripts/ci/ কপির প্রায়-ডুপ্লিকেট; একটি রাখুন |
| orphan_route_finder.py | scripts/advanced_analysis/ | ব্যাকএন্ড রুট বনাম ফ্রন্টএন্ড কল orphan খোঁজে | অপরিবর্তিত ✅ | scripts/_archive/ | api_contract_diff-এর সাথে ফিচার-ওভারল্যাপ |
| pydantic_schema_consistency_checker.py | scripts/advanced_analysis/ | Pydantic মডেল/রুট/TS টাইপ ড্রিফট যাচাই | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| secret_rotation_reminder.py | scripts/advanced_analysis/ | secrets_registry থেকে রোটেশন-বয়স রিমাইন্ডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_coverage_gap_mapper.py | scripts/advanced_analysis/ | মডিউল-ভিত্তিক টেস্ট-কভারেজ গ্যাপ ম্যাপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/ai/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bias_detector.py | scripts/ai/ | AI মডেলে bias/fairness মেট্রিক বিশ্লেষণ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| feature_store_sync.py | scripts/ai/ | ফিচার-স্টোর সিঙ্ক (জেনেরিক টেমপ্লেট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| memory_read.py | scripts/ai/ | Supabase সেমান্টিক মেমরি রিকল CLI | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| memory_write.py | scripts/ai/ | সেশন-লার্নিং vector হিসেবে Supabase-এ সেভ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| model_drift_detector.py | scripts/ai/ | বেসলাইন বনাম বর্তমান পারফরম্যান্স ড্রিফ্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| model_version_manager.py | scripts/ai/ | মডেল ভার্সনিং ও রোলব্যাক ম্যানেজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| prompt_injection_tester.py | scripts/ai/ | LLM প্রম্পট-ইনজেকশন দুর্বলতা টেস্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| audit_env_usage.py | scripts/ | env var বনাম secrets_registry ক্রিটিকালিটি অডিট | অপরিবর্তিত ✅ | scripts/advanced_analysis/ | env-অডিট পরিবারের সাথে একত্র |
| audit_observability.py | scripts/ | silent except/print স্ক্যান (ছোট সংস্করণ) | অপরিবর্তিত ✅ | scripts/_archive/ | detect_silent_errors.py-ই ক্যানোনিকাল ডুপ্লিকেট |
| auto_fix_silent_excepts.py | scripts/ | except:pass ব্লক অটো-রিরাইটার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| __init__.py | scripts/backup/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_cross_cloud_replicate.py | scripts/backup/ | Firestore→সেকেন্ডারি ক্লাউড DR রেপ্লিকেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_firestore_backup.py | scripts/backup/ | Firestore export → GCS ব্যাকআপ + রোটেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| backup_telegram.py | scripts/backup/ | এনক্রিপ্টেড zero-knowledge ব্যাকআপ Telegram-এ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| create_desktop_backup.py | scripts/backup/ | ডেস্কটপ আর্কাইভ + AI-digest/ডিফ প্যাচ জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| superai_backup_manager.py | scripts/backup/ | DB/env/code/Redis ব্যাকআপ+রিস্টোর ম্যানেজার | backup_manager.py ⚠️ | অপরিবর্তিত ✅ | মানুষিক টুলে ব্র্যান্ড-প্রিফিক্স অপ্রয়োজনীয় |
| __init__.py | scripts/benchmark/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| perf_benchmark.py | scripts/benchmark/ | API লেটেন্সি/থ্রুপুট হালকা বেঞ্চমার্ক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| superai_load_tester.py | scripts/benchmark/ | LLM এন্ডপয়েন্ট লোড/স্ট্রেস টেস্টার | load_tester.py ⚠️ | অপরিবর্তিত ✅ | ব্র্যান্ড-প্রিফিক্স অপসারণ |
| __init__.py | scripts/billing/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| fraud_detector.py | scripts/billing/ | লেজার বিশ্লেষণে বিলিং ফ্রড অ্যানোমালি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| quota_enforcer.py | scripts/billing/ | টেন্যান্ট কোটা এনফোর্সমেন্ট ও অটো-সাসপেন্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| usage_reporter.py | scripts/billing/ | টেন্যান্ট ব্যবহার-রিপোর্ট (JSON/Markdown) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/bots/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_alert_bot.py | scripts/bots/ | Discord/Slack সিস্টেম-অ্যালার্ট বট | অপরিবর্তিত ✅ | scripts/_archive/ | ডকস্ট্রিং-বর্ণিত DEPRECATED; ডিলিট প্রস্তাব |
| auto_daily_standup_bot.py | scripts/bots/ | দৈনিক স্ট্যান্ডআপ সামারি পোস্টার | অপরিবর্তিত ✅ | scripts/_archive/ | DEPRECATED; Admin Center-এ স্থানান্তরিত |
| check_actions.py | scripts/ | GitHub Actions ভার্সন যাচাইকারী ছোট হেল্পার | অপরিবর্তিত ✅ | scripts/ci/ | Actions-হেল্পার ci/-তে যায় |
| check_app_boots.sh | scripts/ | push-এর আগে backend বুট-টেস্ট গার্ড | অপরিবর্তিত ✅ | scripts/ci/ | CI/push-gate পরিবারে যায় |
| check_no_requests_in_backend.sh | scripts/ | backend-এ requests-ইমপোর্ট ব্লককারী CI গার্ড | অপরিবর্তিত ✅ | scripts/ci/ | CI গার্ড পরিবারে যায় |
| checkpoint_update.py | scripts/ | git commit-এ CHECKPOINT.md অটো-আপডেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| README-config-registry-migration.md | scripts/ci/ | রেজিস্ট্রি-মাইগ্রেশন ইভিডেন্স ওয়ার্কফ্লো নির্দেশিকা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/ci/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_deploy.sh | scripts/ci/ | Google Cloud Run অটো-ডিপ্লয় স্ক্রিপ্ট | auto-deploy.sh | scripts/deploy/ | kebab-case; ডিপ্লয় স্ক্রিপ্ট deploy/-তে |
| check_config_contract.py | scripts/ci/ | ক্যানোনিকাল রেজিস্ট্রি বনাম runtime অ্যালায়েস গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_config_control_plane.py | scripts/ci/ | কনফিগ কন্ট্রোল-প্লেন কন্ট্রাক্ট স্ট্রাকচারাল গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_database_schema.py | scripts/ci/ | লাইভ DB বনাম schema_contract.yaml ডিফ গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_free_tier_limits.py | scripts/ci/ | ফ্রি-টায়ার সাইজ-লিমিট pre-commit/nightly গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_frontend_secrets.py | scripts/ci/ | VITE_ ভেরিয়েবলে সিক্রেট-কীওয়ার্ড গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_hardcoded_deployment_config.py | scripts/ci/ | হার্ডকোডেড প্রোডাকশন হোস্টনেম স্ক্যান গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_migration_safety.py | scripts/ci/ | Alembic destructive-অপ চেক (CI fail) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_required_secrets.py | scripts/ci/ | CI-তে প্রয়োজনীয় সিক্রেট উপস্থিতি যাচাই | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_service_topology.py | scripts/ci/ | workflow env বনাম topology manifest মিল গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| config_registry_evidence.py | scripts/ci/ | রানটাইম অ্যালায়েস ইভিডেন্স রিপোর্ট জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| coverage_policy.yaml | scripts/ci/ | কভারেজ থ্রেশহোল্ড পলিসি (PR/critical) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| coverage_quality_gate.py | scripts/ci/ | coverage_policy অনুযায়ী কভারেজ গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| deploy.sh | scripts/ci/ | ৯ লাইনের খালি প্লেসহোল্ডার ডিপ্লয় | অপরিবর্তিত ✅ | scripts/_archive/ | প্লেসহোল্ডার; ডিলিট প্রস্তাব |
| generate_changelog.sh | scripts/ci/ | প্লেসহোল্ডার চেঞ্জলগ স্ক্রিপ্ট | অপরিবর্তিত ✅ | scripts/_archive/ | প্লেসহোল্ডার; ডিলিট প্রস্তাব |
| migration_safety_diff.py | scripts/ci/ | মাইগ্রেশন সেফটি ডিফ (বিস্তারিত ক্যানোনিকাল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| run_tests.sh | scripts/ci/ | ruff+mypy+pytest রানার | run-tests.sh | অপরিবর্তিত ✅ | .sh ফাইলে kebab-case কনভেনশন |
| update_ci_comments.py | scripts/ci/ | ci.yml-এ কমেন্ট-ইনজেক্টর (একবারই প্রয়োগ) | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| validate_config_registry.py | scripts/ci/ | কনফিগ রেজিস্ট্রি PR-টাইম স্ট্রাকচারাল গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| validate_frontend_build.py | scripts/ci/ | dist/ বিল্ডে URL/সিক্রেট লিক স্ক্যান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| validate_router_imports.py | scripts/ci/ | দ্রুত in-process রাউটার import স্মোক-টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| verify_api_contract.py | scripts/ci/ | ব্যাকএন্ড রুট বনাম ফ্রন্টএন্ড কল ভেরিফায়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| clean_flutter_build.dart | scripts/ | Flutter বিল্ড-আর্টিফ্যাক্ট ক্লিনার (apps/mobile) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cloudflare_worker.test.mjs | scripts/ | Worker circuit-breaker Miniflare e2e টেস্ট | অপরিবর্তিত ✅ | scripts/testing/ | টেস্ট ফাইল testing/-এ স্থানান্তর |
| codegraph_integration.py | scripts/ | কোডবেস নলেজ-গ্রাফ জেনারেটর + CI হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/core_engine/ | খালি init; ডির ভাঙার প্রস্তাব | অপরিবর্তিত ✅ | ডিলিট | ডিরেক্টরি বিলুপ্ত হচ্ছে |
| multicatalog_search.py | scripts/core_engine/ | সব রিসোর্স-ক্যাটালগে ইউনিফাইড সার্চ ইঞ্জিন | অপরিবর্তিত ✅ | scripts/resource_collection/ | রিসোর্স-কালেকশন পরিবারেরই অংশ |
| tool_ranker.py | scripts/core_engine/ | জনপ্রিয়তা/কোয়ালিটি-ভিত্তিক টুল র‍্যাংকার | অপরিবর্তিত ✅ | scripts/resource_collection/ | multicatalog_search-এর সাথে একত্র |
| __init__.py | scripts/db/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_migrate.py | scripts/db/ | Alembic মাইগ্রেশন রানার (startup/CI) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_seed.py | scripts/db/ | ডিফল্ট ডেটা/অ্যাডমিন সিডার (idempotent) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ingest_knowledge.py | scripts/db/ | knowledge ইনজেকশন পাইপলাইন (pgvector) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| load_coldstart_knowledge.py | scripts/db/ | cold-start knowledge ChromaDB লোডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| run_migration.py | scripts/db/ | phase3 SQL মাইগ্রেশন এককালীন রানার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| validate_retrieval.py | scripts/db/ | retrieval gold-set hit@k ভ্যালিডেশন গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/deploy/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| add_secrets_to_infisical.py | scripts/deploy/ | Infisical-এ সিক্রেট আপসার্ট (হার্ডকোডেড ক্রেড) | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন; হার্ডকোডেড ক্রেডেনশিয়াল |
| blue_green_deploy.py | scripts/deploy/ | ব্লু/গ্রিন zero-downtime ডিপ্লয় স্ক্রিপ্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| canary_deploy.py | scripts/deploy/ | ক্যানারি ধাপে ধাপে রোলআউট ম্যানেজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_render.py | scripts/deploy/ | নির্দিষ্ট সার্ভিসের Render deploy-স্টেটাস চেক | render_status.py | অপরিবর্তিত ✅ | ৩টি টুইন একটি render_status-এ মার্জ |
| check_render_auto_deploy.py | scripts/deploy/ | Render সার্ভিস স্টেটাস চেক (টুইন) | অপরিবর্তিত ✅ | scripts/_archive/ | check_render-এর ডুপ্লিকেট; মার্জ/ডিলিট |
| check_render_svc.py | scripts/deploy/ | Render সার্ভিস JSON ডাম্পার (টুইন) | অপরিবর্তিত ✅ | scripts/_archive/ | ডুপ্লিকেট টুইন; মার্জ/ডিলিট |
| create_render_service.py | scripts/deploy/ | এককালীন Render সার্ভিস-তৈরি স্ক্রিপ্ট | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| disaster_recovery_test.py | scripts/deploy/ | DR টেস্ট-প্রসিডিউর অটোমেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| generate_firebase_config.py | scripts/deploy/ | টেমপ্লেট থেকে deterministic firebase config | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| infrastructure_as_code_validator.py | scripts/deploy/ | Terraform/CloudFormation ভ্যালিডেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| list_render_services.py | scripts/deploy/ | Render সার্ভিস লিস্টার (এককালীন) | অপরিবর্তিত ✅ | scripts/_archive/ | render_status টুলে মার্জযোগ্য |
| superai_quick_deploy.sh | scripts/deploy/ | one-click ফুল ডিপ্লয় (build+health+rollback) | quick-deploy.sh ⚠️ | অপরিবর্তিত ✅ | ব্র্যান্ড-প্রিফিক্স + kebab-case |
| trigger_render_deploy.py | scripts/deploy/ | Render deploy ট্রিগারার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| update_infisical_render.py | scripts/deploy/ | Infisical ক্রেড দিয়ে সিক্রেট আপডেটার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন; হার্ডকোডেড ক্রেডেনশিয়াল |
| update_render_env2.py | scripts/deploy/ | Render env-var আপডেটার (সংখ্যাযুক্ত নাম) | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| update_render_image.py | scripts/deploy/ | Render image-mode সেটার (এককালীন) | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| deploy_cloud_mesh.sh | scripts/ | GCP/Cloudflare মাল্টি-ক্লাউড ডিপ্লয় | deploy-cloud-mesh.sh | scripts/deploy/ | kebab-case; ডিপ্লয় ফ্যামিলিতে |
| detect_silent_errors.py | scripts/ | stdlib silent-error স্ক্যানার (CI-ওয়্যার্ড) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (ক্যানোনিকাল) |
| refactor_scanner_fixes.py | scripts/dev/ | import/bare-except এককালীন ফিক্সার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| __init__.py | scripts/devops/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bug_prophet.py | scripts/devops/ | AST+AI বাগ-প্রেডিকশন PR-রিভিউ এজেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | এজেন্ট-পারসোনা নাম; অবস্থান ঠিক |
| cloud_watchman.py | scripts/devops/ | মাল্টি-ক্লাউড কোটা/বিল/এরর মনিটর এজেন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cli.py | scripts/devops/config/ | SuperAI Config Validator CLI | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| models.py | scripts/devops/config/ | ভ্যালিডেশন রেজাল্ট মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rules.py | scripts/devops/config/ | কনফিগ ভ্যালিডেশন নিয়মাবলি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| validators.py | scripts/devops/config/ | কম্প্রিহেনসিভ কনফিগ ভ্যালিডেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| devops_ai_scribe.py | scripts/devops/ | LLM দিয়ে docstring/readme জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| devops_security_scan.py | scripts/devops/ | স্টেজড-ফাইল ফাস্ট সিক্রেট স্ক্যানার (মার্জড) | fast_secret_scan.py | অপরিবর্তিত ✅ | মার্জে ডুপ্লিকেট main; কাজ সিক্রেট-স্ক্যান |
| fix_eslint_any.py | scripts/devops/ | eslint any-টাইপ এককালীন অটো-ফিক্স | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| fix_mypy.py | scripts/devops/ | mypy এরর এককালীন অটো-ফিক্সার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| generate_modular_audits.py | scripts/devops/ | AI-অডিটরের জন্য ১৪+ মডুলার অডিট MD | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| get_slug.py | scripts/devops/ | Infisical slug আনার এককালীন স্ক্রিপ্ট | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন; হার্ডকোডেড ক্রেডেনশিয়াল |
| refactor_wiz.py | scripts/devops/ | টেক-ডেট মেট্রিক্স + AI রিফ্যাক্টর প্ল্যানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | এজেন্ট-পারসোনা নাম; অবস্থান ঠিক |
| run_local_audit.py | scripts/devops/ | Ollama/ফ্রি API দিয়ে লোকাল অডিট রানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| todo_manager.py | scripts/devops/ | TODO/FIXME স্ক্যান-ট্র্যাক-রিপোর্ট টুল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| update_secret.py | scripts/devops/ | Infisical সিক্রেট আপডেট (এককালীন) | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন; হার্ডকোডেড ক্রেডেনশিয়াল |
| update_vault.py | scripts/devops/ | Infisical vault আপডেট (এককালীন) | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন; হার্ডকোডেড ক্রেডেনশিয়াল |
| upload_infisical.py | scripts/devops/ | .env → Infisical আপলোডার (এককালীন) | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন; হার্ডকোডেড ক্রেডেনশিয়াল |
| __init__.py | scripts/diagnostics/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| superai_console_detective.py | scripts/diagnostics/ | কনসোল-লগ হিউম্যান-স্টাইল এরর হান্টার | console_detective.py ⚠️ | অপরিবর্তিত ✅ | ব্র্যান্ড-প্রিফিক্স অপসারণ |
| BROWSER_CROWN_JEWEL_INTEGRATION_GUIDE.md | scripts/docs/ | CommandCenter-এ ব্রাউজার প্যাচ (diff ফরম্যাট) | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন প্যাচ-ডক, আর্কাইভ/ডিলিট |
| CONSOLE_DETECTIVE_README.md | scripts/docs/ | Console Detective টুলের ব্যবহার-গাইড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টুলের সাথে সংশ্লিষ্ট ডক |
| __init__.py | scripts/docs/ | ডক-ফোল্ডারে অপ্রয়োজনীয় খালি init | অপরিবর্তিত ✅ | ডিলিট | ডক্স প্যাকেজ নয়; init দরকার নেই |
| auto_adr_generator.py | scripts/docs/ | PR-বর্ণনা থেকে ADR অটো-জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_api_doc_sync.py | scripts/docs/ | OpenAPI → docs/ Markdown সিঙ্কার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_readme_update.py | scripts/docs/ | রাউট স্ক্যান করে README API-টেবিল আপডেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/evolution/ | এক-ফাইলের evolution প্যাকেজ init | অপরিবর্তিত ✅ | ডিলিট | ডিরেক্টরি বিলুপ্ত হচ্ছে |
| auto_marketing_skill_forge.py | scripts/evolution/ | Firestore মনিটর করে মার্কেটিং স্কিল ফোর্জ | marketing_skill_forge.py | scripts/automation/ | "evolution" ডির ভুল; অটোমেশন ফ্যামিলি |
| find_stub_data.py | scripts/ | stub/placeholder স্ক্যান করে CI fail করায় | অপরিবর্তিত ✅ | scripts/ci/ | CI গেট পরিবারে যায় |
| fix_backend.py | scripts/ | নির্দিষ্ট ফাইল-লিস্টে এককালীন প্যাচার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| fix_cancelled_errors.py | scripts/ | CancelledError-handling এককালীন ফিক্সার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন; Windows F:\ হার্ডকোডেড পাথ |
| fix_scripts.py | scripts/ | ৪টি স্ক্রিপ্টে এককালীন প্যাচ | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| fix_scripts_2.py | scripts/ | ai/billing স্ক্রিপ্টে sys.path ইনজেক্টর | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| fix_time_sleep.py | scripts/ | অ্যাসিঙ্কে time.sleep→asyncio.sleep কনভার্টার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| fix_urls.py | scripts/ | রেন্ডার ডোমেইন এককালীন রিরাইটার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| free-tier-health-check.sh | scripts/ | ফ্রি-টায়ার লিমিট ডেইলি হেলথ-চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম (kebab) ও অবস্থান উপযুক্ত |
| generate_api_health_report.py | scripts/ | FastAPI অ্যাপ থেকে হেলথ-রিপোর্ট জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| generate_openapi.py | scripts/ | অ্যাপ থেকে OpenAPI স্কিমা → YAML | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| generate_types.py | scripts/ | Pydantic → TS/Dart টাইপ জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| get_shas.py | scripts/ | GitHub Actions pinned-SHA সংগ্রাহক | get_action_shas.py | scripts/ci/ | নাম অস্পষ্ট; Actions-হেল্পার ci/-তে |
| __init__.py | scripts/git/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pre-push | scripts/git/ | SyncGuard অডিট pre-push হুক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/health/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_system_health.py | scripts/health/ | ক্যানোনিকাল হেলথ-চেক (ডুপ্লিকেট-প্রতিস্থাপক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cleanup_duplicate_health_scripts.sh | scripts/health/ | ডুপ্লিকেট হেলথ-স্ক্রিপ্ট মুভার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| superai_health_check.py | scripts/health/ | বৃহৎ কম্প্রিহেনসিভ হেলথ/ডায়াগনস্টিক সুইট | system_health_check.py ⚠️ | scripts/_archive/ | check_system_health-এর ডুপ্লিকেট; মার্জ করুন |
| __init__.py | scripts/i18n/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bangla_translator.py | scripts/i18n/ | UI/কনটেন্ট বাংলা অনুবাদ টুল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| banglish_converter.py | scripts/i18n/ | Banglish↔বাংলা কনভার্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| rtl_support_checker.py | scripts/i18n/ | CSS/HTML RTL-সাপোর্ট ভ্যালিডেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/k6/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| load_test.js | scripts/k6/ | k6 স্টেজড লোড-টেস্ট স্ক্রিপ্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/kaggle/ | খালি; কোনো মডিউল নেই | অপরিবর্তিত ✅ | ডিলিট | অব্যবহৃত খালি প্যাকেজ |
| keepalive.js | scripts/ | Render backend ৫ মিনিট পরপর পিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/maintenance/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cleanup.py | scripts/maintenance/ | ব্যাকআপ .env থেকে কী-মুছে ফেলা | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন; হার্ডকোডেড F:\ পাথ |
| create_issue.py | scripts/maintenance/ | ভালনারেবিলিটি রিপোর্ট থেকে GitHub issue | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| notify.py | scripts/maintenance/ | Telegram অ্যালার্ট নোটিফায়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/monitoring/ | প্যাকেজ-ডকস্ট্রিংসহ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| capacity_planner.py | scripts/monitoring/ | অটো-স্কেলিং ক্যাপাসিটি প্ল্যানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cost_analyzer.py | scripts/monitoring/ | মাল্টি-ক্লাউড/AI খরচ বিশ্লেষণ+ফোরকাস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sla_tracker.py | scripts/monitoring/ | SLO/SLI কমপ্লায়েন্স ট্র্যাকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| superai_console_capture.js | scripts/monitoring/ | DevTools কনসোল-ক্যাপচার স্নিপেট | console_capture.js ⚠️ | scripts/diagnostics/ | ব্র্যান্ড অপসারণ; console_detective পরিবারে |
| superai_console_detective.html | scripts/monitoring/ | টুলবিহীন কনসোল এরর-হান্টার UI | console_detective.html ⚠️ | scripts/diagnostics/ | ব্র্যান্ড অপসারণ; ডায়াগনস্টিক পরিবারে |
| superai_cpu_monitor.py | scripts/monitoring/ | রিয়েল-টাইম CPU/মেমরি মনিটর ড্যাশবোর্ড | cpu_monitor.py ⚠️ | অপরিবর্তিত ✅ | ব্র্যান্ড-প্রিফিক্স অপসারণ |
| superai_log_analyzer.py | scripts/monitoring/ | লগ বিশ্লেষণ+অ্যালার্ট ইঞ্জিন | log_analyzer.py ⚠️ | অপরিবর্তিত ✅ | ব্র্যান্ড-প্রিফিক্স অপসারণ |
| multi_model_validator.py | scripts/ | AST+মাল্টি-মডেল কোড সেফটি ভ্যালিডেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/orchestrator/ | এক-ফাইলের প্যাকেজ init | অপরিবর্তিত ✅ | ডিলিট | ডিরেক্টরি বিলুপ্ত হচ্ছে |
| auto_budget_guardian.py | scripts/orchestrator/ | AI প্রোভাইডার কোটা ৮০%-এ অটো-পজ | budget_guardian.py | scripts/monitoring/ | বাজেট-মনিটরিং monitoring/-এই শোভে |
| organize_tests.sh | scripts/ | backend/tests ফাইল git mv করে সাজায় | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| CROWN_JEWEL_BROWSER_PATCH.md | scripts/patches/ | ব্রাউজার কম্পোনেন্ট রিরাইট প্যাচ-ডক | অপরিবর্তিত ✅ (⚠️) | scripts/_archive/ | এককালীন প্যাচ-ডক, আর্কাইভ/ডিলিট |
| __init__.py | scripts/patches/ | খালি init | অপরিবর্তিত ✅ | ডিলিট | ডিরেক্টরি বিলুপ্ত হচ্ছে |
| pre_commit_hook.py | scripts/ | commit-এ lessons/checkpoint/Actions গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| prune_cache.sh | scripts/ | ৭ দিনের পুরনো GH Actions cache প্রুনার | prune-cache.sh | scripts/ci/ | kebab-case; Actions-হেল্পার ci/-তে |
| __init__.py | scripts/quality/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_dead_code_remover.py | scripts/quality/ | vulture+radon ডেড-কোড/কমপ্লেক্সিটি রিপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_improve_coverage.py | scripts/quality/ | কভারেজ-গ্যাপে অটো টেস্ট-জেনারেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_refactor_suggester.py | scripts/quality/ | হিউরিস্টিক রিফ্যাক্টর-সাজেশন জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_ollama_test_coverage.py | scripts/quality/ | Ollama টেস্ট-জেন পরীক্ষা (গ্যার্বলড টেক্সট) | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন এক্সপেরিমেন্ট, আর্কাইভ/ডিলিট |
| docs_drift_check.py | scripts/quality/ | ট্র্যাকিং-ডকের claim বনাম repo-state যাচাই | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| regression_scanner.py | scripts/quality/ | প্রজেক্ট-নির্দিষ্ট পুনরাবৃত্ত বাগ-প্যাটার্ন স্ক্যানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| self_audit_scan.py | scripts/quality/ | stdlib AST জেনেরিক বাগ/সিক্রেট স্ক্যানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/refactor/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| move_core_modules.py | scripts/refactor/ | git mv + shim সহ নিরাপদ মডিউল-মুভার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| moves_p1b.json | scripts/refactor/ | billing/email/storage মুভ-ম্যানিফেস্ট (প্রয়োগৃত) | অপরিবর্তিত ✅ | scripts/_archive/ | প্রয়োগ-সম্পন্ন মাইগ্রেশন ম্যানিফেস্ট |
| moves_p1c.json | scripts/refactor/ | error-family মুভ-ম্যানিফেস্ট (প্রয়োগৃত) | অপরিবর্তিত ✅ | scripts/_archive/ | প্রয়োগ-সম্পন্ন মাইগ্রেশন ম্যানিফেস্ট |
| moves_p1d.json | scripts/refactor/ | db-repository family মুভ-ম্যানিফেস্ট | অপরিবর্তিত ✅ | scripts/_archive/ | প্রয়োগ-সম্পন্ন মাইগ্রেশন ম্যানিফেস্ট |
| moves_p2a.json | scripts/refactor/ | logging/metrics মুভ-ম্যানিফেস্ট (প্রয়োগৃত) | অপরিবর্তিত ✅ | scripts/_archive/ | প্রয়োগ-সম্পন্ন মাইগ্রেশন ম্যানিফেস্ট |
| moves_p2b.json | scripts/refactor/ | middleware family মুভ-ম্যানিফেস্ট | অপরিবর্তিত ✅ | scripts/_archive/ | প্রয়োগ-সম্পন্ন মাইগ্রেশন ম্যানিফেস্ট |
| moves_p3.json | scripts/refactor/ | llm_router মুভ-ম্যানিফেস্ট (প্রয়োগৃত) | অপরিবর্তিত ✅ | scripts/_archive/ | প্রয়োগ-সম্পন্ন মাইগ্রেশন ম্যানিফেস্ট |
| rewrite_shims.py | scripts/refactor/ | eager shim → lazy PEP 562 shim রিরাইটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| superai_transform.py | scripts/refactor/ | SupremeAI→SuperAI ব্র্যান্ড ট্রান্সফর্মার | অপরিবর্তিত ✅ (⚠️) | scripts/_archive/ | এককালীন ব্র্যান্ডিং ট্রান্সফর্ম; ডিলিট |
| render_build_backend.sh | scripts/ | Poetry ইনস্টল+বিল্ড (Render backend) | render-build-backend.sh | scripts/deploy/ | kebab-case; Render ডিপ্লয় ফ্যামিলি |
| render_build_frontend.sh | scripts/ | ফ্রন্টএন্ড বিল্ড+firebase প্লেসহোল্ডার রিপ্লেস | render-build-frontend.sh | scripts/deploy/ | kebab-case; ডিপ্লয় ফ্যামিলি |
| __init__.py | scripts/resource_collection/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| api_clients.py | scripts/resource_collection/ | API-কালেকশনের BaseAPIClient বেস ক্লাস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/resource_collection/ossinsight/ | Ossinsight ক্লায়েন্ট প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| run_all.py | scripts/resource_collection/ | সব স্ক্র্যাপার চালানোর এন্ট্রি-পয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| run_all_collectors.py | scripts/resource_collection/ | ১ লাইনের ভাঙা রিডাইরেক্ট | অপরিবর্তিত ✅ | scripts/_archive/ | ভাঙা রিডাইরেক্ট; ডিলিট প্রস্তাব |
| scrapers.py | scripts/resource_collection/ | awesome-list স্ক্র্যাপার পরিবার (ABC) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (ক্যানোনিকাল) |
| __init__.py | scripts/resource_scraping/ | খালি init | অপরিবর্তিত ✅ | ডিলিট | ডিরেক্টরি বিলুপ্ত হচ্ছে |
| scrape.py | scripts/resource_scraping/awesome_go/ | awesome-go README স্ক্র্যাপার | অপরিবর্তিত ✅ | scripts/_archive/ | scrapers.py-তেই সমতুল্য ক্লাস আছে |
| scrape.py | scripts/resource_scraping/awesome_python/ | awesome-python README স্ক্র্যাপার | অপরিবর্তিত ✅ | scripts/_archive/ | scrapers.py-তেই সমতুল্য ক্লাস আছে |
| scrape.py | scripts/resource_scraping/awesome_selfhosted/ | awesome-selfhosted README স্ক্র্যাপার | অপরিবর্তিত ✅ | scripts/_archive/ | scrapers.py-তেই সমতুল্য ক্লাস আছে |
| rotate_lessons.py | scripts/ | LESSONS_LEARNED.md 12KB ক্যাপ এনফোর্সার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/runner/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| setup_runner.sh | scripts/runner/ | CI/লোকাল রানার এনভ-সেটআপ | setup-runner.sh | অপরিবর্তিত ✅ | kebab-case কনভেনশন |
| zero_cost_optimizer.sh | scripts/runner/ | ডকার/মেমরি ক্যাশ প্রুনিং (zero-cost) | zero-cost-optimizer.sh | অপরিবর্তিত ✅ | kebab-case কনভেনশন |
| safety_guard.py | scripts/ | ক্রিটিক্যাল ফাইলে AI-এজেন্ট চেঞ্জ গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/security/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| audit_log_analyzer.py | scripts/security/ | অডিট-লগ SIEM অ্যানোমালি+অ্যালার্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_find_blindspots.py | scripts/security/ | blindspot-ডকভিত্তিক সিকিউরিটি স্ক্যানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_secret_rotate.py | scripts/security/ | GCP Secret Manager রোটেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_vulnerability_scanner.py | scripts/security/ | CVE/SAST/secret/SBOM স্ক্যানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_dependencies.py | scripts/security/ | pnpm/poetry ডিপেন্ডেন্সি ভালনারেবিলিটি চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (ডকস্ট্রিং পাথ স্টেল) |
| code-quality.yml | scripts/security/ | উইকলি কোয়ালিটি GitHub workflow | অপরিবর্তিত ✅ | .github/workflows/ | workflow ফাইল workflows/-এ থাকবে |
| dependency-health-check.yml | scripts/security/ | ডিপেন্ডেন্সি হেলথ GitHub workflow | অপরিবর্তিত ✅ | .github/workflows/ | workflow ফাইল workflows/-এ থাকবে |
| find_dead_code.py | scripts/security/ | vulture-র‍্যাপার ডেড-কোড ফাইন্ডার | অপরিবর্তিত ✅ | scripts/_archive/ | অন্য দুটি ডেড-কোড টুলের ডুপ্লিকেট |
| generate_secrets.py | scripts/security/ | .env-এ সিক্রেট জেনারেটর (F:\ পাথ) | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন; হার্ডকোডেড Windows পাথ |
| secrets_rotation_manager.py | scripts/security/ | Infisical+zero-downtime সিক্রেট রোটেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| setup-git-hooks.sh | scripts/ | pre-push/pre-commit হুক ইনস্টলার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম (kebab) ও অবস্থান উপযুক্ত |
| setup_kms.sh | scripts/ | লোকাল Fernet কী জেনারেটর | setup-kms.sh | অপরিবর্তিত ✅ | kebab-case কনভেনশন |
| silent_errors_baseline.json | scripts/ | silent-error স্ক্যানের বেসলাইন ফাইন্ডিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| supreme_ops.py | scripts/ | অপস-টাস্কের ইউনিফাইড CLI ডিসপ্যাচার | ops_cli.py ⚠️ | অপরিবর্তিত ✅ | ব্র্যান্ড-প্রিফিক্স অপসারণ |
| supremeai_performance_benchmark.py | scripts/ | ক্যাশ/tracker ব্যাকএন্ড বেঞ্চমার্ক | backend_cache_benchmark.py ⚠️ | scripts/benchmark/ | ব্র্যান্ড অপসারণ; benchmark/ প্যাকেজে |
| __init__.py | scripts/supremeai_toolkit/ | খালি; কোনো মডিউল নেই | অপরিবর্তিত ✅ | ডিলিট | অব্যবহৃত খালি প্যাকেজ |
| __init__.py | scripts/tenant/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_tenant_health_report.py | scripts/tenant/ | টেন্যান্ট হেলথ/ব্যবহার রিপোর্ট জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auto_tenant_setup.py | scripts/tenant/ | নতুন টেন্যান্ট প্রভিশনিং অটোমেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | scripts/testenv/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| setup_test_env.sh | scripts/testenv/ | আইসোলেটেড টেস্ট-এনভ তৈরি | setup-test-env.sh | অপরিবর্তিত ✅ | kebab-case কনভেনশন |
| __init__.py | scripts/testing/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| _gen_services.py | scripts/testing/ | Pydantic স্কিমা থেকে সার্ভিস স্ক্যাফোল্ডার | service_scaffolder.py | অপরিবর্তিত ✅ | টেস্টিং নয়; underscore নাম অস্পষ্ট |
| alert_manager.py | scripts/testing/ | মাল্টি-চ্যানেল অ্যালার্টিং (SMS/Slack/PagerDuty) | অপরিবর্তিত ✅ | scripts/monitoring/ | অ্যালার্টিং টুল; টেস্টিং নয় |
| api_contract_validator.py | scripts/testing/ | OpenAPI কন্ট্রাক্ট/breaking-change ভ্যালিডেটর | অপরিবর্তিত ✅ | scripts/_archive/ | api_contract_diff+verify_api_contract-এ মার্জ |
| auto_test_generator.py | scripts/testing/ | LLM দিয়ে অটো টেস্ট-কেস জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| check_timing.py | scripts/testing/ | GH Actions রান-টাইম এককালীন চেকার | অপরিবর্তিত ✅ | scripts/_archive/ | এককালীন স্ক্রিপ্ট, আর্কাইভ/ডিলিট |
| log_anomaly_detector.py | scripts/testing/ | ML (IsolationForest/LSTM) লগ-অ্যানোমালি ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| mutation_testing.py | scripts/testing/ | mutation-testing ইঞ্জিন (AST মিউট্যান্ট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| performance_benchmark.py | scripts/testing/ | API/DB/LLM বেঞ্চমার্ক+লোড-টেস্ট সুইট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (ক্যানোনিকাল) |
| test_runners.py | scripts/testing/ | E2E ইন্টিগ্রেশন টেস্ট রানার | integration_test_runner.py | অপরিবর্তিত ✅ | নামে আসল দায়িত্ব (integration) নেই |
| test_security.py | scripts/testing/ | সিকিউরিটি অডিট+পেন-টেস্ট সুইট | security_audit.py | scripts/security/ | টেস্ট নয় — অডিট টুল; security/-তে |
| verify_capabilities.py | scripts/ | capability matrix ফাংশনাল টেস্ট গেট | অপরিবর্তিত ✅ | scripts/ci/ | push-gate পরিবারে যায় |
| __init__.py | scripts/worktrees/ | খালি প্যাকেজ init | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| run_task.sh | scripts/worktrees/ | worktree-তে আইসোলেটেড টাস্ক রানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| setup_worktree.sh | scripts/worktrees/ | প্যারালাল এজেন্ট worktree সেটআপ | setup-worktree.sh | অপরিবর্তিত ✅ | kebab-case কনভেনশন |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- **ব্র্যান্ড-প্রিফিক্স বিস্তর:** superai_/supremeai_/supreme_ প্রিফিক্স ১০+ মানুষিক স্ক্রিপ্টে (health check, cpu monitor, log analyzer, backup manager, load tester, console detective, ops CLI) — সবই ⚠️; superai_transform.py ব্র্যান্ড-পরিবর্তনকারী এককালীন স্ক্রিপ্ট হিসেবে নিজেই ডিলিটযোগ্য।
- **API-contract টুল ৪টি:** advanced_analysis/api_contract_diff, advanced_analysis/orphan_route_finder, ci/verify_api_contract, testing/api_contract_validator — api_contract_diff + verify_api_contract রেখে বাকি দুটি আর্কাইভ/মার্জ প্রস্তাব।
- **ফাংশনাল-ডুপ্লিকেট পরিবার:** ডেড-কোড ডিটেক্টর ৩টি, সিক্রেট-রোটেশন টুল ৩টি (auto_secret_rotate, secrets_rotation_manager, secret_rotation_reminder), হেলথ-চেক ২টি, silent-error স্ক্যানার ৩টি, বেঞ্চমার্ক/লোড-টেস্টার ৫টি — প্রতি পরিবারে ক্যানোনিকাল একটি রাখার প্রস্তাব।
- **হার্ডকোডেড ক্রেডেনশিয়াল:** ৬টি Infisical স্ক্রিপ্টে (deploy/ ও devops/-) একই clientId/clientSecret এমবেড করা — সবই এককালীন, ডিলিট প্রস্তাব; secrets_rotation_manager.py জেনেরিক বিকল্প।
- **one-off fix_ জঞ্জাল:** fix_backend, fix_urls, fix_scripts(_2), fix_time_sleep, fix_cancelled_errors, fix_mypy, fix_eslint_any, dev/refactor_scanner_fixes — ১২+ প্রয়োগ-সম্পন্ন প্যাচার; ৩টিতে Windows F:\ হার্ডকোডেড পাথ; সবই আর্কাইভ/ডিলিট প্রস্তাব।
- **ভুল স্থানে workflow:** security/code-quality.yml ও dependency-health-check.yml GitHub workflow ফাইল — .github/workflows/-এ স্থানান্তর প্রস্তাব।
- **kebab-case পরিষ্কার:** ১০টি .sh রিনেম (run_tests→run-tests, setup_kms→setup-kms ইত্যাদি); bots/-এর ২টি DEPRECATED স্ক্রিপ্ট এখনো বাতিল-অঘোষিতভাবে রয়ে গেছে।
- **খালি/ভাঙা প্যাকেজ:** kaggle/, supremeai_toolkit/ খালি; run_all_collectors.py অস্তিত্বহীন পাথে রিডাইরেক্ট; core_engine/, evolution/, orchestrator/, patches/, resource_scraping/ এক-উদ্দেশ্যের ডির — বিলুপ্ত/একত্র করার প্রস্তাব।


---

## ব্যাচ ১৩ — Tools, Packages ও Extensions
**ব্যাচ:** 13 | **তালিকাভুক্ত:** 239 | **বিশ্লেষিত:** 239 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 32 | **স্থানান্তর প্রস্তাব:** 16 | **⚠️ সেমান্টিক মিসম্যাচ:** 8

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| api-reference.md | apps/docs/docs | REST API এন্ডপয়েন্ট রেফারেন্স টেবিল (auth/health) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| bangla-guide.md | apps/docs/docs | বাংলা সম্পূর্ণ ইউজার গাইড (quick start) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| elai-code-extension-reference-bn.md | apps/docs/docs | eLai থার্ড-পার্টি এক্সটেনশন বিশ্লেষণ (বাংলা) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| elai-code-extension-reference.md | apps/docs/docs | eLai এক্সটেনশন বিশ্লেষণ (English) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| intro.md | apps/docs/docs | Docusaurus getting-started ভূমিকা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| docusaurus.config.ts | apps/docs | ডক সাইট কনফিগ (en+bn i18n) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| package.json | apps/docs | Docusaurus ডিপেন্ডেন্সি ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| sidebars.ts | apps/docs | ডক সাইডবার (শুধু intro) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| custom.css | apps/docs/src/css | Docusaurus কাস্টম স্টাইল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| package.json | packages/core-infrastructure | @supremeai/core-infrastructure ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| index.ts | packages/core-infrastructure/src | CircuitBreaker/ErrorHandler প্লেসহোল্ডার স্টাব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; কনটেন্ট ফাঁকা স্টাব |
| tsconfig.json | packages/core-infrastructure | TS কম্পাইলার কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| build.js | packages/design-tokens | Style Dictionary বিল্ড (css/dart/vscode) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| design-tokens.json | packages/design-tokens | লিগ্যাসি ফ্ল্যাট প্যালেট; tokens/-এর ডুপ্লিকেট সোর্স | tokens/legacy.json | packages/design-tokens/tokens/ | ডুপ্লিকেট টোকেন সোর্স একত্র করুন |
| variables.css | packages/design-tokens/outputs/css | জেনারেটেড CSS ভেরিয়েবল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড আর্টিফ্যাক্ট, নাম ঠিক |
| colors.dart | packages/design-tokens/outputs/flutter | জেনারেটেড Flutter AppColors | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | tokens.dart-এর সাথে হালকা ওভারল্যাপ |
| tokens.json | packages/design-tokens/outputs/json | জেনারেটেড ফ্ল্যাট JSON টোকেন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড আর্টিফ্যাক্ট, নাম ঠিক |
| tokens-vscode.css | packages/design-tokens/outputs | জেনারেটেড VS Code থিম CSS | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড আর্টিফ্যাক্ট, নাম ঠিক |
| tokens.css | packages/design-tokens/outputs | জেনারেটেড মূল টোকেন CSS | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড আর্টিফ্যাক্ট, নাম ঠিক |
| tokens.dart | packages/design-tokens/outputs | জেনারেটেড DesignTokens Dart | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড আর্টিফ্যাক্ট, নাম ঠিক |
| supremeai-theme.json | packages/design-tokens/outputs/vscode | জেনারেটেড VS Code থিম JSON | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড আর্টিফ্যাক্ট, নাম ঠিক |
| package.json | packages/design-tokens | @supremeai/design-tokens ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| copy-to-flutter.js | packages/design-tokens/scripts | tokens.dart → apps/mobile কপি স্ক্রিপ্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| admin.bn.json | packages/design-tokens/src | বাংলা-লেবেলড অ্যাডমিন রঙ প্যালেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| admin.json | packages/design-tokens/src | অ্যাডমিন রঙ প্যালেট (সোর্স) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| primitives.json | packages/design-tokens/tokens | প্রিমিটিভ কালার টোকেন (single source) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| semantic.json | packages/design-tokens/tokens | সেমান্টিক টোকেন ম্যাপিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vscode.json | packages/design-tokens/tokens | VS Code-নির্দিষ্ট টোকেন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| master_validator.py | packages/scripts | প্রোডাকশন রেডিনেস ভ্যালিডেটর (env/API) | অপরিবর্তিত ✅ | scripts/ | Python অপস-স্ক্রিপ্ট; packages/-এ নয় |
| security_guard.py | packages/scripts | pre-commit সিক্রেট-লিক স্ক্যানার | অপরিবর্তিত ✅ | scripts/ | রিপো-লেভেল হুক; packages/-এ নয় |
| test_security_guard.py | packages/scripts | security_guard প্যাটার্ন রিগ্রেশন টেস্ট | অপরিবর্তিত ✅ | scripts/tests/ | স্ক্রিপ্টের সাথে টেস্ট সরুন |
| package.json | packages/shared-services | @supremeai/shared-services ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| index.ts | packages/shared-services/src | ব্যারেল (services/platform/ui এক্সপোর্ট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| platform.ts | packages/shared-services/src | PlatformLogger/Notification/Prompt অ্যাবস্ট্র্যাকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| electron.ts | packages/shared-services/src/platform | Electron preload IPC অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vscode.ts | packages/shared-services/src/platform | vscode মডিউল→অ্যাবস্ট্র্যাকশন অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| BaseWebSocketManager.ts | packages/shared-services/src/realtime | রিকানেক্ট+হার্টবিট WebSocket বেস ক্লাস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CrossAiObserverService.ts | packages/shared-services/src/services | অন্য AI এজেন্ট শনাক্ত করে লার্নিং রিপোর্ট পাঠায় | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | হার্ডকোডেড Cloud Run URL কনফিগে আনুন |
| HealingStateManager.ts | packages/shared-services/src/services | self-healing স্টেট মেশিন (singleton) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| PerformanceMonitor.ts | packages/shared-services/src/services | AI-ভিত্তিক পারফরম্যান্স অ্যানালাইসিস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিক্যাল কপি; এক্সটেনশন কপি মুছুন |
| ScopeGuardService.ts | packages/shared-services/src/services | READ_ONLY/READ_WRITE পারমিশন স্কোপ গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SecurityScanner.ts | packages/shared-services/src/services | AI-ভিত্তিক কোড সিকিউরিটি স্ক্যানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SelfHealingService.ts | packages/shared-services/src/services | এরর বিশ্লেষণ+অটো-প্যাচ প্রস্তাব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SupremeAIService.ts | packages/shared-services/src/services | ব্যাকএন্ড কমিউনিকেশন কোর (platform-agnostic) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| TelemetryTracker.ts | packages/shared-services/src/services | Levenshtein দিয়ে প্যাচ গ্রহণযোগ্যতা ট্র্যাকিং | PatchTelemetryTracker.ts | অপরিবর্তিত ✅ | শুধু প্যাচ-টেলিমেট্রি; নাম সংকুচিত করুন |
| apiBridge.ts | packages/shared-services/src/services | SupremeExtensionBridge (টোকেন+401) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিক্যাল সংস্করণ; এক্সটেনশন কপি মুছুন |
| index.ts | packages/shared-services/src/types | শেয়ার্ড সার্ভিস টাইপ সংজ্ঞা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| JitOtpDialog.ts | packages/shared-services/src/ui | JIT OTP প্রম্পট হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ক্যানোনিক্যাল সংস্করণ; এক্সটেনশন কপি মুছুন |
| index.ts | packages/shared-services/src/vscode | VS Code অ্যাডাপ্টার এন্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tsconfig.json | packages/shared-services | TS কম্পাইলার কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| package.json | packages/shared-types | @supremeai/shared-types ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent.types.ts | packages/shared-types/src | AgentAction/Reasoning/Response টাইপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| auth.types.ts | packages/shared-types/src | AuthState/Workspace zod স্কিমা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| conversation.ts | packages/shared-types/src | Conversation/Skill/ApiResponse zod স্কিমা | conversation.types.ts | অপরিবর্তিত ✅ | sibling *.types.ts কনভেনশন মেলান |
| SkillGovernance.dart | packages/shared-types/src/dart | জেনারেটেড Dart গভর্নেন্স মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটর বাগ: সব টাইপ `null` |
| SkillManifest.dart | packages/shared-types/src/dart | জেনারেটেড Dart স্কিল ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | একই জেনারেটর বাগ |
| SkillPermissions.dart | packages/shared-types/src/dart | জেনারেটেড Dart পারমিশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | একই জেনারেটর বাগ |
| index.dart | packages/shared-types/src/dart | Dart ব্যারেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| index.ts | packages/shared-types/src | ব্যারেল এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| message.ts | packages/shared-types/src | Message/ToolCall zod স্কিমা | message.types.ts | অপরিবর্তিত ✅ | sibling কনভেনশন মেলান |
| SkillGovernance.d.ts | packages/shared-types/src/typescript | জেনারেটেড d.ts (ভাঙা টাইপ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটর বাগ: সব টাইপ `null` |
| SkillManifest.d.ts | packages/shared-types/src/typescript | জেনারেটেড d.ts (ভাঙা টাইপ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | একই জেনারেটর বাগ |
| SkillPermissions.d.ts | packages/shared-types/src/typescript | জেনারেটেড d.ts (ভাঙা টাইপ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | একই জেনারেটর বাগ |
| index.d.ts | packages/shared-types/src/typescript | d.ts ব্যারেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tsconfig.json | packages/shared-types | TS কম্পাইলার কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| package.json | packages/ui-components | @supremeai/ui-components ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ChatBubble.tsx | packages/ui-components/src | চ্যাট বার্তা বাবল কম্পোনেন্ট | অপরিবর্তিত ✅ | src/components/ | সহযোগীদের মতো components/-এ সরুন |
| DashboardShell.tsx | packages/ui-components/src/components | সাইডবার+মেইন ড্যাশবোর্ড লেআউট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ErrorBoundary.tsx | packages/ui-components/src/components | ক্র্যাশ-প্রতিরোধী রিক্যাভারি বাউন্ডারি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LiveSujonBackground.tsx | packages/ui-components/src/components | মাত্র একটি গ্রেডিয়েন্ট ব্যাকড্রপ div | GradientBackdrop.tsx | অপরিবর্তিত ✅ | ⚠️ ব্যক্তিগত ব্র্যান্ড-নাম; সাধারণ গ্রেডিয়েন্ট |
| SupremeCard.test.tsx | packages/ui-components/src/components | SupremeCard vitest ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SupremeCard.tsx | packages/ui-components/src/components | গ্লাসমরফিজম কার্ড কম্পোনেন্ট | GlassCard.tsx | অপরিবর্তিত ✅ | ⚠️ "Supreme" ব্র্যান্ড-উপসর্গ মানক কার্ডে |
| SupremeHeader.tsx | packages/ui-components/src/components | পেজ হেডার+গ্রেডিয়েন্ট টাইটেল | PageHeader.tsx | অপরিবর্তিত ✅ | ⚠️ ব্র্যান্ড-উপসর্গ; ফাংশন সাধারণ হেডার |
| styles.css | packages/ui-components/src/components | ২টি খালি ক্লাস — মৃত স্টাব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | খালি স্টাব; মুছে ফেলার প্রার্থী |
| SharedProviders.tsx | packages/ui-components/src/contexts | QueryClientProvider র‍্যাপার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| index.ts | packages/ui-components/src | ব্যারেল এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| api.ts | packages/ui-components/src/utils | getApiBaseUrl (VITE_API_* রেজোলিউশন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tsconfig.json | packages/ui-components | TS কম্পাইলার কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| supreme_engine.proto | shared/protos | WorkerService gRPC কন্ট্রাক্ট (task+audit) | worker_service.proto | অপরিবর্তিত ✅ | সার্ভিস WorkerService; ফাইলনাম ভিন্ন |
| README.md | tools/autonomy | অটোনমি প্যাক ডক (কন্ট্রোল লুপ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| source_candidates.json | tools/autonomy/examples | trust_engine স্যাম্পল ইনপুট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| smoke_test.py | tools/autonomy/tests | ৩ টুলের subprocess স্মোক টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agent_change_budget.py | tools/autonomy/tools | পরিবর্তন-ঝুঁকি স্কোর+অ্যাপ্রোভাল টায়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| autonomy_cycle.py | tools/autonomy/tools | ৩ টুলের লাইফসাইকেল রিপোর্ট অর্কেস্ট্রেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| capability_builder.py | tools/autonomy/tools | গোল→দক্ষতা-গ্যাপ প্ল্যান জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| common.py | tools/autonomy/tools | শেয়ার্ড ফাইলওয়াক/সিক্রেট-স্ক্যান হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| deploy_guard.py | tools/autonomy/tools | প্রি-ডিপ্লয় রিস্ক গেট (সিক্রেট/টেস্ট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| knowledge_ingestor.py | tools/autonomy/tools | সোর্স→provenance-সহ নলেজ রেকর্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| maintenance_watchdog.py | tools/autonomy/tools | বড় ফাইল/TODO ডেট ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| self_heal_loop.py | tools/autonomy/tools | লগ→বাউন্ডেড রিপেয়ার প্ল্যান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| source_trust_engine.py | tools/autonomy/tools | সোর্স ট্রাস্ট স্কোরার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | discovery trust_engine-এর সাথে ওভারল্যাপ |
| test_synthesizer.py | tools/autonomy/tools | লগ→রিগ্রেশন টেস্ট স্কেলিটন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cache_cleanup.py | tools | Redis temp_cache কী ক্লিনআপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| README.md | tools/discovery_fabric | evidence-first ডিসকভারি লেয়ার ডক | solution_discovery/README.md | অপরিবর্তিত ✅ | ⚠️ "fabric" ব্যান-শব্দ; কনটেন্ট সাধারণ ডিসকভারি |
| example_problem.json | tools/discovery_fabric | স্যাম্পল প্রবলেম ইনপুট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pyproject.toml | tools/discovery_fabric | supremeai-discovery-fabric প্যাকেজ কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্যাকেজ রিনেম হলে এটিও আপডেট |
| __init__.py | tools/discovery_fabric/supremeai_discovery | প্যাকেজ ইনিট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| marketplace_scout.py | tools/discovery_fabric/supremeai_discovery | শর্টলিস্ট র‍্যাংক/ক্লাসিফায়ার (কোনো marketplace API নেই) | artifact_ranker.py | অপরিবর্তিত ✅ | নাম বিভ্রান্তিকর; কাজ র‍্যাংকিং |
| solution_synthesizer.py | tools/discovery_fabric/supremeai_discovery | benefit/effort/risk ভিত্তিক সলিউশন র‍্যাংকার | solution_ranker.py | অপরিবর্তিত ✅ | tools/solution_synthesizer-এর সাথে হোমোনিম |
| source_scout.py | tools/discovery_fabric/supremeai_discovery | GitHub/npm/HF/PyPI সার্চ ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| trust_engine.py | tools/discovery_fabric/supremeai_discovery | Evidence স্কোরিং+aggregate | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| fix_gen_syntax.py | tools | gen_knowledge_seed-এর সিনট্যাক্স প্যাচ (one-shot) | fix_knowledge_seed_syntax.py | অপরিবর্তিত ✅ | নাম অস্পষ্ট; ব্যবহারের পর মুছুন |
| fix_json.py | tools | coldstart seed JSON ব্র্যাকেট ফিক্সার (one-shot) | fix_coldstart_seed_json.py | অপরিবর্তিত ✅ | হার্ডকোডেড পাথ; নাম অস্পষ্ট |
| gap_finder.py | tools | gap_finder প্যাকেজের ডেলিগেটিং র‍্যাপার | মুছে ফেলুন ❌ | — | প্যাকেজের নাম-সংঘর্ষ; `python -m` ব্যবহার করুন |
| __init__.py | tools/gap_finder | প্যাকেজ ইনিট (AuditReport এক্সপোর্ট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cli.py | tools/gap_finder | CLI (profile/focus/baseline ফ্ল্যাগ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| config.py | tools/gap_finder | ignore-list/manifest/সিক্রেট প্যাটার্ন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| helpers.py | tools/gap_finder | finding/সিভিয়ারিটি হেল্পার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| models.py | tools/gap_finder | Finding/AuditStats/AuditReport ডেটাক্লাস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| scanner.py | tools/gap_finder | ১২০৬ লাইনের GapScanner মনোলিথ (৭ ক্যাটাগরি) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ক্যাটাগরি অনুযায়ী ভাঙুন |
| README.md | tools/gap_miner | gap miner টুলকিট ডক | project_auditor/README.md | অপরিবর্তিত ✅ | ⚠️ "miner" বনাম audit scanner; gap_finder ডুপ্লিকেট |
| run_gap_mining.sh | tools/gap_miner | ৪ মাইনারের ব্যাচ রানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | CWD-নির্ভর পাথ; ডকে উল্লেখ করুন |
| architecture_miner.py | tools/gap_miner/tools | import fan-out/coupling স্ক্যান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| context_packager.py | tools/gap_miner/tools | AI-র জন্য কনটেক্সট প্যাক জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| drift_detector.py | tools/gap_miner/tools | docs/code/CI ড্রিফ্ট ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| gap_miner.py | tools/gap_miner/tools | মূল প্রজেক্ট-ইন্টেলিজেন্স স্ক্যানার (২৪৪L) | project_auditor.py | অপরিবর্তিত ✅ | ⚠️ "miner" মিসম্যাচ; gap_finder.scanner ডুপ্লিকেট |
| incident_replay.py | tools/gap_miner/tools | লগ→রিপ্লে কেস জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| project_fingerprint.py | tools/gap_miner/tools | ভাষা/ইমপোর্ট/সাইজ ফিঙ্গারপ্রিন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| prompt_distiller.py | tools/gap_miner/tools | প্রম্পট বয়লারপ্লেট ডিডুপ্লিকেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| provider_capacity_miner.py | tools/gap_miner/tools | LLM প্রোভাইডার ক্যাপাসিটি স্ক্যান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| safe_autofix_plan.py | tools/gap_miner/tools | র‍্যাংকড রিমিডিয়েশন প্ল্যান (read-only) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| security_config_miner.py | tools/gap_miner/tools | সিক্রেট/কনফিগ হাইজিন স্ক্যানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| gen_knowledge_seed.py | tools | ৫৮৮ লাইন হার্ডকোডেড seed-JSON জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; ডেটা আলাদা ফাইলে আনুন |
| README.md | tools/intelligence_extensions | ১০ মডিউলের এক্সটেনশন প্যাক ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| run_examples.py | tools/intelligence_extensions/scripts | উদাহরণ রানার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| __init__.py | tools/intelligence_extensions/supremeai_intelligence | ব্যারেল (১০ মডিউল রি-এক্সপোর্ট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| autonomous_red_team.py | tools/intelligence_extensions/supremeai_intelligence | ৮-ক্যাম্পেইন async red-team হার্নেস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| contracts.py | tools/intelligence_extensions/supremeai_intelligence | SourceRecord কনট্রাক্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| contradiction_hunter.py | tools/intelligence_extensions/supremeai_intelligence | মেমোরি কন্ট্রাডিকশন/ডুপ ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| evidence_verifier.py | tools/intelligence_extensions/supremeai_intelligence | ক্লেইম ভেরিফায়ার (reliability heuristic) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| execution_verifier.py | tools/intelligence_extensions/supremeai_intelligence | AST+deny-import+sandbox ভেরিফায়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| failure_pattern_miner.py | tools/intelligence_extensions/supremeai_intelligence | ফিঙ্গারপ্রিন্ট-ভিত্তিক ব্যর্থতা গ্রুপার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| knowledge_graph_builder.py | tools/intelligence_extensions/supremeai_intelligence | আর্টিফ্যাক্ট→নোড/এজ গ্রাফ বিল্ডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| knowledge_revalidator.py | tools/intelligence_extensions/supremeai_intelligence | TTL-ভিত্তিক রিচেক সিডিউলার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| memory_curator.py | tools/intelligence_extensions/supremeai_intelligence | promote/demote/archive সিদ্ধান্ত ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| model_router_economist.py | tools/intelligence_extensions/supremeai_intelligence | কস্ট/কোয়ালিটি-ভিত্তিক মডেল রাউটার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| pipeline.py | tools/intelligence_extensions/supremeai_intelligence | IntelligenceGate — প্রমোশন গেট | promotion_gate.py | অপরিবর্তিত ✅ | "pipeline" অস্পষ্ট; কাজ গেটকিপিং |
| skill_distiller.py | tools/intelligence_extensions/supremeai_intelligence | ওয়ার্কফ্লো→স্কিল ক্যান্ডিডেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| conftest.py | tools/intelligence_extensions/tests | sys.path সেটআপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| test_extensions.py | tools/intelligence_extensions/tests | ৫ মডিউলের ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| card_builder.py | tools/knowledge | ১৬৮৩ লাইনের হার্ডকোডেড নলেজ-কার্ড ডেটা | knowledge_cards_data.py | অপরিবর্তিত ✅ | ডেটা-কোড মিশ্রণ; JSON-এ সরান |
| cards.py | tools/knowledge | ToolKnowledgeCard ডেটাক্লাস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cli.py | tools/knowledge | ইনজেকশন/এক্সপোর্ট CLI | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| injector.py | tools/knowledge | ai_memory-তে কার্ড ইনজেক্টর (hash dedup) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| README.md | tools/knowledge_squeezer | মাল্টি-মডেল নলেজ রিফাইনারি ডক | knowledge_refinery/README.md | অপরিবর্তিত ✅ | ⚠️ "squeezer" ব্যান-শব্দ; কনটেন্ট রিফাইনারি |
| SUGGESTED_NEW_SCRIPTS.md | tools/knowledge_squeezer | ভবিষ্যৎ স্ক্রিপ্ট রোডম্যাপ নোট | অপরিবর্তিত ✅ | docs/ বা archive | প্রস্তাবগুলো intelligence_extensions-এ বাস্তবায়িত |
| __init__.py | tools/knowledge_squeezer/knowledge_squeezer | প্যাকেজ ইনিট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| cli.py | tools/knowledge_squeezer/knowledge_squeezer | squeeze CLI (topic+domain) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| engine.py | tools/knowledge_squeezer/knowledge_squeezer | ৬-ধাপ জেনারেট→অডিট→সিন্থেসাইজ ইঞ্জিন | knowledge_refinery/engine.py | অপরিবর্তিত ✅ | ⚠️ "Squeezer" ক্লাসনাম রিফাইনারি করুন |
| example_run.py | tools/knowledge_squeezer/knowledge_squeezer | ডেমো রান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| memory_adapter.py | tools/knowledge_squeezer/knowledge_squeezer | long-term memory পেলোড অ্যাডাপ্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| models.py | tools/knowledge_squeezer/knowledge_squeezer | Candidate/Critique/KnowledgeArtifact | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| prompts.py | tools/knowledge_squeezer/knowledge_squeezer | ৫টি সিস্টেম প্রম্পট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| prompts_schema.json | tools/knowledge_squeezer/knowledge_squeezer | আর্টিফ্যাক্ট JSON স্কিমা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| providers.py | tools/knowledge_squeezer/knowledge_squeezer | OpenAI-compatible/Anthropic/Gemini প্রোভাইডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| scoring.py | tools/knowledge_squeezer/knowledge_squeezer | কনসেনসাস/কভারেজ/এভিডেন্স স্কোর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| knowledge_squeezer.py | tools/knowledge_squeezer/scripts | PYTHONPATH র‍্যাপার এন্ট্রি | মুছে ফেলুন ❌ | — | cli.py ডুপ্লিকেট এন্ট্রি |
| master_orchestrator.py | tools | backend master-orchestrator-এর CLI র‍্যাপার | orchestrator_cli.py | backend/scripts/ | নাম বড় শোনাচ্ছে; আসলে CLI shim |
| multi_model_knowledge_distiller.py | tools | মাল্টি-মডেল জ্ঞান সংশ্লেষণ→ai_memory | অপরিবর্তিত ✅ | tools/knowledge/ | knowledge টুল-ফ্যামিলির সাথে গ্রুপ করুন |
| pipeline_recipe_compiler.py | tools | টুল-পাইপলাইন রেসিপি কম্পাইলার→ai_memory | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| README.md | tools/solution_synthesizer | নিরাপদ রিপেয়ার লুপ ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| issue.json | tools/solution_synthesizer/examples | স্যাম্পল রিপেয়ার রিকোয়েস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| self_test_issue.json | tools/solution_synthesizer/examples | সেলফ-টেস্ট ইনপুট (১ লাইন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| solution_synthesizer.json | tools/solution_synthesizer/reports | কমিট হওয়া রান-আউটপুট | মুছে ফেলুন ❌ | — | বিল্ড আর্টিফ্যাক্ট; .gitignore করুন |
| smoke_test.py | tools/solution_synthesizer/tests | py_compile স্মোক টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| solution_synthesizer.py | tools/solution_synthesizer/tools | ডায়াগনোসিস→প্যাচ→ভেরিফাই লুপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ARCHITECTURE_BN.md | tools/vscode-extension | এক্সটেনশন আর্কিটেকচার ডক (বাংলা) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AdminMetricsController.java | tools/vscode-extension | Spring Boot /api/admin/metrics কন্ট্রোলার | অপরিবর্তিত ✅ | tools/java-admin-api/ | এক্সটেনশনে Java থাকা অনুচিত |
| CHANGELOG.md | tools/vscode-extension | v6.0.0 পরিবর্তন লগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CodebaseAuditService.java | tools/vscode-extension | সিমুলেটেড অটো-অডিট সার্ভিস (স্টাব) | অপরিবর্তিত ✅ | tools/java-admin-api/ | Python backend-এর কাজের ডুপ্লিকেট |
| FeatureDefinition.java | tools/vscode-extension | ফিচার মডেল POJO | অপরিবর্তিত ✅ | tools/java-admin-api/ | ভুল ডিরেক্টরি |
| FeatureRegistryController.java | tools/vscode-extension | /api/admin/features REST কন্ট্রোলার | অপরিবর্তিত ✅ | tools/java-admin-api/ | ভুল ডিরেক্টরি |
| FeatureRegistryService.java | tools/vscode-extension | ইন-মেমরি ফিচার রেজিস্ট্রি | অপরিবর্তিত ✅ | tools/java-admin-api/ | ভুল ডিরেক্টরি |
| GlobalMetrics.java | tools/vscode-extension | মেট্রিক্স POJO | অপরিবর্তিত ✅ | tools/java-admin-api/ | ভুল ডিরেক্টরি |
| GlobalMetricsService.java | tools/vscode-extension | Firestore মেট্রিক্স ইনক্রিমেন্ট সার্ভিস | অপরিবর্তিত ✅ | tools/java-admin-api/ | Python backend ডুপ্লিকেট |
| INTEGRATION_GUIDE_BN.md | tools/vscode-extension | হাইব্রিড AI রাউটিং গাইড (বাংলা) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| LICENSE | tools/vscode-extension | MIT লাইসেন্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| README.md | tools/vscode-extension | এক্সটেনশন ফিচার/ইনস্টল ডক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| README_BANGLA.md | tools/vscode-extension | বাংলা README (eLai-অনুপ্রাণিত) | মুছে ফেলুন ❌ (README_BN-এ মার্জ) | — | দুটি বাংলা README ডুপ্লিকেট |
| README_BN.md | tools/vscode-extension | বাংলা README (thin-client সংস্করণ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| _INDEX.md | tools/vscode-extension | AI ফাইল ইনডেক্স+থিন-ক্লায়েন্ট নিয়ম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| eslint.config.mjs | tools/vscode-extension | ESLint flat কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| jest.config.js | tools/vscode-extension | ts-jest কনফিগ | মুছে ফেলুন ❌ | — | Vitest প্রধান রানার; দ্বৈত ডুপ্লিকেট |
| icon.png | tools/vscode-extension/media | এক্সটেনশন আইকন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| icon.svg | tools/vscode-extension/media | ভেক্টর আইকন সোর্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| supremeai-theme.css | tools/vscode-extension/media | ব্র্যান্ড CSS ওভাররাইড (tokens import) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vscode-theme.css | tools/vscode-extension/media | ওয়েবভিউ ডিজাইন সিস্টেম (৩৭৮L) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| package.json | tools/vscode-extension | VS Code ম্যানিফেস্ট v6.0.0 (৪৩৪L) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; activationEvents "*" lazy করুন |
| package.nls.bn.json | tools/vscode-extension | বাংলা NLS স্ট্রিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| build.mjs | tools/vscode-extension/scripts | esbuild+pnpm symlink বিল্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| VsCodePlatformAdapter.ts | tools/vscode-extension/src/adapters | TokenProvider ব্রিজ (vscode auth) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| agentDetector.ts | tools/vscode-extension/src | IDE/agent শনাক্তকারী (swarm mode) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AIService.ts | tools/vscode-extension/src/ai | থিন-ক্লায়েন্ট কমপ্লিশন সার্ভিস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CodeGenerationService.ts | tools/vscode-extension/src/ai | ফাংশন/ক্লাস/টেস্ট জেনারেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CodeReviewService.ts | tools/vscode-extension/src/ai | AI কোড রিভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ContextBuilder.ts | tools/vscode-extension/src/ai | এডিটর কনটেক্সট সংগ্রাহক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| EnhancedAIService.ts | tools/vscode-extension/src/ai | AIService সাবক্লাস; হার্ডকোডেড মেট্রিক্স স্টাব | মুছে ফেলুন/মার্জ ❌ | — | parseComplexity ভুয়া ভ্যালু; AIService-এ মার্জ |
| extension.ts | tools/vscode-extension/src | এন্ট্রি পয়েন্ট+কমান্ড রেজিস্ট্রেশন (৬৯৬L) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; activate() ভাঙুন |
| AuthHandler.ts | tools/vscode-extension/src/handlers | URI লগইন কলব্যাক (CSRF চেক) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CodeEditHandler.ts | tools/vscode-extension/src/handlers | ডিবাউন্সড কোড-এডিট ট্র্যাকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CodeFlowHandler.ts | tools/vscode-extension/src/handlers | CodeFlow অ্যানালাইসিস+কমান্ড (৭২২L) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ঠিক; মনোলিথ ভাঙুন |
| ErrorHandler.ts | tools/vscode-extension/src/handlers | ডায়াগনস্টিক→ব্যাকএন্ড রিপোর্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| FeedbackHandler.ts | tools/vscode-extension/src/handlers | সাজেশন accept/reject ট্র্যাকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| VisualizationHandler.ts | tools/vscode-extension/src/handlers | ৩টি "coming soon" কমান্ড স্টাব | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্টাব; বাস্তবায়ন বা মুছুন |
| PerformanceMonitor.ts | tools/vscode-extension/src/performance | shared-services কপির ডুপ্লিকেট (হার্ডকোডেড স্কোর) | মুছে ফেলুন ❌ | — | shared-services ক্যানোনিক্যাল; ডুপ্লিকেট |
| TerminalActivitySensor.ts | tools/vscode-extension/src/performance | টার্মিনাল ব্যস্ততা সেন্সর (zero-lag) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| BrowserPreviewProvider.ts | tools/vscode-extension/src/providers | ব্রাউজার টাস্ক ওয়েবভিউ প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| CodeFlowPanel.ts | tools/vscode-extension/src/providers | CodeFlow গ্রাফ প্যানেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| DependencyGraphProvider.ts | tools/vscode-extension/src/providers | ডিপেন্ডেন্সি গ্রাফ ভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| StreamingChatProvider.ts | tools/vscode-extension/src/providers | নাম streaming, কিন্তু একক-রেসপন্স র‍্যাপার | মার্জ: SupremeAIChatProvider ❌ | — | স্ট্রিমিং নয়; ডুপ্লিকেট চ্যাট পাথ |
| SupremeAIActionProvider.ts | tools/vscode-extension/src/providers | এরর-লাইন QuickFix CodeAction | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SupremeAIActivityProvider.ts | tools/vscode-extension/src/providers | লার্নিং-অ্যাক্টিভিটি ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SupremeAIAdminDashboardProvider.ts | tools/vscode-extension/src/providers | অ্যাডমিন ওয়েবভিউ ড্যাশবোর্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SupremeAIChatProvider.ts | tools/vscode-extension/src/providers | চ্যাট ওয়েবভিউ প্রোভাইডার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SupremeAIChatView.ts | tools/vscode-extension/src/providers | চ্যাট HTML টেমপ্লেট জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SupremeAICustomerDashboardProvider.ts | tools/vscode-extension/src/providers | কাস্টমার ওয়েবভিউ ড্যাশবোর্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SupremeAISidebarProvider.ts | tools/vscode-extension/src/providers | জেনেরিক সাইডবার (tokens CSS লোড) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SupremeWebviewProvider.ts | tools/vscode-extension/src/providers | /api/skills রেসিপি লিস্ট ভিউ | SupremeAISkillsProvider.ts | অপরিবর্তিত ✅ | নাম অস্পষ্ট; কাজ skills প্যানেল |
| AuthService.ts | tools/vscode-extension/src/services | SecretStorage-ভিত্তিক অথ সিঙ্গেলটন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| AutonomousCodingAgent.ts | tools/vscode-extension/src/services | OpenHands সার্ভার থিন-ক্লায়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SupremeAIService.ts | tools/vscode-extension/src/services | shared-services রি-এক্সপোর্ট shim | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SwarmPipelineProvider.ts | tools/vscode-extension/src/services | ide-trio ব্যাকএন্ড পাইপলাইন+ফলব্যাক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| apiBridge.ts | tools/vscode-extension/src/services | SupremeExtensionBridge ডুপ্লিকেট কপি | মুছে ফেলুন ❌ | — | shared-services-এ ক্যানোনিক্যাল সংস্করণ আছে |
| index.ts | tools/vscode-extension/src/types | shared টাইপ রি-এক্সপোর্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| HealingStatusBar.ts | tools/vscode-extension/src/ui | healing স্টেট স্ট্যাটাস বার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| JitOtpDialog.ts | tools/vscode-extension/src/ui | shared JitOtpDialog ডুপ্লিকেট | মুছে ফেলুন ❌ | — | shared-services ফাংশন-সংস্করণ ব্যবহার করুন |
| BaseDisposable.ts | tools/vscode-extension/src/utils | Disposable বেস ক্লাস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| DynamicSignatureRegistry.ts | tools/vscode-extension/src/utils | হার্ডকোডেড গ্রিটিং/ইনটেন্ট প্যাটার্ন | IntentPatternRegistry.ts | অপরিবর্তিত ✅ | "signature" অস্পষ্ট; ইনটেন্ট-প্যাটার্ন |
| logger.ts | tools/vscode-extension/src/utils | রিড্যাকশন-সহ লগার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ScopeGuardService.test.ts | tools/vscode-extension/test | ভাঙা ইমপোর্টের টেস্ট (লোকাল ফাইল নেই) | অপরিবর্তিত ✅ | packages/shared-services/test/ | ক্লাস এখন shared প্যাকেজে |
| vscode.d.ts | tools/vscode-extension/test/__mocks__ | jest mock টাইপ ডিক্লারেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vscode.ts | tools/vscode-extension/test/__mocks__ | jest vscode মক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | vitest mock-এর সাথে ডুপ্লিকেট |
| auth-service.test.ts | tools/vscode-extension/test | AuthService ইউনিট টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| autonomous-coding-agent.test.ts | tools/vscode-extension/test | agent skip/upstream টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vscode.ts | tools/vscode-extension/test/mocks | vitest vscode মক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| setup.ts | tools/vscode-extension/test | গ্লোবাল axios/vscode মক সেটআপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| supremeai-service.test.ts | tools/vscode-extension/test | apiBridge/সার্ভিস টেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tsconfig.json | tools/vscode-extension | TS কনফিগ (strict) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| vitest.config.ts | tools/vscode-extension | vitest কনফিগ (vscode alias) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- tools/-এর নতুন টুলকিট প্রজন্ম (autonomy, gap_finder, gap_miner, intelligence_extensions, knowledge_squeezer, discovery_fabric, solution_synthesizer) সুশৃঙ্খলভাবে read-only, dependency-free ডিজাইন করা — মূল সমস্যা নাম-অহংকার ও ওভারল্যাপ, কোড-মান নয়।
- gap_finder (১২০৬ লাইনের scanner.py) ও gap_miner-এর gap_miner.py প্রায় একই প্রজেক্ট-অডিট কাজ দু'বার করে — একটি ক্যানোনিক্যাল project_auditor-এ মার্জ করুন; "miner/fabric/squeezer" নামগুলো ⚠️ সেমান্টিক মিসম্যাচ।
- ট্রাস্ট/স্কোরিং লজিক ৩ জায়গায় বিক্ষিপ্ত: autonomy/source_trust_engine.py, discovery_fabric/trust_engine.py, knowledge_squeezer/scoring.py — ইউনিফাই করার সুযোগ।
- vscode-extension-এ ৭টি Java (Spring Boot + Firestore) ফাইল ভুল ডিরেক্টরিতে — Python/FastAPI backend-এর metrics/features কার্যকারিতার ডুপ্লিকেট; আলাদা java-admin-api/ ফোল্ডারে সরান বা মুছুন।
- shared-services ঠিকভাবে DRY করা হলেও এক্সটেনশনে পুরনো কপি রয়ে গেছে: src/services/apiBridge.ts, src/performance/PerformanceMonitor.ts, src/ui/JitOtpDialog.ts — ৩টিই ডুপ্লিকেট, মুছে ফেলুন।
- টেস্ট ইনফ্রা দ্বৈত: jest.config.js + vitest.config.ts দুটোই আছে, দুই সেট vscode মক (test/__mocks__ ও test/mocks); test/ScopeGuardService.test.ts ভাঙা ইমপোর্টের কারণে ডেড — shared-services/test-এ সরান।
- packages/shared-types-এর টাইপ জেনারেটরে বাগ: dart/ ও typescript/ ফাইলের প্রায় সব প্রপার্টির টাইপ `null` — জেনারেটর ফিক্স না করা পর্যন্ত এই বাইন্ডিং অব্যবহারযোগ্য।
- ডুপ্লিকেট ডক/আর্টিফ্যাক্ট: README_BANGLA.md বনাম README_BN.md; knowledge_squeezer/SUGGESTED_NEW_SCRIPTS.md-এর প্রস্তাবগুলো intelligence_extensions-এ ইতোমধ্যে বাস্তবায়িত; solution_synthesizer/reports/*.json কমিট হওয়া রান-আউটপুট। CrossAiObserverService/apiBridge-এ ৩টি হার্ডকোডেড Cloud Run URL কেন্দ্রীয় কনফিগে আনুন।


---

## ব্যাচ ১৪ — Docs, Specs, Reports ও Infrastructure Config
**ব্যাচ:** 14 | **তালিকাভুক্ত:** 241 | **বিশ্লেষিত:** 241 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 58 | **স্থানান্তর প্রস্তাব:** 57 | **⚠️ সেমান্টিক মিসম্যাচ:** 27

| বর্তমান নাম | বর্তমান অবস্থান | কনটেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| 100+rules_for_agent.md | .agents | "Supreme Developer" মাইন্ডসেট/স্ট্যান্ডার্ড নিয়ম (বাংলা) | agent-development-standards-bn.md | অপরিবর্তিত ✅ | ⚠️ গ্র্যান্ডিওজ শিরোনাম, '+' ফাইলনেম অ-স্ট্যান্ডার্ড |
| AGENTS.md | .agents | এজেন্ট কোর ডিরেক্টিভ; STATUS.md-কে SSO বলে | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | AGENTS.md কনভেনশন, সঠিক স্থান |
| cine_rules.json | .agents | "cine" এজেন্টের পুরনো রুল-স্কিমা (v1 স্টাইল) | অপরিবর্তিত ✅ | _archive/ | config/agent_rules.json (v2) সাপারসিডেড |
| AI_AGENT_ANTIPATTERN_PLAYBOOK.md | .agents/rules | অ্যান্টি-প্যাটার্ন প্লেবুক — ব্রাঞ্চ-স্ন্যাপশট কপি | অপরিবর্তিত ✅ | _archive/ | docs/-এ নতুন v3 লিভিং ভার্সন আছে |
| SKILL.md | .agents/skills/browser-automation | ব্রাউজার অটোমেশন স্কিল ডেফিনিশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | SKILL.md কনভেনশন সঠিক |
| SKILL.md | .agents/skills/concise-planning | অ্যাটমিক কোডিং-প্ল্যান তৈরির স্কিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SKILL.md | .agents/skills/environment-health | Render/Supabase পরিবেশ হেলথ চেক স্কিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SKILL.md | .agents/skills/fastapi-pro | FastAPI/SQLAlchemy অ্যাসিঙ্ক API স্কিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SKILL.md | .agents/skills/github-actions-debugger | Actions ফেইলিউর ডায়াগনোসিস স্কিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SKILL.md | .agents/skills/mcp-tool-developer | MCP সার্ভার/টুল ডেভেলপমেন্ট স্কিল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| speckit-analyze.md | .clinerules/workflows | ক্রস-আর্টিফ্যাক্ট কনসিস্টেন্সি অ্যানালাইসিস ওয়ার্কফ্লো | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| speckit-checklist.md | .clinerules/workflows | ফিচার-নির্দিষ্ট চেকলিস্ট জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| speckit-clarify.md | .clinerules/workflows | স্পেক অস্পষ্টতা চিহ্নিতকারী ওয়ার্কফ্লো | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| speckit-constitution.md | .clinerules/workflows | প্রজেক্ট কনস্টিটিউশন তৈরি/আপডেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| speckit-converge.md | .clinerules/workflows | কোডবেস বনাম স্পেক গ্যাপ মূল্যায়ন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| speckit-implement.md | .clinerules/workflows | tasks.md এক্সিকিউশন ওয়ার্কফ্লো | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| speckit-plan.md | .clinerules/workflows | ইমপ্লিমেন্টেশন প্ল্যানিং ওয়ার্কফ্লো | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| speckit-specify.md | .clinerules/workflows | ন্যাচারাল-ল্যাঙ্গুয়েজ থেকে স্পেক তৈরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| speckit-tasks.md | .clinerules/workflows | ডিপেন্ডেন্সি-অর্ডারড tasks.md জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| speckit-taskstoissues.md | .clinerules/workflows | tasks → GitHub issues কনভার্টার | speckit-tasks-to-issues.md | অপরিবর্তিত ✅ | পাঠযোগ্যতার জন্য হাইফেন |
| Dockerfile | .devcontainer | Python 3.11 + Node ডেভ-কনটেইনার ইমেজ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড নাম ও স্থান |
| devcontainer.json | .devcontainer | SupremeAI ফ্রি-টিয়ার ডেভ-এনভায়রনমেন্ট কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড নাম ও স্থান |
| AUDIT_MASTER_CHECKLIST.md | .gemini/temp_patch | অডিট চেকলিস্টের temp কপি (audit_reports কপি থেকে ভিন্ন) | অপরিবর্তিত ✅ | _archive/ | টেম্প-প্যাচ স্ন্যাপশট, স্টেল |
| MANUAL_STEPS.md | .gemini/temp_patch | ম্যানুয়াল অ্যাকশন তালিকা (2026-08-30 স্ন্যাপশট) | অপরিবর্তিত ✅ | _archive/ | তারিখ-স্ট্যাম্পড অডিট-সেশন আর্টিফ্যাক্ট |
| MANUAL_STEPS_REMAINING.md | .gemini/temp_patch | প্যাচ v2-পরবর্তী বাকি ম্যানুয়াল স্টেপ | অপরিবর্তিত ✅ | _archive/ | স্টেল অডিট-সেশন আর্টিফ্যাক্ট |
| PATCH_NOTES_v2.md | .gemini/temp_patch | অডিট প্যাচ v2 নোট (2026-08-30) | অপরিবর্তিত ✅ | _archive/ | ভার্সন-স্ট্যাম্পড টেম্প প্যাচ নোট |
| TASK_7_1_7_6_7_7_PATCH.md | .gemini/temp_patch | টাস্ক 7.1/7.6/7.7 ইমপ্লিমেন্টেশন প্যাচ | অপরিবর্তিত ✅ | _archive/ | টাস্ক-নম্বর নাম, একবার-ব্যবহারযোগ্য প্যাচ |
| CODEOWNERS | .github | রিভিউয়ার অ্যাসাইনমেন্ট কনফিগ (বাংলা নোটসহ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড নাম ও স্থান |
| action.yml | .github/actions/setup-backend | Poetry/virtualenv সেটআপ কম্পোজিট অ্যাকশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | অ্যাকশন কনভেনশন সঠিক |
| failed_job_log.md | .github/actions/setup-backend | CI ফেইল লগ স্ন্যাপশট (coverage 63.8% ফেইল) | অপরিবর্তিত ✅ | _archive/ | কমিটেড লগ-আর্টিফ্যাক্ট, রিপোতে অনুচিত |
| codeql-config.yml | .github/codeql | CodeQL স্ক্যান-স্কোপ কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | CI কনফিগ সঠিক স্থানে |
| dependabot.yml | .github | ডিপেন্ডেন্সি আপডেট কনফিগ (pip+npm) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড নাম ও স্থান |
| check-render-quota.py | .github/scripts | Render কোটা চেক স্ক্রিপ্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | CI হেল্পার, নাম সঠিক |
| ci_error_report.py | .github/scripts | Actions লগ স্ক্যান করে এরর রিপোর্ট তৈরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও দায়িত্ব মিলে যায় |
| ci_smart_summary.py | .github/scripts | CI স্মার্ট-সামারি জেনারেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও দায়িত্ব মিলে যায় |
| ci_summary_v2.py | .github/scripts | "SuperAI Enhanced CI Summary v2.0" জেনারেটর | ci_summary.py | অপরিবর্তিত ✅ | ⚠️ ভার্সন-সাফিক্স ও SuperAI ব্র্যান্ডিং |
| clean_action_logs.py | .github/scripts | পুরনো Actions লগ ক্লিনার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও দায়িত্ব মিলে যায় |
| dependency_upgrader.py | .github/scripts | Python ডিপেন্ডেন্সি আপগ্রেড স্ক্রিপ্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও দায়িত্ব মিলে যায় |
| detect-previous-failures.py | .github/scripts | পূর্ববর্তী ফেইলিউর ডিটেক্টর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম সঠিক (স্টাইল-মিশ্রণ গৌণ) |
| enforce_24h_gap.py | .github/scripts | শিডিউলড রানে ২৪-ঘণ্টা গ্যাপ গেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও দায়িত্ব মিলে যায় |
| maintenance-pipeline-documentation-bn.md | .github/scripts | maintenance ওয়ার্কফ্লোর বাংলা গাইড | maintenance-pipeline-guide-bn.md | docs/devops/bn/ | স্ক্রিপ্ট-ডিরেতে ডক বেমানান, স্টেল রেফারেন্স |
| service_preflight_check.py | .github/scripts | CI প্রি-ফ্লাইট সার্ভিস চেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও দায়িত্ব মিলে যায় |
| supreme-ci-auto-fix-documentation-bn.md | .github/scripts | অটো-ফিক্স ওয়ার্কফ্লো বাংলা গাইড | ci-auto-fix-guide-bn.md | docs/devops/bn/ | ⚠️ ব্র্যান্ড-প্রিফিক্স; ডক scripts/-এ বেমানান |
| supreme-ci-documentation-bn.md | .github/scripts | মূল CI/CD পাইপলাইন বাংলা গাইড | ci-pipeline-guide-bn.md | docs/devops/bn/ | ⚠️ ব্র্যান্ড-প্রিফিক্স; রেফারেন্সড workflow ফাইল নেই |
| supreme-release-builds-documentation-bn.md | .github/scripts | রিলিজ বিল্ড ওয়ার্কফ্লো বাংলা গাইড | release-builds-guide-bn.md | docs/devops/bn/ | ⚠️ ব্র্যান্ড-প্রিফিক্স; স্টেল রেফারেন্স |
| supreme_ci.py | .github/scripts | ইউনিফাইড CI/CD CLI — legacy রিপ্লেসমেন্ট দাবি | ci_cli.py | অপরিবর্তিত ✅ | ⚠️ ব্র্যান্ড-নাম; legacy স্ক্রিপ্ট এখনো সক্রিয় |
| trigger_render_deploy.py | .github/scripts | Render সার্ভিস ডিপ্লয় ট্রিগার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও দায়িত্ব মিলে যায় |
| verify-render-deploy.py | .github/scripts | Render ডিপ্লয় স্ট্যাটাস ভেরিফায়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও দায়িত্ব মিলে যায় |
| verify_admin_auth.py | .github/scripts | অ্যাডমিন রাউটার অথ-লিন্ট CI গার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও দায়িত্ব মিলে যায় |
| audit-release.yml | .github/workflows | অডিট ও রিলিজ সেন্টার ওয়ার্কফ্লো | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | CI কনফিগ সঠিক স্থানে |
| ci.yml | .github/workflows | SHA-pinned হার্ডেনড CI/CD পাইপলাইন v4 | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | CI কনফিগ সঠিক স্থানে |
| maintenance.yml | .github/workflows | ম্যানুয়াল মেইনটেন্যান্স/অটো-ফিক্স পাইপলাইন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | CI কনফিগ সঠিক স্থানে |
| notify-staging.yml | .github/workflows/templates | মেইন-রিপো টার্গেটেড নোটিফিকেশন টেমপ্লেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | templates/ ডিরে অর্থবহ |
| init-options.json | .specify | speckit init অপশন (ai: cline) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ক্যাফোল্ড কনভেনশন |
| integration.json | .specify | ইন্টিগ্রেশন স্টেট ফাইল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ক্যাফোল্ড কনভেনশন |
| cline.manifest.json | .specify/integrations | Cline ইন্টিগ্রেশন ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ক্যাফোল্ড কনভেনশন |
| speckit.manifest.json | .specify/integrations | speckit ইন্টিগ্রেশন ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ক্যাফোল্ড কনভেনশন |
| constitution.md | .specify/memory | SupremeAI ইঞ্জিনিয়ারিং কনস্টিটিউশন (SDD) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| check-prerequisites.ps1 | .specify/scripts/powershell | প্রিরিকুইজিট চেক স্ক্রিপ্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ক্রিপ্ট কনভেনশন |
| common.ps1 | .specify/scripts/powershell | শেয়ার্ড PowerShell ফাংশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ক্রিপ্ট কনভেনশন |
| create-new-feature.ps1 | .specify/scripts/powershell | নতুন ফিচার বুটস্ট্র্যাপ স্ক্রিপ্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ক্রিপ্ট কনভেনশন |
| resolve-template.ps1 | .specify/scripts/powershell | টেমপ্লেট রিজলভার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ক্রিপ্ট কনভেনশন |
| setup-plan.ps1 | .specify/scripts/powershell | প্ল্যান সেটআপ স্ক্রিপ্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ক্রিপ্ট কনভেনশন |
| setup-tasks.ps1 | .specify/scripts/powershell | টাস্ক সেটআপ স্ক্রিপ্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ক্রিপ্ট কনভেনশন |
| checklist-template.md | .specify/templates | চেকলিস্ট টেমপ্লেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit টেমপ্লেট কনভেনশন |
| constitution-template.md | .specify/templates | কনস্টিটিউশন টেমপ্লেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit টেমপ্লেট কনভেনশন |
| plan-template.md | .specify/templates | প্ল্যান টেমপ্লেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit টেমপ্লেট কনভেনশন |
| spec-template.md | .specify/templates | স্পেক টেমপ্লেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit টেমপ্লেট কনভেনশন |
| tasks-template.md | .specify/templates | টাস্ক টেমপ্লেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit টেমপ্লেট কনভেনশন |
| workflow.yml | .specify/workflows/speckit | speckit ওয়ার্কফ্লো ডেফিনিশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| workflow-registry.json | .specify/workflows | ওয়ার্কফ্লো রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit কনভেনশন সঠিক |
| README_BD.md | _archive/.../firebase_functions_v1 | Firebase Functions গাইড (বাংলা) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| api-router.js | _archive/.../firebase_functions_v1 | Express API রাউটিং (Functions v1) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| deployment-monitor.js | _archive/.../firebase_functions_v1 | Groq-ভিত্তিক ডিপ্লয় মনিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| api_routes.js | _archive/.../handlers | রিকোয়ারমেন্ট-প্রসেসিং হ্যান্ডলার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| firestore_triggers.js | _archive/.../handlers | Firestore অ্যাপ্রোভাল ট্রিগার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| scheduled_tasks.js | _archive/.../handlers | শিডিউলড হেলথ টাস্ক হ্যান্ডলার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| health-smart.js | _archive/.../firebase_functions_v1 | এমুলেটর হেলথ/স্ট্যাটস এন্ডপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| index.js | _archive/.../firebase_functions_v1 | Functions এন্ট্রি (scheduler) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| auth.js | _archive/.../middleware | সিস্টেম-সিক্রেট অথেনটিকেশন মিডলওয়্যার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| cors.js | _archive/.../middleware | গ্লোবাল CORS মিডলওয়্যার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| package.json | _archive/.../firebase_functions_v1 | Functions প্যাকেজ ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| providers-smart.js | _archive/.../firebase_functions_v1 | প্রোভাইডার রাউটিং লজিক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| server-connection-monitor.js | _archive/.../firebase_functions_v1 | সার্ভার কানেকশন মনিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| chatClassifier.ts | _archive/.../src | ইনটেন্ট/ChatType ক্ল্যাসিফায়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| email_handler.ts | _archive/.../src | ইমেইল প্রসেসিং ফাংশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| index.ts | _archive/.../src | TS Functions এন্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| scrapeEngine.ts | _archive/.../src | Firestore-ভিত্তিক স্ক্র্যাপিং ইঞ্জিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| scrapeHistoryManager.ts | _archive/.../src | স্ক্র্যাপ-হিস্ট্রি ম্যানেজার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| scrapeSchema.yaml | _archive/.../src | Firestore কালেকশন স্কিমা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| swagger.yaml | _archive/.../firebase_functions_v1 | পুরনো OpenAPI স্পেক | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| system-health.js | _archive/.../firebase_functions_v1 | Firebase/GCloud হেলথ মনিটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| tsconfig.json | _archive/.../firebase_functions_v1 | TypeScript কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| externalClient.js | _archive/.../utils | Axios HTTP র‍্যাপার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| ocrTrigger.ts | _archive/firebase_functions_removed_20260825 | OCR ট্রিগার নমুনা ফাংশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | আর্কাইভড কনটেন্ট — যেমন আছে |
| AUDIT_MASTER_CHECKLIST.md | audit_reports/supreme-deep-audit-reports | লিভিং প্রোডাকশন-রেডিনেস ভেরিফিকেশন চেকলিস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সক্রিয় অডিট ট্র্যাকার, স্থান উপযুক্ত |
| CHECKPOINT.md | audit_reports/supreme-deep-audit-reports | এজেন্ট সেশন চেকপয়েন্ট/হ্যান্ডওফ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সক্রিয় হ্যান্ডওফ ফাইল |
| CONTRIBUTING.md | audit_reports/supreme-deep-audit-reports | কন্ট্রিবিউশন/ব্রাঞ্চিং গাইড | অপরিবর্তিত ✅ | রুট (repo root) | কনভেনশনে রুট-লেভেল ফাইল |
| FEATURE_TRACKING_LOG.md | audit_reports/supreme-deep-audit-reports | ফিচার-ট্র্যাকিং এজেন্ট লগ টেবিল | অপরিবর্তিত ✅ | reports/archive/ | সেশন-লগ স্ন্যাপশট |
| LESSONS_LEARNED.md | audit_reports/supreme-deep-audit-reports | রিভার্স-ক্রোনো লেসন লগ ('ব্রেইন' ফাইল) | অপরিবর্তিত ✅ | docs/ | ব্রেইন ফাইল, অডিট-রিপোর্ট নয় |
| MANUAL_STEPS.md | audit_reports/supreme-deep-audit-reports | হিউম্যান-রিকোয়ারড রিমিডিয়েশন ট্র্যাকার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সক্রিয় ট্র্যাকার, স্থান উপযুক্ত |
| README.md | audit_reports/supreme-deep-audit-reports | প্রজেক্টের 'সেন্ট্রাল এন্ট্রি-পয়েন্ট' ব্রেইন ফাইল | অপরিবর্তিত ✅ | রুট README-তে মার্জ | এন্ট্রি-পয়েন্ট গভীর নেস্টে বিভ্রান্তিকর |
| REAL_TESTING_LOG.md | audit_reports/supreme-deep-audit-reports | রিয়েল টেস্টিং/ভেরিফিকেশন লগ (বাংলা) | অপরিবর্তিত ✅ | reports/archive/ | তারিখ-স্ট্যাম্পড টেস্ট-লগ স্ন্যাপশট |
| SECRETS.md | audit_reports/supreme-deep-audit-reports | সিক্রেটস/Infisical ভল্ট স্ট্র্যাটেজি (আসল কি নেই) | অপরিবর্তিত ✅ | docs/security/ | নীতি-ডক; secrets-management.md-তে মার্জ |
| STATUS.md | audit_reports/supreme-deep-audit-reports | সিস্টেম স্ট্যাটাস 'Single Source of Truth' | অপরিবর্তিত ✅ | রুট (repo root) | SSO ফাইল গভীর নেস্টে আটকে আছে |
| TIER_S_PATCH_GUIDE.md | audit_reports/supreme-deep-audit-reports | ১২টি Tier-S ফিচার প্যাচ গাইড | অপরিবর্তিত ✅ | reports/archive/ | ⚠️ 'Tier-S' মার্কেটিং-ধাঁচ; প্যাচ-সেশন স্ন্যাপশট |
| TODO.md | audit_reports/supreme-deep-audit-reports | ফেজ 13-17 অডিট TODO (CVE ফলাফলসহ) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সক্রিয় অডিট ট্র্যাকার |
| implementation_plan.md | audit_reports/supreme-deep-audit-reports | AETHEL Command Center টুডু-কমপ্লিশন প্ল্যান | aethel-command-center-plan.md | reports/archive/ | নামে টপিক নেই; এক-সেশন প্ল্যান |
| refactoring_suggestions.md | audit_reports/supreme-deep-audit-reports | ৭৮৭-সাজেশনের রিফ্যাক্টরিং রিপোর্ট (জেনারেটেড) | অপরিবর্তিত ✅ | reports/archive/ | তারিখ-স্ট্যাম্পড জেনারেটেড রিপোর্ট |
| render_deployment_failure_logs.md | audit_reports/supreme-deep-audit-reports | Render ডিপ্লয় ফেইলিউর লগ (2026-08-13) | অপরিবর্তিত ✅ | reports/archive/ | ইনসিডেন্ট-লগ স্ন্যাপশট |
| agent_rules.json | config | cine এজেন্ট রুলস স্কিমা v2 (নতুন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনফিগ ডিরে সঠিক, ক্যানোনিক্যাল স্কিমা |
| audit-rules.yml | config | সিক্রেট/রিস্ক প্যাটার্ন ডিটেকশন রুল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| compliance-rules.yml | config | Docker কমপ্লায়েন্স রুল (non-root ইত্যাদি) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| docker-limits.yml | config | প্রতি-সার্ভিস Docker সাইজ লিমিট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| dummy_registry.json | config | ডামি স্কিল রেজিস্ট্রি (টেস্ট ফিক্সচার) | অপরিবর্তিত ✅ | tests/fixtures/ | ডামি ডেটা ফিক্সচার-ডিরেতে ভালো |
| firestore.indexes.json | config | Firestore ইনডেক্স কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | Firebase CLI কনভেনশন |
| firestore.rules | config | Firestore সিকিউরিটি রুলস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | Firebase CLI কনভেনশন |
| kilo.json | config | Kilo AI (kilo.ai) এডিটর কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টুল-কনফিগ, স্কিমা-নাম সঠিক |
| promptfooconfig.yaml | config | promptfoo LLM ইভাল কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | promptfoo ডিফল্ট নামকরণ |
| proxy_list.json | config | ফ্রি/প্রিমিয়াম প্রক্সি প্রোভাইডার তালিকা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | রানটাইম ডেটা, নাম সঠিক |
| routing_policy.json | config | কমপ্লেক্সিটি-ভিত্তিক মডেল রাউটিং পলিসি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| ADMIN_TASKS.md | docs | অ্যাডমিন-অনলি প্রোডাকশন সেটআপ টাস্ক | admin-tasks.md | docs/operations/ | kebab-case + operations ডিরেতে খাপে |
| AGENTS.md | docs | এজেন্ট ডিরেক্টিভ — .agents কপির ভিন্ন ভার্সন | অপরিবর্তিত ✅ | _archive/ | ডুপ্লিকেট; .agents কপি ক্যানোনিক্যাল |
| AI_AGENT_ANTIPATTERN_PLAYBOOK.md | docs | অ্যান্টি-প্যাটার্ন প্লেবুক v3.0 (লিভিং ডক) | ai-agent-antipattern-playbook.md | অপরিবর্তিত ✅ | kebab-case; ক্যানোনিক্যাল ভার্সন |
| ARCHITECTURE.md | docs | ক্যানোনিক্যাল আর্কিটেকচার রেফারেন্স (Render+PG) | অপরিবর্তিত ✅ | docs/architecture/ | আর্কিটেকচার ডক সেই ডিরেতেই |
| CI_DASHBOARD_INTEGRATION.md | docs | CI সামারি ↔ অ্যাডমিন ড্যাশবোর্ড ইন্টিগ্রেশন গাইড | ci-dashboard-integration.md | অপরিবর্তিত ✅ | kebab-case; ⚠️ 'SuperAI' ব্র্যান্ডিং শিরোনামে |
| CONFIG_CONTROL_PLANE.md | docs | কনফিগ কন্ট্রোল প্লেন (Phase 3) ডিজাইন | config-control-plane.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| CONFIG_REGISTRY_MIGRATION.md | docs | কনফিগ রেজিস্ট্রি মাইগ্রেশন প্ল্যান | config-registry-migration.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| CONVENTIONS.md | docs | কোডিং কনভেনশন ('ব্রেইন' ফাইল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম-টপিক মিল, পরিচিত অবস্থান |
| DECISION_LOG.md | docs | ডিসিশন লগ (ADR-স্টাইল এন্ট্রি) | decision-log.md | docs/architecture/ | ADR পরিবারের সাথে কোলোকেট |
| DEPLOYMENT_CHECKLIST.md | docs | ক্যানোনিক্যাল ডিপ্লয়মেন্ট চেকলিস্ট | deployment-checklist.md | docs/runbooks/ | রানবুক-ধর্মী অপারেশনাল চেকলিস্ট |
| FREE_TIER_STORAGE_PLAN.md | docs | Render ফ্রি-টিয়ার পারসিস্টেন্ট স্টোরেজ সমাধান | free-tier-storage-plan.md | docs/plans/ | প্ল্যান-ধর্মী ডক plans/-এ |
| KNOWN_ISSUES.md | docs | পরিচিত সমস্যা ও টেক-ডেট রেজিস্ট্রি | known-issues.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| PLUGIN_ARCHITECTURE_DECISION.md | docs | প্লাগিন ইকোসিস্টেম ADR (V2.1) | plugin-architecture-decision.md | docs/architecture/ | ADR docs/architecture/-এ থাকে |
| PLUGIN_SDK.md | docs | প্লাগিন SDK ডক (V1 ডিক্লারেটিভ) | plugin-sdk.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| PRODUCTION_READINESS_PLAN_V3.md | docs | v3 প্রোডাকশন-রেডিনেস প্ল্যান (Z.ai জেনারেটেড) | অপরিবর্তিত ✅ | reports/archive/ | ভার্সন-স্ট্যাম্পড স্ন্যাপশট প্ল্যান |
| REGRESSION_FIX_REPORT.md | docs | regression-fixes ব্রাঞ্চের ইমপ্লিমেন্টেশন রিপোর্ট | regression-fix-report.md | reports/archive/ | সেশন-জেনারেটেড রিপোর্ট, docs নয় |
| SPEC_KIT_ADOPTION.md | docs | Spec Kit গভর্নেন্স অ্যাডপশন রেকর্ড | spec-kit-adoption.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| SUPREMEAI_PRE_PRODUCTION_GO_LIVE_MASTER_TODO.md | docs | প্রি-প্রোডাকশন/গো-লাইভ মাস্টার চেকলিস্ট | go-live-checklist.md | docs/runbooks/ | ⚠️ 'MASTER' গ্র্যান্ডিওজ; রানবুক-চেকলিস্ট |
| SupremeAI_Complete_Documentation.docx | docs | 38KB সম্পূর্ণ ডকুমেন্টেশন (Word বাইনারি) | supremeai-complete-documentation.docx | অপরিবর্তিত ✅ | PascalCase → kebab; রিপোতে বাইনারি অ-আদর্শ |
| SUPREME_API_DATABASE_SPEC.md | docs/api-database | API/DB স্পেক — নিজেই HISTORICAL সতর্কতা | অপরিবর্তিত ✅ | _archive/ | ⚠️ সাপারসিডেড; ডক নিজেই ব্যবহার নিষেধ করে |
| agent_permissions_migration.sql | docs/api-database/migrations | এজেন্ট পারমিশন টেবিল SQL (Supabase) | অপরিবর্তিত ✅ | migrations/ | SQL মাইগ্রেশন docs/-এ নয় |
| ai_memory_migration.sql | docs/api-database/migrations | ai_memory টেবিল SQL মাইগ্রেশন | অপরিবর্তিত ✅ | migrations/ | SQL মাইগ্রেশন docs/-এ নয় |
| API_VERSIONING_STRATEGY.md | docs/api/versioning | API ভার্সনিং গাইডলাইন | api-versioning-strategy.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| 0002-self-evolution-security-boundaries.md | docs/architecture | ADR 0002: সেল্ফ-ইভোলিউশন সিকিউরিটি গেটিং | adr-002-self-evolution-security-boundaries.md | অপরিবর্তিত ✅ | ADR-001 নামকরণের সাথে সামঞ্জস্য |
| ADR-001-firestore-for-tenancy.md | docs/architecture | Firestore টেন্যান্সি ADR | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ADR কনভেনশন সঠিক |
| DEPLOYMENT_STRATEGY.md | docs/architecture | সেন্ট্রালাইজড ডিপ্লয়মেন্ট স্ট্র্যাটেজি | deployment-strategy.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| DFD-001-new-user-signup.md | docs/architecture | নতুন টেন্যান্ট সাইনআপ ডেটা-ফ্লো ডায়াগ্রাম | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | DFD কনভেনশন সঠিক |
| PRODUCTION_ENDPOINT_MAPPING.md | docs/architecture | প্রোডাকশন এন্ডপয়েন্ট ম্যাপিং (বাংলা) | production-endpoint-mapping.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| PROJECT_MODULES_COMPLETE_INVENTORY.md | docs/architecture | সম্পূর্ণ মডিউল/মাইক্রো-ফিচার ইনভেন্টরি (বাংলা) | module-inventory.md | অপরিবর্তিত ✅ | ⚠️ 'COMPLETE' দাবি; সংক্ষিপ্ত টপিক-নাম |
| SEQ-001-canary-deployment.md | docs/architecture | ক্যানারি ডিপ্লয়মেন্ট সিকোয়েন্স | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | SEQ কনভেনশন সঠিক |
| SUPREMEAI_CONSOLIDATION_AND_CLEANUP_PLAN.md | docs/architecture | কনসোলিডেশন ও ক্লিনআপ মাস্টার প্ল্যান | consolidation-cleanup-plan.md | অপরিবর্তিত ✅ | ⚠️ দীর্ঘ গ্র্যান্ডিওজ নাম |
| SUPREME_SYSTEM_ARCHITECTURE.md | docs/architecture | HA ব্লুপ্রিন্ট v3 'canonical' দাবিসহ | system-architecture-blueprint.md | অপরিবর্তিত ✅ | ⚠️ ARCHITECTURE.md/system-overview ওভারল্যাপ |
| SYSTEM_DIAGRAMS_AND_FLOWS.md | docs/architecture | সিস্টেম ডায়াগ্রাম ও ভিজ্যুয়াল ফ্লো | system-diagrams-and-flows.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| THEORY_OF_MIND_AND_DIGITAL_TWIN_DEEP_DIVE.md | docs/architecture | ToM ও ডিজিটাল-টুইন সিমুলেশন স্পেক | theory-of-mind-digital-twin.md | অপরিবর্তিত ✅ | দীর্ঘ নাম সংক্ষিপ্ত করুন |
| gcp-killer-stack.md | docs/architecture | GCP-বিকল্প জিরো-কস্ট সার্ভারলেস স্ট্যাক | zero-cost-serverless-stack.md | অপরিবর্তিত ✅ | ⚠️ 'killer' গ্র্যান্ডিওজ; GCP-পাথ রিটায়ার্ড |
| multi-platform-failover-strategy.md | docs/architecture | মাল্টি-ক্লাউড ফেইলওভার 'Hydra' স্ট্র্যাটেজি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| service_registry.yaml | docs/architecture | 3rd-party সার্ভিস/কস্ট রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম সঠিক (স্টেল পাথ-কমেন্ট নোট) |
| service_topology.yml | docs/architecture | frontend→backend টপোলজি SSO (CI পড়ে) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | CI-রেফারেন্সড — স্থানান্তর নিষেধ |
| system-overview.md | docs/architecture | হাই-লেভেল সিস্টেম আর্কিটেকচার ওভারভিউ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| tri-pillar-distribution-strategy.md | docs/architecture | ট্রাই-পিলার ডিস্ট্রিবিউশন কোর স্ট্র্যাটেজি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| architecture_decision_records.md | docs | 2026 ADR সংকলন (swarm রাউটিং ইত্যাদি) | adr-index.md | docs/architecture/ | ADR পরিবার architecture/-তে একত্র |
| SUPREME_BROWSER_MASTER_PLAN.md | docs/browser | অটোনোমাস ব্রাউজার স্যুট মাস্টার প্ল্যান v3 | browser-suite-plan.md | অপরিবর্তিত ✅ | ⚠️ 'SUPREME…MASTER' ব্র্যান্ডিং |
| SUPREME_CLIENTS_MASTER.md | docs/clients | ক্লায়েন্ট/থিন-রানটাইম মাস্টার প্ল্যান | clients-thin-runtime-plan.md | অপরিবর্তিত ✅ | ⚠️ 'MASTER' ব্র্যান্ডিং |
| competitor_analysis_report.md | docs | SupremeAI বনাম টপ AI মডেল বিশ্লেষণ (বাংলা) | competitor-analysis-report.md | reports/ | সেশন-জেনারেটেড বিশ্লেষণ রিপোর্ট |
| CI_DEBUGGING_ROADMAP.md | docs/devops | CI ফেইলিউর ট্রায়াজ ১০-ধাপ রোডম্যাপ | ci-debugging-roadmap.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| SUPREME_DEVOPS_DEPLOYMENT.md | docs/devops | DevOps/CI-CD মাস্টার প্ল্যান v3 | devops-deployment-plan.md | অপরিবর্তিত ✅ | ⚠️ ব্র্যান্ড-প্রিফিক্স |
| WORKER_POLICY_AND_CAPACITY_PLAN.md | docs/devops | Uvicorn ওয়ার্কার পলিসি (AUD-1.2) | worker-policy-capacity-plan.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| SUPREME_AI_INTELLIGENCE_MASTER.md | docs/intelligence | ইন্টেলিজেন্স/সেল্ফ-ইভোলিউশন ব্লুপ্রিন্ট v3 | intelligence-blueprint.md | অপরিবর্তিত ✅ | ⚠️ 'SUPREME…MASTER' ব্র্যান্ডিং |
| BACKUP_RESTORE_POLICY.md | docs/operations | ব্যাকআপ/রিস্টোর পলিসি (AUD-5.7) | backup-restore-policy.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| FREE_TIER_FEDERATION_MASTER_PLAN_V4.md | docs/plans | ফ্রি-টিয়ার ফেডারেশন প্ল্যান v4 (বাংলা) | free-tier-federation-plan.md | অপরিবর্তিত ✅ | ⚠️ 'MASTER'+ভার্সন-সাফিক্স; সর্বশেষ ক্যানোনিক্যাল |
| FREE_TIER_FEDERATION_PLAN_V3.md | docs/plans | ফেডারেশন প্ল্যান v3 (সাপারসিডেড) | অপরিবর্তিত ✅ | _archive/ | V4 সাপারসিডেড স্ন্যাপশট |
| FREE_TIER_UPGRADE_PLAN.md | docs/plans | ফ্রি-টিয়ার আপগ্রেড প্ল্যান v2.1 (পুরনো) | অপরিবর্তিত ✅ | _archive/ | v2-যুগের প্ল্যান, V3/V4 সাপারসিডেড |
| MISSING_SERVICES_INTEGRATION_PLAN_V4.1.md | docs/plans | ফেডারেশন প্ল্যান v4.1 আপডেট | অপরিবর্তিত ✅ | docs/plans/ (V4 ফাইলে মার্জ) | একই প্ল্যানের আংশিক আপডেট |
| PRODUCTION_UPGRADE_PLAN.md | docs/plans | প্রোডাকশন আপগ্রেড প্ল্যান v2.0 (পুরনো) | অপরিবর্তিত ✅ | _archive/ | v2-যুগের স্ন্যাপশট প্ল্যান |
| DEPENDENCY_POLICY.md | docs/security | ডিপেন্ডেন্সি পলিসি ও এক্সেপশন (AUD-7.8) | dependency-policy.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| SUPREME_SECURITY_GOVERNANCE.md | docs/security | সিকিউরিটি/থ্রেট-মডেল গভর্নেন্স মাস্টার প্ল্যান | security-governance-plan.md | অপরিবর্তিত ✅ | ⚠️ ব্র্যান্ড-প্রিফিক্স; threat-model.md ওভারল্যাপ |
| THREAT-MODEL-001-authentication.md | docs/security | অথেনটিকেশন থ্রেট-মডেল 001 | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | THREAT-MODEL কনভেনশন সঠিক |
| TOOL_EXECUTION_INVENTORY.md | docs/security | প্রোডাকশন টুল-এক্সিকিউশন ইনভেন্টরি | tool-execution-inventory.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| VULN-SSLCOMMERZ-WEBHOOK.md | docs/security | SSLCommerz ওয়েবহুক ভাল্ন অ্যাডভাইজরি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | VULN-ID কনভেনশন সঠিক |
| blindspots-bangla.md | docs/security | সিস্টেম ব্লাইন্ড-স্পট ফুল লিস্ট (বাংলা) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| blink_spots_gemini.md | docs/security | Gemini-র করা গ্যাপ/ব্লাইন্ড-স্পট বিশ্লেষণ | blindspots-gemini.md | অপরিবর্তিত ✅ | ⚠️ 'blink' টাইপো; টুইন ডক-এর সাথে সামঞ্জস্য |
| SECURITY_HEADERS_CONFIG.md | docs/security/headers | HTTP সিকিউরিটি হেডার সেটআপ গাইড | security-headers-config.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| OWASP_COMPLIANCE_CHECKLIST.md | docs/security/owasp | OWASP Top-10 কমপ্লায়েন্স চেকলিস্ট | compliance-checklist.md | অপরিবর্তিত ✅ | owasp/ ডিরেতে প্রিফিক্স রিডান্ডেন্ট |
| PENETRATION_TESTING_GUIDE.md | docs/security/pentest | পেনিট্রেশন টেস্টিং ফ্রেমওয়ার্ক গাইড | penetration-testing-guide.md | অপরিবর্তিত ✅ | pentest/ ডিরেতে প্রিফিক্স রিডান্ডেন্ট |
| secrets-management.md | docs/security | সিক্রেটস স্টোরেজ/রোটেশন পলিসি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত (SECRETS.md মার্জ) |
| threat-model.md | docs/security | সিস্টেম থ্রেট মডেল ও মাইটিগেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| SECURITY_SCAN_CONFIG.md | docs/security/vulnerability-scan | Trivy/Snyk/Bandit স্ক্যান কনফিগ গাইড | security-scan-config.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| superai_competitor_playbook.md | docs | 'SuperAI' কম্পিটিটিভ ইন্টেলিজেন্স প্লেবুক | competitor-playbook.md | অপরিবর্তিত ✅ | ⚠️ 'SuperAI' ব্র্যান্ডিং |
| supremeai_analysis.md | docs | AI-জেনারেটেড কোডবেস অডিট রিপোর্ট (08-22) | অপরিবর্তিত ✅ | reports/archive/ | তারিখ-স্ট্যাম্পড অডিট স্ন্যাপশট |
| supremeai_roadmap.png | docs | রোডম্যাপ ইমেজ — প্রকৃতপক্ষে Git LFS পয়েন্টার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ⚠️ LFS পয়েন্টার (131B) — আসল ইমেজ অনুপস্থিত |
| TECHNICAL_SPECIFICATION.md | docs/technical-specs | v1.0.0 টেকনিক্যাল স্পেসিফিকেশন | technical-specification.md | অপরিবর্তিত ✅ | kebab-case সামঞ্জস্য |
| SUPREMEAI_2_CURRENT_STATE_AUDIT.md | docs/ui-ux | ফ্রন্টএন্ড রুট/পোর্টাল কারেন্ট-স্টেট অডিট | ui-current-state-audit.md | অপরিবর্তিত ✅ | ⚠️ 'SUPREMEAI_2' ভার্সন-ব্র্যান্ডিং |
| SUPREME_UI_DASHBOARD_MASTER.md | docs/ui-ux | ড্যাশবোর্ড/ডিজাইন-সিস্টেম মাস্টার প্ল্যান v3 | dashboard-design-system-plan.md | অপরিবর্তিত ✅ | ⚠️ 'SUPREME…MASTER' ব্র্যান্ডিং |
| dashboard_design_blueprint.md | docs/ui-ux | অ্যাডমিন+ইউজার ড্যাশবোর্ড ডিজাইন ব্লুপ্রিন্ট | dashboard-design-blueprint.md | অপরিবর্তিত ✅ | snake → kebab-case |
| check_deploy_gate.py | infrastructure | Firestore-ভিত্তিক ডিপ্লয়-গেট ভেরিফায়ার | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ইনফ্রা স্ক্রিপ্ট, নাম সঠিক |
| enhanced-worker-v2.js | infrastructure/cloudflare | 'Reduced entry point' — আনওয়্যার্ড ভ্যারিয়েন্ট | অপরিবর্তিত ✅ | _archive/ | wrangler এটিকে ব্যবহার করে না |
| enhanced-worker.js | infrastructure/cloudflare | এজ কম্পিউটিং ওয়ার্কার (wrangler main) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনফিগ-রেফারেন্সড এন্ট্রি ফাইল |
| auth-checker.js | infrastructure/cloudflare/worker-modules | ওয়ার্কার অথ মডিউল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | মডিউলার কাঠামো সঠিক |
| cache-handler.js | infrastructure/cloudflare/worker-modules | ওয়ার্কার ক্যাশ মডিউল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | মডিউলার কাঠামো সঠিক |
| response-builder.js | infrastructure/cloudflare/worker-modules | ওয়ার্কার রেসপন্স মডিউল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | মডিউলার কাঠামো সঠিক |
| router.js | infrastructure/cloudflare/worker-modules | ওয়ার্কার রাউটিং মডিউল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | মডিউলার কাঠামো সঠিক |
| worker.js | infrastructure/cloudflare | বেসিক fetch হ্যান্ডলার (পুরনো ভ্যারিয়েন্ট) | অপরিবর্তিত ✅ | _archive/ | enhanced-worker সাপারসিডেড ভ্যারিয়েন্ট |
| wrangler.toml | infrastructure/cloudflare | ক্লাউডফ্লেয়ার কনফিগ (main=enhanced-worker.js) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | সক্রিয় মডিউলার সেটআপ |
| cloudflare_worker.js | infrastructure | সার্কিট-ব্রেকারসহ রুট-লেভেল ওয়ার্কার | অপরিবর্তিত ✅ | infrastructure/cloudflare/ | ডুপ্লিকেট সেটআপ — cloudflare/ ডিরেতে একত্র |
| deploy.ps1 | infrastructure | GCP/Railway/Render ডিপ্লয় অর্কেস্ট্রেটর | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ইনফ্রা ডিপ্লয় স্ক্রিপ্ট সঠিক |
| namespace.yaml | infrastructure/kubernetes | K8s নেমস্পেস বেস ম্যানিফেস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনভেনশন সঠিক |
| supremeai-overview.json | infrastructure/monitoring/grafana/dashboards | Grafana ওভারভিউ ড্যাশবোর্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | Grafana কনভেনশন সঠিক |
| otel-collector-config.yaml | infrastructure/monitoring/opentelemetry | OpenTelemetry কালেক্টর কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনভেনশন সঠিক |
| alert_rules.yml | infrastructure/monitoring/prometheus | Prometheus অ্যালার্ট রুল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনভেনশন সঠিক |
| prometheus.yml | infrastructure/monitoring/prometheus | Prometheus স্ক্রেপ কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনভেনশন সঠিক |
| wrangler.toml | infrastructure | রুট ক্লাউডফ্লেয়ার কনফিগ (main=cloudflare_worker.js) | অপরিবর্তিত ✅ | _archive/ | ডুপ্লিকেট wrangler — cloudflare/ ক্যানোনিক্যাল |
| coldstart_knowledge_seed_comprehensive.json | knowledge | কোল্ড-স্টার্ট নলেজ সিড (স্কিমা 2.0) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | লোডার-রেফারেন্সড (পাথ-বাগ নোট) |
| coldstart_knowledge_seed_expanded.json | knowledge | সম্প্রসারিত ফলব্যাক সিড কাঠামো | অপরিবর্তিত ✅ | _archive/ | ৩ সিড-ভ্যারিয়েন্ট রিডান্ডেন্সি |
| coldstart_knowledge_seed_knowledge_base.json | knowledge | জেনারেটেড ক্যানোনিক্যাল সিড (স্কিমা 2.1) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | gen_knowledge_seed আউটপুট, ক্যানোনিক্যাল |
| goldset.json | knowledge | রিট্রিভাল ইভাল গোল্ডসেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | validate_retrieval স্ক্রিপ্ট-রেফারেন্সড |
| add_user_id_to_ai_memory.sql | migrations | ai_memory-তে user_id কলাম SQL | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | রুট migrations/ ক্যানোনিক্যাল SQL হোম |
| phase3_multi_tenant_schema.sql | migrations | মাল্টি-টেন্যান্ট স্কিমা SQL (user_keys ইত্যাদি) | multi-tenant-schema.sql | অপরিবর্তিত ✅ | ⚠️ 'phase3' স্প্রিন্ট-নাম টপিক লুকায় |
| codebase_fixes_applied.md | reports | প্রয়োগকৃত ফিক্স রিপোর্ট (08-07, In Progress) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | reports/ সঠিক, লাইভ ট্র্যাকার |
| codebase_issues_report.md | reports | ভেরিফায়েড কোডবেস ইস্যু রিপোর্ট (08-07) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| duplicates.json | reports | ১৯ ডুপ্লিকেট-গ্রুপের অ্যানালাইসিস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড অ্যানালাইসিস আর্টিফ্যাক্ট |
| import_analysis.json | reports | ১৮৭ ফাইলের ইমপোর্ট অ্যানালাইসিস | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | জেনারেটেড অ্যানালাইসিস আর্টিফ্যাক্ট |
| knowledge_cards_v2_lifecycle.json | reports | নলেজ-কার্ড লাইফসাইকেল রেজিস্ট্রি ডেটা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ⚠️ ভাঙা JSON (লাইন ~২৬৯ পার্স-এরর) |
| pipeline_recipe_registry.json | reports | পাইপলাইন রেসিপি রেজিস্ট্রি (রানটাইম ডেটা) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | রেজিস্ট্রি ডেটা, নাম সঠিক |
| tool_knowledge_registry.json | reports | টুল-নলেজ রেজিস্ট্রি কার্ড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | রেজিস্ট্রি ডেটা, নাম সঠিক |
| __init__.py | skills | রুট-লেভেল skills প্যাকেজ মার্কার | অপরিবর্তিত ✅ | backend/skills/ | backend থেকে ইমপোর্ট হয় — প্যাকেজ একত্র |
| csv_exporter.py | skills/dynamic | ডাইনামিক স্কিল: CSV এক্সপোর্টার | অপরিবর্তিত ✅ | backend/skills/ | backend self_evolution এটি ব্যবহার করে |
| text_summarizer.py | skills/dynamic | ডাইনামিক স্কিল: টেক্সট সামারাইজার | অপরিবর্তিত ✅ | backend/skills/ | backend self_evolution এটি ব্যবহার করে |
| web_scraper.py | skills/dynamic | ডাইনামিক স্কিল: httpx ওয়েব স্ক্র্যাপার | অপরিবর্তিত ✅ | backend/skills/ | backend self_evolution এটি ব্যবহার করে |
| installer.py | skills | SkillInstaller (রিপো ক্লোন/ইনস্টল) | অপরিবর্তিত ✅ | backend/skills/ | auto_skill_creator ইমপোর্ট করে |
| marketplace.py | skills | SkillMarketplace সার্ভিস | অপরিবর্তিত ✅ | backend/skills/ | backend প্যাকেজে একত্র করুন |
| registry.py | skills | SkillRegistry (JSON রেজিস্ট্রি লোডার) | অপরিবর্তিত ✅ | backend/skills/ | backend প্যাকেজে একত্র করুন |
| schema.py | skills | UniversalSkillSchema (pydantic ভ্যালিডেটর) | অপরিবর্তিত ✅ | backend/skills/ | backend প্যাকেজে একত্র করুন |
| configuration.md | specs/001-dynamic-production-configuration/checklists | কনফিগ গভর্নেন্স রিকোয়ারমেন্ট চেকলিস্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ট্যান্ডার্ড স্ট্রাকচার |
| config-contract.md | specs/001-dynamic-production-configuration/contracts | ক্যানোনিক্যাল কনফিগ-কি কন্ট্রাক্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ট্যান্ডার্ড স্ট্রাকচার |
| data-model.md | specs/001-dynamic-production-configuration | কনফিগ-ডোমেইন ডেটা মডেল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ট্যান্ডার্ড স্ট্রাকচার |
| plan.md | specs/001-dynamic-production-configuration | ইমপ্লিমেন্টেশন প্ল্যান | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ট্যান্ডার্ড স্ট্রাকচার |
| quickstart.md | specs/001-dynamic-production-configuration | ভ্যালিডেশন ড্রিল কুইকস্টার্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ট্যান্ডার্ড স্ট্রাকচার |
| research.md | specs/001-dynamic-production-configuration | রিসার্চ ও সিদ্ধান্ত (ডিরেক্ট ইন্সপেকশন) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ট্যান্ডার্ড স্ট্রাকচার |
| spec.md | specs/001-dynamic-production-configuration | ফিচার স্পেসিফিকেশন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ট্যান্ডার্ড স্ট্রাকচার |
| tasks.md | specs/001-dynamic-production-configuration | ডিপেন্ডেন্সি-অর্ডারড টাস্ক তালিকা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | speckit স্ট্যান্ডার্ড স্ট্রাকচার |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- "ব্রেইন"/SSO ফাইলগুলো (README.md, STATUS.md, LESSONS_LEARNED, CONTRIBUTING) audit_reports/supreme-deep-audit-reports/ গর্ভে বন্দি — রুট বা docs/-এ তোলা জরুরি; .agents/AGENTS.md STATUS.md-কে SSO বলেও সেটি প্রায় অগম্য।
- ⚠️ 'SUPREME_*/…MASTER — v3.0 Canonical Source of Truth' সিরিজ (browser, clients, devops, intelligence, security, ui-ux, system-architecture) — একই টেমপ্লেটে ৭টি গ্র্যান্ডিওজ ব্র্যান্ডেড প্ল্যান; ব্র্যান্ড-সাফিক্স সরিয়ে টপিক-নাম দেওয়ার প্রস্তাব।
- Cloudflare Worker-এর ২টি সমান্তরাল সেটআপ: রুট wrangler.toml+cloudflare_worker.js বনাম cloudflare/wrangler.toml+enhanced-worker.js (+আনওয়্যার্ড v2 ও worker.js) — এক ক্যানোনিক্যাল সেটআপে কনসোলিডেট করুন।
- ডুপ্লিকেট/টুইন ডক-জোড়া: AGENTS.md (.agents বনাম docs), AI_AGENT_ANTIPATTERN_PLAYBOOK (docs v3 বনাম .agents পুরনো কপি), AUDIT_MASTER_CHECKLIST (.gemini/temp_patch বনাম audit_reports), SECRETS.md বনাম docs/security/secrets-management.md — ক্যানোনিক্যাল একটি রাখুন।
- স্ন্যাপশট প্ল্যান-চেইন: ফ্রি-টিয়ার ফেডারেশন V3→V4→V4.1, PRODUCTION_UPGRADE v2.0, READINESS v3 — পুরনোগুলো _archive/-এ; V4.1 V4-ফাইলে মার্জ প্রস্তাব।
- অ্যানোমালি: docs/supremeai_roadmap.png আসলে 131-বাইট Git LFS পয়েন্টার (আসল ইমেজ নেই); reports/knowledge_cards_v2_lifecycle.json পার্স-ভাঙা JSON; .github/actions-এ কমিটেড CI ফেইল-লগ।
- .github/scripts/-এর ৪টি বাংলা ওয়ার্কফ্লো-ডক docs/devops/bn/-এ সরান; এগুলো এমন workflow ফাইলনাম (supreme-ci.yml, maintenance_pipeline.yml) রেফারেন্স করে যা .github/workflows/-এ নেই — স্টেল ডকুমেন্টেশন।
- কনভেনশন-লকড ফাইল অপরিবর্তিত থাকা উচিত: .github CI, .specify/speckit স্ক্যাফোল্ড, SKILL.md, CODEOWNERS, CI-রেফারেন্সড service_topology.yml; রুট skills/ প্যাকেজ backend-এ ব্যবহৃত → backend/skills/-এ স্থানান্তর; docs/api-database/migrations/ SQL রুট migrations/-এ একত্র করুন।


---

## ব্যাচ ১৫ — Repository Root ফাইল
**ব্যাচ:** 15 | **তালিকাভুক্ত:** 68 | **বিশ্লেষিত:** 68 | **অনুপস্থিত/স্কিপ:** 0 | **রিনেম প্রস্তাব:** 19 | **স্থানান্তর প্রস্তাব:** 14 | **⚠️ সেমান্টিক মিসম্যাচ:** 5

| বর্তমান নাম | বর্তমান অবস্থান | কন্টেন্ট সারাংশ | সাজেস্টেড নাম | সাজেস্টেড অবস্থান | কারণ |
|---|---|---|---|---|---|
| .actionlint.json | ./ | actionlint (GitHub Actions linter) শেল/পারমিশন কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড root টুল কনফিগ |
| .aiignore | ./ | AI অ্যাসিস্ট্যান্ট ignore রুল (ক্যাশ/বিল্ড আর্টিফ্যাক্ট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনভেনশন ঠিক; ×৬ ডুপ্লিকেট সিঙ্ক ঝুঁকি |
| .clineignore | ./ | .aiignore-এর byte-identical কপি (Cline) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টুল-বাধ্যতামূলক নাম; CI সিঙ্ক দরকার |
| .codegeexignore | ./ | .aiignore-এর ডুপ্লিকেট কপি (CodeGeeX) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টুল-বাধ্যতামূলক নাম; সিঙ্ক ঝুঁকি |
| .cursorignore | ./ | .aiignore-এর ডুপ্লিকেট কপি (Cursor) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টুল-বাধ্যতামূলক নাম |
| .env.example | ./ | ১৮১-লাইন এনভায়রনমেন্ট ভেরিয়েবল টেমপ্লেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড env টেমপ্লেট |
| .eslintrc.js | ./ | legacy ESLint কনফিগ (TS strict + react রুল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্টেল tsconfig প্রজেক্ট-রেফারেন্স ফিক্স দরকার |
| .firebaserc | ./ | Firebase প্রজেক্ট ও hosting টার্গেট ম্যাপ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড Firebase কনফিগ |
| .gcloudignore | ./ | gcloud ডিপ্লয় এক্সক্লুশন তালিকা | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | ডিপ্লয়-টুল কনভেনশন |
| .gitattributes | ./ | ইমেজ ফাইলের LFS ফিল্টার রুল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড git কনফিগ |
| .gitignore | ./ | ৫৯৯-লাইন বিস্তৃত ignore রুল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড; দীর্ঘ হলেও কার্যকর |
| .gitleaks.toml | ./ | gitleaks কাস্টম রুল + টেস্ট allowlist | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড সিক্রেট-স্ক্যান কনফিগ |
| .kiloignore | ./ | .aiignore-এর ডুপ্লিকেট কপি (Kilo) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টুল-বাধ্যতামূলক নাম |
| .knip.json | ./ | knip dead-code কনফিগ; entry src/main.tsx অস্তিত্বহীন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | পাথ স্টেল — frontend-মুখী ফিক্স দরকার |
| .lingma/rules/agents.md | .lingma/rules/ | Lingma always-on এজেন্ট ডিরেক্টিভ (SSOT: STATUS.md) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টুল-নির্দিষ্ট ডিরেক্টরি বাধ্যতামূলক |
| .npmrc | ./ | pnpm frozen-lockfile=false সেটিং | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড npm কনফিগ |
| .nvmrc | ./ | Node 24 ভার্সন পিন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড ভার্সন পিন |
| .pre-commit-config.yaml | ./ | pre-commit হুক (ফাইল-ইন্টিগ্রিটি গেট) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড হুক কনফিগ |
| .qoderignore | ./ | .aiignore-এর ডুপ্লিকেট কপি (Qoder) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টুল-বাধ্যতামূলক নাম |
| .secrets-allowlist.json | ./ | GitHub secret-scanning false-positive allowlist | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | টুল-রেফারেন্সড allowlist |
| AGENTS.md | ./ | ৭৫৬-লাইন AI এজেন্ট কনফিগ/আচরণ গাইড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড এজেন্ট-প্রোটোকল ফাইল |
| CHECKPOINT.md | ./ | pre-commit হুকে অটো-আপডেট হওয়া সেশন চেকপয়েন্ট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | এজেন্ট প্রোটোকল; হুক-রেফারেন্সড |
| CODEOWNERS | ./ | ২৭-লাইন মালিকানা ম্যাপ (SaifulHaqueNiloy) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড GitHub কনফিগ |
| CONTRIBUTING.md | ./ | ৮৫০-লাইন কন্ট্রিবিউশন গাইড | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড root ডক |
| ERROR_AUDIT.md | ./ | 2026-08-29 এরর অডিট রিপোর্ট (৪৭৩ লাইন) | error_audit_2026-08-29.md | reports/audits/ | তারিখ-স্ন্যাপশট রিপোর্ট root-এ নয় |
| FEATURE_TRACKING_LOG.md | ./ | এজেন্ট ফিচার-ট্র্যাকিং টেবিল (append-only) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | এজেন্ট প্রোটোকল লগ |
| LESSONS_LEARNED.md | ./ | কালানুক্রমিক লেসন-লার্ন্ড লগ ("Brain" ফাইল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | এজেন্ট প্রোটোকল লগ |
| LICENSE | ./ | MIT লাইসেন্স (2026) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| PATCH_NOTES_v2.md | ./ | audit patch v2 নোট (2026-08-30 স্ন্যাপশট) | অপরিবর্তিত ✅ | _archive/patches/ | সংস্করণ-নির্দিষ্ট প্যাচ স্ন্যাপশট |
| PATCH_NOTES_v3.md | ./ | audit patch v3 নোট (রি-ভেরিফিকেশন) | অপরিবর্তিত ✅ | _archive/patches/ | সংস্করণ-নির্দিষ্ট প্যাচ স্ন্যাপশট |
| README.md | ./ | ৯৪৫-লাইন প্রজেক্ট README (ব্যাজ, আর্কিটেকচার) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| REAL_TESTING_LOG.md | ./ | রিয়েল-টেস্টিং প্রোটোকল লগ (ভেরিফিকেশন টেবিল) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | এজেন্ট প্রোটোকল লগ |
| SECRETS.md | ./ | Infisical/GitHub secrets ম্যানেজমেন্ট স্ট্র্যাটেজি (কোনো সিক্রেট নেই) | SECRETS_MANAGEMENT.md ⚠️ | docs/security/ | নাম বিভ্রান্তিকর — আসলে স্ট্র্যাটেজি ডক |
| SECRETS_AUDIT.md | ./ | _audit.py দিয়ে জেনারেটেড secrets অডিট রিপোর্ট | secrets_audit_2026-08-29.md | reports/audits/ | জেনারেটেড স্ন্যাপশট root-এ নয় |
| SILENT_ERRORS_AUDIT.md | ./ | silent-error AST স্ক্যান রিপোর্ট (2026-08-28) | অপরিবর্তিত ✅ | reports/audits/ | পয়েন্ট-ইন-টাইম অডিট স্ন্যাপশট |
| STATUS.md | ./ | লাইভ সিস্টেম স্ট্যাটাস SSOT (এজেন্ট-রেফারেন্সড) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | এজেন্ট প্রোটোকল SSOT |
| TIER_S_PATCH_GUIDE.md | ./ | ৭০৭-লাইন Tier-S ফিচার প্যাচ গাইড | tier_s_patch_guide.md | docs/guides/ | গাইড ডক — root clutter কমান |
| TODO.md | ./ | Phase 13–17 audit TODO — সব checkbox ✓ | অপরিবর্তিত ✅ | _archive/ | সম্পন্ন অডিট তালিকা — আর্কাইভ |
| _audit.py | ./ | ৩৬৫-লাইন secrets অডিট স্ক্রিপ্ট (Infisical/GH/Render) | audit_secrets.py | scripts/security/ | root স্ক্রিপ্ট; আন্ডারস্কোর-নাম অস্পষ্ট |
| admin-dashboard-after-fix.png | ./ | ১৩০-বাইট প্লেসহোল্ডার স্টাব (আসল স্ক্রিনশট নয়) | মুছে ফেলুন ⚠️ | — | নাম বনাম কনটেন্ট মিসম্যাচ; ফাঁকা স্টাব |
| agent-ctx/s7-s12-backend-routes.md | agent-ctx/ | S7–S12 রাউট ফাইলের সেশন ওয়ার্ক-রেকর্ড | অপরিবর্তিত ✅ | _archive/agent-ctx/ | সেশন ওয়ার্ক-লগ স্ন্যাপশট |
| apply_patch.py | ./ | হার্ডকোডেড Windows-পাথ টেক্সট-রিপ্লেস প্যাচার | মুছে ফেলুন | — | এক-অফ প্যাচ, ইতিমধ্যে প্রয়োগ হয়েছে |
| apply_tier_patch.py | ./ | CI workflow_dispatch ইনপুট প্যাচার (এক-অফ) | মুছে ফেলুন | — | এক-অফ প্যাচ — ইতোমধ্যে প্রয়োগ |
| configs/train/bengali_lora.yaml | configs/train/ | বাংলা LoRA ফাইন-টিউন রেসিপি (Qwen/Llama) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | নাম ও অবস্থান উপযুক্ত |
| conftest.py | ./ | backend/ কে sys.path-এ যোগকারী root conftest | মুছে ফেলুন | — | root tests/ ডিরেক্টরি অনুপস্থিত — অনাথ |
| docker-compose.production.yml | ./ | ২৯২-লাইন প্রোডাকশন compose (multi-service) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | প্রচলিত root কনফিগ |
| docker-compose.yml | ./ | লোকাল dev compose (backend 8080) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড; package.json পাথ-ভুল দেখুন |
| firebase-admin-dashboard.png | ./ | ১৩০-বাইট প্লেসহোল্ডার স্টাব | মুছে ফেলুন ⚠️ | — | নাম বনাম কনটেন্ট মিসম্যাচ |
| firebase.json | ./ | Firebase hosting/firestore ডিপ্লয় কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড Firebase কনফিগ |
| firebase.template.json | ./ | {{placeholder}} হোস্টিং টেমপ্লেট | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | generate_firebase_config.py রেফারেন্স করে |
| fix_fk.py | ./ | j9k0l1m2n3o4 মাইগ্রেশনের FK-মুছে ফেলার প্যাচ | মুছে ফেলুন | — | এক-অফ ফিক্স — ইতোমধ্যে প্রয়োগ |
| fix_migration.py | ./ | মাইগ্রেশনে idempotent create_table যোগের প্যাচ | মুছে ফেলুন | — | এক-অফ ফিক্স — ইতোমধ্যে প্রয়োগ |
| flowchart.png | ./ | ০-বাইট খালি ফাইল | মুছে ফেলুন ⚠️ | — | খালি ফাইল — নামের কিছু নেই |
| gcp-login.png | ./ | ১৩০-বাইট প্লেসহোল্ডার স্টাব | মুছে ফেলুন ⚠️ | — | নাম বনাম কনটেন্ট মিসম্যাচ |
| implementation_plan.md | ./ | AETHEL Command Center TODO কমপ্লিশন প্ল্যান | aethel_commandcenter_plan.md | _archive/plans/ | বিশৃঙ্খল নাম; সম্পন্ন প্ল্যান স্ন্যাপশট |
| mkdocs.yml | ./ | MkDocs Material সাইট কনফিগ (docs/) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড docs কনফিগ |
| package.json | ./ | monorepo root প্যাকেজ (turbo scripts, devDeps) | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড; docker script পাথ ভাঙা |
| playwright-ct.config.ts | ./ | কম্পোনেন্ট-টেস্ট কনফিগ; কোনো *.ct.spec.tsx নেই | মুছে ফেলুন | — | ম্যাচিং টেস্ট ফাইল অনুপস্থিত — নিষ্ক্রিয় |
| playwright.config.ts | ./ | E2E কনফিগ; testDir ./tests/e2e অস্তিত্বহীন | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | কনফিগ ঠিক; tests/e2e পুনরুদ্ধার দরকার |
| pnpm-lock.yaml | ./ | ১১K-লাইন pnpm লকফাইল | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড লকফাইল |
| pnpm-workspace.yaml | ./ | workspace: packages/*, frontend, vscode-ext | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড workspace কনফিগ |
| poll_render.py | ./ | হার্ডকোডেড deploy-ID পোলার (Render API) | মুছে ফেলুন | — | এক-অফ ডিপ্লয়-পোলার; হার্ডকোডেড ID |
| render_deployment_failure_logs.md | ./ | 2026-08-13 Render ডিপ্লয় ফেইলিয়র লগ | render_failure_log_2026-08-13.md | _archive/incidents/ | তারিখ-স্ন্যাপশট ইনসিডেন্ট লগ |
| secrets_registry.yaml | ./ | ১১১৮-লাইন ক্যানোনিকাল key→service রেজিস্ট্রি | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | অডিট টুল/CI-রেফারেন্সড রেজিস্ট্রি |
| supabase-ca.crt | ./ | Supabase প্রোডাকশন CA সার্টিফিকেট | অপরিবর্তিত ✅ | infrastructure/certs/ | কোডে অ-রেফারেন্সড infra অ্যাসেট |
| supremeai_performance_benchmark.json | ./ | LRUCache বেঞ্চমার্ক রান স্ন্যাপশট (2026-08-22) | perf_benchmark_2026-08-22.json | reports/benchmarks/ | এক-রান বেঞ্চমার্ক স্ন্যাপশট |
| tsconfig.json | ./ | root TS কনফিগ; include/paths → অস্তিত্বহীন ./src | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্টেল src পাথ — ফিক্স বা ডিলিট দরকার |
| turbo.json | ./ | Turborepo টাস্ক পাইপলাইন কনফিগ | অপরিবর্তিত ✅ | অপরিবর্তিত ✅ | স্ট্যান্ডার্ড monorepo কনফিগ |

### এই ডোমেইনের মূল পর্যবেক্ষণ
- Root ভারী: ৮+ পয়েন্ট-ইন-টাইম স্ন্যাপশট (ERROR_AUDIT, SILENT_ERRORS_AUDIT, SECRETS_AUDIT, PATCH_NOTES_v2/v3, TODO, render_deployment_failure_logs, benchmark json, implementation_plan) → reports/ বা _archive/-এ সরানোর প্রস্তাব।
- ৫টি one-off প্যাচ/ফিক্স স্ক্রিপ্ট (apply_patch, apply_tier_patch, fix_fk, fix_migration, poll_render) root-এ — সবই হার্ডকোডেড টার্গেট ও ইতিমধ্যে-প্রয়োগিত → ডিলিট; _audit.py একমাত্র পুনর্ব্যবহারযোগ্য → scripts/security/audit_secrets.py।
- স্টেল-কনফিগ ক্লাস্টার: root tsconfig.json ও .knip.json `./src` পাথ রেফার করে (root src/ নেই), playwright.config.ts testDir ./tests/e2e নেই, playwright-ct.config.ts-এর কোনো ct.spec ফাইল নেই, conftest.py root tests/-হীন অনাথ — একসময় root src/tests ছিল বলে মনে হয়।
- ৬টি AI-ignore ফাইল (.aiignore/.cursorignore/.clineignore/.codegeexignore/.kiloignore/.qoderignore) byte-identical (একই md5) — CI জেনারেশন/সিঙ্ক ছাড়া ড্রিফট অনিবার্য।
- package.json-এর docker:build/docker:up scripts অস্তিত্বহীন infrastructure/docker/docker-compose.yml রেফার করে; আসল compose ফাইল root-এ — স্ক্রিপ্ট পাথ ফিক্স দরকার।
- ৪টি "ছবি" বাস্তবে ফাঁপা: ৩টি ১৩০-বাইট প্লেসহোল্ডার png + flowchart.png ০-বাইট — মুছে ফেলুন; .gitattributes-এ LFS নিয়ম থাকলেও রিপোতে কার্যত কোনো আসল ইমেজ নেই।
- SECRETS.md-এ কোনো আসল সিক্রেট নেই (শুধু Infisical vault স্ট্র্যাটেজি), কিন্তু নামটি ভয় দেখায় — SECRETS_MANAGEMENT.md রিনেম প্রস্তাব; আসল সিক্রেট-ম্যাপ secrets_registry.yaml (রেফারেন্সড, root-এই থাকবে)।
- এজেন্ট-প্রোটোকল ফাইল (AGENTS.md, STATUS.md, CHECKPOINT.md, LESSONS_LEARNED.md, FEATURE_TRACKING_LOG.md, REAL_TESTING_LOG.md) root-এই রাখা যুক্তিসঙ্গত — .lingma/rules/agents.md STATUS.md-কে "Single Source of Truth" বলে রেফার করে।


---

## ৭. পরিশিষ্ট: পদ্ধতি ও সীমাবদ্ধতা

- **পদ্ধতি:** প্রতিটি ফাইল ডোমেইন-ভিত্তিক এজেন্ট দিয়ে সরাসরি পড়া হয়েছে (বড় ফাইলে header + definition grep); নাম শুধু দেখে সিদ্ধান্ত নেওয়া হয়নি।
- **সীমাবদ্ধতা:** runtime dependency graph ১০০% নিশ্চিত করা যায়নি — তাই ডিলিট/মুভের আগে importer grep আবার চালান; বাইনারি অ্যাসেট কনটেন্ট-বিশ্লেষণের বাইরে।
- **রেফারেন্স:** ব্যাচ-ভিত্তিক কাঁচা অংশগুলো এই ZIP-এর `parts/` ফোল্ডারে আলাদা ফাইল হিসেবেও রাখা আছে।

*রিপোর্ট তৈরি: 2026-09-07 08:17 · বেস কমিট: 61c9a49 · মোট 2,755 ফাইল রেকর্ড*