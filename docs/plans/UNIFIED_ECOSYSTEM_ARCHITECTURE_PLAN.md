# SupremeAI Unified Ecosystem Architecture — Master Execution Plan

**Document Version:** 2.0.0  
**Status:** Active Master Architecture & Execution Plan  
**Location:** `docs/plans/UNIFIED_ECOSYSTEM_ARCHITECTURE_PLAN.md`  
**Scope:** Current architecture → target architecture → implementation order → architecture governance  
**Primary principle:** **Consolidate what already works; canonicalize contracts; connect capabilities; then evolve.**

> This document replaces the old "design from scratch" interpretation of the ecosystem plan. SupremeAI already has a substantial production-oriented architecture. The goal is **not** to rebuild it or introduce parallel subsystems. The goal is to make the existing capabilities coherent, observable, composable, resource-efficient, and progressively production-ready.

---

## 1. Executive Decision

### 1.1 What is already strong

The current SupremeAI architecture already provides a strong capability foundation:

- Chat / Workspace / Files / Projects / Agents / IDE / Integrations / Research / Memory / Scheduled Tasks / Settings / Billing surfaces.
- A separate Admin hierarchy with `AdminShell` and role protection.
- Existing MCP-oriented orchestration and capability discovery.
- Existing Central MCP Dependency Graph concepts using `system_dependencies` and related platform summaries/health checks.
- Existing memory infrastructure and vector/RAG foundations.
- Existing Playwright-based browser automation plus a lightweight HTTP scraping path.
- Mission / agent orchestration and HITL-oriented execution concepts.
- Production-oriented API, health/readiness, authentication/CSRF, tenant isolation and platform operations foundations.
- A machine-readable QA contract and CI automation covering build, security, MCP, constitution, parity and deployment preflight concerns.
- Existing Render/GitHub/Cloudflare/Infisical/Supabase/Redis/provider integrations that should be composed rather than duplicated.

The repository's architecture documentation already identifies `system_dependencies` as part of the active Central MCP Dependency Graph and uses it for dependency/status analysis and blast-radius thinking. fileciteturn15file0 fileciteturn15file1

The release/QA surface also already contains a dedicated `qa-contract.yml` workflow and machine-readable QA contract rather than relying exclusively on manual checking. fileciteturn16file0 fileciteturn16file1

### 1.2 What the ecosystem plan adds

The strategic ecosystem work adds the missing **architecture coherence layer**:

1. Canonical execution model: **Run**.
2. Canonical context model: **Context Engine**.
3. Canonical memory lifecycle rather than another memory backend.
4. Browser execution abstraction over the existing browser foundation.
5. Static + runtime architecture graph.
6. Automated blast-radius and architecture-diff governance.
7. Lightweight-first resource policy.
8. Lazy capability discovery to control model/tool context size.
9. Artifact/reference passing for large payloads.
10. Architecture-aware AI-agent workflow before code changes.
11. Optional skill ecosystems without contaminating the core platform.
12. Continuous QA/release gates as architecture governance, not a final manual step.

### 1.3 Final strategic decision

**Do not rebuild SupremeAI.**

Use this transformation:

```text
CURRENT CAPABILITIES
       ↓
CONSOLIDATE DUPLICATES
       ↓
CANONICAL CONTRACTS
       ↓
CONNECT EXISTING SYSTEMS
       ↓
ARCHITECTURE / QA GOVERNANCE
       ↓
PRODUCTION HARDENING
       ↓
CONTROLLED EVOLUTION
```

---

## 2. Target Architecture

SupremeAI remains a federated/hybrid platform, but the **Run + Context + Capability + Architecture** contracts become the organizing backbone.

