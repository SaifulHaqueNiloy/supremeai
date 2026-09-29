# SupremeAI — Universal Agent Architecture (Merged Plan v2)

> **তারিখ**: ২০২৮-০৯-২৮
> **উৎস**: ফাউন্ডার প্ল্যান (Universal Agent + Dynamic Task Router) + কোডার প্ল্যান (Unified Agent + Orchestrator) — গভীর তুলনা ও মার্জ
> **মূল নীতি**: "Agent type নয় → Task type। সব এজেন্ট একই Universal Protocol follow করবে। Database-এ কাজের নিয়ম থাকবে, script বর্তমান অবস্থা দেখে কাজ বরাদ্ধ করবে।"

---

## তুলনা: আমার প্ল্যান vs আপনার প্ল্যান

### আমার প্ল্যানে যা ছিল (ভালো অংশ)

| বিষয় | আমার প্ল্যানে ছিল | মান |
|------|------------------|-----|
| একক এজেন্ট টাইপ | ✅ | একই |
| Orchestrator script | ✅ (supremeai_orchestrator.py) | একই ধারণা |
| Task types (FIX, REVIEW, MERGE, CLEANUP) | ✅ | একই |
| Audit মোড | ✅ | একই |
| সরল AGENTS.md (~৫০ লাইন) | ✅ | একই |
| মাইগ্রেশন প্ল্যান | ✅ | একই |
| সিকিউরিটি (self-merge, scope, CAS) | ✅ | একই |

### আপনার প্ল্যানে যা আছে কিন্তু আমার প্ল্যানে ছিল না (যোগ করতে হবে)

| # | বিষয় | আপনার প্ল্যানে | আমার প্ল্যানে | কেন দরকার |
|---|------|---------------|--------------|-----------|
| ১ | **Database টাস্ক পলিসি লেয়ার** | ✅ task-specific rules DB-তে | ❌ script-এ hardcoded | নিয়ম পরিবর্তন করতে code edit লাগে না — DB update করলেই হয় |
| ২ | **Smart Context Selection** | ✅ শুধু relevant rules পাঠায় | ❌ সব context পাঠায় | LLM context window সাশ্রয়, focus বাড়ে |
| ৩ | **Agent Memory / Historical Knowledge** | ✅ successful solutions DB-তে | ❌ নেই | একই সমস্যা বারবার solve করতে হয় না |
| ৪ | **Rule Layering (priority hierarchy)** | ✅ ৮-স্তর priority | ❌ flat | কোন rule কখন override করবে স্পষ্ট |
| ৫ | **Breaker / Adversarial Mode** | ✅ rule bypass, security gap খোঁজে | ❌ নেই | সিস্টেমের দুর্বলতা ধরা যায় |
| ৬ | **Dynamic Instruction Format** | ✅ standard structure | ❌ ad-hoc output | Machine-readable + consistent |
| ৭ | **Permisson per task** | ✅ DB-driven permissions | ❌ সব এজেন্ট সব পারে | Audit task-এ code modify করতে পারবে না |
| ৮ | **Self-Improving Router** | ✅ historical data থেকে শেখে | ❌ static logic | Evidence-driven workflow |
| ৯ | **Learning Loop** | ✅ task → action → result → knowledge → DB | ❌ নেই | "ভুল একবারই" — কিন্তু automated |
| ১০ | **Branch ≠ Agent identity** | ✅ branch reuse across tasks | ❌ বলে নি | বেশি flexible |
| ১১ | **CI Failure Automation** | ✅ CI fail → root cause instruction | ❌ সাধারণ FIX task | নির্দিষ্ট: "root cause খোঁজো, disable করবে না" |
| ১২ | **Task State Machine** | ✅ START → AUDIT → ISSUES → GROUP → IMPLEMENT → PR → CI → VERIFY → MERGE/FIX/REISSUE | ❌ সাধারণ loop | সম্পূর্ণ lifecycle |
| ১৩ | **Group Verification** | ✅ "individual PR green ≠ group correct" | ❌ বলে নি | Integration bugs ধরা |
| ১৪ | **Agent Capability Matching** | ✅ task → model matching | ❌ নেই | ভবিষ্যতে multi-model support |
| ১৫ | **Forbidden Actions per task** | ✅ "Do not: disable checks, weaken security" | ❌ শুধু "3-tier verify" | সুনির্দিষ্ট নিষেধ |

### আমার প্ল্যানে যা ছিল কিন্তু আপনার প্ল্যানে নেই (রাখা যায়)

