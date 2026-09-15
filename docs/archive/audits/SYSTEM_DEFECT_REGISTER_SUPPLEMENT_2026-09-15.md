# SupremeAI — Supplemental Defect Register (Git-Tracked Deep Scan)

**Document ID:** `SYSTEM_DEFECT_REGISTER_SUPPLEMENT_2026-09-15`
**Status:** Living Baseline — Supplement to `SYSTEM_DEFECT_REGISTER_2026-09-15.md`
**Scope:** All 3,700 git-tracked files (backend, frontend, packages, scripts, tests, CI)
**Method:** static reconstruction + executed audit tooling (see §0)
**Companion register:** `docs/audits/SYSTEM_DEFECT_REGISTER_2026-09-15.md` (existing, classes A–F)
**Evidence bundle:** `docs/audits/evidence/2026-09-15/` · **Scanner:** `scripts/audit/system_deep_scan_2026_09_15.py`

> **বাংলা সারসংক্ষেপ:** বিদ্যমান রেজিস্ট্রি (Class A–F) পুনঃযাচাই করে তার বাইরে **নতুন ৩৮টি ত্রুটি** পাওয়া গেছে। সবচেয়ে গুরুত্বপূর্ণ তিনটি:
> 1. **বিলিং মক চেকআউট (`ERR-G01`)** — Stripe key না থাকলে ইউজারকে ভুয়া `mock_session_123` সহ success URL দেওয়া হয় (P0, আর্থিক)।
> 2. **`production_deploy.py` ডিপ্লয় সিমুলেট করে (`ERR-G02`)** — `time.sleep()` দিয়ে fake deploy **এবং fake rollback**।
> 3. **Stub-detection gate অন্ধ + CI-তে নেই (`ERR-M01`)** — `.pre-commit-config.yaml`-এর "Gate 1" `_crown_jewel.py`-এর মক ধরতে পারে না, অথচ `[PASS]` দেখায়।
>
> এছাড়া **"False Assurance" (Class G)** নামে নতুন একটি ডিফেক্ট-ক্লাস সংযোজিত — যেখানে সিস্টেম *সফল/নিরাপদ* দেখায় কিন্তু আসলে কিছুই করে না।

---

## 0. Method, Tooling & Evidence (reproducible)

| Evidence artifact | Command | Result |
|---|---|---|
| Tracked file census | `git ls-files` | **3,700** tracked files (older `AUDIT_REPORT_2026-09-10` said 3,202) |
| Working-tree cleanliness | `git status --short` | 1 untracked file only → **everything else is committed** |
| Route/parity reconstruction | `scripts/audit/system_deep_scan_2026_09_15.py` | 149 mounted modules → **765 route rows** |
| Frontend call inventory | same scanner | **287** `/api…` literals |
| Unmatched frontend calls | same scanner | **86** candidates → **26 hand-verified dead** (§3) |
| Orphan backend families | same scanner | **57** families (§5) |
| Backend stub/mock census | same scanner | **1,157** hits / 340 files (tests excluded) |
| Frontend stub/mock census | same scanner | **280** hits / 145 files (tests excluded) |
| Project's own stub gate | `python scripts/find_stub_data.py --path backend --fail-on HIGH` | printed `[PASS] No stub patterns found` — **FALSE PASS** (§6) |
| Project's own parity tool | `python scripts/feature_parity_sentinel.py --fail-on never` | **CRASHED** — `UnicodeEncodeError: 'charmap' codec … '\U0001f50d'` (§6) |

### 0.1 Scanner defects found and fixed during this audit

The first reconstruction produced **115** unmatched calls. Two scanner bugs were found, fixed, and the scan re-run (**86** unmatched — 29 false positives eliminated):

1. **Package routers were invisible.** `backend/api/routes/browser/__init__.py` declares `router = APIRouter(prefix="/api/browser", …)` but every decorator lives in a sibling submodule (`_session_store.py`, `_tasks.py`, …). The scanner now walks `__init__.py` **plus** sibling `*.py`.
2. **Multiline `APIRouter(...)` prefixes were missed.** Now parsed with balanced-paren scanning rather than a single-line regex.

> **Honest limitation:** the parity result is a *static heuristic*, not a runtime route-table assertion. Every mismatch in §3 was additionally hand-verified by reading both sides. Items I could not hand-verify are labelled **[CANDIDATE]** and must not be treated as confirmed.

---

## 1. Corrections to the Existing Register (Class A–F)

Errors in `SYSTEM_DEFECT_REGISTER_2026-09-15.md` that should be fixed so remediation is not misdirected.

