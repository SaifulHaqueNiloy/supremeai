---
id: ci-pipeline-consolidation
subject: "SupremeAI CI/CD Architecture Optimization Specification (v2.0)"
document_role: implementation
planning_authority: DevEx / CI Circle
canonical: candidate
status: active
evidence_state: partial
disposition: retain
last_verified: 2026-09-17
supersedes: []
superseded_by: []
target_scope: supremeai_internal
---

# SupremeAI CI/CD Architecture Optimization Specification (v2.0)

**Document ID:** `CI_PIPELINE_CONSOLIDATION_PLAN_2026-09-15`  
**Version:** 2.0 (Post-Review Technical Refinement)  
**Status:** Approved Architectural Living Asset  
**Scope:** `.github/workflows/ci.yml`, `.github/actions/setup-backend/action.yml`, Docker build pipelines, Frontend & Backend workflows  
**Pattern:** Deterministic Prepare → Immutable Artifact Publication → Adaptive Parallel Test → Aggregation → Layer-Cached Deployment  

---

## 1. Executive Summary & Problem Statement

### 1.1 The Performance & Resource Regression
In `.github/workflows/ci.yml`, backend testing was parallelized into 4 matrix groups (`security`, `api`, `core`, `services`). While meant to reduce wall-clock time, the observed runtime reality is a severe resource regression:
* **Previous Monolithic Execution Time:** 3–4 minutes in a single job.
* **Current Matrix Execution Time:** 3–4 minutes per matrix job across 4 concurrent runners.
* **Runner-Minute Cost:** $4 \times 3.5\text{ min} \approx 14\text{ minutes}$ consumed per commit (a 4× billing expansion with zero wall-clock acceleration).

### 1.2 Root Cause Analysis
1. **The "Setup Tax" Duplicated 6×:**
   - Every GitHub Actions matrix runner is an isolated, ephemeral virtual machine.
   - Each runner redundantly executes:
     - `apt-get update && apt-get install -y build-essential libpq-dev` (~35s)
     - `actions/setup-python` and `install-poetry` (~20s)
     - Postgres 16 Docker service startup & health probing (~20s)
     - `poetry install --no-root --with dev` wheel building and virtualenv generation (~75s)
   - **Result:** ~2.5 minutes of setup overhead runs before `pytest` executes a single line of test code.
2. **Duplicated Setup Across Other Pipeline Jobs:**
   - Setup Backend runs across: `backend-tests` (4×), `integration-test` (1×), and `backend-aggregate` (1×) = **6 identical runs**.
   - Setup Frontend runs across: `frontend-tests` (1×) and `build` (1×) = **2 identical setup/install runs**.

---

## 2. Core Architectural Principles (v2 Refinements)

### 2.1 Immutable Dependency Artifacts over "Shared Environment"
A GitHub Actions cache is **not a shared live filesystem**. Each runner restores its own isolated copy. The mental model is:
$$\text{Prepare Once} \longrightarrow \text{Publish Immutable Dependency Artifact} \longrightarrow \text{Parallel Runners Restore}$$

### 2.2 Decoupled Dependency Layers (OS vs. Python Runtime)
System native packages (`libpq`, `build-essential`, C-extensions) reside outside `.venv`. Restoring `.venv` alone will fail if OS dynamic libraries are absent. 

The architecture strictly decouples dependency layers:
```text
GitHub Runner VM (Ubuntu Latest)
│
├── Layer 1: OS Runtime Prerequisites (libpq, build libraries, Docker)
│            -> Installed quickly via lightweight runtime-only packages (e.g. libpq5 instead of build-essential)
│
├── Layer 2: Python Engine (Pinned Python 3.11)
│            -> actions/setup-python (cached)
│
├── Layer 3: Restored Immutable Dependency Artifact (backend/.venv)
│            -> Restored in 3-5 seconds via actions/cache or artifact
│
└── Layer 4: Test & Execution Targets
             -> pytest execution with zero compile overhead
```

### 2.3 Adaptive Matrix Granularity (No Tiny Runner Waste)
Launching an entire Ubuntu runner for a 15-second test suite (e.g., `security`) introduces scheduling and teardown overhead that negates parallelism. 
* Groupings must be **adaptive based on measured execution time**, merging lightweight groups (e.g., `security` + `api`) while keeping compute-intensive suites (`core`, `services`) parallel.

### 2.4 End-to-End BuildKit & Docker Layer Caching
Optimizing test setup by 4 minutes is undermined if downstream Docker image builds spend 6 minutes rebuilding unchanged layers. The CI pipeline incorporates BuildKit with registry-backed caching (`cache-from`, `cache-to`).

---

## 3. Inventory of Current CI Jobs (19 Jobs)

