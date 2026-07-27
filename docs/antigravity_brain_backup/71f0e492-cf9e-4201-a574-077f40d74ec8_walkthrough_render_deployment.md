# Walkthrough: Backend Deployment to Render

I have successfully prepared the project for deployment to Render. 

## Changes Made
- Created a `render.yaml` Blueprint definition at the root of the project.
- Configured a Docker-based Web Service named `supremeai-backend` using the root `Dockerfile`.
- Set the tier to `free` and region to `oregon`.
- Defined environment variables including `PORT=10000` and placeholders for critical API keys (Supabase, Stripe, OpenRouter, Gemini, etc.).
- Validated the Blueprint using the local Render CLI `.\render.exe blueprints validate .\render.yaml` (returned `valid: true`).
- Pushed the file to the `main` branch.

## Next Steps for the User

> [!IMPORTANT]
> **Action Required: Connect Blueprint in Dashboard**
> Since `render.yaml` cannot be automatically deployed via the CLI the very first time, you must perform these steps:
> 
> 1. Go to the [Render Dashboard (Blueprints)](https://dashboard.render.com/blueprints).
> 2. Click **New Blueprint Instance**.
> 3. Connect your GitHub repository (`supremeai`).
> 4. Render will automatically detect the `render.yaml` file.
> 5. You will be prompted to enter the missing secrets (`sync: false` variables). Please have the following ready to paste in:
>    - `SUPABASE_URL`
>    - `SUPABASE_KEY`
>    - `OPENROUTER_API_KEY`
>    - `GEMINI_API_KEY`
>    - `SUPREMEAI_JWT_SECRET`
>    - `SUPREMEAI_ADMIN_PASSWORD_HASH`
>    - `STRIPE_API_KEY`
>    - `STRIPE_WEBHOOK_SECRET`
> 6. Click **Apply**. 

Once applied, Render will build the Docker container and start serving traffic!

> [!NOTE]
> Future pushes to `main` will automatically trigger a re-deployment on Render!