```text
                         ┌───────────────────────────┐
                         │       USER / DEVELOPER    │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                 ┌────────────────────────────────────────┐
                 │ FRONTEND / CHAT / IDE / ADMIN          │
                 │ "The Face" — outcome + observability  │
                 └──────────────────┬─────────────────────┘
                                    │
                                    ▼
                 ┌────────────────────────────────────────┐
                 │        CONTROL / ORCHESTRATION         │
                 │ MCP Gateway + Policy + Discovery       │
                 │ Lightweight control plane              │
                 └──────────────┬───────────────┬─────────┘
                                │               │
                     ┌──────────▼──────┐  ┌────▼──────────┐
                     │  CONTEXT ENGINE │  │ CANONICAL RUN │
                     │ Files / Memory  │  │ Mission/Agent │
                     │ Workspace / RAG │  │ Tool/MCP/Code │
                     └──────────┬──────┘  └────┬──────────┘
                                │              │
                                └──────┬───────┘
                                       ▼
                    ┌────────────────────────────────┐
                    │       CAPABILITY CIRCLES       │
                    │ Code │ Cloud │ Knowledge       │
                    │ Auth │ Agent │ Browser │ ...   │
                    └───────────────┬────────────────┘
                                    │
                       ┌────────────┼────────────┐
                       ▼            ▼            ▼
                    Workers      Services      External
                    /Tools       /Modules       Systems

 Cross-cutting across every layer:
 Security • Policy • Tenancy • Permissions • Audit
 Observability • Cost • Token Budget • Rate Limits
 QA • Architecture Graph • Release Gates • Recovery
```

### 2.1 The four canonical planes

| Plane | Canonical responsibility | Rule |
|---|---|---|
| **Experience Plane** | Chat, IDE, customer workspace, admin mission center | Observe/request/approve; do not own hidden orchestration logic |
| **Control Plane** | MCP gateway, policy, routing, discovery, metadata | Lightweight; never carry large payloads |
| **Execution/Data Plane** | Runs, workers, tools, browser, code, storage, artifacts | Own actual computation and heavy payloads |
| **Architecture Plane** | Static graph, runtime graph, contracts, blast radius, QA evidence | Continuously verifies that the other planes remain coherent |

---

## 3. Core Architectural Constitution

### Rule 1 — Reuse Before Creation

Before creating a module, service, tool, worker, database table, API, or abstraction:

1. Search the repository.
2. Search the architecture graph.
3. Identify an existing capability that can be extended/composed.
4. Prefer adaptation over duplication.
5. Add a new subsystem only when an explicit architectural reason exists.

### Rule 2 — No New Parallel Subsystem

A new implementation must not silently create a second:

- memory system,
- RAG system,
- browser system,
- execution/run system,
- dependency graph,
- tool registry,
- artifact store,
- auth/tenant boundary,
- provider abstraction,
- QA gate.

If two systems already solve the same problem, the plan must first decide which becomes canonical and how the other is migrated, adapted, or retired.

### Rule 3 — Canonical Run

Every meaningful execution should converge on one Run contract.

```text
Mission
Agent
Tool
MCP
Browser
Code
Research
Scheduled Task
        │
        ▼
   CANONICAL RUN
        │
   ┌────┼───────────────┐
   ▼    ▼               ▼
Steps  Events        Artifacts
   │    │               │
   └────┴───────┬───────┘
                 ▼
              Result
```

A Run owns or references:

- run ID,
- tenant/workspace/project context,
- initiating actor,
- capability/tool selected,
- policy decision,
- lifecycle state,
- step/event history,
- retries and failure classification,
- approvals/HITL checkpoints,
- resource/time/token budgets,
- artifact references,
- final result,
- audit metadata.

### Rule 4 — Canonical Context Engine

All agent context should converge through a Context Engine instead of independently assembling arbitrary prompt payloads.

```text
Workspace
   ├── Project
   │    ├── Files
   │    ├── Docs
   │    └── Artifacts
   ├── Memory
   ├── Chat
   └── Run
          │
          ▼
   Context Engine
          │
     ┌────┼────┐
     ▼    ▼    ▼
    L0   L1   L2
  summary relevant detailed
          │
          ▼
       Agent Context
```

The L0/L1/L2 idea is an OpenViking-inspired optimization, **not** a requirement to introduce a second context database. SupremeAI's existing Files, Memory, Workspace and RAG infrastructure remains the source of truth.

### Rule 5 — Lightweight First

For every capability:

```text
Cheap/local/lightweight path
          ↓
Does it solve the task?
     ┌────┴────┐
    YES       NO
     │         │
   Finish   Heavy path
             ↓
       isolated worker
```

Examples:

