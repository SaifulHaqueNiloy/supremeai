SupremeAI রিপোজিটরি গভীরভাবে পর্যালোচনা করে দেখা গেছে, বর্তমান কোডবেসকে সরাসরি Production-এ নেওয়া নিরাপদ নয়। অনেক গুরুত্বপূর্ণ Security Fix করা হয়েছে, কিন্তু Deployment, Database, Observability, CI/CD এবং Self-Evolution অংশে এখনও বেশ কিছু Blocker আছে।

রিভিউ করা হয়েছে:

- বর্তমান GitHub main branch
- Backend FastAPI কোড
- Frontend React/Vite কোড
- CI/CD workflows
- Production Docker configuration
- Audit checklist
- Manual deployment steps
- Silent error audit
- Secrets এবং infrastructure documentation
- সর্বশেষ commit: 304fdfe

প্রোডাকশনের আগে করণীয় পূর্ণ তালিকা:

# ==================================================

P0 — Production Blocker

১. Render-এ সর্বশেষ কোড Redeploy করতে হবে

বর্তমান Render deployment পুরনো image ব্যবহার করছে। Audit অনুযায়ী পুরনো deployed image-এ:

- Token refresh 401 হচ্ছিল
- Database readiness 503 হচ্ছিল
- HITL router load হচ্ছিল না
- Supabase read-only transaction error হচ্ছিল
- automation_executions table missing ছিল
- Memory usage প্রায় 90% ছিল

সর্বশেষ main branch deploy না করা পর্যন্ত code-level fix বাস্তবে production-এ কার্যকর হবে না।

করনীয়:

- Render-এ নতুন image deploy করুন
- Deployment SHA যাচাই করুন
- পুরনো image cache বা stale deployment ব্যবহার হচ্ছে কিনা পরীক্ষা করুন

২. Render-এ SUPABASE_DATABASE_URL_WRITER সেট করতে হবে

এটি সবচেয়ে গুরুত্বপূর্ণ অসম্পূর্ণ configuration।

বর্তমানে read-only pooler connection দিয়ে DDL চালানোর চেষ্টা হচ্ছিল। ফলে:

- CREATE TABLE ব্যর্থ হচ্ছিল
- ai_memory schema তৈরি হচ্ছিল না
- checkpoints table তৈরি হচ্ছিল না
- automation_executions table তৈরি হচ্ছিল না
- database readiness ব্যর্থ হচ্ছিল

Render environment-এ writable direct database URL দিতে হবে:

SUPABASE_DATABASE_URL_WRITER

এটি অবশ্যই Supabase-এর writable direct connection হতে হবে। Read-only pooler বা port 6543 ব্যবহার করা যাবে না, যদি সেটি DDL সমর্থন না করে। সাধারণত direct PostgreSQL connection ব্যবহার করতে হবে।

৩. Database migration pipeline Production deploy-এর সাথে যুক্ত করতে হবে

বর্তমানে migration ফাইল থাকলেও startup বা Render pre-deploy-এ নিয়মিতভাবে:

alembic upgrade head

চালানোর নিশ্চয়তা নেই।

ফলে database code এবং actual schema-এর মধ্যে drift তৈরি হবে।

বিশেষ করে:

- automation_executions
- automation_execution_attempts
- ai_memory
- checkpoints
- নতুন index
- tenant-related columns

এসব schema Production-এ সত্যিই আছে কিনা নিশ্চিত করতে হবে।

ভালো পদ্ধতি:

- Render pre-deploy command-এ migration চালানো
- অথবা আলাদা CI migration job তৈরি করা
- migration failure হলে deploy বন্ধ করা
- destructive migration-এর জন্য manual approval রাখা

৪. Database readiness endpoint আবার Production-এ পরীক্ষা করতে হবে

এই endpoint অবশ্যই 200 দিতে হবে:

/api/v1/health/live

এবং:

/api/v1/health/ready

আগের deployed version-এ live 200 হলেও ready 503 ছিল। নতুন deployment-এর পরে দুই endpoint-ই পরীক্ষা করতে হবে।

Ready endpoint-এ বিশেষভাবে যাচাই করতে হবে:

- Writable database connection
- Redis connection
- Supabase connection
- Required tables
- Required migrations
- AI provider configuration

৫. `/api/v1/evolution/forge`-এ Human Approval বাধ্যতামূলক করতে হবে

