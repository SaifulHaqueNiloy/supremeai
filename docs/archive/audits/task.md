# SupremeAI Production-Readiness — Task Checklist

**Source:** [implementation_plan.md](file:///C:/Users/N/.gemini/antigravity-ide/brain/489c0d6f-f7b2-415f-84d3-9a2fb014b0aa/implementation_plan.md)  
**Repo:** `f:\supremeai`

---

## 🔴 Phase 1 — Immediate Launch-Blockers (Week 1)

### 1.1 — `build_test_failure_trend.py` JUnit Passed Bug Fix
- [ ] [`scripts/ci/build_test_failure_trend.py`](file:///f:/supremeai/scripts/ci/build_test_failure_trend.py) — `parse_junit()` ফাংশনে `passed += int(suite.get("passed", 0))` লাইনটি `passed = max(0, total - failed - errors - skipped)` দিয়ে replace করা
- [ ] লোকালে pytest রান করে `test-results.xml` generate করে script টেস্ট করা — `"passed"` এখন non-zero দেখাবে
- [ ] git commit + push

### 1.2 — Docker Container Non-Root Hardening
- [ ] [`frontend/Dockerfile`](file:///f:/supremeai/frontend/Dockerfile) — Nginx runtime stage-এ `USER nginx` + chown যোগ করা
- [ ] [`infrastructure/mcp-control-plane/Dockerfile`](file:///f:/supremeai/infrastructure/mcp-control-plane/Dockerfile) — Node runtime stage-এ `USER node` যোগ করা
- [ ] `docker build` দিয়ে উভয় ইমেজ build verify করা
- [ ] `docker run --rm <image> id` দিয়ে non-root confirm করা
- [ ] git commit + push

### 1.3 — GitHub Actions `timeout-minutes` যোগ করা
- [ ] [`.github/workflows/ci.yml`](file:///f:/supremeai/.github/workflows/ci.yml) — নিচের সব ২৫টি job-এ `timeout-minutes` যোগ:
  - [ ] `changes` → `timeout-minutes: 5`
  - [ ] `security` → `timeout-minutes: 15`
  - [ ] `advanced-checks` → `timeout-minutes: 15`
  - [ ] `registry` → `timeout-minutes: 10`
  - [ ] `backend-tests` → `timeout-minutes: 30`
  - [ ] `integration-test` → `timeout-minutes: 30`
  - [ ] `frontend-tests` → `timeout-minutes: 20`
  - [ ] `build` → `timeout-minutes: 20`
  - [ ] `build-mcp` → `timeout-minutes: 20`
  - [ ] `deploy-frontend` → `timeout-minutes: 25`
  - [ ] `publish-core-image` → `timeout-minutes: 25`
  - [ ] `publish-scraper-image` → `timeout-minutes: 25`
  - [ ] `publish-worker-alias` → `timeout-minutes: 25`
  - [ ] `render-budget-guard` → `timeout-minutes: 10`
  - [ ] `deploy-core` → `timeout-minutes: 25`
  - [ ] `deploy-worker` → `timeout-minutes: 25`
  - [ ] `deploy-scraper` → `timeout-minutes: 25`
  - [ ] `deploy-mcp` → `timeout-minutes: 25`
  - [ ] `db-schema-check` → `timeout-minutes: 15`
  - [ ] `deploy-cloudflare-worker` → `timeout-minutes: 15`
  - [ ] `notify-failure` → `timeout-minutes: 10`
  - [ ] `smart-summary` → `timeout-minutes: 10`
- [ ] git commit + push

### 1.4 — TruffleHog `curl | sh` → SHA-Pinned Action
- [ ] [`.github/workflows/ci.yml`](file:///f:/supremeai/.github/workflows/ci.yml) — `curl -sSfL ... | sh` স্টেপ খুঁজে বের করা
- [ ] `trufflesecurity/trufflehog` official GitHub Action দিয়ে replace করা
- [ ] `trufflesecurity/trufflehog@<commit-sha>` দিয়ে full SHA pin করা
- [ ] git commit + push

---

## 🟠 Phase 2 — Test Coverage Expansion (Week 2-4)

### 2.1 — Backend: Command Center Route Tests
- [ ] [`backend/tests/api/routes/commandcenter/`](file:///f:/supremeai/backend/tests/api/routes/commandcenter/) ডিরেক্টরি তৈরি করা + `__init__.py`
- [ ] `test_commandcenter_overview.py` — `GET /commandcenter/overview` endpoint unit tests
- [ ] `test_commandcenter_build.py` — `GET /commandcenter/build` endpoint unit tests
- [ ] `test_commandcenter_secure.py` — `GET /commandcenter/secure` endpoint unit tests
- [ ] `test_commandcenter_money.py` — `GET /commandcenter/money` endpoint unit tests
- [ ] `test_commandcenter_operate.py` — `GET /commandcenter/operate` endpoint unit tests
- [ ] `test_commandcenter_observe.py` — `GET /commandcenter/observe` endpoint unit tests
  - প্রতিটিতে: auth-required (401/403), authenticated (200), error path (422/500) test case

### 2.2 — Backend: Central Error Handler Tests
- [ ] [`backend/tests/api/test_errors.py`](file:///f:/supremeai/backend/tests/api/test_errors.py) তৈরি — [`api/errors.py`](file:///f:/supremeai/backend/api/errors.py) cover করা
  - 404 handler, 422 handler, 500 handler — response format verify

### 2.3 — Backend: Plugin Security Tests
- [ ] [`backend/tests/core/plugins/`](file:///f:/supremeai/backend/tests/core/plugins/) ডিরেক্টরি তৈরি করা + `__init__.py`
- [ ] `test_security_scanner.py` — [`core/plugins/security_scanner.py`](file:///f:/supremeai/backend/core/plugins/security_scanner.py) unit tests
- [ ] `test_capability_resolver.py` — [`core/plugins/capability_resolver.py`](file:///f:/supremeai/backend/core/plugins/capability_resolver.py) unit tests
- [ ] `test_manifest_registry.py` — [`core/plugins/manifest_registry.py`](file:///f:/supremeai/backend/core/plugins/manifest_registry.py) unit tests

### 2.4 — `conftest.py` Test Tier Registration
- [ ] [`backend/tests/conftest.py`](file:///f:/supremeai/backend/tests/conftest.py) — `_CRITICAL_TEST_PARTS`-এ যোগ করা:
  - `("api", "routes", "commandcenter")`
  - `("api", "test_errors")`
  - `("core", "plugins")`

### 2.5 — Frontend: Vitest Coverage Tests
- [ ] [`frontend/src/components/auth/ServiceHealthBar.test.tsx`](file:///f:/supremeai/frontend/src/components/auth/ServiceHealthBar.test.tsx) তৈরি — সম্প্রতি আপডেটেড component
- [ ] [`frontend/src/hooks/usePlugins.test.ts`](file:///f:/supremeai/frontend/src/hooks/usePlugins.test.ts) তৈরি — সম্প্রতি আপডেটেড hook
- [ ] [`frontend/src/components/shell/RoleAwareNavRail.test.tsx`](file:///f:/supremeai/frontend/src/components/shell/RoleAwareNavRail.test.tsx) তৈরি
- [ ] `frontend/src/pages/.../EvolutionForge.test.tsx` তৈরি
- [ ] `pnpm test --coverage` রান করে coverage % verify করা

### 2.6 — MCP firebase-admin Moderate CVE Fix
- [ ] `infrastructure/mcp-control-plane/package.json` খুলে `firebase-admin` ও `@google-cloud/storage` current version চেক করা
- [ ] Breaking changes changelog রিভিউ করা
- [ ] `npm install firebase-admin@latest` টেস্ট পরিবেশে রান করা
- [ ] MCP build ও health-check verify করা (`npm run build && npm run health`)
- [ ] `package-lock.json` আপডেট করে git commit + push

---

## 🟢 Phase 3 — Observability & Structural Debt (Month 1-2)

### 3.1 — Core Production `print()` → Structured Logger Migration
- [ ] [`api/routes/stream_chat_sse.py`](file:///f:/supremeai/backend/api/routes/stream_chat_sse.py) — ৬টি print → `logger.debug/info()`
- [ ] [`main.py`](file:///f:/supremeai/backend/main.py) — ৩টি print → `logger.info()`
- [ ] [`api/errors.py`](file:///f:/supremeai/backend/api/errors.py) — ১টি print → `logger.error()`
- [ ] [`core/agent_factory.py`](file:///f:/supremeai/backend/core/agent_factory.py) — ১টি print → `logger.info()`
- [ ] [`core/unified_router.py`](file:///f:/supremeai/backend/core/unified_router.py) — ১টি print → `logger.info()`
- [ ] [`worker_service.py`](file:///f:/supremeai/backend/worker_service.py) — ১টি print → `logger.info()`
- [ ] [`sandbox/docker_sandbox.py`](file:///f:/supremeai/backend/sandbox/docker_sandbox.py) — ১টি print → `logger.info()`
- [ ] পরীক্ষা: `grep -rn "print(" backend/ --include="*.py" | grep -v test | grep -v .venv` → core files-এ শূন্য হবে
- [ ] git commit + push

### 3.2 — `|| true` Non-Blocking Shell Failure Audit
- [ ] [`.github/workflows/ci.yml`](file:///f:/supremeai/.github/workflows/ci.yml) — ৫টি `|| true` review করা:
  - গুরুত্বপূর্ণ step হলে → সরানো
  - nice-to-have হলে → `continue-on-error: true` দিয়ে explicit করা + comment যোগ
- [ ] [`.github/workflows/maintenance.yml`](file:///f:/supremeai/.github/workflows/maintenance.yml) — ১৩টি `|| true` review ও classify করা
- [ ] [`.github/workflows/audit-release.yml`](file:///f:/supremeai/.github/workflows/audit-release.yml) — ১টি `|| true` review করা
- [ ] git commit + push

### 3.3 — ADMIN_TASKS.md Open Operational Items Track করা
- [ ] `open` — Canary traffic routing verify → Provider dashboard metrics সংগ্রহ করা
- [ ] `open` — Artifact-backed rollback & restore drill → Evidence document করা
- [ ] `open` — Vercel deployment failure investigate → Deployment ID + root cause + rerun
- [ ] `open` — `main` branch protection rules → GitHub API/screenshot export
- [ ] `blocked` — Playwright dedicated browser service → Runtime image + smoke test
- [ ] `open` — Browser compat state → durable storage → Cross-owner isolation test

---

## ✅ সম্পূর্ণ হলে পরবর্তী পদক্ষেপ
- [ ] `LESSONS_LEARNED.md` আপডেট করা (JUnit passed bug root cause + fix snippet)
- [ ] `STATUS.md` আপডেট করা — pending tasks থেকে সম্পূর্ণ আইটেমগুলো সরানো
- [ ] `ADMIN_TASKS.md` verified আইটেমগুলো `[x]` mark করা
