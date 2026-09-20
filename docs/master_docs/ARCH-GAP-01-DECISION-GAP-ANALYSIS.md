# ARCH-GAP-01 — Architectural Decision Gap Analysis

> **উদ্দেশ্য:** সুপ্রিমএআই-এর মাল্টি-এজেন্ট আর্কিটেকচার, টোকেন কানোনিকালাইজেশন, পিআর হেল্পার লাইফসাইকেল এবং পলিমরফিক ওয়ার্কফোর্স সিদ্ধান্তগুলোতে বিদ্যমান লজিক্যাল গ্যাপ ও অসামঞ্জস্য চিহ্নিত করে ভবিষ্যৎ সংশোধনের জন্য একটি কার্যকর রোডম্যাপ তৈরি করা।  
> **রেফারেন্স ডকুমেন্টস:** OPS-05, OPS-06, OPS-07, OPS-08, AGENTS.md, GITHUB_TOKEN_CANONICALIZATION_PLAN.md  
> **তৈরির তারিখ:** সেপ্টেম্বর ২০২৬

---

## 🔍 গ্যাপ ইনডেক্স (Index of Gaps)

| # | গ্যাপ শিরোনাম | সম্পর্কিত ডকুমেন্ট | তীব্রতা | স্ট্যাটাস |
|---|---|---|---|---|
| GAP-01 | মিউটেক্স লকিং অ্যাটমিক নয় | OPS-06 সেফগার্ড ৩ | 🔴 Critical | ❌ Open |
| GAP-02 | সুপ্রিমএআই নিজের PR-এ Self-Approval কনফ্লিক্ট | OPS-05, OPS-06, OPS-08 | 🔴 Critical | ❌ Open |
| GAP-03 | স্টল্ড এজেন্ট রিকভারি (Orphan Mutex) কোনো Watchdog নেই | OPS-06, OPS-07 | 🟠 High | ❌ Open |
| GAP-04 | শুধুমাত্র একটি শেয়ার্ড `GITHUB_TOKEN` — Rate Limit ঝুঁকি | OPS-07, CANONICALIZATION_PLAN | 🟠 High | ❌ Open |
| GAP-05 | Branch Naming Regex CI-তে অনুপস্থিত | OPS-06 সেফগার্ড ৪ | 🟠 High | ❌ Open |
| GAP-06 | PR Helper নিজেকে নিজে Validate করতে পারে না | OPS-05 | 🟠 High | ❌ Open |
| GAP-07 | SupremeAI-এর Developer/Runtime মোড সুইচে Authorization নেই | OPS-07, OPS-08 | 🟠 High | ❌ Open |
| GAP-08 | পলিমরফিক এজেন্ট স্লট রেজিস্ট্রি নেই | OPS-06, OPS-07 | 🟡 Medium | ❌ Open |
| GAP-09 | OPS-07 শিরোনাম বনাম কনটেন্টে নামের অসামঞ্জস্য | OPS-07 | 🟡 Medium | ❌ Open |
| GAP-10 | HITL SupremeAI-এর নিজস্ব HITL কোড পরিবর্তনে প্রযোজ্য কিনা অস্পষ্ট | OPS-08, AGENTS.md | 🟡 Medium | ❌ Open |
| GAP-11 | OPS-06 এজেন্ট চেকলিস্টে `ruff --fix` Auto-Commit স্টেপ নেই | OPS-06 ধাপ ৩ | 🟡 Medium | ❌ Open |
| GAP-12 | PR Helper Block-এর পরে Re-run Protocol অস্পষ্ট | OPS-05, OPS-06 | 🟡 Medium | ❌ Open |

---

## 🔴 GAP-01 — মিউটেক্স লকিং প্রকৃত অ্যাটমিক নয়

### সমস্যার বিবরণ
OPS-06 সেফগার্ড ৩-এ দাবি করা হয়েছে যে `gh issue edit --add-assignee --add-label` কমান্ড দিয়ে "অ্যাটমিক মিউটেক্স লকিং" সম্পন্ন হয়। কিন্তু এটি **ভুল ধারণা**।

