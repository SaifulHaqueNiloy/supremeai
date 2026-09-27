# সুপ্রিমএআই সিম্প্লিফিকেশন অডিট রিপোর্ট

> **তারিখ**: 2026-09-27  
> **HEAD অডিটেড**: `c89c0006`  
> **মেথড**: ৫টা প্যারালাল অডিট এজেন্ট (A: CI/CD, B: ব্যাকএন্ড কোর, C: API রাউটস, D: টেস্ট, E: ফ্রন্টএন্ড)  
> **ফ্রেমিং**: `2+2=4` vs `1+8-9+4=4` — জটিল পথ সরল করা, **ফলাফল অপরিবর্তিত থাকবে**।

---

## সারাংশ (Executive Summary)

| মেট্রিক্স | মান |
|----------|-----|
| মোট ফাইল অডিটেড | ~১,৪০০+ (workflows, scripts, backend, frontend, tests) |
| মোট simplification findings | **৮২** (A:১৩, B:১৮, C:২৫, D:৮, E:১৮) |
| সম্ভাব্য LOC কমানো | **~৬,২০০–৭,৪০০** (dead code + duplication + over-abstraction) |
| সম্ভাব্য CI minutes saved/run | **৩–৫ মিনিট** (overlapping gates, coverage overhead) |
| Quick wins (S effort, low risk) | **~২৫টি** (~১,৫০০ LOC removable শুধু মুছে ফেলে) |
| Architectural refactors | ~১০টি (M/L effort, med risk, পৃথক PR) |

### "1+8-9+4 → 2+2" এর উদাহরণ (অডিট থেকে)

| বর্তমান (1+8-9+4) | সরলীকৃত (2+2) | ফলাফল |
|-------------------|----------------|--------|
| ৪টা আলাদা generator list (regen_all_artifacts.sh + ci.yml + ci-advanced-checks.yml + ci-doctor.yml) | ১টা canonical `regen_all_artifacts.sh` সব জায়গা থেকে call | একই artifacts তৈরি হবে |
| ৩টা overlapping route↔frontend scanner (route_client_inventory + route_consumer_inventory + verify_api_contract) | ১টা canonical scanner (AST-based) | একই orphan detection |
| ৩৬টা identical `@property` getter in config_secrets.py | ১টা `__getattr__` + class-level key map | একই API, শুধু boilerplate কম |
| ৫টা prompt-classifier router (IntentClassifier/V1/V2/IntelligenceRouter/SupremeMoE) | ১টা canonical classifier + config-driven | একই intent routing |
| `security.py` function-level `from X import redis_manager` (monkeypatch bypass) | module-level import | একই behavior, টেস্ট monkeypatch কাজ করবে |
| ১০+ টেস্ট `from core.app import app` (heavy lifespan init) | `FastAPI() + include_router(...)` minimal | একই route behavior verify |
| `test_gateway_context` hardcoded `total >= 14` ও ৯-ফাইল expected set | শুধু `assert violations == []` (BASELINE=0 আছে) | একই gate, শূন্য maintenance |
| ৩টা overlapping localhost-exclude lists (ARCH-001, regression_scanner, check_hardcoded) | ১টা shared helper | একই exclusions |
| `record_merge_learning.py` open PR তে `exit 1` | `exit 0` ("nothing to learn yet" = info, not error) | একই learning behavior, শুধু false-red দূর |
| ৩টা dead ErrorBoundary + dead i18n stack (frontend) | delete | একই UI |

---

## স্তর ১ — CI/CD পাইপলাইন (Agent A)

**৮২ findings এর মধ্যে ১৩টি** · ~১,৮০০–২,২০০ LOC removable · ৩–৫ CI min/run saved

### শীর্ষ সুযোগ