- HTTP/HTML extraction before Playwright.
- Metadata/reference passing before full payload transfer.
- Lazy tool discovery before exposing the full tool catalog.
- Optional dependency groups before loading heavy provider/browser/ML packages into the API process.

### Rule 6 — Control Plane Never Carries Heavy Payloads

Large logs, AST dumps, screenshots, downloaded files, embeddings batches, browser artifacts and similar payloads move through artifact/reference storage.

```text
Worker → Artifact Store → ref://...
Worker → Control Plane: metadata + reference
Control Plane → Consumer: reference
Consumer → Artifact Store: fetch when needed
```

### Rule 7 — Modules Own Execution; Circles Own Domains

The existing federated Circle concept remains valuable:

- Circle Lead exposes a stable domain contract.
- Member modules own their implementation.
- Peer modules do not create direct spaghetti coupling.
- Cross-domain composition occurs through canonical orchestration/contracts.

### Rule 8 — Dynamic Discovery, Not Hardcoded Examples

Examples such as Gemini, Grok, Ollama, Cursor, Cline, Claude Code, Render, AWS, Qdrant, etc. are **capability examples**, not fixed architectural bounds.

All resource discovery should support `1..N` resources and capability-based selection.

### Rule 9 — Frontend Is the Face, Not the Brain

The frontend remains outcome-focused for customers and mission-control focused for administrators.

It may display:

- status,
- progress,
- approvals,
- artifacts,
- summaries,
- health,
- governance state.

It must not become the hidden source of truth for orchestration, policy, secrets or execution state.

### Rule 10 — Every Module Has a Contract

Every significant module must document:

- generalized purpose,
- owner/domain,
- inputs/outputs,
- lifecycle,
- dependencies,
- failure modes,
- security boundary,
- resource profile,
- observability,
- replacement/deprecation path.

---

## 4. Capability Circles

The Circle model remains the domain-level federation mechanism. The exact membership can evolve dynamically.

| ID | Circle | Responsibility | Existing/Expected Capabilities |
|---|---|---|---|
| C1 | Code & Quality | analysis, review, syntax, formatting, verification | Trio / adaptive multi-agent assembly, Ruff, Flake8, Actionlint |
| C2 | Cloud & Infrastructure | deploy, routing, cache, secrets, infrastructure | Render, Cloudflare, Redis, Infisical |
| C3 | Knowledge & Memory | retrieval, memory, embeddings, learning | Supabase/pgvector, existing memory, optional vector services |
| C4 | Auth, Tenancy & Security | identity, RBAC, RLS, policy, audit | Supabase Auth, Firebase where required, policy engine |
| C5 | Agent Orchestration | planning, agents, missions, verification | Mission/agent orchestration, autonomous loops, review/HITL |
| C6 | Browser & Web | web access, extraction, browser execution | HTTP scraper, Playwright, browser tools, isolated browser worker |
| C7 | Developer / Execution | code execution, IDE-facing tasks, artifacts | code tools, workers, artifact pipeline |
| C8+ | Future capability domains | dynamically discovered domains | added only when justified by capability boundaries |

A Circle is **not** a microservice mandate. It is primarily a domain and governance boundary.

---

## 5. Canonical Context Engine

### 5.1 Objective

Unify:

- Workspace context,
- Files,
- chat history,
- memory,
- RAG,
- project knowledge,
- Run state,
- artifacts.

### 5.2 Context hierarchy

```text
GLOBAL
  ↓
USER
  ↓
WORKSPACE
  ↓
PROJECT
  ↓
CHAT
  ↓
RUN
  ↓
STEP
```

Each context item should have:

- scope,
- source/provenance,
- timestamp/lifecycle,
- relevance/confidence where applicable,
- security/tenant boundary,
- token/cost estimate,
- retention policy.

### 5.3 Context budgeter

Before sending context to a model:

1. calculate available budget;
2. select L0 summary;
3. add high-relevance L1 context;
4. fetch L2 only when required;
5. remove duplicates;
6. enforce tenant/security scope;
7. emit context provenance.

Success is not "more context". Success is **the smallest sufficient context that reliably solves the task**.

---

## 6. Memory Consolidation

SupremeAI already has memory/vector/RAG foundations. The ecosystem plan therefore adopts **agentmemory-style lifecycle concepts without adding a competing memory backend**.

