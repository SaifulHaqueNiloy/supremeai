# LESSONS_LEARNED
> **[🤖 AI AGENT INSTRUCTION]** 
> This is a core SupremeAI "Brain" file. When adding a new lesson:
> 1. Add it to the TOP of the list (reverse chronological).
> 2. Include Date, Issue, Fix, and Lesson.
> 3. DO NOT delete or overwrite past historical entries.
> 4. Keep it concise and technical.

## 2026-08-19 — ⚡ Python f-string Backslash Syntax & WebSocket Delta Streaming Optimization
- **সমস্যা:** (1) `backend/api/routes/task.py`-এ f-string এক্সপ্রেশনে ব্যাকস্ল্যাশড কোটস `f"'{circuit_breaker_name or \"unknown\"}'"` থাকার কারণে Python 3.11-এ `SyntaxError: unexpected character after line continuation character` হচ্ছিল যা pytest টেস্ট স্যুটের ইমপোর্ট ক্র্যাশ করাচ্ছিল; (2) `realtime_dashboard.py`-এ SwarmPubSub থেকে প্রতি ২ সেকেন্ডে ফুল মেট্রিক স্ন্যাপশট ব্রডকাস্ট করায় লাইভ কানেকশনে প্রচুর ব্যান্ডউইথ খরচ হচ্ছিল।
- **ফিক্স:** (1) `task.py`-এর f-string এক্সপ্রেশনের ভেতরে নেস্টেড কোটস বাইরে ভ্যারিয়েবলে অ্যাসাইন করে সিনট্যাক্স এরর দূর করা হয়েছে; (2) `DashboardWebSocketManager`-এ `compute_metric_delta` স্টেট ডিফারেন্সিং ইঞ্জিন যুক্ত করে শুধুমাত্র পরিবর্তিত ফিল্ডগুলো (`metrics.delta`) স্ট্রিম করার ব্যবস্থা করা হয়েছে; (3) CI ও `pyproject.toml`-এ কভারেজ সোর্স সব প্রডাকশন মডিউলে সম্প্রসারিত করা হয়েছে।
- **লেসন:** (1) Python f-string-এর ভেতরে সরাসরি ব্যাকস্ল্যাশ দিয়ে কোটস এস্কেপ করা এড়াতে হবে (বাইরে ভ্যারিয়েবলে রাখা নিরাপদ); (2) রিয়েল-টাইম পাব-সাব ডেটা ক্লায়েন্টে স্ট্রিমিংয়ের ক্ষেত্রে ফুল অবজেক্টের বদলে স্টেট ডেল্টা ফিল্টারিং ব্যবহার করলে নেটওয়ার্ক ব্যান্ডউইথ ও মেমরি খরচ ৯০% পর্যন্ত কমানো যায়।

## 2026-08-18 — 🧠 Trio 2.0: Self-Healing Loop + Cache + AST

- **সমস্যা:** (1) স্বয়ংচালিত রিপেয়ার লুপে `issues`-কে `writer.repair()`-এ পাঠাতে হলে কোডের কন্টেক্স্ট হারিয়ে যায়;
  (2) ৩টি আলাদা পরীক্ষার জন্য `tri_adapters.py` lazy import + importlib path resolution inconsistent (worktree আগে primary-এর চেয়ে পছন্দ করে);
  (3) `trio_pipeline.py`-এর module-level `from loguru import logger` test env-তে ImportError ট্রিগার করে।
- **ফিক্স:** (1) `repair()`-এর `previous_code` প্যারামিটার যোগ করে সঠিক রিকনটেক্স্ট বজায় রাখা হয়;
  (2) test-এর `_load_adapters()` candidate listে main repo path-worktree path আগে রাখা হয়;
  (3) test-এর `_load_pipeline()`-এ loguru stub injection + `agents.ide` package hierarchy sys.modules-এ যোগ করা হয়।
- **লেসন:** importlib-এ সম্পূর্ণ package hierarchy sys.modules-এ inject করলে lazy `from agents.ide.trio_adapters import ...` কাজ করে;
  shadow learning (cache.set) test env-তে graceful exception handling বাধ্যতন্নয়ী — `_shadow_learn` try/except করে কখনোই পাইপলাইনকে ব্লক করে না।

## 2026-08-19 — 🗄️ Memory Layer Encapsulation & Eager DB Connection Guard
- **সমস্যা:** `memory/cloud_postgres_store.py` ক্লাসের `__init__`-এ সরাসরি eager `_init_tables()` কল
  করা হয়েছিল যা লোকাল ডেভেলপমেন্ট বা টেস্ট এনভায়রনমেন্টে PostgreSQL সার্ভার অনুপস্থিত থাকলে ইমপোর্ট টাইমে
  ক্র্যাশ ঘটাত (`psycopg2.OperationalError: connection refused`)। এছাড়া `UnifiedDBManager`-এ ডিলিট ও
  হেলথ চেক মেথডের অভাব ছিল।
- **ফিক্স:** (A) `cloud_postgres_store.py`-তে কানেকশন স্ট্রিং চেক ও `try/except` রেজিলিয়েন্ট গার্ড যোগ
  করা হয়েছে যাতে অফলাইন/টেস্ট মোডে কোনো ক্র্যাশ না হয়; (B) `UnifiedDBManager`-এ `delete_record()` এবং
  `health_check()` মেথড যোগ করা হয়েছে; (C) `sqlite_store.py`-তে অ্যাসিঙ্ক KV persistence ও `SQLiteStore`
  অ্যালিয়াস যোগ করা হয়েছে; (D) `memory/__init__.py`-তে সেন্ট্রাল এক্সপোর্ট ডিফাইন করা হয়েছে।
