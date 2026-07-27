# SupremeAI 2.0 — স্ব-পরিচালিত AI: সম্পূর্ণ ইমপ্লিমেন্টেশন প্ল্যান

> **লক্ষ্য:** `3.3supremeai-gaps-analysis.md`-এর Gap বিশ্লেষণ অনুযায়ী SupremeAI-কে সত্যিকারের স্ব-পরিচালিত (Self-Directed) AI-তে রূপান্তরিত করা — Devin, Cursor ও Copilot-এর সমকক্ষ বা তার চেয়ে উন্নত।

---

## বর্তমান অবস্থা (Current State)

| ফাইল | অবস্থা | আকার | সমস্যা |
|------|--------|------|--------|
| `cloud_sandbox_orchestrator.py` | ⚠️ অসম্পূর্ণ | 5.7 KB | শুধু Mock/API shell, persistent state নেই |
| `parallel_agent_executor.py` | ✅ কিছুটা সম্পূর্ণ | 10 KB | ভালো কিন্তু Redis pub/sub যোগ করা দরকার |
| `image_to_code.py` | ⚠️ অসম্পূর্ণ | 5.2 KB | React/Flutter output নেই |
| `diagram_to_architecture.py` | ⚠️ অসম্পূর্ণ | 7.4 KB | Terraform output নেই |
| `style_learner.py` | ⚠️ আংশিক | 7.6 KB | AST pattern analysis দুর্বল |
| `pr_reviewer.py` | ⚠️ আংশিক | 9.4 KB | GitHub webhook integration নেই |
| `code_smell_detector.py` | ✅ সবচেয়ে সম্পূর্ণ | 23 KB | CI/CD integration নেই |
| `game_dev_agent.py` | ❌ খালি stub | 1.4 KB | বাস্তবায়ন নেই |
| `blockchain_agent.py` | ❌ খালি stub | 2.4 KB | বাস্তবায়ন নেই |
| `legal_agent.py` | ❌ খালি stub | 2.3 KB | বাস্তবায়ন নেই |

---

## Open Questions (User Review Required)

> [!IMPORTANT]
> নিচের বিষয়গুলো বাস্তবায়নের আগে সিদ্ধান্ত নেওয়া দরকার:
>
> 1. **Cloud Provider**: Cloud Sandbox-এর জন্য `RunPod` নাকি `Modal` ব্যবহার করবেন? (RunPod সস্তা, Modal zero-cost friendly)
> 2. **PR Review Bot**: GitHub Webhook-এর জন্য public URL লাগবে — Render.com ব্যবহার করবেন?
> 3. **Phase Priority**: নিচের ধাপগুলো কি ক্রমানুসারে করবেন নাকি সব একসাথে শুরু করবেন?

> [!WARNING]
> `game_dev_agent.py`, `blockchain_agent.py`, `legal_agent.py` — এই ফাইলগুলো সম্পূর্ণ নতুনভাবে লিখতে হবে। পুরনো stub ফাইলগুলো overwrite করা হবে।

---

## প্রস্তাবিত পরিবর্তনসমূহ (Proposed Changes)

---

### ধাপ ১: ক্রিটিক্যাল গ্যাপ — Autonomous Engine (সপ্তাহ ১-৩)

**লক্ষ্য:** Devin-এর মতো স্বায়ত্তশাসিত কোডিং ক্ষমতা তৈরি

---

#### [MODIFY] [cloud_sandbox_orchestrator.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tools/cloud_sandbox_orchestrator.py)

**কী পরিবর্তন হবে:**
- Persistent volume mount সহ RunPod/Modal-এ দীর্ঘস্থায়ী VM তৈরি
- Session-aware state management (কাজ মাঝপথে থামলে পুনরায় শুরু করতে পারবে)
- File system ops: multi-file read/write/execute
- Dependency installer: `pip`, `npm`, `apt` রান করার ক্ষমতা
- WebSocket-based live log streaming

**নতুন ক্লাস/মেথড:**
```python
class PersistentSandbox:
    async def create_with_volume(spec) -> SandboxSession
    async def execute_in_session(session_id, command) -> StreamedOutput  
    async def install_dependency(session_id, pkg_manager, package) -> bool
    async def upload_file(session_id, path, content) -> bool
    async def download_file(session_id, path) -> bytes
    async def destroy_sandbox(session_id) -> bool
```

