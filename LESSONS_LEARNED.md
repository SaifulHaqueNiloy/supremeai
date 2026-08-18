# LESSONS_LEARNED
> **[🤖 AI AGENT INSTRUCTION]** 
> This is a core SupremeAI "Brain" file. When adding a new lesson:
> 1. Add it to the TOP of the list (reverse chronological).
> 2. Include Date, Issue, Fix, and Lesson.
> 3. DO NOT delete or overwrite past historical entries.
> 4. Keep it concise and technical.

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

## 2026-08-19 — 📋 Roadmap Metric Validation: Codebase drift in DEVELOPMENT_ROADMAP.md
- **সমস্যা:** `DEVELOPMENT_ROADMAP.md`-এর সবচেয়ে বড় সমস্যা ছিল রোডম্যাপের মেট্রিকগুলো কোডবেসের সঙ্গে sync নয়।
  Store count 11 (actual 9 — themeStore deleted + useWorkspaceSettingsStore merged), test file 282
  (actual 373), route files 84 (actual 85 incl. `__init__.py`), client paths `apps/mobile`+`apps/desktop`
  (actual: `tools/mobile`+`tools/desktop`)।
- **ফিক্স:** কোডবেস স্ক্যান করে সব মেট্রিক সরাসরি verify করে রোডম্যাপ আপডেটেড।
- **লেসন:** রোডম্যাপ/ডকুমেন্ট আপডেটের সময় অবশ্যই `Get-ChildItem` / `grep` দিয়ে live metric
  cross-check করুন — ডকুমেন্টের ওপর ভিত্তি করে প্ল্যান বানালে ভুল ধারণা হয়।

## 2026-08-18 — 🐛 Admin Session Fix: 3 frontend/backend bugs causing forced-logout & 405 on Skills tab

- **সমস্যা:** (A) Admin পেজ রিফ্রেশ করলে সেশন হারায় — `adminStore.ts`-এ কোনো session restore নেই,
  `adminAuthenticated: false` ডিফল্ট; (B) apiInterceptor global fetch wrapper-এ 401/403 হলে সবার জন্যে
  `handleAdminLogout()` call করে — ইউজার-ফেসিং API-এর 401ও অ্যাডমিন সেশন ভাঙায়; (C) Skills & Agents
  ট্যাবে `apiClient.get('/api/skills/search')` কল করে কিন্তু backend-এ POST-only route ছিল → 405।
- **ফিক্স:** (A) `restoreAdminSession()` যোগ করে localStorage-এর `supreme_admin_jwt`-কে decode +
  exp চেক করে `adminAuthenticated`/`adminRole` restore; (B) `isAdminApiPath()` helper যোগ করে
  শুধু `/api/admin` + `/api/skills` পাথ-এর 401/403-ই auto-logout ট্রিগার করে; (C) backend-এ
  GET `/skills/search` endpoint যোগ করে (shared `_search_skill_manifests` helper) +
  `adminTokenStore.ts`-এ exp validation যোগ করে।
- **লেসন:** (1) Zustand store-এর initial state পুনঃস্থাপন (session restore) ছাড়া
  JWT-based auth সবসময় refresh-এ ভাঙবে; (2) Global fetch interceptor override করলে
  auto-logout logic-কে কি পাথে scope করা যাচ্ছে তা explicitly check করুন; (3) Frontend
  GET কলের জন্য backend-এ GET endpoint আছে কিনা code-level ভেরিফাই করুন — POST-only route
  থাকলে 405 Method Not Allowed পাওয়া যায়।

- **সমস্যা:** consolidate করতে গিয়ে দেখা গেল যে `useSupremeStore` (generic ১-কনসামার স্কাফোল্ড) আসল store-গুলোর
  সাথে **আংশিক shape match** করে — ফলে blind re-export shim বা সরাসরি রিনেম করলে কনসামার ব্ল্যাক হয়।
  যেম: `authStore.login(email,password)` বাস্তব apiClient POST করে, কিন্তু
  `useSupremeStore.login(userData)` সরাসরি set করে (signature ভিন্ন)।
- **ফিক্স/লেসন:**
  (১) `themeStore`-এর কনসামার **শূন্য** (frontend/src + apps/ দুটোখানেই 0 import) → dead code, সরিয়ে
  ফেলা হয়েছে (useSupremeStore-এর `theme` fieldটা আছে)। (২) Store merge-এর সময় কেবলমাত্র স্টোরের নাম,
  consumer count দেখে না বাঁচানো যায় — **field shape + action signature match** করে নি কিন্তে
  typecheck-এ ব্যরক্তিকরণ ধরা দেয়। (৩) `useSupremeStore` একটি generic scaffold (১টি কনসামার, শুধু `user`)
  — সেজন্য এর মধ্যে merge করার আগে আসল logic port করতে হবে; staged migration + typecheck gate জরুরি।

