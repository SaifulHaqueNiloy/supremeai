# SupremeAI — সম্পূর্ণ Architecture Map
**তারিখ:** ১৯ আগস্ট, ২০২৬ | **রেপো:** `SaifulHaqueNiloy/supremeai` (main) | সরাসরি কোড বিশ্লেষণ করে বানানো, template না

---

## ১. আসল সিস্টেম ম্যাপ (যা সত্যিই ডিপ্লয় হয়)

`render.yaml` অনুযায়ী মাত্র **৩টা সার্ভিস** সত্যিই লাইভ:

```
┌─────────────────────┐      ┌──────────────────────┐
│  supremeai-frontend  │─────▶│   supremeai-backend   │  (main FastAPI monolith)
│  (static, React)     │      │   backend/core/app.py │
└─────────────────────┘      └──────────┬────────────┘
                                          │ proxy (SCRAPER_SERVICE_URL)
                                          ▼
                              ┌──────────────────────┐
                              │  supremeai-scraper    │  (Docker, Playwright)
                              │  backend/services/    │
                              │  scraper/              │
                              └──────────────────────┘
```

এইটুকু simple-rewrite-এর পর genuinely পরিষ্কার — আগের admin/user dual-backend জটিলতা সত্যিই সরানো হয়েছে। **এই অংশটা ভালো আছে, হাত দেওয়ার দরকার নেই।**

---

## ২. আসল সমস্যা: `backend/` ভেতরে ৩৪টা top-level subsystem

```
233  core/        117  api/         52  agents/      33  services/
 31  models/       27  scripts/     22  brain/       19  memory/
 14  engine/       11  evolution/   10  utils/         8  monitoring/
  8  middleware/    8  database/     8  alembic/       7  integrations/
  7  adaptive_engine/  5  skills/    4  workers/       4  p2p/
  4  byoc/          3  storage/      3  scout/         3  schemas/
  3  sandbox/       3  pipelines/    3  admin/         2  reports/
  1  ws/  ...  (Python ফাইল সংখ্যা)
```

প্রতিটা directory-কে "বাইরে থেকে import হয় কিনা" দিয়ে যাচাই করে দেখা গেল:

| Directory | ফাইল | বাইরে থেকে import | রায় |
|---|---|---|---|
| `evolution/` | ১১ | **০** | 🔴 সম্পূর্ণ dead scaffold |
| `p2p/` | ৪ | **০** | 🔴 সম্পূর্ণ dead |
| `scout/` | ৩ | **০** | 🔴 সম্পূর্ণ dead |
| `skills/` | ৫ | **০** | 🔴 সম্পূর্ণ dead |
| `byoc/` | ৪ | ১ (শুধু `api/routes/byoc_api.py`) | 🟡 প্রায় dead, ১ কলার আছে |
| `engine/` | ১৪ | ২ | 🟡 বেশিরভাগ dead |
| `adaptive_engine/` | ৭ | ৩ | 🟡 আংশিক ব্যবহৃত |
| `brain/` | ২২ | ১২ | 🟢 genuinely ব্যবহৃত |

**এই ৭টা directory-র মধ্যে ৪টা সম্পূর্ণ এবং ৩টা প্রায় dead** — অর্থাৎ ৩৪টার মধ্যে ~২০% ইতিমধ্যে ভূতুড়ে কোড, যেগুলো compile হয়, tests থাকতে পারে, কিন্তু live app কখনো ছোঁয় না।

---

## ৩. সবচেয়ে বড় আবিষ্কার — **৩টা আলাদা, প্রতিযোগী "Agent System"**

এইটাই সম্ভবত আপনার "সব একসাথে কাজ করে না মনে হচ্ছে" অনুভূতির সবচেয়ে বড় একক কারণ:

1. **`agents/`** (top-level, ৫২ ফাইল) — `devops/`, `domain/`, `evolution/`, `governance/`, `ide/`, `infrastructure/`, `monitoring/`, `syncguard/`, `ux/` উপ-ফোল্ডার সহ। যাচাই করে দেখা গেছে এই package-এর **৩২টা Agent ক্লাসের ২৯টাই** নিজের ফোল্ডারের বাইরে কোথাও instantiate হয় না।
2. **`tools/ai_agents/`** (১১ ফাইল) — এইটাই **আসল, লাইভ সিস্টেম**। প্রমাণ: `api/routes/agents.py`-তে নিজেরই একটা কমেন্ট আছে —
   > "আগে nonexistent `agents.legal_agent` ইত্যাদি import করে endpoints 500 দিত। এখন real `tools.ai_agents.*` ব্যবহার করা হয়।"

   অর্থাৎ কেউ একজন আগেই আবিষ্কার করেছিল যে `agents/` ভাঙা, আর route-গুলোকে `tools/ai_agents/`-এ সরিয়ে দিয়েছিল — কিন্তু পুরনো `agents/` ফোল্ডারটা কখনো মুছে ফেলা হয়নি।