বর্তমান audit নিজেই উল্লেখ করেছে যে evolution forge route স্বয়ংক্রিয়ভাবে generated skill promote করতে পারে।

এটি অত্যন্ত ঝুঁকিপূর্ণ, কারণ:

- AI-generated code তৈরি হচ্ছে
- Sandbox ও AST check থাকলেও ভুল code production-এ যেতে পারে
- Human-in-the-loop policy অনুযায়ী high-risk production change approval দরকার
- Autonomous code mutation একটি supply-chain এবং privilege escalation ঝুঁকি তৈরি করে

Production-এর আগে সিদ্ধান্ত নিতে হবে:

- Forge proposal তৈরি করবে, কিন্তু সরাসরি install করবে না
- Admin approval ছাড়া SkillInstaller চালানো যাবে না
- Approval-এর সাথে user, role, timestamp, payload hash এবং artifact hash সংরক্ষণ করতে হবে
- Reject, expire, replay এবং duplicate approval test করতে হবে

৬. Self-Evolution deployment-এর জন্য বাস্তব Canary এবং Rollback ব্যবস্থা করতে হবে

বর্তমানে CanaryRolloutController আছে, কিন্তু বাস্তব traffic splitting পুরোপুরি wired নয়।

এখনো নিশ্চিত নয়:

- কত শতাংশ user নতুন version পাবে
- Canary failure কীভাবে detect হবে
- কোন version-এ rollback হবে
- Render deployment কীভাবে স্বয়ংক্রিয়ভাবে rollback করবে
- Error rate, latency এবং success rate বাস্তব traffic থেকে আসছে কিনা

বিশেষ ঝুঁকি:

- Fake বা synthetic success rate ব্যবহার করা যাবে না
- Canary pass না করেই production promotion করা যাবে না
- Rollback monitor বর্তমানে Cloud Run-কেন্দ্রিক হলে Render অনুযায়ী ঠিক করতে হবে

# ==================================================

P1 — অত্যন্ত গুরুত্বপূর্ণ

৭. CI coverage gate বাস্তবসম্মত করতে হবে

CI workflow-এ দেখা যাচ্ছে:

- MIN_BACKEND_COVERAGE: 35
- MIN_FRONTEND_COVERAGE: 9

এই threshold Production-grade security platform-এর জন্য অত্যন্ত কম।

অন্যদিকে documentation এবং pyproject-এ 80% বা তার বেশি coverage-এর কথা বলা হয়েছে।

এই inconsistency দূর করতে হবে:

- Backend overall coverage: কমপক্ষে 80%
- Security-critical modules: কমপক্ষে 90%
- Auth modules: কমপক্ষে 90%
- HITL modules: কমপক্ষে 90%
- Tool gateway: কমপক্ষে 90%
- Tenant isolation: কমপক্ষে 90%
- Frontend critical flows-এর জন্য বাস্তব coverage gate নির্ধারণ করতে হবে
- CI যেন শুধু test pass নয়, coverage fail হলে ব্যর্থ হয়

৮. Full CI pipeline সফলভাবে চালিয়ে প্রমাণ সংরক্ষণ করতে হবে

লোকাল বা offline test pass যথেষ্ট নয়।

সত্যিকারের CI environment-এ যাচাই করতে হবে:

- PostgreSQL 16
- Redis
- Production-like environment variables
- Backend test suite
- Frontend build
- Frontend test
- OpenAPI validation
- Migration validation
- Security scanners
- Docker build
- Startup health probe
- Coverage gate

CI run ID এবং artifact সংরক্ষণ করতে হবে।

৯. Production Docker image build করতে হবে

Docker engine দিয়ে সম্পূর্ণ Production image build এখনও verified নয়।

যাচাই করতে হবে:

- backend/Dockerfile সত্যিই build হয়
- Poetry lockfile reproducible
- Production image-এ dev dependency নেই
- ML/browser dependency ঢুকে যায়নি
- Image size গ্রহণযোগ্য
- Container 512 MB memory limit-এ boot করে
- Port 8080 সঠিকভাবে expose করে
- Health check কাজ করে
- Graceful shutdown কাজ করে

১০. Runtime memory pressure পুনরায় মাপতে হবে

পূর্বে boot-এর সময় প্রায় 460 MB / 512 MB ব্যবহার হচ্ছিল, যা প্রায় 90%।

Lazy singleton fix করার পরে বাস্তব Render metrics যাচাই করা হয়নি।

