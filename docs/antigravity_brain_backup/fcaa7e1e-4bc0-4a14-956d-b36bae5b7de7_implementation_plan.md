# Implementation Plan: Webhook-based CI Reporting API

This plan outlines the implementation of a full-stack Webhook-based CI Reporting API to replace the git-push anti-pattern in our GitHub Actions pipeline, storing reports in the database and visualizing them dynamically in the VS Code/Studio Client admin panel.

## User Review Required

> [!IMPORTANT]
> The database migration will create the `ci_reports` table. It utilizes PostgreSQL via the existing PgBouncer connection pool and raw `asyncpg` queries, matching the established backend patterns.

> [!IMPORTANT]
> A webhook secret `CI_WEBHOOK_SECRET` must be set in the `.env` file of the backend and added to GitHub Secrets as `CI_WEBHOOK_SECRET` for secure reporting.

## Proposed Changes

### Backend Component

#### [NEW] [ci_report.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/models/ci_report.py)
Create Pydantic schema and raw `asyncpg` database operation functions:
* `create_ci_report(payload: CIReportPayload)`
* `get_recent_ci_reports(limit: int = 20)`
* `get_ci_report_by_run_id(run_id: int)`

#### [NEW] [ci_webhooks.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/api/routes/ci_webhooks.py)
Create FastAPI route `POST /api/ci/webhook` to handle GitHub Actions reports payload:
* Validate incoming request using `CI_WEBHOOK_SECRET` header check.
* Store payload in the `ci_reports` table.

#### [NEW] [migration](file:///c:/Users/n/supremeai/supremeai_2.0/backend/alembic/versions/add_ci_reports_table.py)
Manually create an Alembic migration script to construct the `ci_reports` table.

#### [MODIFY] [config.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/config.py)
* Add `ci_webhook_secret` configuration setting.

#### [MODIFY] [app.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/core/app.py)
* Register `/api/ci/webhook` and fetch endpoint for admin dashboard list `/api/admin/ci-logs`.

#### [MODIFY] [admin_dashboard.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/api/routes/admin_dashboard.py)
* Add/Modify endpoint `GET /api/admin/ci-logs` to query recent CI logs from database using `get_recent_ci_reports()`.

---

### Frontend Component (React Client)

#### [NEW] [ciReportService.ts](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/services/ciReportService.ts)
* Create fetch clients for retrieving CI logs from backend `/api/admin/ci-logs`.

#### [NEW] [useCIReports.ts](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/hooks/useCIReports.ts)
* Create React hook to handle state, loading, and refreshing for CI reports.

#### [MODIFY] [CICDVisualizer.tsx](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/components/admin/CICDVisualizer.tsx)
* Replace mock pipeline with dynamic CI logs list and detailed log viewer component.
* Display build status badges, runtime seconds, trigger actor, and details of failed jobs dynamically.

---

### GitHub Actions Configuration

#### [MODIFY] [supreme-ci.yml](file:///c:/Users/n/supremeai/supremeai_2.0/.github/workflows/supreme-ci.yml)
* Remove the `git push` logic to `logs/ci/` in the `📤 CI লগ রিপোতে কমিট` step.
* Update `generate-ci-report.py` or the runner step to curl the backend endpoint:
  ```bash
  curl -X POST -H "Content-Type: application/json" \
    -H "X-CI-Webhook-Secret: ${{ secrets.CI_WEBHOOK_SECRET }}" \
    -d @report_payload.json \
    "${{ env.SUPREMEAI_API_URL }}/api/ci/webhook"
  ```

## Verification Plan

### Automated Tests
* Test database functions in `backend/tests/test_ci_report.py`.
* Test webhook validation in `backend/tests/test_ci_webhook_route.py`.
* Run pytest locally using `python -m pytest backend/tests/test_ci_report.py`.

### Manual Verification
* Run backend server and trigger mock webhook payloads using postman/curl to verify they insert successfully.
* Open Studio Client Admin dashboard, navigate to CI/CD tab, and ensure items render dynamically.
