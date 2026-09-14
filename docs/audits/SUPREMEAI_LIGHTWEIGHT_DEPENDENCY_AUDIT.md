# SupremeAI — Lightweight Dependency Audit & Replacement Plan

Date: 2026-08-29
Repository: `SaifulHaqueNiloy/supremeai`
Focus: Render production footprint, memory pressure, container size, cold-start risk, and long-term maintenance.

## Executive conclusion

The first important finding is that `sentence-transformers` is **already isolated into the optional Poetry `ml` group** in the current `backend/pyproject.toml`, while the production Dockerfile installs `--only main`. Therefore, **sentence-transformers + torch should not be part of the normal Render runtime image unless another build path explicitly installs the ML group**.

The current code also has a stronger simplification opportunity: `backend/core/embeddings.py` has `_HAS_SENTENCE_TRANSFORMERS = False`, so the local SentenceTransformer path is intentionally disabled and the application already has a pure-Python feature-hashing fallback plus a remote embedding path through LiteLLM. This means keeping `sentence-transformers` around for the core runtime is currently unnecessary.

The biggest production-weight opportunity is not sentence-transformers. It is **Playwright + Chromium system dependencies**, followed by the broad `litellm` stack and optional cloud/ML capabilities.

---

## What “heavy” means for this audit

A package is considered a lightweight-risk candidate when one or more of these are true:

1. Large native wheel / binary footprint.
2. Large transitive dependency tree.
3. OS packages or browser runtimes are required.
4. Significant resident memory when imported/initialized.
5. The capability is optional but currently installed in the core production image.
6. A simpler HTTP/API client can provide the same business capability.

Package size examples from current PyPI listings are used only as directional evidence; installed image size is always larger or smaller depending on platform and transitive dependencies.

---

# 1. Highest-priority dependency changes

| Current dependency / feature | Current role in SupremeAI | Weight risk | Better strategy | Recommended replacement / architecture | Priority |
|---|---|---:|---|---|---:|
| `torch` | ML / evolution scaffolding | **Extreme** | Do not install in core | Keep only in optional `ml`/research environment; remove from production core | P0 |
| `sentence-transformers` | Local embeddings | **High** because it pulls the PyTorch ecosystem | Do not install in core | `fastembed` for local CPU embeddings, OR external embeddings via OpenAI/Gemini/provider API, OR current hash fallback for non-semantic fallback | P0 |
| `playwright` + Chromium | Browser automation / scraping | **Very High** | Make browser automation optional | Dedicated optional `browser` group or separate browser worker/service; do not install Chromium in core web image | P0 |
| `litellm` | Unified multi-provider LLM gateway | **Medium/High** | Keep only if multi-provider abstraction is truly needed | Prefer direct provider adapters (`openai`, `anthropic`, Google provider SDK) for the small set of providers actually used; otherwise keep LiteLLM but isolate lazy imports | P1 |
| `numpy` | ML / scientific utilities | Medium | Keep out of core unless production code imports it | Optional ML group | P1 |
| `scipy` | ML / statistics | High | Optional only | Pure-Python math, `statistics`, or NumPy only where sufficient | P1 |
| `pandas` | Data analysis/reporting | Medium/High | Optional only | Standard library + SQL aggregation; `polars` only when dataframe workloads genuinely exist | P1 |
| `opencv-python-headless` | CV / image processing | High | Optional only | Pillow for basic image operations; external vision API for semantic vision | P1 |
| `plotly` | Charts/analysis | Medium | Never in core API runtime unless actively serving charts server-side | Generate chart data in API; render in frontend; keep Plotly in admin/report worker only | P1 |
| `google-cloud-*` set | Firestore/GCS/GCP integrations | Medium | Optional by feature | Prefer Supabase/Firebase existing platform where functionally equivalent; lazy-load GCP modules | P1 |
| `boto3` | S3/R2/cross-cloud storage | Medium (mostly transitive `botocore`) | Optional only | Supabase Storage for primary storage; direct R2/S3-compatible HTTP only if truly required | P1 |
| `docker` SDK | Container management/sandbox tooling | Medium | Optional only | HTTP API/CLI in isolated operations tooling; never needed for normal API requests | P1 |
| `mcp` | Model Context Protocol tooling | Medium | Keep only if MCP server/client features are active | Optional integration group if not core | P2 |
| `neo4j` | Graph DB integration | Low/Medium | Optional only | Keep only if Graphiti/graph workflows are active; otherwise remove | P2 |
| `qdrant-client` | Vector DB integration | **Low** | Keep if actively used | Keep; client wheel is small; do not confuse client size with vector backend cost | P2 |
| `pillow` | Image processing | Low/Medium | Keep | No need to replace for ordinary image handling | KEEP |
| `sqlalchemy` | Primary relational ORM | Low/Medium | Keep | Do not replace for size reasons; core infrastructure | KEEP |
| `aiohttp` | Async HTTP | Low | Keep where used | Existing dependency is relatively small | KEEP |
| `asyncpg` | Postgres driver | Low | Keep | Appropriate for async Postgres | KEEP |
| `redis` + `hiredis` | Upstash Redis | Low/Medium | Keep | This is core infrastructure, not a candidate for removal | KEEP |
| `fastapi[all]` | API framework | Medium due to extras | Slim the extras | Prefer bare `fastapi` unless every `[all]` extra is truly required | P1 |
| `uvicorn[standard]` | ASGI server | Low/Medium | Keep standard if used | Standard extras are generally worth the runtime performance | KEEP |
| OpenTelemetry stack | Observability | Medium | Keep only required exporters/instrumentation | Remove unused exporters/instrumentation | P2 |