| # | Register claim | Verified reality | Verdict |
|---|---|---|---|
| **C-1** | `ERR-A02`: "Frontend calls `POST /api/v1/agent/execute`" citing `agentService.ts:L19` | Correct **for `agentService.ts`**, but **incomplete**: `AgentWorkspace.tsx:73` — the only live caller of the agent flow — calls the **plural** `/api/v1/agents/execute`. | **Split the defect.** A02 is a *service-layer* bug (`agentService` appears unused); A01 is the *live* 422. |
| **C-2** | `ERR-A01`: frontend sends `{ prompt, project_id }` without `task_id` | Confirmed at `AgentWorkspace.tsx:73` (`{ prompt, project_id: 'default' }`) vs `AgentTaskRequest.task_id` (`agent.py:24`). | ✅ Accurate |
| **C-3** | `ERR-A05`: `/api/v1/projects` has no route | Confirmed — absent from the reconstructed 765-row route table. | ✅ Accurate |
| **C-4** | Class D item: `browserService.ts:L16` "Client-side SDK calls stubbed with `console.log`" | `browserService.ts` actually calls real endpoints (`/api/browser/automation/sessions`, `…/actions`, `…/saved-sessions`). No `console.log` stub is present in that file. | ❌ **Stale / incorrect — remove or re-locate** |
| **C-5** | Class E: "Total skipped tests: 96" | `docs/SKIPPED_TESTS.md` itself records **102 raw markers → 100 after pass**, 98 rows → **96 active**. The register quotes the *active* figure but omits the raw-marker count and the `FIXED` rows. | ⚠️ **Precision gap** |
| **C-6** | Class C: "22 orphan APIs" (Missions 11 + MCP 7 + Circles 4) | **Under-counted.** The reconstructed table yields **57 orphan route families** (§5), including an entire `commandcenter` admin surface and six `image-to-*` tools. | ❌ **Incomplete — expanded in §5** |
| **C-7** | Class D lists 6 mock items (implying containment) | **Under-counted by two orders of magnitude.** 1,157 backend stub/mock hits were found, including **financial** and **deployment** paths the register never mentions (§2). | ❌ **Materially incomplete** |
| **C-8** | `ERR-F04`: `react-router-dom` v6→v7 drift | Confirmed `"react-router-dom": "^6.30.6"` at `frontend/package.json:66`. | ✅ Accurate |

---

## 2. NEW Class G — "False Assurance" Defects (P0/P1)

**This class does not exist in the current register.** It is arguably the most dangerous: **the system reports success, health, or security while performing no work.** A component that *fails* is safer than one that *lies*.

> **Why this class matters:** every downstream guard — tests, dashboards, HITL, and the self-evolution loop — consumes these signals. A fabricated "success" poisons the entire feedback loop and is invisible to outcome-checking, because the outcome itself was invented.

| ID | File / Location | What the code does | Impact |
| :--- | :--- | :--- | :--- |
| **ERR-G01** | `backend/api/routes/billing_api.py:271–275` | If no Stripe key: `logger.warning("Stripe API key not set in settings. Using mock checkout session.")` then returns `{"status": "mock", "session_id": "mock_session_123", "url": payload.success_url + "?session_id=mock_session_123"}` | **Financial integrity.** Customer is redirected to the success URL with a fabricated session id, indistinguishable from a paid checkout. No payment occurred. |
| **ERR-G02** | `backend/core/deployment/production_deploy.py:379–476` | `# For demo purposes, we'll simulate the process`; `time.sleep(2) # Simulate deployment time`; `# For demo, we'll use a mock URL - in real implementation this would come from config`; `# Simulate rollback process` | A module named **`production_deploy`** fakes deploys **and rollbacks**. If wired to a route, rollback evidence is fiction. |
| **ERR-G03** | `backend/api/routes/browser/_crown_jewel.py:43–45` | `@router.post("/security-scan")` → unconditional `return {"success": True, "score": 100, "issues": []}` | **Security theatre.** Every target scores a perfect 100 with zero issues. Falsifies the platform's "verify before trust" promise. |
| **ERR-G04** | `backend/core/orchestration/cloud_sandbox_orchestrator.py:70–140` | Missing API key → `mock: True`, `stdout: f"Mock output for execution of: {command}"` | "Code execution" returns **fabricated stdout**; the user sees output no sandbox produced. |
| **ERR-G05** | `backend/api/routes/browser/_crown_jewel.py:60–69` | `@router.post("/tasks/{id}/step")` → `# Simulate a step execution` → always `{"action": "navigated to dashboard", "details": "Autonomous step succeeded"}` | Task progress is a constant; the autonomy dashboard can show forward motion on a stalled task. |
| **ERR-G06** | `backend/api/routes/browser/_crown_jewel.py:21–25` | `@router.post("/browse-session")` returns `session_id = "sess_" + sha256(url)[:16]` — a hash of the **URL**, not a session that exists | Deterministic fake session id; subsequent lookups fail but the caller was told `success: True`. |
| **ERR-G07** | `backend/api/routes/agents.py:42–49` | `get_agent_status()` returns hardcoded `{"status": "active", "last_activity": "2026-01-01T00:00:00Z"}` for **any** `agent_id` | Fabricated liveness + a frozen timestamp; cannot distinguish a running agent from a nonexistent one. |
| **ERR-G08** | `backend/api/routes/agents.py:30–37` | `list_agents()` returns a hardcoded single `{"id": "research", …}` entry | The "available agents" registry is a literal. |
| **ERR-G09** | `frontend/src/providers/MockSwarmProvider.tsx:39–79` | `cpuUsage: 15 + activeCount * 8.5 + (Math.random() * 4)`; `errorRate: Math.max(0, 0.5 + Math.random() * 2)`; log lines `['Analyzing AST…','Running test suite…'][Math.floor(Math.random()*4)]`; `level: Math.random() > 0.9 ? 'warn' : 'info'` | Swarm telemetry and the live event stream are **random numbers and canned strings**. Operators tune the fleet off noise. |
| **ERR-G10** | `frontend/src/pages/user/AgentWorkspace.tsx:81` | `runCode` → `setTimeout(() => { term.writeln('[execution] Evaluation queued.'); setIsHealing(false); }, 700)` | "Run & evaluate" prints a fake step and reports completion after 700 ms; no code is run. |
| **ERR-G11** | `backend/api/routes/browser/_crown_jewel.py:1` (module docstring) | `"""Crown Jewel mock endpoints + the legacy in-memory task-step executor.` | The module **documents itself as mock** yet is mounted, tagged `browser`, and shipped in the live API surface. |

