# SupremeAI 2.0 — End-to-End Production Deployment Plan

This plan details the steps required to finalize integration testing, deploy the cloud infrastructure, and configure the production database, bringing SupremeAI 2.0 fully online.

## Open Questions

> [!WARNING]
> Before we can proceed with execution, I need the following information/credentials from you:
> 
> 1. **Supabase Cloud Credentials**: Please provide the Production Supabase URL and Service Role Key so I can configure the backend environment.
> 2. **GCP / Firebase Configuration**: What is the target Google Cloud Project ID? Are you authenticated locally with the `gcloud` and `firebase` CLIs?
> 3. **Docker Target**: Do you want to deploy the Docker container to GCP Cloud Run, or are we pushing it to a specific registry first?

## Proposed Changes

### Phase 1: Frontend & Mobile Integration Testing
We will run all unit and integration test suites for the clients to ensure they can communicate correctly with the production-ready backend.
- Run `vitest` in `apps/studio-client` to verify React components and API client services.
- Run Flutter widget and integration tests in `apps/mobile` (if available).
- Ensure `.env.production` files in both apps point to the correct live API endpoints.

### Phase 2: Production Database Setup
We will update the backend configuration to target the live Supabase instance instead of the local/test database.
- Update `backend/core/config.py` and `.env` with the Supabase Production URL and Keys.
- Execute any pending migrations or Supabase schema bootstrapping against the live cloud database using `supabase db push` or direct SQLAlchemy scripts.
- Verify connections using our health-check endpoints.

### Phase 3: Cloud Infrastructure Deployment
We will package and deploy the backend and frontend to their respective cloud hosting environments.
- **Backend**: Build `Dockerfile.backend` and deploy the image. Depending on your preference, we will use `gcloud run deploy` to push it to GCP Cloud Run.
- **Frontend**: Build the React/Vite app via `pnpm build` in `apps/studio-client` and deploy to Firebase Hosting using `firebase deploy --only hosting`.

## Verification Plan

### Automated Tests
- Run full suite of E2E and API tests against the deployed Cloud Run endpoint.

### Manual Verification
- You will need to access the public Firebase Hosting URL and verify that the UI loads and successfully communicates with the live backend.
- Attempt a chat or code generation task from the UI to ensure the LLM Gateway and Supabase DB operate properly in the cloud.
