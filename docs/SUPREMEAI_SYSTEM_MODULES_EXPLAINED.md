# SupremeAI 2.0 — সিস্টেমের প্রতিটা ছোট ছোট মডিউল ও কাজের সম্পূর্ণ গাইড
**Master Architecture & Subsystem Specification Document**
*তারিখ:* ২৭ জুলাই, ২০২৬  
*সংস্করণ:* SupremeAI 2.0 (Production Core & Cognitive Architecture)

---

## 📌 সূচিপত্র (Table of Contents)
1. [উচ্চপর্যায়ের আর্কিটেকচার (High-Level Architecture)](#১-উচ্চপর্যায়ের-আর্কিটেকচার)
2. [কোর এআই ইঞ্জিন ও রাউটিং মডিউল (Core AI Engine & Routing)](#২-কোর-এআই-ইঞ্জিন-ও-রাউটিং-মডিউল)
3. [কগনিটিভ ও সেলফ-ইভোলিউশন সাব-সিস্টেম (Cognitive & Evolution Subsystems)](#৩-কগনিটিভ-ও-সেলফ-ইভোলিউশন-সাব-সিস্টেম)
4. [মেমোরি ও ভেক্টর নলেজ বেস (Memory & Vector Knowledge Base)](#৪-মেমোরি-ও-ভেক্টর-নলেজ-বেস)
5. [রেজিলিয়েন্স, সেলফ-হিলিং ও সিকিউরিটি (Resilience, Auto-Healing & Security)](#৫-রেজিলিয়েন্স-সেলফ-হিলিং-ও-সিকিউরিটি)
6. [মাল্টি-টেন্যান্ট, বিলিং ও কোটা সিস্টেম (Multi-Tenant, Billing & Quota)](#৬-মাল্টি-টেন্যান্ট-বিলিং-ও-কোটা-সিস্টেম)
7. [MCP সার্ভার ইন্টিগ্রেশন (Model Context Protocol Integration)](#৭-mcp-সার্ভার-ইন্টিগ্রেশন)
8. [সিআই/সিডি জেনিটর ও ফাইন-টিউনিং পাইপলাইন (CI/CD Janitor & Fine-Tuning)](#৮-সিআইসিডি-জেনিটর-ও-ফাইন-টিউনিং-পাইপলাইন)

---

## ১. উচ্চপর্যায়ের আর্কিটেকচার

SupremeAI 2.0 হলো একটি অটোনোমাস মাল্টি-এজেন্ট প্ল্যাটফর্ম যা **4-Layered Modular Architecture** নীতিতে গঠিত:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND / CLIENT LAYER                         │
│     (Next.js Studio Client, ChatPanel, Dashboard, VS Code MCP)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / WebSocket / JSON-RPC (MCP)
┌───────────────────────────────────▼────────────────────────────────────┐
│                         API & MIDDLEWARE LAYER                         │
│     (FastAPI Routers, RBAC, API Key Auth, Rate Limiter, BYOC Router)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                     COGNITIVE & REASONING LAYER                        │
│   (LLMRouter, TreeOfThought, SelfReflection, ToM System, ToolForge)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                    MEMORY & EVOLUTION DATA LAYER                       │
│    (EpisodicMemory, LongTermMemory, ChromaDBStore, Postgres/Redis)     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ২. কোর এআই ইঞ্জিন ও রাউটিং মডিউল

### `backend/core/llm_router.py` & `smart_router.py`
- **কাজের বিবরণ:** এটি সিস্টেমের প্রধান এআই মডেল রাউটার। ব্যবহারকারীর প্রম্পট পাওয়া মাত্রই এটি প্রশ্নের জটিলতা (Complexity), লেটেন্সি চাহিদা এবং খরচের ওপর নির্ভর করে সেরা LLM প্রোভাইডার নির্বাচন করে।
- **সমর্থিত প্রোভাইডারসমূহ:** Gemini, Groq, OpenRouter, DeepSeek, Together, Ollama, HuggingFace Space।
- **ফলব্যাক চেইন (Fallback Chain):** প্রাথমিক প্রোভাইডার ফেল করলে এটি স্বয়ংক্রিয়ভাবে ২য় বা ৩য় ব্যাকআপ প্রোভাইডারে সুইচ করে (Failover Mechanism)।

### `backend/engine/tool_forge.py`
- **কাজের বিবরণ:** কোনো কাজের জন্য আগে থেকে তৈরি টুল না থাকলে এআই স্বয়ংক্রিয়ভাবে নতুন পাইথন ফাংশন বা টুল তৈরি (Dynamic Tool Synthesis) করে কোড এক্সিকিউট করে।

---

## ৩. কগনিটিভ ও সেলফ-ইভোলিউশন সাব-সিস্টেম

### `backend/engine/tree_of_thought.py` (Tree-of-Thought Reasoner)
- **কাজের বিবরণ:** জটিল কোডিং সমস্যা বা সিদ্ধান্ত নেওয়ার জন্য এটি একাধিক বিকল্প চিন্তার শাখা (Thought Branches) তৈরি করে, প্রতিটি চিন্তার মান স্কোরের মাধ্যমে মূল্যায়ন করে এবং সেরা সমাধানটি বেছে নেয়।

### `backend/engine/self_reflection.py` (Self-Reflection Loop)
- **কাজের বিবরণ:** যেকোনো উত্তর বা কোড ইউজারকে দেওয়ার আগে এআই নিজের উত্তর নিজেই রিভিউ করে। এতে ভুল লজিক বা সিকিউরিটি বাগ থাকলে নিজেই শুধরে নেয়।

### `backend/evolution/theory_of_mind/tom_system.py` (Theory-of-Mind Engine)
- **কাজের বিবরণ:** ব্যবহারকারীর মানসিক অবস্থা (Belief, Desire, Intention) এবং অন্যান্য এজেন্টের দৃষ্টিভঙ্গি প্রেডিক্ট করে আচরণ নির্ধারণ করে।

### `backend/evolution/digital_twin/` (Digital-Twin World Model)
- **কাজের বিবরণ:** আসল ডাটাবেজ বা সার্ভারে কোনো ধ্বংসাত্মক কমান্ড রান করার আগে ব্যাকগ্রাউন্ডে পুরো সিস্টেমের ভার্চুয়াল কপি তৈরি করে সিমুলেশন চালায়।

### `backend/core/tier8/agent_evolution_engine.py`
- **কাজের বিবরণ:** সিস্টেমের বিবর্তন ইঞ্জিন। এটি প্রতিদিনের কাজের অভিজ্ঞতা থেকে শেখে এবং EWC (Elastic Weight Consolidation) পেনাল্টি প্রয়োগ করে যাতে এআই নতুন জিনিস শিখতে গিয়ে পুরনো শিক্ষা ভুলে না যায় (Catastrophic Forgetting Prevention)।

---

## ৪. মেমোরি ও ভেক্টর নলেজ বেস

### `backend/memory/episodic_memory.py` (Episodic Memory Engine)
- **কাজের বিবরণ:** এটি এআই-এর স্বল্পমেয়াদী ও দীর্ঘমেয়াদী টাস্ক মেমোরি। প্রতিটি টাস্কের ফলাফল, ইনপুট, রেসপন্স এবং লেটেন্সি ভেক্টরাইজ করে ট্র্যাকিং রাখে।
- **উপকার:** অতীতে করা কাজ পুনরায় এলে এআই মুহূর্তের মধ্যে উত্তর তৈরি করতে পারে।

### `backend/memory/long_term_memory.py` (Long-Term User Preference Memory)
- **কাজের বিবরণ:** ব্যবহারকারীর ব্যক্তিগত পছন্দ (যেমন: প্রিয় কোডিং স্টাইল, ভাষা, প্রজেক্ট স্ট্রাকচার) স্থায়ীভাবে মনে রাখে।

### `backend/memory/chromadb_store.py` (Vector Search Engine)
- **কাজের বিবরণ:** ChromaDB ভেক্টর ডাটাবেজের স্থানীয় ও ফলব্যাক মেমোরি ম্যানেজার। এটি টেক্সট ও কোডের সিমিলারিটি সার্চ নিশ্চিত করে।

---

## ৫. রেজিলিয়েন্স, সেলফ-হিলিং ও সিকিউরিটি

### `backend/monitoring/behavioral_guard.py` & `backend/agents/sentinel_agent.py`
- **কাজের বিবরণ:** সিকিউরিটি প্রহরী। এটি সিস্টেমের ইনফিনিট লুপ, এনামালি, রেট লিমিট ভায়োলেশন এবং প্রম্পট ইনজেকশন অ্যাটাক শনাক্ত ও প্রতিরোধ করে।

### `backend/core/resilience/circuit_breaker.py`
- **কাজের বিবরণ:** সার্কিট ব্রেকার প্যাটার্ন (CLOSED, OPEN, HALF-OPEN)। কোনো এপিআই বারবার ফেল করলে সাময়িকভাবে সেখানে ট্রাফিক পাঠানো বন্ধ রাখে।

### `backend/monitoring/causal_debugger.py`
- **কাজের বিবরণ:** যেকোনো রানটাইম ট্রেসবেক (Stacktrace) বিশ্লেষণ করে মূল কারণ (Root Cause Analysis) বের করে অটো-প্যাচ জেনারেট করে।

---

## ৬. মাল্টি-টেন্যান্ট, বিলিং ও কোটা সিস্টেম

### `backend/core/billing/quota_enforcer.py` & `fraud_detector.py`
- **কাজের বিবরণ:** ব্যবহারকারীদের ডেইলি টোকেন বাজেট ও কোটা নিয়ন্ত্রণ করে। কোনো ইউজার জালিয়াতি (Fraud) করতে চাইলে অ্যাকাউন্ট ফ্ল্যাগ করে।

### `backend/core/security/rbac.py`
- **কাজের বিবরণ:** রোল-বেসড এক্সেস কন্ট্রোল (Admin, Developer, Guest) নিশ্চিত করে।

---

## ৭. MCP সার্ভার ইন্টিগ্রেশন (Model Context Protocol)

### LaunchDarkly MCP Integration (`.vscode/mcp.json`)
- **কাজের বিবরণ:** VS Code, Cursor, Antigravity IDE এবং অন্যান্য সমর্থিত AI এজেন্টকে সেন্ট্রাল লঞ্চডার্কলি ফিচার ফ্ল্যাগ ও এনভায়রনমেন্ট কনফিগারেশনের সাথে রিয়েল-টাইমে সিঙ্ক রাখে।

---

## ৮. সিআই/সিডি জেনিটর ও ফাইন-টিউনিং পাইপলাইন

### `.github/workflows/workflow-janitor.yml`
- **কাজের বিবরণ:** প্রতিদিন ০৪:০০ ইউটিসি-তে রান করে অপ্রয়োজনীয় পুরনো গিটহাব অ্যাকশন লগ ও ক্যাশ মুছে ফেলে।

### `.github/workflows/weekly-fine-tuning.yml`
- **কাজের বিবরণ:** প্রতি সপ্তাহে সংগৃহীত সেরা সিন্থেটিক ডাটা ব্যবহার করে HuggingFace-এ মডেল ফাইন-টিউনিং পাইপলাইন রান করায়।