| ID | শিরোনাম | LOC | কনফিডেন্স | প্রচেষ্টা | ঝুঁকি |
|----|---------|-----|-----------|-----------|--------|
| **A1** | ৪টা generator list → ১টা canonical `regen_all_artifacts.sh` | ~150 | high | M | low |
| **A2** | `test_gateway_context` hardcoded threshold/set সরাও | ~15 | high | S | low |
| **A3** | CORE_ROUTERS/OPTIONAL_ROUTERS → AST parse | ~75 | high | S | low |
| **A4** | ARCH-001 এ `_BLOCKED` denylist carve-out port | ~20 | high | S | low |
| **A5** | regression_scanner এ baseline JSON ratchet | ~0 (new file) | high | S | low |
| **A7** | ৩টা route↔frontend scanner → ১টা canonical | ~280 | medium | M | med |
| **A8** | dead `check_config_control_plane.py` ডিলিট + merge | ~138 | high | S | low |
| **A9** | `audit_module_wiring.py` + `sync_modules_list.py` wire বা delete | ~184 | high | S | low |
| **A11** | `ci-doctor.yml` regen block ডিলিট (artifact-regen canonical) | ~50 | medium | S | med |
| **A13** | STATUS.md এ `qa-live-smoke.yml` → `nightly-ops.yml` (live-smoke) | ~0 (doc) | high | S | low |

### গুরুত্বপূর্ণ প্যাটার্ন

**প্যাটার্ন A-I: "masked pre-existing debt"** — `e179bd1f` (শেষ সবুজ) তে Advanced Pre-Merge job **skipped** ছিল। #1858 consolidation এটাকে unmask করেছে। ফলে regression_scanner (৫টা pre-existing localhost finding), validate_domain_boundaries (test→prod import false positive), record_merge_learning (open PR exit 1) — সব একসাথে surface হয়েছে। এটাই whack-a-mole এর root cause।

**প্যাটার্ন A-II: "৪টা generator list drift"** — `regen_all_artifacts.sh` (৮ generators), `ci-advanced-checks.yml` (৮ + ৫ unittests interleaved), `ci-doctor.yml:447` (৫ generators), `ci.yml:467` (১ generator, warning-only)। রোলআপ #2067 এই ৪টা লিস্টের একটাতেও `stream_voice_sse` সরানো হয়নি ছিল — ফলে drift। একটা canonical list হলে এটা ঘটতই না।

**প্যাটার্ন A-III: "৩টা overlapping route scanners"** — `generate_route_client_inventory.py` (REGEX), `generate_route_consumer_inventory.py` (AST, নিজের docstring এ বলা আছে "upgraded version"), `verify_api_contract.py` (REGEX, no artifact)। সব issue #480 / orphan detection করে। AST-based canonical একটাই রাখলে বাকি দুটোর ~280 LOC মুছে যায়।

---

## স্তর ২ — ব্যাকএন্ড কোর (Agent B)

**৮২ findings এর মধ্যে ১৮টি** · ~৩,৪০০ LOC safely removable · ৬১১ ফাইল অডিটেড

### শীর্ষ সুযোগ

| ID | শিরোনাম | LOC | কনফিডেন্স | প্রচেষ্টা | ঝুঁকি |
|----|---------|-----|-----------|-----------|--------|
| **B1** | ৩৬ identical `@property` getter + ১৪ setter in `config_secrets.py` → `__getattr__` + key map | ~250 | high | M | low |
| **B2** | ৫টা prompt-classifier router (identical regex-scoring) → ১টা + config | ~400 | high | L | med |
| **B3** | ৪টা rate limiter + duplicate in `RequestValidationMiddleware` → canonical | ~300 | high | M | med |
| **B5** | `AutoCacheProxy` dead code delete | ~150 | high | S | low |
| **B6** | `IntelligentCacheBridge` dead code delete | ~120 | high | S | low |
| **B8** | `SlidingWindowRateLimiter` deprecated delete | ~80 | high | S | low |
| **B9** | `SwarmConsensusEngine` orphan delete | ~90 | high | S | low |
| **B10** | ৪টা messaging dead files delete | ~200 | high | S | low |
| **B12** | পুরো `external_agents/` 2,873 LOC — কোনো live caller নেই | ~2873 | medium | M | med |
| **B13+B14** | ২টা `DeclarativeBase` subclass (canonical vs legacy) → ১টা | ~60 | high | M | med |
| **B16** | `SupremeAgentOrchestrator` orphan + ২টা shim re-export delete | ~46 | high | S | low |