**বাস্তবতা:**
```
1. Agent-1: gh issue list --search "no:assignee" → দেখে Issue #900 খালি ✅
2. Agent-2: gh issue list --search "no:assignee" → একই সময়ে দেখে Issue #900 খালি ✅
3. Agent-1: gh issue edit 900 --add-assignee "agent-1"  ← প্রায় একই সময়ে
4. Agent-2: gh issue edit 900 --add-assignee "agent-2"  ← প্রায় একই সময়ে
5. ফলাফল: Issue #900-এ দুটো assignee → উভয় এজেন্ট একই কাজ শুরু করে 💥
```

GitHub REST API-এর `issue edit` কোনো Compare-and-Swap (CAS) অপারেশন নয়। একটি `assignees` array-তে শুধু append করে — race condition সম্পূর্ণ সম্ভব।

### লজিক্যাল গ্যাপ
- **ডক বলছে:** "অ্যাটমিকভাবে ক্লেইম করবে"
- **বাস্তবে:** কোনো True Atomic Lock নেই, শুধু optimistic assignment আছে।

### সম্ভাব্য ফিক্স
1. **Claim-then-Verify pattern:** `edit` করার পর পুনরায় `gh issue view $ID --json assignees` চালিয়ে নিজের নাম আছে কিনা ভেরিফাই করা।
2. **টাইমস্ট্যাম্প-ভিত্তিক লীডার ইলেকশন:** গিটহাব ইস্যু কমেন্টে `agent-X: claiming at <timestamp>` লিখে তারপর assignee চেক করা।

---

## 🔴 GAP-02 — SupremeAI নিজের PR-এ Self-Approval কনফ্লিক্ট

### সমস্যার বিবরণ
OPS-05 এ স্পষ্টভাবে লেখা আছে:
> *"Self-Approval Guard: নিজের PR নিজে approve করা GitHub-এ নিষিদ্ধ — সেক্ষেত্রে approve/auto-merge skip (notice সহ)।"*

কিন্তু OPS-08 সেকশন ৫-এ বলা হয়েছে SupremeAI নিজেই `agent-X` হিসেবে PR সাবমিট করতে পারবে।

**কনফ্লিক্ট:**
- PR Author: `supremeai` (agent-X হিসেবে)
- PR Reviewer/Approver: PR Helper → যে একই `GITHUB_TOKEN` ব্যবহার করে (`SaifulHaqueNiloy` অ্যাকাউন্ট)
- **সমস্যা:** SupremeAI-এর PR গিটহাব একই token দিয়ে approve করার চেষ্টা করবে → Self-approval block → **PR কখনো auto-merge হবে না!**

### লজিক্যাল গ্যাপ
- OPS-05: Self-approval নিষিদ্ধ।
- OPS-06/08: SupremeAI agent হিসেবে PR সাবমিট করতে পারে।
- এই দুটো একসাথে সত্য হতে পারে না যদি একই `GITHUB_TOKEN` ব্যবহার হয়।

### সম্ভাব্য ফিক্স
1. **Bot Account Strategy:** SupremeAI-এর জন্য আলাদা GitHub Bot Account তৈরি করে তার নামে PR সাবমিট করা, যাতে মূল `SaifulHaqueNiloy` টোকেন দিয়ে PR Helper আলাদাভাবে approve করতে পারে।
2. **Human Review Mandate:** SupremeAI-এর PR-এ সর্বদা Human reviewer (maintainer) প্রয়োজন — Auto-merge বন্ধ, শুধু classification comment রাখা।
3. **Explicit Policy Clarification:** SupremeAI self-approval conflict হলে Maintainer notification পাঠানো এবং manual review প্রয়োজন বলে ডকুমেন্ট করা।

---

## 🟠 GAP-03 — Stalled Agent Orphan Mutex (কোনো Watchdog নেই)

### সমস্যার বিবরণ
OPS-06 এ বলা হয়েছে কাজ অসমাপ্ত রেখে চলে গেলে এজেন্ট `status:in-progress` লেবেল সরাবে। কিন্তু **কোনো এনফোর্সমেন্ট মেকানিজম নেই।**

