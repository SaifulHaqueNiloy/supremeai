সর্বশেষ updated codebase পরীক্ষা করেছি।

সর্বশেষ commit:

203c41b

কোড, router registry, startup flow, configuration validation, CI workflow এবং integration wiring দেখে সিদ্ধান্ত:

প্রকল্পে অনেক module যুক্ত আছে, কিন্তু “সব module একসাথে perfectly wired” এখনো বলা যাবে না। প্রধান সমস্যা এখন শুধু isolated error নয়; configuration contract, route authorization, CI truthfulness, startup mode এবং feature ownership-এর মধ্যে অসঙ্গতি আছে।

বর্তমান অবস্থা:

Code completeness: মাঝারি থেকে ভালোCore API wiring: আংশিকভাবে সম্পূর্ণSecurity wiring: কিছু গুরুত্বপূর্ণ ঝুঁকি আছেCI reliability: এখনো সম্পূর্ণ নির্ভরযোগ্য নয়Production readiness: NO-GOArchitecture direction: ভালো, কিন্তু অতিরিক্ত module এবং duplicate system আছে

# ==================================================

P0 — অবশ্যই আগে ঠিক করতে হবে

১. ENV configuration mismatch

ফাইল:

backend/core/config_validator.py

লাইন 104-112:

বর্তমান:

```python
VarDefinition(    name="ENV",    var_type=VarType.ENUM,    required=True,    allowed_values=["development", "staging", "production"],    description="Application environment",    examples=["development", "production"],),
```

ফাইল:

backend/main.py

লাইন 15:

```python
os.environ["ENV"] = os.getenv("SUPREMEAI_DEFAULT_ENV", "local")
```

সমস্যা:

main.py default হিসেবে `local` সেট করছে, কিন্তু config validator `local` গ্রহণ করে না। ফলে local startup fail করতে পারে অথবা configuration validation inconsistent হতে পারে।

REMOVE:

```python
allowed_values=["development", "staging", "production"],
```

ADD:

```python
allowed_values=["local", "development", "test", "staging", "production"],
```

এবং examples পরিবর্তন করুন:

REMOVE:

```python
examples=["development", "production"],
```

ADD:

```python
examples=["local", "development", "test", "staging", "production"],
```

অথবা আরও পরিষ্কার পদ্ধতি:

backend/main.py line 15 পরিবর্তন করুন:

REMOVE:

```python
os.environ["ENV"] = os.getenv("SUPREMEAI_DEFAULT_ENV", "local")
```

ADD:

```python
os.environ["ENV"] = os.getenv("SUPREMEAI_DEFAULT_ENV", "development")
```

সুপারিশ:

`local` রাখা দরকার হলে validator-এ রাখুন। বর্তমান main.py এবং validator একই contract ব্যবহার করা বাধ্যতামূলক।

==================================================
২. JWT secret নামের অসঙ্গতি

ফাইল:

backend/core/config_validator.py

লাইন 148-155:

```python
VarDefinition(    name="JWT_SECRET",    var_type=VarType.STRING,    required=True,    severity=Severity.ERROR,    min_value=32,    description="JWT signing secret (min 32 chars)",    examples=["your-super-secret-key-at-least-32-chars"],),
```

সমস্যা:

Repository-এর বিভিন্ন জায়গায় দুইটি নাম ব্যবহৃত হচ্ছে:

```plaintext
JWT_SECRETSUPREMEAI_JWT_SECRET
```

এতে একটি secret সেট থাকলেও অন্য component startup fail করতে পারে।

প্রস্তাবিত canonical নাম:

```plaintext
SUPREMEAI_JWT_SECRET
```

REMOVE:

```python
name="JWT_SECRET",
```

ADD:

```python
name="SUPREMEAI_JWT_SECRET",
```

তারপর পুরো codebase-এ `JWT_SECRET` খুঁজে দেখে একই canonical নাম ব্যবহার করুন।

Compatibility দরকার হলে:

```python
jwt_secret = os.getenv("SUPREMEAI_JWT_SECRET") or os.getenv("JWT_SECRET")
```

কিন্তু fallback-এর জন্য warning দিতে হবে এবং পরবর্তী release-এ পুরনো নাম remove করতে হবে।

