# SupremeAI Kaggle 6-Node Cluster Architecture & Guide

> **Compute Matrix:** 6 Kaggle Accounts $\times$ 30 GPU Hours = **180 GPU Hours / Week** ($0 Cost Cloud Supercomputer)

---

## 1. Overview & Core Purpose

This guide outlines the operations of SupremeAI's Kaggle 6-Node Cluster. Rather than attempting brittle 24/7 web hosting on temporary kernels, this cluster acts as an **Offline High-Throughput Brain & Quality Forge**:

1. **Vector Fabric Engine:** Ingests the entire codebase and docs into Supabase `ai_memory` (pgvector).
2. **Brain Distillation Forge:** Pre-computes code patches and error resolutions into Cloudflare KV for sub-5ms lookups.
3. **Weekend Self-Healer:** Runs deep static analysis, automated linting, test synthesis, and generates GitHub PRs.

---

## 2. Setting Up Kaggle Account Credentials

1. Go to [kaggle.com](https://www.kaggle.com) and log in to each account (1 through 6).
2. Navigate to **Account Settings** $\to$ **API** $\to$ Click **"Create New Token"**.
3. A file named `kaggle.json` will download containing:
   ```json
   {"username":"your_username","key":"your_api_key"}
   ```
4. Add these 6 credentials into your SupremeAI root `.env` or Infisical Vault:

```env
# ── Kaggle 6-Node Pool ──────────────────────────────────────────────
KAGGLE_USER_1=account1_username
KAGGLE_KEY_1=account1_api_key

KAGGLE_USER_2=account2_username
KAGGLE_KEY_2=account2_api_key

KAGGLE_USER_3=account3_username
KAGGLE_KEY_3=account3_api_key

KAGGLE_USER_4=account4_username
KAGGLE_KEY_4=account4_api_key

KAGGLE_USER_5=account5_username
KAGGLE_KEY_5=account5_api_key

KAGGLE_USER_6=account6_username
KAGGLE_KEY_6=account6_api_key
```

---

## 3. CLI Orchestration Commands

### Check Cluster Status & Quotas
```bash
python scripts/kaggle/pipeline_orchestrator.py --status
```

### Validate Authentication for All 6 Nodes
```bash
python scripts/kaggle/pipeline_orchestrator.py --check-auth
```

### Run Pipeline Stages

#### Dry Run (Validates configuration without pushing to Kaggle)
```bash
python scripts/kaggle/pipeline_orchestrator.py --stage vector_fabric --dry-run
```

#### Run Phase 1: Vector Fabric Engine
```bash
python scripts/kaggle/pipeline_orchestrator.py --stage vector_fabric
```

#### Run Phase 2: Brain Distillation Forge
```bash
python scripts/kaggle/pipeline_orchestrator.py --stage brain_distillation
```

#### Run Phase 3: Weekend Self-Healer
```bash
python scripts/kaggle/pipeline_orchestrator.py --stage weekend_self_healer
```

---

## 4. Architecture & State Management

- **Quota Tracking:** Stored in `scripts/kaggle/artifacts/cluster_state.json`. Usage resets automatically every 7 days (Sunday 00:00 UTC).
- **Failover Logic:** If a node encounters an auth error or exceeds its 30-hour limit, the `AccountPoolRotator` automatically selects the next healthy node in the pool.