**বাস্তব সিনারিও:**
- Agent-1 Issue #850 ক্লেইম করে `status:in-progress` লেবেল লাগায়।
- Agent-1-এর সেশন ক্র্যাশ হয় অথবা নেটওয়ার্ক ত্রুটিতে সংযোগ বিচ্ছিন্ন হয়।
- Issue #850 চিরকালের জন্য `status:in-progress` হয়ে থাকে।
- নতুন কোনো Agent ওই ইস্যু ধরতে পারে না।
- **ব্যাকলগ অচল হয়ে যায়।**

### লজিক্যাল গ্যাপ
- ডকুমেন্টে "কাজ না করলে লেবেল সরাবে" একটি সদিচ্ছার নিয়ম, কিন্তু এটি ক্র্যাশড এজেন্টের ক্ষেত্রে কাজ করে না।
- কোনো টাইমআউট, watchdog, বা orphan detection mechanism নেই।

### সম্ভাব্য ফিক্স
1. **GitHub Actions Scheduled Cleanup:** একটি ক্রন জব (`stale-mutex-cleanup.yml`) যা প্রতি রাতে `status:in-progress` থাকা ইস্যু কিন্তু সাথে কোনো ওপেন PR নেই এমন ইস্যু থেকে লেবেল সরিয়ে দেবে।
2. **Claim Timeout Policy:** ইস্যু ক্লেইমের পর N ঘণ্টার (যেমন ২৪ ঘণ্টা) মধ্যে PR না আসলে লক স্বয়ংক্রিয়ভাবে মুক্ত।

---

## 🟠 GAP-04 — একক শেয়ার্ড GITHUB_TOKEN-এ Rate Limit ঝুঁকি

### সমস্যার বিবরণ
GITHUB_TOKEN Canonicalization-এ সব Agent, PR Helper, CI Script — সবাই একই `GITHUB_TOKEN` ব্যবহার করে। GitHub Fine-Grained PAT-এর রেট লিমিট: **৫,০০০ রিকোয়েস্ট/ঘণ্টা**।

**বাস্তব চাপের হিসাব:**
```
Agent-1: gh issue edit + git push + gh pr create        ≈ 10 API calls
Agent-2: gh issue edit + git push + gh pr create        ≈ 10 API calls  
Agent-3: gh issue edit + git push + gh pr create        ≈ 10 API calls
PR Helper (per PR): 20+ API calls (labels, comments, review, merge)
CI Workflows: 50+ API calls per run
─────────────────────────────────────────────────────────────
5 concurrent agents + 5 PRs + CI = ~200-300 API calls/cycle
```

ব্যাকলগ ক্লিয়ারের সময় সমান্তরাল অনেক Agent চলতে থাকলে Rate Limit হিট হওয়ার সম্ভাবনা আছে।

### লজিক্যাল গ্যাপ
- একক টোকেনের সুবিধা (Simple Rotation) এবং Rate Limit ঝুঁকির মধ্যে কোনো পলিসি নেই।
- কতজন Agent একই সময়ে সক্রিয় থাকতে পারে তার কোনো সর্বোচ্চ সীমা নির্ধারণ করা হয়নি।

### সম্ভাব্য ফিক্স
1. **Max Concurrent Agent Policy:** একসাথে সর্বোচ্চ N জন সক্রিয় Agent সীমা নির্ধারণ করা (যেমন: Max 5)।
2. **Rate Limit Monitoring:** CI-তে `x-ratelimit-remaining` হেডার চেক করে ৫০০-এর নিচে গেলে সতর্কতা পাঠানো।

---

## 🟠 GAP-05 — Branch Naming Regex CI Workflow-এ নেই

### সমস্যার বিবরণ
OPS-06 সেফগার্ড ৪-এ একটি Bash regex validation script দেওয়া আছে:
```bash
VALID_PATTERN="^(agent-[0-9]+\/issue-[0-9]+-.+|feat\/|fix\/|hotfix\/|perf\/|chore\/)"
```

কিন্তু এই স্ক্রিপ্টটি কোনো CI workflow file-এ (`ci.yml`, `pr-helper.yml`, বা আলাদা `branch-guard.yml`) সংযুক্ত নেই।

