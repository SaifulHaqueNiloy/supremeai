# SupremeAI Full Checking System Replan — 111-Trap Coverage Matrix

## লক্ষ্য (Goal)
`ERROR_AND_MISMATCH_COMPENDIUM.md`-এ থাকা **১১১টি failure trap**-এর প্রতিটি কোন automated gate-এ ধরা পড়বে তার সম্পূর্ণ ম্যাপিং।

---

## ৩-স্তরের Gate Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: Pre-Commit Hooks  (লোকাল, <5s, commit-block)         │
│  LAYER 2: CI Pipeline       (GitHub Actions, PR/push gate)      │
│  LAYER 3: Nightly/Scheduled (রাত ৩টা UTC, non-blocking audit)   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Coverage Matrix — ১১১টি Trap

### Layer 1: Pre-Commit (বর্তমান hooks + নতুন gaps)

| Trap # | বিষয় | বর্তমান Hook | Gap? |
|--------|------|-------------|------|
| **#১** | Missing `await` (Silent Coroutine) | ❌ নেই (Ruff config-এ ASYNC নেই) | **GAP** |
| **#৩** | Mutable Default Arguments | ✅ Ruff `B006` | — |
| **#৪** | Silent Exception Swallowing | ✅ `observability-audit` hook | — |
| **#৫** | In-Memory Leak (Global Dict) | ❌ নেই | **GAP** |
| **#৫২** | SQL Injection via Raw SQL | ✅ `supremeai-blindspot-scan` | — |
| **#৫৫** | XSS in AI Markdown | ❌ নেই | **GAP** |
| **#৫৮** | Secret Leakage in Code | ✅ `secret-hunter`, `detect-private-key` | — |
| **#৫৯** | Sensitive Data Logging | ✅ `observability-audit` | — |
| **#৬২** | Field Name/Casing Mismatch | ✅ `api-contract-check` (pre-push) | — |
| **#৬৩** | FastAPI Nested Prefix Bug | ✅ `router-smoke-test` | — |
| **#৬৪** | Unmounted Router | ✅ `router-smoke-test` | — |
| **#৭৪** | React EventBus Leak | ❌ নেই | **GAP** |
| **#৮৩** | String "false" vs Bool | ❌ নেই | **GAP** |
| **#৮৭** | Lockfile Desync | ✅ `check-toml` / `check-json` (partial) | Partial |
| **#১০৫** | Import-Time Side Effect | ❌ নেই | **GAP** |
| **#১০৬** | Singleton Re-Init | ❌ নেই | **GAP** |
| **#১১০** | Dev/Prod ENV Collapse | ❌ নেই | **GAP** |

**Pre-commit-এ যোগ করতে হবে (৫টি নতুন hook):**
1. `import-budget-check` — `python -c "import <module>"` < 5s gate
2. `env-mode-guard` — `ENV=production` লোকালে থাকলে block
3. `singleton-init-counter` — `SkillManager initialized` > 1 হলে warn
4. `react-cleanup-audit` — `useEffect` without `return` + subscriber pattern
5. `truthy-env-checker` — `== "true"` without `.lower()` pattern detect