| # | বিষয় | আমার প্ল্যানে | আপনার প্ল্যানে | মতামত |
|---|------|---------------|--------------|-------|
| ১ | Script code (supremeai_orchestrator.py) | ✅ সম্পূর্ণ Python structure | ❌ conceptual only | আপনার conceptual design-এ implementation skeleton যোগ করা যায় |
| ২ | মাইগ্রেশন প্ল্যান (৫ ধাপ) | ✅ | ❌ | কীভাবে পুরনো থেকে নতুনে যাওয়া যায় |
| ৩ | ঝুঁকি ও প্রতিকার table | ✅ | ❌ | কী ভুল হতে পারে |

---

## মার্জড প্ল্যান (আপনার design + আমার implementation)

### স্থপতি (Architecture)

```
                    ADMIN / GOVERNANCE
                          │
                          ▼
                     AGENTS.md v3
                Universal Contract (~৫০ লাইন)
                          │
                          ▼
                   AGENT STARTUP
              ./scripts/agent/start
                          │
                          ▼
                    TASK ROUTER
              (supremeai_orchestrator.py)
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   Current State    Database Rules    History
   (repo + GitHub)  (task policies)  (knowledge)
          │               │               │
          └───────────────┼───────────────┘
                          ▼
               SMART CONTEXT SELECTION
            (শুধু relevant rules পাঠায়)
                          │
                          ▼
               DYNAMIC INSTRUCTION
           (standard format — machine-readable)
                          │
                          ▼
                  UNIVERSAL AGENT
                          │
                          ▼
                    EXECUTION
                          │
                          ▼
              TEST / VALIDATE (৩-স্তর)
                          │
                          ▼
              PR / ISSUE UPDATE
                          │
                          ▼
                  VERIFICATION
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
        MERGE            FIX           REISSUE
                          │
                          ▼
                   LEARNING DATA
                  (task → result → knowledge)
                          │
                          └──────► ROUTER
                         (self-improving)
```

### তিন-স্তর কন্ট্রোল মডেল

**Layer 1 — AGENTS.md (~৫০ লাইন)**
- Universal rules: সততা, পরমাণু স্কোপ, ৩-স্তর যাচাই, বাংলা, queue:hold
- Stable — কদাচিৎ পরিবর্তন

**Layer 2 — Database (Task Policy + Knowledge)**
- `task_policies`: audit_rules, coding_rules, review_rules, ci_rules, security_rules, breaker_rules
- `task_permissions`: per-task কী করতে পারবে (read_repo, modify_code, create_issue, merge)
- `task_history`: successful solutions (problem → root cause → solution → files → tests)
- `task_knowledge`: lessons learned, patterns, anti-patterns

**Layer 3 — Dynamic Router (supremeai_orchestrator.py)**
- বর্তমান state: repo audit + GitHub state + CI status
- প্রায়োরিটি: main red → stale PR → unreviewed PR → group merge → issue → dead code → audit
- Smart context: শুধু relevant rules + history পাঠায়
- Instruction: standard format (MODE, RULES, ACTIONS, FORBIDDEN, VALIDATION)

### Rule Layering (priority hierarchy)

```
১. Admin / Core Governance (highest — override করতে পারে না)
২. AGENTS.md (universal — সব task-এ থাকবে)
৩. Security Rules (task-specific)
৪. Task Rules (coding/audit/review/breaker)
৫. Group Rules (group-specific staging)
৬. Issue Rules (acceptance criteria)
৭. Repository Context (current architecture)
৮. Historical Knowledge (lowest — truth নয়, শুধু reference)
```

### Task Types (আপনার প্ল্যান + আমার task types মার্জড)