### লজিক্যাল গ্যাপ
- নিয়ম আছে কিন্তু এনফোর্সমেন্ট নেই।
- যেকেউ যেকোনো নামে ব্রাঞ্চ তৈরি করে PR দিতে পারবে এবং CI তাতে আপত্তি করবে না।

### সম্ভাব্য ফিক্স
1. **[NEW]** `.github/workflows/branch-naming-guard.yml` তৈরি করা যা PR `opened` ইভেন্টে ব্রাঞ্চ নাম regex চেক করবে।
2. **branch protection rules-এ** GitHub Repository Settings থেকে ব্রাঞ্চ নামের regex pattern enforce করা।

---

## 🟠 GAP-06 — PR Helper নিজেকে নিজে Validate করতে পারে না

### সমস্যার বিবরণ
OPS-05 এ বলা হয়েছে PR Helper `base_sha`-এর স্ক্রিপ্ট ব্যবহার করে নিরাপত্তা নিশ্চিত করে। কিন্তু যদি **PR Helper-কেই পরিবর্তন করার PR** আসে তাহলে:

```
PR #999: ".github/workflows/pr-helper.yml" পরিবর্তন করছে

PR Helper চলছে → base_sha (main) থেকে pr-helper.yml লোড করছে
                → সেই পুরনো pr-helper.yml দিয়ে নতুন pr-helper.yml-এর পরিবর্তন evaluate করছে
                → পুরনো লজিক দিয়ে নতুন লজিক judge করছে
```

এটি **Bootstrap Problem** — PR Helper নিজের evolution-কে সঠিকভাবে evaluate করতে পারে না।

### লজিক্যাল গ্যাপ
- `pr-helper.yml`, `delta_analysis.py`, বা `hunk_isolation.py` পরিবর্তনকারী PR-কে সাধারণ PR-এর মতো evaluate করা উচিত হবে না।
- এই ধরনের PR-এ Auto-merge অনুমতি দেওয়া নিরাপদ নয়।

### সম্ভাব্য ফিক্স
1. **Special Guard:** `.github/workflows/pr-helper.yml` বা `.github/scripts/pr_helper/` পরিবর্তনকারী PR detect করলে Auto-merge bypass করে **mandatory human review** enforce করা।
2. **PR Helper self-modification label:** `pr-helper:self-modification` লেবেল দিয়ে Maintainer-এ নোটিফিকেশন পাঠানো।

---

## 🟠 GAP-07 — SupremeAI Runtime→Developer মোড সুইচে কোনো Authorization নেই

### সমস্যার বিবরণ
OPS-08 সেকশন ৫-এ বলা হয়েছে SupremeAI "মেইনটেইনার দ্বারা অ্যাসাইন হলে" Developer Mode-এ প্রবেশ করে। কিন্তু:

1. **কীভাবে trigger হয়?** কোনো API endpoint নেই, কোনো GitHub label নেই, কোনো Infisical flag নেই।
2. **কে authorize করতে পারবে?** যেকোনো ব্যবহারকারী চ্যাটে "SupremeAI, fix issue #900" বলে দিলেই কি Developer mode শুরু হবে?
3. **Audit trail কোথায়?** SupremeAI কখন, কার নির্দেশে, কোন Issue ধরেছিল তার log নেই।

### লজিক্যাল গ্যাপ
- "ইউজার অ্যাসাইন করবেন" — এই প্রক্রিয়াটি সম্পূর্ণ অনির্দিষ্ট।
- SupremeAI নিজে GitHub Actions trigger করার টেকনিক্যাল পথ নথিবদ্ধ নেই।

### সম্ভাব্য ফিক্স
1. **Explicit Trigger Mechanism:** Admin dashboard-এ একটি বোতাম অথবা `gh workflow dispatch` command দিয়ে SupremeAI developer mode শুরু হবে।
2. **Audit Log:** SupremeAI যখন Developer mode-এ প্রবেশ করে তখন Infisical-এ বা GitHub Issue-এ `supremeai:developer-mode-activated` লেবেল দিয়ে Maintainer-কে নোটিফাই করা।
3. **Authorization Scope:** শুধুমাত্র `admin` বা `maintain` পারমিশনের ইউজার SupremeAI-কে Developer Mode-এ সুইচ করাতে পারবেন।

