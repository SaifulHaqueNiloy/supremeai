# SupremeAI 2.0 — Auto-Fix Pytest & AI Code Modification Implementation Plan

This plan addresses the omission of pytest failure handling in `ci-auto-fix-v3.py` and fully implements the execution/applying of AI-suggested code fixes.

## Proposed Changes

### CI/CD Scripts

#### [MODIFY] [ci-auto-fix-v3.py](file:///c:/Users/n/supremeai/supremeai_2.0/.github/scripts/ci-auto-fix-v3.py)
1. **Pytest Failure Detection**: Update `fix_backend()` to run `poetry run pytest -q --tb=short` if the formatting checks passed but a failure occurred. Capture its stdout/stderr as error logs.
2. **Structured AI Prompt**: Modify the system prompt in `call_supremeai_api`, `call_openai_api`, and `call_gemini_api` to request code fixes in a structured JSON format:
   ```json
   {
     "explanation": "Brief explanation in Bengali",
     "files": [
       {
         "path": "backend/tests/test_api.py",
         "content": "full updated file content..."
       }
     ]
   }
   ```
3. **Suggestion Application**: Write a parser in `get_ai_suggestion` or the fixer functions to parse this JSON structure, write the updated contents back to the workspace, and append to `FIXES_APPLIED`.
4. **Bengali Comments**: Add Bangla comments explaining the implementation.

## Verification Plan

### Automated Tests
- Run `python .github/scripts/ci-auto-fix-v3.py --job backend-test --mode suggest-only` locally with a mocked failure to verify it parses and outputs the correct suggestions.
