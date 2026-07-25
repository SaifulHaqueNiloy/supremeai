# 📡 Future Roadmap Phase 7: Theory of Mind (Not Implemented)

> **Status:** 🔴 Not Implemented (Future Roadmap Phase 7)  
> **Priority:** P2 | **Complexity:** Very High | **Risk:** High

---

## 1. Overview

Implements Theory of Mind (ToM) capabilities in AI agents, enabling them to model and reason about the mental states, beliefs, and intentions of users and other agents.

---

## 2. Technical Blueprint & Proposed Architecture

### A. ToM Modeling (`backend/evolution/theory_of_mind/model.py`)
- Belief state tracking for users and agents.
- Intent recognition and prediction.

### B. Integration with Agent Reasoning
- ToM-aware decision making for more natural interactions.
- User modeling for personalized responses.

---

## 🔍 Codebase Audit (2026-07-26)

### Status: 🔴 Truly Not Implemented

No files found under `backend/evolution/theory_of_mind/`. This is genuinely new research work.

### What Already Exists (Related Infrastructure)

| Component | Code Location | How It Helps |
|-----------|--------------|--------------|
| **Evolution Engine** | `backend/core/evolution_engine.py` | Can integrate ToM into agent decision-making |
| **Memory Store** | `backend/memory/supabase_store.py` | Can store user belief states and interaction history |
| **LLM Router** | `backend/core/llm_router.py` | Can route ToM-related queries to appropriate models |

### Recommendation
This is genuinely new research work. The memory store can serve as the foundation for tracking user beliefs and interaction history over time.
