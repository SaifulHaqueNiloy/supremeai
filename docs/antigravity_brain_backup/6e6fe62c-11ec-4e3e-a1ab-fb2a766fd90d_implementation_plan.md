# 🔌 Connecting 5 Custom Hugging Face Models to SupremeAI 2.0

Overview of steps required to connect your 5 newly created Hugging Face models (`njelitltd/supreme-reasoner-3b`, `njelit1/supreme-coder-3b`, `ziaulhaq1/supreme-general-3b`, `njelitltd2/supreme-creative-3b`, `njelitltd3/supreme-master-3b`) into the SupremeAI 2.0 Smart Router and LLM Gateway.

---

## 🎯 Architectural Overview

```
                                               [User Request]
                                                      │
                                                      ▼
                                       ┌───────────────────────────────┐
                                       │   backend/core/llm_router.py  │
                                       │      (Task Classifier)        │
                                       └──────────────┬────────────────┘
                                                      │
         ┌───────────────────┬────────────────────────┼────────────────────────┬───────────────────┐
         │ (Coding Task)     │ (Logic/Math Task)      │ (General/Bengali)      │ (Creative Task)   │ (Master Task)
         ▼                   ▼                        ▼                        ▼                   ▼
┌─────────────────┐ ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐ ┌─────────────────┐
│  njelit1/       │ │  njelitltd/     │      │  ziaulhaq1/     │      │  njelitltd2/    │ │  njelitltd3/    │
│ supreme-coder   │ │ supreme-reasoner│      │ supreme-general │      │ supreme-creative│ │ supreme-master  │
└─────────────────┘ └─────────────────┘      └─────────────────┘      └─────────────────┘ └─────────────────┘
```

---

## 🛠️ Step-by-Step Action Plan

### Step 1: Model Serverless Inference API / Space Deployment
Ensure the models are accessible via Hugging Face Inference API or HF Spaces:
1. **Serverless Inference API (Default Zero-Cost):** Uses HF Router endpoints (`https://api-inference.huggingface.co/models/{model_id}`).
2. **Dedicated HF Space / vLLM Endpoint (Optional High-Performance):** Deploy GGUF/Safetensors on an HF Space or local Ollama/vLLM runner for low-latency streaming.

### Step 2: Register Models in `backend/core/llm_router.py` & Model Registry
Map task classifications directly to the 5 models with key round-robin rotation across the 5 HF API keys:
- **Coding / Technical:** `njelit1/supreme-coder-3b`
- **Math / Reasoning:** `njelitltd/supreme-reasoner-3b`
- **General / Multi-turn:** `ziaulhaq1/supreme-general-3b`
- **Creative / Content:** `njelitltd2/supreme-creative-3b`
- **Master Orchestration:** `njelitltd3/supreme-master-3b`

### Step 3: Implement HF Key Rotation Helper
Since 5 HF keys are stored in `HF_API_KEY` in `.env` as comma-separated values, implement automatic round-robin key selection in `HFInferenceProvider` to distribute load and quota across all 5 accounts (`njelitltd`, `njelit1`, `ziaulhaq1`, `njelitltd2`, `njelitltd3`).

---

## Proposed Changes

### `backend/core/llm_router.py`
#### [MODIFY] [llm_router.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/llm_router.py)
- Register `HUGGINGFACE_SWARM` provider and model endpoints.
- Add task routing mapping for the 5 3B models.

### `backend/core/config.py`
#### [MODIFY] [config.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/config.py)
- Parse comma-separated `HF_API_KEY` into a list of keys for round-robin rotation.

---

## Verification Plan

### Automated Tests
- Run `pytest backend/tests/test_task_router.py` to ensure task classification correctly routes to the assigned HF 3B model.
- Test key rotation and provider fallback behavior.

### Manual Verification
- Execute test prompt requests for Coding, Reasoning, Creative, and General domains via backend API endpoints.