### Canonical lifecycle

```text
Capture → Normalize → Score → Store → Retrieve → Use
                         ↓
                  Update / Decay / Archive
```

Memory should support:

- provenance,
- confidence,
- source Run,
- scope,
- deduplication,
- lifecycle/decay,
- tenant isolation,
- deletion/retention policy.

### Hybrid retrieval

Use the existing vector/RAG direction plus structured metadata/relationships where valuable. Introduce a graph database only when an actual workload requires it; do not add one merely because an OSS project demonstrates the pattern.

---

## 7. Canonical Run & Execution Fabric

This is the highest-priority architectural addition because it becomes the nervous system connecting existing capabilities.

### 7.1 Run lifecycle

```text
REQUESTED
   ↓
POLICY_CHECKED
   ↓
PLANNED
   ↓
RUNNING
   ├── WAITING_APPROVAL
   ├── RETRYING
   ├── DEGRADED
   └── BLOCKED
   ↓
COMPLETED / FAILED / CANCELLED
   ↓
FINALIZED
```

### 7.2 Async boundary

Operations expected to exceed the synchronous request budget should return a Run/task reference rather than holding an HTTP/MCP request open indefinitely.

```text
request
  ↓
policy
  ↓
create run
  ↓
ack + run_id
  ↓
worker execution
  ↓
progress/events
  ↓
artifact refs
  ↓
result
```

The exact queue implementation is an implementation decision; the architecture only requires a durable execution contract.

### 7.3 Retry classification

Retries must be classified rather than blindly repeated:

- transient,
- rate limited,
- dependency unavailable,
- policy blocked,
- invalid input,
- deterministic application failure,
- resource exhausted,
- human approval required.

### 7.4 Resource budgets

Every Run should be able to enforce, where applicable:

- wall-clock limit,
- token budget,
- tool-call budget,
- browser-action budget,
- memory/storage budget,
- retry budget.

---

## 8. Browser Execution Layer

The existing Playwright foundation should be **wrapped and governed**, not blindly replaced.

### 8.1 Unified browser contract

Expose agent-friendly operations such as:

```text
browser.open
browser.click
browser.type
browser.select
browser.extract
browser.screenshot
browser.download
browser.wait
```

These are logical capabilities; existing implementation details may remain Playwright-based.

### 8.2 Routing policy

```text
Task
 ↓
Can HTTP/static extraction solve it?
 ├─ YES → lightweight scraper
 └─ NO  → browser execution
              ↓
        isolated browser worker
```

### 8.3 Production rules

- Browser dependencies must not unnecessarily inflate the normal API process.
- Chromium-heavy work should be isolated when resource pressure requires it.
- Browser sessions belong to Runs.
- Session artifacts are referenced, not pushed through the control plane.
- Timeouts, action budgets and cleanup are mandatory.
- Browser capability failures must degrade cleanly without taking down unrelated Circles.

Browser Use is therefore treated as an **interaction-model inspiration**, not as a mandatory replacement dependency.

---

## 9. MCP Control Tower

The original Hub-and-Spoke concept remains, but the Tower is explicitly a **control plane**, not the universal execution engine.

### Tower responsibilities

- capability discovery,
- routing,
- policy/permission checks,
- Run creation,
- Circle dispatch,
- lifecycle metadata,
- health/status,
- event routing,
- artifact references,
- audit metadata.

### Tower must not

- execute heavy AST analysis,
- host Chromium,
- carry multi-megabyte logs,
- load every provider SDK,
- expose hundreds of raw tools to every model by default,
- become a second database for domain state.

### Lazy discovery

```text
Model
 ↓
~small stable gateway surface
 ↓
capability discovery
 ↓
selected Circle
 ↓
selected tool
 ↓
Run
```

This reduces prompt/tool-schema overhead while retaining extensibility.

---

## 10. Artifact & Reference Broker

The platform should standardize references such as:

```text
ref://run/{run_id}/artifact/{artifact_id}
```

Artifact metadata should include, where appropriate:

- owner/tenant,
- Run ID,
- MIME type,
- size,
- checksum,
- retention,
- access policy,
- creation timestamp.

Heavy payloads remain outside the control plane.

---

## 11. Architecture Intelligence Graph