---

#### [MODIFY] [parallel_agent_executor.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tools/parallel_agent_executor.py)

**কী পরিবর্তন হবে:**
- Redis Pub/Sub যোগ করে এজেন্টগুলোর মধ্যে real-time যোগাযোগ
- Shared state: একজন `Coder` এজেন্ট কোড লিখলে `Tester` এজেন্ট সাথে সাথে টেস্ট লিখতে শুরু করবে
- Task DAG (Directed Acyclic Graph) দিয়ে dependency-aware scheduling
- Result aggregation with voting (একাধিক এজেন্টের আউটপুট থেকে সেরাটি বাছাই)

**নতুন ক্লাস/মেথড:**
```python
class AgentDAGScheduler:
    async def execute_dag(task_graph: DAG) -> AggregatedResult
    async def broadcast_state(channel, state) -> None
    async def subscribe_to_updates(channel) -> AsyncIterator
```

---

#### [NEW] `backend/api/routes/sandbox_api.py`

- `POST /api/v1/sandbox/create` — নতুন persistent sandbox তৈরি
- `POST /api/v1/sandbox/{id}/execute` — command রান করা
- `GET /api/v1/sandbox/{id}/logs` — live log streaming (SSE)
- `DELETE /api/v1/sandbox/{id}` — sandbox মুছে ফেলা

---

### ধাপ ২: মাল্টি-মডাল ইন্টেলিজেন্স (সপ্তাহ ২-৪)

**লক্ষ্য:** Claude/Cursor-এর মতো image ও diagram থেকে কোড তৈরির ক্ষমতা

---

#### [MODIFY] [image_to_code.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tools/image_to_code.py)

**কী পরিবর্তন হবে:**
- Figma/UI screenshot → pixel-perfect **React** component তৈরি
- Figma/UI screenshot → Flutter widget তৈরি
- Tailwind CSS class mapping
- Color palette extraction ও CSS variable generation
- Component tree extraction (nested components শনাক্ত করা)

**নতুন মেথড:**
```python
async def figma_to_react(image_path, framework="react") -> ComponentCode
async def extract_color_palette(image_path) -> ColorTheme
async def detect_component_tree(image_path) -> ComponentHierarchy
```

---

#### [MODIFY] [diagram_to_architecture.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tools/diagram_to_architecture.py)

**কী পরিবর্তন হবে:**
- হাতে আঁকা ডায়াগ্রাম → **Terraform** HCL কনফিগারেশন
- Cloud architecture diagram → **Docker Compose** / **Kubernetes YAML**
- ER diagram → **SQLAlchemy Model** / **Prisma Schema**
- Flowchart → **Python/TypeScript** logic code

**নতুন মেথড:**
```python
async def to_terraform(diagram_path, cloud_provider="gcp") -> TerraformCode
async def to_kubernetes(diagram_path) -> K8sManifest  
async def to_database_schema(er_diagram_path, orm="sqlalchemy") -> SchemaCode
```

---

### ধাপ ৩: পার্সোনালাইজেশন ও কোড কোয়ালিটি (সপ্তাহ ৩-৫)

**লক্ষ্য:** Copilot/Amazon Q-এর মতো কোড স্টাইল শেখা ও স্বয়ংক্রিয় রিভিউ

---

#### [MODIFY] [style_learner.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tools/style_learner.py)

**কী পরিবর্তন হবে:**
- `tree-sitter` দিয়ে AST-level কোড pattern বিশ্লেষণ
- Variable naming convention শেখা (snake_case, camelCase, হাঙ্গেরিয়ান)
- Function length preference শেখা
- Import ordering style শেখা  
- Comment style detection (inline, docstring ইত্যাদি)
- Vector embedding-এ style সংরক্ষণ → নতুন কোড generate করার সময় inject করা

**নতুন মেথড:**
```python
async def analyze_codebase(repo_path) -> StyleProfile
async def generate_with_style(prompt, user_id) -> StyledCode
async def sync_team_style(repo_path, team_id) -> TeamStyleProfile
```

---