চেক করতে হবে:

- Boot RSS memory
- Peak memory
- Memory leak
- Long-running worker memory
- WebSocket connection বৃদ্ধির পরে memory
- Multiple conversation-এর পরে memory
- AI request চলাকালে memory
- Garbage collection behavior

যদি memory 85%-এর বেশি থাকে, তাহলে:

- Heavy singleton খুঁজে বের করতে হবে
- Module-level object creation বন্ধ করতে হবে
- HTTP client pool সীমিত করতে হবে
- Cache size সীমিত করতে হবে
- Worker scaling strategy নির্ধারণ করতে হবে

১১. Read-only Supabase এবং writable Supabase connection আলাদা রাখতে হবে

Database operation ভাগ করা প্রয়োজন:

- Read query: pooler/read connection
- Migration/DDL: direct writer connection
- Schema bootstrap: writer connection
- Backup/restore: writer বা privileged connection

Pooler connection দিয়ে কখনো:

- CREATE TABLE
- ALTER TABLE
- CREATE INDEX
- Migration
- DDL bootstrap

চালানো যাবে না।

১২. HITL audit log Redis থেকে durable append-only storage-এ নিতে হবে

বর্তমানে audit record-এর একটি অংশ Redis-এ ৩০ দিনের retention-এ থাকে।

এটি compliance এবং forensic investigation-এর জন্য যথেষ্ট নয়।

Production-এর জন্য:

- PostgreSQL append-only audit table তৈরি করতে হবে
- Audit row update/delete নিষিদ্ধ করতে হবে
- Hash chain অথবা signed event ব্যবহার করতে হবে
- Actor, tenant, action, payload hash, decision, timestamp সংরক্ষণ করতে হবে
- Approval এবং execution আলাদা event হিসেবে রাখতে হবে
- Redis শুধু temporary queue/cache হিসেবে রাখা যেতে পারে
- Backup-এ audit data অন্তর্ভুক্ত করতে হবে

১৩. Backup এবং Restore drill বাস্তবে চালাতে হবে

Backup policy documentation আছে, কিন্তু বাস্তব restore drill এখনও manual।

চেক করতে হবে:

- Database backup নিয়মিত তৈরি হচ্ছে কিনা
- Backup encrypted কিনা
- Backup retention policy কাজ করছে কিনা
- Scratch database-এ restore সম্ভব কিনা
- Restore-এর পরে application boot করে কিনা
- Conversation round-trip কাজ করে কিনা
- Memory recall কাজ করে কিনা
- HITL audit record পাওয়া যায় কিনা
- RPO এবং RTO বাস্তবে পূরণ হচ্ছে কিনা

১৪. সব frontend authenticated endpoint-এর সাথে token পাঠাতে হবে

Backend authentication শক্ত করা হয়েছে, কিন্তু frontend client-গুলোর জন্য breaking change তৈরি হয়েছে।

বিশেষভাবে যাচাই করতে হবে:

- Markdown export UI
- CI dashboard WebSocket
- Service topology WebSocket
- `/agent/terminal-stream`
- Health stream
- Admin dashboard
- Conversation history
- Memory endpoints

যেসব WebSocket এখন token চায়, সেখানে frontend থেকে JWT সঠিকভাবে পাঠানো হচ্ছে কিনা পরীক্ষা করতে হবে।

শুধু token storage থাকলেই হবে না; expired token হলে:

- Refresh করতে হবে
- Connection পুনরায় তৈরি করতে হবে
- User-কে পরিষ্কার error দিতে হবে
- Infinite reconnect loop বন্ধ করতে হবে

১৫. GitHub Actions-এর সব action full SHA দিয়ে pin করতে হবে

CI file-এ কিছু action SHA-pinned হলেও অনেক action এখনো version tag ব্যবহার করছে:

- actions/setup-python@v5
- docker/setup-buildx-action@v3
- sigstore/cosign-installer@v3.5.0
- anchore/sbom-action@v0.16.0
- actions/checkout@v4
- actions/setup-node@v4
- trufflesecurity/trufflehog@main

বিশেষ ঝুঁকি:

- `@main` সবচেয়ে ঝুঁকিপূর্ণ
- Tag force-move হতে পারে
- Supply-chain attack হলে CI compromise হতে পারে

সব action 40-character immutable commit SHA দিয়ে pin করতে হবে।