The current `system_dependencies`/system-summary/health direction becomes the foundation of a broader Architecture Intelligence layer rather than being replaced.

### 11.1 Graph sources

```text
Repository structure
      +
TypeScript dependency graph
      +
Python dependency graph
      +
API/service contracts
      +
Database relationships
      +
Runtime dependency observations
      +
CI / deployment metadata
      ↓
UNIFIED ARCHITECTURE GRAPH
```

### 11.2 Static analysis

Preferred tools/patterns:

- GitHub Repo Visualizer / repository structure for orientation.
- Dependency Cruiser for JS/TS dependency edges and boundary rules.
- Pydeps or equivalent for Python dependency visualization.
- Existing `system_dependencies` for runtime/platform dependency state.
- Custom scripts for graph normalization and policy checks.

Archify-style visualization may be useful, but it should not become a second architecture authority.

### 11.3 Required graph capabilities

The architecture system should eventually detect:

- circular dependencies,
- forbidden layer crossings,
- unexpected new edges,
- orphan modules,
- duplicated capability implementations,
- high fan-in/fan-out hotspots,
- service dependency failures,
- blast radius,
- architecture drift,
- static/runtime disagreement.

### 11.4 Baseline policy

Existing technical debt should not block all progress immediately.

```text
main baseline = N known violations
PR creates N   → pass
PR creates N+1 → fail
PR reduces N   → pass + improvement evidence
```

New architectural violations should be blocked even while old debt is being retired gradually.

---

## 12. AI-Agent Architecture-Aware Workflow

Every AI coding agent working on SupremeAI should follow this sequence:

```text
Task
 ↓
Repository search
 ↓
Architecture graph lookup
 ↓
Existing capability check
 ↓
Dependency / blast-radius analysis
 ↓
Relevant QA/test selection
 ↓
Implementation
 ↓
Static graph re-check
 ↓
Tests / lint / build / security
 ↓
QA contract
 ↓
Deployment preflight
 ↓
Evidence
```

### Mandatory agent questions

Before adding a subsystem:

1. Does an existing module already provide this capability?
2. Which Circle owns it?
3. Which Run contract will execute it?
4. Which Context sources does it require?
5. What new dependency edges will it create?
6. What is the blast radius?
7. Which tests and QA checks are affected?
8. Is it lightweight enough for the target runtime?
9. How will it be observed, rolled back or degraded?
10. What is the deprecation path if it becomes obsolete?

---

## 13. QA & Production Governance

Architecture governance must be continuous, not a final checklist.

The repository already has a machine-readable QA contract and CI workflow; this plan makes those checks a permanent part of architecture evolution. fileciteturn16file1

### PR gate

```text
Changed files
   ↓
Architecture diff
   ↓
Dependency diff
   ↓
Cycle / boundary checks
   ↓
Blast radius
   ↓
Affected capability matrix
   ↓
Relevant tests
   ↓
Build / lint / security
   ↓
QA Contract
   ↓
Deploy preflight
```

### Production readiness layers

**Layer A — Contract**

- type/build contracts,
- API contracts,
- env/config contracts,
- MCP contract.

**Layer B — Correctness**

- unit,
- integration,
- E2E,
- workflow tests.

**Layer C — Security**

- auth/RBAC,
- tenant isolation/RLS,
- CSRF,
- dependency scanning,
- secret handling,
- DAST where applicable.

**Layer D — Operational**

- health/readiness,
- telemetry,
- retries,
- resource budgets,
- failure/degraded mode.

**Layer E — Release**

- deployment preflight,
- smoke checks,
- artifact/report evidence,
- rollback/recovery evidence.

The current QA system should be expanded rather than duplicated. Existing evidence shows the repository has dedicated QA-contract and modular CI surfaces, while some broader production/sign-off coverage remains incomplete. fileciteturn16file0

---

## 14. Resource & Dependency Strategy

SupremeAI should remain capable on constrained infrastructure.

### Dependency policy

Classify dependencies as:

```text
CORE
 ├── required by normal API path

OPTIONAL
 ├── browser
 ├── worker
 ├── ML
 ├── provider-specific
 └── observability / specialized tooling
```

Heavy libraries should not be imported into the critical API path merely because another capability may use them.

### Colibrì decision

