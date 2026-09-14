হ্যাঁ—**আপনার proposed policy ভালো**, এবং আমি বর্তমান SupremeAI repository দেখে এটাকে আরও একটু refine করব।

আমি আপনার repository `SaifulHaqueNiloy/supremeai`-এর বর্তমান structure/coverage configuration দেখেছি। Repository-তে ইতিমধ্যেই coverage infrastructure আছে—যেমন `backend/.coveragerc`, `backend/analyze_coverage.py`, `backend/tools/devops/coverage_auditor.py`, এবং আগের `COVERAGE_90_PLAN.md`।

আর সবচেয়ে গুরুত্বপূর্ণ: পুরোনো coverage plan-এ `core`, `tools`, `services`, `api`, `models` আলাদা করে মাপা হচ্ছে; সেই baseline-এ `core` ছিল ~68%, `tools` ~59%, `services` ~51%, `api` ~50%, আর `models` ~90%।

তাই **শুধু overall 35% gate রাখা যথেষ্ট নয়।**

---

# আমার recommended policy

আপনার proposed:

> Core <80% → fail
> Overall <30% → fail
> Critical paths <95% → fail

**আমি এটাকে সামান্য পরিবর্তন করে এই policy করব:**

| Gate                        |                PR এখন | Long-term |
| --------------------------- | --------------------: | --------: |
| **Overall line coverage**   |              **≥30%** |      70%+ |
| **Core module coverage**    |              **≥80%** |      90%+ |
| **Critical-path tests**     |              **≥95%** |      100% |
| **Critical-path execution** |              Required |  Required |
| **New/changed core code**   |                  ≥80% |      ≥90% |
| **Branch coverage**         | Report-only initially |      70%+ |

### কেন Overall 30%?

কারণ এখনই overall-কে 60–80% mandatory করলে আপনার existing codebase-এর ওপর huge test-writing burden পড়বে।

**30% হলো floor, target নয়।**

অর্থাৎ:

> `30%` = "project dangerously untested হয়ে যাচ্ছে না"

আর:

> `80%/90%` = "important logic যথেষ্ট protected"

---

# সবচেয়ে গুরুত্বপূর্ণ পরিবর্তন: "Core" hardcoded folder নয়

আমি চাই না agent এমন কিছু বানাক:

```text
core/** = critical
```

কারণ SupremeAI evolve করবে।

আজ `core/llm_router.py` critical, কাল নতুন `services/model_gateway.py` critical হতে পারে।

তাই একটি **Coverage Policy Registry** থাকবে।

যেমন:

```text
coverage/
├── policy.yaml
├── critical_paths.yaml
└── README.md
```

এখানে classification থাকবে:

```yaml
tiers:
  critical:
    threshold: 80

  important:
    threshold: 60

  standard:
    threshold: 30
```

এবং module mapping:

```yaml
critical:
  - backend/core/llm/**
  - backend/core/security/**
  - backend/api/auth/**
  - backend/services/memory/**
```

**কিন্তু actual paths repository audit করে agent নির্ধারণ করবে।**

---

# SupremeAI Coverage Classification

বর্তমান architecture এবং existing coverage plan দেখে আমি এই hierarchy recommend করছি।

## 🔴 Tier 1 — CRITICAL

Target:

**≥80% এখন**
**≥90% long-term**

### 1. AI/LLM orchestration

```text
core/llm/
core/orchestration/
core/agent*
```

বিশেষ করে:

* LLM routing
* provider selection
* fallback
* token accounting
* model selection
* agent execution

Existing plan-এ `core/llm_router.py`-এর coverage ~57% ছিল—এটা clear priority।

---

### 2. Security

```text
core/security/
api/auth/
authentication
authorization
secret handling
API key validation
```

এখানে coverage percentage-এর পাশাপাশি **negative tests** mandatory হবে।

যেমন:

```text
valid token
expired token
invalid token
wrong role
missing permission
malformed request
```

---

