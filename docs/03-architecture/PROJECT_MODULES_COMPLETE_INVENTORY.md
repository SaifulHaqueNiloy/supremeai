# SupremeAI 2.0 — প্রজেক্টের প্রতিটি মডিউল ও ফাইলের সম্পূর্ণ ইনভেন্টরি ক্যাটালগ
**Master Component Inventory & Comprehensive Documentation Roadmap**
*তারিখ:* ২৭ জুলাই, ২০২৬  
*সংস্করণ:* SupremeAI 2.0 (Complete Repository Index)

---

## 📌 ১. উদ্দেশ্য (Purpose)

এই ক্যাটালগ ডকুমেন্টের মূল উদ্দেশ্য হলো SupremeAI 2.0 রিপোজিটরির **প্রতিটি ছোট-বড় মডিউল, সাব-সিস্টেম, সার্ভিস, এজেন্ট, পাইপলাইন ও স্ক্রিপ্টের শতভাগ ইনভেন্টরি তৈরি করা**। ভবিষ্যতে প্রতিটি মডিউলের জন্য আলাদা আলাদা গভীর টেকনিক্যাল ম্যানুয়াল (Deep-Dive Manual) তৈরি করতে এটি মাস্টার ইনডেক্স নির্দেশিকা হিসেবে কাজ করবে।

---

## 📂 ২. মডিউল ইনভেন্টরি ক্যাটালগ (Subsystem Index)

### 🧠 ২.১. Core AI Engine & Routing (`backend/core/` & `backend/engine/`)

| ফাইল / মডিউল | অবস্থান (File Path) | মূল দায়িত্ব ও ফাংশন | ভবিষ্যৎ ম্যানুয়াল লিঙ্ক |
|---|---|---|---|
| **LLMRouter** | `backend/core/llm_router.py` | প্রোভাইডার লজিক, বাজেট কনস্ট্রেইন্ট ও ফলব্যাক চেইন | `DOC-CORE-LLMROUTER.md` |
| **SmartModelRouter** | `backend/engine/smart_router.py` | ডাইনামিক মডেল নির্বাচন ও কস্ট-ক্যাপ অপ্টিমাইজেশন | `DOC-ENG-SMARTROUTER.md` |
| **TreeOfThoughtReasoner** | `backend/engine/tree_of_thought.py` | মাল্টি-ব্রাঞ্চ চিন্তা ও হিউরিস্টিক ইভালুয়েশন | `DOC-ENG-TREEOFTHOUGHT.md` |
| **SelfReflectionLoop** | `backend/engine/self_reflection.py` | আউটপুট ভ্যালিডেশন ও অটো-কারেকশন লুপ | `DOC-ENG-SELFREFLECTION.md` |
| **ToolForge** | `backend/engine/tool_forge.py` | রানটাইমে কাস্টম পাইথন টুল জেনারেটর | `DOC-ENG-TOOLFORGE.md` |
| **WorkerNode Engine** | `backend/engine/worker_node.py` | এ্যাসিঙ্ক টাস্ক এক্সিকিউটর ও হার্টবিট | `DOC-ENG-WORKERNODE.md` |

---

### 🧬 ২.২. Cognitive & Self-Evolution (`backend/evolution/`)

| ফাইল / মডিউল | অবস্থান (File Path) | মূল দায়িত্ব ও ফাংশন | ভবিষ্যৎ ম্যানুয়াল লিঙ্ক |
|---|---|---|---|
| **TheoryOfMindSystem** | `backend/evolution/theory_of_mind/tom_system.py` | Level 0-4 Mental State Attribution & Intent Detection | `THEORY_OF_MIND_AND_DIGITAL_TWIN_DEEP_DIVE.md` |
| **DigitalTwinWorldModel** | `backend/evolution/digital_twin/world_model.py` | স্টেট ভেক্টর রেপ্লিকা ও ওয়ার্ল্ড মডেল | `THEORY_OF_MIND_AND_DIGITAL_TWIN_DEEP_DIVE.md` |
| **SimulationSandbox** | `backend/evolution/digital_twin/simulation_sandbox.py` | জিরো-রিস্ক ইন-মেমোরি কমান্ড স্যান্ডবক্স | `THEORY_OF_MIND_AND_DIGITAL_TWIN_DEEP_DIVE.md` |
| **AgentEvolutionEngine** | `backend/core/tier8/agent_evolution_engine.py` | Tier-8 অটো-বিবর্তন ও EWC প্যানাল্টি | `DOC-EVO-AGENTEVOLUTION.md` |
| **SelfImprovementAgent** | `backend/adaptive_engine/self_improving_agent.py` | পারফরম্যান্স ফিডব্যাক থেকে সেলফ-ইম্প্রুভমেন্ট | `DOC-EVO-SELFIMPROVEMENT.md` |

---

### 💾 ২.৩. Memory & Knowledge Storage (`backend/memory/` & `backend/storage/`)