---

# 2. Sentence-Transformers: the specific answer

## Current state

The repository's Poetry configuration places:

- `torch`
- `sentence-transformers`
- `numpy`
- `opencv-python-headless`
- `pandas`
- `plotly`
- `scipy`

inside the optional `[tool.poetry.group.ml]` group.

The Dockerfile uses:

```text
poetry install --only main --no-root
```

so those ML dependencies are intentionally excluded from the main production installation.

That is good architecture.

## But there is still dead weight in the dependency graph

`backend/core/embeddings.py` currently sets:

```python
_HAS_SENTENCE_TRANSFORMERS = False
```

and describes the SentenceTransformer model as a local-first path, but the active default path is the non-ML fallback. The module already has:

- pure-Python feature hashing
- a lazy local encoder hook
- remote 1536-dimensional embeddings via LiteLLM
- an in-process cosine similarity implementation

Therefore, for a lightweight production image:

### Recommended

Remove these from the core production install entirely:

```text
torch
sentence-transformers
```

Then choose one of two optional embedding modes:

### Mode A — Lowest maintenance / lowest memory

```text
Embedding request
    -> external embedding API
    -> Supabase pgvector
```

Best when semantic quality matters more than local/offline execution.

### Mode B — Local CPU embedding, still relatively lightweight

Use `fastembed` + ONNX Runtime instead of SentenceTransformers/PyTorch.

FastEmbed explicitly positions itself as lightweight and avoids the multi-hundred-MB PyTorch dependency burden by using ONNX Runtime. Current PyPI documentation describes it as designed for serverless runtimes and says it does not require downloading GBs of PyTorch dependencies.

Do NOT install both FastEmbed and SentenceTransformers.

---

# 3. Torch is the dependency I would remove first

Current PyPI Linux x86-64 wheels for recent Torch releases are hundreds of MB.

That is fundamentally incompatible with a small always-on API image unless the application genuinely performs local deep-learning inference.

SupremeAI currently does not need Torch in the normal API process.

### Recommendation

Create three dependency tiers:

```text
core
  FastAPI
  SQLAlchemy
  asyncpg
  Redis
  Supabase/Firebase clients
  HTTP clients
  auth/security
  provider SDKs
  observability

optional-browser
  Playwright
  browser-specific packages

optional-ml
  FastEmbed / ONNX Runtime
  numpy (only if needed)

research-only
  Torch
  SentenceTransformers
  SciPy
  Pandas
  Plotly
  OpenCV
```

This is better than simply swapping every package one-for-one.

---

# 4. Playwright is the other major production-weight issue

The current Dockerfile does more than install the Python package:

```text
playwright install --with-deps chromium
```

That means the production image also receives:

- Chromium
- browser runtime files
- Linux system packages required by Chromium

The current repository also contains dedicated browser managers and browser agents, so Playwright is genuinely used in code. But it does not belong in the always-on lightweight API image if browser automation is not needed for every request.

## Recommended architecture

```text
Render Web API
    |
    +-- core API image (small)
    |
    +-- optional browser execution path
          |
          +-- dedicated worker/service OR
          +-- QStash -> browser job endpoint
```

This is a much larger win than replacing Playwright with another Python browser library.

### Important

Do not replace Playwright with Selenium merely for size.

Selenium's Python wheel is smaller, but real browser automation still requires an actual browser/driver/runtime. You would usually trade one complexity for another rather than materially improving the production image.

The lightweight solution is **isolation**, not a different browser library.

---

# 5. LiteLLM: keep or remove?

Current PyPI wheels are roughly tens of MB before accounting for its dependency tree.

This package is bigger than a single provider SDK because it provides a broad gateway abstraction.

SupremeAI supports multiple LLM providers and has routing/circuit-breaker logic.

Therefore I would NOT remove LiteLLM merely because it is larger.

## Decision rule

### Keep LiteLLM when:

- multiple providers are first-class
- fallback/routing is centralized
- embeddings and chat share the provider abstraction
- new providers are expected frequently

### Replace with direct SDK adapters when:

- only 2–3 providers are actually used
- you want the smallest possible core image
- provider-specific features are more important than gateway abstraction

### Best compromise

Keep this abstraction:

```text
LLMGateway
  ├── OpenAIAdapter
  ├── GeminiAdapter
  ├── OpenRouterAdapter
  └── AnthropicAdapter
```

and make LiteLLM just one optional implementation instead of the whole application's transport layer.

Do not rewrite the whole system until dependency profiling shows LiteLLM is a meaningful runtime cost.

---

# 6. Pandas / SciPy / Plotly / OpenCV

These should not be in the API core.

The current `ml` group already isolates them, which is a good start.

## Preferred replacements by use case

### Pandas

For normal API/database tasks:

```text
SQL aggregation
+
Python lists/dicts
+
statistics
```

Use `polars` only when there is a real dataframe workload that benefits from it.

Do not add Polars just because it is fashionable; otherwise you replace one dataframe dependency with another.

### SciPy

For:

- basic statistics → `statistics`
- basic numerical math → `math`
- vector arithmetic → Python/NumPy where needed

Keep SciPy in research/ML only.

### Plotly

The best lightweight server strategy is:

```text
Backend -> JSON series
Frontend -> chart library
```

Do not generate interactive Plotly objects on every API request.

### OpenCV

If the need is only:

- resize
- crop
- encode/decode
- basic image format conversion

keep Pillow.

Use OpenCV only for actual computer-vision algorithms.

---

# 7. Cloud SDK consolidation

Current codebase has multiple cloud ecosystems:

```text
Firebase Admin
Google Cloud Firestore
Google Cloud Storage
Google Auth
Boto3 / S3-compatible storage
Supabase
```

This increases operational and dependency complexity.

## Recommended target

For normal SupremeAI production:

```text
Auth           -> Firebase
Primary DB     -> Supabase/Postgres
Object storage -> Supabase Storage
Cache          -> Upstash Redis
Async jobs     -> QStash
Vector         -> one canonical vector system
```

Only keep GCP/Boto3 modules when there is a concrete feature that requires them.

The application can still support these integrations, but they should be optional adapters.