==================================================
৩. Admin router authorization অতিরিক্ত generic

ফাইল:

backend/api/routers.py

লাইন 263:

```python
deps = [Depends(get_current_user_token)] if is_admin else None
```

সমস্যা:

`is_admin=True` হওয়া router-গুলোতে শুধু `get_current_user_token` dependency বসানো হচ্ছে। এটি user authenticated কিনা নিশ্চিত করতে পারে, কিন্তু প্রত্যেক route-এ admin role নিশ্চিত করে কিনা source-level evidence নেই।

বিশেষ ঝুঁকিপূর্ণ router:

- evolution
- browser_routes
- internal
- admin
- metrics
- cloud_mesh
- tools_ops
- living_brain
- ecosystem_admin
- approval_manager

REMOVE:

```python
deps = [Depends(get_current_user_token)] if is_admin else None
```

ADD:

```python
from api.deps import get_current_admin
```

তারপর:

```python
deps = [Depends(get_current_admin)] if is_admin else None
```

যদি `get_current_admin` বর্তমানে না থাকে, নতুন fail-closed dependency তৈরি করতে হবে।

Admin dependency-তে অবশ্যই:

- valid session
- active user
- admin role
- tenant scope
- revoked session check
- audit context

থাকতে হবে।

এটি সবচেয়ে গুরুত্বপূর্ণ code-level security patch-গুলোর একটি।

==================================================
৪. include_admin_routers-এ একই সমস্যা

ফাইল:

backend/api/routers.py

লাইন 285-297:

বর্তমান:

```python
def include_admin_routers(app: FastAPI) -> None:    """For compatibility/tests - registers admin routers."""    for router_def in ALL_ROUTERS:        if router_def["is_admin"]:            deps = [Depends(get_current_user_token)]            register_router(                app,                router_def["path"],                prefix=router_def["prefix"],                optional=True,                dependencies=deps,            )
```

REMOVE:

```python
deps = [Depends(get_current_user_token)]
```

ADD:

```python
deps = [Depends(get_current_admin)]
```

এবং import section-এ:

REMOVE:

```python
from api.deps import get_current_user_token
```

ADD:

```python
from api.deps import get_current_admin, get_current_user_token
```

শুধু যদি user dependency অন্য জায়গায় এখনও ব্যবহৃত থাকে। না হলে unused import remove করতে হবে।

==================================================
৫. CI workflow এখনো নিজেই failure লুকাচ্ছে

ফাইল:

.github/workflows/ci.yml

লাইন 187:

```yaml
run: python scripts/testing/mutation_testing.py --target backend/core/health_check.py --threshold 0 || true
```

লাইন 190:

```yaml
run: python scripts/testing/performance_benchmark.py --target api || true
```

সমস্যা:

যে test বা benchmark ব্যর্থ হলেও CI green থাকবে। এটি “সব error ধরার” উদ্দেশ্যের বিপরীত।

Mutation testing critical হলে:

REMOVE:

```yaml
run: python scripts/testing/mutation_testing.py --target backend/core/health_check.py --threshold 0 || true
```

ADD:

```yaml
run: python scripts/testing/mutation_testing.py \  --target backend/core/health_check.py \  --threshold 60
```

Performance benchmark advisory হলে failure না লুকিয়ে warning report করুন:

REMOVE:

```yaml
run: python scripts/testing/performance_benchmark.py --target api || true
```

ADD:

```yaml
run: |  set +e  python scripts/testing/performance_benchmark.py --target api  status=$?  set -e  if [ "$status" -ne 0 ]; then    echo "::warning::Performance benchmark failed with exit code $status"    exit 0  fi
```

তবে production release workflow-এ performance failure হলে `exit 1` করা উচিত।

==================================================
৬. CI Node version অসঙ্গতি

ফাইল:

.github/workflows/ci.yml

লাইন 45:

```yaml
NODE_VERSION: '24'
```

লাইন 196:

```yaml
uses: actions/setup-node@v4
```

লাইন 198:

```yaml
node-version: 20
```

সমস্যা:

Top-level Node 24 বলা হলেও Advanced Checks job Node 20 ব্যবহার করছে। এতে local, CI এবং production build আলাদা আচরণ করতে পারে।

REMOVE:

```yaml
uses: actions/setup-node@v4
```

ADD:

```yaml
uses: actions/setup-node@<FULL_COMMIT_SHA> # v latest compatible
```

REMOVE:

```yaml
node-version: 20
```

ADD:

```yaml
node-version: ${{ env.NODE_VERSION }}
```

`<FULL_COMMIT_SHA>`-এর জায়গায় নির্দিষ্ট immutable SHA বসাতে হবে। Tag ব্যবহার করবেন না।

==================================================
৭. CI-তে production-like dummy database দিয়ে migration audit

ফাইল:

.github/workflows/ci.yml

লাইন 214-225-এর environment:

```yaml
SUPABASE_DATABASE_URL_WRITER: "postgresql://dummy:pass@localhost:5432/db"
```

সমস্যা:

এটি বাস্তব database নয়। কিন্তু `scripts/ci-full-audit.sh` migration এবং database checks চালায়। ফলে:

- connection failure
- migration failure
- false production signal
- audit result বিভ্রান্তিকর

REMOVE:

```yaml
SUPABASE_DATABASE_URL_WRITER: "postgresql://dummy:pass@localhost:5432/db"
```

ADD:

```yaml
SUPABASE_DATABASE_URL_WRITER: "postgresql://test_user:test_password@localhost:5432/supremeai_test"
```

এবং audit step-এর আগে PostgreSQL service নিশ্চিত করতে হবে। বর্তমানে `advanced-checks` job-এ PostgreSQL service নেই। তাই এই audit job-এ service যোগ করুন অথবা migration audit-কে backend-tests job-এ সরান।

সুপারিশ:

Database-dependent audit backend-tests job-এ চালান। Static audit advanced-checks job-এ রাখুন।

==================================================
৮. Production ENV দিয়ে local CI server চালানো

ফাইল:

.github/workflows/ci.yml

লাইন 378-385:

```yaml
SUPABASE_DATABASE_URL_POOLER: "sqlite+aiosqlite:///./test.db"SUPABASE_URL: "https://mock-supabase.co"SUPABASE_KEY: "mock-supabase-key"SUPABASE_SERVICE_ROLE_KEY: "mock-supabase-service-role-key"OPENAI_API_KEY: "sk-mock-openai-api-key"ENV: production
```

সমস্যা:

Test PostgreSQL service থাকা সত্ত্বেও `sqlite+aiosqlite` ব্যবহার করা হচ্ছে এবং `ENV: production` দিয়ে local CI server চালানো হচ্ছে।

এটি বাস্তব production wiring যাচাই করে না এবং SQLite fallback accidentally pass করতে পারে।

REMOVE:

```yaml
SUPABASE_DATABASE_URL_POOLER: "sqlite+aiosqlite:///./test.db"
```

ADD:

```yaml
SUPABASE_DATABASE_URL_POOLER: "postgresql://test_user:test_password@localhost:5432/supremeai_test"
```

REMOVE:

```yaml
ENV: production
```

ADD:

```yaml
ENV: test
```

যদি production-only startup validation পরীক্ষা করতে চান, আলাদা dedicated job বানান। একই job-এ test এবং production semantics মেশাবেন না।

==================================================
৯. Router registry duplicate এবং optional import সমস্যা

ফাইল:

backend/api/routers.py

লাইন 244-269:

```python
for router_def in ALL_ROUTERS:    ...    register_router(app, path, prefix=prefix, optional=True, dependencies=deps)
```

সমস্যা:

প্রায় সব router `optional=True` দিয়ে load হচ্ছে। ফলে গুরুত্বপূর্ণ router import বা wiring failure silently skip হতে পারে। Critical router ছাড়া application boot হওয়ার সম্ভাবনা আছে।

বর্তমান:

```python
if is_critical:    register_router(app, path, prefix=prefix, optional=False, dependencies=deps)else:    register_router(app, path, prefix=prefix, optional=True, dependencies=deps)
```

সুপারিশ:

Core production router-কে critical করুন।

উদাহরণ:

```python
CORE_REQUIRED_ROUTERS = {    "api.routes.auth",    "api.routes.agents",    "api.routes.agent",    "api.routes.conversations",    "api.routes.health",    "api.routes.llm_gateway_routes",    "api.routes.approval_manager",}
```

তারপর:

```python
required = is_critical or path in CORE_REQUIRED_ROUTERSregister_router(    app,    path,    prefix=prefix,    optional=not required,    dependencies=deps,)
```

এতে core route missing হলে startup বা CI fail করবে, কিন্তু optional integrations gracefully skip করতে পারবে।

==================================================
১০. `approval_manager` admin router-এ current dependency নিশ্চিত করতে হবে

ফাইল:

backend/api/routers.py

লাইন 220-224:

```python
{    "path": "api.routes.approval_manager",    "prefix": "",    "is_admin": True,    "is_critical": False,},
```

সমস্যা:

HITL approval surface business-critical। এটিকে `is_critical=False` রেখে optional import করা হয়েছে।

REMOVE:

```python
"is_critical": False,
```

ADD:

```python
"is_critical": True,
```

যদি module import failure-এ পুরো application বন্ধ করতে না চান, তাহলে অন্তত dedicated CI contract test-এ এটি mandatory করুন।

==================================================
১১. Test bypass guard আরও কঠোর করতে হবে

ফাইল:

backend/core/config_validator.py

`ALLOW_TEST_AUTH_BYPASS` schema এবং auth dependency যাচাই করুন।

Production-এ এই value true হলে startup fail হওয়া উচিত।

ADD করুন:

```python
if os.getenv("ENV") == "production" and os.getenv("ALLOW_TEST_AUTH_BYPASS", "").lower() == "true":    raise RuntimeError(        "ALLOW_TEST_AUTH_BYPASS must be disabled in production"    )
```

এটি config validation-এর একেবারে শেষে বা startup validation-এর আগে ব্যবহার করুন।

শুধু warning দেওয়া যাবে না। এটি hard failure হওয়া উচিত।

==================================================
১২. Main.py-তে `local` mode এবং settings.env mismatch

ফাইল:

backend/main.py

লাইন 15:

```python
os.environ["ENV"] = os.getenv("SUPREMEAI_DEFAULT_ENV", "local")
```

ফাইলের পরে:

```python
is_local = settings.env == "local"
```

সমস্যা:

Validator `local` না মানলে settings load এবং `run_server()`-এর local branch একই সঙ্গে কাজ করবে না।

উপরের Patch 1-এর সঙ্গে এই issue সমাধান করতে হবে। এই দুই ফাইলের মধ্যে environment contract এক করতে হবে।

==================================================
১৩. Full API wiring test যোগ করতে হবে

বর্তমান router registry আছে, কিন্তু প্রতিটি registered router বাস্তবে app-এ loaded কিনা নিশ্চিত করার জন্য দৃশ্যমান contract test দরকার।

নতুন test ফাইল:

backend/tests/api/test_router_registry_contract.py

যোগ করুন:

```python
from fastapi import FastAPIfrom api.routers import ALL_ROUTERS, register_all_routersdef test_all_critical_routers_are_registered():    app = FastAPI()    register_all_routers(app)    route_paths = {        route.path        for route in app.routes        if hasattr(route, "path")    }    missing = []    for router_def in ALL_ROUTERS:        if router_def["is_critical"]:            module_name = router_def["path"]            if not any(module_name.split(".")[-1] in path for path in route_paths):                missing.append(module_name)    assert not missing, f"Critical routers missing: {missing}"
```

তবে module name এবং route path এক নয়। আরও নির্ভরযোগ্যভাবে প্রতিটি router module-এর expected endpoint contract map করা উচিত।

সঠিক test হবে:

- route name
- method
- path
- auth requirement
- admin requirement
- response schema

সবকিছু explicit contract file-এ রাখা।

==================================================
১৪. Health endpoint smoke test-এ readiness যোগ করুন

ফাইল:

.github/workflows/ci.yml

লাইন 402-410:

```yaml
echo "Probing ${BASE}/api/v1/health/live ..."
```

