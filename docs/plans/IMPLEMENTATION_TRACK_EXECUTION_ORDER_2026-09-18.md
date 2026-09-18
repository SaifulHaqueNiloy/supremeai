---
id: implementation-track-execution-order
subject: "Issue #453 Implementation Track — প্রমাণ-ভিত্তিক এক্সিকিউশন অর্ডার: ২৩ মডিউলের কোড-সত্য রিকনসিলিয়েশন, মালিকানা ডি-ডুপ্লিকেশন এবং ওয়েভ-ভিত্তিক বাস্তবায়ন ক্রম"
document_role: roadmap
owner_circle: Planning Circle / Head of Planning (docs/plans/ প্ল্যানিং কর্পাসের ধারাবাহিক মালিক)
status: active
target_scope: supremeai_internal
canonical: true
evidence_state: verified
disposition: retain
last_verified: 2026-09-18
supersedes: []
superseded_by: []
source_of_truth: true
---

# Issue #453 — প্রমাণ-ভিত্তিক এক্সিকিউশন অর্ডার (Evidence-Based Execution Order)

**Method (Gate-0 পদ্ধতি):** ২৩টি Crown Jewel মডিউল + Teleport প্ল্যান সম্পূর্ণ পাঠ → fresh main
(`4ac43642`) থেকে প্রতিটি দাবির কোড-যাচাই (file:line evidence)। এই ডকুমেন্টটি issue #453-এর
tier ordering-কে কোড-সত্যের সাথে reconcile করে এবং মালিকানা দ্বন্দ্ব মেটায়।

## ১. ক্রস-ডকুমেন্ট নাম-ড্রিফট সংশোধন (canonical module map)

`.agents/prompts/MASTER_KICKOFF_PROMPT.md` §7-এ কয়েকটি মডিউল-পরিচয় ভুল ছিল; সংশোধিত
ক্যানোনিক্যাল ম্যাপিং (frontmatter title অনুযায়ী):

| Module | Canonical identity (ভুল দাবি → সত্য) |
| --- | --- |
| M03 | **LLM Gateway & Model Routing** — 3-Tier GPU + Zero-Bypass এখানেই (ভুলভাবে M17-কে দেওয়া হয়েছিল) |
| M05 | **Self-Evolution & Learning Loop** (ভুলভাবে M12-কে "Self-Evolution" বলা হয়েছিল) |
| M07 | **Context Engine** (ভুলভাবে "Multi-Agent Swarm" — সেটি M02 Orchestration) |
| M12 | **Governed Skill Ecosystem** |
| M17 | **HITL & Approval Chain** (ভুলভাবে "3-Tier GPU" বলা হয়েছিল) |
| M22 | **Scheduler & Cron Organ** (supervisor heartbeat — "Autonomous SRE" নয়) |
| M18 | **Telegram Integration Organ** |

## ২. কোড-সত্য রিকনসিলিয়েশন (issue-এর tier order বনাম বাস্তবতা)

Issue #453 Tier-1-এর ১ নম্বরে থাকা **Supreme Teleport-এর কোড ০%** (শুধু plan; acceptance gate
নেই) — অথচ শক্তিশালী ভিত্তি অন্য জায়গায় প্রমাণিত:

- **HITL (M17):** ৩টি টেস্টেড সারফেস, atomic + tamper-proof state machine — সবচেয়ে শক্ত ভিত
- **LLM Gateway core (M03):** ১,৬১৬ LOC প্যাকেজ + ১,০০১ LOC টেস্ট (শুধু accounting contracts নেই)
- **Telegram organ (M18):** fail-closed secret-token webhook মাউন্টেড + টেস্টেড (শুধু `/abort` নেই)
- **Tier-S S1–S12 (M10):** ১২ backend router + migration + ৮ component তৈরি — শুধু অর্ধেক মাউন্টেড
- **Billing spine (M16):** wallet + ledger + idempotent webhook + fail-closed Redis mutex

## ৩. মালিকানা ডি-ডুপ্লিকেশন (এক দাবি, এক মালিক)

| Duplicated scope | Claimed by | Single owner |
| --- | --- | --- |
| Zero-bypass inference CI gate | M03 P0, M11 P-G, M15 P-I, M21 P-I | **M03** (contract) + **M11** (enforcement) |
| CancellationToken / `/abort` | M02, M06, M12, M18, Teleport | **M02** |
| 6x Kaggle canary handover | M03 §2.4.3, M22 P-I | **M03** (M22 only consumes heartbeat) |
| Bengali token estimator | M07 P-E, M19 P-D | **M19** (`bengali_text.py`) |
| tenant_rate_limiter fail-mode | M13, M15, M16 | **M15** (limiter authority), M13 config-izes |

