# Display GitHub CI and Health Reports on Admin Dashboard

This plan outlines the steps to add real-time monitoring cards for GitHub Actions (CI) and the System Health status directly in the SupremeAI Admin Dashboard.

## User Review Required
> [!IMPORTANT]
> To fetch GitHub CI data, we need to interact with the GitHub API. 
> - **Option 1 (Recommended)**: Create a new backend admin endpoint (e.g., `GET /api/v1/admin/github-ci`) that uses a GitHub Personal Access Token (stored securely in the backend environment) to fetch the workflow runs and pass them securely to the frontend.
> - **Option 2**: Call the GitHub API directly from the React frontend using a token, which is easier but less secure.
> 
> Also, for the Health Report, we will hit the existing `/api/v1/health` endpoint, or should we expose the results of the newly updated `auto_health_check.py` via a new endpoint?

## Proposed Changes

### Backend Components

#### [NEW] backend/api/routes/admin_dashboard.py (or update existing admin routes)
- Add an endpoint to fetch the latest GitHub Workflow Runs for the `supreme-core-ci.yml` pipeline using the `httpx` client.
- Ensure this endpoint is protected by the admin JWT middleware.

### Frontend Components

#### [MODIFY] apps/studio-client/src/pages/admin/AdminDashboard.tsx (or equivalent dashboard entry)
- Add a two-column grid (or two new widgets/cards) for the new reports.

#### [NEW] apps/studio-client/src/components/admin/GitHubCIWidget.tsx
- A React component that fetches the CI data from the backend and displays the status (Passed, Failed, Running) with appropriate colors (green, red, yellow).
- Shows the latest commit message and author.

#### [NEW] apps/studio-client/src/components/admin/HealthReportWidget.tsx
- A React component that fetches the health status (either from `/api/v1/health` or the new health check logic).
- Displays individual service statuses (API Gateway, Redis, etc.) with visual indicators (checkmarks/crosses).

## Verification Plan

### Automated Tests
- Run backend pytest to ensure the new admin endpoints are protected and functional.
- Run frontend vitest to ensure the new widget components render without crashing.

### Manual Verification
- Log in to the Admin Portal in the Studio Client.
- Verify that the GitHub CI card displays the latest pipeline run.
- Verify that the Health Report card displays the correct system status and handles offline services gracefully.
