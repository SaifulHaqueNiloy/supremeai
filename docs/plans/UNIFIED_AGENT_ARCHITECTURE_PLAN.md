# SupremeAI — একক এজেন্ট আর্কিটেকচার প্ল্যান (Unified Agent Architecture)

> **তারিখ**: ২০২৮-০৯-২৮
> **মূল ধারণা**: মাল্টি-টাইপ এজেন্ট (coder/ci/planner/pr-helper/browser/platform/super) বাদ দিয়ে একক এজেন্ট টাইপ — সব এজেন্ট একই AGENTS.md ফলো করবে, আর একটি স্ক্রিপ্ট বলে দেবে কে কী কাজ করবে।

---

## ১. বর্তমান সমস্যা (কেন পরিবর্তন দরকার)

### বর্তমান মডেল: ৭টি এজেন্ট টাইপ

```
coder    → শুধু কোড লেখে, PR মার্জ করতে পারে না
ci       → শুধু CI ঠিক করে, কোড লেখে না
planner  → শুধু issue তৈরি করে, PR খুলতে পারে না
pr-helper → শুধু PR রিভিউ ও মার্জ করে
browser  → শুধু ব্রাউজারে কাজ করে
platform → শুধু ইনফ্রা দেখে
super    → সব করতে পারে (কিন্তু তখন আর নিয়ম থাকে না)
```

### সমস্যাগুলো:

| # | সমস্যা | প্রভাব |
|---|--------|-------|
| ১ | **সাইলো ইফেক্ট** — coder আইডল থাকলেও CI-এর কাজ করতে পারে না | এজেন্ট নষ্ট হয় |
| ২ | **৭টি slot pool** ম্যানেজ করা জটিল | coder-1, ci-1, planner-1... কনফিউশন |
| ৩ | **handoff লেবেল সাইলো** — `handoff:coder` issue একমাত্র coder নিতে পারে | কাজ আটকে থাকে |
| ৪ | **৭টি রুল সেট** — প্রতিটি lane-এর আলাদা নিয়ম | রক্ষণাবেক্ষণ কঠিন |
| ৫ | **planner PR খুলতে পারে না** — শুধু issue আউটপুট | অপ্রয়োজনীয় সীমাবদ্ধতা |
| ৬ | **প্রতিটি lane-এ আলাদা role card, charter, boundary** | ৪৮,৬০০ লাইন গভর্নেন্স |
| ৭ | **cross-lane coordination জটিল** — planner বলে কী করতে, coder করে | এক ধাপ বেশি |
| ৮ | **যখন এক lane ব্যস্ত, অন্য lane আইডল** | রিসোর্স নষ্ট |

---

## ২. প্রস্তাবিত মডেল: একক এজেন্ট (Unified Agent)

### মূল ধারণা

```
┌─────────────────────────────────────────────────┐
│              AGENTS.md (সরল, ~৫০ লাইন)            │
│  ১. সবসময় script রান করো প্রথমে                    │
│  ২. script যা বলবে তাই করো                          │
│  ৩. ৩-স্তর যাচাই করো                                 │
│  ৪. queue:hold দাও                                   │
│  ৫. বাংলায় কথা বলো                                   │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│         supremeai_orchestrator.py                  │
│  (এটাই আসল "মস্তিষ্ক" — script এটা চালায়)          │
│                                                    │
│  ১. কোডবেস অডিট করো (প্রতি রানে)                    │
│  ২. কী কাজ দরকার তা চিন্তা করো                       │
│  ৩. প্রায়োরিটি করো                                  │
│  ৪. এই এজেন্টকে কী করতে বলছে সেটা আউটপুট দাও          │
│  ৫. verify করো আগের কাজ সম্পন্ন হয়েছে কি না          │
└───────────────────┬─────────────────────────────┘
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Agent 1 │ │ Agent 2 │ │ Agent 3 │
    │ (একই    │ │ (একই    │ │ (একই    │
    │  টাইপ)  │ │  টাইপ)  │ │  টাইপ)  │
    └─────────┘ └─────────┘ └─────────┘
```

### কীভাবে কাজ করবে:

**ধাপ ১: এজেন্ট সেশন শুরু → script রান**
```bash
python scripts/agents/supremeai_orchestrator.py --slot agent-1
```