---

# 8. Qdrant client is NOT a major size problem

The current Qdrant Python client wheel is only a few hundred KB.

So do not remove `qdrant-client` merely to save image size.

The real question is architectural:

```text
Do we want Qdrant?
OR
Do we want Upstash Vector?
OR
Do we want Supabase pgvector?
```

Choose one canonical vector backend instead of carrying several.

---

# 9. Supabase SDK is also NOT the problem

The current Supabase Python distribution is tiny at the top-level package level.

Its existence is not responsible for the kind of Render footprint problem created by Torch/Chromium/large ML stacks.

Keep it.

---

# 10. FastAPI `[all]` should be questioned

Current configuration:

```toml
fastapi = {extras = ["all"], version = "^0.136.0"}
```

This is broader than a normal production API needs.

Replace with:

```toml
fastapi = "^0.136.0"
```

and add only the extras/packages that are actually imported.

This is a clean, low-risk optimization.

---

# 11. Production dependency architecture I recommend

## Tier 1 — `main`

Must be small and boring:

```text
fastapi
uvicorn
sqlalchemy
alembic
pydantic
pydantic-settings
asyncpg
redis
supabase
firebase-admin
httpx / aiohttp
openai
anthropic
auth/security dependencies
stripe
observability
Infisical
```

## Tier 2 — `browser`

```text
playwright
browser automation helpers
browser-specific tools
```

## Tier 3 — `ml`

```text
fastembed
onnxruntime
numpy
opencv-python-headless  (only if required)
```

## Tier 4 — `research`

```text
torch
sentence-transformers
scipy
pandas
plotly
```

---

# 12. Concrete target dependency policy

## REMOVE FROM MAIN

```text
torch
sentence-transformers
playwright
```

## KEEP, BUT OPTIONALIZE

```text
numpy
scipy
pandas
plotly
opencv-python-headless
boto3
docker
google-cloud-firestore
google-cloud-storage
google-auth-oauthlib
mcp
neo4j
```

## KEEP IN MAIN

```text
fastapi
uvicorn
sqlalchemy
asyncpg
redis
supabase
firebase-admin
openai
anthropic
aiohttp
pillow
cryptography
pyjwt
stripe
pydantic
pydantic-settings
alembic
loguru
prometheus-client
sse-starlette
```

## REVIEW AFTER PROFILING

```text
litellm
opentelemetry stack
pygithub
posthog
pydantic-ai
```

---

# 13. Most important codebase changes

## A. Make optional imports truly optional

Every optional integration must obey:

```python
try:
    import optional_package
except ImportError:
    optional_package = None
```

and must only activate when its configuration flag is enabled.

The current code already follows this pattern for Playwright and SentenceTransformers in several places; standardize it across all optional providers.

## B. Do not import optional modules at application startup

Use lazy imports inside the feature implementation.

Bad:

```python
import playwright
import pandas
import scipy
```

at module import time.

Better:

```python
async def run_browser_task(...):
    from playwright.async_api import async_playwright
```

## C. Keep feature flags environment-driven

Examples:

```text
SUPREMEAI_ML_ENABLED=false
SUPREMEAI_BROWSER_ENABLED=false
SUPREMEAI_RESEARCH_ENABLED=false
SUPREMEAI_VECTOR_BACKEND=...
```

The application should decide what gets activated from environment/configuration, not from hardcoded domains or assumptions.

---

# 14. Suggested replacement matrix

