# CI Fix Plan - Progress Tracker

## Problem 1: HuggingFaceSpaceProvider TypeError (CRITICAL) ✅
- [x] Fix `backend/core/llm_router.py` - Add type safety in HuggingFaceSpaceProvider.__init__()
- [x] Fix `backend/tests/test_cross_provider_consistency.py` - Replace MagicMock with specific attribute patches

## Problem 2: ImportError - google.genai ✅
- [x] Fix `backend/skills/core_knowledge_qa.py` - Add try/except fallback for google import
- [x] Fix `backend/skills/core_doc_summarizer.py` - Add try/except fallback for google import
- [x] `backend/agents/morphic_adapter.py` - Already has proper try/except fallback

## Problem 3: Admin Token JWSSignatureError
- [ ] Fix admin token test - Ensure consistent JWT secret usage

## Verification
- [ ] Run tests locally to verify fixes