---

## 🟡 GAP-08 — Polymorphic Agent Slot Registry নেই

### সমস্যার বিবরণ
OPS-06 বলছে `agent-1=Antigravity, agent-2=Claude, agent-10=SupremeAI` — কিন্তু এই ম্যাপিং কোথাও formally রেকর্ড করা হয়নি।

**ব্যবহারিক সমস্যা:**
- PR হিস্টোরিতে শুধু `agent-10` দেখা যাবে — এটি কোন সেশনে SupremeAI ছিল, কোন সেশনে Cursor ছিল তা বোঝার কোনো উপায় নেই।
- একই সময়ে দুজন ভিন্ন maintainer দুটি ভিন্ন টুলকে `agent-1` হিসেবে অ্যাসাইন করতে পারেন — কোনো conflict prevention নেই।

### সম্ভাব্য ফিক্স
1. **[NEW]** `docs/ops/AGENT_SLOT_REGISTRY.yaml` — কে কোন স্লট, কতদিনের জন্য, কোন maintainer অ্যাসাইন করেছেন তার living record।
2. GitHub Issue label: `agent-slot:X=<tool-name>` ফরম্যাটে tag করা যাতে PR history searchable থাকে।

---

## 🟡 GAP-09 — OPS-07 শিরোনাম বনাম কনটেন্টে Naming Inconsistency

### সমস্যার বিবরণ
OPS-07-এর শিরোনাম: **"External AI Developer Lifecycle"**

কিন্তু সেকশন ১-এ নিজেই লেখা হয়েছে:
> *"এই পুলের যেকোনো স্লট... বাহ্যিক কোনো এআই অথবা **স্বয়ং সুপ্রিমএআই (SupremeAI Himself)** হতে পারে।"*

SupremeAI কিন্তু "External" নয় — সে এই প্ল্যাটফর্মের নিজস্ব সত্তা। তাহলে শিরোনামে "External" লেখা misleading।

### সম্ভাব্য ফিক্স
OPS-07-এর শিরোনাম পরিবর্তন করে রাখা:  
`OPS-07 — Developer Agent Lifecycle (Engineering & Contribution Protocol)`  
(External শব্দটি সরিয়ে দেওয়া।)

---

## 🟡 GAP-10 — SupremeAI নিজের HITL কোড পরিবর্তন করতে পারে কিনা অস্পষ্ট

### সমস্যার বিবরণ
OPS-08 সেকশন ৫-এ বলা হয়েছে SupremeAI Developer Mode-এ যেকোনো ইস্যু ধরে কোড ফিক্স করতে পারে। কিন্তু যদি SupremeAI কোনো ইস্যু নেয় যা **HITL লজিক (`services/hitl/`)** পরিবর্তন করে?

**নিরাপত্তা ঝুঁকি:**
- SupremeAI HITL লজিক modify করতে পারলে সে নিজের উপর মানব-নিয়ন্ত্রণ হ্রাস করতে পারে।
- HITL bypass করার সম্ভাবনা তৈরি হয় (non-intentional but possible).

### লজিক্যাল গ্যাপ
- "যেকোনো ইস্যু" — HITL/security core কোড কি এই "যেকোনো"-র মধ্যে পড়বে?

### সম্ভাব্য ফিক্স
1. **Protected Scope Definition:** কিছু নির্দিষ্ট পাথ (`services/hitl/`, `services/security/`, `core/auth/`) SupremeAI Developer Mode-এর বাইরে — এই পাথগুলো শুধুমাত্র Human review দিয়ে মার্জ হবে।
2. **CODEOWNERS:** `.github/CODEOWNERS` ফাইলে এই critical paths-এ mandatory human reviewer যোগ করা।

---

## 🟡 GAP-11 — OPS-06 Agent Checklist-এ Auto-Remediation Step নেই

### সমস্যার বিবরণ
OPS-06 ধাপ ৩-এ বলা হয়েছে "কোড পরিবর্তন ও লোকাল প্রি-ফ্লাইট টেস্ট"। কিন্তু `AGENTS.md` Directive 10 বলছে:
> *"যা কিছু অটো-ফিক্সযোগ্য (`ruff --fix`, `eslint --fix`, `docgen`) তা আগে নিজে ঠিক হবে।"*

