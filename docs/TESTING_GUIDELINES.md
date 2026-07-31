# SupremeAI — টেস্টিং গাইডলাইন (Testing Guidelines)

> এই ডকুমেন্টটি `paykaribazaronline/supremeai` রিপোর **আসল কোডবেস সরাসরি চেক করে** (৩০ জুলাই ২০২৬, `main` ব্রাঞ্চ,
> কমিট `fe44744`) লেখা হয়েছে। এখানে কোনো কাল্পনিক উদাহরণ নেই — প্রতিটা সমস্যা ও সমাধান বিদ্যমান
> `conftest.py`, `pyproject.toml`, এবং CI workflow ফাইল থেকে সরাসরি ভেরিফাই করা।

---

## অংশ ১: এই মুহূর্তে যে ৩টি কারণে টেস্ট ফেল হচ্ছে (Root Cause + Fix)

### বাগ #১ — `testpaths` মিসকনফিগ (CI-তে root-level `tests/` কখনো রানই হয় না)

**প্রমাণ:**
```toml
# backend/pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests", "backend/tests"]
```
```yaml
# .github/workflows/supreme-core-ci.yml
- name: 🧪 Run Tests
  working-directory: backend      # ← rootdir = backend/
  run: poetry run pytest ...
```
যেহেতু CI `backend/` ফোল্ডারের ভেতর থেকে pytest চালায়, pytest-এর rootdir হয় `backend/`। তখন
`testpaths` রিজলভ হয়:
- `"tests"` → `backend/tests` (আসল ফোল্ডার, ঠিক আছে)
- `"backend/tests"` → **`backend/backend/tests`** — এই ফোল্ডার আদৌ নেই!

ফলাফল: রুট-লেভেল `/tests/` (যেখানে নতুন `test_middleware_anti_hacking.py`-র মতো ফাইল আছে) CI-তে
**কখনোই কালেক্ট হয় না**। GitHub Actions সবুজ দেখাবে, কিন্তু আসলে `/tests/`-এর কোনো টেস্টই রান হয়নি।

**সমাধান** — rootdir-independent path ব্যবহার করুন:
```toml
# backend/pyproject.toml — ফিক্সড ভার্সন
testpaths = ["tests", "."]
# অথবা আরও স্পষ্ট, absolute approach:
# rootdir_relative হওয়ায় ভালো সমাধান হলো root pyproject.toml থেকে pytest চালানো,
# অথবা conftest.py-তে rootdir ফিক্স করে দেওয়া:
```
```toml
# ✅ সবচেয়ে নির্ভরযোগ্য ফিক্স: repo root-এ একটি pytest.ini/pyproject.toml যোগ করুন যেটা
# testpaths সংজ্ঞায়িত করবে, আর backend/pyproject.toml থেকে টেস্ট-সংক্রান্ত অংশ সরিয়ে দিন।
# তাহলে CI root থেকে চালালেও, backend থেকে চালালেও একই ফলাফল আসবে।
```
সবচেয়ে সহজ ও কম-ঝুঁকির ফিক্স: `working-directory: backend` বাদ দিয়ে CI স্টেপে
`poetry run pytest --rootdir=..` অথবা `cd ..` করে repo root থেকে `poetry -C backend run pytest` চালানো।

### বাগ #২ — একই নামের দুইটা টেস্ট ফাইল (import file mismatch)

**প্রমাণ:**
```
tests/test_ephemeral_executor.py                    ← __init__.py নেই এই ফোল্ডারে
backend/tests/agents/test_ephemeral_executor.py      ← __init__.py আছে backend/tests/-এ
```
যখনই `pytest` কে root থেকে (বা IDE থেকে) পুরো রিপো স্ক্যান করতে বলা হয়, দুটো ভিন্ন ফোল্ডারের
একই-নামের ফাইল pytest-এর rootdir-relative import-এ ধাক্কা খায়:
```
import file mismatch:
imported module 'test_ephemeral_executor' has this __file__ attribute:
  .../backend/tests/agents/test_ephemeral_executor.py
which is not the same as the test file we want to collect:
  .../tests/test_ephemeral_executor.py
```
**সমাধান:**
1. প্রতিটা টেস্ট ফোল্ডারে (এবং সাব-ফোল্ডারে) `__init__.py` রাখুন — `backend/tests/` এ আছে, কিন্তু
   root `tests/`-এ নেই। এটা যোগ করলে pytest দুটোকে আলাদা প্যাকেজ হিসেবে বিবেচনা করবে।
