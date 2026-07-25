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

## 3. Remaining Tasks & Technical Specifications

### A. Google Colab Mergekit Pipeline (`scripts/colab_merge_pipeline.py`)
- **GPU Resource Requirement:** Google Colab Free Tier (Tesla T4 GPU with 16GB VRAM) or Google Colab Pro.
- **Merge Configuration (YAML Schema):**
  - **Method:** `ties` (TIES-Merging is optimized for merging specialized LoRAs without degrading base capabilities).
  - **Base Model:** `meta-llama/Meta-Llama-3-8B-Instruct`
  - **Adapters:**
    - `bengali-lora-adapter` (Weight: 0.4)
    - `coder-lora-adapter` (Weight: 0.4)
    - `math-logic-adapter` (Weight: 0.2)
- **Bengali Pipeline Logic Comments:**
  ```python
  # গুগল কোলাব-এ মার্জকিট স্ক্রিপ্ট রান করার লুপ
  # মডেল মার্জ করার পর সেটিকে HuggingFace হাব-এ আপলোড করার অটোমেটেড পুশ লজিক
  ```

### B. HuggingFace Space Host Container (`apps/hf-space/`)
- **Quantization:** Quantize the merged model to 4-bit (`Q4_K_M` GGUF format) using `llama.cpp` to fit within HuggingFace Space RAM limits.
- **Hosting Spec:** Deploy a containerized backend (`llama-cpp-python` server or vLLM) to Hugging Face Free CPU Space (16GB RAM limit).
- **Fallback Integration:** If the HuggingFace Space encounters a sleep timeout or cold-start latency, the `LLMRouter` automatically falls back to Groq API.

---

## 🔍 Codebase Audit (2026-07-26)

### What Already Exists (Better Than Planned)

| Component | Code Location | Why It's Better |
|-----------|--------------|-----------------|
| **LLM Router (5 providers)** | `backend/core/llm_router.py` | Significantly more advanced than planned: supports 5 providers (Moonshot, DeepSeek V3, Together AI, Gemini, Ollama), 7 task types, cost-sensitive routing, circuit breakers, Redis caching, token budget enforcement, Bengali normalizer with Banglish→Bengali transliteration, SSE streaming with mid-stream fallback, Prometheus metrics |
| **MoE Expert Router** | `backend/brain/expert_router.py` | Already classifies prompts into BENGALI, CODER, REASONER, GENERAL with appropriate model chains — integrates with LLM Router via `SupremeMoERouter.get_model_chain()` |
| **Fallback Chain System** | `backend/core/llm_router.py` | Built-in fallback chains per task type with cost-sensitive sorting — more sophisticated than the planned single HF Space → Groq fallback |

### What Still Needs Work

| Missing Piece | Why Needed | Effort |
|--------------|------------|--------|
| `scripts/colab_merge_pipeline.py` | Google Colab script to run Mergekit TIES merging | 2 days |
| `apps/hf-space/Dockerfile` | HuggingFace Space container for merged model | 2 days |
| Add HF Space as provider in LLM Router | Minor update to add new provider entry | 0.5 day |

### Recommendation
The existing `LLMRouter` already has a sophisticated multi-provider routing system with fallback chains, circuit breakers, and cost optimization. The Mergekit pipeline should focus on model merging only — the routing infrastructure is already superior to what was originally planned. When adding the HF Space, simply register it as a new provider in the existing router rather than building a separate fallback system.