**ধাপ ২: script অডিট করে এবং কাজ বরাদ্ধ করে**

script আউটপুট (প্রথম বার):
```
🔍 কোডবেস অডিট চলছে...
📊 পাওয়া গেছে: ২৯০টি dead file, ৪টি circular import, ১৯টি broken API

📝 আপনার কাজ: FIX
   Issue: #2480 (290 dead files)
   কাজ: প্রথম ৫টি dead file delete করো (3-tier verify সহ)
   Branch: agent-1-2480-dead-files-batch-1
   Files: backend/core/competitive_kit.py, ...
```

script আউটপুট (অন্য বার):
```
📝 আপনার কাজ: REVIEW
   PR: #2338 (fix(webhooks): #2205)
   কাজ: 4-Pillar Rubric দিয়ে review করো
   যদি ✅ হয়: gh pr review --approve
   যদি ❌ হয়: gh pr review --comment -b 'findings'
```

script আউটপুট (আরেক বার):
```
📝 আপনার কাজ: MERGE
   গ্রুপ: step-2 সম্পূর্ণ (সব PR green, closeout audit done)
   কাজ: Merge Train চালাও
   gh pr merge --squash
```

---

## ৩. script-এর কাজের তালিকা (Orchestrator Logic)

script প্রতি রানে এই সিদ্ধান্তগুলো নেয়:

### ক. অডিট মোড (প্রতি N ঘণ্টা বা প্রথম রানে)

```python
def audit_codebase():
    """কোডবেসের বর্তমান অবস্থা যাচাই করো"""
    findings = {
        "dead_files": scan_dead_imports(),
        "broken_apis": check_frontend_backend_contracts(),
        "circular_imports": detect_circular_deps(),
        "stale_prs": check_stale_prs(),
        "red_ci": check_main_ci_status(),
        "open_issues": fetch_unclaimed_issues(),
        "unreviewed_prs": fetch_open_prs_without_review(),
    }
    return findings
```

### খ. কাজ বরাদ্ধকরণ মোড (প্রতি রানে)

```python
def assign_work(agent_slot, audit_findings):
    """এই এজেন্টকে কী কাজ দেওয়া হবে তা ঠিক করো"""

    # প্রায়োরিটি ১: main লাল হলে ঠিক করো
    if audit_findings["red_ci"]:
        return {"task": "FIX_RED_MAIN", "details": ...}

    # প্রায়োরিটি ২: unreviewed PR থাকলে review করো
    if audit_findings["unreviewed_prs"]:
        return {"task": "REVIEW_PR", "pr": oldest_unreviewed_pr}

    # প্রায়োরিটি ৩: গ্রুপ সম্পূর্ণ হলে merge করো
    if group_ready_for_merge():
        return {"task": "MERGE_GROUP", "group": ...}

    # প্রায়োরিটি ৪: নতুন issue থাকলে solve করো
    if audit_findings["open_issues"]:
        return {"task": "SOLVE_ISSUE", "issue": highest_priority_issue}

    # প্রায়োরিটি ৫: dead code থাকলে cleanup করো
    if audit_findings["dead_files"]:
        return {"task": "CLEANUP", "files": top_5_dead_files}

    # প্রায়োরিটি ৬: কিছু না থাকলে audit করো
    return {"task": "AUDIT", "scope": "full"}
```

### গ. কাজের ধরন (Task Types)

script এই ধরনের কাজ দিতে পারে:

| Task Type | কী করে | কখন দেয় |
|-----------|--------|---------|
| `FIX_RED_MAIN` | main লাল হলে ঠিক করো | main CI red |
| `SOLVE_ISSUE` | GitHub issue solve করো | unclaimed issue আছে |
| `REVIEW_PR` | open PR review করো | unreviewed PR আছে |
| `MERGE_GROUP` | গ্রুপ merge করো | সব PR green + audit done |
| `CLEANUP` | dead code delete করো | dead files পাওয়া গেছে |
| `AUDIT` | কোডবেস audit করো | নির্দিষ্ট সময় পরপর |
| `FIX_BROKEN_API` | frontend-backend contract ঠিক করো | broken API পাওয়া গেছে |
| `FIX_CIRCULAR` | circular import ঠিক করো | circular dep পাওয়া গেছে |
| `VERIFY_PRS` | stale PR গুলো চেক করো | ২৪+ ঘণ্টা পুরনো PR |

