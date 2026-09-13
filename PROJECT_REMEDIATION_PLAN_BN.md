# SupremeAI প্রকল্প: ঝুঁকি থেকে বাস্তব Fix Plan

> **উদ্দেশ্য:** এই নথিতে শুধু পরামর্শ নয়—প্রতিটি বড় ঝুঁকির জন্য কোথায় পরিবর্তন করতে হবে, কীভাবে করতে হবে, কীভাবে যাচাই করতে হবে এবং কোন পর্যায়ে কাজটি সম্পূর্ণ ধরা হবে তা দেওয়া হয়েছে।
>
> **ভিত্তি:** `AUDIT_REPORT_2026-09-10.md`, `STATUS.md`, `MASTER_PLAN.md`, `CHECKPOINT.md`, `PRODUCTION_ROADMAP_2026-09-11.md` এবং repository structure।
>
> **নীতি:** আগে নিরাপত্তা ও সত্যতা, তারপর reliability, তারপর নতুন feature। কোনো পরিবর্তন সরাসরি `main`-এ নয়; branch + PR + CI evidence ব্যবহার করতে হবে।

---

## ১. P0: Secret এবং credential ঝুঁকি বন্ধ করুন

### ঝুঁকি

Render credential আগে chat/transcript-এ ব্যবহৃত হয়েছে। Live key এখন scan-এ পাওয়া না গেলেও key compromise ধরে rotate করা উচিত।

### কোথায় পরিবর্তন হবে

- `backend/tools/learning/Diagnosed deployment failures and organizations.ini`
- `backend/tools/learning/`
- `.secrets-allowlist.json`
- `.github/workflows/ci.yml`
- `backend/core/security/secret_vault.py`
- `backend/utils/environment.py`

### কীভাবে fix করবেন

1. Render dashboard-এ `RENDER_API_KEY` এবং `RENDER_API_KEY_BACKUP` revoke করে নতুন key তৈরি করুন।
2. নতুন key repository-তে লিখবেন না; Infisical বা Vercel environment variable-এ রাখুন।
3. `backend/tools/learning/Diagnosed deployment failures and organizations.ini` ফাইলটি admin approval নিয়ে repository থেকে সরান। এটি code package-এর মধ্যে transcript হিসেবে থাকা উচিত নয়।
4. `.gitignore`-এ যোগ করুন:

   ```gitignore
   *.ini.local
   *.secret
   *.credentials
   backend/tools/learning/*.ini
   ```

5. `backend/core/security/secret_vault.py`-কে একমাত্র application secret access layer করুন। Route, agent বা provider adapter থেকে সরাসরি secret read নিষিদ্ধ করুন।
6. `backend/utils/environment.py`-এ environment variable-এর truthiness parsing এক জায়গায় রাখুন; `"false"`, `"0"`, empty string যেন সত্য হিসেবে গণ্য না হয়।
7. `.github/workflows/ci.yml`-এ secret scan blocking করুন। Scan fail হলে workflow pass করা যাবে না।

### যাচাই

- TruffleHog/Gitleaks scan clean
- `git log -S "RENDER_API_KEY" --all`-এ actual value নেই
- secret rotation-এর audit evidence আছে
- application log-এ secret value বা full token নেই

### সম্পূর্ণ ধরা হবে যখন

Credential rotate, transcript অপসারিত, CI secret scan blocking এবং runtime secret access centralised হবে।

---

## ২. P0: Backend authentication এবং tenant isolation শক্ত করুন

### ঝুঁকি

AI/MCP system-এ শুধু endpoint authentication যথেষ্ট নয়। কোনো authenticated user যেন অন্য tenant-এর task, memory, workspace, credential, execution বা audit record পড়তে/পরিবর্তন করতে না পারে। এটি BOLA/IDOR ঝুঁকি।

### কোথায় পরিবর্তন হবে

- `backend/core/security/authentication/auth_middleware.py`
- `backend/core/security/authentication/rbac.py`
- `backend/core/security/tool_gateway.py`
- `backend/core/task_policy.py`
- `backend/runtime/task_context.py`
- `backend/database/tenant_db.py`
- `backend/api/routes/task.py`
- `backend/api/routes/task_gateway.py`
- `backend/api/routes/unified_memory_api.py`
- `backend/api/routes/workspaces_route.py`
- `backend/api/routes/tools_ops.py`
- `backend/api/routes/tenant_admin.py`