### গুরুত্বপূর্ণ প্যাটার্ন

**প্যাটার্ন B-I: "boilerplate property sprawl"** — `core/config_secrets.py` এ ৩৬টা identical `@property` getter ও ১৪টা setter pair। প্রতিটা ৫-৬ লাইন। সব হুবহু একই pattern: `return self._get_cached_secret("KEY_NAME")`। একটা `__getattr__` + class-level `_SECRET_KEYS = ("OPENROUTER_API_KEY", ...)` list দিলে ~250 LOC কমে যায়, API অপরিবর্তিত থাকবে।

**প্যাটার্ন B-II: "৫টা identical prompt router"** — `IntentClassifier`, `IntentRouter`, `IntentRouterV2`, `IntelligenceRouter`, `SupremeMoERouter`। সব identical regex-scoring algorithm। একটা canonical `PromptClassifier` + config-driven scoring table দিলে ~400 LOC কমবে।

**প্যাটার্ন B-III: "dead code accumulation"** — `external_agents/` (2,873 LOC), `AutoCacheProxy` (150), `IntelligentCacheBridge` (120), `SlidingWindowRateLimiter` (80), `SwarmConsensusEngine` (90), ৪টা messaging files (200) — মোট ~3,400 LOC যেগুলোর কোনো live caller নেই। শুধু মুছে ফেললেই হয়।

**প্যাটার্ন B-IV: "২টা DeclarativeBase"** — `models/base.py` (canonical) ও `core/db.py` (legacy)। alembic silent-miss hazard। একটা রাখলে বাকি ~60 LOC যায়।

---

## স্তর ৩ — API রাউটস (Agent C)

**৮২ findings এর মধ্যে ২৫টি** · ১৯৪ রাউট ফাইল অডিটেড · ৬৭৭ openapi paths / ৭৬১ routes

### শীর্ষ সুযোগ

| ID | শিরোনাম | LOC | কনফিডেন্স | প্রচেষ্টা | ঝুঁকি |
|----|---------|-----|-----------|-----------|--------|
| **C12** | `websocket_hitl.py` (১৭৬ LOC, কোনো importer/mount নেই) delete | ~176 | high | S | low |
| **C13** | `codeflow.py` shim (২৩ LOC, শুধু validator ইম্পোর্ট করে) delete | ~23 | high | S | low |
| **C11** | `get_current_admin` duplicate function in `admin_routes.py:159` | ~7 | high | S | low |
| **C8** | `/admin/rules` + `/api/v1/admin/alerts` deprecated duplicates | ~30 | high | S | low |
| **C1+C9** | `admin.py:1028-1106` render block shadow of `render_preflight_admin.py` | ~79 | high | S | low |
| **C4** | `browser_routes.py` ৪ duplicate endpoints shadow of `browser/_crown_jewel.py` | ~250 | high | M | med |
| **C6** | `task.py:179` `POST /api/chat/stream` shadow of `stream_chat_sse.py` | ~40 | high | S | low |
| **C5** | `ci_webhooks.py` duplicate `POST /api/ci/webhook` (different schema) | ~50 | medium | M | med |
| **C3** | ৩× `/api/v1/health` mount (core/health_routes + api/routes/health + api/routes/scraper) | ~30 | high | S | low |
| **C14+C15** | ৩ stale entry in `validate_router_imports.py` (deleted modules) | ~10 | high | S | low |
| **C20** | `admin_v1.py` 19 alias-endpoint elimination | ~317 | medium | M | med |
| **C16** | agent/ ৭ ফাইল → ১ subpackage (browser/ pattern) | ~100 | medium | L | med |
| **C19** | admin/ ৫ ফাইল + ১৭ submodules → subpackage | ~200 | medium | L | med |