| Task Type | কী করে | Permissions | Forbidden |
|-----------|--------|-------------|-----------|
| `INITIAL_AUDIT` | কোডবেস audit করে issue তৈরি করে | read_repo: ✅, create_issue: ✅, modify_code: ❌ | কোড পরিবর্তন নিষিদ্ধ |
| `SOLVE_ISSUE` | issue solve করে PR খোলে | read_repo: ✅, modify_code: ✅, create_pr: ✅, merge: ❌ | টেস্ট ম্যানিপুলেশন নিষিদ্ধ |
| `REVIEW_PR` | PR review করে 4-Pillar Rubric দিয়ে | read_repo: ✅, comment: ✅, merge: ❌ | নিজের PR review নিষিদ্ধ |
| `MERGE_GROUP` | গ্রুপ merge করে | read_repo: ✅, merge: ✅ (if verified) | বিনা verify মার্জ নিষিদ্ধ |
| `CLEANUP` | dead code delete করে | read_repo: ✅, modify_code: ✅, create_pr: ✅ | ৩-tier verify ছাড়া delete নিষিদ্ধ |
| `FIX_RED_MAIN` | main লাল হলে ঠিক করে | read_repo: ✅, modify_code: ✅, create_pr: ✅ | CI disable / security weaken নিষিদ্ধ |
| `ADVERSARIAL_AUDIT` | rule bypass + security gap খোঁজে | read_repo: ✅, create_issue: ✅, modify_code: ❌ | কোড পরিবর্তন নিষিদ্ধ — শুধু findings |
| `CI_FAILURE` | CI fail → root cause খোঁজে | read_repo: ✅, modify_code: ✅ | check disable / failure hide নিষিদ্ধ |
| `GROUP_VERIFICATION` | পুরো গ্রুপ একসাথে যাচাই | read_repo: ✅, comment: ✅ | কোড পরিবর্তন নিষিদ্ধ |
| `LEARNING` | task result → knowledge DB | read_repo: ✅, write_db: ✅ | code modify / rule change নিষিদ্ধ |

### Dynamic Instruction Format

```text
SUPREMEAI AGENT TASK
═══════════════════════════════════════

MODE: SOLVE_ISSUE
TASK_ID: task-2026-09-28-001
GROUP: pipeline-restoration
ISSUES: #2480, #2481
PR: (none yet)

OBJECTIVE:
  Issue #2480: 290 dead files delete করো (batch 1: 5 files)
  Issue #2481: 21 dead frontend components delete করো

CONTEXT:
  Repository: supremeai @ HEAD 9710b763
  Main CI: 🟢 GREEN
  Open PRs: 3 (all queue:hold)
  Unclaimed issues: 8
  Dead files: 290 (backend) + 21 (frontend)

APPLICABLE RULES (priority order):
  1. AGENTS.md v3 (universal)
  2. security_rules (no secret exposure)
  3. coding_rules (3-tier verify, atomic scope)
  4. group:pipeline-restoration (sequential hold)

REQUIRED ACTIONS:
  ১. atomic_claim.sh 2480 agent-1
  ২. প্রতিটি file-এর জন্য: grep 0 importers (Tier 1)
  ৩. Boot smoke: python -c 'import main' (Tier 2)
  ৪. Pytest (Tier 3)
  ৫. Delete + commit + PR + has-pr + queue:hold

FORBIDDEN ACTIONS:
  ❌ টেস্ট delete/skip/fake assertion
  ❌ claim ছাড়া কোড পরিবর্তন
  ❌ declared files-এর বাইরে touch
  ❌ check disable / security weaken
  ❌ failure hide / unrelated change

VALIDATION:
  - 3-Tier: Reflection (grep) → Boot (import main) → Pytest
  - PR description-এ Test Evidence section বাধ্যতামূলক

ACCEPTANCE CRITERIA:
  - প্রতিটি deleted file-এর 0 importers প্রমাণিত
  - Boot smoke PASS
  - Pytest 0 new failures
  - PR green (pr-gate:passed)

STOP CONDITIONS:
  - যদি কোনো file-এ 1+ importer পাওয়া যায় → STOP, skip that file
  - যদি boot smoke fail করে → STOP, revert, report
  - যদি pytest-এ new failure আসে → STOP, revert, report

EXPECTED OUTPUT:
  - PR with queue:hold + has-pr
  - PR body-এ: deleted files list + 3-tier evidence
  - Issue-এ comment: "PR #N opened"

═══════════════════════════════════════
```

### Breaker / Adversarial Mode

```python
# Database-এ breaker_rules:
{
    "mode": "ADVERSARIAL_AUDIT",
    "permissions": {
        "read_repo": True,
        "create_issue": True,
        "modify_code": False,  # কোড পরিবর্তন করতে পারবে না
    },
    "checks": [
        "rule_bypass: কোনো CI gate বাইপাস করা যায় কিনা",
        "security_gap: hardcoded secret, broken auth, SSRF",
        "arch_weakness: circular import, dead code accumulation pattern",
        "scope_violation: declared files-এর বাইরে কোড ঢুকে কিনা",
        "test_manipulation: skip marker যোগ করে CI green করা যায় কিনা",
        "merge_bypass: queue:hold ছাড়া মার্জ করা যায় কিনা",
        "permission_escalation: audit task-এ code modify করা যায় কিনা",
    ],
    "output": "GitHub issues (P0-critical বা P1-high label সহ)",
    "forbidden": [
        "কোড পরিবর্তন করা",
        "PR খোলা",
        "merge করা",
    ],
}
```