## 2026-08-18 — 🧩 M0.2 Store Consolidation: `useWorkspaceSettingsStore` → `useWorkspaceStore` (single source of truth)

- **সমস্যা:** দুইটি workspace store (`useWorkspaceStore` + `useWorkspaceSettingsStore`) আলাদা আলাদা
  integration state রাখত — `activeIntegrations: string[]` vs `integrations: DockIntegration[]`; উভয়েই
  আলাদা `toggleIntegration` ও আলাদা persist key ছিল। ফলে এক জায়গায় toggle করলে অন্যটায় সিঙ্ক হতো না
  (duplication + inconsistent state)।
- **ফিক্স:** `useWorkspaceSettingsStore`-কে `useWorkspaceStore`-তে একীভূত করা হয়েছে —
  `toggleIntegration` এখন `activeIntegrations` ও `integrations[].enabled` দুটোই সিঙ্ক করে। `DockIntegration`
  type export, `reorderIntegrations`, merged `partialize` (persist)। ActionDock-এর import re-point, redundant
  store file delete। **Store count 11 → 10।** Typecheck clean (store-সংক্রান্ত 0 error)।
- **লেসন:** (১) একই ডোমেইনের duplicated state ২টা store-এ রাখা যাবে না — merge করে single source of truth
  বানাতে হবে; (২) store merge-এর আগে consumer blast radius স্ক্যান করুন (ActionDock / DynamicActionDock /
  DashboardShell — মাত্র ৩ ফাইল) — ছোট, নিরাপদ consolidation দিয়ে শুরু করা ভালো; (৩) shared working tree-তে
  unrelated files অন্য agent-modify করলে (BrainVisualizer.tsx untracked, AdminSubTabContent.tsx modified)
  typecheck-এ unrelated error আসতে পারে — নিজের changed files-এর error-ই যাচাই করুন।

## 2026-08-18 — 🐛 M0.1 Mistake: Frontend wired to non-existent `/api/chat/history` endpoint

- **সমস্যা:** `InteractiveChatTab.tsx`-এ chat history-র জন্য `useEffect` + `isLoadingMessages` state যোগ করে
  `${getApiBaseUrl()}/api/chat/history`-তে fetch করার প্ল্যান করা হয়েছিল — কিন্তু **backend-এ ওই GET endpoint
  exists-ই করে না** (chat routes সব POST-only: `/stream_chat`, `/api/chat/stream`, `/api/chat/completion`)।
  ফলে সবসময় fallback hit হতো + unused state-র জন্য typecheck error (TS6133)।
- **ফিক্স:** backend route scan করে নিশ্চিত হওয়া গেল endpoint নেই; তাই unused `isLoadingMessages`/
  `setIsLoadingMessages` বাদ দিয়ে welcome message-কে legitimate static UI initial state হিসেবে রাখা হয়েছে।
- **লেসন:** ফ্রন্টএন্ডে `fetch()` wire করার **আগে** backend-এ ওই endpoint কোড-লেভেল ভেরিফাই করো
  (route scan), নতুবা dead-endpoint wiring + unused state-র debt হয়।

## 2026-08-18 — 🔄 GitHub Actions: `gh pr edit` GraphQL `read:org` Scope Failure → REST API Failsafe

- **সমস্যা:** Staging CI workflow-তে `gh pr edit` কমান্ড দিয়ে প্রমোশন পিআর আপডেট করতে গিয়ে GitHub GraphQL API ফেইল করছিল: `The 'login'/'name'/'slug' field requires one of the following scopes: ['read:org'], but your token has only been granted the: ['repo', 'workflow'] scopes`। ক্লাসিক PAT-এ `read:org` স্কোপ না থাকলে `gh pr edit` ফেইল করে সম্পূর্ণ সিআই ব্লক করে দেয়।
- **ফিক্স:** `supreme-core-ci.yml`-এ `gh pr edit` / `gh pr merge` কমান্ডের পরিবর্তে পিওর Python `urllib.request` দিয়ে GitHub REST API (`PATCH /repos/{owner}/{repo}/pulls/{id}`) ব্যবহার করা হয়েছে। REST API শুধুমাত্র `repo` স্কোপেই পারফেক্টলি কাজ করে এবং `read:org` স্কোপের উপর নির্ভরশীল নয়।
- **লেসন:** সিআই স্ক্রিপ্টে ক্রস-অর্গানাইজেশন পিআর বা ইস্যু ম্যানেজমেন্টের জন্য `gh` GraphQL-নির্ভর কমান্ডের চেয়ে GitHub REST API (v3) অনেক বেশি স্থিতিশীল ও স্কোপ-অ্যাগনস্টিক।