১৬. Image signing এবং SBOM বাধ্যতামূলক করতে হবে

Cosign এবং SBOM tooling আছে, কিন্তু বাস্তব release artifact-এ এগুলো সম্পূর্ণভাবে enforced কিনা নিশ্চিত নয়।

Production-এর আগে:

- Docker image sign করতে হবে
- Signature verify না হলে deploy বন্ধ করতে হবে
- SBOM generate করতে হবে
- Release artifact হিসেবে SBOM upload করতে হবে
- Critical vulnerability থাকলে build fail করতে হবে
- Image provenance সংরক্ষণ করতে হবে

১৭. Secrets rotation এবং leak response process তৈরি করতে হবে

Secrets documentation আছে, কিন্তু operational process আরও পরিষ্কার করা দরকার।

চেক করতে হবে:

- JWT secret কীভাবে rotate হবে
- Encryption key rotate করলে পুরনো data কীভাবে decrypt হবে
- Redis credential rotation
- Supabase service-role key rotation
- Render secret rotation
- GitHub Actions secret rotation
- Compromised credential হলে incident response
- Old secrets revoke করা হয় কিনা
- Production এবং staging secret আলাদা কিনা

কোনো `.env` ফাইল Git history-তে থাকলে:

- Secret revoke করতে হবে
- Git history scan করতে হবে
- Gitleaks এবং TruffleHog দিয়ে full history scan করতে হবে

১৮. `DEBUG` এবং unsafe error response Production-এ বন্ধ আছে কিনা নিশ্চিত করতে হবে

Backend error response-এ অনেক জায়গা ঠিক করা হয়েছে, কিন্তু পুরো কোডবেসে নিশ্চিত করতে হবে:

- Stack trace client-এ যাচ্ছে না
- `str(e)` response-এ যাচ্ছে না
- SQL error প্রকাশ পাচ্ছে না
- Provider key বা URL প্রকাশ পাচ্ছে না
- Tenant/user data অন্য user দেখতে পাচ্ছে না
- Debug mode বন্ধ
- Swagger/ReDoc public রাখা হবে কিনা সিদ্ধান্ত নেওয়া হয়েছে
- Correlation ID ছাড়া internal detail পাঠানো হচ্ছে না

# ==================================================

P2 — Production Hardening

১৯. Silent error handling কমাতে হবে

Silent error audit-এ পাওয়া গেছে:

- `except Exception: pass` প্রায় 32টি
- Default return দিয়ে error লুকানো প্রায় 106টি
- TypeScript-এর empty catch প্রায় 30টি
- Floating fetch promise প্রায় 11টি
- `contextlib.suppress(Exception)` প্রায় 11টি

সবচেয়ে ঝুঁকিপূর্ণ জায়গা:

- Backup script
- RAG indexing
- Memory service
- Code validator
- Admin operations
- Auto-scaling
- Uptime tracker
- Redis cache
- WebSocket handlers
- Frontend API client
- Global error boundary
- Auth store
- Admin dashboard
- VS Code extension

প্রতিটি error path-এ অন্তত:

- Structured log
- Correlation ID
- Error counter/metric
- User-safe fallback
- Retry বা circuit breaker

থাকা উচিত।

বিশেষভাবে backup failure কখনো silently ignore করা যাবে না।

২০. WebSocket JSON parsing নিরাপদ করতে হবে

কিছু frontend WebSocket handler-এ সরাসরি:

JSON.parse(event.data)

ব্যবহার করা হয়েছে।

Malformed frame বা proxy message এলে:

- Handler crash করতে পারে
- Connection connected দেখাতে পারে
- Dashboard update বন্ধ হতে পারে
- User কোনো error দেখতে নাও পারে

প্রতিটি WebSocket message-এ:

- try/catch
- Message schema validation
- Invalid frame counter
- Warning log
- Connection state update

যোগ করতে হবে।

২১. Floating fetch promise ঠিক করতে হবে

কিছু frontend জায়গায় fetch await করা হয়নি এবং `.catch()`-ও নেই।

এর ফলে:

- Unhandled rejection হতে পারে
- Admin UI stale হয়ে থাকতে পারে
- Screenshot বা browser session ব্যর্থ হলেও বোঝা যাবে না
- Production console error তৈরি হবে

সব fetch:

- await করতে হবে
- অথবা `.catch()` সহ logging করতে হবে
- AbortController ব্যবহার করতে হবে
- Timeout রাখতে হবে

