# 🧠 Learning Brain System Specification (Implemented)

> **Status:** ✅ Fully Implemented (2026-07-26)  
> **Location:** `backend/brain/smart_router.py`, `backend/brain/supreme_learning_engine.py`, `backend/core/llm/llm_gateway_with_learning.py`

---

## 1. Executive Summary

The **Learning Brain System** introduces a self-learning loop to SupremeAI 2.0 ("Steal the Brain, Not the Body"). It observes external AI provider responses, extracts reasoning chains and patterns into an internal SQLite Pattern DB and JSON Knowledge Graph, and independently answers repetitive queries locally with zero API cost.

---

## 2. Technical Implementation Details

### A. Smart Router (`backend/brain/smart_router.py`)
- **Routing Decision Engine (`SelfSovereignRouter`):**
  - **Tier Allocation:**
    - `local` (0$ cost): Runs local open models like Ollama (`llama3.1:70b`, `deepseek-coder:33b`, `qwen2.5:32b`).
    - `managed` ($0.09/1M tokens): Fast APIs (Groq, DeepSeek API, Gemini 2.5 Flash).
    - `frontier` ($5.00/1M tokens): Powerful models (GPT-4o, Claude 3.5 Sonnet).
  - **Complexity Score Algorithm:** Evaluates input prompt token counts and predefined keyword arrays to assign a difficulty class (`simple`, `medium`, `complex`, `extreme`).
    - Simple queries bypass external APIs entirely and target local or cached engines first.

### B. Supreme Learning Engine (`backend/brain/supreme_learning_engine.py`)
- **Storage Layer:**
  - **SQLite Database (`patterns.db`):** Stored under `data/patterns.db`. Contains a schema with columns for `id`, `prompt_hash`, `prompt_pattern`, `response_payload`, `confidence_score`, `success_count`, and `failure_count`.
  - **Knowledge Graph (`knowledge_graph.json`):** Tracks conceptual entity relationships extracted from successful solution cycles to enable structured local lookups.
- **Pattern Learning Algorithm:**
  - When external providers return responses, the prompt-response pair is passed to `learn_pattern(prompt, response)`.
  - **Bengali Logic Mapping:**
    ```python
    # নতুন লার্নিং প্যাটার্ন মেমরিতে সেভ করার মেকানিজম
    # SQL কুয়েরির মাধ্যমে চেক করা হয় যে প্যাটার্নটি ইতিমধ্যে ডেটাবেসে আছে কি না
    ```
- **Local Generation Threshold:**
  - If a incoming prompt matches a recorded pattern with a confidence score $\ge 0.75$ (calculated using Jaro-Winkler string distance and ratio of success to failure counts), the engine returns the cached response locally, bypassing external LLM APIs.

### C. LLM Gateway wrapper (`backend/core/llm/llm_gateway_with_learning.py`)
- **Drop-in replacement for `LLMRouter`:**
  - Intercepts completion invocations inside the FastAPI request lifecycles.
  - Returns `[SupremeAI Brain]` cached responses when confidence is sufficient ($\ge 0.75$).
  - Otherwise, delegates execution to `LLMRouter`, captures the output, and schedules asynchronous learning tasks.

---

## 3. Verification & Tests

Executed from the backend root using:
```bash
poetry run pytest tests/test_learning_brain.py
```
Tests assert database record insertions, Jaro-Winkler confidence matching thresholds, entity extraction to `knowledge_graph.json`, and wrapper interception.