**Escalation note (`ERR-G01`):** the only defect found where a *customer-visible success state* is manufactured inside a **billing** path. It should be the highest-priority item in this document regardless of trigger frequency, because the failure mode is silent revenue/entitlement divergence.

---

## 3. Newly VERIFIED FrontendBackend Contract Mismatches (P0)

Every row below was confirmed by reading **both** the frontend call site and the backend route definition. All produce `404 Not Found` at runtime.

### 3.1 `/api/user/preferences` — five callers, two wrong prefixes (`ERR-H01`)

The backend exposes only the **no-`v1`** path:

```
backend/api/routes/preferences.py:15   prefix="/preferences"
backend/api/routes/preferences.py:31   @router.get("/")
backend/api/routes/preferences.py:59   @router.post("/")
backend/api/routes/preferences.py:115  @router.get("/{user_id}/stream")
mount (ALL_ROUTERS)                    prefix="/api"
→ real paths:  GET|POST /api/preferences/   and   GET /api/preferences/{user_id}/stream
```

| Frontend caller | Path called | Backend match | Result |
|---|---|---|---|
| `frontend/src/contexts/ThemeProvider.tsx:30,74` | `/api/v1/preferences` | ❌ (no `v1`) | **404** |
| `frontend/src/i18n/I18nProvider.tsx:27` | `/api/user/preferences` |  | **404** |
| `frontend/src/store/themeStore.ts:69,85` | `/api/user/preferences` |  | **404** |
| `frontend/src/pages/ProfilePage.tsx:33` | `/api/user/preferences` |  | **404** |

**Impact:** theme, locale **and** profile preferences are all unsaved across 5 call sites — user-visible data loss (P0). This is a defect class *not covered* by the existing register.

### 3.2 `/api/skills/...` — three dead calls (`ERR-H02`)

```
backend/api/routes/skills.py:12     prefix="/skills"
backend/api/routes/skills.py:23     GET  /catalog
backend/api/routes/skills.py:61-62  GET|POST /search
backend/api/routes/skills.py:81     POST /install          ← no path parameter
mount (ALL_ROUTERS)                 prefix="/api"
→ real paths: /api/skills/catalog, /api/skills/search, /api/skills/install
```

| Frontend caller | Path called | Verdict |
|---|---|---|
| `frontend/src/services/skillsService.ts:104` | `POST /api/skills/${skillId}/install` | ❌ backend has `/api/skills/install` (**no id segment**) → **404** |
| `frontend/src/services/skillsService.ts:118` | `DELETE /api/skills/${skillId}/uninstall` | ❌ **no `uninstall` route exists at all** → **404** |
| `frontend/src/pages/user/EvolutionForge/EvolutionForge.tsx:293` | `POST /api/skills/deploy-blueprint` | ❌ no such route → **404** |

**Impact:** skill install **and** uninstall are both broken — a user who installs a skill cannot remove it.

### 3.3 `/api/v1/workspaces/bind-target` — wrong entire prefix (`ERR-H03`)

```
backend/api/routes/workspaces_route.py:30  prefix="/admin-api/workspaces"
backend/api/routes/workspaces_route.py:68  @router.post("/bind-target")
→ real path: POST /admin-api/workspaces/bind-target
```

| Frontend caller | Path called | Verdict |
|---|---|---|
| `frontend/src/services/aiActions.ts:174` (+ its test) | `POST /api/v1/workspaces/bind-target` |  admin prefix vs `api/v1` → **404** |

### 3.4 `/api/v1/ecosystem/admin/*` — seventeen dead admin calls (`ERR-H04`)

`backend/api/routes/ecosystem_admin.py` exists with `prefix="/api/v1/ecosystem/admin"` and exposes exactly:
`POST /capabilities`, `/capabilities/{id}/archive`, `/capabilities/{id}/lifecycle`, `/capabilities/{id}/promote`, `GET /decisions`, `GET|POST /opportunities`, `POST /opportunities/{id}/advance`, `GET /overview`, `GET|POST /proposals`, `POST /proposals/{id}/decide`.