## ৪. ওয়েভ-ভিত্তিক এক্সিকিউশন অর্ডার (benefit-per-effort × dependency)

**Wave 1 — দৃশ্যমান জয় (built-but-unwired জমাগুলো ফেরত চালু):**
- **M10 P-A/P-B (Frontend Tier-S)** ✅ *শুরু হয়েছে (2026-09-18):* ChatInterface host মাউন্ট (`/chat` রুট +
  nav), ভুয়া `"current_conv"` প্লেসহোল্ডার সত্য ক্লায়েন্ট conversation_id দিয়ে প্রতিস্থাপন
  (backend ConversationCommand ক্লায়েন্ট-সরবরাহকৃত id গ্রহণ করে — `gateway_center.py:79`),
  S2 ThinkingPanel + S3 ArtifactsPanel মাউন্ট, `/prompt-library` nav truth, integration-guide
  প্যাথ-সত্য সংশোধন। টেস্ট: ৫টি নতুন চুক্তি-টেস্ট, frontend 532/532।
- **M16 P-A:** gateway বা chat path-এ এক-লাইন `record_spend` ফিড → ড্যাশবোর্ডের চিরস্থায়ী $0 সত্য হয়।
- **M20 P-B:** `/ws/dashboard` subscription-task-এর ২-লাইন বাগ ফিক্স।
- **M22 P-A:** AgentSupervisor heartbeat-এ due-task sweep (S10 store ready, executor নেই)।
- **M18 P-I:** `/abort <run_id>` → runs cancellation path; fake `/telemetry` KPI সরিয়ে লাইভ রিড।

**Wave 2 — ব্যাকবোন (unlocks ~১০ মডিউল):**
- **M03 P0–P2:** InferenceContext চুক্তি, streaming/non-streaming কস্ট-টেলিমেট্রি প্যারিটি,
  tenant/cost enforcement ১৩টি বাইপাস রুট বন্ধ, fabricated model name পরিষ্কার।
- **M02 P-B (ERR-F01):** run-bridge writers production-wired (M05/M06/M17 খুঁজে পাবে)।
- **M23 P-A/P-C:** `POST /api/knowledge/ask`-এর প্রতি-কল 500 বন্ধ (৩-লাইন ফিক্স) + format-adapter
  convoy → ১২১ বাংলা এন্ট্রি retrieval-এ আসে।

**Wave 3 — সত্য-স্তর (cheap governance credibility):**
- **M13 (S):** middleware truth-map, hardcoded limits → config, tenant limiter bounded fail-mode।
- **M14 (S):** ভুয়া STT/TTS success semantics প্রত্যাহার, zero-cost Web Speech first।
- **M05 P-A:** ভুয়া evolution সারফেস পরিষ্কার + apply-executor।

**Wave 4 — ভারী গঠন (তখনই যখন Wave 2-এর ভিত দাঁড়িয়েছে):**
- M01 memory consolidation, M06 ৮/৮ RunType adoption, M07 context budget, M08 SSE চুক্তি ফিক্স,
  M09 ReAct loop, M17 seven→one, M19 language loop, M11 architecture graph।
- **Supreme Teleport:** সর্বশেষ — এটি M18+M17+M06+M04-এর **composition**; আগে ভিতগুলো লাগবে।
  এর প্ল্যানে acceptance gate retrofit করা হয়েছে (এই commit-এ)।

## ৫. বেসলাইন আপডেট (এই ওয়েভ থেকে)

| Gate | আগে | এখন |
| --- | --- | --- |
| frontend vitest | 527 (101 files) | **532 (102 files)** — M10 চুক্তি-টেস্ট যোগ |
| frontend tsc (সঠিক গেট) | — | `tsc -p tsconfig.app.json --noEmit` = 0 errors |

⚠️ **গেট-সত্য সতর্কতা:** root `tsconfig.json` `"files": []` + references — ফলে খালি
`npx tsc --noEmit` **কিছুই চেক করে না**। প্রকৃত গেট: `pnpm typecheck`
(`tsc -p tsconfig.app.json --noEmit`)। CI ও golden loop-এ এটিই ব্যবহার করতে হবে।

## ৬. শৃঙ্খলা

প্রতি ওয়েভ = একাধিক atomic PR; প্রতি PR = এক মডিউলের এক phase (Plan → Code → Test →
Verification → Close Checkbox, issue #453 Rule #2)। ভুয়া "implemented" দাবি নিষিদ্ধ —
checkbox কেবল CI-প্রমাণিত অবস্থায় বন্ধ হবে।
