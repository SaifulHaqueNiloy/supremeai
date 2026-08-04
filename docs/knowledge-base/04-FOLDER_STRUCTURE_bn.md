# সুপ্রিম AI 2.0 — ফোল্ডার স্ট্রাকচার

**ভার্সন**: 2.0.0  
**শেষ আপডেট**: 2025-01-04  
**স্ট্যাটাস**: লিভিং ডকুমেন্ট  
**ক্লাসিফিকেশন**: ইন্টার্নাল  

---

## 📁 প্রজেক্ট স্ট্রাকচার ওভারভিউ

সুপ্রিম AI 2.0 একটি মনোরেপো আর্কিটেকচার অনুসরণ করে যেখানে ব্যাকএন্ড, ফ্রন্টএন্ড, ডকুমেন্টেশন এবং ইনফ্রাস্ট্রাকচার সব একই রিপোজিটরিতে থাকে। এই স্ট্রাকচার কোড শেয়ারিং, অ্যাটমিক কমিট এবং সিমপ্লিফাইড ডিপেন্ডেন্সি ম্যানেজমেন্ট সক্ষম করে।

### মূল ডিরেক্টরি

```
supremeai_2.0/
├── backend/                    # FastAPI ব্যাকএন্ড সার্ভিস
├── apps/                       # ফ্রন্টএন্ড অ্যাপ্লিকেশন
├── cloudflare-worker/          # এজ লেয়ার (লোড ব্যালেন্সার)
├── infrastructure/             # Infrastructure as Code
├── config/                     # শেয়ার্ড কনফিগারেশন ফাইল
├── docs/                       # প্রজেক্ট ডকুমেন্টেশন
├── scripts/                    # অটোমেশন স্ক্রিপ্ট
├── tools/                      # ডেভেলপমেন্ট টুল
└── shared/                     # শেয়ার্ড লাইব্রেরি
```

---

## 🗂️ ব্যাকএন্ড স্ট্রাকচার (`backend/`)