`frontend/src/lib/ecosystem/api.ts` calls a **differently-named surface**:

| Frontend caller | Path called | Backend | Verdict |
|---|---|---|---|
| `api.ts:607,613,620,627` | `/api/v1/ecosystem/admin/sources` (+`/discover`, `/{id}/transition`, `/{id}`) | ❌ no `sources` route | **404** |
| `api.ts:636,641,654,660` | `/api/v1/ecosystem/admin/policies` (+`/{id}`, `/match`) | ❌ no `policies` route | **404** |
| `api.ts:669,674,683` | `/api/v1/ecosystem/admin/learned` (+`/prune`, `/{id}`) | ❌ no `learned` route | **404** |
| `api.ts:733,740` | `/governance/decisions`, `/governance/budgets` | ❌ no `governance` route | **404** |
| `api.ts:597` | `/proposals/{id}/**decisions**` | ⚠️ backend is `/proposals/{id}/**decide**` | **404 — singular/plural mismatch** |
| `api.ts:558` | `/admin/capabilities/{id}` | ⚠️ admin has `POST /capabilities` only | **404** |
| `api.ts:439,463` | `/api/v1/ecosystem/tasks/{id}/cancel`, `/{id}/events` | ⚠️ backend has `/transition` + `/deliver` only | **404** |
| `api.ts:348,353` | `/api/v1/auth/users`, `/api/v1/auth/users/{id}/role` | ❌ no such route | **404** |

**Impact:** the entire **ecosystem admin console client is a ghost** — 17 hand-written endpoints against a backend implementing a differently-named set. Note `decisions` vs `decide`: a one-word mismatch that survives code review.

### 3.5 `/api/knowledge/*` — four dead calls from the shared service (`ERR-H05`)

```
backend/api/routes/knowledge.py  (mount prefix="/api", own prefix="")
POST /api/knowledge/ask | /api/knowledge/ask-scribe | /api/knowledge/search | /api/knowledge/seed
```

| Frontend caller (`packages/shared-services/src/services/SupremeAIService.ts`) | Path called | Verdict |
|---|---|---|
| `:98, :154` | `/api/knowledge/learn` | ❌ **404** |
| `:111` | `/api/knowledge/failure` | ❌ **404** |
| `:127` | `/api/knowledge/feedback` | ❌ **404** |
| `:136` | `/api/knowledge/stats` | ❌ **404** |

**Impact:** the learning-loop client writes to nonexistent endpoints — the "system learns from failure" path silently 404s. This compounds `ERR-F03` (no context engine) in the existing register.

### 3.6 Additional **[CANDIDATE]** unmatches (NOT hand-verified)

Triage only; full list in `docs/audits/evidence/2026-09-15/missing_calls.txt`:
`/api/codeflow/*` (5 calls, `SupremeAIService.ts`), `/api/v1/billing/plans` (`BillingPage.tsx:26`), `/api/v1/swarm/forge` (`EvolutionForge.tsx:237`), `/api/admin/llm/{providers,router,rules,router/override}` (5, `LlmGatewayPage.tsx`), `/api/admin/trusted-browsers` (3, `SettingsPage.tsx`), `/api/admin/librarian/process`, `/api/admin/gate/override`, `/api/evolution/forge`, `/api/v1/sync/{table}`, `/api/v1/connections/*`.

**Explicitly excluded as verified false positives:** `/api/health`, `/api/config`, `/api/health-aggregation` in `frontend/src/utils/apiInterceptor.ts:95–117` are *string classifiers* that suppress error toasts (not requests); `apiClient.ts:273–279` is a prefix allow-list. Also excluded: `.test.ts`/`.spec.ts` and `qa/playwright` literals.

### 3.7 Guaranteed-500 module-level break (`ERR-H06`)

```
backend/api/routes/agents.py:55   from agents.research_assistant import ResearchAssistant
```

`backend/agents/` contains: `autonomous_agent, base_pydantic_agent, churn_prophet, code_vulnerability_scanner_agent, data_trend_anomaly_agent, ephemeral_executor, headless_terminal_agent, insight_mage, internet_monitor_agent, morphic_adapter, performance_guardian, sentinel_agent, skill_gc, skill_ingestor, skill_librarian, user_retention_risk_agent, vulnerability_prophet` — **`research_assistant.py` does not exist** (verified by directory listing *and* by a tracked-file search returning zero hits).

**Impact:** `POST /api/agents/research/search`, `/research/summarize`, `/research/cite` (`agents.py:52,71,82`) each wrap the import in `try/except Exception → HTTPException(500, str(exc))`. All three return **HTTP 500 unconditionally**. This is not "unverified" — the dependency is provably absent.

### 3.8 Dual agent routers with divergent conventions (`ERR-H07`)

`backend/api/routers.py` mounts **both**:

| ALL_ROUTERS entry | Module | Own prefix | Full path | Router-level auth |
|---|---|---|---|---|
| `routers.py:99` | `api.routes.agents` | `/api/agents` | `/api/agents/…` | `Depends(get_current_user_token)` |
| `routers.py:100` | `api.routes.agent` | `/api/v1/agents` | `/api/v1/agents/execute` | `Depends(verify_autonomous_agent_token)` |

No path collision, but the coexistence is the direct cause of `ERR-A02`'s plural/singular confusion, and the stale comment at `agents.py:28–29` still claims the Studio client calls `/api/v1/agents` while the client actually calls `/api/agents/`. Two agent surfaces with two auth schemes and two versioning conventions is an architecture defect, not merely a bug.

### 3.9 Blocking synchronous call inside an async route (`ERR-H08`)

```
backend/api/routes/agent.py:36   async def execute_agent_task(...)
backend/api/routes/agent.py:54   exec_res = agent.execute(task_description=payload.prompt)
backend/core/agents/framework/task_runner_agent.py:66   def execute(self, task_description, context=None) -> dict
```

`brain/autonomous_agent.py` is a **re-export facade** (`from core.agents.framework.task_runner_agent import AutonomousAgent, StepResult`), and the real `execute` is **synchronous**. With no `await` / `run_in_threadpool`, the call **blocks the event loop** for the entire agent run. Additionally `background_tasks: BackgroundTasks` is injected but never used, and `AgentTaskRequest.auto_execute` is declared but never read — the route pretends to support background execution it does not implement.

---

## 4. Governance & Tooling Defects — "Gates That Don't Gate" (P0/P1)