### কীভাবে fix করবেন

প্রতিটি resource query এবং mutation-এর আগে এই scope বাধ্যতামূলক করুন:

```text
actor_id → tenant_id → resource_id → permitted action
```

1. `task_context.py`-এ immutable request context রাখুন:
   - `actor_id`
   - `tenant_id`
   - `roles`
   - `scopes`
   - `correlation_id`
2. Route path থেকে আসা `tenant_id` কখনো trusted identity হিসেবে ব্যবহার করবেন না। Session/token থেকে tenant resolve করুন; path tenant কেবল equality check হিসেবে ব্যবহার করুন।
3. `tenant_db.py`-এর সব read/write helper-এ `tenant_id` required parameter করুন। Optional default রাখবেন না।
4. `tool_gateway.py`-তে tool call allow করার আগে tenant, capability, resource এবং action যাচাই করুন।
5. Admin route-এ সাধারণ user-এর `tenant_id` override নিষিদ্ধ করুন।
6. Memory query-তে `tenant_id` এবং user-scoped data হলে `user_id` বাধ্যতামূলক filter করুন।
7. Object lookup না পেলে `404` দিন; অন্য tenant-এর object আছে কি না বোঝায় এমন error দেবেন না।
8. প্রতিটি denied action `audit_logger.py`-তে actor, tenant, resource, action, reason সহ লিখুন।

### নতুন test কোথায় লিখবেন

- `backend/tests/security/test_cross_tenant_isolation.py`
- `backend/tests/security/test_hardening_controls.py`
- `backend/tests/core/test_multi_tenant_isolation.py`
- `backend/tests/api/test_route_rbac_matrix.py`

প্রতিটি resource-এর জন্য অন্তত এই test লিখুন:

```text
Tenant A token + Tenant B resource → 404/403
User A token + User B private memory → 404/403
Non-admin + admin endpoint → 403
Valid tenant + invalid resource → 404
```

### সম্পূর্ণ ধরা হবে যখন

Critical route-এর cross-tenant test pass করবে এবং query helper-এ unscoped access আর থাকবে না।

---

## ৩. P0: Thin-client key exposure বন্ধ করুন

### ঝুঁকি

`frontend/src/services/SupremeAIService.ts`-এ OpenRouter direct fetch থাকার কথা `CHECKPOINT.md` এবং audit-এ উল্লেখ আছে। Frontend থেকে provider call হলে secret expose হতে পারে এবং policy bypass হতে পারে।

### কোথায় পরিবর্তন হবে

- `frontend/src/services/SupremeAIService.ts`
- `frontend/src/services/`-এর provider-specific service files
- `backend/api/routes/stream_chat_sse.py`
- `backend/api/routes/task_gateway.py`
- `backend/core/providers/`
- `frontend/.env.example`

### কীভাবে fix করবেন

1. `SupremeAIService.ts` থেকে OpenRouter URL, API key এবং direct provider fetch সরান।
2. Frontend কেবল backend-এর authenticated endpoint call করবে।
3. Backend provider adapter-এর মাধ্যমে model call করবে; provider key server-side environment-এ থাকবে।
4. Offline mode দরকার হলে কেবল explicitly configured local Ollama endpoint ব্যবহার করুন; public production build-এ provider key fallback রাখবেন না।
5. Frontend bundle scan-এ provider key pattern এবং `OPENROUTER_API_KEY` search যোগ করুন।
6. Backend-এ model/provider selection allowlist করুন; client-supplied arbitrary URL বা model blindly গ্রহণ করবেন না।

### যাচাই

- `frontend/dist` বা production bundle-এ কোনো provider key নেই
- Browser network trace-এ সরাসরি OpenRouter request নেই
- Backend endpoint ছাড়া frontend model response পায় না
- Unauthorized request rejected হয়

---

## ৪. P0: Migration system একটিতে নামিয়ে আনুন

### ঝুঁকি

দুটি migration tree আছে:

- `backend/database/migrations/`
- `backend/alembic_migrations/versions/`

দুটি source of truth থাকলে staging এবং production schema আলাদা হয়ে যেতে পারে।

### কোথায় পরিবর্তন হবে

- `backend/alembic.ini`
- `backend/alembic_migrations/env.py`
- `backend/alembic_migrations/versions/`
- `backend/database/migrations/`
- `backend/pyproject.toml`
- `backend/README.md`
- `.github/workflows/ci.yml`