### 3. API / request boundary

```text
api/
api/routes/
middleware
```

কিন্তু পুরো `api/`-কে blindly critical করা হবে না।

Critical:

```text
auth
agent execution
model invocation
billing
quota
API keys
security
```

---

### 4. Usage / quota / billing

Existing coverage plan-এ `billing_api.py` এবং `tenant_admin.py` low coverage ছিল।

এগুলোতে:

**≥90% preferred**

কারণ এখানে bug হলে financial/data integrity problem হতে পারে।

---

### 5. Database/service boundary

```text
services/
repositories/
database/
```

বিশেষ করে:

```text
user
tenant
conversation
memory
usage
billing
configuration
```

---

### 6. Agent/tool execution

SupremeAI-এর agentic nature-এর কারণে:

```text
tool execution
parallel execution
task queue
checkpoint
retry
fallback
sandbox
```

এগুলোও critical।

Existing plan-এ `parallel_agent_executor`, `checkpoint_manager`, `task_queue_enhanced`, `microvm_sandbox`-এর মতো modules আলাদা করে test করার কথা আছে।

---

# 🟠 Tier 2 — IMPORTANT

Target:

**≥60% এখন**

**≥75–85% long-term**

এখানে থাকবে:

```text
tools/
services/
automation
workflow integrations
knowledge/RAG
memory integrations
browser integrations
admin functionality
non-critical API routes
```

Existing plan-এ `services/memory_service.py` এবং `tools/knowledge/local_search_rag.py`-এর coverage যথাক্রমে ~35% এবং ~25% ছিল—এগুলো Tier 2 থেকে gradually Tier 1-এর দিকে উঠতে পারে যদি production path-এ heavily used হয়।

---

# 🟢 Tier 3 — STANDARD

Target:

**≥30%**

যেমন:

```text
simple utilities
CLI helpers
development tools
documentation tooling
scripts
non-critical admin helpers
formatters
migration helpers
```

এখানে 80–90% chase করা unnecessary।

---

# ⚪ Tier 4 — EXCLUDED

Coverage থেকে বাদ যাবে:

```text
generated code
migration artifacts where appropriate
vendored code
static assets
configuration-only files
type-only declarations
test files
unreachable platform-specific code
```

তবে:

**"coverage বাড়ানোর জন্য exclude" করা যাবে না।**

শুধু legitimate exclusion।

---

# Critical Path আসলে কী?

এখানে একটা খুব গুরুত্বপূর্ণ distinction আছে।

**Critical-path coverage ≠ line coverage.**

এটা হবে **end-to-end/business-flow verification**।

আমি SupremeAI-তে প্রথমে এই flows define করব:

### CP-01 Authentication

```text
User
 ↓
Login
 ↓
Authentication
 ↓
Session/token
 ↓
Authorized dashboard
```

---

### CP-02 AI Chat

```text
User request
 ↓
API
 ↓
Auth
 ↓
Model selection
 ↓
LLM provider
 ↓
Response
 ↓
Usage tracking
 ↓
Conversation persistence
```

---

### CP-03 Agent execution

```text
User
 ↓
Agent request
 ↓
Planner/orchestrator
 ↓
Tool selection
 ↓
Tool execution
 ↓
Result
 ↓
Final response
```

---

### CP-04 Failure/fallback

```text
Primary provider fails
 ↓
Retry
 ↓
Fallback provider
 ↓
Response
```

---

### CP-05 Quota/usage

```text
Request
 ↓
Quota check
 ↓
Execution
 ↓
Usage calculation
 ↓
Persistence
```

---

### CP-06 Admin/security

```text
Admin login
 ↓
Role validation
 ↓
Protected operation
 ↓
Audit/result
```

---

### CP-07 Automation

আপনার existing automation architecture-এর কারণে:

```text
Workflow
 ↓
Trigger
 ↓
Execution
 ↓
Queue
 ↓
Retry
 ↓
Success / failure
```

