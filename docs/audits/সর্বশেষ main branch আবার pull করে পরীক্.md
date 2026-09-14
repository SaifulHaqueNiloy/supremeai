সর্বশেষ main branch আবার pull করে পরীক্ষা করেছি।

সর্বশেষ commit:

304fdfe test: fix event loop closure issue in test_audit_logger

নিচের code fixes এখনো করা উচিত।

==================================================
১. Docker healthcheck path ভুল
==================================================

ফাইল:

backend/Dockerfile

বর্তমান লাইন 46:

CMD python -c "import urllib.request; urllib.request.urlopen('<http://localhost:8080/health/live>')" || exit 1

সমস্যা:

Application মূল health route হিসেবে নিচের path register করেছে:

/api/v1/health/live

বর্তমান `/health/live` compatibility route থাকার কথা থাকলেও Dockerfile-কে canonical production route ব্যবহার করা উচিত। এতে ভবিষ্যতে `/health` compatibility route সরালেও container healthcheck ভাঙবে না।

REMOVE:

লাইন 46-এর বর্তমান সম্পূর্ণ লাইন:

CMD python -c "import urllib.request; urllib.request.urlopen('<http://localhost:8080/health/live>')" || exit 1

ADD:

CMD python -c "import urllib.request; urllib.request.urlopen('<http://localhost:8080/api/v1/health/live>')" || exit 1

==================================================
২. CI coverage threshold খুব কম
==================================================

ফাইল:

.github/workflows/ci.yml

বর্তমান লাইন 48:

MIN_BACKEND_COVERAGE: 35

বর্তমান লাইন 49:

MIN_FRONTEND_COVERAGE: 9

সমস্যা:

এই threshold দিয়ে Production security platform-এর গুরুত্বপূর্ণ code খুব কম test coverage নিয়েও CI pass করতে পারে।

REMOVE:

MIN_BACKEND_COVERAGE: 35

MIN_FRONTEND_COVERAGE: 9

ADD:

MIN_BACKEND_COVERAGE: 80

MIN_FRONTEND_COVERAGE: 70

নোট:

Frontend threshold 70 করার আগে বর্তমান test suite-এ coverage কম থাকলে CI fail করবে। এটি সঠিক আচরণ। প্রথমে coverage বাড়াতে হবে, threshold কমিয়ে Production pass করানো যাবে না।

==================================================
৩. CI coverage comment অসম্পূর্ণ
==================================================

ফাইল:

.github/workflows/ci.yml

বর্তমান লাইন 3:

# 📊 Code coverage gates enabled (fail-under thresholds)

সমস্যা:

শুধু overall threshold যথেষ্ট নয়। Auth, HITL, tenant isolation এবং tool gateway-এর মতো critical module আলাদা করে enforce করা দরকার।

REMOVE:

# 📊 Code coverage gates enabled (fail-under thresholds)

ADD:

# Code coverage gates: overall thresholds plus mandatory critical-module coverage

==================================================
৪. Maintenance workflow-এ SHA pinning অসম্পূর্ণ
==================================================

ফাইল:

.github/workflows/maintenance.yml

বর্তমান লাইন 188:

uses: actions/setup-python@v5

সমস্যা:

এটি mutable tag। Supply-chain security-এর জন্য full commit SHA ব্যবহার করা উচিত।

REMOVE:

uses: actions/setup-python@v5

ADD:

uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0

==================================================
৫. Status document বাস্তব অবস্থার সঙ্গে অসঙ্গতিপূর্ণ
==================================================

ফাইল:

STATUS.md

বর্তমান লাইন 4:

**Overall System Health:** 🟢 OPERATIONAL (100% Core Passing)

সমস্যা:

একই ফাইলে নিচের Production কাজগুলো এখনো pending বলা আছে:

- Supabase ai_memory verification
- CI coverage hardening
- Live embedding insert test
- Production deployment verification
- Database migration verification

তাই “100% Core Passing” লেখা বিভ্রান্তিকর।

REMOVE:

**Overall System Health:** 🟢 OPERATIONAL (100% Core Passing)

ADD:

**Overall System Health:** Production verification pending

এবং Active Phase-এর পরে এই লাইন যোগ করুন:

**Production Readiness:** NO-GO until deployment, database migration, CI coverage, and live health verification are complete

==================================================
৬. Status-এ Python version ঠিক করতে হবে
==================================================

ফাইল:

STATUS.md

বর্তমান লাইন 15-এর Backend Core row-এ:

FastAPI (Python 3.12, Async SQLAlchemy 2.0)