### কীভাবে fix করবেন

1. সিদ্ধান্ত লিখুন: **Alembic canonical migration system**।
2. `backend/database/migrations/`-এর প্রতিটি SQL migration inventory করুন।
3. ইতিমধ্যে production-এ থাকা schema-এর জন্য একটি baseline Alembic revision তৈরি করুন।
4. পরের raw SQL migration Alembic-এর বাইরে নিষিদ্ধ করুন।
5. পুরনো SQL-গুলো `backend/database/migrations/legacy/`-এ read-only archive হিসেবে রাখুন অথবা admin approval নিয়ে সরান।
6. `backend/README.md`-এ একমাত্র migration command লিখুন:

   ```bash
   alembic upgrade head
   ```

7. CI-তে fresh database তৈরি করে `alembic upgrade head` চালান এবং schema validation করুন।
8. Production migration-এর আগে backup, dry-run এবং rollback plan বাধ্যতামূলক করুন।

### যাচাই

- Fresh database থেকে `upgrade head` সফল
- Previous production snapshot থেকে upgrade সফল
- Alembic ছাড়া migration চালালে CI fail
- Schema diff empty

---

## ৫. P1: Scripts/tools-এর real runtime bug ঠিক করুন

### ঝুঁকি

Audit-এ `tools`, `scripts`, `packages`, `.github/scripts`-এ প্রায় ১৮১টি `F821 undefined-name` পাওয়া গেছে। এগুলো operational script হওয়ায় runtime-এ সরাসরি crash করবে।

### নির্দিষ্ট file

প্রথম batch:

- `scripts/core_engine/tool_ranker.py`
- `scripts/db/auto_seed.py`
- `scripts/devops/cloud_watchman.py`
- `scripts/devops/config/cli.py`
- `tools/knowledge/card_builder.py`
- `scripts/devops/config/validators.py`

### কীভাবে fix করবেন

1. প্রতিটি F821-এর জন্য import, rename, missing implementation বা dead path—একটি সিদ্ধান্ত নিন।
2. Missing type হলে সঠিক shared type import করুন; placeholder `Any` দিয়ে ঢাকবেন না।
3. `logger`-এর মতো dependency হলে module-level `logging.getLogger(__name__)` ব্যবহার করুন।
4. Undefined validator বা service হলে বাস্তব implementation import করুন; silent fallback রাখবেন না।
5. Script-এর অন্তত একটি smoke test লিখুন।
6. Unused বা abandoned script হলে delete না করে admin approval request তৈরি করুন—repository constitution অনুযায়ী।

### CI কোথায় পরিবর্তন হবে

- `.github/workflows/ci.yml`

Backend-only ruff-এর পাশাপাশি root job যোগ করুন:

```bash
ruff check tools scripts packages .github/scripts
```

প্রথম ধাপে F821 blocking করুন; পরের ধাপে style warnings কমান।

### সম্পূর্ণ ধরা হবে যখন

সব F821 resolve বা approved exception হবে এবং CI নতুন F821 আটকাবে।

---

## ৬. P1: Test collection এবং skipped tests পরিষ্কার করুন

### ঝুঁকি

`respx` না থাকায় test collection ভাঙে এবং ছয়টি test missing module-এর কারণে skip হয়। Skip থাকা মানে capability সত্যিই কাজ করে না বা test stale।

### কোথায় পরিবর্তন হবে

- `backend/pyproject.toml`
- `backend/README.md`
- `backend/tests/tools/test_sso_integrator_comprehensive.py`
- `backend/tests/scripts/test_billing_fraud_detector.py`
- `backend/tests/scripts/test_billing_quota_enforcer.py`
- `backend/tests/scripts/test_billing_usage_reporter.py`
- `backend/tests/test_strategic_patches/test_cognitive_router.py`
- `backend/tests/core/test_grpc_client.py`
- `backend/tests/api/test_task_router.py`

### কীভাবে fix করবেন

1. Standard setup হিসেবে `poetry install` document করুন; bare pip install-কে supported setup হিসেবে রাখবেন না।
2. `respx` dev dependency হিসেবে lock file-এ আছে কি না নিশ্চিত করুন; CI ও local command একই করুন।
3. Billing tests-এর জন্য সিদ্ধান্ত নিন:
   - `scripts/billing/` বাস্তবে দরকার হলে তিনটি module implement করুন;
   - দরকার না হলে tests এবং stale dependency admin approval নিয়ে archive করুন।