---

## ৪. নতুন AGENTS.md (সরলীকৃত — ~৫০ লাইন)

```markdown
# SupremeAI — AGENTS.md v3 (Unified Agent)

> সব এজেন্ট একই টাইপ। কে কী করবে স্ক্রিপ্ট বলে দেবে।

## বুটস্ট্র্যাপ (প্রতি সেশনে এই ক্রমে)

১. `git fetch origin --prune` — main sync
২. `python scripts/agents/supremeai_orchestrator.py --slot agent-N` — কাজ নাও
৩. script যা বলে তাই করো — fix, review, merge, audit যাই হোক
৪. ৩-স্তর যাচাই বাধ্যতামূলক (Reflection → Boot → Pytest)
৫. PR খুলে `queue:hold` দাও + `has-pr` লেবেল দাও
৬. কাজ শেষ হলে আবার step ২ চালাও — পরবর্তী কাজ নাও

## হার্ড রুল (মাত্র ৪টি)

১. সততা: টেস্ট ম্যানিপুলেশন সর্বোচ্চ অপরাধ
২. পরমাণু: ১ কাজ = ১ ব্রাঞ্চ = ১ PR
৩. অবিরাম: কাজ শেষ হলে পরবর্তী কাজ নাও — অলস থাকা নিষিদ্ধ
৪. বাংলা: সব যোগাযোগ ও কমেন্ট বাংলায়

## স্ক্রিপ্ট যা করে

- কোডবেস অডিট করে (dead code, broken API, circular import, stale PR)
- প্রায়োরিটি দিয়ে কাজ বরাদ্ধ করে (main red → fix, PR unreviewed → review, issue unclaimed → solve)
- গ্রুপ সম্পূর্ণ হলে merge train চালায়
- সব এজেন্ট একই protocol ফলো করে — lane ভেদে নিয়ম নেই
```

---

## ৫. স্ক্রিপ্টের গঠন (supremeai_orchestrator.py)