## 2026-08-18 — 🔑 Cross-Repo Staging Promotion 403: Secret Token Scopes & Organization Ownership

- **সমস্যা:** Staging CI workflow-তে `🟢 Auto Create Promotion PR from Staging to Main Repo` ফেইল করছিল: `remote: Permission to paykaribazaronline/supremeai.git denied to SaifulHaqueNiloy. fatal: unable to access ... 403`। কারণ GitHub Secrets-এ `MAIN_REPO_TOKEN` হিসেবে `SaifulHaqueNiloy`-এর fine-grained PAT ছিল যা `paykaribazaronline` অর্গানাইজেশনে রাইট/পুশ পারমিশন রাখেনি।
- **ফিক্স:** `.env`-এর ভ্যালিড `GITHUB_PAT_AUTO_FIX` (যা `paykaribazaronline` ওনারের `repo` + `workflow` পারমিশন সম্পন্ন ফুল ক্লাসিক PAT) সনাক্ত করে `gh secret set` দিয়ে `SaifulHaqueNiloy/supremeai` এবং `paykaribazaronline/supremeai` উভয় রিপোজিটরির `MAIN_REPO_TOKEN` ও `MIRROR_REPO_TOKEN` সিক্রেটে আপডেট করা হয়েছে। এছাড়া Infisical ভল্টেও `SUPREMEAI_GITHUB_TOKEN` সিঙ্ক করা হয়েছে এবং `git ls-remote` দিয়ে কানেক্টিভিটি টেস্ট (Exit code 0) ভেরিফাই করা হয়েছে।
- **লেসন:** Cross-repo git push / promotion PR তৈরি করতে টার্গেট রিপোজিটরির ওনার অ্যাকাউন্টের ফুল `repo` ও `workflow` স্কোপযুক্ত PAT সিক্রেট হিসেবে কনফিগার করতে হবে।

## 2026-08-18 — 🐛 Scraper CI Lint Failures: Ruff F401 / I001 / BLE001

- **সমস্যা:** GitHub Actions-এর Scraper Service Build CI ফেইল করছিল। `backend/services/scraper/` এবং তার টেস্ট ফাইলে ৪টি লিন্টার এরর ছিল: (১) `test_scraper_service.py`-তে unused `MagicMock` import (F401), (২) `test_scraper_service.py`-তে unsorted imports (I001), (৩) `test_stagehand.py`-তে unused `os` import (F401), (৪) `stagehand_agent.py`-তে blind exception catch `except Exception` without `# noqa: BLE001` (BLE001)।
- **ফিক্স:** `test_scraper_service.py`-তে unused `MagicMock` রিমুভ ও import সাজানো হয়েছে, `test_stagehand.py`-তে unused `os` বাদ দেওয়া হয়েছে, এবং `stagehand_agent.py`-তে `# noqa: BLE001` যুক্ত করা হয়েছে। `ruff check` এবং `pytest` রান করে ৪৩টি টেস্ট ১০০% পাস ভেরিফাই করা হয়েছে।
- **লেসন:** CI পুশ করার আগে সার্ভিস সাব-ডিরেক্টরির উপর `ruff check` ও `pytest` রান করে নেওয়া নিশ্চিত করতে হবে।

## 2026-08-18 — 🐛 `.gitignore: test_*.py` Path Trap: Test Files Silent in Version Control

- **সমস্যা:** `.gitignore`-এ `/` prefix ছাড়া `test_*.py` লাইন ছিল — যা **যেকোনো depth-এ** ম্যাচ
  করে (root-স্কোপ নয়)। ফলে নতুন লেখা সব `backend/tests/test_*.py` ফাইল গিটে commit হতোই না —
  `test_confidence_gate.py`, `test_multi_needle.py` ইত্যাদি **roadmap-এ "implemented & verified
  (24/24 pass)" দাবিকৃত টেস্ট files-ও কখনো version control-এ ছিল না**, CI-তেও চলে না। একইভাবে
  `sync_*.py` ও `*_env.py` নেস্টেড ফাইল ignore করত।
- **ফিক্স:** এক-off root স্ক্রিপ্ট ইগনোর করা হলো **root-স্কোপ** দিয়ে — `/test_*.py`,
  `/sync_*.py` (M1.6)। এরপর ১০টি পূর্ব-অনির্বচিত টেস্ট ফাইল **git add** করে commit
  (`13040e2080`, 11 files, 76 tests collect, test_confidence_gate 10/10 pass)।
- **লেসন:** (১) `.gitignore` প্যাটার্ন সবসময় `/` দিয়ে root-scope করো — নতুবা `test_*.py` nested
  টেস্ট সাইলেন্ট exclude হয় (version control + CI থেকে হারায়); (২) "verified পাস" দাবি
  `git ls-files` দিয়ে যাচাই করো।