বর্তমানে live endpoint পরীক্ষা হচ্ছে। readiness endpoint অবশ্যই একই loop-এ পরীক্ষা করতে হবে।

ADD:

```shellscript
echo "Probing ${BASE}/api/v1/health/ready ..."READY_CODE=$(curl -s -o /dev/null -w "%{http_code}" \  "${BASE}/api/v1/health/ready" || echo "000")if [ "$READY_CODE" != "200" ]; then  echo "Readiness check failed with HTTP ${READY_CODE}"  exit 1fi
```

Live 200 কিন্তু database unavailable হলে ready 503 হওয়া উচিত। দুইটি আলাদা health signal রাখতে হবে।

==================================================
১৫. CI full audit script-এ false success বন্ধ করতে হবে

ফাইল:

scripts/ci-full-audit.sh

যেসব command ব্যর্থ হলেও script চলতে পারে সেগুলো খুঁজে ঠিক করুন:

```shellscript
|| true
```

বিশেষ করে:

- migration
- Docker build
- secret scan
- production health
- backend tests
- security scan

ব্যবহার করা যাবে না।

শুধু advisory check-এ warning ব্যবহৃত হবে। Critical check-এ:

```shellscript
set -Eeuo pipefail
```

এবং non-zero exit বাধ্যতামূলক রাখতে হবে।

==================================================
১৬. Background task failure visibility

ফাইল:

backend/core/utils/background_tasks.py

এবং background worker modules

সমস্ত task-এর জন্য নিশ্চিত করুন:

```python
task = asyncio.create_task(worker())task.add_done_callback(log_task_failure)
```

Callback:

```python
def log_task_failure(task: asyncio.Task) -> None:    if task.cancelled():        return    exc = task.exception()    if exc is not None:        logger.exception(            "Background task failed",            exc_info=(type(exc), exc, exc.__traceback__),        )
```

শুধু `create_task()` করে reference না রাখলে task failure হারিয়ে যেতে পারে।

==================================================
১৭. Multi-tenant cache key audit

Codebase-এ memory, Redis, vector, conversation এবং rate-limit feature আছে। প্রত্যেক key-তে tenant/user scope থাকা নিশ্চিত করতে হবে।

ভুল:

```python
cache_key = f"conversation:{conversation_id}"
```

সঠিক:

```python
cache_key = f"tenant:{tenant_id}:user:{user_id}:conversation:{conversation_id}"
```

চেক করতে হবে:

- Redis keys
- Memory keys
- Vector namespace
- WebSocket channel
- Export cache
- Rate-limit key
- Background job key
- Idempotency key

এটি full codebase search এবং test ছাড়া সম্পূর্ণ হয়েছে বলা যাবে না।

==================================================
১৮. Feature combination test এখনো নেই

এটাই আপনার মূল কথার সবচেয়ে গুরুত্বপূর্ণ অংশ।

একটি module আলাদাভাবে pass করলেই product কাজ করে না। বাস্তব achievement হলো:

Authentication → Conversation → LLM → Streaming → Memory → Tool → HITL → Audit → Billing → Admin visibility

এই সম্পূর্ণ chain একসাথে pass করা।

এই end-to-end test যোগ করতে হবে:

backend/tests/e2e/test_core_product_journey.py

Test flow:

১. User login২. Tenant create/select৩. Agent create৪. Conversation create৫. Message submit৬. LLM response stream৭. Memory write৮. Tool invocation৯. High-risk tool হলে approval request১০. Admin approval১১. Tool execution১২. Audit ledger write১৩. Usage/billing record১৪. Conversation history reload১৫. Memory recall১৬. Logout১৭. Token refresh১৮. Same data অন্য tenant থেকে না পাওয়া

এই test ছাড়া “সব wired perfectly” বলা যাবে না।

==================================================
১৯. E2E test-এ mock provider এবং real provider আলাদা করুন

বর্তমান codebase-এ অনেক provider আছে:

- Gemini
- Groq
- OpenRouter
- OpenAI
- Firebase
- Supabase
- Redis
- external integrations

সবকিছু এক test-এ real করা যাবে না।

দুটি layer রাখুন:

Layer A: deterministic integration test

- Test PostgreSQL
- Test Redis
- Fake LLM provider
- Fake external services
- Full business flow

