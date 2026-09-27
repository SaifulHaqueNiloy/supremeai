# SupremeAI — Collective Agent Memory & Solution Knowledge Base Architecture

> **Axiom:**  
> **“তোমার মতো আরও অনেকের সেইম সমস্যা হয়েছিল—সেটা কীভাবে সলভ করেছে? আমাদের সিস্টেমে অলরেডি কোনো সমাধান আছে কি না দেখো! না থাকলে তোমার ও তোমার মতো যারা ভবিষ্যতে সমস্যায় পড়বে তাদের জন্য রাস্তা তৈরি করো।”**
>
> **Core Principle:**  
> **Search Before Solving · Pave Before Leaving**  
> No agent solves in isolation. Collective intelligence transforms individual mistakes into permanent system strengths.

---

## 1. Executive Summary

SupremeAI-এর মাল্টি-এজেন্ট সিস্টেমে প্রতিদিন শত শত জটিল কোডিং, কনফিগারেশন ও টেস্ট চ্যালেঞ্জ আসবে। কোনো এজেন্টকে শূন্য থেকে চাকা আবিষ্কার করতে হবে না। প্রতিটি এজেন্টের কাজ শুরু হবে অতীত সমাধানের অভিজ্ঞতা যাচাই করে এবং কাজ শেষ হবে ভবিষ্যতের সহকর্মীদের জন্য স্পষ্ট পথ তৈরি করে।

```text
               [ INCOMING TASK OR ERROR ]
                           │
                           ▼
          ┌──────────────────────────────────┐
          │  Step 1: Search Past Solutions   │
          │  "Does SupremeAI already know?"   │
          └─────────────────┬────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
          [ FOUND ]                  [ NOT FOUND ]
              │                           │
              ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │  Step 2: Apply   │        │ Step 2b: Solve   │
    │  Proven Recipe   │        │ Soundly & Verify │
    └─────────┬────────┘        └─────────┬────────┘
              │                           │
              │                           ▼
              │                 ┌──────────────────┐
              │                 │ Step 3: Pave Way │
              │                 │ Record in DB &   │
              │                 │ LESSONS_LEARNED  │
              │                 └─────────┬────────┘
              └─────────────┬─────────────┘
                            ▼
                     [ SAFE DELIVERY ]
```

---

## 2. The Three Architectural Pillars

### Pillar 1: Mandatory MCP Control Tower Connection (`mcp.json`)
সকল এজেন্ট (Antigravity IDE, Cursor, Claude Desktop, CLI Agent, Autonomous Worker) স্টার্টআপে বাধ্যতামূলকভাবে SupremeAI MCP Control Tower-এর সাথে কানেক্ট করবে:
- **Local IDE Configuration:** Workspace রুট ফোল্ডারে `mcp.json`-এর মাধ্যমে `supremeai-control-tower` কানেক্ট করা থাকে:
  ```json
  {
    "mcpServers": {
      "supremeai-control-tower": {
        "command": "npx",
        "args": ["tsx", "infrastructure/mcp-control-plane/src/index.ts"],
        "env": {
          "MCP_TRANSPORT": "stdio",
          "MCP_CLIENT_REGISTRY_FILE": "config/mcp-clients.json"
        }
      }
    }
  }
  ```
- **Remote / SSE Connection:** রিমোট রানারের জন্য `MCP_TOWER_URL=https://supremeai-mcp-tower.onrender.com/sse` ব্যবহার করে হার্টবিট ও টুলস এক্সেস করা হয় (`scripts/agents/mcp_tower_client.py`)।
- **Exposed Memory Tools:**
  - `memory_get_similar_tasks`: সদৃশ সমস্যা ও সমাধান খুঁজে আনে।
  - `memory_search_learned_facts`: অতীতে শেখা শিক্ষা ও নিয়ম সার্চ করে।
  - `memory_record_task`: নতুন সমাধানের ধাপ ও মেট্রিক ডাটাবেসে সেভ করে।
  - `memory_remember_fact`: স্থায়ী ফ্যাক্ট ও প্রতিরোধমূলক নির্দেশ সংরক্ষণ করে।

