# Security Policy

## 📋 Overview

SupremeAI 2.0 implements a multi-layered security architecture designed around the **AutonoGuard Engine**, providing enterprise-grade protection while maintaining zero operating cost.

*Last Updated: 2026-07-20 (Phase 0 Hardening Completed)*

---

## 🔐 Core Security Principles

### 1. JIT OTP Enforcement (Just-In-Time One-Time Password)
All sensitive operations require OTP verification through:
- **SHA-256 hash-based storage** (plaintext never stored)
- **Masked admin_id** in all logs (3 visible characters)
- **Timing-safe comparison** via `secrets.compare_digest`
- **Free-tier delivery** via Discord webhook or Resend email

### 2. IP Churn Detection (Malware Immunity)
- **Redis-backed IP tracking** with 1-hour TTL
- **Threshold:** >5 different IPs in 1 hour triggers OTP re-verification
- **Blocks:** Automated attacks attempting to bypass security via IP rotation

### 3. Zero Silent Failures
- **ErrorEvent bus** emits structured events on ALL code paths
- **Circuit breaker** pattern prevents cascade failures
- **Fail-Closed** for security-critical operations (production/staging)

### 4. AST Security Scanning
- **Blocked functions:** `eval`, `exec`, `compile`, `getattr`, `hasattr`, `setattr`, `delattr`, `open`, `__import__`
- **Blocked attributes:** `__class__`, `__bases__`, `__subclasses__`, `__globals__`, `__builtins__`, `__dict__`, `__mro__`, `__code__`, `__closure__`
- **Sandbox escape prevention** via chained attribute/subscript validation

---

## 🛡️ Security Controls Matrix

| Layer | Component | Implementation | File |
|-------|-----------|---------------|------|
| **Authentication** | JWT-based auth | `backend/core/auth.py` | Token validation, HTTPOnly cookies |
| **Authorization** | Role-based access | `backend/core/admin_god.py` | God Mode enforcement |
| **Rate Limiting** | Redis-backed | `backend/core/rate_limiter.py` | Fail-Closed + fallback |
| **OTP** | JIT verification | `backend/core/otp_router.py` | SHA-256 hash storage |
| **IP Protection** | Churn detection | `backend/core/autonoguard_engine.py` | Redis hgetall tracking |
| **Code Security** | AST scanning | `backend/core/immune_system.py` | Sandbox escape prevention |
| **Remediation** | Self-healing | `backend/core/error_remediation.py` | Qdrant vector search |
| **Audit Trail** | Event bus | `backend/core/messaging/event_bus.py` | Structured ErrorEvent emission |

---

## 📡 Protected Endpoints

The following endpoints require AutonoGuard OTP enforcement:

| Path Pattern | Protection Level |
|--------------|------------------|
| `/api/v1/admin/*` | 🔴 High — Full admin access |
| `/api/v1/billing/*` | 🔴 High — Payment operations |
| `/api/v1/orchestrate/*` | 🔴 High — Agent orchestration |
| `/api/v1/skills/execute` | 🟠 Medium — Code execution |
| `/api/v1/system/*` | 🟠 Medium — System operations |

---

## 🚨 Vulnerability Reporting

If you discover a security vulnerability within SupremeAI 2.0, please report it immediately to the security team.

**Contact Methods:**
1. Email: `security@supremeai.dev`
2. GitHub Security Advisory (preferred for non-critical issues)
3. For critical vulnerabilities: Include reproduction steps and impact assessment

**What We Look For:**
- Authentication/authorization bypass
- SSRF/RCE vulnerabilities
- IDOR (Insecure Direct Object Reference)
- SQL injection or NoSQL injection
- Rate limit bypass attempts
- AutonoGuard enforcement bypass

**Response SLA:** 24 hours for critical, 72 hours for high-severity issues.

---

## 🔒 Production Security Configuration

### Cookie Security
```python
# Production-only settings
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
```

### Rate Limit Configuration
```python
# Per-tier limits
RATE_LIMIT_GEMINI_RPM = 9
RATE_LIMIT_GROQ_RPM = 28
RATE_LIMIT_OPENROUTER_RPM = 19
```

### OTP Configuration
```python
OTP_COOLDOWN_SECONDS = 300  # 5 minutes between OTP requests
ANTI_HACKING_ENABLED = True  # IP churn detection active
```

---

## 🛠️ Security Development Guidelines

### For AI Agents & Contributors

1. **Never hardcode secrets** — Use environment variables or Secret Manager
2. **Always emit ErrorEvent** — No silent failure paths allowed
3. **Use Fail-Closed** — Security ops must fail safely in production
4. **Validate all inputs** — AST scan before code execution
5. **Check IP churn** — Before sensitive operations, call `detect_ip_churn()`
6. **Timing-safe comparisons** — Use `secrets.compare_digest()` for secrets
7. **Mask sensitive data** — Use `_mask(value, visible=3)` in logs

### Code Review Checklist

- [ ] No hardcoded credentials
- [ ] All security paths emit ErrorEvent
- [ ] Rate limiting implemented for public endpoints
- [ ] OTP required for admin operations
- [ ] AST scanning applied to generated code
- [ ] Circuit breaker used for external calls
- [ ] Redis operations have fallbacks
- [ ] Production-safe error messages (no stack traces)

---

## 📊 Security Audit History

| Date | Auditor | Findings | Status |
|------|---------|----------|--------|
| 2026-07-08 | AutonoGuard Architect | Zero-Cost & Production Lockdown | ✅ Passed |
| 2026-07-18 | Cyber Security Team | 13 Critical/High/Medium | ✅ Remediated |
| 2026-07-20 | Principal Architect | Phase 0 Hardening | ✅ Verified |

---

*This security policy is enforced by the AutonoGuard Engine — Any violation triggers automatic security alerts and OTP re-verification.*
