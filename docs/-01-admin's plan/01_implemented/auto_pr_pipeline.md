# 🛠️ Auto PR Pipeline Specification (Implemented)

> **Status:** ✅ Fully Implemented (2026-07-26)  
> **Location:** `backend/tools/code/auto_pr_pipeline.py`, `backend/core/security/guardian_ai.py`

---

## 2. Technical Implementation Details

### A. Guardian AI Security Scan (`backend/core/security/guardian_ai.py`)
- Core method `scan_code(code: str)` runs code analysis before commit or push operations.
- Intercepts unsafe code blocks (e.g. potential code injections, hardcoded secrets, shell syntax violations).
- Integrates with `OutputSanitizer` to clean up payloads before git branch allocation.

### B. Auto PR Pipeline Orchestrator (`backend/tools/code/auto_pr_pipeline.py`)
- **Execution Pipeline Steps:**
  1. Validates input fix patch string using `GuardianAI`.
  2. Spawns isolated shell command or python-git process to create patch branches.
  3. Commits fixes and creates GitHub pull requests targetting the destination branch.
- **Bengali Logic Comments:**
  ```python
  # গিট ব্রাঞ্চ তৈরি এবং রিমোট রিপোজিটরিতে কোড পুশ করার প্রাক-প্রস্তুতি লজিক
  # পুশ করার পূর্বে Guardian AI দিয়ে পুরো কোড অটো-স্ক্যান করা হয়
  ```

---

## 3. Verification & Tests

Executed from the backend root using:
```bash
poetry run pytest tests/test_auto_pr_pipeline.py
```
Tests assert security screening triggers, git branch execution safety, mock PR submission, and result structures.
