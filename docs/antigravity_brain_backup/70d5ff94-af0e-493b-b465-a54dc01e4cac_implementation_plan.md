# SupremeAI 2.0 — Full Health Audit & Bug Fix Plan

সম্পূর্ণ codebase deep-scan করে ৬টি **critical bug** এবং ২টি **medium-risk issue** পাওয়া গেছে। নিচে বিস্তারিত:

---

## 🔴 Critical Bugs (অবশ্যই ঠিক করতে হবে)

### Bug 1: `pending_tasks.py` — কানেকশন বন্ধ করার পরও কুয়েরি চালানো (CRASH)

> [!CAUTION]
> `update_task_status()` ফাংশনে `conn.close()` কল করার **পরে** `cursor.execute(SELECT ...)` আবার চালানো হচ্ছে। এটি প্রতিটি approve/reject কলে `sqlite3.ProgrammingError` crash করবে।

**File:** [pending_tasks.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/models/pending_tasks.py#L110-L126)

```diff
 def update_task_status(task_id: str, status: TaskStatus, resolved_by: str, reason: str | None = None) -> PendingTask | None:
     conn = _get_conn()
     cursor = conn.cursor()
     resolved_at = datetime.now(timezone.utc).isoformat() if status != TaskStatus.PENDING else None
     cursor.execute(
         """
         UPDATE pending_tasks SET status = ?, resolved_by = ?, resolved_at = ?, reason = ?
         WHERE task_id = ?
         """,
         (status, resolved_by, resolved_at, reason, task_id),
     )
     conn.commit()
-    conn.close()
     cursor.execute("SELECT * FROM pending_tasks WHERE task_id = ?", (task_id,))
     row = cursor.fetchone()
     conn.close()
     return row_to_task(row) if row else None
```

---

### Bug 2: `pending_tasks.py` — `init_db()` কখনো কল হয় না

> [!CAUTION]
> `init_db()` ফাংশনটি define করা আছে কিন্তু startup-এ কখনো কল হচ্ছে না। প্রথমবার `create_pending_task()` চালালে `sqlite3.OperationalError: no such table: pending_tasks` crash হবে।

**Fix:** `_get_conn()` ফাংশনে অথবা `create_pending_task()` এর শুরুতে `init_db()` কল করতে হবে।

```diff
 def _get_conn():
     DB_PATH.parent.mkdir(parents=True, exist_ok=True)
     conn = sqlite3.connect(DB_PATH)
     conn.row_factory = sqlite3.Row
+    conn.execute("""
+        CREATE TABLE IF NOT EXISTS pending_tasks (
+            task_id TEXT PRIMARY KEY,
+            task_type TEXT NOT NULL,
+            payload TEXT NOT NULL,
+            status TEXT NOT NULL,
+            created_at TEXT NOT NULL,
+            resolved_by TEXT,
+            resolved_at TEXT,
+            reason TEXT
+        )
+    """)
     return conn
```

---

### Bug 3: Python Version Mismatch — `3.14` ব্যবহার হচ্ছে, `pyproject.toml`-এ `<3.13`

> [!WARNING]
> সিস্টেমে **Python 3.14.5** ইনস্টল আছে কিন্তু `pyproject.toml` বলছে `python = ">=3.11,<3.13"`।  
> এই কারণে **Poetry dependency resolution কাজ করবে না** এবং `litellm`, `crewai` সহ অনেক package ইনস্টল হয়নি।

**Fix Options:**
1. **(Recommended)** Python 3.12 ইনস্টল করে ব্যবহার করুন (crewai ও অন্যান্য packages 3.12 পর্যন্ত সাপোর্ট করে)
2. অথবা `pyproject.toml` এর version constraint আপডেট করুন: `python = ">=3.11,<3.15"` — তবে এতে crewai/langgraph কাজ নাও করতে পারে

---

### Bug 4: `litellm` ইনস্টল নেই — **সমস্ত LLM কল ব্রেক**

> [!CAUTION]
> `litellm` module ইনস্টল নেই। এর ফলে `llm_gateway.py` → `model_router.py` → `brain/` → `core/app.py` পুরো import chain ব্রেক হচ্ছে। **সার্ভার স্টার্টই হবে না, কোনো API endpoint কাজ করবে না।**

**Fix:** Python version ঠিক করার পর `poetry install` চালান।

---

### Bug 5: `approval_manager.py` — Skill write path ভুল directory-তে লিখছে

> [!IMPORTANT]
> Approve হওয়ার পর skill ফাইল `backend/api/skills/` ডিরেক্টরিতে লেখা হচ্ছে (because of `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` which resolves to `backend/api/`). কিন্তু `auto_skill_creator.py` skills সেভ করে root-level `skills/` ডিরেক্টরিতে।

**File:** [approval_manager.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/api/routes/approval_manager.py#L45-L48)

```diff
-                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
-                skills_dir = os.path.join(backend_dir, "skills")
+                # বাংলা মন্তব্য: backend root থেকে skills ডিরেক্টরি resolve করা হচ্ছে
+                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+                skills_dir = os.path.join(backend_dir, "skills")
```

---

### Bug 6: `evolution/auto_skill_creator.py` — `evolution` মডিউল `sys.path`-এ নেই

> [!WARNING]
> `auto_skill_creator.py` ফাইলটি `evolution/` ডিরেক্টরিতে আছে এবং `from evolution.evolution_react_agent import ...` করছে, কিন্তু `evolution/` ডিরেক্টরি **backend-এর বাইরে** root-level-এ। Backend tests এটিকে খুঁজে পাচ্ছে না কারণ Python path-এ root project directory নেই।

Test error: `ModuleNotFoundError: No module named 'evolution.evolution_react_agent'`

**Fix:** `auto_skill_creator.py`-তে relative import ব্যবহার করতে হবে:

```diff
-from evolution.evolution_react_agent import EvolutionReActAgent
+from .evolution_react_agent import EvolutionReActAgent
```

---

## 🟡 Medium-Risk Issues

### Issue 7: `llm_gateway.py` — `_stream_completion` return type mismatch

`acompletion()` method `stream=True` হলে `return self._stream_completion(...)` করছে, কিন্তু `_stream_completion` একটি `async generator` (yield ব্যবহার করে)। তাই `acompletion()` এর return type `AsyncGenerator` হবে — caller-কে `async for` দিয়ে consume করতে হবে, কিন্তু non-stream path এ dictionary return হয়। এটি inconsistent।

### Issue 8: HITL WebSocket `/ws/hitl` — শুধু sleep loop, কোনো pending task notification পাঠায় না

**File:** [approval_manager.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/api/routes/approval_manager.py#L69-L78)

WebSocket endpoint শুধু `asyncio.sleep(1)` loop-এ wait করছে, কখনো client-কে pending task notification পাঠায় না। এটি একটি incomplete feature।

---

## Proposed Changes

### [Models] pending_tasks.py
#### [MODIFY] [pending_tasks.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/models/pending_tasks.py)
- Fix double `conn.close()` crash (Bug 1)
- Auto-init DB table in `_get_conn()` (Bug 2)

### [API Routes] approval_manager.py
#### [MODIFY] [approval_manager.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/api/routes/approval_manager.py)
- Fix skills directory path resolution (Bug 5)

### [Evolution] auto_skill_creator.py
#### [MODIFY] [auto_skill_creator.py](file:///c:/Users/n/supremeai/supremeai_2.0/evolution/auto_skill_creator.py)
- Fix relative import for `evolution_react_agent` (Bug 6)

---

## User Review Required

> [!IMPORTANT]
> **Python Version Decision:** তোমার সিস্টেমে Python 3.14.5 আছে কিন্তু project 3.11-3.12 require করে। নিচের options থেকে কোনটি চাও?
> - **Option A (Recommended):** Python 3.12 ইনস্টল করে virtualenv তৈরি (সবচেয়ে safe, সব dependency কাজ করবে)  
> - **Option B:** `pyproject.toml` আপডেট করে `<3.15` করা (risky — crewai/langgraph ব্রেক হতে পারে)

> [!IMPORTANT]
> **Bug 3 & 4 ফিক্স করতে dependency install দরকার।** Code fix গুলো (Bug 1, 2, 5, 6) আমি এখনই করতে পারি। Python version decision তোমার কাছ থেকে দরকার।

## Verification Plan

### Automated Tests
```bash
python -m pytest tests/ -x --tb=short -q
```

### Manual Verification
- `POST /approval/approve/{task_id}` endpoint টেস্ট করে দেখা যে crash হচ্ছে না
- Server startup verify করা (`uvicorn main:app`)
