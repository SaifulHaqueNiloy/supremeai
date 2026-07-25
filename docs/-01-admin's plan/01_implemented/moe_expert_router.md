# 🔀 MoE Expert Router Specification (Implemented)

> **Status:** ✅ Fully Implemented (2026-07-26)  
> **Location:** `backend/brain/expert_router.py`, `backend/core/llm_router.py`

---

## 1. Executive Summary

The **SupremeMoERouter** (Mixture of Experts Router) inspects prompt domain characteristics and directs generation requests to specialized model chains with automatic fallback.

---

## 2. Technical Implementation Details

### A. Expert Router Architecture (`backend/brain/expert_router.py`)
- **Domain Classifier:** Matches prompts against 4 specialized categories using character boundaries, regex, and syntactic heuristics:
  - **`BENGALI`:**
    - **Trigger Heuristics:** Bengali Unicode block detection range (`U+0980`–`U+09FF`) and Banglish keyword matcher arrays (e.g. `kemon`, `acho`, `ki`, `apni`, `dhonnobad`).
    - **Routing Chain:** `hf_space/supreme-hybrid-8b` $\rightarrow$ `groq/llama-3.3-70b-versatile` $\rightarrow$ `gemini/gemini-2.5-flash` (auto-fallback).
  - **`CODER`:**
    - **Trigger Heuristics:** Code fence patterns (triple backticks), syntax identifiers (`def `, `class `, `import `, `async def`, `const `, `import React`), and language extensions.
    - **Routing Chain:** `deepseek/deepseek-coder` $\rightarrow$ `groq/qwen-2.5-coder-32b` $\rightarrow$ `openai/gpt-4o`.
  - **`REASONER`:**
    - **Trigger Heuristics:** Logic proofs, math symbols, theorem declarations, calculation keywords (`calculate`, `solve`, `evaluate`, `prove`, `why`).
    - **Routing Chain:** `deepseek/deepseek-chat` (DeepSeek-R1 Distill) $\rightarrow$ `groq/deepseek-r1-distill-llama-70b` $\rightarrow$ `gemini/gemini-2.5-pro`.
  - **`GENERAL`:**
    - **Trigger Heuristics:** Standard general-purpose conversation.
    - **Routing Chain:** `gemini/gemini-2.5-flash` $\rightarrow$ `groq/llama-3.1-8b-instant` $\rightarrow$ `openai/gpt-4o-mini`.

- **Bengali Logic Comments:**
  ```python
  # ব্যবহারকারীর প্রম্পট কোন ডোমেইনের সাথে মিলে তা নির্ধারণ করার লজিক
  # ইউনিকোড রেঞ্জ দিয়ে সরাসরি বাংলা হরফ শনাক্ত করা হয়
  ```

### B. LLM Router Integration (`backend/core/llm_router.py`)
- The class method `LLMGateway.async_generate` accepts `use_moe: bool = False`.
- When set to `True`, the router calls `classify_prompt(prompt)` to select the optimal model pipeline.
- Integrates with the backend resilience circuit breaker to automatically hop to the fallback provider chain on token limits or server outages.

---

## 3. Verification & Tests

Executed from the backend root using:
```bash
poetry run pytest tests/test_expert_router.py
```
Tests verify Unicode Bengali recognition, code segment classification, math query extraction, and the fallback routing pipelines.
