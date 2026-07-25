# 🔎 Causal Reasoning Engine Specification (Implemented)

> **Status:** ✅ Fully Implemented (2026-07-26)  
> **Location:** `backend/brain/causal/interventions.py`, `backend/brain/causal/discovery.py`, `backend/brain/causal/root_cause.py`

---

## 2. Technical Implementation Details

### A. Intervention Tracker (`backend/brain/causal/interventions.py`)
- Tracks actions taken on the system (`DEPLOYMENT`, `CONFIG_CHANGE`, `SCALE_OUT`).
- Logs a timeline snapshot containing pre-intervention and post-intervention system performance metrics (e.g. latency, error rate, CPU load).

### B. Causal Discovery Engine (`backend/brain/causal/discovery.py`)
- Takes telemetry data and evaluates relationships using statistical correlation and time-lag analysis.
- Generates a directed causal graph (DAG) representing system dependencies.
- **Bengali Logic Comments:**
  ```python
  # সংগৃহীত মেট্রিক্স ডেটা থেকে ভেরিয়েবলগুলোর মধ্যে কার্যকারণ সম্পর্ক (Causal Link) খুঁজে বের করার লজিক
  ```

### C. Root Cause Analyzer (`backend/brain/causal/root_cause.py`)
- Uses Pearl's Do-Calculus to simulate interventions on candidate failure nodes.
- Computes causal effects and confidence scores to isolate true root causes from downstream symptoms.
- Returns actionable remediation paths (e.g. recommend database index update instead of container scale-out).

---

## 3. Verification & Tests

Executed from the backend root using:
```bash
poetry run pytest tests/test_causal_engine.py
```
Tests assert causal link generation accuracy, do-calculus calculation math, and diagnostic predictions under synthetic load anomalies.