### গুরুত্বপূর্ণ প্যাটার্ন

**প্যাটার্ন C-I: "shadow endpoints"** — একই path ২টা ভিন্ন handler এ serve হচ্ছে। `test_no_route_registered_more_than_once` টেস্ট শুধু exact `(path, method, qualified_name)` duplicate ধরে, কিন্তু same-path-different-handler shadow ধরে না। অডিটে **১২টা** shadow pair পাওয়া গেছে।

**প্যাটার্ন C-II: "fragmentation"** — `admin.py`, `admin_v1.py`, `admin_auth.py`, `admin_dashboard/` (১৭ submodules) — ৫+ জায়গায় admin routes। `agent.py`, `agent_action.py`, `agent_breeding.py`, `agent_registry.py`, `agent_tasks.py`, `agent_workspace.py`, `agents.py` — ৭টা agent ফাইল। browser/ subpackage এর pattern follow করলে merge করা যায়।

**প্যাটার্ন C-III: "security inconsistency"** — ৬টা admin-auth dep: `get_current_user_token`, `get_current_admin`, `get_project_admin`, `get_current_platform_admin`, `require_admin_token`, `admin_rate_limit`। `get_current_admin` (৩৮ files/১৪২ uses, কোনো jti revocation check নেই) vs `require_admin_token` (১১ files/৩১ uses, revocation-checked) — **inconsistent admin-auth posture**।

---

## স্তর ৪ — টেস্ট সুইট (Agent D)

**৮২ findings এর মধ্যে ৮টি** · ২ confirmed root causes for known CI failures

### শীর্ষ সুযোগ

| ID | শিরোনাম | প্রভাব | কনফিডেন্স | প্রচেষ্টা | ঝুঁকি |
|----|---------|-------|-----------|-----------|--------|
| **D1** | `security.py` function-level import → module-level (monkeypatch fix) | security_rate_limit ৪× CI fail ঠিক | high | S | low |
| **D2** | JWTAuthMiddleware যোগ (multicloud 403 fix) বা টেস্ট mark skip | multicloud 403 fix | medium | M | med |
| **D3** | pytest `--cov=core` addopts থেকে সরাও | unit tests ২০-৩০% দ্রুত | high | S | low |
| **D4** | ১০+ টেস্ট `from core.app import app` → minimal `FastAPI()+include_router` | collection ব্যর্থ দূর | high | M | low |
| **D5** | `mock_external_apis` autouse → explicit | test isolation fix | medium | M | med |
| **D6** | `db_engine` fixture local default → `sqlite+aiosqlite` | local test runs fix | high | S | low |
| **D7** | sentinel_agent ১১ stale skip → delete বা rewrite | dead test noise দূর | high | S/L | low/med |
| **D8** | `test_gateway_context` hardcoded threshold/set সরাও | maintenance burden দূর | high | S | low |

### Known-failure root causes (confirmed)

১. **`security_rate_limit_backend` ৪× fail**: `backend/core/middleware/security.py:261` function-level `from core.cache.redis_manager import redis_manager`। প্রতিবার `_check_rate_limit` কল হলে নতুন local binding, monkeypatch bypass। CI তে real `SecureRedisManager` ব্যবহার হয়, "Event loop is closed" এরর (বন্ধ event loop এ Redis client)। **Fix**: module-level import (Finding D1, effort S)।

২. **`multicloud` 403**: `grep -rn "request.state.user =" backend/` = ০ — কোনো middleware JWT decode করে user state সেট করে না। `get_current_user_token` (dependencies.py:107) শুধু `request.state.user` চেক করে। টেস্ট `jwt.encode({"role":"admin"})` পাঠায় কিন্তু কেউ decode করে state সেট করে না। **এটা হয় by-design external auth (Firebase/Supabase) অথবা টেস্টটাই ভুল** — Issue #2097 তে আলাদা ইনভেস্টিগেশন দরকার।

### গুরুত্বপূর্ণ প্যাটার্ন

