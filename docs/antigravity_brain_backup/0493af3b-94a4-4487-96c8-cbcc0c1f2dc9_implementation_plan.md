# 🛠️ SupremeAI 2.0 — বুদ্ধিমত্তা বিবর্তন: বিস্তারিত বাস্তবায়ন পরিকল্পনা (Implementation Plan)

**ভিত্তি পরিকল্পনা:** [AI_INTELLIGENCE_EVOLUTION_PLAN.md](file:///c:/Users/n/supremeai/supremeai_2.0/docs/AI_INTELLIGENCE_EVOLUTION_PLAN.md)  
**সময়কাল:** ১২ সপ্তাহ (৩টি পর্ব)

---

## ✅ বিদ্যমান সুবিধা (What Already Exists)

> আমরা স্ক্র্যাচ থেকে শুরু করছি না — অনেক মূল উপাদান ইতিমধ্যে বিদ্যমান!

| বিদ্যমান মডিউল | অবস্থান | বর্তমান অবস্থা |
| :--- | :--- | :--- |
| `ChromaDBStore` + Fallback TF-IDF | `backend/memory/chromadb_store.py` | ✅ সক্রিয়, ২০+ ডকুমেন্ট সংরক্ষিত |
| `EpisodicMemory` | `backend/memory/episodic_memory.py` | ✅ বিদ্যমান, সংযোগ প্রয়োজন |
| `LongTermMemory` | `backend/memory/long_term_memory.py` | ✅ বিদ্যমান, প্রসার প্রয়োজন |
| `RAGPipeline` | `backend/memory/rag_pipeline.py` | ✅ সক্রিয় |
| `DebateEngine` | `backend/engine/debate_engine.py` | ✅ বিদ্যমান, সম্পূর্ণ করা প্রয়োজন |
| `LearningLoop` | `backend/adaptive_engine/learning_loop.py` | ✅ বিদ্যমান, EWC যোগ প্রয়োজন |
| `ExperienceDB` | `backend/adaptive_engine/experience_db.py` | ✅ বিদ্যমান |
| `SentinelAgent` | `backend/agents/sentinel_agent.py` | ✅ বিদ্যমান |
| `EphemeralExecutor` | `backend/agents/ephemeral_executor.py` | ✅ বিদ্যমান |
| Evolution Modules | `backend/evolution/` (8 sub-dirs) | ✅ স্কেলেটন বিদ্যমান |

---

## 📦 পর্ব ১: নিরাপত্তা, স্যান্ডবক্স ও মেমরি কাঠামো (সপ্তাহ ১-৪)
**পিলার:** #2 (Hierarchical Memory) + #6 (Behavioral Security)

---

### 🔧 ১.১ — Long-Term Episodic Memory Integration (সপ্তাহ ১)

**লক্ষ্য:** প্রতিটি ব্যবহারকারীর সফল ও ব্যর্থ টাস্ক `EpisodicMemory`-তে স্বয়ংক্রিয়ভাবে লগ করা।

#### পরিবর্তন প্রয়োজন:

**[MODIFY] `backend/memory/episodic_memory.py`**
- `record_task()` মেথড যোগ করা — টাস্ক ID, ইনপুট, আউটপুট, সাফল্য/ব্যর্থতা, ও টাইমস্ট্যাম্প সহ।
- `get_similar_past_tasks(query)` মেথড যোগ করা — ভেক্টর সার্চ দিয়ে অনুরূপ অতীত টাস্ক খোঁজা।

**[MODIFY] `backend/memory/long_term_memory.py`**
- `store_user_preference(user_id, key, value)` মেথড প্রসার করা।
- `get_context_for_user(user_id)` মেথড — পার্সোনালাইজড কনটেক্সট রিট্রাইভ করা।

**[MODIFY] `backend/main.py`**
- প্রতিটি এপিআই রেসপন্সের পরে `episodic_memory.record_task()` কল করা।

```python
# backend/memory/episodic_memory.py — নতুন মেথড
async def record_task(self, task_id: str, prompt: str, response: str, 
                       success: bool, latency_ms: float, model_used: str):
    """সফল ও ব্যর্থ সকল টাস্ক স্বয়ংক্রিয়ভাবে ইতিহাসে সংরক্ষণ করে।"""
    ...
    
async def get_similar_past_tasks(self, query: str, n: int = 3) -> list[dict]:
    """ভেক্টর সার্চ দিয়ে অনুরূপ অতীত সমাধান খুঁজে আনে।"""
    ...
```

---

### 🔧 ১.২ — Behavioral Anomaly Detection (সপ্তাহ ২)

**লক্ষ্য:** এআই এজেন্টের অস্বাভাবিক প্যাটার্ন সনাক্ত ও ব্লক করা।

**[NEW] `backend/monitoring/behavioral_guard.py`**
- `BehavioralGuard` ক্লাস — প্রতিটি এজেন্ট টুল কলের আচরণ ট্র্যাক করে।
- `detect_anomaly(agent_id, action, context)` — অস্বাভাবিক কমান্ড স্পাইক ধরা।
- `block_if_suspicious()` — ব্লকিং + Discord অ্যালার্ট পাঠানো।

```python
# backend/monitoring/behavioral_guard.py
class BehavioralGuard:
    ANOMALY_THRESHOLDS = {
        "tool_calls_per_minute": 30,    # এক মিনিটে ৩০+ টুল কল = সন্দেহজনক
        "identical_prompts": 5,          # একই প্রম্পট ৫ বার = লুপ ডিটেকশন
        "sandbox_escape_attempts": 1,    # ১ বারও স্যান্ডবক্স ব্রেক ট্রাই = ব্লক
    }
```

**[MODIFY] `backend/agents/sentinel_agent.py`**
- `BehavioralGuard` ইন্টিগ্রেট করা।

---

### 🔧 ১.৩ — Causal Root-Cause Analyzer (সপ্তাহ ৩-৪)

**লক্ষ্য:** স্ট্যাকট্রেস থেকে সরাসরি ত্রুটির মূল কারণ খুঁজে বের করা।

**[NEW] `backend/monitoring/causal_debugger.py`**
- `analyze_exception(exc, traceback_str)` — স্ট্যাকট্রেস পার্স করে সম্ভাব্য কারণ বিশ্লেষণ।
- `suggest_fix(analysis)` — LLM দিয়ে অটো-প্যাচ পরামর্শ তৈরি করা।

---

## 📦 পর্ব ২: বুদ্ধিমত্তা উন্নয়ন (সপ্তাহ ৫-৮)
**পিলার:** #1 (Cognitive Reasoning) + #4 (Swarm Debate)

---

### 🧠 ২.১ — Tree-of-Thought Meta-Reasoning Engine (সপ্তাহ ৫-৬)

**লক্ষ্য:** জটিল প্রম্পটে ৩টি ভিন্ন লজিক পাথ তৈরি করে সেরাটি নির্বাচন করা।

**[NEW] `backend/engine/tree_of_thought.py`**

```python
class TreeOfThoughtReasoner:
    """
    জটিল সমস্যায় ৩টি reasoning path তৈরি করে।
    BFS/DFS দিয়ে সেরা চিন্তার পাথ নির্বাচন করে।
    """
    async def reason(self, problem: str, depth: int = 3) -> ReasoningResult:
        # ধাপ ১: ৩টি থট জেনারেট করা
        thoughts = await self._generate_thoughts(problem, n=3)
        # ধাপ ২: প্রতিটি থট মূল্যায়ন করা (LLM দিয়ে স্কোর দেওয়া)
        scored = await self._evaluate_thoughts(thoughts)
        # ধাপ ৩: সেরাটি বেছে নিয়ে গভীরতর চিন্তা করা
        return await self._expand_best(scored, depth)
```

**[NEW] `backend/engine/self_reflection.py`**

```python
class SelfReflectionLoop:
    """
    কাজ শেষে স্বয়ংক্রিয়ভাবে ৩টি প্রশ্নের উত্তর দিয়ে শেখে।
    """
    REFLECTION_PROMPT = """
    কাজটি সম্পন্ন হয়েছে। এখন বিশ্লেষণ কর:
    ১. কাজটি কি সঠিক হয়েছে? কেন/কেন না?
    ২. কোন ধাপে সমস্যা হয়েছিল?
    ৩. পরেরবার কীভাবে আরও ভালো করা যাবে?
    """
    async def reflect(self, task, result) -> ReflectionReport: ...
```

**[MODIFY] `backend/engine/debate_engine.py`**
- বিদ্যমান `DebateEngine`-এ `ToT` রিজনিং যোগ করা।
- ডিবেটের প্রতিটি রাউন্ডে `SelfReflection` লুপ চালানো।

---

### 🧠 ২.২ — Smart Model Router (সপ্তাহ ৬)

**লক্ষ্য:** কমান্ড বিশ্লেষণ করে সবচেয়ে উপযুক্ত HF মডেলে স্বয়ংক্রিয়ভাবে রাউট করা।

**[NEW] `backend/engine/smart_router.py`**

```python
class SmartModelRouter:
    """
    ইনপুটের ধরন বুঝে সঠিক মডেলে রাউট করে।
    প্রতিটি মডেলের সাফল্য হার ট্র্যাক করে ডাইনামিকভাবে সিদ্ধান্ত নেয়।
    """
    ROUTING_RULES = {
        "code":      "Supreme-Coder-3B",
        "reasoning": "Supreme-Reasoner-3B",
        "bengali":   "Supreme-Bhasha-1.5B",
        "math":      "Supreme-Math-1.5B",
        "general":   "Supreme-General-3B",
    }
    
    async def route(self, prompt: str) -> str:
        intent = await self._classify_intent(prompt)   # NLP ক্লাসিফিকেশন
        model = self._select_best_model(intent)         # সাফল্য হার দেখে নির্বাচন
        return model
```

---

### 🧠 ২.৩ — 3-Agent Swarm Consensus (সপ্তাহ ৭-৮)

**লক্ষ্য:** বড় কোড বা আর্কিটেকচার পরিবর্তনে ৩ এজেন্টের সম্মতি নেওয়া।

**[MODIFY] `backend/engine/debate_engine.py`**
- `DebateEngine.run_consensus(task)` মেথড সম্পূর্ণ করা।
- `Coder`, `SecurityAuditor`, `Architect` — ৩ রোলে LLM কল করা।
- ৩ রাউন্ড ডিবেটের পর সংখ্যাগরিষ্ঠ ভোটে সিদ্ধান্ত নেওয়া।

**[NEW] `backend/engine/tool_forge.py`**
```python
class ToolForge:
    """
    কোনো উপযুক্ত টুল না থাকলে নতুন পাইথন হেলপার তৈরি করে।
    """
    async def synthesize_tool(self, task_description: str) -> callable: ...
```

---

## 📦 পর্ব ৩: স্কেলিং, ফাইন-টিউনিং ও মাল্টি-মোডাল (সপ্তাহ ৯-১২)
**পিলার:** #3 (Self-Evolution) + #5 (Multi-Modal UX)

---

### 🎓 ৩.১ — Synthetic Dataset Auto-Generation (সপ্তাহ ৯-১০)

**লক্ষ্য:** প্রতিদিনের চ্যাট থেকে HF ফাইন-টিউনিং ডাটা তৈরি করা।

**[NEW] `backend/pipelines/synthetic_data_pipeline.py`**
```python
class SyntheticDataPipeline:
    """
    সফল টাস্ক থেকে উচ্চমানের Prompt-Response জোড়া বের করে।
    HF dataset format-এ JSONL ফাইল এক্সপোর্ট করে।
    """
    async def generate_daily_dataset(self) -> Path:
        # EpisodicMemory থেকে সফল টাস্ক পড়া
        # মান যাচাই করা (score > 0.85)
        # HuggingFace format-এ এক্সপোর্ট
        ...
```

**[MODIFY] `backend/adaptive_engine/learning_loop.py`**
- `EWC (Elastic Weight Consolidation)` লজিক যোগ করা।
- সাপ্তাহিক ফাইন-টিউনিং ট্রিগার অটোমেশন।

**[NEW] `.github/workflows/weekly-fine-tuning.yml`**
- প্রতি রোববার সিন্থেটিক ডাটা জেনারেট করে HF-এ আপলোড করা।

---

### 🎙️ ৩.২ — Multi-Modal: Voice (STT/TTS) Integration (সপ্তাহ ১১)

**লক্ষ্য:** বাংলা ভয়েস ইনপুট ও আউটপুট সাপোর্ট।

**[NEW] `backend/services/voice_service.py`**
```python
class VoiceService:
    """
    Whisper (STT) + Supreme-Bhasha TTS ইন্টিগ্রেশন।
    সম্পূর্ণ বিনামূল্যে (OpenAI Whisper OSS + Coqui TTS)।
    """
    async def speech_to_text(self, audio_bytes: bytes) -> str: ...
    async def text_to_speech(self, text: str, lang: str = "bn") -> bytes: ...
```

---

### 🖼️ ৩.৩ — Visual Intelligence (সপ্তাহ ১২)

**লক্ষ্য:** ইমেজ ইনপুট বিশ্লেষণ করা।

**[NEW] `backend/services/vision_service.py`**
```python
class VisionService:
    """
    Gemini Vision API বা LLaVA (ফ্রি) দিয়ে ইমেজ বিশ্লেষণ।
    """
    async def analyze_image(self, image_bytes: bytes, query: str) -> str: ...
```

---

## 📋 সামগ্রিক ফাইল পরিবর্তন সারসংক্ষেপ (Complete Change Summary)

| কাজ | ফাইল | ধরন | পর্ব |
| :--- | :--- | :--- | :--- |
| Episodic Memory Integration | `backend/memory/episodic_memory.py` | MODIFY | ১ |
| Long-Term User Preferences | `backend/memory/long_term_memory.py` | MODIFY | ১ |
| Behavioral Anomaly Guard | `backend/monitoring/behavioral_guard.py` | **NEW** | ১ |
| Causal Debugger | `backend/monitoring/causal_debugger.py` | **NEW** | ১ |
| Main API Task Recording | `backend/main.py` | MODIFY | ১ |
| Tree-of-Thought Reasoner | `backend/engine/tree_of_thought.py` | **NEW** | ২ |
| Self-Reflection Loop | `backend/engine/self_reflection.py` | **NEW** | ২ |
| Smart Model Router | `backend/engine/smart_router.py` | **NEW** | ২ |
| Debate Engine (Completion) | `backend/engine/debate_engine.py` | MODIFY | ২ |
| Dynamic Tool Forge | `backend/engine/tool_forge.py` | **NEW** | ২ |
| Synthetic Data Pipeline | `backend/pipelines/synthetic_data_pipeline.py` | **NEW** | ৩ |
| Learning Loop + EWC | `backend/adaptive_engine/learning_loop.py` | MODIFY | ৩ |
| Weekly Fine-Tuning CI | `.github/workflows/weekly-fine-tuning.yml` | **NEW** | ৩ |
| Voice Service (STT/TTS) | `backend/services/voice_service.py` | **NEW** | ৩ |
| Vision Service | `backend/services/vision_service.py` | **NEW** | ৩ |

> **মোট: ৬টি MODIFY + ৯টি NEW ফাইল = ১৫টি পরিবর্তন**

---

## 🚀 এখনই শুরু করুন (Start Now)

নিচের যেকোনো একটি বেছে নিন এবং বলুন — আমরা সাথে সাথে সেটি ইমপ্লিমেন্ট শুরু করব:

| কমান্ড | কী হবে |
| :--- | :--- |
| `"pillar 1 start"` | Episodic Memory + Behavioral Guard শুরু করা |
| `"pillar 2 start"` | Tree-of-Thought + Smart Router শুরু করা |
| `"pillar 3 start"` | Synthetic Data Pipeline + EWC শুরু করা |
| `"all phases start"` | সব ১৫টি পরিবর্তন একসাথে শুরু করা |