Layer B: staging smoke test

- Real LLM gateway
- Real Supabase
- Real Redis
- Real deployed frontend/backend
- Limited test tenant
- Budget cap

==================================================
২০. Generated frontend/admin deployment wiring যাচাই করুন

Frontend build, admin build এবং backend API origin একই contract ব্যবহার করছে কিনা যাচাই করতে হবে।

চেক করুন:

- Frontend `VITE_API_URL`
- Admin `VITE_API_URL`
- WebSocket URL
- SSE fallback URL
- Production CORS
- Token refresh endpoint
- Firebase hosting rewrite
- Backend `/api/v1` prefix

বিশেষ ঝুঁকি:

Router registry-তে কিছু route prefix:

```plaintext
/api/api/v1/ /api/voice
```

Frontend যদি সব endpoint-এ `/api/v1` prefix ধরে নেয়, তাহলে কিছু feature unreachable হবে।

একটি canonical API client তৈরি করুন:

```plaintext
frontend/src/lib/api-client.ts
```

সব endpoint hardcoded string না ব্যবহার করে endpoint registry থেকে URL তৈরি করবে।

==================================================
২১. API endpoint registry এবং frontend usage diff চালু করুন

প্রতি CI run-এ যাচাই করুন:

- Backend registered endpoint
- Frontend requested endpoint
- Admin requested endpoint
- WebSocket endpoint
- SSE fallback endpoint
- Docs endpoint

যে endpoint backend-এ নেই কিন্তু frontend call করছে, CI fail করবে।

যে critical backend endpoint frontend-এ ব্যবহারই হচ্ছে না, সেটি warning হবে।

==================================================
২২. Dead modules এবং duplicate implementations কমাতে হবে

বর্তমান repository-তে অনেক parallel implementation আছে:

- multiple memory stores
- multiple Firestore helpers
- multiple MCP modules
- multiple evolution engines
- multiple deployment helpers
- multiple database routers
- multiple AI/provider adapters
- legacy scripts
- examples
- auto-fix scripts

এগুলো একসাথে রাখলে wiring ambiguity তৈরি হয়।

প্রতি feature-এর জন্য একটি canonical implementation নির্ধারণ করুন:

Memory:

- canonical store
- fallback store
- migration-only store

Evolution:

- proposal
- approval
- canary
- promotion
- rollback

Database:

- read connection
- write connection
- migration authority

AI:

- gateway
- provider adapters
- fallback policy

অপ্রয়োজনীয় duplicate code remove বা `legacy/` এবং `experimental/` namespace-এ আলাদা করুন।

==================================================
২৩. Startup import সব router validate করছে না

বর্তমানে optional router load failure সম্ভবত warning দিয়ে skip করে। কিন্তু feature registry-তে route declared থাকলে minimum contract test দরকার।

প্রতিটি router entry-তে যোগ করুন:

```python
{    "path": "api.routes.conversations",    "prefix": "/api/v1",    "is_admin": False,    "is_critical": True,    "required_in": ["monolith", "core"],}
```

তারপর service role অনুযায়ী expected routers test করুন।

এতে `scraper`, `worker`, `core`, `monolith` role-এ কোন route থাকবে তা deterministic হবে।

==================================================
২৪. Service role classification যথেষ্ট নির্ভুল নয়

ফাইল:

backend/api/routers.py

লাইন 251:

```python
is_scraper_route = "scraper" in path or "browser" in path
```

সমস্যা:

String matching দিয়ে route classification করা fragile।

উদাহরণ:

- browser route accidentally core service-এ বাদ যেতে পারে
- scraper নাম থাকা optional utility route বাদ যেতে পারে
- future module naming বদলালে behavior বদলে যাবে

REMOVE:

```python
is_scraper_route = "scraper" in path or "browser" in pathis_health_route = "health" in path or "service_topology" in path
```

ADD:

প্রতিটি router definition-এ explicit field:

```python
"roles": ["monolith", "scraper"],"health_route": False,
```

তারপর:

```python
is_scraper_route = "scraper" in router_def.get("roles", [])is_health_route = router_def.get("health_route", False)
```