| Job ID | Job Title | Needs | Current Responsibilities & Steps |
|---|---|---|---|
| `changes` | Detect Changes | `None` | `actions/checkout`, `detect-previous-failures.py`, `dorny/paths-filter` |
| `constitution-audit` | Constitution Audit | `None` | Checkout, Setup Python, Install audit deps, Run Constitution audit & rule tests, Upload SARIF/evidence |
| `tooling-quality` | Operational Tooling Quality Gate | `changes` | Checkout, Setup Python, Install Ruff, Lint backend/tooling, Check single Alembic head, Enforce boundary |
| `security` | Security Scan | `None` | Checkout, Trivy vulnerability scan, Machine-readable gate, Secret scan, Upload evidence |
| `security-gate` | Security Aggregate Gate | `security` | Require security scan success |
| `advanced-checks` | Advanced Pre-Merge Checks | `changes` | Reusable workflow call (`ci-advanced-checks.yml`) |
| `backend-tests` (Matrix: 4) | Backend Tests (`security`, `api`, `core`, `services`) | `changes` | Checkout, **Full Setup Backend (apt + poetry install)**, Detect changed tests, Filter matrix targets, **Pytest**, Trend report, Upload coverage |
| `backend-aggregate` | Backend Aggregate Gate | `backend-tests` | Checkout, **Full Setup Backend**, Validate OpenAPI, Mission scoreboard, Infisical staging, Verify startup/pgvector, Merge & enforce coverage |
| `integration-test` | Integration Tests | `changes` | Checkout, **Full Setup Backend**, Run integration tests (`pytest tests/integration/`), Upload report |
| `frontend-tests` | Frontend Tests | `changes` | Checkout, **Full Setup Frontend (Node + pnpm install)**, Type check (`tsc`), Lint (`eslint`), Vitest unit tests, Check dead code |
| `build` | Build Verification | `changes` | Checkout, **Full Setup Frontend (Node + pnpm install)**, Infisical secrets, `pnpm build`, Verify VITE_* contracts, Upload artifact |
| `deploy-frontend` | Deploy Frontend | `build`, `frontend-tests` | Download build, Render `firebase.json`, Deploy to Firebase Hosting |
| `render-deploy-preflight` | Render Deploy Preflight | `changes` | Quota preflight, verify & upload deployment evidence |
| `docker` | Docker Publish | `backend-aggregate`, `integration-test`, `render-deploy-preflight` | Build & publish Docker images |
| `mcp-build` | MCP Build | `render-deploy-preflight` | Build MCP control plane packages |
| `production-deploy` | Production Deploy | `docker`, `mcp-build`, `advanced-checks` | Trigger production deployment |
| `smart-summary` | Smart Pipeline Summary | All upstream jobs | Generate enhanced pipeline summary v2, upload evidence |
| `qa-contract` | QA Contract | `changes` | Reusable workflow call (`qa-contract.yml`) |
| `staging-deploy` | Staging Deployment | `qa-contract`, `build`, `deploy-frontend`, `production-deploy` | Trigger staging rollout |

---

## 4. Target 5-Phase Pipeline Architecture

```mermaid
flowchart TD
    subgraph Phase 0 [Phase 0: Telemetry & Baseline Metrics]
        M0[Record Baseline: Wall-Clock, Runner-Minutes, Failure Rate, Docker Build Time]
    end

    subgraph Phase 1 [Phase 1: Deterministic Preparation - RUN ONCE]
        CH[changes: Detect Changes]
        
        B_PREP[<b>backend-prepare</b><br/>• Setup Python & OS Native Libs (libpq-dev)<br/>• Poetry install --with dev<br/>• Static Lint (Ruff), Alembic & OpenAPI Validation<br/>• <b>Publish Immutable .venv Dependency Artifact/Cache</b>]
        
        F_PREP[<b>frontend-prepare</b><br/>• Setup Node 24 & pnpm<br/>• Benchmark: pnpm store cache vs node_modules<br/>• Run Typecheck (tsc) & Lint (eslint)<br/>• <b>Publish Frontend Dependency Artifact/Cache</b>]
    end

    subgraph Phase 2 [Phase 2: Adaptive Parallel Execution - ZERO SETUP TAX]
        B_PREP -->|Restore Artifact + Fast OS Runtime| BT_FAST[Adaptive Group: Security + API ~45s]
        B_PREP -->|Restore Artifact + Fast OS Runtime| BT_CORE[Heavy Group: Core ~1.5m]
        B_PREP -->|Restore Artifact + Fast OS Runtime| BT_SERV[Heavy Group: Services ~1.8m]
        B_PREP -->|Restore Artifact + Fast OS Runtime| B_INT[Integration Tests ~1m]
        
        F_PREP -->|Restore Artifact/Store| FT[Frontend Vitest Unit Tests]
        F_PREP -->|Restore Artifact/Store| FB[Frontend Vite Production Build]
    end

    subgraph Phase 3 [Phase 3: Aggregation & Gate Enforcement]
        BT_FAST & BT_CORE & BT_SERV --> B_AGG[Backend Coverage Merge & Gate<br/>Startup Verification (AUD-1.1)]
        FT & FB --> F_DEP[Deploy Frontend to Firebase]
    end

    subgraph Phase 4 [Phase 4: Docker & Production Deployment]
        B_AGG & B_INT --> DOCKER[<b>Docker Build with BuildKit Caching</b><br/>Registry-backed cache-from/cache-to]
        DOCKER --> PREFLIGHT[Render Deploy Preflight]
        PREFLIGHT --> PROD_DEP[Production Deploy & Post-Smoke]
    end
```