3. **`models/dynamic_agent.py`** — একদম আলাদা তৃতীয় "Agent" ধারণা, যেটা `core/agent_factory.py` ব্যবহার করে।

**তিনটা ভিন্ন জিনিস, একই নাম, ভিন্ন উদ্দেশ্যে — এটাই একজন developer (বা AI session)-কে বিভ্রান্ত করবে প্রতিবার "agent" নিয়ে কাজ করার সময়।**

---

## ৪. একই নামের ফাইল/ফোল্ডার (module-identity সংঘর্ষ ঝুঁকি)

আগের রিপোতে (paykaribazaronline) ঠিক এই কারণেই দুটো real production bug হয়েছিল (`secret_vault`, `honeypot_middleware` দুইবার আলাদাভাবে import হয়ে দুটো ভিন্ন singleton তৈরি করেছিল)। এখানেও একই ঝুঁকি:

- **`evolution`** — top-level `evolution/`, `agents/evolution/`, `core/evolution/` — **৩ বার**
- **`config.py`** — `core/config.py`, `api/routes/config.py`, `api/routes/admin/config.py` — **৩ বার**
- **`llm_gateway.py`** — `core/llm/llm_gateway.py`, `api/routes/llm_gateway.py` — **২ বার**

## ৫. Top-level markdown ফাইল (১৭টা)
`AGENTS.md`, `ARCHITECTURE.md`, `CHECKPOINT.md`, `CONTRIBUTING.md`, `CONVENTIONS.md`, `DECISION_LOG.md`, `DEPLOYMENT_CHECKLIST.md`, `DEVELOPMENT_ROADMAP.md`, `FEATURE_TRACKING_LOG.md`, `KNOWN_ISSUES.md`, `LESSONS_LEARNED.md`, `PROJECT_REVIEW_AND_ROADMAP.md`, `REAL_TESTING_LOG.md`, `TODO.md`, `implementation_plan.md`, `out_of_box.md`, `README.md` — নিজেদের মধ্যে content overlap আছে কিনা এখনো check করা হয়নি (পরের ধাপ)।

## ৬. অন্যান্য পর্যবেক্ষণ
- `config/` বনাম `configs/` — দুটো ভিন্ন top-level ফোল্ডার, সম্পূর্ণ ভিন্ন content (agent rules বনাম ML training ডেটা) — নামের মিল বিভ্রান্তিকর।
- `core/tier8/` — নামটা অস্পষ্ট (কোনো internal codename মনে হচ্ছে, বাইরে থেকে বোঝা যায় না কী করে)।
- `api/` (৮৯টা route ফাইল) বনাম `tools/` (১৬টা sub-package) — দুটোরই যথেষ্ট justification আছে (routes বনাম business-logic), কিন্তু কিছু জায়গায় ওভারল্যাপ থাকতে পারে, যাচাই করা হয়নি।

---

## ৭. সুপারিশকৃত অগ্রাধিকার (safe → risky ক্রমে)

| ধাপ | কাজ | ঝুঁকি |
|---|---|---|
| ১ | `evolution/`, `p2p/`, `scout/`, `skills/` (০ ব্যবহার, নিশ্চিত) — সরিয়ে ফেলা বা archive | নিরাপদ |
| ২ | পুরনো `agents/` প্যাকেজ (২৯টা orphaned ক্লাস) — মুছে ফেলা, `tools/ai_agents/`-কে single source of truth করা | মাঝারি (৩টা ব্যবহৃত ক্লাস আগে migrate করতে হবে) |
| ৩ | `config.py`/`llm_gateway.py` ডুপ্লিকেট নাম — rename করে unique করা | মাঝারি (import path সব জায়গায় আপডেট লাগবে) |
| ৪ | `engine/`, `byoc/`, `adaptive_engine/` — deep-dive করে বাকি অংশও ব্যবহৃত কিনা যাচাই | সময়সাপেক্ষ |
| ৫ | ১৭টা markdown ফাইল — content দেখে consolidate | নিরাপদ কিন্তু ম্যানুয়াল |

---

**পরের ধাপ কোনটা দিয়ে শুরু করব?** #১ (নিশ্চিত dead code সরানো) সবচেয়ে নিরাপদ এবং দ্রুত — একবারে সবচেয়ে বেশি "clutter" কমাবে ঝুঁকি ছাড়াই।