#### [MODIFY] [pr_reviewer.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tools/pr_reviewer.py)

**কী পরিবর্তন হবে:**
- GitHub Webhook receiver (PR opened/updated event)
- `git diff` বিশ্লেষণ করে লাইন-বাই-লাইন কমেন্ট
- Security vulnerability scan (SQL injection, XSS, hardcoded secrets)
- Style compliance check (ব্যবহারকারীর নিজের style দিয়ে তুলনা)
- Auto-approve যদি সব চেক পাস করে
- GitHub API দিয়ে PR-এ সরাসরি কমেন্ট পোস্ট

**নতুন ফ্লো:**
```
GitHub PR → Webhook → pr_reviewer.py → 
  ├── Security Scan
  ├── Style Check (style_learner.py)
  ├── Code Smell (code_smell_detector.py)
  └── Post Comments → GitHub PR Review
```

---

#### [MODIFY] [code_smell_detector.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tools/code_smell_detector.py)

**কী পরিবর্তন হবে:**
- CI/CD pipeline-এ mandatory integration (GitHub Actions step)
- Pre-commit hook installer
- JSON/SARIF রিপোর্ট output (GitHub Security tab-এ দেখায়)
- রিপোর্ট ইতিহাস ট্র্যাকিং (কোড quality সময়ের সাথে ভালো হচ্ছে কিনা)

#### [NEW] `backend/api/routes/pr_review_api.py`

- `POST /api/v1/pr-review/webhook` — GitHub webhook endpoint
- `GET /api/v1/pr-review/{pr_id}/status` — রিভিউ স্ট্যাটাস

---

### ধাপ ৪: বিশেষায়িত ডোমেইন এজেন্ট (সপ্তাহ ৪-৬)

**লক্ষ্য:** নির্দিষ্ট শিল্পে সেরা হওয়া

---

#### [MODIFY] [game_dev_agent.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tools/game_dev_agent.py)

**সম্পূর্ণ নতুন বাস্তবায়ন:**
```python
class GameDevAgent:
    # Unity C# script generation
    async def generate_unity_script(description, script_type) -> UnityScript
    # Game design document থেকে কোড
    async def gdd_to_code(gdd_text, engine="unity") -> GameCode
    # Asset description থেকে Blender Python script
    async def generate_asset_script(asset_description) -> BlenderScript
    # Performance profiling suggestions
    async def profile_game_code(code) -> PerformanceReport
```

---

#### [MODIFY] [blockchain_agent.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tools/blockchain_agent.py)

**সম্পূর্ণ নতুন বাস্তবায়ন:**
```python
class BlockchainAgent:
    # Solidity smart contract generation
    async def generate_contract(description, standard="ERC20") -> SolidityContract
    # Security audit
    async def audit_contract(solidity_code) -> SecurityReport
    # Gas optimization
    async def optimize_gas(solidity_code) -> OptimizedContract
    # Test generation (Hardhat/Foundry)
    async def generate_tests(contract_code) -> TestSuite
```

---

#### [MODIFY] [legal_agent.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/tools/legal_agent.py)

**সম্পূর্ণ নতুন বাস্তবায়ন:**
```python
class LegalAgent:
    # চুক্তি তৈরি
    async def generate_contract(contract_type, parties, terms) -> LegalDocument
    # ক্লজ বিশ্লেষণ
    async def analyze_clause(clause_text, jurisdiction="BD") -> ClauseAnalysis
    # Compliance check
    async def check_compliance(document, regulation) -> ComplianceReport
    # Terms of Service / Privacy Policy
    async def generate_tos(product_description, jurisdiction) -> TosDocument
```

---

### ধাপ ৫: CI/CD Integration ও API Wiring (সপ্তাহ ৫-৬)

**লক্ষ্য:** সব কিছু একসাথে সংযুক্ত করা

---

#### [MODIFY] `.github/workflows/monorepo_ci_cd.yml`

- `code-smell-check` step যোগ করা (mandatory, blocking)
- `pr-review-bot` step যোগ করা
- `style-lint` step যোগ করা

#### [MODIFY] `backend/main.py`

নতুন router গুলো register করা:
```python
app.include_router(sandbox_api.router, prefix="/api/v1/sandbox")
app.include_router(pr_review_api.router, prefix="/api/v1/pr-review")
```