2. অথবা `pyproject.toml`-এ `--import-mode=importlib` যোগ করুন (আধুনিক pytest recommended approach,
   filename collision সহনশীল)।
3. দীর্ঘমেয়াদে: দুইটা টেস্ট রুট (`/tests` আর `/backend/tests`) একীভূত করে একটাই কনভেনশনে আনুন —
   নিচে "অংশ ২"-এ এই কনভেনশন নির্ধারণ করা হয়েছে।

### বাগ #৩ — দুই `conftest.py`-তে সাংঘর্ষিক mocking কনভেনশন

**প্রমাণ:**
```python
# tests/conftest.py (root) — পুরো core প্যাকেজকে blanket MagicMock বানিয়ে দেয়
sys.modules['core'] = MagicMock()
sys.modules['core.config'] = MagicMock()
# ...ইত্যাদি
```
```python
# backend/tests/conftest.py — backend/ কে sys.path-এ যোগ করে, যাতে "from core.config import settings" আসল মডিউল টানে
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
```
`backend/middleware/anti_hacking.py`-র ভেতরে লেখা আছে `from core.config import settings`। এই একই
লাইন দুই জায়গায় দুই রকম আচরণ করে:
- `backend/tests/` থেকে রান হলে → আসল `settings` অবজেক্ট (real `enforce_anti_hacking`, `otp_cooldown_seconds` ইত্যাদি সহ)
- root `tests/` থেকে রান হলে → `MagicMock()`-এর একটা অটো-জেনারেটেড attribute (কোনো real value নেই, সব `assert settings.enforce_anti_hacking is False`-জাতীয় assertion মিথ্যা পাস/ফেল দেবে)

**সমাধান:** একটামাত্র conftest.py স্ট্র্যাটেজি রাখুন (root-এরটা রাখুন অথবা backend/tests-এরটা রাখুন,
দুটো একসাথে ব্যবহার করবেন না)। নিচে "অংশ ৩"-এ recommended কনভেনশন দেওয়া হলো।

---

## অংশ ২: টেস্ট ফোল্ডার স্ট্রাকচার — একটাই কনভেনশন মেনে চলুন

এই রিপোতে বর্তমানে **দুইটা** টেস্ট রুট আছে যেগুলো ভিন্ন import কনভেনশন ব্যবহার করে। ভবিষ্যতে
বিভ্রান্তি এড়াতে নিচের নিয়ম মেনে চলুন:

| নতুন টেস্ট লিখছেন? | কোথায় রাখবেন | Import কনভেনশন |
|---|---|---|
| `backend/**` এর কোনো মডিউলের জন্য | `backend/tests/<same-relative-path>/test_<module>.py` | `from core.x import y` (backend/ থেকে সরাসরি) |
| `apps/studio-client` (React/TS) এর জন্য | `apps/studio-client/src/**/*.test.tsx` (colocated) | Vitest কনভেনশন |
| রিপো-ওয়াইড টুলিং/স্ক্রিপ্ট এর জন্য | ~~root `tests/`~~ **নতুন করে ব্যবহার করবেন না** — এটা legacy, উপরের বাগ #১/#৩ এর উৎস | — |

**নিয়ম:** নতুন backend টেস্ট সবসময় `backend/tests/` এর ভেতরে যাবে, root `tests/`-এ না। প্রতিটা
নতুন সাব-ফোল্ডারে (`backend/tests/<new_folder>/`) `__init__.py` তৈরি করুন — এই রিপোর বিদ্যমান
কনভেনশন অনুসরণ করে।

---

## অংশ ৩: নতুন backend টেস্ট লেখার সম্পূর্ণ গাইড

### ৩.১ — ফাইলের শুরুতে যা মনে রাখবেন

`backend/tests/conftest.py` (৪৯৩ লাইন) ইতিমধ্যে auto-use fixture দিয়ে নিচেরগুলো সেটআপ করে দেয় —
**এগুলো আবার নিজে করার দরকার নেই**:

- `TESTING=True`, `ENV=test`, in-memory SQLite DB
- Supabase, Redis, litellm, opentelemetry, firebase, chromadb, pinecone সহ ৪০+ external
  SDK মডিউল mock করা থাকে (network call কখনো বাইরে যায় না)