**সমস্যা:** ধাপ ৩-এ `ruff check --fix` এবং `eslint --fix` চালানো Checklist-এ উল্লেখ নেই, শুধু `ruff check` আছে।

### সম্ভাব্য ফিক্স
OPS-06 ধাপ ৩-এ Checklist update করে:
```bash
ruff check --fix backend/  # Auto-remediate first (Directive 10)
ruff check backend/         # Confirm zero remaining errors
pytest ...
```

---

## 🟡 GAP-12 — PR Helper Block-এর পরে Re-run Protocol অস্পষ্ট

### সমস্যার বিবরণ
OPS-05-এ বলা হয়েছে regression হলে PR Helper `pr-helper:blocked` লেবেল দেয় এবং Issue তৈরি করে। কিন্তু এরপরে Agent কী করবে?

**অস্পষ্ট প্রশ্নসমূহ:**
1. Agent কি সেই ব্রাঞ্চেই নতুন কমিট পুশ করবে? 
2. নাকি পুরো ব্রাঞ্চ delete করে নতুন branch তৈরি করবে?
3. PR Helper কি নতুন কমিট আসলে স্বয়ংক্রিয়ভাবে re-run হয়? (Synchronize ইভেন্ট — হ্যাঁ, হওয়ার কথা, কিন্তু ডকে স্পষ্ট নেই।)
4. Blocked PR-এ নতুন কমিটের পর আগের `pr-helper:blocked` লেবেল কি সরানো হয়?

### সম্ভাব্য ফিক্স
OPS-05 বা OPS-06-এ একটি explicit "After Block Recovery Protocol" যোগ করা।

---

## 📊 সারসংক্ষেপ ও অগ্রাধিকার তালিকা (Priority Matrix)

```
IMPACT
  ↑
  │  GAP-02 (Self-Approval)          GAP-01 (False Mutex)
  │  GAP-07 (Mode Switch Auth)       GAP-03 (Orphan Lock)
  │  GAP-10 (HITL Self-Modify)
  │
  │  GAP-04 (Rate Limit)             GAP-05 (Branch Guard CI)
  │  GAP-06 (PR Helper Bootstrap)
  │
  │  GAP-08 (Slot Registry)          GAP-11 (AutoFix Step)
  │  GAP-09 (Naming)                 GAP-12 (Block Recovery)
  └─────────────────────────────────────────────────→ EASE OF FIX
      Hard                                            Easy
```

### তাৎক্ষণিক ফিক্স করার পরামর্শ (Low Effort, High Value)
1. **GAP-05:** Branch naming regex CI workflow তৈরি করা — ১-২ ঘণ্টার কাজ।
2. **GAP-09:** OPS-07 শিরোনাম পরিবর্তন — ৫ মিনিটের কাজ।
3. **GAP-11:** OPS-06 Checklist-এ `ruff --fix` ধাপ যোগ করা — ১০ মিনিটের কাজ।

### মাঝারি মেয়াদে ফিক্স করার পরামর্শ (Medium Effort)
4. **GAP-03:** Stale mutex cleanup cron job তৈরি করা।
5. **GAP-08:** Agent Slot Registry YAML তৈরি করা।
6. **GAP-10:** `.github/CODEOWNERS` ফাইলে critical path অ্যাড করা।

### দীর্ঘমেয়াদী আর্কিটেকচারাল সংশোধন (High Effort)
7. **GAP-01:** True atomic mutex mechanism (Claim-then-Verify pattern)।
8. **GAP-02:** SupremeAI bot account বা mandatory human review policy।
9. **GAP-06:** PR Helper self-modification guard।
10. **GAP-07:** SupremeAI Developer Mode authorization framework।

---

*ডকুমেন্ট আইডি: ARCH-GAP-01 · সুপ্রিমএআই কোর আর্কিটেকচার টিম · সেপ্টেম্বর ২০২৬*  
*সকল গ্যাপ চিহ্নিত হলে এই ডকুমেন্টের স্ট্যাটাস কলাম আপডেট করুন।*