এটাও critical path হওয়া উচিত।

আপনার বর্তমান codebase-এ automation/workflow abstraction ইতিমধ্যেই রয়েছে—তাই এগুলো rebuild না করে **test-hardening** করা উচিত।

---

# Critical Path 95% কীভাবে measure হবে?

এখানে আমি **95% line coverage** ব্যবহার করব না।

বরং:

```text
Critical paths defined = 20

Passing critical paths = 19

19 / 20 = 95%
```

অর্থাৎ 20টি mandatory business flow-এর মধ্যে অন্তত 19টি green হতে হবে।

কিন্তু আরও ভালো:

```text
Critical path test suite
        +
failure-path tests
        +
security assertions
        +
data-integrity assertions
```

সবগুলো pass করতে হবে।

---

# আপনার CI architecture

আমি final pipeline এমন করব:

```text
                    Git Push / PR
                         │
                         ▼
                ┌─────────────────┐
                │ Static Checks   │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │ Unit Tests      │
                └────────┬────────┘
                         ▼
              ┌──────────────────────┐
              │ Coverage Collection  │
              └──────────┬───────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
       Overall       Core         Critical
        ≥30%        ≥80%          ≥95%
            │            │            │
            └────────────┼────────────┘
                         ▼
                   QUALITY GATE
                         │
                ┌────────┴────────┐
                │                 │
              PASS              FAIL
                │                 │
                ▼                 ▼
             Merge            Block PR
```

---

# আরও একটি গুরুত্বপূর্ণ gate যোগ করব

আপনার proposal-এ এটি missing:

## Changed-code coverage

ধরুন existing repository:

```text
Overall = 75%
```

কিন্তু developer নতুন critical module লিখল:

```text
new code = 8%
```

এবং test coverage:

```text
new code = 10%
```

Overall এখনও 74% থাকবে।

তাহলে CI pass করবে—যদিও নতুন code practically untested।

এটা dangerous।

তাই:

### New/changed critical code

**≥80%**

### New/changed normal code

**≥60%**

এটা খুব effective quality gate।

---

# Coverage policy-এর final version

আমি SupremeAI-এর জন্য এই matrix recommend করছি:

| Gate                     | PR Requirement | Release Requirement |
| ------------------------ | -------------: | ------------------: |
| Overall coverage         |       **≥30%** |                ≥70% |
| Critical modules         |       **≥80%** |                ≥90% |
| Important modules        |           ≥60% |                ≥80% |
| Critical paths           |       **≥95%** |            **100%** |
| Changed critical code    |       **≥80%** |                ≥90% |
| Changed normal code      |           ≥60% |                ≥75% |
| Critical branch coverage |         report |                ≥80% |
| Critical security tests  |      100% pass |           100% pass |
| Regression suite         |      100% pass |           100% pass |

---

# Implementation Plan

নিচের plan-টাই আমি agent-কে দেব।

# SUPREMEAI — Multi-Layer Test Coverage & Quality Gate Implementation Plan

## 1. Objective

Replace the existing single overall-coverage gate with a multi-dimensional quality system.

### Current problem

The project currently relies too heavily on one global coverage percentage. This can hide untested critical modules when large amounts of low-risk code inflate the total codebase.

### New philosophy

SupremeAI must measure:

1. Overall repository coverage
2. Core/critical module coverage
3. Important module coverage
4. Critical business-path test health
5. New/changed-code coverage
6. Critical branch/security behavior

Coverage percentage is a quality signal, not a substitute for meaningful tests.

---

# 2. Mandatory Quality Gates

## PR Gate

A pull request must fail when any of these conditions is true:

```text
Overall line coverage < 30%
Critical module coverage < 80%
Critical-path pass rate < 95%
Changed critical code coverage < 80%
Changed normal code coverage < 60%
Critical/security regression tests fail
```

## Release Gate

Production/release validation should require:

```text
Overall line coverage >= 70%
Critical module coverage >= 90%
Important module coverage >= 80%
Critical-path pass rate = 100%
Changed critical code coverage >= 90%
Changed normal code coverage >= 75%
Critical security tests = 100% pass
```

---

# 3. Coverage Tiers

## Tier 1 — CRITICAL

Target:

```text
PR: >=80%
Release: >=90%
```

Candidate areas:

```text
backend/core/llm/**
backend/core/orchestration/**
backend/core/security/**
backend/api/auth/**
backend/api/routes/agent*
backend/api/routes/api_keys*
backend/api/routes/billing*
backend/services/usage*
backend/services/memory*
backend/core/queue/**
backend/tools/checkpoint_manager*
backend/tools/parallel_agent_executor*
backend/core/microvm_sandbox*
```

Do not blindly assume every file under these directories is critical.

The final classification must be based on actual runtime/business responsibility.

---

# 4. Tier 2 — IMPORTANT

Target:

```text
PR: >=60%
Release: >=80%
```

Candidate areas:

```text
backend/services/**
backend/tools/**
backend/api/routes/**
backend/tools/knowledge/**
automation/workflow integrations
RAG/memory integrations
browser integrations
admin functionality
```

Promote a Tier 2 module to Tier 1 when it becomes part of a critical production path.

---

# 5. Tier 3 — STANDARD

Target:

```text
PR: >=30%
Release: >=50–60%
```

Examples:

```text
simple utilities
CLI helpers
development scripts
documentation tooling
non-critical helpers
```

Do not waste engineering time forcing these modules to 90–100% coverage.

---

# 6. Tier 4 — LEGITIMATE EXCLUSIONS

Coverage may exclude only genuinely non-executable or non-testable material.

Allowed examples:

```text
generated code
vendored code
static assets
type-only declarations
test code
physically unreachable platform-specific code
```

Never exclude production code merely because it is difficult to test.

Every exclusion must have a documented reason.

---

# 7. Coverage Policy Registry

Create a single source of truth:

```text
coverage/
├── policy.yaml
├── critical_paths.yaml
└── README.md
```

## policy.yaml

Store:

```yaml
version: 1

thresholds:
  overall:
    pr: 30
    release: 70

  critical:
    pr: 80
    release: 90

  important:
    pr: 60
    release: 80

  changed:
    critical: 80
    standard: 60

  release_changed:
    critical: 90
    standard: 75

  critical_paths:
    pr: 95
    release: 100
```

Do not hardcode these values in Python or GitHub Actions.

CI must read the policy file.

This keeps the system maintainable and allows thresholds to change without modifying the test runner.

---

# 8. Module Classification

Create a machine-readable classification file.

Example:

```yaml
critical:
  - backend/core/llm/**
  - backend/core/security/**
  - backend/core/orchestration/**
  - backend/api/auth/**
  - backend/services/usage/**

important:
  - backend/services/**
  - backend/tools/**
  - backend/api/routes/**

standard:
  - scripts/**
```

The implementation agent MUST audit the current repository before finalizing these mappings.

Do not duplicate paths unnecessarily.

Do not classify a directory as critical merely because its name contains "core".

---

# 9. Critical Paths

Create:

```text
coverage/critical_paths.yaml
```

Initial required flows:

```yaml
critical_paths:

  - id: CP-01
    name: authentication
    required: true

  - id: CP-02
    name: ai_chat
    required: true

  - id: CP-03
    name: agent_execution
    required: true

  - id: CP-04
    name: provider_failure_fallback
    required: true

  - id: CP-05
    name: usage_quota
    required: true

  - id: CP-06
    name: admin_authorization
    required: true

  - id: CP-07
    name: automation_execution
    required: true
```

Expand this list only after auditing actual production flows.

---

# 10. Critical Path Definition

A critical path is NOT simply a source file.

It is a user/business flow.

Each critical path must test:

```text
happy path
validation
authorization
failure behavior
external dependency failure
persistence
expected result
```

For AI flows additionally test:

```text
provider selection
fallback
timeout
retry
usage accounting
response persistence
```

---

# 11. Critical Path Scoring

The CI script should calculate:

```text
passed required critical paths
-------------------------------- × 100
total required critical paths
```

Example:

```text
19 / 20 = 95%
```

If:

```text
score < configured threshold
```

CI fails.

For release:

```text
score must equal 100%
```

---

# 12. Existing Coverage Infrastructure

Do NOT rebuild the existing coverage system from scratch.

Audit and reuse:

```text
backend/.coveragerc
backend/analyze_coverage.py
backend/tools/devops/coverage_auditor.py
scripts/quality/auto_improve_coverage.py
backend/tools/devops/auto_coverage_improver.py
```

The repository already contains coverage tooling, so the objective is to consolidate and harden it rather than create duplicate systems.

---

# 13. Coverage Collection

Backend coverage should continue using the existing pytest/coverage infrastructure.

Required reports:

```text
terminal
XML
JSON
HTML
```

The JSON report should be the machine-readable source for custom policy evaluation.

Example:

```bash
pytest \
  --cov=. \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=json \
  --cov-report=xml
```

Use the repository's existing package manager and test commands rather than inventing a new environment.

---

# 14. Coverage Evaluator

Create or consolidate into one evaluator:

```text
scripts/quality/check_coverage_policy.py
```

Responsibilities:

```text
1. Load coverage/policy.yaml
2. Load module classification
3. Read coverage.json
4. Calculate overall coverage
5. Calculate critical coverage
6. Calculate important coverage
7. Calculate changed-code coverage
8. Read critical-path results
9. Apply thresholds
10. Produce human-readable report
11. Exit non-zero on failure
```

Do not duplicate threshold logic in multiple scripts.

---

# 15. Critical Module Calculation

Do not calculate critical coverage as:

```text
average(file percentages)
```

Use weighted line coverage:

```text
covered executable lines
----------------------- × 100
total executable lines
```

This prevents a 10-line file from having the same weight as a 1,000-line file.

---

# 16. Changed-Code Coverage

For every PR:

```text
git diff base...HEAD
```

Identify changed executable lines.

Calculate:

```text
covered changed lines
--------------------- × 100
changed executable lines
```

Apply:

```text
critical changed code >= 80%
standard changed code >= 60%
```

This prevents new untested code from being hidden by existing repository coverage.

---

# 17. Critical-Path Test Layout

Prefer a clear structure:

```text
backend/tests/
├── unit/
├── integration/
├── critical_paths/
│   ├── test_authentication.py
│   ├── test_ai_chat.py
│   ├── test_agent_execution.py
│   ├── test_provider_fallback.py
│   ├── test_usage_quota.py
│   ├── test_admin_authorization.py
│   └── test_automation_execution.py
```

Use the existing repository test structure if equivalent directories already exist.

Do not duplicate existing tests.

---

# 18. Test Quality Rules

A test must verify behavior.

Bad:

```python
result = function()
assert result is not None
```

Good:

```python
result = function()
assert result.status == "success"
assert result.model == expected_model
assert usage_record.tokens == expected_tokens
```

Coverage-only tests are prohibited.

---

# 19. Required Critical Test Categories

Every critical module should cover:

### Happy path

```text
valid input
expected result
```

### Validation

```text
missing input
invalid input
boundary input
```

### Authorization

```text
unauthenticated
wrong role
missing permission
```

### Failure

```text
timeout
provider failure
database failure
queue failure
external API failure
```

### Recovery

```text
retry
fallback
rollback
idempotency
```

### Persistence

```text
correct data
duplicate prevention
transaction behavior
```

---

# 20. Branch Coverage

Do not make 100% branch coverage a PR gate initially.

Initially:

```text
branch coverage = report
```

Later:

```text
critical modules >=80%
```

Recommended long-term:

```text
critical branch coverage >=80%
overall branch coverage >=70%
```