- `override_auth` fixture — `get_current_user_token` এবং `verify_autonomous_agent_token`
  স্বয়ংক্রিয়ভাবে `{"sub": "test_admin@supremeai.com", "role": "admin"}` রিটার্ন করে, তাই বেশিরভাগ
  admin-route টেস্টে ম্যানুয়াল auth mocking লাগে না
- `isolate_env` fixture — প্রতিটা টেস্টের আগে/পরে env var এবং `core.config.settings` রিসেট করে,
  টেস্টের মধ্যে "bleed" (এক টেস্টের সাইড-ইফেক্ট আরেক টেস্টে চলে যাওয়া) ঠেকায়
- `mock_supabase` fixture — `SupabaseDB.__init__` কে no-op করে দেয়, তাই কখনো আসল Supabase-এ কল যায় না

### ৩.২ — নতুন ফাংশন লিখলে সাথে সাথে যা করবেন (checklist)

কোনো নতুন backend ফাংশন/এন্ডপয়েন্ট যোগ করার সময়:

1. **একই PR-এ টেস্ট লিখুন** — আলাদা PR-এ "পরে লিখব" বলবেন না; কোড আর টেস্ট আলাদা হলে টেস্ট প্রায়ই
   অসম্পূর্ণ থেকে যায় (যেমনটা `verify-otp` এন্ডপয়েন্টে হয়েছিল — কোড ছিল, endpoint সম্পূর্ণ ছিল না,
   টেস্টও ছিল না)।
2. **নতুন external dependency আনলে**, `backend/tests/conftest.py`-তে `sys.modules["<pkg>"] = create_mock_module(...)`
   যোগ করুন — নাহলে CI-তে "ModuleNotFoundError" আসবে (CI-তে pip install হয় `pyproject.toml`
   অনুযায়ী; নতুন paid/optional SDK CI-তে install নাও হতে পারে)।
3. **নতুন env var/setting যোগ করলে**, `_TEST_ENV_DEFAULTS` ডিকশনারিতে (backend/tests/conftest.py,
   লাইন ~২৩৯) একটা placeholder মান যোগ করুন — নাহলে `settings.<new_field>` টেস্টে `None`/missing হয়ে
   অপ্রত্যাশিত ফেইলিওর দেবে।
4. **Redis/DB-নির্ভর কোড লিখলে**, real connection-এর বদলে `redis_manager` কে mock/patch করুন
   (নিচে ৩.৪ দেখুন) — কখনো টেস্টে আসল Upstash Redis-এ কল যাওয়া উচিত না (এটা zero-cost নীতির
   সাথেও সাংঘর্ষিক, ফ্রি-টায়ার quota টেস্ট রানেই শেষ হয়ে যেতে পারে)।

### ৩.৩ — নেমিং ও স্ট্রাকচার কনভেনশন

```
backend/tests/
├── conftest.py                     ← গ্লোবাল fixtures (আগে থেকেই আছে)
├── test_<module_name>.py           ← টপ-লেভেল মডিউলের জন্য
├── <package>/
│   ├── __init__.py                 ← আবশ্যক! (import mismatch এড়াতে)
│   └── test_<submodule>.py
```
- ফাইলনেম: `test_*.py` (pytest কনভেনশন, `pyproject.toml`-এ `python_files` দেখুন)
- ফাংশন: `test_*` — বর্ণনামূলক নাম, যেমন `test_dispatch_admin_request_context_mismatch_enforce_mode`
  (নতুন `test_middleware_anti_hacking.py`-এর প্যাটার্ন অনুসরণ করুন — নাম পড়েই বোঝা যায় কী টেস্ট হচ্ছে)
- ক্লাস দরকার নেই যদি না রিলেটেড টেস্টগুলো গ্রুপ করতে চান (`python_classes = ["Test*"]` সাপোর্টেড আছে)

### ৩.৪ — Redis/external service mock করার প্যাটার্ন (রিপোর নিজস্ব উদাহরণ থেকে)