| ID | Artifact | Defect | Evidence |
| :--- | :--- | :--- | :--- |
| **ERR-M01** | `scripts/find_stub_data.py` (`.pre-commit-config.yaml:137` — *"Gate 1 — Stub & Placeholder Data Blocker"*) | The gate scans for only **20 literal patterns**, e.g. `simulated_api_key_\w+`, `YOUR_API_KEY_HERE`, `MOCK_[A-Z_]+ =`, `Mock different responses based on provider`. It has **no pattern for `mock`, `mock_png`, `Math.random`, `Simulate`, `fake`, `placeholder implementation` in prose, or hardcoded fake responses.** | Running it on `backend/` prints **`[PASS] No stub patterns found`** while `_crown_jewel.py` (docstring: *"Crown Jewel mock endpoints"*), `billing_api.py` (`mock_session_123`) and `cloud_sandbox_orchestrator.py` (mock stdout) all live in `backend/`. **False PASS.** |
| **ERR-M02** | `.github/workflows/ci.yml` | The stub gate is **not referenced in CI at all** — a repo-wide search for `find_stub_data` matches only `.pre-commit-config.yaml`. | Gate runs only for developers who installed the local pre-commit hook. Stub code merges freely. |
| **ERR-M03** | `scripts/feature_parity_sentinel.py:729` | The platform's primary route-parity auditor **crashes on Windows**: `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f50d'` (the 🔍 emoji in `print("🔍 Scanning backend (AST)...")`). | Traceback captured verbatim. The `NON_WORKING_COMPONENTS_FULL_AUDIT.md` scan result (643 findings) **cannot be reproduced locally**, so its baseline cannot be verified or updated on Windows. |
| **ERR-M04** | `backend/htmlcov/`, `.coverage`, `coverage.xml`, `htmlcov/` | Present in the working tree (untracked/ignored) — audit surface is cluttered. Verified **not** tracked (`git ls-files "htmlcov/*"`, `"*.xml"`, `"*.tmp"` all empty), so this is hygiene-only, not a data leak. | `git ls-files` counts |
| **ERR-M05** | Remote refs | **~320 remote branches** are fetched locally, including 79 `dependabot/*`, 16 `auto-fix-main-*`, 11 `promote/staging-*`, 7 `test/supremeai-unit-*`, and multiple `kilo/*`, `devin/*` branches. | `git branch -a` output (see evidence bundle) |
| **ERR-M08** | `.gitignore:479` — global `*.txt` rule | `*.txt` is ignored repo-wide (only narrow `!requirements*.txt` exceptions exist). **Consequence: text-based audit evidence can never be committed**, directly conflicting with the AGENTS.md rule that consequential findings must preserve evidence. Discovered when this audit's own `docs/audits/evidence/2026-09-15/*.txt` did **not** appear in `git status -uall`; `git check-ignore -v` returned `.gitignore:479:*.txt`. | **Fix applied with this change:** a scoped negation `!docs/audits/evidence/**` was added to `.gitignore`, so evidence is preservable without re-opening scratch-file commits. |

---

## 5. Orphan Backend Surface — Expanded from 22 to 57 Families (P1)

The existing register lists 22 orphan APIs (Missions, MCP Hub, Circles). Static reconstruction finds **57 route families whose leaf segment never appears anywhere in `frontend/src`**. Below are the families *not* already covered by the existing register — i.e. **newly identified orphans**.

**Entire admin `commandcenter` surface:** `/admin-api/commandcenter/{build/*, events, health, metrics, money/*, observe/*, operate/*}` — a full admin console API with **no frontend consumer**.

```
/admin-api/cost-caps            /api/admin/model-branding        /tools/image-to-code
/admin-api/data-export          /api/billing/add-funds           /tools/image-to-component
/admin-api/health-stream (WS)   /api/billing/checkout            /tools/image-to-palette
/admin-api/ping-all             /api/billing/wallet              /tools/image-to-tree
/admin-api/ping-service         /api/browser/browse-sessions     /tools/smell-check
/admin-api/service-categories   /api/chat/get_completion         /tools/vulnerability-check
/admin-api/service-topology     /api/chat/stream_chat            /tools/deploy/helm
/admin/free-tier-status         /api/comment-ai/handle-comment   /voice/process-audio
/admin/token-budget-stats       /api/comment-ai/stale-prs/{o}/{r} /ws/cost-updates (WS)
/api/admin-api/provider-readiness  /api/knowledge/ask-scribe     /config/validation-report
/api/admin-api/test-service     /api/memory/recall               /internal/run-daily-evolution
/api/admin/cloud-mesh/* (4)     /api/v1/collaborate/ws (WS)      /internet-monitor/start-monitoring
                                /api/v1/localization/* (3)       /llm-gateway/admin/circuit-breaker/reset/{name}
                                /api/v1/meta-ai/* (8)            /payments/checkout
                                /api/v1/pr-review/* (2)          /security/vulnerabilities/scan-project
                                /api/v1/syncguard/audit          /integrations/email/gmail
                                /api/v1/tools-registry/* (4)     /api/voice/stream_audio
                                /auth/sso/oidc/* (4)             /diagram/{api-spec,to-kubernetes,to-schema,to-terraform}
                                /auth/sso/saml                   /skills
```

**Notable observations:**

- **`ERR-M06` — `/api/admin-api/…` double-prefix anomaly.** Two routes register at `/api/admin-api/provider-readiness` and `/api/admin-api/test-service`; the `api` and `admin-api` prefixes are **concatenated**. Almost certainly an unintended mount+decorator collision, yielding a path no client would guess.
- **Six `image-to-*` tools are unreachable** (`image_to_code.py` exists in `backend/tools/`): an entire capability family with zero exposure — a direct instance of the constitution's "orphan capability" anti-pattern.
- **`/api/v1/meta-ai/*` (8 routes incl. `/breed`)** is orphaned while `meta_ai.py` is registered — the agent-breeding engine has no UI.
- **`/payments/checkout` and `/api/billing/checkout`** are both orphaned, yet billing is a live customer concern — consistent with `ERR-G01` (the mock checkout is what shipped instead).

**Caveat:** orphan classification derives from `frontend/src` text presence only. A family may legitimately be consumed by an external client, an MCP tool, CI, or a WebSocket-only client. Each family needs an explicit **wire-or-delete** decision; this list is triage input, not a deletion mandate.

---

## 6. Security & Guard-Consistency Findings (P0/P1)

### 6.1 `ERR-S01` (P0): Inconsistent `mock-` token acceptance in admin auth

`backend/core/admin_routes.py` enforces **two different policies for the same `mock-` token prefix**:

| Endpoint | Line | Guard style | Rejects when |
|---|---|---|---|
| `/api/admin/firebase-login` | 174–183 | **Allow-list** | `env NOT IN {local, test, testing}` → 403 |
| `/api/admin/firebase-totp-setup` | 304–311 | **Allow-list** | same shape |
| `/api/admin/firebase-totp-recover` | 365–369 | **Deny-list** | `env == "production"` only |
| `/api/admin/firebase-totp-verify` | 412–418 | **Deny-list** | `env == "production"` only |
| `_ensure_admin_authorized()` | 278–279 | **Deny-list** | `env != "production"` → **returns early (authorizes)** |

Verified consequences:

1. **Default-config fail-open.** `backend/core/config.py:98` — `env: str = Field(default="local", validation_alias="ENV")`. If `ENV` is **unset or misspelled**, `settings.env == "local"`, so the deny-list endpoints accept `mock-*`, set `uid = "mock-admin-uid"`, and `_ensure_admin_authorized` returns **without any role or Firestore check**.
2. **`ENV=prod` is asymmetric.** `config.py:169` treats **both** `"production"` and `"prod"` as production (`is_bypass_allowed → False`), but `admin_routes.py:278/366/414` compare **only** against the literal `"production"`. Under `ENV=prod` the deny-list paths activate while the platform's own bypass guard believes it is in production. The strict allow-list paths (login / TOTP-setup) are **not** affected.
3. **The docstring at `admin_routes.py:269–276`** records that TOTP flows mint an admin JWT (`role:"admin"`) and that a prior P0 was fixed by adding `_ensure_admin_authorized`. That fix is therefore load-bearing — and its guard is the **weakest** of the three variants in the file.

> **Claim status:** verified by **static reading of all five sites** plus the `config.py` default. I did **not** execute an exploit (no running instance with a known `ENV` was available).
> **Recommended remediation:** (a) one shared `is_mock_token_allowed()` helper using allow-list semantics; (b) treat `prod`, `staging`, and **unset** `ENV` as fail-closed; (c) an automated test asserting every `mock-` site rejects under `ENV=prod` **and** under unset `ENV`.

### 6.2 `ERR-S02` (P1): Client-side workaround for a live CORS defect

`frontend/src/services/apiClient.ts:262–279` documents, **inside the code**, a production CORS failure:

> *"the deployed backend's CORS allow-list still omits 'idempotency-key', sending that header on ANY request fails the CORS preflight outright (Starlette returns 400 **'Disallowed CORS headers'** for OPTIONS), which made login (and every key-less route) impossible on the deployed app — users saw a misleading 'Network Error' toast on /login."*

The mitigation is a hardcoded `IDEMPOTENCY_REQUIRED_PREFIXES` list (`/api/task`, `/api/github`, `/api/auth/callback`, `/api/pr`, `/api/agent`). Consequences:

- The header is attached **only** for those five prefixes — a hand-maintained mirror of server behaviour that will drift. Any route requiring idempotency outside the list silently loses it.
- `/api/v1/agents/execute` does **not** match `/api/agent`, so the live agent flow never receives an idempotency key. Whether that is correct is **unverified** (requires the backend's required-prefix list).

> **Follow-up:** the CORS `allow_headers` setting could not be located — a case-insensitive search for `allow_headers` across `backend/core/config.py`, `backend/main.py`, and `backend/api/middleware/*.py` returned **no matches**. Whether CORS is configured elsewhere (or via a middleware assembled at runtime) must be established before the client workaround can be removed. **This absence is itself suspicious and is logged as an open question, not as a confirmed defect.**

### 6.3 `ERR-S03` (informational — verified NOT defective)

`backend/core/resilience/chaos_engine.py:10–11` reads `os.getenv("ENABLE_CHAOS_MODE", "False").lower() == "true"` — i.e. **opt-in and correctly gated**. The simulated `TimeoutError` / `ConnectionError` injections cannot fire unless explicitly enabled. Recorded here to pre-empt a false positive: this file legitimately contains the word "simulated".

Also verified **not** a defect: **no `.env` file is tracked** (`git ls-files` matches only `.env.example`, `.secrets-allowlist.json`, `tools/firebase_functions_v1/.env.example`), and no `htmlcov/`, `*.xml`, or `*.tmp` artifacts are tracked.

---

## 7. Stub/Mock Census & Dependency Findings

### 7.1 Scale of the stub surface (`ERR-M07`)

The existing register's Class D lists **6** mock items. The executed census finds **1,157** backend hits in 340 files and **280** frontend hits in 145 files (tests excluded). Full per-file breakdowns: `docs/audits/evidence/2026-09-15/stubs_backend.txt` and `stubs_frontend.txt`.

**Highest-density backend files requiring owner review** (hit count in brackets). These are *candidates*, since legitimate uses of the words exist (e.g. `unittest.mock` in test-support modules, `chaos_engine`, commented-out code):

```
backend/core/testing/qa_suite.py (30)                     backend/core/config_fields.py (8)
backend/core/admin_routes.py (21)                         backend/core/deployment/production_deploy.py (8)  ← ERR-G02
backend/core/human_behavior.py (15)                       backend/core/resilience/chaos_engine.py (8)       ← S03 OK
backend/tools/devops/docker_sandbox.py (15)               backend/api/routes/browser/_crown_jewel.py (7)    ← G03/G05/G06/G11
backend/tools/browser/playwright_browser_agent.py (14)    backend/core/evolution_module.py (7)
backend/core/self_evolution/digital_twin/simulator.py (13) backend/core/health/proactive_healer.py (7)
backend/core/orchestration/cloud_sandbox_orchestrator.py (12) ← ERR-G04   backend/core/self_evolution/auto_skill_creator.py (7)
backend/core/tier8/agent_evolution_engine.py (12)         backend/agents/ide/trio_adapters.py (6)
backend/tools/browser/web_fallback_agent.py (10)          backend/browser/semantic_dom.py (6)
backend/api/routes/billing_api.py (5)                     ← ERR-G01
```

> **Method note:** the census uses *broad* keyword matching to maximise recall. `scripts/testing/_gen_services.py` (`unittest.mock`) is test-support and likely benign; but `qa_suite.py` also **simulates security checks** ("Simulate SQL injection check", "Simulate XSS check"), which warrants the same false-assurance review as `ERR-G03`.

### 7.2 Frontend mock surface — notable files

`frontend/src/providers/MockSwarmProvider.tsx` (8 — see `ERR-G09`); `frontend/src/components/admin/shared/ActionCard.tsx` (9); `frontend/src/components/admin/InteractiveChatTab.tsx` (4 — matches register `ERR-D04`).

**`ERR-G12` (new Class G finding):** `frontend/src/components/admin/shared/ActionCard.tsx:57` — `setTimeout(() => setActionStatus('✅ Code executed successfully!'), 1500)`. This is an **admin** surface that fabricates success messages on a 1.5–5 s timer, so an administrator can be told an action succeeded while nothing was dispatched.

### 7.3 Dependency findings

| ID | Finding | Detail |
|---|---|---|
| **ERR-P01** | **Intra-package Storybook version conflict** | `frontend/package.json` declares `"storybook": "^10.5.10"` (line 107) **and** `"@storybook/addon-essentials": "^8.6.14"` (line 81) plus `@storybook/blocks ^8.6.14`, `@storybook/react ^8.6.18`, `@storybook/react-vite ^8.6.18`, `@storybook/test ^8.6.15` — v8 addons against a v10 core. `addon-essentials` was folded into core in SB9 and **removed** in SB10. The repo mixes v10 (`addon-a11y`, `addon-docs`, `addon-vitest`, `eslint-plugin-storybook`) and v8 packages simultaneously. **This is a stronger and *different* problem than the register's `ERR-F04` "Dependabot drift"** — it is an internally inconsistent dependency set, not merely an outdated one. |
| **ERR-P02** | `react-router-dom` pinned to v6 | Confirmed `^6.30.6` (`package.json:66`) — matches register `ERR-F04`. |
| **ERR-P03** | Audit tooling not reproducible | `feature_parity_sentinel.py` cannot run on Windows (`ERR-M03`); `find_stub_data.py` runs but is blind (`ERR-M01`). The platform's two audit gates are therefore **non-functional as gates**. |

---

## 8. Consolidated Remediation Priority

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ P0 — IMMEDIATE (silent-wrongness & customer-visible data loss)                │
│  1. ERR-G01  billing mock checkout  → never fabricate a paid success state    │
│  2. ERR-G02  production_deploy simulates deploy AND rollback                  │
│  3. ERR-S01  mock-token guard inconsistency (fail-open on unset ENV / prod)   │
│  4. ERR-G03  security-scan always returns score 100, issues []                │
│  5. ERR-H01  preferences 404 × 5 call sites (theme/locale/profile lost)       │
│  6. ERR-H02  skill install + uninstall 404                                    │
│  7. ERR-H06  agents.research_assistant missing → 3 endpoints always 500       │
├──────────────────────────────────────────────────────────────────────────────┤
│ P1 — CORE (correctness of the control plane)                                  │
│  8. ERR-M01/M02  make the stub gate real AND wire it into CI                  │
│  9. ERR-H04  ecosystem admin client: 17 dead endpoints (wire or delete)       │
│ 10. ERR-H07/H08  unify the two agent routers; stop blocking the event loop    │
│ 11. ERR-G04/G05/G12  sandbox stdout, task-step, ActionCard fake success       │
│ 12. ERR-H03/H05  workspaces bind-target + knowledge learning loop             │
│ 13. ERR-S02  fix backend CORS allow_headers, then delete the client hack      │
├──────────────────────────────────────────────────────────────────────────────┤
│ P2 — HYGIENE & SURFACE                                                        │
│ 14. ERR-M03  make feature_parity_sentinel.py Windows-safe (stdout encoding)   │
│ 15. §5       wire-or-delete the 57 orphan route families                      │
│ 16. ERR-M06  fix the /api/admin-api double prefix                             │
│ 17. ERR-P01  reconcile Storybook v8/v10;  ERR-P02 router v7 migration        │
│ 18. ERR-M05  prune ~320 stale remote branches                                 │
│ 19. ERR-C04  correct/remove the stale register entry for browserService.ts    │
└──────────────────────────────────────────────────────────────────────────────
```

---

## 9. Explicit Statement of Limits (what was NOT verified)

Per the repository's "never claim verification without evidence" rule:

- **No runtime execution of the application.** The backend was never started with dependencies installed; **no endpoint was called over HTTP**. Every "404 / 422 / 500" claim derives from static route-table reconstruction plus source reading.
- **No test suite was run.** `pytest`, `vitest`, and Playwright were not executed in this session.
- **Auth behaviour was not executed.** `ERR-S01` is a static guard-inconsistency finding; exploitability depends on the deployed `ENV` value, which is unknown in this environment.
- **The parity/route model is approximate.** 149 modules resolved with **0 unresolved**, 765 routes reconstructed — but routers mounted outside `ALL_ROUTERS`, `app.include_router(..., prefix=...)` compositions, and dynamically generated routes may be missing, which would produce *false* "missing" candidates. §3.6 items are labelled **[CANDIDATE]** for exactly this reason.
- **No secret scanning or penetration testing** was performed; the repo's own `gitleaks` / CodeQL configs were not run, and `.secrets-allowlist.json` / `secrets_registry.yaml` were not audited for staleness.
- **Chaos/self-evolution runtime behaviour** was not exercised.

**Reproduction commands:**

```bash
python scripts/audit/system_deep_scan_2026_09_15.py      # writes the six evidence files
python scripts/find_stub_data.py --path backend --fail-on HIGH
python scripts/feature_parity_sentinel.py --fail-on never   # currently crashes on Windows (ERR-M03)
```

---

*This document is a supplement, not a replacement. It must be read together with `SYSTEM_DEFECT_REGISTER_2026-09-15.md`; §1 records the corrections that should be applied to that register.*