এটি ভবিষ্যৎ modular deployment-এর জন্য অনেক নিরাপদ।

==================================================
২৫. Config validator-এর error output secret leak করতে পারে

ফাইল:

backend/core/config_validator.py

লাইন 89:

```python
lines.append(f"   Actual value: '{err.actual_value}'")
```

সমস্যা:

Validation error-এ actual secret value output হলে logs-এ credential leak হতে পারে।

REMOVE:

```python
if err.actual_value:    lines.append(f"   Actual value: '{err.actual_value}'")
```

ADD:

```python
if err.actual_value:    sensitive = any(        token in err.var_name.upper()        for token in ("SECRET", "KEY", "TOKEN", "PASSWORD", "CREDENTIAL")    )    display_value = "[REDACTED]" if sensitive else err.actual_value    lines.append(f"   Actual value: '{display_value}'")
```

==================================================
২6. Sentry error handling-এ `str(exc)` log review

ফাইল:

backend/main.py

লাইন 100-112 এবং 119-131:

```python
except Exception as sentry_exc:    logger.warning(f"Failed to report error to Sentry: {sentry_exc}")
```

এটি startup error না হলেও Sentry exception-এর মধ্যে credential বা URL থাকতে পারে।

REMOVE:

```python
logger.warning(f"Failed to report error to Sentry: {sentry_exc}")
```

ADD:

```python
logger.warning(    "Failed to report startup error to Sentry",    exc_info=True,)
```

একই পরিবর্তন দুই জায়গায় করুন।

==================================================
২৭. Production Docker image-এ startup mode যাচাই

ফাইল:

backend/Dockerfile

বর্তমান CMD এবং main.py-এর interaction যাচাই করুন:

- `ENV=production`
- `PORT=8080`
- `HOST=0.0.0.0`
- `UVICORN_WORKERS=1`
- health path `/api/v1/health/live`

Dockerfile-এর healthcheck canonical path ব্যবহার করতে হবে:

REMOVE:

```dockerfile
CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health/live')" || exit 1
```

ADD:

```dockerfile
CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/v1/health/live')" || exit 1
```

==================================================
২৮. CI test step-এ auto-fix বন্ধ করুন

ফাইল:

.github/workflows/ci.yml

লাইন 325-328:

```yaml
- name: Auto-fix lint and formatting  run: |    poetry run ruff check --fix . || true    poetry run ruff format . || true
```

সমস্যা:

CI source code mutate করছে। এতে test-এর আগে code পরিবর্তিত হচ্ছে এবং CI result repository code-এর সঙ্গে ভিন্ন হতে পারে।

REMOVE:

```yaml
- name: Auto-fix lint and formatting  run: |    poetry run ruff check --fix . || true    poetry run ruff format . || true
```

ADD:

```yaml
- name: Verify lint and formatting  run: |    poetry run ruff check .    poetry run ruff format --check .
```

Developer machine বা separate autofix workflow-তে auto-fix রাখা যেতে পারে। Main CI-তে নয়।

==================================================
পূর্ণ roadmap

Phase 1: Startup এবং security contract

১. ENV mismatch ঠিক করুন২. JWT secret canonical করুন৩. Production test bypass fail-closed করুন৪. Admin dependency ঠিক করুন৫. Config error redact করুন৬. Docker health path ঠিক করুন

Exit condition:

- Local startup pass
- Test startup pass
- Production config invalid হলে fail
- Non-admin user admin endpoint access করতে না পারে

Phase 2: CI truthfulness

১. CI auto-fix remove২. `|| true` audit করুন৩. Node version এক করুন৪. All actions SHA pin করুন৫. Dummy DB-এর বদলে test PostgreSQL ব্যবহার করুন৬. readiness probe যোগ করুন৭. Smart summary failed job লুকাবে না৮. Coverage policy এক জায়গায় আনুন

Exit condition:

- Failure হলে CI fail
- Warning হলে warning
- False positive আলাদা
- Failed job কখনো Clean দেখাবে না

Phase 3: API contract এবং wiring

১. Critical router required করুন২. Optional router failure আলাদা করুন৩. Explicit service role metadata দিন৪. Backend endpoint registry তৈরি করুন৫. Frontend endpoint diff চালু করুন৬. Admin এবং user auth contract test করুন৭. OpenAPI generated schema validate করুন

