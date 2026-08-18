# SupremeAI 2.0 Architectural Blueprint: Self-Evolving Memory Storage
> **Document ID:** `BLUEPRINT-MEM-001`  
> **Status:** Approved Blueprint for AI Evolution Sprint (Phase 5)  
> **Infrastructure Cost:** $0 (Supabase pgvector + PostgreSQL / Local SQLite)  
> **Language:** Bangla / Banglish (Simple Language) with standard technical specs.

---

## ১. ভূমিকা ও উদ্দেশ্য (Overview & Objective)

SupremeAI-এর **"The Eternal Brain Principle"** অনুযায়ী, ৩য় পক্ষের LLM-গুলো কেবল সাময়িক প্রসেসিং ইঞ্জিন, কিন্তু সিস্টেমের স্থায়ী মেধা সংরক্ষিত হয় নিজস্ব ভেক্টর মেমোরিতে (`ai_memory` / `pgvector`)।

গতানুগতিক মেমোরি সিস্টেমে নতুন তথ্য শুধু ইনসার্ট হতে থাকে, যার ফলে ডুপ্লিকেট তৈরি হয়, সার্চ স্লো হয় এবং প্রাসঙ্গিকতা কমে যায়। **Self-Evolving Memory Storage** এমন একটি অটোনোমাস সাব-সিস্টেম যা:
1. **Semantic Clustering:** সম্পর্কিত মেমোরিগুলোকে স্বয়ংক্রিয় ক্লাস্টারে গ্রুপিং করে।
2. **Semantic Deduplication:** >০.৯৬ সিমিলারিটির মেমোরিগুলোকে মার্জ করে সিন্থেসাইজড মেমোরি তৈরি করে।
3. **Decay & Garbage Collection:** অ্যাক্সেস ফ্রিকোয়েন্সি ও ইম্পরট্যান্স স্কোরের ওপর ভিত্তি করে পুরনো অপ্রয়োজনীয় ডাটা ছাঁটাই করে।
4. **Hierarchical Retrieval:** বড় ভেক্টর স্পেস স্ক্যান না করে ক্লাস্টার হেড থেকে দ্রুত সাব-সেকেন্ডে নিখুঁত কনটেক্সট উদ্ধার করে।

---

## ২. কোর আর্কিটেকচার ডায়াগ্রাম (Architecture Flow)

```
       [New User/Agent Interaction]
                    │
                    ▼
       ┌─────────────────────────┐
       │   RAG / Ingestion Bus   │
       └────────────┬────────────┘
                    │ (Raw Embeddings)
                    ▼
       ┌─────────────────────────┐
       │   ai_memory (pgvector)  │ ◄─────────────────────────┐
       └────────────┬────────────┘                           │
                    │                                        │
                    ▼                                        │
 ┌──────────────────────────────────────┐                    │
 │    SelfEvolveMemoryService (Worker)  │                    │
 ├──────────────────────────────────────┤                    │
 │ 1. Semantic Clusterer (K-Means/Cosine)│ ──► Cluster Heads  │
 │ 2. Semantic Deduplicator (>= 0.96)   │ ──► Merged Memory ─┘
 │ 3. Decay Evaluator (Ebbinghaus Curve) │ ──► Pruned / Archived
 └──────────────────────────────────────┘
```

---

## ৩. কম্পোনেন্ট স্পেসিফিকেশন (Component Specifications)

### ৩.১. `backend/memory/self_evolve_service.py`
অটোনোমাস সার্ভিস যা ব্যাকগ্রাউন্ডে শিডিউলড বা ইভেন্ট-ট্রিগারড ভিত্তিতে চলে।

```python
class SelfEvolveMemoryService:
    def __init__(self, db_manager: UnifiedDBManager):
        self.db = db_manager

    async def cluster_memories(self, tenant_id: str, similarity_threshold: float = 0.82) -> list[MemoryCluster]:
        """মেমোরি ভেক্টরগুলোর মধ্যে কোসাইন সিমিলারিটি বিশ্লেষণ করে ক্লাস্টার তৈরি করে।"""
        ...

    async def deduplicate_memories(self, tenant_id: str, threshold: float = 0.96) -> int:
        """উচ্চমাত্রার সদৃশ মেমোরিগুলোকে একত্রিত করে ১টি একক সামারি মেমোরি বানায়।"""
        ...

    async def prune_decayed_memories(self, tenant_id: str, retention_days: int = 90) -> int:
        """Ebbinghaus Decay Formula: R = e^(-t/S) অনুযায়ী অপ্রয়োজনীয় মেমোরি মুছে ফেলে।"""
        ...
```

### ৩.২. ডেটাবেস স্কিমা এক্সটেনশন (`ai_memory` Table)

```sql
-- Existing ai_memory table extension
ALTER TABLE ai_memory
ADD COLUMN IF NOT EXISTS cluster_id UUID NULL,
ADD COLUMN IF NOT EXISTS access_count INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS importance_score FLOAT DEFAULT 1.0,
ADD COLUMN IF NOT EXISTS is_synthesized BOOLEAN DEFAULT FALSE;

-- Index for cluster and decay queries
CREATE INDEX IF NOT EXISTS idx_ai_memory_cluster ON ai_memory (cluster_id);
CREATE INDEX IF NOT EXISTS idx_ai_memory_decay ON ai_memory (last_accessed_at, importance_score);
```

---

## ৪. এক্সিকিউশন ও ভেরিফিকেশন প্ল্যান (Execution & Test Strategy)

1. **Phase 5 Milestone M5.1:** `backend/memory/self_evolve_service.py` বাস্তবায়ন।
2. **Deterministic Test Suite:** `backend/tests/memory/test_self_evolving_memory.py` তৈরি করা (ক্লাস্টারিং, মার্জিং এবং ডিকে অ্যালগরিদম ভেরিফিকেশন)।
3. **Performance Target:** মেমোরি সার্চ Latency < ৫০ms ($0 Supabase free-tier pgvector-এ)।