### Smart Context Selection

```python
def build_context(task_type, audit_findings, issue_context):
    """শুধু relevant rules + history পাঠায় — সব context নয়"""

    context = {
        # Layer 1: সবসময় থাকবে
        "universal_rules": load_agents_md(),

        # Layer 2: task-specific
        "task_rules": load_db(f"task_policies/{task_type}"),
        "permissions": load_db(f"task_permissions/{task_type}"),

        # Layer 3: context-specific
        "issue_context": issue_context or {},
        "repo_state": audit_findings,

        # Layer 4: historical (relevant only)
        "similar_solutions": find_similar_tasks(task_type, issue_context),
    }

    # যদি task = coding → frontend rules পাঠাবে না
    if task_type == "SOLVE_ISSUE" and issue_context.get("area") == "backend":
        context["task_rules"].pop("frontend_rules", None)

    # যদি task = review → coding rules পাঠাবে না (শুধু review_rules)
    if task_type == "REVIEW_PR":
        context["task_rules"] = {
            "review_rules": context["task_rules"].get("review_rules"),
            "security_rules": context["task_rules"].get("security_rules"),
        }

    return context
```

### Learning Loop

```python
def record_learning(task, result):
    """task শেষে knowledge DB-তে রেকর্ড করো"""

    if result["success"]:
        knowledge = {
            "task_type": task["mode"],
            "problem": task["objective"],
            "root_cause": result.get("root_cause"),
            "solution": result.get("approach"),
            "files_changed": result.get("files"),
            "tests_used": result.get("tests"),
            "failed_approaches": result.get("failed_attempts", []),
            "verification": result.get("verification"),
            "timestamp": now(),
        }
        db.save("task_history", knowledge)

    # Self-improving router: historical data থেকে pattern শেখো
    if db.count("task_history") > 50:  # enough data
        patterns = analyze_patterns(db.query("task_history"))
        db.update("router_patterns", patterns)
```

### Database Schema

```sql
-- Task Policies (Layer 2: কাজের নিয়ম)
CREATE TABLE task_policies (
    task_type TEXT PRIMARY KEY,    -- 'coding_rules', 'audit_rules', etc.
    rules JSON,                     -- কাজের নিয়ম
    forbidden_actions JSON,         -- নিষিদ্ধ কাজ
    permissions JSON,               -- কী করতে পারবে
    updated_at TIMESTAMP
);

-- Task History (Layer 2: পূর্বের সমাধান)
CREATE TABLE task_history (
    id SERIAL PRIMARY KEY,
    task_type TEXT,                 -- 'SOLVE_ISSUE', 'AUDIT', etc.
    issue_number INT,
    problem TEXT,
    root_cause TEXT,
    solution TEXT,
    files_changed JSON,
    tests_used JSON,
    failed_approaches JSON,
    verification_result TEXT,
    success BOOLEAN,
    created_at TIMESTAMP
);

-- Router Patterns (Layer 3: self-improving)
CREATE TABLE router_patterns (
    task_type TEXT,
    common_rules_needed JSON,
    common_failures JSON,
    successful_approaches JSON,
    confidence FLOAT,
    updated_at TIMESTAMP
);
```

### Task State Machine

```
START
  ↓
INITIAL_AUDIT (first run only)
  ↓
ISSUES_CREATED
  ↓
GROUP_WORK (issues grouped by objective)
  ↓
IMPLEMENTATION (solve issues, create PRs)
  ↓
PR_OPENED (queue:hold)
  ↓
CI_RUNS
  ↓
GROUP_VERIFICATION (সব PR একসাথে যাচাই)
  ↓
  ┌───────────┬───────────┬───────────┐
  ▼           ▼           ▼           ▼
MERGE      FIX        REISSUE     ADVERSARIAL
  │           │           │       (breaker checks
  │           │           │        merged code)
  └───────────┴───────────┘
              ↓
        LEARNING_DATA
         (record to DB)
              ↓
        NEXT_GROUP
```

---

## মাইগ্রেশন প্ল্যান (আপডেটেড)

### ধাপ ১: Database তৈরি (২-৩ দিন)
- `task_policies` table তৈরি + initial rules seed
- `task_history` table তৈরি
- `task_permissions` per task type
- LESSONS_LEARNED.md entries → DB-তে migrate

