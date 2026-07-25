# 🧪 Weekly Chaos Engineering Pipeline Specification (Implemented)

> **Status:** ✅ Fully Implemented (2026-07-26)  
> **Location:** `.github/workflows/disaster-recovery-drill.yml`, `backend/scripts/run_chaos_experiment.py`

---

## 2. Technical Implementation Details

### A. GitHub Action Workflow Scheduler (`.github/workflows/disaster-recovery-drill.yml`)
- Triggered automatically via weekly cron expression `0 2 * * 0` (every Sunday at 2 AM) and manually via `workflow_dispatch`.
- Sets up virtualized monorepo test env via `scripts/testenv/setup_test_env.sh`.
- Installs Poetry dependencies, mounts backend services, and executes the chaos runner script.

### B. Chaos Experiment Runner (`backend/scripts/run_chaos_experiment.py`)
- **Fault Injection Scenarios:**
  - **Provider Outage:** Intercepts LLM calls, raises connection errors to trigger the `CircuitBreaker`.
  - **Latency Spike:** Introduces delay using time sleeps to verify timeout exceptions.
- **Circuit Breaker State Machine Validation:**
  - Asserts transition from `CLOSED` $\rightarrow$ `OPEN` upon 3 consecutive failures.
  - Verifies the half-open cooling period (e.g. 5 seconds) during which 1 successful test query restores state to `CLOSED`.
- **Bengali Logic Comments:**
  ```python
  # চওস টেস্ট রানার স্ক্রিপ্ট - ফেইলুর ইনজেকশন করার লজিক
  # এপিআই রেসপন্সে কৃত্রিম বিলম্ব বা ত্রুটি তৈরি করে সার্কিট ব্রেকারের কার্যকারিতা যাচাই করা হয়
  ```
- **Report Generation:** Generates a structured report at `backend/reports/chaos_report.md` recording latency metrics, failure counts, and a final resilience score (target 100%).

---

## 3. Verification & Tests

Executed locally using:
```bash
poetry run python scripts/run_chaos_experiment.py
```
Outputs validation steps showing successful circuit breaker transitions and generates `chaos_report.md`.