কিন্তু backend/Dockerfile এবং CI দুটিতেই Python 3.11 ব্যবহার হচ্ছে।

REMOVE:

FastAPI (Python 3.12, Async SQLAlchemy 2.0)

ADD:

FastAPI (Python 3.11, Async SQLAlchemy 2.0)

==================================================
৭. Status-এ Firestore audit claim পুনরায় যাচাই করতে হবে
==================================================

ফাইল:

STATUS.md

বর্তমান লাইন 50:

**HITL & Cryptographic Audit Ledger:** Implemented `HITLEngine` and `HITLAuditLedger` (`hitl_audit_ledger` via Firestore)...

সমস্যা:

Production database architecture Supabase/PostgreSQL হলেও HITL audit এখনো Firestore-এ লেখা হচ্ছে। এটি ইচ্ছাকৃত হলে architecture documentation-এ Firebase/Firestore production dependency হিসেবে স্পষ্ট করতে হবে। ইচ্ছাকৃত না হলে PostgreSQL append-only audit table-এ migrate করতে হবে।

যদি Firestore রাখা না হয়, REMOVE:

`HITLAuditLedger` (`hitl_audit_ledger` via Firestore)

ADD:

`HITLAuditLedger` with append-only PostgreSQL persistence

==================================================
৮. Firestore/Firebase dependency সরানোর আগে code audit দরকার
==================================================

ফাইলগুলোতে পাওয়া গেছে:

- backend/pyproject.toml
- backend/tools/mcp/mcp_supabase.py
- backend/tools/security_tools/multi_account_rotator.py
- backend/tools/knowledge/git_knowledge_extractor.py
- docs/architecture/service_topology.yml

এখানে Firebase, Firestore এবং SQLite usage আছে।

এগুলো সব সরাসরি delete করা যাবে না, কারণ কিছু tool offline knowledge store বা migration utility হতে পারে।

প্রথমে প্রতিটি ব্যবহারের জন্য সিদ্ধান্ত নিন:

A. Production runtime dependency হলে:

- রাখুন
- documentation update করুন
- credentials এবং access scope verify করুন

B. Legacy বা migration-only হলে:

- runtime import সরান
- file-টি `tools/legacy/`-তে সরান
- CI production package থেকে বাদ দিন

C. Sensitive persistent data হলে:

- PostgreSQL/Supabase-এ migrate করুন
- tenant-scoped query যোগ করুন
- backup-এ অন্তর্ভুক্ত করুন

এই অংশে সরাসরি blind remove করা নিরাপদ নয়।

==================================================
৯. SQLite fallback Production-এ বন্ধ করা উচিত
==================================================

ফাইল খুঁজে যাচাই করতে হবে:

backend/core/
backend/services/
backend/api/
backend/memory/

যেখানে application runtime database হিসেবে SQLite fallback আছে, সেখানে fallback remove করতে হবে।

REMOVE ধরনের code:

if not database_url:
    database_url = "sqlite:///..."

অথবা:

try:
    connect_postgres()
except Exception:
    use_sqlite()

ADD:

if not database_url:
    raise RuntimeError(
        "Production database URL is required; SQLite fallback is disabled"
    )

আরও ভালোভাবে, এই validation startup-এর শুরুতেই করতে হবে, যাতে Production ভুল configuration নিয়ে boot না করে।

==================================================
১০. Auto-evolution direct promotion বন্ধ করতে হবে
==================================================

সর্বশেষ search-এ `AutoSkillCreator`, `SkillInstaller`, forge এবং HITL workflow পাওয়া গেছে। কিন্তু production-safe approval gate বাস্তবে সম্পূর্ণ enforce হয়েছে কিনা source-level verification ছাড়া নিশ্চিত বলা যাচ্ছে না।

যে code path-এ সরাসরি install/promotion হচ্ছে, সেটি:

REMOVE ধরনের call:

installer.install(skill)
installer.promote(skill)
auto_skill_creator.deploy(skill)

ADD:

approval = await hitl_engine.require_approval(
    action="skill_deploy",
    tenant_id=tenant_id,
    artifact_hash=artifact_hash,
)

if approval.status != "approved":
    raise PermissionError("Human approval is required before skill deployment")

await installer.install(
    skill,
    approval_id=approval.id,
    artifact_hash=artifact_hash,
)

==================================================
১১. Skill approval-এ artifact hash enforce করতে হবে
==================================================

Approval নেওয়ার পরে skill payload পরিবর্তিত হলে পুরনো approval ব্যবহার করা যাবে না।

REMOVE:

if approval.status == "approved":
    await installer.install(skill)