Do **not** introduce Colibrì into the current roadmap. Its specialized C/MoE disk-streaming problem is not a demonstrated core SupremeAI bottleneck. Revisit only if a measured workload proves the need.

### Specialized skill packs

Cybersecurity and scientific agent skill repositories remain optional extension packs. They should be introduced through a governed skill registry with:

- explicit capability scope,
- permissions,
- tenant boundary,
- resource budget,
- provenance,
- audit trail.

They are not core architecture dependencies.

---

## 15. OSS Integration Policy

| OSS / Concept | Decision | Integration mode | Priority |
|---|---|---|---|
| **OpenViking** | Adopt concepts | Context hierarchy / L0-L2 / virtual context paths over existing storage | P0 |
| **agentmemory** | Adopt concepts | memory lifecycle, provenance, scopes, hybrid retrieval; no second backend | P0/P1 |
| **Browser Use** | Adopt concepts | agent-friendly browser contract over existing Playwright | P1 |
| **Awesome Harness Engineering** | Adopt principles | agent workflow, sandbox/tool boundaries, quality gates | P0 |
| **Diagram Design** | Optional | structured diagram renderer/skill | P2 |
| **Archify** | Selective | visualization ideas only; existing graph remains authoritative | P1/P2 |
| **Colibrì** | Reject for now | revisit only with measured need | P4 |
| **Cybersecurity Skills** | Optional | governed skill pack | P3 |
| **Scientific Agent Skills** | Optional | governed skill pack | P3 |

**Principle:** learn from OSS; do not accumulate OSS projects merely because they are interesting.

---

## 16. Implementation Roadmap — Plan-Driven Order

The execution order is intentionally different from the original document. The original phases were useful, but **Canonical Run must move earlier** because it is the common execution contract for Missions, Agents, Tools, MCP, Browser and Code.

### Phase 0 — Architecture Baseline & Inventory

**Goal:** establish the measured current state before changing architecture.

Tasks:

- inventory existing modules and capabilities;
- map existing Circles;
- capture `system_dependencies` and runtime health;
- generate TS/JS dependency graph;
- generate Python dependency graph;
- map APIs, workers, queues, artifacts and stores;
- identify duplicate subsystems;
- establish architecture baseline;
- define known violations/debt counts.

**Exit criteria:** architecture graph + baseline report + known-debt register.

---

### Phase 1 — Canonical Run Fabric

**Goal:** unify execution semantics without rewriting feature implementations.

Tasks:

- define Run contract/schema;
- connect Mission/Agent execution to Run;
- connect Tool/MCP execution to Run;
- define lifecycle/events;
- define async task boundary;
- define retry classification;
- add cancellation/timeout/resource budgets;
- connect HITL approvals;
- standardize Run artifacts/results.

**Exit criteria:** major execution paths can be observed as Runs without feature duplication.

---

### Phase 2 — Context Engine

**Goal:** unify context assembly.

Tasks:

- define context scopes;
- integrate Workspace/Project/Chat/Files;
- integrate current Memory/RAG;
- implement L0/L1/L2 retrieval strategy;
- add context budgeter;
- attach provenance;
- enforce tenant/security filtering;
- measure token reduction and task quality.

**Exit criteria:** agents receive canonical, budget-aware context rather than independent ad-hoc context assembly.

---

### Phase 3 — Memory Consolidation

**Goal:** make current memory infrastructure canonical and lifecycle-aware.

Tasks:

- map all memory read/write paths;
- remove duplicate memory abstractions where confirmed;
- standardize scopes/provenance/confidence;
- standardize deduplication/lifecycle;
- connect memory writes to completed Runs;
- connect retrieval to Context Engine;
- preserve existing vector/storage contracts unless a measured migration is required.

**Exit criteria:** one authoritative memory path with traceable provenance.

---

### Phase 4 — Browser Execution Layer

**Goal:** standardize browser capability without forcing a rewrite.

Tasks:

- define browser capability contract;
- route lightweight tasks to HTTP extraction;
- route JS-heavy tasks to Playwright;
- attach browser sessions to Runs;
- isolate heavy browser execution where needed;
- standardize screenshots/downloads/artifacts;
- add browser timeout/action budgets;
- add cleanup and degraded-mode behavior.