4. Cognitive Router test-এর জন্য `backend/brain/cognitive_router.py`-এর বাস্তব contract সম্পূর্ণ করুন অথবা test-কে planned test হিসেবে আলাদা করুন।
5. gRPC test-এর `protos` generation pipeline তৈরি করুন; generated file commit করবেন না হলে CI generation বাধ্যতামূলক করুন।
6. Permanent `pytest.skip` রেখে issue বন্ধ করবেন না; প্রত্যেক skip-এর owner ও deadline রাখুন।

### যাচাই

```bash
poetry install
poetry run pytest --collect-only
poetry run pytest -q
```

Collection error শূন্য এবং unexplained skip শূন্য হতে হবে।

---

## ৭. P1: Coverage gate বাস্তব করুন

### ঝুঁকি

`.github/workflows/ci.yml`-এ backend coverage 35% এবং frontend coverage 9%—এগুলো regression আটকানোর জন্য খুব কম।

### কোথায় পরিবর্তন হবে

- `.github/workflows/ci.yml`
- `backend/pyproject.toml`
- `frontend/vitest.config.ts`
- `backend/tests/`
- `frontend/src/`

### কীভাবে fix করবেন

1. আগে CI-তে actual coverage report artifact হিসেবে publish করুন।
2. প্রথম release-এ gate করুন:
   - backend: 65%
   - frontend: 40%
3. প্রতি মাসে threshold বাড়ানোর issue তৈরি করুন।
4. Security, tenant isolation, tool gateway এবং task execution module-এর জন্য আলাদা higher threshold রাখুন।
5. Coverage দিয়ে untested critical path আড়াল করবেন না; mission tests আলাদা বাধ্যতামূলক রাখুন।

### সম্পূর্ণ ধরা হবে যখন

Coverage threshold fail করলে CI fail হবে এবং report PR-এ দেখা যাবে।

---

## ৮. P1: Frontend quality debt কমান

### ঝুঁকি

Frontend-এ ১২৬টি ESLint warning আছে, যার মধ্যে ৫৭টি `no-explicit-any`, ৪৮টি unused variable এবং ১২টি `no-console`।

### কোথায় পরিবর্তন হবে

প্রথমে audit-এ চিহ্নিত file:

- `frontend/src/components/ChatInterface.tsx`
- `frontend/src/components/BrowserPreview.tsx`
- `frontend/src/providers/ThemeProvider.tsx`
- `frontend/src/hooks/useEventBus.ts`
- `frontend/src/services/authStore.ts`
- `frontend/src/services/ecosystem/api.ts`
- `frontend/src/services/llm.router.ts`
- `frontend/src/services/secureWebSocket.ts`
- `frontend/src/components/InteractiveChatTab.tsx`
- `frontend/src/components/SlashCommandMenu.tsx`
- `frontend/src/components/ServiceHealthMonitor.tsx`
- `frontend/src/components/AuthGuards.tsx`
- `frontend/src/routes/workspaceFeatureRoutes.tsx`

### কীভাবে fix করবেন

1. Unused imports এবং variables সরান।
2. `any`-এর বদলে domain interface বা `unknown` + runtime narrowing ব্যবহার করুন।
3. `console.*`-এর বদলে central logger ব্যবহার করুন; production bundle-এ debug log নিষিদ্ধ করুন।
4. `useEventBus.ts` এবং `SlashCommandMenu.tsx`-এর hook dependency warning যুক্তিসঙ্গতভাবে ঠিক করুন; warning suppress করবেন না।
5. Component file থেকে non-component export আলাদা utility file-এ সরান।
6. ESLint warning count CI artifact হিসেবে রাখুন এবং ধীরে zero-এর দিকে নামান।

---

## ৯. P1: Bare exception এবং silent failure বন্ধ করুন

### ঝুঁকি

নিচের production file-গুলোতে bare `except:` আছে; এতে security, provider failure এবং data corruption লুকিয়ে যেতে পারে।

### কোথায় পরিবর্তন হবে

