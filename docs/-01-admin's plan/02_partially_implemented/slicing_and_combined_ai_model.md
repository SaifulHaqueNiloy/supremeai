# ⚖️ Slicing & Combined AI Model Blueprint (Partially Implemented)

> **Status:** 🟡 Partially Implemented (2026-07-26)  
> **Completed:** MoE Expert Router (`backend/brain/expert_router.py`)  
> **Remaining:** Google Colab Mergekit slicing pipeline & HuggingFace Space host container (`apps/hf-space/`)

---

## 1. Overview

Combines specialized model weights (Bengali language + Coder + Logic) into a single hybrid 8B model using `Mergekit` (TIES/DARE/SLERP method) and routes traffic using the MoE Expert Router.

---

## 2. Completed Components

- ✅ **MoE Expert Router (`backend/brain/expert_router.py`):** Classified prompts into `BENGALI`, `CODER`, `REASONER`, and `GENERAL` with appropriate model chains.

---

## 3. Remaining Tasks

- ⏳ **Colab Mergekit Pipeline:** Run `scripts/colab_merge_pipeline.py` on Google Colab T4 GPU to merge `Llama-3-8B` with Bengali & Coder LoRA adapters.
- ⏳ **HuggingFace Space Hosting (`apps/hf-space/`):** Deploy quantized `.gguf` file to Hugging Face free 16GB RAM CPU Space.