**Exit criteria:** browser tasks use a single logical capability contract with lightweight-first routing.

---

### Phase 5 — Unified Architecture Intelligence

**Goal:** turn architecture knowledge into an automated control mechanism.

Tasks:

- normalize TS/JS/Python/static graphs;
- ingest runtime `system_dependencies`;
- define architecture rules;
- add cycle detection;
- add boundary checks;
- add changed-edge detection;
- add blast-radius calculation;
- compare static vs runtime topology;
- publish architecture health score.

**Exit criteria:** every significant PR can show architecture impact automatically.

---

### Phase 6 — MCP Gateway & Lazy Discovery Refinement

**Goal:** make the control plane lightweight and model-efficient.

Tasks:

- expose coarse-grained Circle gateway capabilities;
- implement lazy discovery;
- standardize capability metadata;
- route selected capabilities into canonical Runs;
- prevent raw tool explosion;
- enforce policy before capability execution.

**Exit criteria:** model-facing tool surface remains small while underlying capability count can grow.

---

### Phase 7 — Artifact/Reference Fabric

**Goal:** eliminate large-payload control-plane pressure.

Tasks:

- standardize artifact metadata;
- implement `ref://` semantics;
- connect browser/code/analysis outputs;
- enforce access/retention;
- add checksum/integrity metadata;
- measure control-plane payload reduction.

**Exit criteria:** heavy data is transferred by reference, not through orchestration messages.

---

### Phase 8 — Diagram & Architecture UX

**Goal:** make the architecture graph understandable to humans and agents.

Tasks:

- structured graph JSON;
- safe SVG/HTML rendering;
- dependency explorer;
- Run → dependency → artifact trace;
- blast-radius visualization;
- architecture diff view;
- optional Diagram Design/Archify-inspired renderer.

**Exit criteria:** developers can understand why a change affects a capability before merging it.

---

### Phase 9 — Governed Skill Ecosystem

**Goal:** add specialized capability without polluting the core.

Tasks:

- governed skill registry;
- capability metadata;
- authorization scopes;
- sandbox/resource policies;
- provenance;
- versioning;
- auditability;
- optional cybersecurity/scientific packs.

**Exit criteria:** new skills can be added/removed without destabilizing core architecture.

---

## 17. CI / GitHub Automation Blueprint

Recommended architecture tooling layout:

```text
.github/workflows/
  architecture-audit.yml
  architecture-pr.yml
  architecture-nightly.yml

.tools/architecture/   # exact placement may follow existing repo conventions
  config/
    architecture-rules.yml
  frontend/
    dependency-cruiser.json
  backend/
    pydeps.conf
  scripts/
    build_graph.py
    compare_graph.py
    detect_cycles.py
    blast_radius.py
    score.py
```

### PR automation

```text
PR
 ↓
changed-file detection
 ↓
architecture graph diff
 ↓
dependency edge diff
 ↓
cycle detection
 ↓
boundary rules
 ↓
blast radius
 ↓
affected tests/capabilities
 ↓
QA contract
 ↓
report artifact
```

### Nightly automation

Nightly checks should be broader than PR checks:

- full graph rebuild,
- runtime/static reconciliation,
- orphan detection,
- dependency drift,
- vulnerability scan,
- architecture health trend,
- stale documentation detection,
- full E2E where environment permits.

Generated SVG/HTML/JSON reports should be CI artifacts rather than committed repository noise unless a human-readable snapshot is intentionally versioned.

---

## 18. Failure & Degraded-Mode Model

A federated platform must fail by capability, not by cascade.

```text
Circle unavailable
      ↓
Tower marks DEGRADED
      ↓
Affected Runs fail/retry gracefully
      ↓
Unrelated Circles continue
      ↓
Frontend shows capability-specific status
```

### Required properties

- explicit health states;
- timeout isolation;
- circuit breaking where appropriate;
- retry classification;
- graceful fallback;
- artifact preservation;
- audit trail;
- operator visibility.

A Control Tower restart should not erase durable Run state or make unrelated platform data unavailable.

---

## 19. Security & Tenancy Invariants

Every new architecture component must preserve:

