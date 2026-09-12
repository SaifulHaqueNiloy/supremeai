# Section 11 capability implementation

This delivery implements the provider-neutral Priority-A foundations from the capability wishlist without adding integrations, credentials, local-machine execution, or vendor hardcoding.

## Delivered

- `backend/tools/knowledge/citation_store.py`: tenant-scoped structured citations with URL validation and confidence bounds. The in-process adapter is intentionally replaceable by the platform's approved durable store.
- `backend/brain/research_harness.py`: bounded planner/scout/judge orchestration with per-scout timeouts and graceful degradation.
- `backend/core/llm/structured_output_router.py`: JSON parsing with bounded repair attempts and a stable validation boundary.
- `backend/core/memory/auto_rag_injector.py`: opt-in tenant-scoped context injection; disabled by default to preserve user control.
- `backend/api/routes/section11_capabilities.py`: API surface for citations and structured-output validation.

## Remaining manual production tasks

1. Connect `CitationStore` to the approved tenant-scoped durable database and add retention/RLS policies.
2. Wire `AutoRAGInjector` to the existing memory adapter only after user opt-in and consent UI are available.
3. Connect `ResearchHarness` scouts and judge to the governed model/tool router; keep budgets and approvals server-side.
4. Add adversarial prompt-injection fixtures and run them in CI against every remote-tool definition.
5. Add live provider/MCP fixtures before claiming benchmark or production reliability results.

No provider credentials or integrations are required for the code-level implementation and tests.
