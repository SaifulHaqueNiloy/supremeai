# 📖 SupremeAI 2.0 — Developer Guide

**Status:** OFFICIAL PRODUCTION DEVELOPER MANUAL  
**Language:** Dual (English + বাংলা)  
**Last Updated:** 2026-07-24  

---

## 🚀 Quick Start / দ্রুত শুরু করার নির্দেশিকা

### 1. Environment Bootstrap / এনভায়রনমেন্ট বুটস্ট্র্যাপ
Run the bootstrap script to verify system dependencies, Python Poetry environment, and Node pnpm modules:

```bash
# Core bootstrap
python scripts/bootstrap_env.py
```

### 2. Multi-Cloud Secret Sync / সিক্রেট সিঙ্ক্রোনাইজেশন
Always ensure your `.env` secrets are synchronized across Render, Vercel, and GitHub Actions:

```bash
# Real-time multi-platform sync
python scripts/sync_all_platforms_env.py
```

---

## 🛠️ Development Workflow / ডেভেলপমেন্ট ওয়ার্কফ্লো

### Backend Dev Server (FastAPI)
```bash
# Start FastAPI backend (Port 8000)
pnpm backend:dev
```

### Web Studio Client Dev Server (React/Vite)
```bash
# Start Web Studio Client (Port 5173)
cd apps/studio-client
pnpm dev
```

### Mobile App (Flutter)
```bash
# Run Flutter app in debug mode
cd apps/mobile
flutter run
```

---

## 🧪 Testing & Verification / টেস্টিং ও যাচাইকরণ

```bash
# Run backend pytest suite
pnpm backend:test

# Run targeted unit tests
poetry run pytest tests/api/test_admin.py tests/api/test_swarm_routes.py tests/test_circuit_breaker.py
```

---

## 🏛️ Core Architecture Checklist

- [x] Zero-Cost Optimization (Always utilize free-tier providers: DeepSeek-V3, Kimi K2.5, Together AI)
- [x] JIT OTP Security Shield (Enforced on sensitive endpoints: `/billing`, `/admin`, `/payments`)
- [x] Correlation ID Tracing (`logger.contextualize(correlation_id=...)`)
- [x] Single CircuitBreaker (`core.resilience.CircuitBreaker`)

---

_SupremeAI 2.0 Engineering Team_