---

### Pillar 2: Collective Memory Storage Engine (Database Layer)
এজেন্টদের জন্য সমাধান ও মেমোরি সংরক্ষণ স্তর:
1. **Vector & Semantic Database:** Supabase pgvector / Qdrant ভেক্টর সার্চ—প্রবলেমের টেক্সট ও এরর সিগনেচারের কসাইন সিমিলারিটি বের করে।
2. **Episodic & Structured Database (`ai_memory` / `task_checkpoints`):** টাস্ক আইডি, ইনপুট প্রম্পট, এক্সিকিউটেড কোড, ল্যাটেন্সি এবং সাকসেস/ফেইলিউর ফলাফল ধারণ করে।
3. **Local Permanent Ledger (`LESSONS_LEARNED.md`):** মানব-পঠনযোগ্য এবং গিট-ভার্শন নিয়ন্ত্রিত রেজিস্ট্রি।

```yaml
# Schema of a Recorded Solution / Episode
solution_record:
  task_id: "issue-2201"
  error_pattern: "UnicodeEncodeError: 'charmap' codec can't encode character '\\u2705'"
  root_cause: "Windows PowerShell default console encoding cp1252 cannot encode UTF-8 emojis."
  validated_solution: "Set $env:PYTHONIOENCODING='utf-8' before executing python script."
  tags: ["windows", "encoding", "ci-guard", "python"]
  timestamp: 1759000000
  success: true
```

---

### Pillar 3: The "Search-and-Pave" Operational Discipline

#### 🔍 Step 1: Search First (খোঁজ করো)
যেকোনো কাজ শুরু করার আগে বা কোনো এরর দেখা দিলে এজেন্টের প্রথম পদক্ষেপ:
```bash
python scripts/agents/agent_solution_memory.py search --query "failing test or error message"
```
অথবা MCP Tool: `memory_get_similar_tasks(query="...")` বা `memory_search_learned_facts(query="...")`।
- যদি সমাধান পাওয়া যায়, তবে অপ্রয়োজনীয় পরীক্ষা-নিরীক্ষা পরিহার করে সরাসরি ভেরিফাইড সমাধানটি প্রয়োগ করবে।

#### 🛠️ Step 2: Apply or Solve (সমাধান করো)
- অতীতের সমাধান থাকলে তা প্রয়োগ করে টেস্ট ভেরিফাই করবে।
- সমাধান না থাকলে এজেন্টের সম্পূর্ণ স্বাধীনতা রয়েছে (Kite & Spool Principle অনুযায়ী) সেরা পদ্ধতি বের করার।

#### 🛣️ Step 3: Pave the Way for Future Agents (রাস্তা তৈরি করো)
সমস্যা সমাধানের পর এজেন্ট ভবিষ্যতের এজেন্টদের জন্য রাস্তা তৈরি করবে:
```bash
python scripts/agents/agent_solution_memory.py record \
  --task-id "issue-xxx" \
  --problem "সমস্যার বিবরণ ও এরর সিগনেচার" \
  --solution "কীভাবে সমস্যার সমাধান করা হয়েছে" \
  --lesson "ভবিষ্যতে যাতে পুনরাবৃত্তি না হয় তার নিয়ম" \
  --tags "area,component"
```
একই সাথে [`LESSONS_LEARNED.md`](../../LESSONS_LEARNED.md)-তে এক লাইনে এন্ট্রি যুক্ত হবে।

---

## 4. Integration with AGENTS.md Constitution
- **Rule Zero:** "Leave SupremeAI better than you found it, day by day."
- **Collective Memory Rule:** "Search past solutions before coding; pave pathways in the database when unrecorded problems are solved."