Exit condition:

- সব critical route loaded
- Unauthorized admin route blocked
- Frontend-এর প্রতিটি critical call valid backend route-এ যায়

Phase 4: Data এবং tenant integrity

১. Read/write DB connection আলাদা করুন২. Alembic একমাত্র schema authority করুন৩. SQLite fallback বন্ধ করুন৪. সব cache key tenant-scoped করুন৫. Memory/vector namespace tenant-scoped করুন৬. Audit log durable করুন৭. Backup restore test করুন

Exit condition:

- Tenant A tenant B-এর data দেখতে পারে না
- Restart-এর পরে data থাকে
- Migration deterministic
- Audit reconstruct করা যায়

Phase 5: Core product journey

একটি end-to-end flow test করুন:

Login → Agent → Conversation → LLM → Stream → Memory → Tool → Approval → Execution → Audit → Billing → Recall

Exit condition:

- একটি user journey শুরু থেকে শেষ পর্যন্ত pass
- Failure হলে rollback/fallback কাজ
- User-visible state এবং backend state একই

Phase 6: Evolution safety

১. Proposal-only default২. Human approval বাধ্যতামূলক৩. Artifact hash৪. Canary deployment৫. Real metrics৬. Automatic stop৭. Rollback৮. Audit trail

Exit condition:

- AI নিজে production code promote করতে পারে না
- মানব অনুমোদন ছাড়া deployment হয় না
- Bad release rollback হয়

Phase 7: Production verification

১. Real Render deployment২. Writable Supabase connection৩. Migration run৪. Live/ready health৫. Load test৬. Memory test৭. WebSocket/SSE test৮. Backup restore৯. Incident drill১০. Cost alert

Exit condition:

- No P0 blocker
- Full CI green
- E2E journey pass
- Canary এবং rollback verified
- Observability alert tested

==================================================
আমার প্রোফেশনাল সুপারিশ

আপনার philosophy—একটি self-improving, multi-module, AI-native platform—সঠিক এবং উচ্চাকাঙ্ক্ষী। কিন্তু এখন সবচেয়ে বড় ঝুঁকি feature কম থাকা নয়; বরং অনেক feature একই সময়ে “active” দেখানো হলেও তাদের মধ্যে একটি নির্ভরযোগ্য end-to-end contract নেই।

আপনার জন্য সবচেয়ে ভালো strategy:

১. নতুন feature এখনই যোগ করবেন না২. প্রথমে “Golden User Journey” স্থির করুন৩. একটি canonical database path রাখুন৪. একটি canonical AI gateway রাখুন৫. একটি canonical memory interface রাখুন৬. একটি canonical approval path রাখুন৭. সব module-কে optional/critical/experimental হিসেবে classify করুন৮. প্রতি release-এ একটি সম্পূর্ণ end-to-end journey pass করান৯. Self-evolution-কে proposal-first রাখুন১০. “Operational 100%” শুধু automated evidence থাকলেই লিখুন

সবচেয়ে গুরুত্বপূর্ণ নীতি:

একটি feature আলাদাভাবে pass করা achievement নয়। সত্যিকারের achievement হলো user-এর বাস্তব journey-তে authentication, AI, memory, tools, approval, audit, billing এবং admin observability একসাথে নির্ভরযোগ্যভাবে কাজ করা।

চূড়ান্ত verdict:

বর্তমান updated codebase আগের চেয়ে ভালো এবং অনেক wiring যুক্ত হয়েছে। কিন্তু এখনো perfect বা fully production-ready নয়। সবচেয়ে জরুরি code fixes হলো:

- ENV contract
- JWT naming
- admin authorization
- CI auto-fix এবং swallowed failures
- dummy SQLite/DB configuration
- required router enforcement
- secret redaction
- explicit service-role routing
- end-to-end product journey test

এই patch ও roadmap সম্পন্ন হলে SupremeAI-এর architecture আপনার মূল philosophy না বদলিয়েই অনেক বেশি নির্ভরযোগ্য, নিরাপদ এবং production-grade হবে।