`tests/test_middleware_anti_hacking.py` থেকে সরাসরি নেওয়া, verified প্যাটার্ন:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_your_new_redis_dependent_function():
    with patch('backend.middleware.anti_hacking.redis_manager') as mock_redis_manager:
        mock_redis_manager.client = AsyncMock()
        mock_redis_manager.get_cache = AsyncMock(return_value=None)   # প্রথমবার কোনো cache নেই
        mock_redis_manager.set_cache = AsyncMock()

        # settings mock করতে চাইলে (enforce_anti_hacking, otp_cooldown_seconds ইত্যাদি):
        with patch('backend.middleware.anti_hacking.settings') as mock_settings:
            mock_settings.enforce_anti_hacking = False
            # ... আপনার আসল টেস্ট লজিক
```

**গুরুত্বপূর্ণ নিয়ম:** সবসময় `patch('<module_that_imports_it>.redis_manager')` — অর্থাৎ যেখানে
ইম্পোর্ট হয়েছে সেখানে patch করুন (`backend.middleware.anti_hacking.redis_manager`), মূল সংজ্ঞার
জায়গায় patch করবেন না (`core.cache.redis_manager.redis_manager`) — কারণ `from x import y` করলে
নতুন নামটা importing module-এর namespace-এই বসে যায়, mock করতে হবে সেই namespace-এ।

### ৩.৫ — async টেস্ট লেখা

`pyproject.toml`-এ `asyncio_mode = "auto"` সেট করা আছে, তাই `async def test_...` লিখলেই যথেষ্ট —
`@pytest.mark.asyncio` decorator টেকনিক্যালি লাগে না, কিন্তু বিদ্যমান কোডবেসে (consistency-র জন্য)
তবুও এক্সপ্লিসিটভাবে লেখা হয় — এই কনভেনশন বজায় রাখুন:
```python
@pytest.mark.asyncio
async def test_something():
    result = await some_async_function()
    assert result == expected
