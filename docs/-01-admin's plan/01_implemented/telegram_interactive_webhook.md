# 📢 Telegram/Slack Interactive AI Webhook Specification (Implemented)

> **Status:** ✅ Fully Implemented (2026-07-26)  
> **Location:** `backend/api/routes/webhooks_ai.py`

---

## 2. Technical Implementation Details

### A. Webhook Alert Controller
- **Endpoint 1: Alert Broadcasting (`POST /api/v1/webhooks/telegram/send-alert`):**
  - Sends system status metrics, vulnerability findings, or PR notifications to specified Telegram channels.
  - Formats payloads with structured markdown and attaches inline buttons:
    - **`[Approve PR]`**: Configured with callback data format: `approve_pr:{branch_name}`.
    - **`[Reject]`**: Configured with callback data format: `reject_pr:{branch_name}`.
- **Endpoint 2: Interactive Callback Receiver (`POST /api/v1/webhooks/telegram/callback`):**
  - Receives payload from Telegram webhook containing user button interaction data.
  - Verifies admin role token metadata mapping.
  - Initiates branch deployment triggers or rejects PRs based on callback payload.
- **Bengali Logic Comments:**
  ```python
  # টেলিগ্রাম বাটন ক্লিক থেকে কলব্যাক ডাটা পাওয়ার পর এক্সিকিউশন শুরু করার লজিক
  # ইউজারের পারমিশন লেভেল বা রোল চেক করা হয়
  ```

---

## 3. Verification & Tests

Executed from the backend root using:
```bash
poetry run pytest tests/test_webhooks_ai.py
```
Tests mock outbound Telegram API responses, simulate callback actions, and verify execution routing of PR actions.