Prioritize branches involving:

```text
authentication
authorization
failure handling
provider fallback
quota
billing
security
data mutation
```

---

# 21. Existing Low-Coverage Priorities

Use the existing coverage report rather than blindly writing tests for every file.

The current/previous coverage plan identifies important gaps including:

```text
api/routes/admin_dashboard.py
api/routes/billing_api.py
api/routes/tenant_admin.py
api/routes/api_keys.py
core/llm_router.py
core/queue/task_queue_enhanced.py
services/memory_service.py
tools/parallel_agent_executor.py
tools/checkpoint_manager.py
core/microvm_sandbox.py
```

These should be re-measured against the current HEAD before assigning work.

---

# 22. Test Priority Algorithm

Do NOT simply test the largest files first.

Priority should be:

```text
Business criticality
        ×
Security risk
        ×
Runtime frequency
        ×
Failure impact
        ×
Coverage gap
```

Suggested priority:

```text
P0 = security / auth / billing / quota / data integrity
P1 = AI routing / agent execution / critical APIs
P2 = memory / automation / tools / integrations
P3 = admin / secondary services
P4 = utilities / scripts
```

---

# 23. CI Jobs

Create logical CI stages:

```text
quality
├── lint
├── typecheck
├── unit-tests
├── backend-coverage
├── critical-path-tests
├── changed-code-coverage
└── quality-gate
```

The final gate should depend on all required jobs.

---

# 24. Failure Output

A failed CI run must clearly say:

```text
SUPREMEAI QUALITY GATE: FAILED

Overall coverage:
  28.7% / 30%   FAIL

Critical coverage:
  76.4% / 80%   FAIL

Critical paths:
  20/20 = 100%  PASS

Changed critical code:
  91% / 80%     PASS

Reason:
  Critical module coverage is below the PR threshold.

Action:
  Add tests for the affected critical modules.
```

Never return only:

```text
Coverage failed
```

---

# 25. PR Comment / Summary

Generate a concise summary:

```text
Overall:              43.2%  PASS
Critical:             86.7%  PASS
Important:            64.1%  PASS
Critical paths:       100%   PASS
Changed critical:     91.4%  PASS
Changed standard:     73.2%  PASS

QUALITY GATE: PASS
```

---

# 26. Regression Protection

Add a regression rule:

A PR must not reduce:

```text
critical coverage
critical-path pass rate
security test health
```

below the configured baseline.

Example:

```text
main critical coverage = 86%

PR critical coverage = 82%

absolute threshold = 80%
```

Even though 82% passes the absolute threshold, the system should report:

```text
WARNING: critical coverage decreased by 4 percentage points
```

For mature/release branches this can become a failure.

---

# 27. No Hardcoded Infrastructure Assumptions

Do not hardcode:

```text
service URLs
provider names
database URLs
Redis URLs
environment-specific paths
credentials
deployment endpoints
```

The coverage system should only depend on repository-local configuration and CI environment variables where required.

This follows the project's existing preference for environment-driven infrastructure.

---

# 28. Lightweight Implementation

Do not add heavyweight dependencies merely for coverage policy.

Prefer the tooling already present in the repository.

For example:

```text
pytest
coverage.py
existing CI tooling
standard-library YAML/JSON handling where possible
```

If YAML parsing already exists, reuse it.

Do not introduce a new framework just to evaluate three percentages.

---

# 29. Migration Strategy

## Phase 0 — Audit

Before changing CI:

```text
1. Inspect current coverage workflow
2. Inspect .coveragerc
3. Inspect existing coverage scripts
4. Generate fresh coverage.json
5. Identify current critical modules
6. Identify existing critical-path tests
7. Identify duplicate coverage tooling
```

Deliver:

```text
coverage/current-baseline.json
coverage/current-baseline.md
```

---

## Phase 1 — Policy Registry

Implement:

```text
coverage/policy.yaml
coverage/critical_paths.yaml
```

No CI behavior change yet.

