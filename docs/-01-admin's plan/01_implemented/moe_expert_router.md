# 🔀 MoE Expert Router Specification (Implemented)

> **Status:** ✅ Fully Implemented (2026-07-26)  
> **Location:** `backend/brain/expert_router.py`, `backend/core/llm_router.py`

---

## 1. Executive Summary

The **SupremeMoERouter** (Mixture of Experts Router) inspects prompt domain characteristics and directs generation requests to specialized model chains with automatic fallback.

---

## 2. Supported Expert Domains

| Expert Type | Triggers & Identifiers | Primary & Fallback Model Chain |
|-------------|-----------------------|--------------------------------|
| `BENGALI` | Bengali Unicode range (`U+0980`–`U+09FF`), Banglish keywords (`kemon`, `acho`, `ki`, `apni`) | `hf_space/supreme-hybrid-8b` → `groq/llama-3.3-70b-versatile` → `gemini/gemini-2.5-flash` |
| `CODER` | Code blocks, keywords (`def`, `class`, `import`, `docker`, `function`) | `deepseek/deepseek-coder` → `groq/qwen-2.5-coder-32b` → `openai/gpt-4o` |
| `REASONER` | Logic, math, theorem, calculation keywords | `deepseek/deepseek-chat` → `groq/deepseek-r1-distill-llama-70b` → `gemini/gemini-2.5-pro` |
| `GENERAL` | Standard conversational queries | `gemini/gemini-2.5-flash` → `groq/llama-3.1-8b-instant` → `openai/gpt-4o-mini` |

---

## 3. Verification & Tests

Unit test suite available at `backend/tests/test_expert_router.py`.