| Requirement | Heavy option | Lightweight option | Recommendation |
|---|---|---|---|
| Local embeddings | SentenceTransformers + Torch | FastEmbed + ONNX Runtime | **FastEmbed** |
| Remote embeddings | Local ML stack | Provider API | **Best for smallest server** |
| Basic semantic fallback | ML model | Feature hashing | **Already available; keep** |
| Image resize/crop | OpenCV | Pillow | **Pillow** |
| Browser automation | Playwright + Chromium in API image | Isolated Playwright worker | **Isolate** |
| Dataframes | Pandas | SQL + Python / Polars when needed | **Avoid unless needed** |
| Scientific computing | SciPy | stdlib / NumPy | **Avoid in core** |
| Interactive charts | Plotly backend | Frontend chart renderer | **Move rendering to frontend** |
| Object storage | Boto3 | Supabase Storage | **Prefer existing storage layer** |
| Graph DB | Neo4j | Postgres JSON/relations when sufficient | **Only keep for real graph workloads** |
| LLM gateway | LiteLLM | Direct provider SDKs | **Profile before replacing** |
| Vector DB | Multiple clients/backends | One canonical backend | **Consolidate** |

---

# 15. Final target

The goal should NOT be:

> “replace every package with a smaller package.”

The correct goal is:

> “Only install what the production request path actually needs.”

Target architecture:

```text
                 SUPREMEAI CORE
        ┌─────────────────────────────┐
        │ FastAPI                     │
        │ Auth / Security             │
        │ Supabase / Postgres         │
        │ Upstash Redis               │
        │ LLM provider adapters       │
        │ Observability               │
        └──────────────┬──────────────┘
                       │
             optional execution
                       │
        ┌──────────────┼───────────────┐
        ▼              ▼               ▼
     QStash         Browser          ML
     jobs           worker           worker
                    Playwright       FastEmbed
```

The core Render service should not pay the memory/storage/startup cost of capabilities that are used only occasionally.

---

# 16. Implementation order for an AI coding agent

### Phase 1 — No behavior change

1. Audit all imports of optional packages.
2. Generate an import-to-feature dependency map.
3. Move optional packages into dedicated Poetry groups.
4. Keep `poetry install --only main`.
5. Remove Playwright browser installation from the core Docker image.
6. Make browser service/worker install it separately.

### Phase 2 — Embedding simplification

1. Remove `sentence-transformers` and `torch` from any non-ML installation path.
2. Keep current hash fallback.
3. Add FastEmbed behind the existing embedding abstraction.
4. Benchmark retrieval quality and memory.
5. Keep remote embeddings as the high-quality fallback.

### Phase 3 — Cloud dependency consolidation

1. Audit GCP usage.
2. Audit Boto3 usage.
3. Keep only the adapters required by production.
4. Prefer Supabase/Firebase/Upstash for the canonical platform stack.

### Phase 4 — LLM stack profiling

1. Measure LiteLLM import time and RSS.
2. Measure actual provider coverage.
3. Keep LiteLLM if its routing value exceeds its footprint.
4. Otherwise move to a small provider-adapter abstraction.

### Phase 5 — Guardrails

Add CI rules:

```text
Core image must not install:
torch
sentence-transformers
playwright
scipy
pandas
plotly
opencv-python-headless
```

unless a specific build profile explicitly enables them.

---

# 17. Success criteria

After the change, verify:

```text
Core image:
- no Torch
- no SentenceTransformers
- no Chromium
- no ML packages unless explicitly enabled
- startup still passes
- /api/v1/health/live -> 200
- /api/v1/health -> healthy/ready
- Redis -> Upstash connected
- database -> Supabase connected
```

Then measure:

```text
Docker image size
cold start time
RSS memory
import/startup time
p95 API latency
background task latency
embedding quality
```

Do not accept a dependency replacement solely because the package is smaller; accept it only if the required SupremeAI behavior remains equivalent or demonstrably better.

---

## Bottom line

**Your instinct about `sentence-transformers` is correct, but the bigger architectural opportunity is to separate optional capabilities from the core Render API.**

The strongest lightweight path for SupremeAI is:

```text
Core:
FastAPI + Supabase + Upstash Redis + provider SDKs

Async:
QStash

Browser:
isolated Playwright worker

Embeddings:
remote API OR FastEmbed

Research/ML:
separate environment
```

This gives you a much smaller, lower-memory, lower-maintenance production backend without removing the advanced features from the overall platform.