```
backend/
├── core/                       # কোর ফ্রেমওয়ার্ক এবং কনফিগারেশন
│   ├── config.py               # Pydantic সেটিংস
│   ├── security/               # সিকিউরিটি মডুল
│   │   ├── auth_middleware.py  # JWT ও API কী ভ্যালিডেশন
│   │   ├── rbac.py             # রোল-বেসড অ্যাক্সেস কন্ট্রোল
│   │   ├── secret_vault.py     # গোপনীয় ভেরিয়েবল ম্যানেজমেন্ট
│   │   └── audit_logger.py     # অডিট লগিং
│   ├── database/               # ডাটাবেস কানেকশন এবং সেশন
│   │   ├── session.py          # SQLAlchemy অ্যাসিঙ্ক সেশন
│   │   ├── migrations/         # Alembic মাইগ্রেশন
│   │   └── models/             # ডাটাবেস মডেল (SQLAlchemy)
│   ├── middleware/             # FastAPI মিডলওয়ার
│   │   ├── cors.py             # CORS কনফিগারেশন
│   │   ├── rate_limit.py       # রেট লিমিটিং
│   │   ├── error_handler.py    # গ্লোবাল এরর হ্যান্ডলিং
│   │   └── logging.py          # লগিং মিডলওয়ার
│   └── app_*.py                # FastAPI অ্যাপ ইনস্ট্যান্স
│       ├── app_user.py         # ইউজার সার্ভিস এপ্লিকেশন
│       └── app_admin.py        # অ্যাডমিন সার্ভিস এপ্লিকেশন
│
├── api/                        # API রাউটার
│   ├── v1/                     # API ভার্সন 1
│   │   ├── auth.py             # অথেনটিকেশন এন্ডপয়েন্ট
│   │   ├── users.py            # ইউজার ম্যানেজমেন্ট
│   │   ├── agents.py           # AI এজেন্ট অপারেশন
│   │   ├── tools.py            # টুল ম্যানেজমেন্ট
│   │   ├── memory.py           # মেমরি অপারেশন
│   │   ├── knowledge.py        # নলেজベース অপারেশন
│   │   ├── vision.py           # ভিশন AI এন্ডপয়েন্ট
│   │   ├── voice.py            # ভয়েস AI এন্ডপয়েন্ট
│   │   ├── video.py            # ভিডিও AI এন্ডপয়েন্ট
│   │   ├── admin.py            # অ্যাডমিন এন্ডপয়েন্ট
│   │   └── health.py           # হেলথ চেক এন্ডপয়েন্ট
│   └── dependencies.py         # শেয়ার্ড ডিপেন্ডেন্সি
│
├── services/                   # বিজনেস লজিক লেয়ার
│   ├── llm/                    # LLM গেটওয়ে
│   │   ├── gateway.py          # LLM রাউটিং এবং লোড ব্যালেন্সিং
│   │   ├── providers/          # LLM প্রোভাইডার ইমপ্লিমেন্টেশন
│   │   │   ├── openai.py       # OpenAI ইন্টিগ্রেশন
│   │   │   ├── anthropic.py    # Anthropic ইন্টিগ্রেশন
│   │   │   └── litellm.py      # LiteLLM ইন্টিগ্রেশন
│   │   └── cache.py            # LLM রেসপন্স ক্যাচিং
│   ├── agent/                  # AI এজেন্ট সিস্টেম
│   │   ├── orchestrator.py     # এজেন্ট অর্কেস্ট্রেশন
│   │   ├── planner.py          # টাস্ক প্ল্যানিং
│   │   ├── executor.py         # এজেন্ট এক্সিকিউশন
│   │   └── memory.py           # এজেন্ট মেমরি ম্যানেজমেন্ট
│   ├── memory/                 # মেমরি সিস্টেম
│   │   ├── cascade.py          # ক্যাসকেড মেমরি (শর্ট/লং টার্ম)
│   │   ├── embeddings.py       # ভেক্টর এমবেডিংস
│   │   ├── retrieval.py        # মেমরি রিট্রieval
│   │   └── consolidation.py    # মেমরি কনসোলিডেশন
│   ├── knowledge/              # নলেজ ম্যানেজমেন্ট
│   │   ├── qa_service.py       # Q&A সার্ভিস
│   │   ├── rag.py              # RAG সিস্টেম
│   │   └── graph.py            # নলেজ গ্রাফ
│   ├── tools/                  # টুল ইমপ্লিমেন্টেশন
│   │   ├── web_search.py       # ওয়েব সার্চ
│   │   ├── code_executor.py    # কোড এক্সিকিউশন
│   │   ├── file_manager.py     # ফাইল ম্যানিপুলেশন
│   │   └── calculator.py       # ক্যালকুলেটর
│   ├── vision/                 # ভিশন AI
│   │   ├── image_analyzer.py   # ইমেজ অ্যানালিসিস
│   │   ├── ocr.py              # OCR সার্ভিস
│   │   └── ui_extractor.py     # UI কম্পোনেন্ট এক্সট্র্যাকশন
│   ├── voice/                  # ভয়েস AI
│   │   ├── stt.py              # স্পিচ-টু-টেক্সট
│   │   ├── tts.py              # টেক্সট-টু-স্পিচ
│   │   └── language_detect.py  # ল্যাঙ্গুয়েজ ডিটেকশন
│   └── video/                  # ভিডিও AI
│       ├── frame_extractor.py  # ফ্রেম এক্সট্র্যাকশন
│       ├── analyzer.py         # ভিডিও অ্যানালিসিস
│       └── code_gen.py         # ভিডিও টু কোড
│
├── models/                     # SQLAlchemy ডাটাবেস মডেল
│   ├── user.py                 # ইউজার মডেল
│   ├── agent.py                # এজেন্ট মডেল
│   ├── execution.py            # এক্সিকিউশন মডেল
│   ├── memory.py               # মেমরি মডেল
│   ├── tool.py                 # টুল মডেল
│   ├── api_key.py              # API কী মডেল
│   └── audit_log.py            # অডিট লগ মডেল
│
├── schemas/                    # Pydantic স্কিমা
│   ├── user.py                 # ইউজার স্কিমা
│   ├── agent.py                # এজেন্ট স্কিমা
│   ├── execution.py            # এক্সিকিউশন স্কিমা
│   ├── memory.py               # মেমরি স্কিমা
│   └── tool.py                 # টুল স্কিমা
│
├── agents/                     # AI এজেন্ট ডেফিনিশন
│   ├── base_agent.py           # বেস এজেন্ট ক্লাস
│   ├── chatbot.py              # চ্যাটবট এজেন্ট
│   ├── coder.py                # কোডিং এজেন্ট
│   ├── analyst.py              # অ্যানালিস্ট এজেন্ট
│   └── swarm.py                # সোয়ার্ম এজেন্ট
│
├── tools/                      # টুল রেজিস্ট্রি
│   ├── registry.py             # টুল রেজিস্ট্রি
│   ├── base_tool.py            # বেস টুল ক্লাস
│   └── implementations/        # টুল ইমপ্লিমেন্টেশন
│
├── memory/                     # মেমরি সিস্টেম
│   ├── store.py                # মেমরি স্টোর
│   ├── retrieve.py             # মেমরি রিট্রieval
│   └── consolidate.py          # মেমরি কনসোলিডেশন
│
├── pipelines/                  # AI পাইপলাইন
│   ├── text_pipeline.py        # টেক্সট প্রসেসিং
│   ├── image_pipeline.py       # ইমেজ প্রসেসিং
│   ├── voice_pipeline.py       # ভয়েস প্রসেসিং
│   └── video_pipeline.py       # ভিডিও প্রসেসিং
│
├── workers/                    # ব্যাকগ্রাউন্ড ওয়ার্কার
│   ├── task_queue.py           # টাস্ক কিউ
│   ├── email_worker.py         # ইমেইল ওয়ার্কার
│   └── cleanup_worker.py       # ক্লিনআপ ওয়ার্কার
│
├── tests/                      # টেস্ট স্যুট
│   ├── unit/                   # ইউনিট টেস্ট
│   ├── integration/            # ইন্টিগ্রেশন টেস্ট
│   ├── e2e/                    # E2E টেস্ট
│   └── conftest.py             # টেস্ট কনফিগারেশন
│
├── main.py                     # এপ্লিকেশন এন্ট্রি পয়েন্ট
├── pyproject.toml              # Python প্রজেক্ট কনফিগারেশন
├── poetry.lock                 # Poetry লক ফাইল
├── Dockerfile                  # Docker কনফিগারেশন
├── .env.example                # এনভায়রনমেন্ট ভেরিয়েবল টেমপ্লেট
└── README.md                   # ব্যাকএন্ড README
```

