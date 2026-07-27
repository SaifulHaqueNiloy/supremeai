# SupremeAI 2.0 - Sprint 5 Implementation Plan

Executing Sprint 5: Backend API Integration. I am proceeding directly with the implementation as per your elite autonomy instruction.

## Goal
Connect the frontend `studio-client` to the FastAPI backend to replace simulated auth and commands with real HTTP/WebSocket API calls.

## Proposed Changes

### 1. Backend Authentication API
- **[MODIFY]** `backend/main.py`: Mount the `auth.py` router under `/api/v1`.
- **[MODIFY]** `backend/api/routes/auth.py`: Implement a `/login/dev` endpoint (or update `/login`) to issue real JWT tokens for local development, overriding the `501 Not Implemented` placeholder.

### 2. Frontend Auth Store Integration
- **[MODIFY]** `apps/studio-client/src/store/authStore.ts`: Replace the `setTimeout` mock login with an actual POST request to `/api/v1/auth/login` using `apiClient`.
- **[MODIFY]** `apps/studio-client/src/services/apiClient.ts`: Restore the `Authorization: Bearer <token>` header logic so authenticated requests to the backend succeed.

## Execution
I will now execute this end-to-end integration.