### ধাপ ২: Orchestrator script (২-৩ দিন)
- `scripts/agent/start` — bootstrap entry point
- `scripts/agent/router` — task router (supremeai_orchestrator.py)
- `scripts/agent/context` — smart context selector
- `scripts/agent/instruction` — dynamic instruction generator
- `scripts/agent/verify` — verification runner
- `scripts/agent/learn` — learning loop recorder

### ধাপ ৩: AGENTS.md v3 (১ দিন)
- ~৫০ লাইন: bootstrap + ৪ hard rules + script ফলো করো
- `rules.yml` আপডেট
- `system-gates.yml` আপডেট

### ধাপ ৪: Breaker Mode (১-২ দিন)
- `breaker_rules` DB-তে seed
- ৭টি check implement (rule_bypass, security_gap, arch_weakness, etc.)
- Output: GitHub issues auto-create

### ধাপ ৫: পরীক্ষা (১ দিন)
- ১টি এজেন্ট দিয়ে সব task type টেস্ট
- Breaker mode টেস্ট
- Learning loop টেস্ট

### ধাপ ৬: মাইগ্রেশন (১ সপ্তাহ)
- পুরনো lane-specific সবকিছু সরাও
- acquire_role_slot.py আপডেট (lane parameter optional)
- সব এজেন্টকে `./scripts/agent/start` ফলো করতে বলো

### ধাপ ৭: পুরনো গভর্নেন্স সাফ (১ দিন)
- `.agents/rules/`, `.lingma`, `.clinerules`, `.specify` আর্কাইভ
- role cards সরাও
- AGENT_WORK_BOUNDARIES_CHARTER.md সরাও
- slot registry সরল করো

---

## সিদ্ধান্ত: কী যোগ/পরিবর্তন/অপসারণ করতে হবে

### আমার প্ল্যানে যোগ করতে হবে (আপনার প্ল্যান থেকে)

১. **Database Task Policy Layer** — script-এ hardcoded না রেখে DB-তে রাখো
২. **Smart Context Selection** — শুধু relevant rules পাঠাও
৩. **Agent Memory** — historical solutions DB-তে রাখো
৪. **Rule Layering** — ৮-স্তর priority hierarchy
৫. **Breaker/Adversarial Mode** — rule bypass + security gap খোঁজে
৬. **Dynamic Instruction Format** — standard machine-readable structure
৭. **Per-task Permissions** — audit task-এ code modify নিষিদ্ধ
৮. **Self-Improving Router** — historical data থেকে pattern শেখে
৯. **Learning Loop** — task → result → knowledge → DB → future
১০. **CI Failure Automation** — নির্দিষ্ট: "root cause খোঁজো, disable করবে না"
১১. **Task State Machine** — সম্পূর্ণ lifecycle
১২. **Group Verification** — "individual PR green ≠ group correct"
১৩. **Branch ≠ Agent identity** — branch reuse across tasks
১৪. **Forbidden Actions per task** — সুনির্দিষ্ট নিষেধ

### আমার প্ল্যান থেকে রাখা যায়

১. **Script implementation skeleton** (supremeai_orchestrator.py Python code)
২. **মাইগ্রেশন ৫-ধাপ প্ল্যান**
৩. **ঝুঁকি ও প্রতিকার table**

### আমার প্ল্যান থেকে সরাতে হবে

১. **Hardcoded task types in script** — সব DB-তে যাবে
২. **Static prioritize_work function** — self-improving হতে হবে
৩. **Flat rule priority** — ৮-স্তর hierarchy দরকার

---

## উপসংহার

**আপনার প্ল্যান আমার প্ল্যানের "next level"** — আমার প্ল্যানে script ছিল কিন্তু সেটা "dumb executor" ছিল। আপনার প্ল্যানে script হলো "intelligent router" যে:
- Database থেকে নিয়ম পড়ে (hardcoded নয়)
- Historical knowledge থেকে শেখে
- Smart context তৈরি করে (সব না, relevant)
- Breaker mode-এ নিজের নিয়ম ভাঙার চেষ্টা করে
- Per-task permission দেয় (audit-এ code modify নিষিদ্ধ)

**আমার implementation skeleton + আপনার design = সম্পূর্ণ প্ল্যান।**

> "simple architecture + dynamic intelligence + strong control"
> "Agent type নয় → Task type।"
> "Task chooses capability; model does not define the task."