---

## 🎨 ফ্রন্টএন্ড স্ট্রাকচার (`apps/`)

### স্টুডিও ক্লায়েন্ট (`apps/studio-client/`)

```
apps/studio-client/
├── src/
│   ├── components/             # রিইউজেবল UI কম্পোনেন্ট
│   │   ├── ui/                 # শারীরিক UI কম্পোনেন্ট (shadcn/ui)
│   │   ├── layout/             # লেআউট কম্পোনেন্ট
│   │   ├── agent/              # এজেন্ট-স্পেসিফিক কম্পোনেন্ট
│   │   ├── tool/               # টুল কম্পোনেন্ট
│   │   └── pipeline/           # পাইপলাইন কম্পোনেন্ট
│   ├── pages/                  # পেজ কম্পোনেন্ট
│   │   ├── Dashboard.tsx       # ড্যাশবোর্ড
│   │   ├── AgentBuilder.tsx    # এজেন্ট বিল্ডার
│   │   ├── ToolBuilder.tsx     # টুল বিল্ডার
│   │   ├── PipelineBuilder.tsx # পাইপলাইন বিল্ডার
│   │   ├── KnowledgeBase.tsx   # নলেজベース
│   │   └── Settings.tsx        # সেটিংস
│   ├── stores/                 # Zustand স্টোর
│   │   ├── authStore.ts        # অথেনটিকেশন স্টেট
│   │   ├── agentStore.ts       # এজেন্ট স্টেট
│   │   ├── toolStore.ts        # টুল স্টেট
│   │   └── uiStore.ts          # UI স্টেট
│   ├── services/               # API সার্ভিস
│   │   ├── api.ts              # Axios কনফিগারেশন
│   │   ├── auth.ts             # অথেনটিকেশন সার্ভিস
│   │   ├── agents.ts           # এজেন্ট API
│   │   ├── tools.ts            # টুল API
│   │   └── websocket.ts        # WebSocket সার্ভিস
│   ├── hooks/                  # কাস্টম React হুক
│   │   ├── useAgent.ts         # এজেন্ট হুক
│   │   ├── useTool.ts          # টুল হুক
│   │   └── usePipeline.ts      # পাইপলাইন হুক
│   ├── utils/                  # ইউটিলিটি ফাংশন
│   │   ├── formatters.ts       # ফরম্যাটার
│   │   ├── validators.ts       # ভ্যালিডেটর
│   │   └── helpers.ts          # হেল্পার ফাংশন
│   ├── types/                  # TypeScript টাইপ
│   │   ├── agent.ts            # এজেন্ট টাইপ
│   │   ├── tool.ts             # টুল টাইপ
│   │   └── pipeline.ts         # পাইপলাইন টাইপ
│   ├── App.tsx                 # মূল অ্যাপ কম্পোনেন্ট
│   ├── main.tsx                # এন্ট্রি পয়েন্ট
│   └── vite-env.d.ts           # Vite টাইপ ডিক্লারেশন
├── public/                     # স্ট্যাটিক অ্যাসেট
│   ├── favicon.ico
│   ├── logo.svg
│   └── fonts/
├── package.json                # NPM কনফিগারেশন
├── vite.config.ts              # Vite কনফিগারেশন
├── tsconfig.json               # TypeScript কনফিগারেশন
├── tailwind.config.ts          # Tailwind CSS কনফিগারেশন
└── .env.example                # এনভায়রনমেন্ট ভেরিয়েবল
```