২২. Frontend error reporting বাস্তব করতে হবে

GlobalErrorBoundary এবং অন্যান্য frontend error handling থাকলেও error telemetry বাস্তবে কাজ করছে কিনা নিশ্চিত নয়।

চেক করতে হবে:

- Runtime crash capture
- API error capture
- Chunk loading error
- WebSocket failure
- Authentication expiry
- Browser compatibility failure
- Source map নিরাপত্তা
- PII এবং token redact করা হচ্ছে কিনা

২৩. API rate limiting আরও ভালোভাবে যাচাই করতে হবে

Rate limiter থাকলেও Production load test দরকার।

পরীক্ষা করতে হবে:

- Login brute force
- Signup abuse
- AI generation abuse
- Tool execution abuse
- WebSocket connection abuse
- Per-user rate limit
- Per-tenant rate limit
- Per-IP rate limit
- API key rate limit
- Admin endpoint rate limit
- Rate limit storage failure behavior

Redis down হলে rate limiter fail-open নাকি fail-closed হবে সেটি স্পষ্ট সিদ্ধান্ত দরকার।

২৪. AI provider cost control যাচাই করতে হবে

AI platform হওয়ায় cost abuse বড় ঝুঁকি।

চেক করতে হবে:

- Per-user token budget
- Per-tenant token budget
- Daily/monthly spending limit
- Model fallback cost
- Retry cost
- Streaming cancellation
- Prompt size limit
- Tool loop limit
- Maximum agent steps
- Maximum execution time
- Provider timeout
- Provider circuit breaker
- Cost logging এবং alert

২৫. Prompt injection এবং tool abuse আরও পরীক্ষা করতে হবে

ToolPolicyGateway যোগ করা হয়েছে, তবে production adversarial testing আরও প্রয়োজন।

পরীক্ষা করতে হবে:

- Prompt injection
- Indirect prompt injection
- Malicious tool arguments
- SQL tool misuse
- File read/write escape
- SSRF
- Internal metadata access
- Unauthorized browser automation
- Cross-tenant tool execution
- Admin privilege escalation
- Tool result poisoning
- Memory poisoning
- RAG document injection

২৬. User-provided file এবং browser tool security পরীক্ষা করতে হবে

File এবং browser-related feature থাকায়:

- File size limit
- MIME validation
- Extension spoofing protection
- Malware scanning
- Path traversal prevention
- Temporary file cleanup
- SSRF protection
- Private IP block
- Internal hostname block
- Download timeout
- Browser sandbox
- Screenshot data retention
- User-to-user file isolation

নিশ্চিত করতে হবে।

২৭. Frontend-এ localStorage-নির্ভর sensitive state কমাতে হবে

Audit-এ frontend localStorage usage পাওয়া গেছে:

- Auth state
- Session history
- Fingerprint
- Dashboard session data

Sensitive token localStorage-এ রাখলে XSS হলে token চুরি হতে পারে।

সম্ভব হলে:

- HttpOnly Secure SameSite cookie ব্যবহার করতে হবে
- Session state server-side রাখতে হবে
- localStorage corruption হলে telemetry দিতে হবে
- পুরনো session safely migrate করতে হবে
- Logout-এ সব client state clear করতে হবে

২৮. Authentication secret configuration একীভূত করতে হবে

README-তে `SECRET_KEY` এবং `JWT_SECRET`-এর মতো পুরনো configuration দেখা যাচ্ছে, কিন্তু বর্তমান codebase-এ `SUPREMEAI_JWT_SECRET` ব্যবহৃত হচ্ছে।

এতে deployment confusion তৈরি হতে পারে।

করনীয়:

- একটি canonical secret নাম নির্ধারণ করুন
- পুরনো নাম remove বা explicit migration fallback দিন
- Startup validation যোগ করুন
- Weak/default secret reject করুন
- Secret length এবং entropy validation করুন
- Staging এবং Production secret আলাদা রাখুন

২৯. CORS এবং Trusted Origin production domain অনুযায়ী সীমাবদ্ধ করতে হবে

README-তে localhost origin রয়েছে, কিন্তু Production deployment-এর জন্য নিশ্চিত করতে হবে:

- Wildcard origin নেই
- Credentials সহ wildcard নেই
- Admin frontend আলাদা origin policy পায়
- WebSocket origin validation আছে
- Preview domain এবং Production domain intentional
- Unknown origin reject করা হচ্ছে