| ফাইল / মডিউল | অবস্থান (File Path) | মূল দায়িত্ব ও ফাংশন | ভবিষ্যৎ ম্যানুয়াল লিঙ্ক |
|---|---|---|---|
| **EpisodicMemory** | `backend/memory/episodic_memory.py` | টাস্ক এক্সিকিউটর মেমোরি ও রিকল | `DOC-MEM-EPISODIC.md` |
| **LongTermMemory** | `backend/memory/long_term_memory.py` | ইউজারের পছন্দ ও কনটেক্সট ট্র্যাকার | `DOC-MEM-LONGTERM.md` |
| **ChromaDBStore** | `backend/memory/chromadb_store.py` | ভেক্টর ইমবেডিং ও সিমিলারিটি সার্চ | `DOC-MEM-CHROMADB.md` |
| **FutureKnowledgeIngest** | `ingest_future_knowledge.py` | ১৪টি ডোমেইনের ভবিষ্যৎ জ্ঞান ইনজেকশন | `DOC-MEM-KNOWLEDGEINGEST.md` |

---

### 🛡️ ২.৪. Monitoring, Resilience & Security (`backend/monitoring/` & `backend/core/security/`)

| ফাইল / মডিউল | অবস্থান (File Path) | মূল দায়িত্ব ও ফাংশন | ভবিষ্যৎ ম্যানুয়াল লিঙ্ক |
|---|---|---|---|
| **BehavioralGuard** | `backend/monitoring/behavioral_guard.py` | ইনফিনিট লুপ ও এনামালি ওয়াচডগ | `DOC-SEC-BEHAVIORALGUARD.md` |
| **SentinelAgent** | `backend/agents/sentinel_agent.py` | রিয়েল-টাইম থ্রেট প্রটেকশন | `DOC-SEC-SENTINEL.md` |
| **CausalDebugger** | `backend/monitoring/causal_debugger.py` | ট্রেসবেক বিশ্লেষণ ও অটো-প্যাচ | `DOC-MON-CAUSALDEBUGGER.md` |
| **CircuitBreaker** | `backend/core/resilience/circuit_breaker.py` | প্রোভাইডার আইসোলেশন ও ট্রাফিক পজ | `DOC-RES-CIRCUITBREAKER.md` |
| **RBAC Manager** | `backend/core/security/rbac.py` | রোল-বেসড পারমিশন ও এক্সেস কন্ট্রোল | `DOC-SEC-RBAC.md` |
| **QuotaEnforcer** | `backend/core/billing/quota_enforcer.py` | ইউজার কোটা ও ডেইলি বাজেট লক | `DOC-BIL-QUOTAENFORCER.md` |

---

### 🌐 ২.৫. Services, Audio/Vision & Pipelines (`backend/services/` & `backend/pipelines/`)

| ফাইল / মডিউল | অবস্থান (File Path) | মূল দায়িত্ব ও ফাংশন | ভবিষ্যৎ ম্যানুয়াল লিঙ্ক |
|---|---|---|---|
| **VoiceService** | `backend/services/voice_service.py` | স্পিচ-টু-টেক্সট ও অডিও ইনফারেন্স | `DOC-SRV-VOICE.md` |
| **VisionService** | `backend/services/vision_service.py` | কগনিটিভ ইমেজ ও মাল্টি-মোডাল প্রসেসিং | `DOC-SRV-VISION.md` |
| **SyntheticDataPipeline** | `backend/pipelines/synthetic_data_pipeline.py` | ফাইন-টিউনিংয়ের জন্য ডাটা জেনারেটর | `DOC-PIP-SYNTHETICDATA.md` |

---

### ⚙️ ২.৬. CI/CD Workflows & Cloudflare (`.github/workflows/` & `cloudflare-worker/`)

| ফাইল / মডিউল | অবস্থান (File Path) | মূল দায়িত্ব ও ফাংশন | ভবিষ্যৎ ম্যানুয়াল লিঙ্ক |
|---|---|---|---|
| **Supreme Core CI** | `.github/workflows/supreme-core-ci.yml` | টেস্ট, বিল্ড ও রেন্ডার ডিপ্লয় চেক | `DOC-OPS-CI.md` |
| **Workflow Janitor** | `.github/workflows/workflow-janitor.yml` | দৈনিক 04:00 UTC রান ওয়াশ পাইপলাইন | `DOC-OPS-JANITOR.md` |
| **Weekly Fine-Tuning** | `.github/workflows/weekly-fine-tuning.yml` | সাপ্তাহিক হাগিংফেস অটো-টিউনিং | `DOC-OPS-FINETUNING.md` |
| **Cloudflare Worker** | `cloudflare-worker/wrangler.toml` | ৮-মিনিট ক্রন ট্র্রিগার ও এজ এজেন্টস | `DOC-OPS-CLOUDFLARE.md` |

---

## 🎯 ৩. পরবর্তী ধাপ (Future Action Plan)

এই মাস্টার ইনভেন্টরি তালিকার ওপর ভিত্তি করে প্রতিটি মডিউলের জন্য আলাদা আলাদা **৩০০+ থেকে ৮০০+ লাইনের গভীর টেকনিক্যাল ম্যানুয়াল** পর্যায়ক্রমে প্রস্তুত করা যাবে, যা পুরো SupremeAI 2.0 প্ল্যাটফর্মের সবচেয়ে বড় ও নিখুঁত ডকুমেন্টেশন ক্যাটালগে পরিণত হবে।