### অ্যাডমিন ড্যাশবোর্ড (`apps/admin/`)

```
apps/admin/
├── src/
│   ├── components/
│   │   ├── ui/                 # UI কম্পোনেন্ট
│   │   ├── layout/             # অ্যাডমিন লেআউট
│   │   ├── dashboard/          # ড্যাশবোর্ড কম্পোনেন্ট
│   │   └── users/              # ইউজার ম্যানেজমেন্ট
│   ├── pages/
│   │   ├── Dashboard.tsx       # অ্যানালিটিক্স ড্যাশবোর্ড
│   │   ├── Users.tsx           # ইউজার ম্যানেজমেন্ট
│   │   ├── Agents.tsx          # এজেন্ট মনিটরিং
│   │   ├── Analytics.tsx       # অ্যানালিটিক্স
│   │   └── Settings.tsx        # সিস্টেম সেটিংস
│   ├── stores/
│   │   └── adminStore.ts       # অ্যাডমিন স্টেট
│   ├── services/
│   │   └── adminApi.ts         # অ্যাডমিন API
│   └── App.tsx
├── public/
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### মোবাইল অ্যাপ (`apps/mobile/`)

```
apps/mobile/
├── lib/
│   ├── screens/                # স্ক্রিন
│   │   ├── chat_screen.dart    # চ্যাট স্ক্রিন
│   │   ├── agents_screen.dart  # এজেন্ট লিস্ট
│   │   └── settings_screen.dart # সেটিংস
│   ├── widgets/                # রিইউজেবল উইজেট
│   │   ├── chat_bubble.dart
│   │   └── agent_card.dart
│   ├── services/
│   │   ├── api_service.dart    # API সার্ভিস
│   │   ├── auth_service.dart   # অথেনটিকেশন
│   │   └── storage_service.dart # লোকাল স্টোরেজ
│   ├── models/                 # ডাটা মডেল
│   │   ├── agent.dart
│   │   └── message.dart
│   └── main.dart               # এন্ট্রি পয়েন্ট
├── android/                    # Android কনফিগারেশন
├── ios/                        # iOS কনফিগারেশন
├── pubspec.yaml                # Flutter ডিপেন্ডেন্সি
└── README.md
```

---

## ☁️ এজ লেয়ার (`cloudflare-worker/`)

```
cloudflare-worker/
├── src/
│   ├── index.ts                # এন্ট্রি পয়েন্ট
│   ├── router.ts               # রাউটিং লজিক
│   ├── load-balancer.ts        # লোড ব্যালেন্সিং
│   ├── health-check.ts         # হেলথ চেক
│   ├── rate-limiter.ts         # রেট লিমিটিং
│   └── keep-alive.ts           # কিপ-অ্যালাইভ পিং
├── wrangler.toml               # Cloudflare কনফিগারেশন
├── package.json
├── tsconfig.json
└── README.md
```

---

## 🏗️ ইনফ্রাস্ট্রাকচার (`infrastructure/`)

```
infrastructure/
├── terraform/                  # Terraform কনফিগারেশন
│   ├── main.tf                 # মূল Terraform কনফিগ
│   ├── variables.tf            # ভেরিয়েবল
│   ├── outputs.tf              # আউটপুট
│   └── modules/                # Terraform মডুল
│       ├── backend/
│       ├── database/
│       └── monitoring/
├── docker/                     # Docker কনফিগারেশন
│   ├── Dockerfile.backend      # ব্যাকএন্ড Dockerfile
│   ├── Dockerfile.frontend     # ফ্রন্টএন্ড Dockerfile
│   └── docker-compose.yml      # Docker Compose
├── kubernetes/                 # Kubernetes ম্যানিফেস্ট
│   ├── deployments/
│   ├── services/
│   └── ingress/
└── scripts/                    # ডিপ্লয়মেন্ট স্ক্রিপ্ট
    ├── deploy.sh
    ├── migrate.sh
    └── backup.sh