#### [NEW] `backend/tests/tools/` — নতুন test files:

- `test_cloud_sandbox_full.py`
- `test_pr_reviewer_webhook.py`
- `test_image_to_code_react.py`
- `test_diagram_to_terraform.py`
- `test_style_learner_ast.py`
- `test_game_dev_agent.py`
- `test_blockchain_agent.py`
- `test_legal_agent.py`

---

## ফাইল পরিবর্তনের সারসংক্ষেপ

| ফাইল | ধরন | ধাপ | কাজের পরিমাণ |
|------|-----|-----|-------------|
| `cloud_sandbox_orchestrator.py` | MODIFY | ১ | বড় (persistent state + session) |
| `parallel_agent_executor.py` | MODIFY | ১ | মাঝারি (Redis pub/sub) |
| `sandbox_api.py` | NEW | ১ | মাঝারি |
| `image_to_code.py` | MODIFY | ২ | মাঝারি (React/Flutter output) |
| `diagram_to_architecture.py` | MODIFY | ২ | মাঝারি (Terraform output) |
| `style_learner.py` | MODIFY | ৩ | বড় (tree-sitter AST) |
| `pr_reviewer.py` | MODIFY | ৩ | বড় (webhook + GitHub API) |
| `code_smell_detector.py` | MODIFY | ৩ | ছোট (CI/CD integration) |
| `pr_review_api.py` | NEW | ৩ | মাঝারি |
| `game_dev_agent.py` | MODIFY/Rewrite | ৪ | বড় |
| `blockchain_agent.py` | MODIFY/Rewrite | ৪ | বড় |
| `legal_agent.py` | MODIFY/Rewrite | ৪ | বড় |
| `monorepo_ci_cd.yml` | MODIFY | ৫ | ছোট |
| `backend/main.py` | MODIFY | ৫ | ছোট |
| `tests/tools/*.py` (8 files) | NEW | ৫ | মাঝারি |

**মোট ফাইল: ১৫ টি (৩ নতুন + ১২ আপডেট)**

---

## ভেরিফিকেশন প্ল্যান

### স্বয়ংক্রিয় টেস্ট (Automated Tests)

```bash
# সব নতুন tool টেস্ট রান
poetry run pytest backend/tests/tools/ -v --tb=short

# Coverage চেক
poetry run pytest --cov=backend/tools --cov-report=term-missing

# Type checking
poetry run mypy backend/tools/

# Lint
poetry run ruff check backend/tools/
```

### ম্যানুয়াল ভেরিফিকেশন

1. **Sandbox**: একটি real Python script রান করে file তৈরি করতে পারে কিনা
2. **Image-to-Code**: একটি UI screenshot থেকে valid React component generate হয় কিনা
3. **PR Reviewer**: একটি test PR-এ webhook fire করে comment আসে কিনা
4. **Style Learner**: কোডবেস analyze করে style profile export করতে পারে কিনা
5. **Game Dev Agent**: একটি Unity coroutine script generate করতে পারে কিনা
6. **Blockchain Agent**: একটি ERC-20 token contract generate ও audit করতে পারে কিনা
7. **Legal Agent**: একটি NDA document তৈরি করতে পারে কিনা

---

## Timeline

```
সপ্তাহ ১-২: ধাপ ১ — Cloud Sandbox + Parallel Executor
সপ্তাহ ২-৩: ধাপ ২ — Image-to-Code + Diagram-to-Architecture  
সপ্তাহ ৩-৪: ধাপ ৩ — Style Learner + PR Reviewer + Code Smell CI
সপ্তাহ ৪-৫: ধাপ ৪ — Game Dev + Blockchain + Legal Agents
সপ্তাহ ৫-৬: ধাপ ৫ — API Wiring + Tests + CI/CD Integration
```

**মোট সময়: ৬ সপ্তাহ | গ্যাপ বন্ধ: ২৫+ | কভার করা ডোমেইন: Devin, Cursor, Copilot, Amazon Q**

---

_পরিকল্পনা তৈরি: 2026-07-12 | ভিত্তি: 3.3supremeai-gaps-analysis.md_