ADD:

current_hash = calculate_artifact_hash(skill)

if approval.status != "approved":
    raise PermissionError("Skill deployment is not approved")

if approval.artifact_hash != current_hash:
    raise PermissionError("Approved artifact does not match deployment artifact")

await installer.install(
    skill,
    approval_id=approval.id,
    artifact_hash=current_hash,
)

==================================================
১২. WebSocket JSON.parse নিরাপদ করতে হবে
==================================================

সর্বশেষ search-এ পাওয়া ফাইল:

tools/vscode-extension/src/providers/CodeFlowPanel.ts

লাইন 107:

window.data = JSON.parse(decodeURIComponent("${safe}"));

এখানে JSON input malformed হলে script crash করতে পারে। এটি VS Code webview-তে user-controlled বা generated data হলে আরও ঝুঁকিপূর্ণ।

REMOVE:

window.data = JSON.parse(decodeURIComponent("${safe}"));

ADD:

try {
  window.data = JSON.parse(decodeURIComponent("${safe}"));
} catch {
  window.data = null;
  console.error("[SupremeAI] Invalid webview payload");
}

নোট:

যদি `${safe}` পুরোপুরি trusted এবং server-generated হয়, তবুও defensive parsing রাখা উচিত।

==================================================
১৩. AuthHandler JSON parsing ইতোমধ্যে try/catch-এ আছে, remove করবেন না
==================================================

ফাইল:

tools/vscode-extension/src/handlers/AuthHandler.ts

লাইন 41:

const user = JSON.parse(decodeURIComponent(userParam));

এর পরের লাইনগুলোতে try/catch আছে। এটি বর্তমান অবস্থায় একটি confirmed bug নয়। তাই এই অংশে patch করা প্রয়োজন নেই।

==================================================
১৪. Test/example code Production package থেকে বাদ দিতে হবে
==================================================

ফাইল:

backend/examples/sample_buggy.py

লাইন 181-182-এ ইচ্ছাকৃতভাবে signature verification বন্ধ করার example আছে:

return jwt.decode(token, options={"verify_signature": False})

এটি production runtime-এ imported না হলেও dangerous pattern search এবং accidental import-এর ঝুঁকি তৈরি করে।

REMOVE:

backend/examples/sample_buggy.py

অথবা file সম্পূর্ণ delete না করলে:

- `backend/examples/` production image থেকে বাদ দিন
- CI-তে নিশ্চিত করুন এটি runtime package-এ ঢোকে না
- README-তে স্পষ্টভাবে insecure demonstration লিখুন
- Secret/security scanner-এ এটি allowlist করবেন না

==================================================
১৫. GitHub workflow-এর সব action পুনরায় SHA scan করতে হবে
==================================================

বর্তমান grep-এ maintenance.yml line 188-এ `actions/setup-python@v5` পাওয়া গেছে। অন্য workflow-গুলোতে সব reference full SHA কিনা পুনরায় যাচাই করতে হবে।

যে pattern থাকা যাবে না:

uses: owner/action@main
uses: owner/action@master
uses: owner/action@v4
uses: owner/action@v5

যে pattern ব্যবহার করতে হবে:

uses: owner/action@40-character-commit-sha # version

==================================================
Confirmed fixes বনাম manual configuration:

কোডে সরাসরি fix করা দরকার:

1. backend/Dockerfile line 46 health path
2. .github/workflows/ci.yml line 48 coverage
3. .github/workflows/ci.yml line 49 coverage
4. .github/workflows/maintenance.yml line 188 SHA pin
5. STATUS.md line 4 status correction
6. STATUS.md line 15 Python version correction
7. CodeFlowPanel.ts line 107 defensive JSON parsing
8. Production runtime-এ SQLite fallback থাকলে fail-fast করা
9. Auto-evolution promotion-এ mandatory approval এবং artifact hash

কোড দিয়ে fix করা যাবে না, deployment/configuration দরকার:

1. SUPABASE_DATABASE_URL_WRITER
2. Render latest deployment
3. Alembic migration execution
4. Render health probe
5. Backup restore drill
6. Real canary traffic split
7. Render rollback
8. Production memory/load test
9. Live Supabase pgvector insert test
10. Production secrets rotation

চূড়ান্ত Production status:

বর্তমান codebase: Production Candidate
বর্তমান deployment status: Verification Pending
বর্তমান Go/No-Go: NO-GO

উপরের confirmed code fixes করার পরে এবং Render, database migration, CI, health, backup, canary ও rollback test সফল হলে তবেই Production launch করা উচিত।