- `backend/api/routes/dock_integrations.py`
- `backend/agents/ide/trio_adapters.py`
- `backend/pyerrorfix/core/catalog.py`
- `backend/pyerrorfix/detectors/`
- `backend/pyerrorfix/fixers/except_fixer.py`
- `backend/tools/code/code_smell_detector.py`
- `backend/core/security/audit_logger.py`

### কীভাবে fix করবেন

1. `except:`-এর বদলে নির্দিষ্ট exception ধরুন।
2. Expected failure হলে structured result return করুন।
3. Unexpected failure হলে correlation ID সহ log করুন এবং যথাযথ error raise করুন।
4. Secret, token, prompt content বা ব্যক্তিগত data log করবেন না।
5. Retry করা নিরাপদ কি না তা আলাদা করুন; সব exception retry করবেন না।
6. Failure path-এর test লিখুন—বিশেষত timeout, invalid response, permission denial এবং provider outage।

---

## ১০. P1: MCP/tool execution-এর জন্য policy gateway বাধ্যতামূলক করুন

### ঝুঁকি

MCP capability discovery শক্তিশালী হলেও tool call ভুল scope, prompt injection, SSRF বা excessive privilege তৈরি করতে পারে। URL বা model instruction কখনো authority হতে পারে না।

### কোথায় পরিবর্তন হবে

- `backend/core/security/tool_gateway.py`
- `backend/tools/mcp/mcp_server.py`
- `backend/tools/mcp/mcp_workspace.py`
- `backend/tools/mcp/mcp_github_cicd.py`
- `backend/tools/mcp/mcp_cloud_deploy.py`
- `backend/adaptive_engine/governed_executor.py`
- `backend/adaptive_engine/approval_workflow.py`
- `backend/core/security/audit_logger.py`
- `backend/tests/security/test_tool_policy_gateway.py`
- `backend/tests/security/test_hitl_state_machine.py`

### কীভাবে fix করবেন

প্রতিটি tool invocation-এর আগে:

```text
validate input
→ resolve tenant and actor
→ check capability allowlist
→ check resource scope
→ classify risk
→ request approval if needed
→ execute with timeout
→ verify output
→ write audit event
```

আরও নির্দিষ্টভাবে:

1. Tool registry-তে risk level, required scopes, allowed resource type এবং timeout রাখুন।
2. User prompt থেকে আসা URL সরাসরি fetch করবেন না; SSRF-safe URL validator ব্যবহার করুন।
3. Filesystem, shell, deployment, email, payment এবং deletion action default-deny করুন।
4. High-risk action-এর জন্য approval state machine ব্যবহার করুন; frontend flag দিয়ে approval bypass করা যাবে না।
5. Tool output untrusted data হিসেবে treat করুন; পরবর্তী tool instruction হিসেবে blind pass করবেন না।
6. প্রতিটি tool call-এর idempotency key এবং correlation ID রাখুন।

---

## ১১. P2: Dead code এবং duplicate surface কমান

### ঝুঁকি

Knip-এ unused dependency/export/type এবং duplicate export পাওয়া গেছে। কিন্তু repository constitution অনুযায়ী admin approval ছাড়া deletion করা যাবে না।

### কোথায় পরিবর্তন হবে

- `frontend/package.json`
- `frontend/src/`-এর Knip report-এ চিহ্নিত files
- `tools/vscode-extension/jest.config.js`
- `tools/vscode-extension/vitest.config.ts`
- `tools/vscode-extension/test/__mocks__/vscode.ts`
- `tools/vscode-extension/test/mocks/vscode.ts`
- `.knip.json`
- `MODULES_LIST.md`

### কীভাবে fix করবেন

1. Knip output থেকে candidate inventory তৈরি করুন।
2. প্রতিটি item-এর caller, owner, replacement এবং risk লিখুন।
3. Admin approval নিয়ে unused dependency/export সরান।
4. VS Code extension-এ একটি test runner এবং একটি mock directory রাখুন।
5. Duplicate default/named export-এর canonical form ঠিক করুন।
6. Package removal-এর পর clean install, typecheck ও test চালান।

---

## ১২. P2: Product scope কমিয়ে verified mission চালু করুন

### ঝুঁকি

অনেক operational/partially wired module থাকলেও user journey এবং reliability evidence তুলনামূলক দুর্বল। নতুন feature যোগ করলে complexity আরও বাড়বে।

### কোথায় পরিবর্তন হবে

