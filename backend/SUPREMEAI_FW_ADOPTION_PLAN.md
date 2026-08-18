# Open-Source Framework Adoption Plan

> **Status:** Analyzed against current codebase — 3 of 5 tools already implemented.
> **Date:** 2026-08-18
> **Context:** Building on the [Needle 2 architectural adoption plan](session:digest:ses_fee3321a7ffe2NLiF4f5s66iGP) and the existing integrations layer (`backend/integrations/`)

---

## Executive Summary

After deep-diving every referenced file, **3 of the 5 proposed tools are already implemented** — often in a superior, $0-cost form. The remaining 2 are either already partially present or represent genuine gaps with concrete implementation plans below.

### Quick Reference

| Tool | Already Implemented? | Where | Action Needed |
|------|---------------------|-------|---------------|
| **RouteLLM** | **FULLY** — Tier 0 confidence-gated fast-path | `core/llm/advanced_model_router.py` | Enhance complexity scoring accuracy (incremental) |
| **Outlines** | **NO** — JSON parsing has zero fallback | `core/skill_manager.py:203`, `services/llm/providers.py:163` | **IMPLEMENT** — zero-dependency constrained JSON decoder |
| **Mem0** | **FULLY** — optional-dependency adapter with fallback | `integrations/mem0_adapter.py` | None (already wired + tested) |
| **smolagents** | **FOLLOWED** — lightweight, no framework bloat | `src/agents/syncguard/`, `core/llm/llm_gateway.py` | None (design philosophy already match) |
| **Letta** | **PARTIALLY** — layered memory via unified_memory.py | `core/unified_memory.py` | Enhance checkpoint resume flow (incremental) |

---

## Detailed Analysis

### 1. RouteLLM — Already Implemented (Enhancement Opportunity)

**Current implementation** in `core/llm/advanced_model_router.py`:

- **Tier 0 Fast-Path** (lines 36–131): `_DETERMINISTIC_PATTERNS` regex matching runs *before* any LLM call, executing pure-stdlib tasks (PyPI search, file listing, text formatting, schema lookup) at **zero token cost**.
- **Confidence gate** (line 331–373): `route_with_confidence()` returns `ConfidenceDecision` with `is_deterministic` flag — bypasses LLM entirely when confidence ≥ 0.85.
- **Integrated** into `llm_gateway.py:446`: The gateway calls `route_with_confidence()` and returns Tier 0 results without any litellm call.
- **Routing policy** in `config/routing_policy.json`: complexity_rules (easy/medium/hard) → model selection.
- **Free-tier tracking** in `free_tier_tracker.py`: 85% predictive thresholds, per-provider RPM/TPM/RPD windows.

**Analysis:** The core RouteLLM concept — *complexity matrix + tiered routing + cost avoidance* — is fully present. The gap is sophistication: RouteLLM uses lightweight ML models to predict routing, whereas our current implementation uses keyword counting. This is acceptable for a $0-cost architecture.

**What's beneficial to add (Phase 1):**
- Extend `_DETERMINISTIC_PATTERNS` with more patterns (regex extraction, URL parsing, simple calculations)
- Add a lightweight scoring model: combine FreeTierTracker availability + latency data from `provider_router.py` into the confidence score in `route_with_confidence()`
- No external dependency needed — RouteLLM itself is heavy; our current implementation is lighter

### 2. Outlines — REAL GAP (Implement)

**Current state** in `core/skill_manager.py:161-208`:

```python
# Line 196-208: raw JSON parse, no fallback
raw_text = response.get("text", "{}").strip()
if raw_text.startswith("```"):
    lines = raw_text.splitlines()
    raw_text = "\n".join(lines[1:-1] if ...)
try:
    new_skill = json.loads(raw_text)  # Can throw — no retry, no recovery
    return new_skill
except Exception as e:
    raise ValueError("Invalid JSON configuration from Skill Factory.")