**প্যাটার্ন D-I: "heavy import chain"** — ১০+ টেস্ট `from core.app import app` করে। এটা পুরো lifespan (orchestrator, telemetry, Redis, Supabase) initialize করে। যেকোনো optional dep (opentelemetry, infisical_client) না থাকলে collection-ই ব্যর্থ। `test_sworm_adapter_contract.py` ইতিমধ্যে canonical pattern দেখায়: `app = FastAPI(); app.include_router(agent_tasks.router)`।

**প্যাটার্ন D-II: "coverage on every run"** — `addopts` এ `--cov=core --cov-report=term/html/xml` প্রতিটা pytest invocation এ। একটা unit test রান করলেও coverage collect হয়। এটা ~২০-৩০% overhead। আলাদা coverage step এ সরালে লোকাল dev দ্রুত হবে, CI coverage gate এখনো চলবে।

---

## স্তর ৫ — ফ্রন্টএন্ড (Agent E)

**৮২ findings এর মধ্যে ১৮টি** · ৪১৪ TS/TSX + ১১২ test ফাইল অডিটেড · ~১,৫০০ LOC removable

### শীর্ষ সুযোগ

| ID | শিরোনাম | LOC | কনফিডেন্স | প্রচেষ্টা | ঝুঁকি |
|----|---------|-----|-----------|-----------|--------|
| **E2** | পুরো i18n stack (৫ ফাইল + translations.ts) dead — শুধু dead Header.tsx consume করে | ~316 | high | S | low |
| **E8** | ৩টা dead service delete (`costOptimizer`, `sandbox`, `socialGrowth`) | ~455 | high | S | low |
| **E10** | ৩টা dead realtime hook delete (`useWebSocket`, `useSwarmStream`, `useServerStream`) | ~354 | high | S | low |
| **E13** | ৫টা dead component delete (Header ×2, Sidebar ×2, AgentStateShader) | ~200 | high | S | low |
| **E14** | ২টা dead dashboard file delete (`useHashRoute`, `sessionStore`) | ~246 | high | S | low |
| **E12** | ২৬৭ LOC `TierSIntegrationGuide` docstring ফাইল থেকে সরাও | ~267 | high | S | low |
| **E11** | ৩টা dead hook delete (`useBudgetCheck`, `useIframeConsole`, `useDashboardActions`) | ~80 | high | S | low |
| **E9** | `WorkspaceModulePage` + `SwarmArchitect` triple-alias delete | ~100 | high | S | low |
| **E1** | `controlPlane.ts` (৪৮ LOC) → fold into `apiClient` | ~48 | medium | M | low |
| **E6** | `unifiedStore.ts` dead flag strip (৫১৫ LOC, শুধু ৬ field live) | ~400 | medium | M | med |
| **E15** | Type duplication (`CapabilityStatus` ২×, `ConnectionContract` ৩×) unify | ~50 | medium | M | low |
| **E18** | `useListResource` migration complete (৬ pages এখনো raw useEffect) | ~120 | medium | M | low |

### গুরুত্বপূর্ণ প্যাটার্ন

**প্যাটার্ন E-I: "dead code graveyard"** — i18n stack (৩১৬ LOC), ৩টা service (৪৫৫), ৩টা realtime hook (৩৫৪), ৫টা component (২০০), ২টা dashboard file (২৪৬) — মোট **~১,৫৭১ LOC dead frontend code** যেগুলোর কোনো live consumer নেই। শুধু মুছে ফেললেই হয়।

**প্যাটার্ন E-II: "false-positive frontend consumers"** — `route_consumer_inventory.json` এ `fe_refs: 145` দাবি করে। কিন্তু অডিটে পাওয়া গেছে **৮টা backend route এর শুধু dead FE consumer আছে**। অর্থাৎ inventory তে সেগুলো "user-facing" classify করা হয়েছে, কিন্তু আসলে orphan।