```

### ৩.৬ — auth-protected এন্ডপয়েন্ট টেস্ট করা

`override_auth` fixture ইতিমধ্যে admin role override করে দেয়, তাই `/api/admin/*` রুট টেস্ট করতে
আলাদা টোকেন জেনারেট করা লাগে না। কিন্তু ভিন্ন role (যেমন non-admin ব্লক করা হচ্ছে কিনা) টেস্ট করতে:
```python
def test_non_admin_blocked(client):
    app.dependency_overrides[get_current_user_token] = lambda: {"sub": "u1", "role": "user"}
    resp = client.post("/api/admin/verify-otp", json={"code": "123456"})
    assert resp.status_code == 403
    app.dependency_overrides = {}   # টেস্ট শেষে অবশ্যই রিসেট করুন, নাহলে পরের টেস্টে leak করবে
```
অথবা `valid_auth_headers` fixture ব্যবহার করুন (আসল JWT তৈরি করে):
```python
def test_with_real_jwt(client, valid_auth_headers):
    resp = client.get("/api/admin/fixes", headers=valid_auth_headers)
    assert resp.status_code == 200
```

### ৩.৭ — coverage থ্রেশহোল্ড মনে রাখুন

```toml
addopts = "... --cov-fail-under=75"
```
`pyproject.toml`-এ ৭৫% কভারেজ থ্রেশহোল্ড **hard-enforced** — এর নিচে গেলে পুরো CI job ফেল করবে,
এমনকি সব individual টেস্ট পাস করলেও। নতুন ফাংশন লেখার সময়:
- Happy-path + কমপক্ষে ১টা error-path কভার করুন
- `if/else` এর দুই ব্রাঞ্চই টেস্ট করুন (যেমন `test_middleware_anti_hacking.py`-তে
  `enforce_mode` vs `alert_only` দুটোই আলাদা টেস্ট)
- `--cov=core` (CI কমান্ডে) মানে coverage শুধু `core/` ফোল্ডারের উপর মাপা হয় — `middleware/`,
  `api/routes/` এর মতো ফোল্ডার এই মেট্রিকে গণনা হয় না, কিন্তু তার মানে এই না যে সেগুলোর টেস্ট
  optional — শুধু CI gate-এ ধরা পড়বে না বলে বেশি সতর্ক থাকা দরকার

### ৩.৮ — filterwarnings নিয়ে সতর্কতা

```toml
filterwarnings = ["error", "ignore::DeprecationWarning", ...]
```
এখানে `"error"` মানে **যেকোনো unlisted warning একটা টেস্ট ফেইলিওরে পরিণত হবে**। নতুন লাইব্রেরি বা
নতুন কোড প্যাটার্ন ব্যবহার করলে যদি নতুন কোনো warning ওঠে (deprecation ছাড়া অন্য কিছু), সেটা টেস্ট
রানে সরাসরি ফেল দেখাবে যদিও লজিক ঠিক আছে। এমন হলে হয় কোড ফিক্স করুন (warning-এর উৎস), অথবা
`pyproject.toml`-এ নির্দিষ্ট warning ক্যাটাগরি হোয়াইটলিস্ট করুন — কখনো ব্লানকেটভাবে `"ignore"` বসিয়ে
দেবেন না, এতে আসল বাগ চাপা পড়ে যায়।

---

## অংশ ৪: PR পাঠানোর আগে লোকাল চেকলিস্ট

```bash
cd backend
poetry run pytest -n auto --dist=loadfile --timeout=120 -q          # CI যা চালায় ঠিক তাই
poetry run pytest --cov=core --cov-report=term-missing --cov-fail-under=75 -q
```
- [ ] নতুন/পরিবর্তিত প্রতিটা ফাংশনের জন্য কমপক্ষে ১টা positive + ১টা negative টেস্ট আছে
- [ ] নতুন env var থাকলে `_TEST_ENV_DEFAULTS`-এ যোগ করা হয়েছে
- [ ] নতুন external import থাকলে `create_mock_module`-এ যোগ করা হয়েছে (CI-তে নেই এমন প্যাকেজের জন্য)
- [ ] টেস্ট ফাইল `backend/tests/` এর ভেতরে, root `tests/`-এ না
- [ ] নতুন সাব-ফোল্ডারে `__init__.py` আছে
- [ ] `redis_manager`/`settings` patch করা হয়েছে importing-module namespace-এ, definition namespace-এ না
- [ ] `app.dependency_overrides` ম্যানুয়ালি সেট করলে টেস্ট শেষে রিসেট করা হয়েছে
- [ ] লোকালি `-n auto --dist=loadfile` দিয়ে রান করে দেখা হয়েছে (parallel রানে race condition ধরা পড়ে,
      সিরিয়াল রানে পড়ে না)

---

## অংশ ৫: Frontend (`apps/studio-client`) টেস্ট — সংক্ষিপ্ত নোট

CI Vitest দিয়ে চালায়:
```bash
pnpm --dir apps/studio-client exec vitest run --reporter=default --reporter=json --outputFile=vitest-report.json
```
- টেস্ট ফাইল সংশ্লিষ্ট কম্পোনেন্টের পাশেই রাখুন (`Component.tsx` + `Component.test.tsx`)
- আগের একটা fix commit (`3c707f6 fix(frontend): resolve duplicate element query errors in Vitest App.test.tsx`)
  থেকে শেখার বিষয়: `getByText`/`getByRole` ব্যবহার করার সময় নিশ্চিত করুন UI-তে সেই টেক্সট/রোল
  **একবারই** আছে — একাধিকবার থাকলে `getAllBy*` ব্যবহার করুন অথবা `data-testid` দিয়ে নির্দিষ্ট করুন,
  নাহলে "Found multiple elements" এরর আসবে।
- নতুন কোনো `apiClient` কল যোগ করলে (যেমন সাম্প্রতিক fingerprint হেডার), সেটার জন্য মক করা `fetch`
  দিয়ে টেস্ট লিখুন — real network call কখনো টেস্টে যাওয়া উচিত না।

---

## সারসংক্ষেপ — সবচেয়ে গুরুত্বপূর্ণ ৩টা নিয়ম

1. **একটাই টেস্ট রুট মেনে চলুন**: backend-এর জন্য `backend/tests/`, root `tests/` legacy —
   নতুন কিছু ওখানে যোগ করবেন না যতক্ষণ না বাগ #১/#২/#৩ ফিক্স হয়।
2. **`conftest.py`-র autouse fixture-গুলো বিশ্বাস করুন, ডুপ্লিকেট করবেন না** — নতুন mock/env var
   লাগলে বিদ্যমান ডিকশনারি/ফাংশনে যোগ করুন, নতুন প্যারালাল সিস্টেম বানাবেন না।
3. **Patch করুন importing-namespace-এ, definition-namespace-এ না** — এই একটা নিয়ম না মানলেই
   সবচেয়ে বেশি "কেন mock কাজ করছে না" টাইপ ফেইলিওর হয়।
