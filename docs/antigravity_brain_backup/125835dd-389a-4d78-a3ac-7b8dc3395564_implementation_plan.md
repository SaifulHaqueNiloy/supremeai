# Achieve 100% Green Test Suite (Fix 26 Remaining Failures)

The 3 architectural bugs requested are 100% fixed and green. However, running the entire test suite `poetry run pytest` reveals 26 other pre-existing failures across several modules that prevent the pipeline from succeeding. 

To strictly enforce the rule: "Pushing code to production is strictly prohibited until the test suite is 100% green," this plan outlines the fixes for the remaining failures.

## Open Questions
- None. These are all standard testing and mocking bugs. 

## Proposed Changes

---

### `tests/test_llm_gateway.py` & `tests/test_llm_gateway_coverage.py`
**Issue:** `litellm.acompletion` is raising `AuthenticationError` in full test runs due to global state pollution of API keys from other tests, and `test_stream_completion_falls_back` is failing due to incorrect mocking.
- **[MODIFY]** `backend/tests/test_llm_gateway.py`
  - Refactor `patch("litellm.acompletion")` to properly isolate the `AsyncMock` to avoid `litellm` state pollution across tests.
  - Fix `test_stream_completion_falls_back` to correctly simulate `litellm.acompletion` throwing an exception on the first call and succeeding on the fallback call.
- **[MODIFY]** `backend/tests/test_llm_gateway_coverage.py`
  - Apply the same isolated `AsyncMock` patching for `litellm.acompletion`.

---

### `tests/tools/test_multilingual_tts.py`
**Issue:** Tests are crashing with `RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited` because they are attempting to use `async for` on a standard `AsyncMock` object instead of an async generator.
- **[MODIFY]** `backend/tests/tools/test_multilingual_tts.py`
  - Replace `communicate.stream.return_value = [b"chunk"]` with a proper async generator function that yields `b"chunk"` to satisfy the `async for` loop inside `MultilingualTTS.synthesize_stream()`.

---

### `tests/tools/test_viral_referral_engine.py`
**Issue:** Tests are crashing with `RuntimeWarning: coroutine 'ViralReferralEngine.process_signup' was never awaited` because the test functions are completely missing the `@pytest.mark.anyio` decorator and the `await` keyword.
- **[MODIFY]** `backend/tests/tools/test_viral_referral_engine.py`
  - Add `@pytest.mark.anyio` to all test methods calling async functions.
  - Add the `await` keyword before `engine.process_signup(...)` and `engine.calculate_reward(...)`.

---

### `tests/test_mcp_servers_integration.py` & `tests/test_swarm_orchestrator.py`
**Issue:** Standard mocking or async execution failures similar to the above.
- **[MODIFY]** `backend/tests/test_mcp_servers_integration.py`
  - Fix API error 401 test mock to properly throw the HTTP exception.
- **[MODIFY]** `backend/tests/test_swarm_orchestrator.py`
  - Ensure the entire graph runner is properly awaited and mocked.

## Verification Plan
1. Run `poetry run pytest` on the entire suite.
2. Verify that 100% of the tests pass without any warnings about unawaited coroutines.
3. Confirm the coverage gate of 25% is maintained.