```

---

## ⚙️ কনফিগারেশন (`config/`)

```
config/
├── agent_rules.json            # এজেন্ট নিয়ম
├── audit-rules.yml             # অডিট নিয়ম
├── compliance-rules.yml        # কমপ্লায়েন্স নিয়ম
├── docker-limits.yml           # Docker লিমিট
├── routing_policy.json         # রাউটিং পলিসি
├── firestore.indexes.json      # Firestore ইনডেক্স
├── firestore.rules             # Firestore সুরক্ষা নিয়ম
└── vercel.json                 # Vercel কনফিগারেশন
```

---

## 📚 ডকুমেন্টেশন (`docs/`)

```
docs/
├── knowledge-base/             # AI-নেটিভ নলেজベース
│   ├── INDEX.md                # ইংরেজি ইনডেক্স
│   ├── INDEX_bn.md             # বাংলা ইনডেক্স
│   ├── 01-PROJECT_OVERVIEW.md
│   ├── 01-PROJECT_OVERVIEW_bn.md
│   ├── 02-PROJECT_VISION.md
│   ├── 02-PROJECT_VISION_bn.md
│   ├── 03-ARCHITECTURE.md
│   ├── 03-ARCHITECTURE_bn.md
│   ├── 04-FOLDER_STRUCTURE.md
│   ├── 04-FOLDER_STRUCTURE_bn.md
│   ├── ... (বাকি ডকুমেন্ট)
│   └── DIAGRAMS_AND_VISUALS.md # ডায়াগ্রাম
├── api/                        # API ডকুমেন্টেশন
├── operations/                 # অপারেশন গাইড
├── developer-guide/            # ডেভেলপার গাইড
└── README.md                   # ডকুমেন্টেশন ইনডেক্স
```

---

## 🔧 স্ক্রিপ্ট (`scripts/`)

```
scripts/
├── fetch_render_logs.py        # Render লগ ফেচ
├── fetch_render_logs_detail.py # ডিটেইলড Render লগ
├── setup_dev_env.sh            # ডেভেলপমেন্ট এনভায়রনমেন্ট সেটআ
├── deploy.sh                   # ডিপ্লয়মেন্ট স্ক্রিপ্ট
├── backup.sh                   # ব্যাকআপ স্ক্রিপ্ট
├── restore.sh                  # রিস্টোর স্ক্রিপ্ট
└── migrate.sh                  # ডাটাবেস মাইগ্রেশন
```

---

## 🛠️ টুল (`tools/`)

```
tools/
├── cli/                        # CLI টুল
│   ├── supremeai-cli.py        # প্রধান CLI
│   ├── agent_manager.py        # এজেন্ট ম্যানেজার
│   └── tool_builder.py         # টুল বিল্ডার
├── migrations/                 # ডাটাবেস মাইগ্রেশন টুল
├── testing/                    # টেস্টিং টুল
│   ├── load_test.py            # লোড টেস্ট
│   └── security_scan.py        # সিকিউরিটি স্ক্যান
└── monitoring/                 # মনিটরিং টুল
    ├── health_check.py         # হেলথ চেক
    └── metrics_collector.py    # মেট্রিক্স কালেক্টর