৩০. Security headers যোগ এবং যাচাই করতে হবে

Production deployment-এ baseline headers থাকা উচিত:

- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin
- Strict-Transport-Security
- Permissions-Policy
- X-Frame-Options, যদি embedding প্রয়োজন না থাকে
- Content-Security-Policy অথবা Report-Only CSP

বিশেষ করে Monaco editor, WebSocket, Firebase, Supabase এবং external AI endpoint থাকলে CSP carefully configure করতে হবে।

৩১. Observability production-ready করতে হবে

শুধু log থাকলেই observability সম্পূর্ণ হয় না।

প্রয়োজন:

- Centralized structured logging
- Request correlation ID
- Tenant-safe logging
- Error rate metrics
- Latency metrics
- Token usage metrics
- Provider failure metrics
- Database pool metrics
- Redis metrics
- Queue depth
- WebSocket count
- Memory/CPU metrics
- Alerting
- Sentry/OpenTelemetry verification
- PII redaction

৩২. Background task lifecycle যাচাই করতে হবে

Audit-এ background task এবং swallowed exception-এর ঝুঁকি আছে।

প্রতিটি background task:

- Reference ধরে রাখবে
- Exception log করবে
- Shutdown-এ cancel হবে
- Cancellation swallow করবে না
- Retry policy রাখবে
- Dead task metric পাঠাবে
- Duplicate worker prevent করবে

বিশেষ করে:

- AutoHealer
- Maintenance pipeline
- Queue worker
- Memory consolidation
- Config refresh
- Evolution controller
- Notification worker

৩৩. Graceful shutdown load test করতে হবে

SIGTERM handler যোগ করা হয়েছে, কিন্তু বাস্তবে পরীক্ষা দরকার।

চেক করতে হবে:

- Active AI request কীভাবে শেষ হয়
- Active WebSocket কীভাবে বন্ধ হয়
- Database connection release হয়
- Redis connection release হয়
- Queue message হারায় কিনা
- Background task cancel হয়
- Shutdown timeout কাজ করে
- Render restart-এর সময় duplicate execution হয় কিনা

৩৪. Single-worker architecture-এর capacity limit নির্ধারণ করতে হবে

বর্তমানে 512 MB constraint-এর কারণে worker count এক রাখা হয়েছে।

এতে:

- একটি worker crash করলে service unavailable হতে পারে
- CPU concurrency সীমিত হতে পারে
- Long AI request অন্য request block করতে পারে
- Background task ও API একই process-এ ঝুঁকি তৈরি করতে পারে

সিদ্ধান্ত নিতে হবে:

- API এবং worker আলাদা service হবে কিনা
- Queue-based background processing দরকার কিনা
- Render plan upgrade দরকার কিনা
- Horizontal scaling কীভাবে হবে
- Sticky WebSocket session দরকার কিনা

৩৫. Database connection pool tuning করতে হবে

চেক করতে হবে:

- Pool size
- Max overflow
- Pool timeout
- Connection recycle
- Idle timeout
- PgBouncer compatibility
- AsyncSession reuse
- Concurrent request behavior
- Read/write connection separation

একটি AsyncSession-এ concurrent `asyncio.gather()` চালানো যাবে না। এই ধরনের pattern পুরো codebase-এ search করতে হবে।

৩৬. Schema drift এবং bootstrap DDL কমাতে হবে

Boot-time `CREATE TABLE IF NOT EXISTS` দীর্ঘমেয়াদে migration system-এর বিকল্প হওয়া উচিত নয়।

বর্তমান bootstrap DDL শুধু stop-gap হিসেবে রাখা যেতে পারে। Long-term:

- Alembic migration একমাত্র schema authority হবে
- Boot-এ silent DDL বন্ধ করা উচিত
- Migration version record যাচাই করা উচিত
- Schema mismatch হলে service unhealthy করা উচিত

৩৭. Firebase এবং পুরনো Cloud Run dependency সম্পূর্ণ retire করতে হবে

Audit অনুযায়ী active architecture Render + PostgreSQL/Supabase হলেও Firebase এবং Cloud Run-এর কিছু legacy reference এখনও আছে।

চেক করতে হবে:

- Firestore tenant path
- Firebase admin
- Backup tooling
- Old deploy scripts
- Cloud Run rollback monitor
- Documentation
- CI deploy references
- Environment variables