```python
#!/usr/bin/env python3
"""SupremeAI Orchestrator — একক এজেন্ট কাজ-বরাদ্ধকারী

এটাই এজেন্টের "মস্তিষ্ক"। এজেন্ট নিজে কী করবে সেটা এই script বলে দেয়।

রান করা:
  python scripts/agents/supremeai_orchestrator.py --slot agent-1
  python scripts/agents/supremeai_orchestrator.py --slot agent-1 --audit-only
"""

import argparse
import json
import subprocess
import os
from pathlib import Path
from typing import Any

# ── অডিট ফাংশন ──────────────────────────────────────────

def audit_dead_files() -> list[dict]:
    """AST import graph দিয়ে dead files খুঁজে বের করো"""
    # backend/ এ সব .py file স্ক্যান করো
    # প্রতিটি file-এর importers গুনো
    # 0 importer = dead
    pass

def audit_broken_apis() -> list[dict]:
    """frontend API calls vs backend openapi.json মিলাও"""
    pass

def audit_circular_imports() -> list[dict]:
    """AST bidirectional import graph দিয়ে circular deps খুঁজে বের করো"""
    pass

def audit_stale_prs() -> list[dict]:
    """২৪+ ঘণ্টা পুরনো open PR গুলো খুঁজে বের করো"""
    pass

def audit_main_ci() -> dict:
    """main branch-এর সর্বশেষ CI status চেক করো"""
    pass

def fetch_unclaimed_issues() -> list[dict]:
    """GitHub API থেকে unclaimed issues আনো + prioritize করো"""
    pass

def fetch_unreviewed_prs() -> list[dict]:
    """GitHub API থেকে review-less open PR গুলো আনো"""
    pass

def check_group_completion() -> dict | None:
    """কোনো গ্রুপের সব PR green + audit done কিনা চেক করো"""
    pass

# ── কাজ বরাদ্ধকারণ ────────────────────────────────────────

def prioritize_work(audit: dict, slot: str) -> dict:
    """সব ফিল্টার করে এই এজেন্টের জন্য সবচেয়ে গুরুত্বপূর্ণ কাজ বেছে নাও"""

    # ১. main লাল → FIX_RED_MAIN
    if audit["main_ci"]["red"]:
        return {
            "task": "FIX_RED_MAIN",
            "priority": "P0",
            "details": audit["main_ci"],
            "instruction": f"main লাল! {audit['main_ci']['failing_job']} ঠিক করো।",
        }

    # ২. stale PR (২৪+ ঘণ্টা) → CHECK_STALE
    if audit["stale_prs"]:
        pr = audit["stale_prs"][0]
        return {
            "task": "CHECK_STALE_PR",
            "pr": pr["number"],
            "instruction": f"PR #{pr['number']} {pr['age_hours']}ঘণ্টা পুরনো — rebase বা close করো।",
        }

    # ৩. unreviewed PR → REVIEW
    if audit["unreviewed_prs"]:
        pr = audit["unreviewed_prs"][0]
        return {
            "task": "REVIEW_PR",
            "pr": pr["number"],
            "instruction": f"PR #{pr['number']} review করো (4-Pillar Rubric)।",
        }

    # ৪. গ্রুপ merge-ready → MERGE
    group = audit.get("group_ready")
    if group:
        return {
            "task": "MERGE_GROUP",
            "group": group["name"],
            "prs": group["pr_numbers"],
            "instruction": f"গ্রুপ '{group['name']}' সম্পূর্ণ — merge train চালাও।",
        }

    # ৫. সর্বোচ্চ priority issue → SOLVE
    if audit["unclaimed_issues"]:
        issue = audit["unclaimed_issues"][0]  # already sorted by priority
        return {
            "task": "SOLVE_ISSUE",
            "issue": issue["number"],
            "title": issue["title"],
            "priority": issue["priority"],
            "instruction": f"Issue #{issue['number']} solve করো।",
        }

    # ৬. dead code → CLEANUP
    if audit["dead_files"]:
        files = audit["dead_files"][:5]  # batch of 5
        return {
            "task": "CLEANUP_DEAD_CODE",
            "files": [f["path"] for f in files],
            "instruction": f"এই {len(files)}টি dead file delete করো (3-tier verify সহ)।",
        }

    # ৭. broken API → FIX
    if audit["broken_apis"]:
        api = audit["broken_apis"][0]
        return {
            "task": "FIX_BROKEN_API",
            "file": api["file"],
            "path": api["path"],
            "instruction": f"Frontend {api['file']} এ {api['path']} call করে কিন্তু backend-এ এই route নেই।",
        }

    # ৮. circular import → FIX
    if audit["circular_imports"]:
        circ = audit["circular_imports"][0]
        return {
            "task": "FIX_CIRCULAR_IMPORT",
            "modules": circ,
            "instruction": f"Circular import: {circ[0]} ↔ {circ[1]} — lazy import দিয়ে ভাঙো।",
        }

    # ৯. কিছু নেই → AUDIT
    return {
        "task": "AUDIT",
        "instruction": "সব কাজ শেষ — নতুন audit চালাও বা নতুন issue খুঁজে বের করো।",
    }

# ── মূল ফাংশন ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SupremeAI Unified Agent Orchestrator")
    parser.add_argument("--slot", required=True, help="Agent slot (e.g. agent-1)")
    parser.add_argument("--audit-only", action="store_true", help="শুধু audit করো, কাজ বরাদ্ধ করবে না")
    args = parser.parse_args()

    print(f"🤖 SupremeAI Orchestrator — Slot: {args.slot}")
    print(f"📅 {datetime.now().isoformat()}")
    print()

    # অডিট চালাও
    print("🔍 কোডবেস অডিট চলছে...")
    audit = {
        "dead_files": audit_dead_files(),
        "broken_apis": audit_broken_apis(),
        "circular_imports": audit_circular_imports(),
        "stale_prs": audit_stale_prs(),
        "main_ci": audit_main_ci(),
        "unclaimed_issues": fetch_unclaimed_issues(),
        "unreviewed_prs": fetch_unreviewed_prs(),
        "group_ready": check_group_completion(),
    }

    # সারাংশ দেখাও
    print(f"  Dead files: {len(audit['dead_files'])}")
    print(f"  Broken APIs: {len(audit['broken_apis'])}")
    print(f"  Circular imports: {len(audit['circular_imports'])}")
    print(f"  Stale PRs: {len(audit['stale_prs'])}")
    print(f"  Main CI: {'🔴 RED' if audit['main_ci']['red'] else '🟢 GREEN'}")
    print(f"  Unclaimed issues: {len(audit['unclaimed_issues'])}")
    print(f"  Unreviewed PRs: {len(audit['unreviewed_prs'])}")
    print()

    if args.audit_only:
        print("📋 Audit complete (--audit-only mode)")
        return

    # কাজ বরাদ্ধ করো
    work = prioritize_work(audit, args.slot)

    print("═" * 50)
    print(f"📝 আপনার কাজ: {work['task']}")
    print("═" * 50)
    print(f"📋 {work['instruction']}")
    print()

    if work["task"] == "SOLVE_ISSUE":
        print(f"   Issue: #{work['issue']}")
        print(f"   Title: {work['title']}")
        print(f"   Priority: {work['priority']}")
        print(f"   Branch: {args.slot}-{work['issue']}-{slugify(work['title'])}")
        print()
        print("   ধাপ:")
        print("   ১. ./scripts/ci/atomic_claim.sh {} {}".format(work['issue'], args.slot))
        print("   ২. সমাধান করো (3-tier verify সহ)")
        print("   ৩. gh pr create + has-pr + queue:hold")
        print("   ৪. আবার এই script রান করো পরবর্তী কাজের জন্য")

    elif work["task"] == "REVIEW_PR":
        print(f"   PR: #{work['pr']}")
        print()
        print("   ধাপ:")
        print("   ১. PR diff পড়ো")
        print("   ২. 4-Pillar Rubric (Stability, Benefit, Regression, Scope)")
        print("   ৩. gh pr review {} --comment -b 'findings'".format(work['pr']))

    elif work["task"] == "MERGE_GROUP":
        print(f"   Group: {work['group']}")
        print(f"   PRs: {work['prs']}")
        print()
        print("   ধাপ:")
        print("   ১. সব PR green কিনা verify করো")
        print("   ২. Closeout audit সম্পন্ন কিনা দেখো")
        print("   ৩. gh pr merge --squash (প্রতিটি PR)")

    elif work["task"] == "CLEANUP_DEAD_CODE":
        print(f"   Files to delete ({len(work['files'])}):")
        for f in work["files"]:
            print(f"     - {f}")
        print()
        print("   ধাপ:")
        print("   ১. প্রতিটি file-এর জন্য: grep 0 importers (Tier 1)")
        print("   ২. Boot smoke: python -c 'import main' (Tier 2)")
        print("   ৩. Pytest (Tier 3)")
        print("   ৪. Delete + commit + PR + has-pr + queue:hold")

    # JSON আউটপুট (machine-readable)
    print()
    print("---JSON---")
    print(json.dumps(work, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

---

## ৬. সুবিধা (কেন এটা ভালো)

| # | বর্তমান (৭ টাইপ) | প্রস্তাবিত (১ টাইপ) |
|---|------------------|---------------------|
| ১ | ৭টি lane, ৭টি slot pool | ১টি pool: agent-1, agent-2, agent-3... |
| ২ | handoff:coder/ci/planner সাইলো | কোনো সাইলো নেই — script assign করে |
| ৩ | planner PR খুলতে পারে না | যেকোনো এজেন্ট যেকোনো কাজ করতে পারে |
| ৪ | ৪৮,৬০০ লাইন গভর্নেন্স | ~৫০ লাইন AGENTS.md + ১টি script |
| ৫ | coder আইডল, ci ব্যস্ত → ভারসাম্যহীন | script সব এজেন্টকে ভারসাম্যপূর্ণ কাজ দেয় |
| ৬ | ৭টি role card, ২৩টি invariant | ৪টি hard rule, বাকি script-এ |
| ৭ | lane-specific collision | সব এজেন্ট একই pool — collision detection সহজ |
| ৮ | নতুন lane যোগ করতে চার্টার আপডেট | script-এ নতুন task type যোগ করো |
| ৯ | "আমি coder, এটা আমার কাজ না" | "script বলেছে করতে, তাই করছি" |
| ১০ | Lane boundary violation (L1 incident) | Lane নেই — violation অসম্ভব |

---

## ৭. সিকিউরিটি বিবেচনা

### স্ব-মার্জ প্রতিরোধ
```
সমস্যা: যদি সব এজেন্ট merge করতে পারে, নিজের PR নিজে merge করবে?
সমাধান: script চেক করবে — PR author != merge requester
         CI gate (self_merge_gate) এটা enforce করে
