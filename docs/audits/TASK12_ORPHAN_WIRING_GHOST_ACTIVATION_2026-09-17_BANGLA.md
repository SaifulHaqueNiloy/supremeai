# Task-12 — অরফান এন্ডপয়েন্ট ওয়্যারিং + গোস্ট কম্পোনেন্ট অ্যাক্টিভেশন + টেস্ট কভারেজ

তারিখ: 2026-09-17 · বেসলাইন: `bd311b9c` (V8 GREEN) · ফিলোসফি: zero cost / lightweight / fast smooth / zero hardcoded

## ১. অরফান এন্ডপয়েন্ট ওয়্যারিং (wire-first doctrine)

স্ক্যান: `docs/generated/route_inventory.json`-এর 762 রুট × frontend caller-map → 154 অরফান ক্যান্ডিডেট।
যাচাইয়ের পর সবচেয়ে অর্থবহ জোড়া নির্বাচিত (নকল ডেটা ছাড়াই বাস্তব ওয়্যারিং):

| Endpoint | আগের অবস্থা | এখন |
|---|---|---|
| `POST /api/knowledge/search` | orphan (শুধু dead কম্পোনেন্ট থেকে GET কল → 405 হতো) | `/knowledge` পেজ থেকে সঠিক POST contract-এ কল হয় |
| `POST /api/knowledge/seed` | orphan | `/knowledge` পেজের Seed বাটনে wired |
| `GET /api/session/{id}/stream` (SSE) | orphan — কোনো frontend গ্রাহক নেই | `/sessions/:sessionId` ককপিট থেকে লাইভ স্ট্রিম |
| `POST /api/v1/runs/{run_id}/cancel` | কল হত, কিন্তু এক-ক্লিকে (দুর্ঘটনা-ঝুঁকি) | hold-to-confirm (২ সেকেন্ড) gesture |

Backend পরিবর্তন (ন্যূনতম): `search_knowledge` এখন manifest থেকে **dynamically derive** করা
`{id, title, content, source, score}` ফেরত দেয় — আগে raw manifest dict যেত যাতে frontend-এর
রেন্ডার-ফিল্ডই ছিল না (ফাঁকা কার্ড = অসৎ UI)। কোনো skill-নির্দিষ্ট শব্দ hardcoded নয়; অজানা
shape-এও honest fallback (file stem + JSON excerpt)। পাশাপাশি `_manifest_dir()` helper —
টেস্টেবল। অন্য কোনো backend route ফাইল বদলায়নি।

## ২. গোস্ট কম্পোনেন্ট অ্যাক্টিভেশন (zero-ref → reachable)

| কম্পোনেন্ট | আগে | এখন |
|---|---|---|
| `KnowledgePage.tsx` | zero-importer; ভুল GET contract | `/knowledge` route + nav registry (`nav-knowledge`, implemented) |
| `SessionDetailPage.tsx` + ককপিট ক্লাস্টার (ExecutionShell, SandboxViewport, ReasoningLog, FileTreePanel, AgentStatePill) | সম্পূর্ণ transitively dead; store-ও unpopulated | `/sessions/:sessionId` route → প্রকৃত SSE স্ট্রিম (connected ইভেন্ট + logs/state/reasoning/filetree চ্যানেল) |
| `HoldToKillButton.tsx` | zero-importer, keyboard-অদৃশ্য | RunsPage cancel-এ wired; pointer + Space/Enter hold (a11y), disabled state, testid |

নোট: ককপিট ক্লাস্টারের ডেটা batcher-ভিত্তিক — এজেন্ট রানটাইম যখন সেই session_id-তে ইভেন্ট
publish করবে তখনই UI-তে আসবে; না হলে সৎ "connected, অপেক্ষমাণ" অবস্থা। কোনো নকল ইভেন্ট নেই।

## ৩. টেস্ট কভারেজ সম্প্রসারণ

নতুন টেস্ট (মোট +19):
- `backend/tests/api/routes/test_knowledge_search_seed.py` — 8: normalized shape, no-match empty,
  limit, malformed-manifest loud-skip, 422 validation, stem-fallback, seed default/custom counting
- `backend/tests/api/routes/test_session_stream.py` — 4: connected ইভেন্ট + logs/state/reasoning/filetree
  চ্যানেল রাউটিং (generator-level drive — TestClient-এর httpx transport SSE বাফার করে hang করে, তাই ইচ্ছাকৃত)
- `frontend/src/components/dashboard/KnowledgePage.test.tsx` — 4: POST contract, unwrap results,
  খালি অবস্থা, এরর অবস্থা, seed কল
- `RunsPage.test.tsx` +1: hold-to-confirm contract (ক্লিকে cancel হয় না; ২ সেকেন্ড hold-এ একবার)
- `App.routes.test.tsx` +1: `/knowledge` route reachable প্রমাণ

## ৪. যাচাই-ম্যাট্রিক্স (সব লোকালি সবুজ)

- Backend: missions 57/57 · tests/api 705 passed (4 pre-existing byoc fail — V7-এ stash-প্রমাণিত) · নতুন 12/12
- Frontend: vitest 523/523 (100 ফাইল) · tsc 0 error · eslint clean · build 10.96s ✓
- ruff format+check সম্পূর্ণ রিপো সবুজ · lint_plans errors: 0 · duplicate_detector exit 0 · any-ratchet 57==57
- 5টি evidence generator পুনর্চালিত → `docs/generated/` drift শুধু domain graph-এ (+11 লাইন, প্রত্যাশিত)

## ৫. বাকি থাকা owner-সিদ্ধান্ত (এ সাইকেলে ইচ্ছাকৃত অস্পৃশ্য)

- বাকি ~150 অরফান এন্ডপয়েন্টের বেশিরভাগই infra-অভ্যন্তরীণ (webhook/telegram/n8n, admin-api,
  diagram/internet-monitor টুল-পরিবার) — এগুলোর frontend গ্রাহক বানানো আলাদা প্রোডাক্ট সিদ্ধান্ত
- `ScreencastViewer.tsx` (WS ভিত্তিক) এখনো dead — ব্যাকএন্ডের কোন WS এন্ডপয়েন্টে wire হবে তা স্পষ্ট নয়
- `CommandCenterRealtimeProvider.tsx` — CommandCenterApp-এ mount-এর সিদ্ধান্ত owner-এর