যা আর দরকার নেই তা remove করতে হবে। যা রাখতে হবে তা architecture document-এ পরিষ্কারভাবে লিখতে হবে।

৩৮. API documentation বাস্তব endpoint-এর সাথে sync করতে হবে

README এবং OpenAPI documentation-এর মধ্যে drift হওয়ার ঝুঁকি আছে।

চেক করতে হবে:

- Authentication requirements
- Refresh endpoint
- HITL cancel endpoint
- WebSocket auth
- Admin-only endpoint
- Error response format
- Correlation ID
- Status codes
- Pagination
- Rate limit response
- 410 expired approval response

৩৯. Production data migration rollback পরিকল্পনা তৈরি করতে হবে

Migration fail বা নতুন schema incompatible হলে:

- কীভাবে rollback হবে
- Backup কোথায়
- Previous image compatible কিনা
- Forward-fix strategy কী
- Long-running migration কীভাবে হবে
- Lock এবং downtime কতটা হতে পারে

এসব লিখিত এবং tested হতে হবে।

৪০. Dependency update policy আরও কঠোর করতে হবে

Dependabot এবং pip-audit আছে, কিন্তু নিয়মিত review দরকার।

চেক করতে হবে:

- Python package vulnerability
- npm package vulnerability
- Transitive dependency
- License compliance
- React/Vite compatibility
- Firebase package size
- Monaco package security
- Playwright/browser dependency isolation
- Lockfile reproducibility
- Node এবং Python version consistency

৪১. Node/Python version mismatch ঠিক করতে হবে

Root package-এ Node >=24 বলা হয়েছে, README-তে Node 18+ বলা হয়েছে। Backend Python version নিয়েও README এবং runtime configuration-এর মধ্যে অসঙ্গতি আছে।

একটি canonical matrix দিতে হবে:

- Node version
- Python version
- pnpm version
- Poetry version
- PostgreSQL version
- Redis version
- Vite version
- React version

CI, Docker, README এবং deployment environment-এ একই version ব্যবহার করতে হবে।

৪২. Monorepo build এবং deploy boundary পরিষ্কার করতে হবে

Root package turbo monorepo ব্যবহার করছে, কিন্তু frontend আলাদা Vite application এবং backend Python application।

চেক করতে হবে:

- কোন package production-এ deploy হয়
- কোন workspace build required
- Build artifact কোথায়
- Frontend environment variables
- Backend environment variables
- Shared package versioning
- Workspace dependency build order
- Unused packages
- Admin এবং user build আলাদা deploy কিনা

৪৩. Frontend production build পরীক্ষা করতে হবে

দুই portal build করতে হবে:

- User portal
- Admin portal

চেক করতে হবে:

- Build সফল
- Runtime asset path সঠিক
- Base URL সঠিক
- API URL production-এর
- Source map policy সঠিক
- Chunk loading কাজ করে
- Refresh করলে SPA route ভাঙে না
- 404 fallback কাজ করে
- Admin route unauthorized হলে redirect করে

৪৪. Browser E2E test বাস্তব environment-এ চালাতে হবে

শুধু unit test যথেষ্ট নয়।

Critical E2E flow:

- Login
- Token refresh
- Logout
- Agent create
- Conversation
- Streaming response
- Memory save/recall
- Tool approval
- Approve/reject/cancel
- Admin dashboard
- WebSocket reconnect
- Markdown export
- File upload
- Error state
- Mobile layout

৪৫. Tenant isolation-এর database-level protection আরও শক্ত করতে হবে

Application-level user filtering যোগ করা হয়েছে, কিন্তু critical data-এর জন্য database-level protection বিবেচনা করা উচিত।

চেক করতে হবে:

- প্রতিটি query-তে tenant/user filter
- Admin bypass audit
- Background job tenant context
- Cache key tenant-scoped
- Vector search tenant-scoped
- Export history tenant-scoped
- WebSocket tenant-scoped
- API key tenant-scoped
- Logs tenant data leak করছে কিনা

৪৬. API key model-এর scope system তৈরি করতে হবে

বর্তমানে API key identification এবং rate-limit principal হিসেবে ব্যবহৃত হচ্ছে। Route authorization-এর জন্য ব্যবহার করলে per-key scope দরকার হবে।

যেমন:

- read:agents
- write:agents
- execute:tools
- read:memory
- admin:hitl

API key দিয়ে protected route চালু করার আগে scopes, expiry, revoke, rotation এবং audit যোগ করতে হবে।