*(Note: #95 Unpinned Actions is covered in L2)*

---

### Layer 2: CI Pipeline — বিদ্যমান Jobs এবং তাদের Coverage

#### Job: `security` (Trivy + TruffleHog)
| Trap # | কভার করে |
|--------|----------|
| **#৫৮** | Secret leakage in git commits |
| **#৯৮** | SBOM generation (partial) |

#### Job: `advanced-checks` (Pre-Merge Gate)
| Trap # | Script | কভার করে |
|--------|--------|----------|
| **#৩১** | `db_model_drift_checker.py` | Migration drift |
| **#৩২** | `migration_safety_diff.py` | Destructive Migration |
| **#৩৩** | `db_model_drift_checker.py` | Schema constraint mismatch |
| **#৫৩** | `regression_scanner.py` | CORS Wildcard + Credentials |
| **#৫০** | `regression_scanner.py` | JWT verification bypass |
| **#৫৬** | `regression_scanner.py` | Path traversal |
| **#৬২,৬৩,৬৭,৭১,৭২,৭৩** | `api_contract_diff.py` | API field/type mismatches |
| **#৬৪** | `orphan_route_finder.py` | Unmounted routers |
| **#৬৫** | `api_contract_diff.py` | SSE protocol check |
| **#৮৩,৮৮** | `env_var_reconciler.py` | Config drift |
| **#৯৪** | `validate_workflow_contracts.py` | Actions Permissions check |
| **#৯৫** | `validate_workflow_contracts.py` | GitHub Actions SHA-pinning |
| **#৯৬** | `check_frontend_secrets.py` | Secret in frontend bundle |
| **#১০৭,১০৮,১০৯** | `api_contract_diff.py` | Transport/payload drift |

**❌ CI advanced-checks-এ যা নেই (Gap analysis):**

| Trap # | বিষয় | প্রস্তাবিত স্ক্রিপ্ট |
|--------|------|------------------|
| **#২** | Blocking Event Loop in async route | `blocking_call_detector.py` |
| **#৯** | Cross-tenant retrieval leak | `rls_policy_auditor.py` |
| **#১০** | Retrieval Authorization Bypass | `rls_policy_auditor.py` |
| **#১১** | Tool Privilege Escalation | `tool_permission_auditor.py` |
| **#১২** | Tool Result Injection | Unit tests / Static analysis |
| **#১৩** | SSRF (Server-Side Request Forgery) | `ssrf_detector.py` / Security lint |
| **#১৪** | Sensitive Data Exfiltration | `data_exfiltration_auditor.py` |
| **#১৫** | Unbounded Agent Loop | `agent_loop_limiter_check.py` |
| **#১৭** | Unvalidated Structured LLM Output | Unit tests (pytest) |
| **#২৬-২৮** | DB Transaction/Pool issues | `db_session_auditor.py` |
| **#২৯** | N+1 Query | `n_plus_one_detector.py` |
| **#৩৬** | Unbounded Query | Static Query Auditor |
| **#৩৭** | Missing Commit | Transaction Logic Check |
| **#৩৮** | Race Condition in Balance | Integration tests |
| **#৩৯-৪৫** | Queue/Worker traps (inc #43 Visibility) | Worker integration tests |
| **#৪৭,৪৮,৪৯** | AuthN/AuthZ, BOLA/IDOR | `bola_idor_detector.py` |
| **#৫১** | JWT Refresh Race | Frontend unit tests |
| **#৫৪** | CSRF Token Missing | Middleware config check |
| **#৫৭** | Unsafe Upload | `upload_security_checker.py` |
| **#৬০** | Brute Force / Rate Limit missing | `rate_limit_endpoint_checker.py` |
| **#৬১** | Missing Security Headers | `security_headers_checker.py` |
| **#৬৬** | WS Auth Protocol Mismatch | Contract test |
| **#৬৮** | HTTP 204 JSON crash | Frontend test |
| **#৬৯** | FormData parsing crash | Payload contract check |
| **#৭০** | Trailing Slash Mismatch | Router path audit |
| **#৭৫-৭৭** | Stale closure, Race condition | Frontend unit tests |
| **#৮১** | Missing React Error Boundaries | ESLint rule / component scan |
| **#৮২** | LocalStorage token exposure | `frontend_security_auditor.py` |
| **#৮৪** | Timezone / Date Drift | Date function usage check |
| **#৮৫** | Cache Key Collision | Redis key pattern checker |
| **#৮৬** | Unverified Webhook Signature | `webhook_signature_checker.py` |
| **#৮৯** | Migration vs App Deploy Order | Deployment gate |
| **#৯০** | Deploy Drift | Manifest audit |
| **#৯১,৯২** | Health Check false positive | `/ready` deep check test |
| **#৯৭** | Docker running as root | Dockerfile `USER` check |
| **#৯৯,১০০** | Correlation ID / Tracing gap | `observability_gap_checker.py` |
| **#১০১** | High-cardinality metrics bomb | Metrics label auditor |
| **#১১১** | Dry-run masquerading as success | Boot audit script |

---

### Layer 3: Nightly/Scheduled (বর্তমান + নতুন gaps)

#### বিদ্যমান `scheduled-deep-audit.yml` (রাত ৩টা UTC)
| Trap # | Step | কভার করে |
|--------|------|----------|
| **#৪,৫৯** | Duplicate Logic Detector | duplicate/dead code |
| **#৫৮** | Auto Vulnerability Scanner | secret/CVE |
| **#৯৮** | SBOM generation | supply chain |
| **#২৯,৩০** | Performance Benchmark | N+1, slow query |

#### বিদ্যমান `maintenance.yml` (রাত ২টা UTC)
| Trap # | Job | কভার করে |
|--------|-----|----------|
| **#৩১** | DB Schema Check | migration drift |
| **#৮৮** | Health Check | env drift detection |
| **#৬,৭,৮,২০** | MLOps Nightly Eval | Prompt injection, embedding drift |

**❌ Nightly-তে যা নেই (সবচেয়ে বড় gaps):**

| Trap # | বিষয় | প্রস্তাবিত Job |
|--------|------|--------------|
| **#৮,২১** | Memory poisoning + GDPR delete | `ai_memory_integrity_audit.py` |
| **#২০** | Embedding model drift | `embedding_drift_detector.py` |
| **#২৩** | Ephemeral vector store | `vector_store_persistence_check.py` |
| **#২৮** | Connection pool exhaustion | `db_pool_health_monitor.py` |
| **#৩০** | Missing index / full table scans | `slow_query_detector.py` |
| **#৩৪** | FK Cascade disaster | `fk_cascade_auditor.py` |
| **#৩৫** | RLS policy correctness | `rls_policy_auditor.py` |
| **#৪১** | Retry storm / no backoff | `retry_pattern_checker.py` |
| **#৪২** | Poison message / Missing DLQ | `queue_health_checker.py` |
| **#৮৫** | Cache key collision | `redis_key_pattern_auditor.py` |
| **#৯৩** | Missing automatic rollback | `rollback_policy_checker.py` |
| **#১০০** | Distributed tracing gap | `otel_coverage_checker.py` |
| **#১০১** | High-cardinality metrics bomb | `metrics_cardinality_auditor.py` |
| **#১০২** | Logging without sampling | `log_volume_analyzer.py` |
| **#১০৩** | No cost telemetry | `llm_cost_projector.py` |
| **#১০৪** | Symptom-only alerting | `alert_coverage_checker.py` |
| **#১০৫** | Import-time side effects | `import_budget_auditor.py` |
| **#১০৬** | Singleton re-init | `singleton_init_counter.py` |
| **#১১১** | Dry-run masquerading | `storage_client_health_audit.py` |

---

## Final Coverage Summary (Corrected)

| Gate | Trap Count | বর্তমান কভারেজ | পরে কভারেজ |
|------|-----------|---------------|-----------|
| L1 Pre-Commit | ~20 | 11/20 (55%) | **17/20 (85%)** |
| L2 CI Pipeline | ~70 | 25/70 (35%) | **50/70 (71%)** |
| L3 Nightly | ~35 | 12/35 (34%) | **30/35 (86%)** |
| Manual Only | ~10 | 10/10 | 10/10 (Manual audit) |
| **মোট** | **111** | **~40% কভার** | **~75% কভার** |

> [!IMPORTANT]
> **Manual Audit Required:** কিছু ট্র্যাপ স্বয়ংক্রিয়ভাবে ধরা অত্যন্ত কঠিন এবং এগুলোর জন্য **সর্বদা manual audit বা human review প্রয়োজন**:
> - **#৭:** Indirect Injection from Live PDF
> - **#৮:** Memory Poisoning Attack Simulation
> - **#১৮:** Model Capability & Safety Mismatch
> - **#১৯:** Fallback Semantic & Context Loss
> - **#২২:** Hallucinated Tool Success
> - **#২৫:** Context Window Overflow / Edge Cases
> - **#৭৮:** Optimistic UI rollback UX issues
> - **#৮৬:** Live Webhook HMAC test
> - **#৯৩:** Production Rollback Drill
> 
> *AI Agent safety এবং Model capability-র মতো বিষয়গুলো সম্পূর্ণ automate করা বাস্তবসম্মত নয়।*

---

## Rollout Strategy & Tuning (গুরুত্বপূর্ণ)

বিশাল সংখ্যক নতুন চেক হুট করে প্রোডাকশনে হার্ড-ব্লকিং গেট হিসেবে চালু করা ঝুঁকিপূর্ণ। 
1. **Audit Mode (প্রথম ১-২ সপ্তাহ):** L1 এবং L2-এর নতুন কাস্টম স্ক্রিপ্টগুলো (`bola_idor_detector.py`, `blocking_call_detector.py` ইত্যাদি) শুরুতে `continue-on-error: true` বা অডিট মোডে রান করা হবে। এগুলো শুধু লগ তৈরি করবে, বিল্ড বা কমিট ফেইল করাবে না (Pre-commit-এর ক্ষেত্রেও ওয়ার্নিং দেওয়া হবে)।
2. **Defensive Tuning:** এই ১-২ সপ্তাহে লগ বিশ্লেষণ করে ফলস পজিটিভ (False Positives) দূর করতে স্ক্রিপ্টগুলোকে ডিফেন্সিভলি টিউন করা হবে।
3. **Hard-Blocking Gate:** ডেটা কালেকশন সন্তোষজনক হলে এবং ফলস পজিটিভ শূন্যের কোঠায় নেমে এলে গ্র্যাজুয়ালি এগুলোকে ব্লকিং গেটে রূপান্তর করা হবে।
