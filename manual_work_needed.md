# Missing APIs and Open Items

This document tracks endpoints and integration gaps that need to be resolved to fully transition the admin dashboard from mock data to real backend data.

## 1. Backup & Restore (`apps/studio-client/src/components/admin/BackupRestore.tsx`)
- **Missing Endpoint**: `GET /admin/backups` (or similar)
- **Description**: The frontend currently initializes the list of backups using a hardcoded `MOCK_BACKUPS` array because there is no API route to fetch the history of backups from the server.
- **Action Required**: Implement the `GET` route in `backend/api/routes/admin_dashboard.py` to list actual backup files/records, and update `BackupRestore.tsx` to use `useQuery` to fetch this list on mount.

## 2. CI/CD Visualizer & Feature Flags (`apps/studio-client/src/components/admin/CICDVisualizer.tsx`)
- **Missing Integration**: Admin-facing Feature Flag write API
- **Description**: The Feature Flags panel relies on a local `MOCK_FLAGS` array. Toggling flags or updating rollout percentages only mutates local React state. While the backend has a `core/ld_client.py` for LaunchDarkly integration, it is unclear if an admin API exists to update these flags dynamically.
- **Action Required**: Verify the existence of (or create) a `POST/PUT` endpoint for feature flags that interacts with LaunchDarkly, and wire `CICDVisualizer.tsx` to use it via `useMutation`.