---

## Phase 2 — Evaluator

Implement/consolidate:

```text
scripts/quality/check_coverage_policy.py
```

Run locally.

Expected output:

```text
overall
critical
important
changed
critical paths
PASS/FAIL
```

---

## Phase 3 — Shadow Mode

Run the new policy in CI without blocking merges.

For approximately 5–10 successful CI runs:

```text
old gate = authoritative
new gate = report only
```

This allows false classifications and flaky critical paths to be discovered.

---

## Phase 4 — Enable PR Gates

Switch to:

```text
overall >=30%
critical >=80%
critical paths >=95%
changed critical >=80%
changed standard >=60%
```

Remove the old single:

```text
overall <35% => fail
```

rule.

There should be one authoritative quality gate.

---

## Phase 5 — Raise Targets Gradually

Once the repository becomes stable:

```text
Overall:
30 → 40 → 50 → 60 → 70

Critical:
80 → 85 → 90

Critical paths:
95 → 100
```

Never raise a threshold merely because a target looks nice.

Raise it after actual coverage improvements.

---

# 30. Anti-Gaming Rules

The system must detect/prevent:

```text
# pragma: no cover
```

abuse.

Also prevent:

```text
moving code into excluded folders
deleting tests
excluding large production modules
writing meaningless tests
mocking the entire function under test
```

Every exclusion should be reviewable.

---

# 31. Definition of Done

The implementation is complete only when:

* [ ] Policy registry exists
* [ ] Critical-path registry exists
* [ ] Current coverage baseline generated
* [ ] Existing coverage tooling audited
* [ ] Duplicate evaluators consolidated
* [ ] Overall coverage calculated
* [ ] Critical coverage calculated
* [ ] Important coverage calculated
* [ ] Changed-code coverage calculated
* [ ] Critical-path score calculated
* [ ] CI quality gate implemented
* [ ] PR output implemented
* [ ] Legitimate exclusions documented
* [ ] Coverage gaming protections implemented
* [ ] Existing tests continue to pass
* [ ] New gate runs in shadow mode successfully
* [ ] Old 35% single gate removed
* [ ] Documentation updated

---

# 32. Final Quality Philosophy

SupremeAI should NOT optimize for:

> "highest possible coverage percentage"

It should optimize for:

> "highest confidence in the code that can actually hurt users, data, security, money, or AI execution."

Therefore:

```text
                TESTING PRIORITY

        Critical business behavior
                    ▲
                    │
              Security/Auth
                    │
            AI/Agent execution
                    │
          Data/Quota/Billing
                    │
         API/Service boundaries
                    │
              Integrations
                    │
               Utilities
                    │
             Low-risk code
```

The final goal is:

```text
Overall coverage        → healthy
Critical coverage       → very high
Critical paths          → fully protected
Changed code            → tested before merge
Security paths          → never regress
```

This is preferable to blindly forcing 100% repository-wide line coverage.

**Bottom line:** আপনার idea সঠিক, কিন্তু আমি **`30% overall + 80% core + 95% critical path`-এর সাথে `changed-code coverage` gate অবশ্যই যোগ করব।** এটা না থাকলে পুরোনো 70% covered code নতুন 5%-covered code-কে লুকিয়ে ফেলতে পারে।

আর আপনার repository-তে যেহেতু আগে থেকেই একটি aggressive **100% coverage plan** এবং coverage tooling আছে, নতুন plan-এর উদ্দেশ্য সেই infrastructure আবার বানানো নয়—বরং **existing tooling consolidate করে business-risk-based quality gate বানানো**। পুরোনো plan-এর baseline-ও দেখাচ্ছে যে `core`, `tools`, `services`, `api`-র coverage একরকম নয়, তাই single global percentage দিয়ে quality বিচার করা যথেষ্ট নয়।

[SupremeAI GitHub repository](https://github.com/SaifulHaqueNiloy/supremeai?utm_source=chatgpt.com)