- tenant isolation,
- authorization before capability execution,
- least-privilege service access,
- RLS/database boundaries where applicable,
- secret isolation,
- auditability,
- safe artifact access,
- Run ownership,
- skill/tool permission scope.

Architecture convenience must never bypass an existing security boundary.

---

## 20. Observability Contract

Every canonical Run and major capability should emit enough metadata to answer:

- Who initiated it?
- Which workspace/project/tenant?
- Which capability?
- Which model/provider?
- Which tools?
- Which dependencies?
- How long?
- How many retries?
- How many tokens/resources?
- Which artifacts?
- What failed?
- What degraded?
- What final result?

This is the foundation for cost analysis, reliability analysis and autonomous learning/evolution.

---

## 21. Architecture Health Score

A future architecture score should combine:

```text
Architecture Health =
  dependency integrity
+ boundary compliance
+ cycle trend
+ test/QA coverage
+ runtime health
+ deployment health
+ security posture
+ documentation completeness
+ resource efficiency
```

The score is an indicator, not a substitute for hard release gates.

---

## 22. Success Metrics

### Execution

- percentage of major tasks represented by canonical Runs;
- Run failure/retry rate;
- mean time to completion;
- cancellation/timeout correctness.

### Context

- tokens saved through L0/L1/L2 selection;
- duplicate context reduction;
- retrieval relevance;
- context-related failure rate.

### Architecture

- new dependency edges per PR;
- new cycles per PR;
- boundary violations;
- blast-radius accuracy;
- static/runtime mismatch count.

### Operations

- API memory footprint;
- browser-worker isolation effectiveness;
- control-plane payload size;
- queue latency;
- dependency failure containment.

### Quality

- QA contract pass rate;
- critical-path coverage;
- E2E breadth;
- production smoke pass rate;
- rollback/recovery evidence.

---

## 23. What Must NOT Happen

1. Do not rebuild the frontend/backend from scratch.
2. Do not add a second memory backend simply to imitate agentmemory.
3. Do not replace existing Playwright blindly with Browser Use.
4. Do not create a second architecture graph alongside `system_dependencies` without a consolidation plan.
5. Do not expose hundreds of raw tools to every model by default.
6. Do not move heavy payloads through the MCP control plane.
7. Do not add Colibrì without measured need.
8. Do not turn optional scientific/security skills into core dependencies.
9. Do not hardcode a fixed number of AI agents/providers when the real requirement is dynamic `1..N` discovery.
10. Do not let a new feature bypass QA, security, tenancy or deployment contracts.
11. Do not use architecture diagrams as proof that runtime behavior is correct; static and runtime evidence must remain distinguishable.
12. Do not block all progress because of legacy architecture debt; prevent **new** debt while retiring old debt incrementally.

---

## 24. Final Architecture Principle

SupremeAI's long-term advantage is not the number of tools, models, providers or OSS repositories integrated.

It is the ability to turn many capabilities into a **single coherent, observable, governed and composable system** without creating architectural duplication.

```text
                 SUPREME AI
                     │
          ┌──────────┴──────────┐
          │                     │
      EXPERIENCE             GOVERNANCE
          │                     │
       Chat/IDE             QA/Policy/Audit
          │                     │
          └──────────┬──────────┘
                     ▼
              CONTEXT ENGINE
          Files / Memory / RAG
                     │
                     ▼
               CANONICAL RUN
          Mission / Agent / Tool
                     │
                     ▼
             MCP / CIRCLES
       Code / Cloud / Knowledge
       Auth / Browser / Execution
                     │
                     ▼
              WORKERS / TOOLS
                     │
                     ▼
              ARTIFACTS / DATA
                     │
                     ▼
                  RESULT

        ─────────────────────────────
        ARCHITECTURE INTELLIGENCE
        Static + Runtime + Blast Radius
        ─────────────────────────────
```

### The operating doctrine

> **Current architecture is the capability foundation. This plan is the coherence and evolution system.**
>
> **Do not replace working capabilities merely to match an external architecture. Canonicalize them, connect them, govern them, measure them, and evolve only where evidence shows a real gap.**

This is the architecture path for taking SupremeAI from a large collection of capable systems to a **unified ecosystem that can safely grow to many users, many models, many tools, many workers and many external services without proportional increases in duplication, coupling, token waste or operational risk.**