```

### স্কোপ কন্ট্রোল
```
সমস্যা: যদি সব এজেন্ট সব কাজ করতে পারে, scope কীভাবে নিয়ন্ত্রণ?
সমাধান: script প্রতি রানে শুধু ১টি কাজ দেয়
         atomic_claim.sh --files দিয়ে file boundary ঘোষণা
         scope_gate undeclared files BLOCK করে
```

### প্রায়োরিটি নিয়ন্ত্রণ
```
সমস্যা: সব এজেন্ট একই issue claim করবে?
সমাধান: atomic_claim.sh CAS (compare-and-swap) — প্রথম এজেন্ট পায়
         script প্রতি এজেন্টকে আলাদা কাজ দেয় (slot-based assignment)
```

---

## ৮. মাইগ্রেশন প্ল্যান

### ধাপ ১: script তৈরি (১-২ দিন)
- `scripts/agents/supremeai_orchestrator.py` লেখো
- audit ফাংশনগুলো implement করো
- prioritize_work লজিক টেস্ট করো

### ধাপ ২: AGENTS.md v3 তৈরি (১ দিন)
- বর্তমান v2.7 থেকে v3 তৈরি করো (~৫০ লাইন)
- `rules.yml` আপডেট করো
- system-gates.yml আপডেট করো (lane-specific নিয়ম সরাও)

### ধাপ ৩: পরীক্ষা (১ দিন)
- ১টি এজেন্ট দিয়ে টেস্ট করো
- script আউটপুট ভেরিফাই করো
- সব task type একবার করে টেস্ট করো

### ধাপ ৪: মাইগ্রেশন (১ সপ্তাহ)
- পুরনো lane-specific branch গুলো clean up করো
- handoff লেবেল গুলো সরাও (বা backward-compatible রাখো)
- acquire_role_slot.py আপডেট করো (lane parameter optional করো)
- সব এজেন্টকে নতুন AGENTS.md v3 ফলো করতে বলো

### ধাপ ৫: পুরনো গভর্নেন্স সাফ (১ দিন)
- `.agents/rules/`, `.lingma`, `.clinerules`, `.specify` আর্কাইভ করো
- role card গুলো সরাও (`docs/agents/roles/*.md`)
- AGENT_WORK_BOUNDARIES_CHARTER.md সরাও
- slot registry সরল করো (শুধু agent-N)

---

## ৯. ঝুঁকি ও প্রতিকার

| ঝুঁকি | সম্ভাবনা | প্রতিকার |
|-------|---------|---------|
| script ভুল কাজ দেয় | মাঝে মাঝে | এজেন্ট reject করতে পারে + পরবর্তী কাজ চাইতে পারে |
| সব এজেন্ট একই কাজ করে | কম (CAS prevents) | atomic_claim.sh CAS lock |
| script ক্র্যাশ করে | কম | fallback: "script unavailable — manually check issues" |
| বিশেষায়িত কাজে দক্ষতা কম | মাঝে মাঝে | script context দেয় (issue body + 3-tier instructions) |
| পুরনো এজেন্ট ভাঙে | মাইগ্রেশন সময় | backward-compatible: lane parameter optional রাখো |

---

## ১০. উপসংহার

**এই মডেলের মূল শক্তি**: জটিলতা এজেন্ট থেকে script-এ সরে যায়। এজেন্ট সরল থাকে — শুধু script ফলো করে। script বুদ্ধিমান — কোডবেস বুঝে, প্রায়োরিটি দিয়ে, কাজ বরাদ্ধ করে।

**"ঘুড়ি ওড়াও, নাটাই আমার হাতে"** — এখন নাটাই শুধু admin-এর হাতে নয়, script-এর হাতেও। script-ই বলে দেয় কে কোন ঘুড়ি ওড়াবে।

> "Code is a liability; Clear Protocol is leverage — অপ্রয়োজনীয় rigid নিয়ম বা জটিল কোড নয়; সবকিছু interconnected, কিন্তু unnecessary complexity ছাড়া।"
