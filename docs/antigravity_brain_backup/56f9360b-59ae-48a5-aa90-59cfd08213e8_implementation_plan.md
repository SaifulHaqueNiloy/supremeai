# Solve Ruff Lint Errors

This plan addresses the two static analysis errors caught by Ruff in the Pre-Merge Gate.

## Proposed Changes

### Backend Core
#### [MODIFY] [llm_gateway.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/llm_gateway.py)
- **Fix `BLE001 Do not catch blind exception: Exception`:**
  - Add `# noqa: BLE001` to the `except Exception:` block on line 140, just like it's done on line 133, or catch a more specific exception. Since this is in the `failure_callback` calculating duration, it is a broad fallback and suppressing the lint is appropriate here.

### Evolution
#### [MODIFY] [auto_skill_creator.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/evolution/auto_skill_creator.py)
- **Fix `W293 [*] Blank line contains whitespace`:**
  - Remove the trailing whitespaces from the blank line at line 212.

## Verification Plan

### Automated Tests
- Run Ruff manually against the backend directory to ensure the errors are resolved:
  `ruff check backend/`