---

## 5. Implementation Roadmap & Technical Details

### Step 1: Baseline Establishment (Phase 0)
Before making edits, measure and record:
- Total Wall-Clock time (P50 and P95 over last 5 runs).
- Total GitHub Action Runner Minutes consumed.
- Breakdown of: OS Setup time, Dependency install time, Test execution time, Docker build time.

### Step 2: Runtime-Optimized `.github/actions/setup-backend`
Split setup into two distinct modes:
1. **`build` mode (used in `backend-prepare`):** Full compiler toolchain, `libpq-dev`, Poetry, lock validation, full `.venv` assembly, and cache emission.
2. **`runtime-only` mode (used in `backend-tests` & `integration-test`):**
   - Install runtime-only C-libraries (`libpq5` instead of heavy `build-essential libpq-dev`).
   - Fast-restore `./backend/.venv` from cache/artifact.
   - Validate virtualenv binary presence in < 5 seconds.

### Step 3: Implement `backend-prepare` and Consolidate Tooling
1. Execute Python setup, `poetry install --with dev`, and publish immutable `.venv` cache.
2. Absorb `tooling-quality` (Ruff linter, Alembic migration verification) and OpenAPI schema validation into `backend-prepare`. This eliminates dedicated VM spin-up for static analysis.

### Step 4: Adaptive Matrix Balancing
Balance the pytest matrix dynamically:
- **Group 1 (Fast & Contracts):** `security` + `api` (Target: ~45–60s).
- **Group 2 (Domain Core):** `core` + `brain` + `adaptive_engine` + `orchestration` (Target: ~1.2–1.5m).
- **Group 3 (Services & Integration):** `services` + `agents` + `missions` + `tools` (Target: ~1.5–1.8m).

### Step 5: Frontend Store vs. Node Modules Benchmarking
Benchmark pnpm caching:
- Test Option A: Caching `~/.local/share/pnpm/store` + offline `pnpm install`.
- Test Option B: Packaging and restoring direct `node_modules` artifact.
Adopt the option providing the lowest P95 restoration time and zero drift.

### Step 6: Docker BuildKit Layer Caching
Update `ci-docker.yml`:
- Enable BuildKit (`DOCKER_BUILDKIT=1`).
- Configure GitHub Actions cache backend (`type=gha,mode=max`) or Docker registry cache (`cache-from` / `cache-to`).
- Ensure multi-stage `Dockerfile` places static system libraries first and dynamic application code last to maximize cache hits.

---

## 6. Performance Targets (Empirical Validation Model)

*Note: The following are architectural target metrics to be empirically validated against 3–5 representative CI runs post-implementation.*

| Target Metric | Baseline (Observed) | Architectural Target | Success Criteria |
|---|:---:|:---:|:---:|
| **Setup Time per Test Runner** | ~2.5 min | **< 15 sec** | > 85% setup reduction |
| **Combined Fast Group (`security` + `api`)** | ~3.2 min | **~45 sec** | P95 < 60s |
| **Core Suite (`core`)** | ~3.8 min | **~1.5 min** | P95 < 2.0m |
| **Services Suite (`services`)** | ~4.0 min | **~1.8 min** | P95 < 2.2m |
| **Total Wall-Clock Time** | 4.0–4.5 min | **~2.2–2.5 min** | ~40-45% reduction |
| **Total Runner Minutes** | 16–20 min | **6–8 min** | **~60% cost savings** |
| **Gate Integrity** | 100% Gates Active | **100% Gates Active** | Zero gates dropped |

---

## 7. Safety, Verification & Rollout Plan

To adhere strictly to `AGENTS.md` (Risk-Tiered Autonomy & Zero-Gap):
1. **Isolated Experiment Branch:** Perform all workflow refactorings on a feature branch (e.g., `feat/ci-pipeline-consolidation`).
2. **Empirical Benchmarking:** Run 3 consecutive test pushes on the branch to measure P50/P95 durations against the recorded baseline.
3. **Artifact Verification:** Verify that test coverage reports, JUnit XMLs, and SARIF security scans remain 100% identical in quality and structure.
4. **Pull Request & Staged Promotion:** Open a formal PR with benchmark evidence before merging into `main`.