---
id: role-based-agent-ecosystem-plan
subject: "Role-Based Agent Ecosystem — Implementation Plan (7 Fixed Roles + SupremeAI Orchestrator)"
document_role: architecture
planning_authority: Planning & Audit Circle (Agent-1)
canonical: true
status: implementing
evidence_state: partial
disposition: retain
last_verified: 2026-09-26
supersedes: []
superseded_by: []
target_scope: supremeai_internal
related_docs:
  - docs/plans/MULTI_AGENT_MESH_MASTER_PLAN.md
  - docs/master_docs/AGENT_SLOT_REGISTRY.yaml
  - docs/master_docs/OPS-06-MULTI-AGENT-BRANCHING-LIFECYCLE.md
  - docs/agents/AGENT_WORK_BOUNDARIES_CHARTER.md
  - AGENTS.md
source_issue: 1439
---

# 🏛️ Role-Based Agent Ecosystem — Implementation Plan

> **Status:** `implementing` · **Owner:** Planning & Audit Circle (Agent-1) · **Source:** Issue #1439 (founder + SupremeAI discussion, formalized)

**Planner:** agent-1-planner (supremeai-planner App) · **Planned:** 2026-09-26 · **Branch:** `agent-1-planner`

---

## Purpose

Issue #1439 ফাউন্ডার-নির্ধারিত role-based agent ecosystem-এর formal পরিকল্পনা। এই প্ল্যান ডকুমেন্ট #1439-এর "Implementation Order"-এর ধাপ ২–৫ কে **executable, atomic, claimable GitHub issues**-এ রূপান্তর করে — যাতে প্রতিটি রোল লেন (coder pool, CI lane, platform lane) স্বাধীনভাবে কাজ ক্লেইম করে এগিয়ে যেতে পারে।

