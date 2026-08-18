# Innovation Tools Adoption Plan — SupremeAI

**তারিখ:** 2026-08-18
**তৈরি করেছেন:** Principal AI Engineer (Kilo)
**স্কোপ:** কোডবেস ভেরিফিকেশনের ভিত্তিতে ৫টি প্রস্তাবিত টুলের মধ্যে বাস্তবসম্মত ও উপকারী গুলোর ইমপ্লিমেন্টেশন প্ল্যান।

---

## ০. Verification Summary (Code-Level Findings)

| টুল | ভেরিফাইড স্ট্যাটাস | সিদ্ধান্ত |
|-----|-------------------|-----------|
| ১. Tree-sitter Repo Map | নতুন ফিচার (tree_sitter শুধু lazy import আছে) | ✅ গ্রহণ — নতুন মডিউল দিয়ে |
| ২. Stagehand Self-Healing | নতুন ফিচার (Playwright-based scraper আছে) | ✅ গ্রহণ — feature-flag + fallback দিয়ে |
| ৩. BAML | pydantic-ai ইতিমধ্যে আছে (pyproject:94) | ❌ বাদ — রিডানডেন্ট |
| ৪. PydanticAI | ইতিমধ্যে ইনস্টল্ড (base_pydantic_agent.py) | ❌ বাদ — ইতিমধ্যে ব্যবহৃত |
| ৫. Durable Execution | LangGraph + CheckpointManager আছে | ⚠️ এনহ্যান্সমেন্ট — step-granular replay |

**Root-cause note:** প্রস্তাব #৪-এর লেখক জানতেন না যে PydanticAI আমাদের core dependency। এজন্য প্রস্তাবগুলো blindly copy না করে code-level verify করা হয়েছে।

---

## ১. Tree-sitter Repo Map (HIGH IMPACT, NEW)

**সমস্যা:** বড় কোডবেসে (৫০০+ ফাইল) সব কোড LLM-এ পাঠানো যায় না। বর্তমানে কোনো compact repo-map নেই।

**Plan:**
1. **Dependency:** `pyproject.toml` এ যোগ করুন:
   - `tree-sitter = "^0.23"`
   - `tree-sitter-language-pack = "^0.1"` (prebuilt grammars — compile দরকার নেই, zero-cost)
   - `networkx = "^3.4"` (PageRank) — অথবা বিদ্যমান থাকলে reuse।
2. **নতুন মডিউল:** `backend/tools/repo_map.py` (প্রস্তাবিত `repo_discovery_agent.py` ভুল জায়গা — ওটা GitHub API search টুল)।
   - `RepoMapBuilder.build(max_tokens=1500)` → AST পার্স → class/func signatures + import graph → PageRank ranking → compact map স্ট্রিং।
   - Lazy import: `tree_sitter` না থাকলে graceful fallback (file-list only)।
3. **Integration:** কোড-লেখা এজেন্টের context-এ `repo_map` স্ট্রিং ইনজেক্ট করুন (যেখানে `tree_sitter` আগে থেকে ব্যবহার হয় `style_learner.py` — সেই pattern follow করুন)।
4. **Verification:** unit test — ছোট ফিক্সচার রিপো দিয়ে map টোকেন কাউন্ট `<= 1500` এবং সঠিক top-N symbols রিটার্ন করে কিনা।

**Benefit:** এজেন্ট মাত্র ~১০০০ টোকেনে পুরো রিপো আর্কিটেকচার বুঝে সঠিক ফাইলে কোড লিখবে।

---

## ২. Stagehand Self-Healing Web Primitives (MEDIUM IMPACT, NEW — GATED)

**সমস্যা:** বর্তমান browser route (`api/routes/browser.py`) মূলত mock + scraper microservice HTTP proxy। CSS/ID ব্রেক করলে brittle।

**Plan:**
1. **Scraper microservice-এ যোগ করুন** (`backend/services/scraper/`): `stagehand` Python SDK optional dependency।
   - প্রিমিটিভ: `act()`, `extract()`, `observe()` — accessibility tree ভিত্তিক self-healing।