```

**Gap analysis:**
- No constrained decoding / guided generation
- No JSON schema validation on LLM output
- No graceful recovery from malformed JSON
- `providers.py:163` uses `json_mode` flag but no schema enforcement
- `skill_manager.py` has dead code at line 199: the codeblock stripping logic is broken (checks `lines.startswith` but `lines` is a list, not string)

**Implementation plan — zero-dependency constrained JSON decoder:**

Since the $0-cost philosophy forbids adding heavy dependencies like `outlines` (which requires `torch`/`transformers`), we build a **lightweight constrained JSON decoder** using only stdlib + existing patterns:

| Phase | File | Change |
|-------|------|--------|
| P1 | `core/llm/constrained_decoder.py` (NEW) | Create `ConstrainedJSONDecoder` with: (a) regex repair for common LLM JSON errors, (b) schema-aware validation via `jsonschema` (or manual type checks), (c) retry loop with corrective prompts |
| P1 | `core/skill_manager.py:196-208` | Replace raw `json.loads` with `ConstrainedJSONDecoder.decode_with_schema(raw_text, schema_dict)` |
| P1 | `services/llm/providers.py:90` | Add `json_schema` kwarg support in provider payloads |
| P1 | `tests/llm/test_constrained_decoder.py` (NEW) | Unit tests: malformed JSON repair, schema validation, nested object handling, Bengali text in JSON values |

**Design:** Follow the existing `integrations/` adapter pattern — zero-dependency, graceful fallback. If `jsonschema` is available (it's likely already a transitive dep), use it; otherwise use runtime type introspection.

### 3. Mem0 — Already Integrated

**Current implementation** in `integrations/mem0_adapter.py`:
- Full `Mem0MemoryAdapter` with optional dependency loading
- Zero-cost fallback: bag-of-words cosine similarity + keyword ranking
- Feature-flagged via `SUPREMEAI_MEM0_ENABLED` (env-first, DB-fallback pattern in `feature_flags.py`)
- Tested in `test_integrations_adapters.py:20-54`

**Analysis:** This is a complete, production-ready integration. No additional work needed.

### 4. smolagents — Already Followed (Design Philosophy Match)

**Current state:**
- Uses `litellm` directly — no LangChain, no AutoGen, no heavy abstraction layers
- `syncguard_agent.py` is 94 lines, uses `unified_memory` directly, no framework wrappers
- `pyproject.toml` has no agent framework dependencies
- `llm_gateway.py` handles all provider routing directly with per-call API key passing (security best practice)

**Analysis:** The codebase already embodies the smolagents philosophy of minimalist, code-first agents. Adding smolagents itself would introduce framework overhead that contradicts our $0-cost principle.

### 5. Letta — Partially Implemented (Enhancement Opportunity)

**Current implementation** in `core/unified_memory.py`:
- **Short-term memory** (`SlidingWindowMemory`): sliding window context with hierarchical compaction, token budgeting
- **Long-term memory** (`CascadeMemoryService`): pgvector-backed Eternal Brain with semantic search
- **Checkpoint manager** (`CheckpointManager`): task state persistence with write-behind batching

**Analysis:** This maps directly to Letta's architecture:
- SlidingWindowMemory = Core Context (RAM-equivalent, managed window)
- CascadeMemoryService = Archival Memory (Disk-equivalent, persistent recall)
- CheckpointManager = Task state persistence (resume flow)

**What's beneficial to add (Phase 2):**
- Explicit `pause()` / `resume()` API in `UnifiedMemoryInterface` that loads checkpoint state + rebuilds sliding window context
- Memory eviction policy (Letta's "archival" pattern) — move old sliding-window entries to CascadeMemoryService
- Currently, `unified_memory.py:44-45` has placeholder summary/structure — connect it to `memory_service._parse_code_structure()`

---

## Implementation Roadmap

### Phase 1: Outlines (Critical — 2-3 days)

```
1. core/llm/constrained_decoder.py   — NEW: ConstrainedJSONDecoder class
2. tests/llm/test_constrained_decoder.py — NEW: 8-10 test cases
3. core/skill_manager.py             — EDIT: lines 196-208, use constrained decoder
4. services/llm/providers.py         — EDIT: add json_schema kwarg passthrough
5. core/llm/__init__.py              — EDIT: export ConstrainedJSONDecoder
```

**Step 1:** Create `ConstrainedJSONDecoder` with:
- `repair_json(raw_text)` → fixes trailing commas, missing brackets, codeblock wrapping
- `validate_json(data, schema)` → runtime type checking (no external dep) or `jsonschema` if available
- `decode_with_schema(raw_text, schema, max_retries=2)` → retry loop with corrective re-prompt

**Step 2:** Wire into `skill_manager.py:synthesize_skill_schema()` — replace the broken codeblock stripping (line 197-200) and raw `json.loads` (line 203) with the constrained decoder.

**Step 3:** Add `json_schema` passthrough in `providers.py` so all providers support `response_format: {"type": "json_schema", "json_schema": {...}}` when available (OpenAI/Groq support this natively).

**Step 4:** Unit tests covering: malformed JSON, missing brackets, trailing commas, codeblocks with language tags, Bengali unicode in JSON values, nested skill schema validation.

### Phase 2: RouteLLM Enhancement (1-2 days)

```
1. core/llm/advanced_model_router.py — EDIT: enhance route_with_confidence()
2. tests/llm/test_advanced_model_router.py — EDIT: add complexity scoring tests
```

- Add 3-4 new Tier 0 patterns: URL parsing, simple math, regex extraction
- Integrate FreeTierTracker availability into `calculate_model_score()` — deprioritize rate-limited providers
- Add latency data from `provider_router.py` ProviderStats into scoring

### Phase 3: Letta Enhancement (2 days)

```
1. core/unified_memory.py          — EDIT: add pause/resume API
2. core/unified_memory.py          — EDIT: wire _parse_code_structure into store_long_term_memory
3. tests/                          — NEW: test checkpoint resume flow
```

- Add `pause(task_id)` → save sliding window snapshot + checkpoint
- Add `resume(task_id)` → load checkpoint + rebuild context window
- Wire real summary/structure extraction (currently placeholder at lines 44-45)

### Phase 4: Cognee Integration (if needed — 1 day)

Graphiti adapter already exists. Cognee adds ECL (Extract, Cognify, Load) pipeline. This is **optional** — the Graphiti adapter at `integrations/graphiti_adapter.py` already provides temporal knowledge graph with `add_episode()` + `search()`. Only implement if multi-hop logical retrieval is needed beyond what Graphiti provides.

---

## Risk Assessment

| Tool | Risk | Mitigation |
|------|------|------------|
| Outlines implementation | Low — zero-dependency, wraps existing json.loads | Feature-flag: `SUPREMEAI_CONSTRAINED_JSON_ENABLED` (default True, fallback to raw json.loads) |
| RouteLLM enhancement | Low — additive scoring | Preserve existing `analyze_prompt_complexity()` API; new logic only boosts scores |
| Letta enhancement | Low — new methods on facade | All new methods are additive; existing callers unaffected |
| smolagents adoption | N/A — already followed | No action taken; adding it would regress $0-cost principle |

## Files to Modify

### Directly (Phase 1 — highest priority):
1. **`core/llm/constrained_decoder.py`** (NEW)
2. **`core/skill_manager.py`** (EDIT lines 196-208)
3. **`services/llm/providers.py`** (EDIT line 90)
4. **`tests/llm/test_constrained_decoder.py`** (NEW)
5. **`core/llm/__init__.py`** (EDIT — export)
