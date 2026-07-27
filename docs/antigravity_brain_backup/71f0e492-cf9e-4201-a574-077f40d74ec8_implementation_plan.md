# Deploy Backend to Render

This plan outlines the steps required to migrate the backend deployment to Render using Infrastructure as Code (IaC) via a Render Blueprint (`render.yaml`).

## User Review Required

> [!WARNING]
> **Secrets Configuration**
> Since this uses a `render.yaml` blueprint, sensitive environment variables (API keys, JWT secrets, etc.) will be created as placeholders (`sync: false`). You will need to manually populate the actual values in the Render Dashboard once the blueprint is applied.
> 
> **Free Tier Limitations**
> The service is targeted for the `free` plan to optimize costs. Render free-tier instances will spin down after a period of inactivity, which may cause a "cold start" delay (up to 50 seconds) on the first request.

## Open Questions

> [!IMPORTANT]
> 1. Which **region** do you prefer? (Default: `oregon`, options include `ohio`, `frankfurt`, `singapore`)
> 2. Do you want to connect a Render **PostgreSQL** instance via this blueprint, or continue using the external Supabase database?
> 3. Does the application require any specific health check path (e.g., `/health`) to be configured for the deploy?

## Proposed Changes

### Configuration

#### [NEW] [render.yaml](file:///c:/Users/n/supremeai/supremeai_2.0/render.yaml)
A new `render.yaml` file will be created at the root of the repository to define the backend service:
```yaml
services:
  - type: web
    name: supremeai-backend
    env: docker
    dockerfilePath: Dockerfile
    dockerContext: .
    region: oregon
    plan: free
    healthCheckPath: /api/v1/system/health  # Adjust based on your health route
    envVars:
      - key: ENV
        value: production
      - key: PORT
        value: 10000
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: SUPREMEAI_JWT_SECRET
        sync: false
      - key: SUPREMEAI_ADMIN_PASSWORD_HASH
        sync: false
      - key: STRIPE_API_KEY
        sync: false
      - key: STRIPE_WEBHOOK_SECRET
        sync: false
```

## Verification Plan

### Automated Steps
- Create the `render.yaml` file.
- Use the available `.\render.exe` CLI to apply the blueprint or check for validation errors.

### Manual Verification
- Go to the Render Dashboard, open the `supremeai-backend` service, and manually insert the secure environment values.
- Wait for the deployment to finish and verify that the backend is responding correctly via the Render-provided `.onrender.com` URL.