2. **Feature flag:** `settings.enable_stagehand` (default False)। False হলে বর্তমান Playwright path ব্যবহার করে (zero regression)।
3. **Endpoint:** scraper-এ `/browse_stagehand` যোগ করুন; `browser.py` এর `_proxy_to_scraper` এ নতুন branch।
4. **Caveat:** Stagehand Browserbase-এর hosted সার্ভিসের সাথে সবচেয়ে ভালো, কিন্তু self-hosted Playwright দিয়েও চলে। Zero-cost রাখতে self-hosted mode ব্যবহার করুন।
5. **Verification:** `REAL_TESTING_LOG.md` এ hard test — একটি লাইভ সাইটে button click + form fill + extract, তারপর UI-এর CSS class পাল্টে আবার একই goal চালিয়ে self-healing verify করুন।

**Benefit:** হার্ড-টেস্টিং অটোমেশন fail-proof হবে।

---

## ৩. Enhance CheckpointManager with Step-Granular Replay (MEDIUM IMPACT, ENHANCEMENT)

**স্ট্যাটাস:** `backend/tools/checkpoint_manager.py` ইতিমধ্যে PG/Firestore/SQLite resume সাপোর্ট করে। LangGraph (`brain/langgraph_agent.py`) ও আছে।

**Plan:**
1. `Checkpoint.state` এর সাথে `step_log: list[dict]` (event-sourcing) যোগ করুন — প্রতি স্টেপের input/output/ts।
2. নতুন মেথড `replay_from(task_id, step_index)` → নির্দিষ্ট স্টেপ থেকে resume (zero redundant work)।
3. Worker boot-এ `resume_interrupted_tasks()` → crash পর auto-resume।
4. **Verification:** chaos test — checkpoint save করে process kill, restart এর পর ঠিক আটকানো স্টেপ থেকে চলে কিনা।

---

## ❌ Rejected (Rationale)

- **BAML:** pydantic-ai ইতিমধ্যে typed structured output দেয় (`result_type=BaseModel`)। BAML আলাদা DSL + compiler + build-step যোগ করবে — redundant এবং maintainence বাড়াবে।
- **PydanticAI:** ইতিমধ্যে `backend/agents/base_pydantic_agent.py` এ ব্যবহৃত। নতুন adopt করার কিছু নেই।

---

## Execution Order (Atomic) — STATUS: ✅ DONE

1. ✅ **Task-1: Tree-sitter Repo Map**
   - `backend/tools/repo_map.py` (RepoMapBuilder + pure-Python PageRank, lazy tree_sitter import)
   - deps: `tree-sitter ^0.26`, `tree-sitter-language-pack` in `backend/pyproject.toml`
   - test: `backend/tests/tools/test_repo_map.py` (4 passed)
2. ✅ **Task-3: CheckpointManager step-granular replay**
   - `step_log` column + `log_step` / `get_step_log` / `replay_from` / `resume_interrupted_tasks`
   - backward-compatible (ALTER COLUMN IF NOT EXISTS; legacy-DB test included)
   - tests: `backend/tests/tools/test_checkpoint_replay.py` (3 passed) + existing `tests/test_checkpoint_resume.py` (6 passed)
3. ✅ **Task-2: Stagehand self-healing (flagged, fallback-safe)**
   - `ch/SCRAPER` side: `backend/services/scraper/stagehand_agent.py` (act/extract/observe) + `/browse_stagehand` endpoint + health flag
   - backend side: `api/routes/browser.py` `/browse_stagehand` route gated by `settings.enable_stagehand` (ENABLE_STAGEHAND)
   - optional dep group `stagehand` in scraper pyproject
   - tests: `backend/services/scraper/tests/test_stagehand.py` (6 passed, no browser needed)

**Verification note:** BAML ও PydanticAI প্রস্তাব বাদ দেওয়া হয়েছে (code-level verify: ইতিমধ্যে বিদ্যমান)।

**Pro-Suggestion [PRO] [Impact: HIGH]** — Tree-sitter Repo Map কে এজেন্ট নয়, বরং `ai_memory` (pgvector) এর সাথে mesh করুন যাতে repo-map সিম্বলগুলো semantic search-এও কাজে লাগে — একবার build করে বারবার reuse।
