# 🌐 SupremeAI 2.0 — Multi-Platform Deployment Architecture

**Last Updated:** 2026-07-24  
**Status:** ACTIVE PRODUCTION TOPOLOGY  

---

## 🏛️ Platform Roles & Responsibilities Matrix

To prevent configuration drift, resource duplication, and race conditions, each cloud platform serves a single, well-defined role:

| Platform | Primary Service Role | Base Domain / URL | Deployment Trigger | Key Responsibility |
|---|---|---|---|---|
| **Render Web Services** | Backend API & Microservices | `api.supremeai.io` / Render Blueprint | Push to `main` (`backend/`) | Runs FastAPI application (`SERVICE_ROLE=user` or `admin`), background workers, and Celery queues. |
| **Vercel Projects** | User Web Studio Client | `studio.supremeai.io` | Push to `main` (`apps/studio-client/`) | Primary high-performance React 19 / Vite 7 user web application & Electron bundle host. |
| **Firebase Hosting** | Admin God-Mode Portal | `admin.supremeai.io` | GitHub Actions workflow | Serves isolated React Admin Dashboard with Firebase Auth & App Check enforcement. |
| **Cloudflare CDN** | Edge Caching & WAF Shield | `*.supremeai.io` | Auto DNS & Proxy Rules | DDoS protection, SSL termination, and static asset caching. (Worker logic bypass mode). |
| **Infisical Cloud** | Centralized Secret Management | `app.infisical.com` | Automated via `python scripts/sync_all_platforms_env.py` | Single Source of Truth for API keys, DB credentials, and secrets. Syncs real-time across all platforms. |

---

## 🔄 Real-Time Multi-Platform Secret Synchronization Flow

Whenever any secret in `.env` or Infisical is modified:

```
                  ┌────────────────────────┐
                  │ Centralized Vault      │
                  │ (.env / Infisical)     │
                  └───────────┬────────────┘
                              │
             python scripts/sync_all_platforms_env.py
                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ Render API   │       │ Vercel CLI   │       │ GitHub       │
│ Environment  │       │ Environment  │       │ Secrets      │
└──────────────┘       └──────────────┘       └──────────────┘
```

1. Run `python scripts/sync_all_platforms_env.py`.
2. The script parses active credentials from `.env` and propagates them via API to Render, Vercel, and GitHub Actions Secrets simultaneously.
3. Every deployment across all platforms operates on 100% identical, validated environment variables.

---

## 🚀 Continuous Deployment Flow (GitHub Actions)

Workflow file: `.github/workflows/monorepo_ci_cd.yml`

1. **Change Detection:** `dorny/paths-filter` checks modified paths:
   - `backend/**` → Triggers Pytest suite & Render Web Hook.
   - `apps/studio-client/**` → Triggers Vercel build & Electron VSIX artifact creation.
   - `apps/mobile/**` → Triggers Flutter analyzer & build test.
2. **Backend Verification:** `poetry run pytest` must pass 100%.
3. **Deployment Execution:** Platform webhooks deploy cleanly without zero-downtime interruption.

---

_SupremeAI 2.0 Architectural Documentation_