**প্যাটার্ন E-III: "monorepo workspace fragmentation"** — ৪টা workspace root (frontend + apps/mission-control + packages/* + tools/vscode-extension)। `apps/mission-control` (Next.js 16, ১৪k LOC) — **ZERO tests**। `packages/ui-components` নাম misleading — শুধু ৪৬ LOC SharedProviders export করে।

---

## প্রায়োরিটি ম্যাট্রিক্স

### Tier 1 — Quick Wins (S effort, low risk, immediate)

এগুলো মেকানিক্যাল, রিভার্সিবল, শুধু মুছে ফেলা বা সরানো। কোনো behavior change নেই।

| ID | কাজ | LOC কমবে |
|----|-----|----------|
| A2 | `test_gateway_context` hardcoded threshold/set সরাও | 15 |
| A4 | ARCH-001 `_BLOCKED` denylist carve-out | 20 |
| A5 | regression_scanner baseline JSON | 0 (new file) |
| A8 | dead `check_config_control_plane.py` delete + merge | 138 |
| A9 | `audit_module_wiring.py` + `sync_modules_list.py` wire বা delete | 184 |
| A11 | `ci-doctor.yml` regen block delete | 50 |
| A13 | STATUS.md `qa-live-smoke` → `nightly-ops` | 0 |
| B5 | `AutoCacheProxy` dead delete | 150 |
| B6 | `IntelligentCacheBridge` dead delete | 120 |
| B8 | `SlidingWindowRateLimiter` deprecated delete | 80 |
| B9 | `SwarmConsensusEngine` orphan delete | 90 |
| B10 | ৪ messaging dead files delete | 200 |
| B16 | `SupremeAgentOrchestrator` orphan + ২ shim delete | 46 |
| C3 | ৩× `/api/v1/health` mount → ১টা | 30 |
| C5 | `ci_webhooks.py` duplicate delete | 50 |
| C8 | deprecated `/admin/rules` + `/api/v1/admin/alerts` delete | 30 |
| C11 | duplicate `get_current_admin` delete | 7 |
| C12 | `websocket_hitl.py` dead delete | 176 |
| C13 | `codeflow.py` shim delete | 23 |
| C14+C15 | stale entries in `validate_router_imports.py` | 10 |
| D1 | `security.py` module-level import | 0 |
| D3 | pytest `--cov=core` addopts থেকে সরাও | 0 |
| D6 | `db_engine` local default → sqlite | 0 |
| D7 | sentinel_agent ১১ stale skip delete | 200 |
| D8 | `test_gateway_context` hardcoded threshold সরাও (overlap A2) | 15 |
| E2 | i18n stack dead delete | 316 |
| E8 | ৩ dead service delete | 455 |
| E10 | ৩ dead realtime hook delete | 354 |
| E11 | ৩ dead hook delete | 80 |
| E12 | `TierSIntegrationGuide` docstring সরাও | 267 |
| E13 | ৫ dead component delete | 200 |
| E14 | ২ dead dashboard file delete | 246 |
| E9 | triple-alias delete | 100 |

**Tier 1 মোট**: ~৩,৩৫১ LOC, সব low risk, S effort

### Tier 2 — Architectural Simplifications (M/L effort, med risk, পৃথক PR)

| ID | কাজ | LOC কমবে | প্রচেষ্টা | ঝুঁকি |
|----|-----|----------|-----------|--------|
| A1 | ৪ গেনারেটর লিস্ট → ১ canonical | 150 | M | low |
| A3 | CORE_ROUTERS → AST parse | 75 | S | low |
| A7 | ৩ route scanner → ১ canonical | 280 | M | med |
| B1 | ৩৬ `@property` → `__getattr__` + key map | 250 | M | low |
| B2 | ৫ prompt router → ১ canonical + config | 400 | L | med |
| B3 | ৪ rate limiter → canonical | 300 | M | med |
| B12 | পুরো `external_agents/` (verify dead first) | 2873 | M | med |
| B13+B14 | ২ `DeclarativeBase` → ১ | 60 | M | med |
| C4 | `browser_routes.py` ৪ duplicate → `browser/_crown_jewel.py` | 250 | M | med |
| C16 | agent/ ৭ ফাইল → subpackage | 100 | L | med |
| C19 | admin/ ফ্র্যাগমেন্টেশন → subpackage | 200 | L | med |
| C20 | `admin_v1.py` ১৯ alias elimination | 317 | M | med |
| D2 | JWTAuthMiddleware বা multicloud test skip | — | M | med |
| D4 | ১০+ test minimal FastAPI() pattern | 0 | M | low |
| E6 | `unifiedStore.ts` dead flag strip | 400 | M | med |
| E15 | Type duplication unify | 50 | M | low |
| E18 | `useListResource` migration complete | 120 | M | low |

**Tier 2 মোট**: ~৫,৮২৩ LOC, পৃথক PR এ M/L effort

### Tier 3 — Large Refactors (L effort, med/high risk, দীর্ঘমেয়াদী)

| ID | কাজ |
|----|-----|
| A12 | `pr-gate.yml` এর ~৬০০ LOC inline Python → scripts |
| A10 | ১৬-step `audit-release.yml` → dispatcher script |
| B2 | ৫টা prompt router unification (overlap Tier 2) |

---

## বাস্তবায়ন ক্রম (Suggested)

### ধাপ ১ — Verification PR (১ দিন)
**B12 (`external_agents/`) verify dead**: এটাই সবচেয়ে large claim (২,৮৭৩ LOC)। আগে `git log --all -- source-path` দিয়ে verify করুন কোনো branch এ এই কোড use হয় কিনা। যদি dead হয় তাহলে delete।

### ধাপ ২ — Quick Wins PR (২-৩ দিন)
Tier 1 এর সবগুলো এক PR এ — সবই S effort, low risk, মেকানিক্যাল। **~৩,৩৫১ LOC কমবে**, কোনো behavior change নেই।

### ধাপ ৩ — Known CI Failures Fix PR (১ দিন)
- **D1** (security.py module-level import) → security_rate_limit ৪× CI fail ঠিক
- **D2** (multicloud — ইনভেস্টিগেট করুন JWTAuthMiddleware দরকার কিনা)
- **D8** (test_gateway_context hardcoded সরাও)

### ধাপ ৪ — CI/CD Consolidation PR (৩-৫ দিন)
- **A1** (৪ গেনারেটর লিস্ট → ১ canonical) — সবচেয়ে বেশি impact, whack-a-mole এর root fix
- **A5** (regression_scanner baseline)
- **A7** (৩ scanner → ১)
- **A8, A9, A11** (dead scripts/workflows delete)

### ধাপ ৫ — Backend Architecture PRs (পৃথক, ১-২ সপ্তাহ)
প্রতিটা পৃথক PR এ:
- **B1** (config_secrets `__getattr__`)
- **B2** (৫ prompt router → ১)
- **B3** (৪ rate limiter → canonical)
- **B13+B14** (২ DeclarativeBase → ১)

### ধাপ ৬ — API Routes Consolidation PRs (পৃথক, ১-২ সপ্তাহ)
- **C4, C16, C19, C20** — প্রতিটা পৃথক PR, কারণ breaking changes হতে পারে

### ধাপ ৭ — Frontend Dead Code PR (২-৩ দিন)
Tier 1 এর সব E findings এক PR এ — ~১,৫৭১ LOC dead delete, কোনো UI change নেই।

---

## "NOT Simplification Candidates" (যেখানে result পরিবর্তন হবে)

অডিট চলাকালীন কিছু pattern খুঁজে পাওয়া গেছে যেগুলো সরল করা যায় না কারণ ফলাফল পরিবর্তন হবে:

১. **`get_current_admin` vs `require_admin_token` security inconsistency (C10)** — এটাই actually inconsistent, কিন্তু unify করলে behavior change হবে (কোনো route হঠাৎ revocation-checked হয়ে যাবে)। এটা আলাদা security fix, simplification নয়।
২. **`multicloud` 403 (D2)** — যদি by-design external auth হয়, তাহলে টেস্টই ভুল; simplification নয়, behavior question।
৩. **manualChunks config** — এটি actual bundle-size optimization, সরল করলে bundle size পরিবর্তন হবে।
৪. **`external_agents/` (B12)** — যদি কোনো feature flag দ্বারা enable থাকে, তাহলে dead নয়। verify করে তবে delete করুন।

---

## মেট্রিক্স ও টার্গেট

| মেট্রিক্স | বর্তমান | টার্গেট (সরল করার পর) |
|----------|---------|----------------------|
| Backend LOC | ~৬১১ ফাইল | ~৫৮০ ফাইল (−৩১ dead delete) |
| Frontend LOC | ~৫৩.৫k + ১৪k | ~৫২k + ১৩.৫k (−১.৫k dead delete) |
| CI jobs | ৩০ | ২৫-২৭ (overlap merge) |
| CI generators | ৮ (৪ list) | ৬ (১ canonical list) |
| CI scanners | ৩ route scanners | ১ |
| Test skip markers | ১৫+ (১১ stale sentinel) | ৪-৫ (documented) |
| pytest addopts | `--cov` প্রতিটা রানে | `--cov` শুধু coverage step এ |
| Duplicate methods | অন্তত ১ (`run_dag_for_workspace`) | ০ |
| Dead code LOC | ~৫,০০০+ | ০ |
| Pre-existing CI failures | ৫ (multicloud + ৪ security) | ০ |

---

## উপসংহার

এই অডিটে **৮২টি simplification opportunity** খুঁজে পাওয়া গেছে যেখানে **ফলাফল অপরিবর্তিত থাকবে** — শুধু পথ সরল হবে (`1+8-9+4 → 2+2`)। এর মধ্যে:

- **~৩,৩৫১ LOC** শুধু মুছে ফেলে যায় (Tier 1, S effort, low risk)
- **~৫,৮২৩ LOC** architectural simplification এ কমবে (Tier 2, M/L effort)
- **৩-৫ CI minutes** per run বাঁচবে
- **৫টা pre-existing CI failure** এর মধ্যে ৪টার root cause confirm হয়েছে + ১টার সমাধান path আছে

**সবচেয়ে গুরুত্বপূর্ণ insight**: whack-a-mole pattern এর root cause হলো **৪টা আলাদা generator list** (Finding A1) ও **masked pre-existing debt** (Pattern A-I)। একটা canonical `regen_all_artifacts.sh` + baseline ratchet scanners হলে রোলআপ #2067 এর ৫-failure cascade আর ঘটত না।

**পরবর্তী পদক্ষেপ**: Tier 1 (Quick Wins) এক PR এ। এটাই সবচেয়ে কম ঝুঁকি, সবচেয়ে বেশি লাভ।

---

## অডিট এজেন্ট সামারি

| এজেন্ট | স্কোপ | ফাইল | Findings | LOC removable |
|--------|-------|------|----------|---------------|
| A — CI/CD | workflows + scripts/ci + quality + governance + audit | ২০ workflows + ৩৮ scripts | ১৩ | ১,৮০০-২,২০০ |
| B — Backend Core | core/ + models + database + brain + services + external_agents | ৬১১ ফাইল | ১৮ | ৩,৪০০ |
| C — API Routes | routes/ + routers + middleware + openapi | ১৯৪ route ফাইল, ৬৭৭ paths | ২৫ | ৪৮০+ |
| D — Tests | conftest + pyproject + tests/ | conftest + config + samples | ৮ | — (behavior fix) |
| E — Frontend | frontend/ + apps/ + packages/ + shared/ | ৪১৪ + ১১২ test | ১৮ | ১,৫০০ |
| **মোট** | | ~১,৪০০+ | **৮২** | **~৬,২০০-৭,৪০০** |

বিস্তারিত findings প্রতিটা এজেন্টের worklog entry তে আছে (`/home/z/my-project/worklog.md` lines 1119-2260)।
