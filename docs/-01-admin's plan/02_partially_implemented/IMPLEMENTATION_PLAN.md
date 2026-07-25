# 📋 Implementation Plan — Partially Implemented Features

> **Scope:** `docs/-01-admin's plan/02_partially_implemented/`  
> **Created:** 2026-07-26  
> **Goal:** Complete all pending remaining tasks across partially implemented features.

---

## 🔴 Pending Items Summary

| Feature | Completed | Remaining |
|---------|-----------|-----------|
| Slicing & Combined AI Model | MoE Expert Router ✅ | Mergekit Pipeline, HF Space |
| Advanced System Enhancement | Pillars 1,2,3,5 ✅ | Pillar 4: NATS Type Sync Bus |

---

## 📌 Plan 1: Slicing & Combined AI Model — Mergekit Pipeline

### Phase 1: Prepare Model Merge Configuration
- **File:** `scripts/colab_merge_pipeline.py` (CREATE NEW)
- **Task:** Write Mergekit-compatible YAML config for TIES merging.
  - Base Model: `meta-llama/Meta-Llama-3-8B-Instruct`
  - Bengali LoRA Adapter: weight `0.4`
  - Coder LoRA Adapter: weight `0.4`
  - Math-Logic Adapter: weight `0.2`
- **Library:** `pip install mergekit` (Google Colab T4 GPU)

### Phase 2: GGUF Quantization
- Run `llama.cpp` quantization on the merged model:
  ```bash
  python llama.cpp/convert.py merged_model/ --outtype q4_k_m --outfile merged-supreme-8b-q4.gguf
  ```
- Target format: `Q4_K_M` (fits within HuggingFace 16GB RAM limit)

### Phase 3: HuggingFace Space Deployment
- **Directory:** `apps/hf-space/` (CREATE NEW)
- Create a `Dockerfile` using `ghcr.io/huggingface/text-generation-inference` base image.
- Configure model serving endpoint compatible with `LLMRouter` API schema.
- **Fallback Strategy:** On HuggingFace cold-start, `LLMRouter` auto-falls back to `groq/llama-3.3-70b-versatile`.

### Phase 4: Router Integration Update
- **File:** `backend/core/llm_router.py` (MODIFY)
- Add `hf_space/supreme-hybrid-8b` provider entry pointing to HuggingFace Space URL.
- Set timeout thresholds (5s) and cold-start detection handling.

### Verification Steps
```bash
# ১. হাগিং ফেস স্পেস হেলথ চেক
curl https://huggingface.co/spaces/{space-id}/api/health

# ২. রাউটার ইন্টিগ্রেশন টেস্ট
poetry run pytest tests/test_expert_router.py -k "test_hf_space"
```

---

## 📌 Plan 2: Advanced System Enhancement — NATS/Redis Type Sync Bus

### Phase 1: Shared Types Package Setup
- **Directory:** `packages/shared-types/` (CREATE NEW)
  ```
  packages/shared-types/
  ├── src/
  │   ├── typescript/        # Generated TypeScript .d.ts files
  │   └── dart/              # Generated Dart model files
  ├── generate_types.py      # Generation script
  └── package.json
  ```

### Phase 2: Pydantic → TypeScript Generator Script
- **File:** `scripts/generate_types.py` (CREATE NEW)
- Inspect all Pydantic models under `backend/core/schemas/` using Python reflection.
- Export TypeScript interfaces (e.g. `interface ChatRequest { ... }`) to `packages/shared-types/src/typescript/`.
- Export Dart classes (e.g. `class ChatRequest { ... }`) to `packages/shared-types/src/dart/`.

### Phase 3: NATS JetStream Event Bus
- **File:** `backend/core/type_sync_bus.py` (CREATE NEW)
- Subscribe to `types.sync` and `types.drift_detected` NATS channels.
- Publishes schema change events whenever Pydantic models are modified.
- Frontend and Flutter clients subscribe and trigger type regeneration automatically.

### Phase 4: CI/CD Pipeline Hook
- **File:** `.github/workflows/monorepo_ci_cd.yml` (MODIFY)
- Add step to run `python scripts/generate_types.py` on every backend schema change via `paths-filter`.

### Verification Steps
```bash
# ১. টাইপ জেনারেশন রান করা
python scripts/generate_types.py

# ২. আউটপুট ফাইল পরীক্ষা করা
ls packages/shared-types/src/typescript/
ls packages/shared-types/src/dart/

# ৩. টাইপ ড্রিফট টেস্ট
poetry run pytest tests/test_type_sync_bus.py
```