```

---

## 📊 ফোল্ডার সংগঠন নীতিমালা

### ১. লজিক্যাল অর্গানাইজেশন
- **লেয়ার অনুযায়ী**: core, api, services, models
- **ফিচার অনুযায়ী**: agents, tools, memory, knowledge
- **টেকনোলজি অনুযায়ী**: backend, frontend, mobile

### ২. নামকরণ কনভেনশন
- **ডিরেক্টরি**: snake_case
- **ফাইল**: snake_case (Python), camelCase (TypeScript)
- **ক্লাস**: PascalCase
- **ফাংশন**: snake_case (Python), camelCase (TypeScript)

### ৩. সাইজ গাইডলাইন
- **ডিরেক্টরি**: ১০+ ফাইলে সাবডিরেক্টরি
- **ফাইল**: ৫০০+ লাইনে স্প্লিট
- **ফাংশন**: ৫০+ লাইনে স্প্লিট

### ৪. ইমপোর্ট অর্ডার
```python
# 1. স্ট্যান্ডার্ড লাইব্রেরি
import os
import sys
from pathlib import Path

# 2. থার্ড-পার্টি লাইব্রেরি
from fastapi import FastAPI
from sqlalchemy import Column

# 3. লোকাল মডুল
from core.config import settings
from models.user import User
```

---

## 🔗 সম্পর্কিত ডকুমেন্ট

- [03-ARCHITECTURE_bn.md](03-ARCHITECTURE_bn.md) - সিস্টেম আর্কিটেকচার
- [05-MODULE_DOCUMENTATION_bn.md](05-MODULE_DOCUMENTATION_bn.md) - মডুল বিবরণ
- [07-DEPENDENCY_DOCUMENTATION_bn.md](07-DEPENDENCY_DOCUMENTATION_bn.md) - ডিপেন্ডেন্সি

---

## ✅ ফোল্ডার স্ট্রাকচার ভেরিফিকেশন

**ভেরিফাই করার উপায়**:

1. **ডিরেক্টরি ট্রি চেক**:
   ```bash
   tree -L 2 -d
   # Should show all main directories
   ```

2. **ফাইল কাউন্ট চেক**:
   ```bash
   find . -name "*.py" | wc -l
   find . -name "*.ts" -o -name "*.tsx" | wc -l
   ```

3. **স্ট্রাকচার ভ্যালিডেশন**:
   ```bash
   # Check required directories exist
   [ -d "backend/core" ] && echo "✓ Backend core exists"
   [ -d "apps/studio-client/src" ] && echo "✓ Frontend exists"
   [ -d "cloudflare-worker/src" ] && echo "✓ Edge layer exists"
   ```

---

**ডকুমেন্ট স্ট্যাটাস**: ✅ সম্পূর্ণ এবং ভেরিফাইড  
**পরবর্তী রিভিউ**: 2025-02-04  
**অনার**: আর্কিটেকচার টিম  
**ক্লাসিফিকেশন**: ইন্টার্নাল