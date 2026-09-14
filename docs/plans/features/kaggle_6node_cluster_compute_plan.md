# Implementation Plan: Supreme-Kaggle 6-Node Cluster (180 GPU Hours/Week)

This updated plan details the design and deployment of the **Supreme-Kaggle 6-Node Cluster Ring**, orchestrating 6 Kaggle accounts to unlock **180 GPU hours per week** (surpassing the 168 hours in a week). This provides SupremeAI with a **24/7 non-stop, zero-downtime, $0-cost cloud AI compute engine** that combines real-time streaming inference with our Hybrid "Supreme-Forge" background processing matrix.

---

## User Review Required

> [!IMPORTANT]
> **Credential Setup:** You will configure 6 Kaggle API credentials (`kaggle_1.json` to `kaggle_6.json` or environment variables `KAGGLE_USER_1`/`KAGGLE_KEY_1` ... `KAGGLE_USER_6`/`KAGGLE_KEY_6`). These are managed through our secure `.env` / Infisical Vault.

> [!TIP]
> **Zero Downtime 12-Hour Session Handoff:** Kaggle kernels automatically restart after 12 hours. The `account_pool_rotator.py` engine pre-warms the next account 5 minutes prior to session expiry, switching the Cloudflare Tunnel endpoint seamlessly without dropping active requests.

---

## 180-Hour Weekly Allocation Architecture

```
                                  [SupremeAI Master Orchestrator]
                                   (scripts/kaggle/pipeline_orchestrator.py)
                                                │
       ┌───────────────────────────┬────────────┴──────────────┬───────────────────────────┐
       ▼                           ▼                           ▼                           ▼
 [Tier 1: 24/7 Live Relay]  [Tier 2: Deep Vector Fabric] [Tier 3: Brain Distillation]  [Tier 4: Weekend Burst]
     (84 GPU Hours)              (24 GPU Hours)              (36 GPU Hours)              (36 GPU Hours)
 - Continuous vLLM Server    - AST Codebase Parser       - Pre-computed Patch Cache  - 3-Node Parallel Burst
 - Cloudflare Tunnel Wire    - Multi-Doc RAG Embeddings  - Synthetic Q&A Matrix      - Fuzz & Test Suite PR
       │                           │                           │                           │
       ▼                           ▼                           ▼                           ▼
 [Real-time AI Chat/Code]    [Supabase pgvector]         [Cloudflare KV / D1]        [GitHub Automated PR]
```

### Allocation Breakdown (Total: 180 GPU Hours):
| Tier | Function | Schedule | GPU Hours Allocated | Target System |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Live Inference Relay** | 24/7 Private LLM Server (vLLM/Ollama) | 12-hr continuous rotation (Mon–Sun) | **84 Hours** | Live Extension / Backend Chat |
| **Tier 2: Deep Vector Fabric** | Codebase AST Parsing & RAG Embeddings | Daily Nightly Runs (2 hrs x 7 days + 10 hr deep) | **24 Hours** | Supabase `ai_memory` (pgvector) |
| **Tier 3: Brain Distillation** | Pre-computed Solution & Error Patch Cache | Mon–Wed Batch Pipeline | **36 Hours** | Cloudflare KV / D1 (Sub-5ms) |
| **Tier 4: Weekend Self-Healer** | 3-Node Parallel Burst Refactoring & Testing | Fri night – Sun morning | **36 Hours** | Automated GitHub PR & Tests |
| **Total** | | | **180 Hours** | **100% Weekly GPU Utilization** |

---

## Proposed Changes

### Component 1: Multi-Account Management & Rotation (`scripts/kaggle/`)

#### [NEW] [account_pool_rotator.py](file:///f:/supremeai%20backup/scripts/kaggle/account_pool_rotator.py)
- Manages the pool of 6 Kaggle credentials.
- Tracks quota usage (hours consumed vs remaining per account).
- Provides graceful handoff and health-checking across accounts.

#### [NEW] [kaggle_config.py](file:///f:/supremeai%20backup/scripts/kaggle/kaggle_config.py)
- Centralized configuration schema for accounts, GPU hardware targets (Nvidia T4 x2), storage endpoints (Supabase, Cloudflare KV, R2), and notification hooks.

#### [NEW] [pipeline_orchestrator.py](file:///f:/supremeai%20backup/scripts/kaggle/pipeline_orchestrator.py)
- Master command-line orchestrator with support for:
  - `--mode live-relay` (Spins up continuous 24/7 inference server)
  - `--mode vector-fabric` (Triggers Tier 2 embedding ingestion)
  - `--mode distillation` (Runs Tier 3 synthetic patch generation)
  - `--mode weekend-burst` (Launches 3-node parallel testing & refactoring)
  - `--mode status` (Real-time cluster dashboard showing all 6 accounts)

---

### Component 2: Kaggle Cluster Notebooks (`scripts/kaggle/notebooks/`)

#### [NEW] [node_live_inference_tunnel.ipynb](file:///f:/supremeai%20backup/scripts/kaggle/notebooks/node_live_inference_tunnel.ipynb)
- Fast vLLM / llama.cpp inference server paired with Cloudflare Quick Tunnel / Named Tunnel to route real-time OpenAI-compatible streaming API requests directly to SupremeAI backend.

#### [NEW] [node_vector_fabric.ipynb](file:///f:/supremeai%20backup/scripts/kaggle/notebooks/node_vector_fabric.ipynb)
- High-throughput GPU embedding generation using `BGE-large` / `nomic-embed-text` pushing vectors directly into Supabase pgvector.

#### [NEW] [node_brain_distillation.ipynb](file:///f:/supremeai%20backup/scripts/kaggle/notebooks/node_brain_distillation.ipynb)
- Automated distillation engine generating pre-computed code patches, refactors, and error resolutions pushed into Cloudflare KV.

#### [NEW] [node_weekend_self_healer.ipynb](file:///f:/supremeai%20backup/scripts/kaggle/notebooks/node_weekend_self_healer.ipynb)
- Multi-threaded code analyzer, security scanner, and automated test builder creating full GitHub PRs.

---

### Component 3: Documentation & Registry

#### [NEW] [docs/KAGGLE_6_NODE_CLUSTER_GUIDE.md](file:///f:/supremeai%20backup/docs/KAGGLE_6_NODE_CLUSTER_GUIDE.md)
- Step-by-step setup guide for generating the 6 API tokens, configuring secrets, managing tunnels, and monitoring the cluster.

#### [MODIFY] [scripts/_INDEX.md](file:///f:/supremeai%20backup/scripts/_INDEX.md)
- Register `scripts/kaggle/` modules and orchestration commands in the master script index.

---

## Verification Plan

### Automated Tests
1. **Cluster Auth Validation:**
   ```bash
   python scripts/kaggle/pipeline_orchestrator.py --check-all-accounts
   ```
   - Verifies all 6 Kaggle account keys are valid and queries active GPU quotas.

2. **Zero-Cost Dry Run:**
   ```bash
   python scripts/kaggle/pipeline_orchestrator.py --dry-run
   ```
   - Validates kernel metadata JSONs, environment variables, and tunnel bindings without consuming GPU minutes.

3. **Canary Session Handoff Simulation:**
   - Tests pre-warming and simulated handoff between Account 1 and Account 2.

### Manual Verification
- Verify Cloudflare Tunnel health status in SupremeAI backend.
- Test sub-5ms lookup latency on distilled KV cache items.