- **লেসন:** ডাটাবেস অ্যাডাপ্টারের `__init__`-এ কখনোই আনগার্ডেড নেটওয়ার্ক কল বা টেবিল ইনিট করবেন না;
  কানেকশন গার্ড ও ফলব্যাক মেকানিজম যুক্ত করে সিস্টেমকে ফল্ট-টলারেন্ট ও $0-cost অফলাইন ফ্রেন্ডলি রাখুন।

## 2026-08-19 — 🎯 Zustand Store Consolidation: 9 stores into unified slice pattern with zero regressions
- **সমস্যা:** Frontend-এ ৯টি ভিন্ন ভিন্ন Zustand স্টোর (`authStore`, `dashboardStore`, `customerStore`,
  `sessionCockpitStore`, `useIdeStore`, `useStore`, `adminStore`, `useWorkspaceStore`, `useSupremeStore`)
  বিচ্ছিন্নভাবে স্টেট মেইনটেইন করছিল, যার ফলে ইন্টার-ট্যাব ডাটা সিঙ্ক নষ্ট হচ্ছিল এবং টাইপিং মিসম্যাচ তৈরি হচ্ছিল।
- **ফিক্স:** `frontend/src/store/slices/` ফোল্ডারে প্রতিটি ডোমেনের স্লাইস (`dashboardSlice`, `customerSlice`,
  `sessionCockpitSlice`, `ideSlice`, `coreSlice`, `authSlice`) পূর্ণাঙ্গভাবে সমৃদ্ধ করে `useSupremeStore`-এ
  মার্জ করা হয়। পুরোনো স্টোর ফাইলগুলোকে টাইপ-সেফ backward-compatible shim-এ রূপান্তর করা হয় যাতে কোনো
  কনজ্যুমার কম্পোনেন্ট না ভাঙে।
- **লেসন:** মনোলিথিক স্টেট রিফ্যাক্টরিং করার সময় একবারে সব কনজ্যুমার আপডেট না করে, আগে প্রতিটি স্লাইসের
  শেপ এবং মেথড এক্সপ্যান্ড করে পুরোনো ফাইলগুলোকে backward-compatible shim বানিয়ে মাইগ্রেশন সম্পন্ন করলে
  জিরো-ব্রেকিং এবং ১০০% টাইপ-সেফটি বজায় থাকে।

## 2026-08-19 — 📋 SSE Auth: EventSource can't send Authorization headers
- **সমস্যা:** Command Center-এর SSE bridges (`sseBridges.ts`) EventSource ব্যবহার করে
  `/admin-api/logs/stream?token=...` ও `/admin-api/events/stream?token=...` এ CONNECT করে। কিন্তু
  backend-এর `admin_dashboard.py` router-এর level-এ `require_admin_token` (HTTP Bearer) dependency
  ছিল — EventSource কখনোই Authorization header পাঠাতে পারে না → 401। আর `/events/stream` endpoint
  আসলে backend-এ একদমই ছিল না → 404।
- **ফিক্স:** (A) `admin_auth.py`-এ `validate_sse_token()` ফাংশন যোগ করে JWT query param থেকে
  verify করে; (B) `admin_dashboard.py`-এ `sse_router` নামে আলাদা APIRouter তৈরি করে
  `validate_sse_token` dependency দিয়ে; (C) `/logs/stream`-কে `@sse_router` এ সরিয়ে দেওয়া হয়;
  (D) নতুন `/events/stream` SSE endpoint যোগ করা হয়; (E) `api/__init__.py`-এর
  `register_router`-এ `sse_router` attribute auto-registration যোগ করা হয়।
- **লেসন:** SSE/WebSocket transport-এর জন্য Authorization header না পাঠানোর কারণে query-param
  token validation প্রয়োজন — router-level `HTTPBearer` dependency কাজ করে না। SSE endpoints-ই
  আলাদা router-এ `validate_sse_token` dependency দিয়ে স্বাধীনভাবে register করুন।

## 2026-08-19 — 🐛 TypeScript Immutability: React state mutation in canvas handlers
- **সমস্যা:** `BrainVisualizer.tsx`-এ `draggedNode` state variable-এর `.x`/`.y` সরাসরি
  mutate করা হয়েছিল (React immutability lint rule violation)।
- **ফিক্স:** `draggedNode` state-টি `draggedNodeId` (string|null) এ পরিবর্তন করে,
  `handleMouseMove`-এ `physicsNodesRef`-এর মাধ্যমে node object খুঁজে mutation করে
  (ref mutation is safe — not tracked by React)。
- **লেসন:** Canvas drag handlers-এ state object-এর property mutate করবেন না;
  ref-based lookup + state-based ID tracking ব্যবহার করুন।

## 2026-08-19 — 🐛 TypeScript: useWorkspaceStore shim doesn't re-export useSupremeStore
- **সমস্যা:** `ActionDock.tsx` `import { useSupremeStore } from '../../store/useWorkspaceStore'`
  করে — কিন্তু `useWorkspaceStore.ts` shim-এ `useSupremeStore` re-export করে নি (কেবলমাত্র
  `DockIntegration`, `Notification` types re-export করে)।
- **ফিক্স:** Type import-টি `../../store/useSupremeStore` থেকে এবং `DockIntegration` type import-টি
  `../../store/slices/types` থেকে সরাসরি করা হয়।
- **লেসন:** Shim file-এর `export { useSupremeStore }` না থাকলে TypeScript `TS2459` error দেয় —
  shim-এর সব public symbol re-export করা নিশ্চিত করুন।