৪৭. Admin access শক্ত করতে হবে

Admin endpoint-এর জন্য:

- MFA বা আরও শক্ত authentication বিবেচনা করুন
- Admin session timeout
- IP/device anomaly detection
- Privileged action approval
- Admin action audit
- Admin WebSocket authorization
- Break-glass account
- Emergency revoke ব্যবস্থা

শুধু role claim-এর ওপর অতিরিক্ত নির্ভর করা যাবে না।

৪৮. Load test এবং chaos test বাস্তবে চালাতে হবে

Production-like load testing দরকার:

- Concurrent users
- Concurrent AI requests
- Long streaming response
- WebSocket clients
- Database slowdown
- Redis unavailable
- AI provider timeout
- Supabase failure
- Memory pressure
- Queue backlog
- Restart during execution

Chaos test থাকলেও বাস্তব staging environment-এ চালিয়ে ফলাফল সংরক্ষণ করতে হবে।

৪৯. Cost monitoring এবং alerting চালু করতে হবে

AI platform হিসেবে প্রতি provider এবং প্রতি tenant-এর:

- Token usage
- Request count
- Model cost
- Retry cost
- Tool cost
- Storage cost
- Database usage

ট্র্যাক করতে হবে।

Budget threshold অতিক্রম হলে:

- Alert
- Soft limit
- Hard stop
- Admin notification
- Tenant notification

থাকা উচিত।

৫০. Incident response এবং rollback runbook তৈরি করতে হবে

Production incident হলে team-এর কাছে লিখিত runbook থাকতে হবে:

- Service down
- Database unavailable
- Redis unavailable
- AI provider outage
- Credential leak
- Cross-tenant data leak
- Tool abuse
- Memory exhaustion
- Bad self-evolution deployment
- Migration failure
- Rollback procedure
- Customer communication
- Evidence preservation

# ==================================================

বর্তমান অবস্থার সারাংশ

ভালো দিক:

- Cross-tenant isolation নিয়ে অনেক fix করা হয়েছে
- HITL state machine উন্নত করা হয়েছে
- Approval expiry, replay এবং tampering guard আছে
- Tool policy gateway যুক্ত হয়েছে
- Self-evolution live-file mutation বন্ধ করা হয়েছে
- Secret scanning CI-তে আছে
- Dependency scanning আছে
- Health routes আছে
- Lazy singleton conversion করা হয়েছে
- Production error response অনেক জায়গায় নিরাপদ করা হয়েছে
- Backend security test suite যথেষ্ট উন্নত হয়েছে

Production আটকাচ্ছে যেসব বিষয়:

১. সর্বশেষ code এখনও Render-এ redeploy করা হয়নি
২. SUPABASE_DATABASE_URL_WRITER সেট করা হয়নি
৩. Alembic migration deploy pipeline-এ properly wired নয়
৪. Health readiness নতুন deployment-এ পুনরায় যাচাই হয়নি
৫. Evolution forge-এ human approval এখনো সিদ্ধান্তাধীন
৬. বাস্তব canary traffic splitting নেই
৭. Render rollback automation অসম্পূর্ণ
৮. Docker production build সম্পূর্ণভাবে verified নয়
৯. CI coverage threshold codebase-এর দাবি অনুযায়ী যথেষ্ট কঠোর নয়
১০. Image signing এবং SBOM বাধ্যতামূলকভাবে enforced নয়
১১. HITL audit data durable append-only storage-এ নেই
১২. Silent error handling এখনও অনেক
১৩. Frontend authenticated WebSocket/API flow পুরোপুরি revalidated হয়নি
১৪. Memory capacity এখনও ঝুঁকিপূর্ণ
১৫. Backup restore drill বাস্তবে চালানো হয়নি
১৬. কিছু GitHub Actions full SHA-pinned নয়
১৭. পুরনো Firebase/Cloud Run architecture-এর residual dependency আছে

চূড়ান্ত সিদ্ধান্ত:

বর্তমান অবস্থা “security remediation completed” বলা যায়, কিন্তু “production ready” বলা যাবে না। Production launch-এর আগে কমপক্ষে P0 এবং P1 বিষয়গুলো সমাধান করতে হবে, বিশেষ করে Render redeploy, writable Supabase database URL, migration pipeline, health probe, evolution HITL approval, canary/rollback এবং full CI verification।