- `backend/tests/missions/test_mission_suite.py`
- `backend/core/orchestration/`
- `backend/core/unified_router.py`
- `backend/core/task_policy.py`
- `backend/core/security/tool_gateway.py`
- `frontend/src/`-এর primary task flow
- `MASTER_PLAN.md`
- `ROADMAP_BANGLA.md`
- `MODULES_LIST.md`

### কীভাবে fix করবেন

প্রথম release-এর জন্য ৩টি mission lock করুন:

1. Repository/code task
2. Research + verified report
3. Bengali business/operator task

প্রতিটি mission-এ লিখুন:

- input contract
- allowed tools
- expected output
- verification rule
- retry limit
- cost budget
- failure reason
- audit evidence

`MODULES_LIST.md`-এ প্রতিটি module-কে `operational`, `wire-next`, `archive-pending`, `remove-approved` status দিন। Status claim-এর পাশে test বা runtime evidence link করুন।

---

## ১৩. Bengali capability-এর জন্য evaluation আগে তৈরি করুন

### কোথায় পরিবর্তন হবে

- `backend/agents/domain/bangla_nlp_agent.py`
- `backend/adapters/`
- `backend/tests/`
- `docs/`-এর Bangla documentation
- নতুন evaluation directory: `evals/bangla/`

### কীভাবে fix করবেন

1. বাংলা, Banglish এবং code-switching-এর ২০০–৫০০টি anonymized test case তৈরি করুন।
2. Category রাখুন:
   - instruction following
   - factuality
   - summarization
   - regional vocabulary
   - business/admin language
   - prompt injection resistance
3. Baseline provider বনাম Bangla adapter head-to-head score করুন।
4. Model training বা routing পরিবর্তনের আগে benchmark run বাধ্যতামূলক করুন।
5. User data evaluation set-এ নেওয়ার আগে consent, anonymization এবং retention policy লিখুন।

---

# বাস্তবায়নের ক্রম

## Sprint 1: Security stop-the-bleed

- Secret rotation
- Transcript removal
- Thin-client key removal
- Tenant isolation test
- Tool gateway deny-default
- Branch protection এবং required CI checks

## Sprint 2: Build এবং test সত্য করা

- `mypy.ini` encoding fix
- Root ruff gate
- `respx`/Poetry setup
- Six skipped test decision
- Coverage report এবং higher gate

## Sprint 3: Architecture cleanup

- Alembic canonical করা
- Bare exception fix
- Dead code approval inventory
- Duplicate VS Code test setup cleanup

## Sprint 4: Product reliability

- Three mission lock
- Pass³ mission suite
- Bengali evaluation set
- User-visible execution summary
- Cost, latency, success এবং retry metrics

---

# Done Definition

এই remediation phase সফল ধরা হবে যখন:

- কোনো known compromised credential active নেই;
- frontend-এ provider secret বা direct provider call নেই;
- critical route-এ cross-tenant access test pass করে;
- MCP/tool action policy gateway ছাড়া execute হয় না;
- Alembic একমাত্র migration source;
- root scripts/tools lint CI-তে blocking;
- test collection error এবং unexplained skip নেই;
- coverage gate বাস্তব এবং reportable;
- তিনটি mission end-to-end verification evidence সহ pass করে;
- `STATUS.md`-এর প্রতিটি production claim-এর পাশে evidence link থাকে।

# প্রত্যেক পরিবর্তনের PR checklist

- [ ] কোন risk ঠিক হচ্ছে তা issue/PR description-এ লেখা আছে
- [ ] নির্দিষ্ট file এবং test উল্লেখ আছে
- [ ] Tenant/auth/security impact review হয়েছে
- [ ] Migration বা data impact review হয়েছে
- [ ] Unit/contract/security test যোগ হয়েছে
- [ ] CI evidence সংযুক্ত আছে
- [ ] Rollback plan আছে
- [ ] Documentation (`STATUS.md`, `CHECKPOINT.md`, roadmap) আপডেট হয়েছে
- [ ] `main`-এ সরাসরি push নয়; branch ও review সম্পন্ন

> **মূল কথা:** নতুন capability যোগ করার আগে existing capability-কে secure, wired, tested এবং measurable করুন। SupremeAI-এর production advantage হবে “অনেক কিছু করতে পারে” নয়; “নিরাপদে, যাচাইসহ, বারবার একই মানে কাজ শেষ করতে পারে।”