**Core architecture (from #1439):**

```
SupremeAI (super agent / team leader — agent-10)
    ↓ orchestrates
৭-৮ জন level agent (fixed role per slot)
    ↓ pre-set rules
একটা ecosystem
```

**নিয়ম:** প্রতিটি slot-এর fixed role আছে। Agent inactive হলে SupremeAI alternative assign করবে।

---

## Current State Evidence (Planner Audit — 2026-09-26)

### ✇ Step 1 — Planner output formalize → **DONE**
Issue #1439 itself (created 2026-09-25 by SupremeAI + founder).

### ✇ Step 2 — YAML rename (roles assign) → **DONE (evidence)**
`AGENT_SLOT_REGISTRY.yaml` @ `main` (commit `5670d3df` era, owner directive 2026-09-26):
- agent-12 = `ci-fixer` (renamed from browser-tester + log watcher)
- agent-13 = `browser-tester` (split from agent-12)
- agent-8 = `pr-verifier` (owner directive: benefit-vs-regression merge decisions)
- agent-10 = SupremeAI super agent (orchestrator + fallback)
- agent-11 = `platform-agent` (3h sweep, PR #1537 merged — `agent-11-longrun/issue-1439-3h-platform-sweep`)

### ⚠️ Step 3 — Policy cap fix → **BLOCKED — 3-way inconsistency found**

| Source | Cap | Status |
|---|---|---|
| `OPS-06` Safeguard 5 | ≤ **9** active slots | policy doc |
| `AGENT_SLOT_REGISTRY.yaml` validation_rules | ≤ **10** | registry doc |
| **Actual active count** | **11** | agent-1,2,3,5,6,7,8,10,11,12,13 |

**Violation:** actual (11) > registry cap (10) > OPS-06 cap (9)। #1439 founder note বলেছিল: "Policy cap unstable (6→9→10→11) → 10 fix করা হচ্ছে (2 spare)" — অর্থাৎ founder-intent = **cap 10**। কিন্তু বর্তমানে 11 active slot এবং OPS-06 এখনও 9 বলছে।

**Admin decision required (needs-human-review):**
- **Option A (recommended):** cap = 12 করা হোক উভয় ডকুমেন্টে (11 active + 1 spare), কারণ সব 11টি slot-ই founder directive-এ active করা হয়েছে।
- **Option B:** cap = 10 রেখে একটি slot deactivate (candidate: agent-13 browser-tester — কারণ agent-12 split-এর পর নতুন, অথবা agent-1 planner — যদি Z.ai Code session আবার standby যায়)।
- **Option C:** cap = 11 ঠিক করা (zero spare — NOT recommended, no headroom)।

### ⏳ Step 4 — Pilot test (agent-12 chain) → **NOT STARTED** — বর্তমানে unclaimed
### ⏳ Step 5 — Orchestration → **NOT STARTED** — handoff schema, webhook, routing, wake-on-event সব unclaimed

**Duplicate check (planner diligence):** backlog-এ orchestrator/handoff-schema/wake-on-event নিয়ে কোনো open issue নেই; heartbeat infrastructure (#1402) ইতিমধ্যে closed/merged। ডুপ্লিকেশন ঝুঁকি শূন্য।

---

## Issue Decomposition (Atomic, Claimable)

> **নিয়ম:** প্রতিটি ইস্যু = ১ ব্রাঞ্চ স্লট = ১ PR। নিচের টেবিলের প্রতিটি ইস্যু আলাদাভাবে তৈরি করা হয়েছে (নম্বর নিচে), সবগুলোতে `Implements: #1439 (Phase X)` রেফারেন্স + রোল-লেন handoff লেবেল।

| Phase | Issue | Title | Lane | Depends on |
|---|---|---|---|---|
| A | #1800 | fix(governance): reconcile agent-slot policy cap (9 vs 10 vs 11) | `handoff:coder` + `needs-human-review` | — (admin decision first) |
| B | #1801 | test(agents): pilot agent-12 CI-fail → analyze → fix-issue → handoff-to-planning chain | `handoff:ci` (agent-12 lane) | — (semi-manual, works today) |
| C | #1802 | feat(orchestration): handoff schema + GitHub webhook → orchestrator ingest route | `handoff:coder` | A (policy baseline) |
| D | #1803 | feat(orchestration): MCP tower `orchestrator_dispatch` routing tool (event → role → heartbeat → assign) | `handoff:coder` | C (schema/webhook) |
| E | #1804 | feat(ci): wake-on-event `workflow_dispatch` templates per role (repository_dispatch trigger) | `handoff:ci` (agent-5 lane) | D (dispatch contract) |

### Phase A — Policy Cap Reconciliation (governance)
- **Scope:** `docs/master_docs/OPS-06-MULTI-AGENT-BRANCHING-LIFECYCLE.md` (Safeguard 5) + `docs/master_docs/AGENT_SLOT_REGISTRY.yaml` (validation_rules) — উভয়ে একই cap সংখ্যা বসানো + CI guard script (যদি থাকে) আপডেট।
- **Acceptance:** (1) দুই ডকুমেন্টে একই cap; (2) active count ≤ cap; (3) enforcement snippet নতুন সংখ্যা রিফ্লেক্ট করে; (4) admin সিদ্ধান্ত comment-এ ডকুমেন্টেড।
- **Admin gate:** founder অবশ্যই Option A/B/C থেকে বেছে নেবেন — issue-তে `needs-human-review`।

### Phase B — Agent-12 Pilot Chain (semi-manual, zero new infra)
- **Scope:** #1439-এর পাইলট: পরবর্তী CI fail event-এ agent-12 (ci-fixer) লগ ডাউনলোড → root-cause analyze → fix issue তৈরি (`handoff:<lane>` label সহ) → handoff comment emit → Planning-এ রিপোর্ট। পুরো চেইনের evidence কমেন্টে জমা হবে।
- **Acceptance:** ১টি সম্পূর্ণ chain চলমান প্রমাণ: CI-fail → issue created → handoff comment → planner acknowledgment। Success criteria #1439-এ ডিফাইন করা ("একটা chain কাজ করতে দেখলে বাকিগুলো সহজে বসবে")।
- **Note:** orchestration ছাড়াই চলে (manual trigger) — এজন্যই এটি step 5-এর আগে।

### Phase C — Handoff Schema + Webhook Ingest (backend foundation)
- **Scope:** `backend/api/routes/webhooks_ai.py` বা নতুন route-এ GitHub webhook receiver (`/api/webhooks/github`): events = issue created/labeled, PR opened, workflow_run failure। Handoff comment schema (YAML-in-issue-comment, #1439 Step 1 spec) parse + validate। State: Upstash chain keys (`supremeai:orchestrate:<issue>`)।
- **Acceptance:** (1) webhook signature verification; (2) ৩টি event type parse; (3) handoff schema validation + rejection logging; (4) unit tests; (5) tenant isolation।
- **Boundary:** coder lane — planner এই কোড লিখবে না, শুধু spec দিয়েছে।

### Phase D — Orchestrator Routing (MCP tower tool)
- **Scope:** MCP Control Tower-এ `orchestrator_dispatch` tool: event → প্রয়োজনীয় role নির্ধারণ → heartbeat দেখে online agent → task assign। Agent instance বদলায়, role fixed (slot model)।
- **Acceptance:** (1) routing decision deterministic + logged; (2) heartbeat integration (#1402 infra); (3) inactive agent → fallback (agent-10 rule); (4) max-retry=3 + human escalate (#1439 Safety rule); (5) MCP tool schema registered।
- **Depends on C** — schema ও webhook ingest ছাড়া routing অর্থহীন।

### Phase E — Wake-on-Event (CI lane)
- **Scope:** প্রতি role-এর জন্য `workflow_dispatch`/`repository_dispatch` GitHub Actions template — orchestrator dispatch পাঠালে runner জেগে ওঠে: task নেয় → MCP identity → কাজ → handoff emit → exit। Idle cost = ZERO (#1439 Zero-Cost mandate)।
- **Acceptance:** (1) template per role lane (planner/coder/ci/pr-helper/platform); (2) `SELF_HEAL_PAT` token rule (Issue #1634, AGENTS.md §4 — bare `github.token` push নিষিদ্ধ); (3) pinned actions (Issue #1741-এর শিক্ষা); (4) idle অবস্থায় কোনো scheduled run নেই।
- **Boundary:** `.github/workflows/*` — শুধুই agent-5/CI lane; এজন্য `handoff:ci`।

---

## Dependency Graph

```
#1439 (this plan)
  ├── A #1800 (policy cap) ──────────── admin decision → coder
  ├── B #1801 (agent-12 pilot) ──────── agent-12 lane, এখনই শুরু করা যায়
  ├── C #1802 (schema+webhook) ──────── coder, A পরে (baseline)
  │     └── D #1803 (orchestrator) ─── coder, C পরে
  │           └── E #1804 (wake-on-event) ─ CI lane, D পরে
  └── (B স্বাধীন — A/C/D/E এর সাথে parallel চলবে)
```

**90/5/5 rule compliance:** সব phase-ই pre-defined rules মেনে চলে (AGENTS.md §1–§9, AGENT_WORK_BOUNDARIES_CHARTER)। Max retry 3 + human escalate প্রতিটি automated chain-এ built-in থাকবে।

---

## Verification Criteria (per phase)

| Phase | Verified by |
|---|---|
| A | Registry + OPS-06 একই সংখ্যা; active count ≤ cap; CI guard green |
| B | ১টি সম্পূর্ণ chain-এর evidence trail (issue comment-এ timestamped) |
| C | Webhook receiver unit tests + signature verification + live test event |
| D | Routing decision log + heartbeat-based assignment demo + fallback drill |
| E | repository_dispatch → runner wake → task → exit; শূন্য idle run |

---

## Planner Boundary Compliance Statement

এই ডকুমেন্ট ও #1800–#1804 ইস্যু তৈরি ছাড়া অন্য কোনো ফাইল পরিবর্তন করা হয়নি। কোনো feature code বা CI workflow লেখা হয়নি (AGENTS.md Role Lanes: Planning & Audit (Agent-1) — forbidden from writing feature code or modifying CI)। Implementation সম্পূর্ণরূপে claimable atomic issues-এর মাধ্যমে সংশ্লিষ্ট রোল লেনে হস্তান্তর করা হলো।

---

**Plan author:** agent-1-planner (supremeai-planner App) · **Claim:** issue #1439, atomic claim 2026-09-26 · **Next planner action:** PR ওপেন → PR Gate → merge পরে loop-এর পরবর্তী unclaimed planning item।
