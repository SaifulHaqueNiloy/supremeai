# Firebase & Vercel Architectural Segregation Completed

The deployment architecture has been successfully updated to separate the Admin Portal (Firebase) from the User Portal (Vercel). This provides enhanced security, targeted caching strategies, and robust path filtering in CI.

## 📁 Path Segregation Implemented

To ensure the GitHub Actions path filters trigger cleanly:
- Created the directory `apps/studio-client/src/pages/user/`.
- Moved all top-level user pages (e.g., `AgentWorkspace.tsx`, `IdeWorkspace.tsx`, `ArchitectTower.tsx`, `EvolutionForge/`, `IntegrationsManager.tsx`) into the new `user/` directory.
- `LoginPage.tsx` was successfully relocated to `auth/`.
- Executed a custom AST-like import resolver to accurately update all `../` and `../../` relative dependencies in the moved files.
- `App.tsx` has been refactored to consume the new `user/` and `auth/` paths cleanly.

## 🚀 CI/CD Pipeline Updates

The `.github/workflows/supreme-core-ci.yml` has been meticulously modified to support dual-deployment:

### 1. `deploy-admin-firebase`
- **Trigger**: Runs strictly when changes are detected in the `admin` paths (`src/pages/admin/**`) or `shared` paths.
- **Build**: Executes `VITE_PORTAL_TYPE=admin pnpm --dir apps/studio-client run build`.
- **Deploy**: Deploys via `FirebaseExtended/action-hosting-deploy@v0` to `supremeai-admin-portal` targeting `admin-hosting`.

### 2. `deploy-user-vercel`
- **Trigger**: Runs strictly when changes are detected in the `user` paths (`src/pages/user/**`, `src/pages/auth/**`) or `shared` paths.
- **Build**: Executes `VITE_PORTAL_TYPE=user pnpm --dir apps/studio-client run build`.
- **Deploy**: Deploys via `vercel --prod` to Vercel, isolated from the Admin code.

## 🔥 Firebase Configuration Updates
- Modified `firebase.json` at the project root to properly map the `"target": "admin-hosting"` to `apps/studio-client/dist-admin`.
- Configured `.firebaserc` to recognize `admin-hosting`.

## 🛠️ Cascading Failures Resolved
- **Circuit Breaker Fix:** Replaced missing `pybreaker` dependency with our internal `core.resilience.circuit_breaker.CircuitBreaker` and implemented `__call__` to allow decorator usage (`@db_breaker`).
- **Test Timings Fix:** Fixed the `CircuitBreaker` timing and state tests so it transitions correctly in CI.
- **Removed Stale Evolution Code:** Deleted the duplicate `backend/evolution` folder via `git rm -r` that was conflicting with `backend/core/evolution` and causing the `MaliciousCodeError` import failure.
- **Import Fixes:** Pointed `cost_guard` and `shutdown_global_browser` to their correct locations in `core`.
- **Portal Separation Verification:** Verified in `apps/studio-client/vite.config.ts` and `package.json` that `VITE_PORTAL_TYPE` conditionally builds into `dist-admin` and `dist-user` artifacts as requested.

## ✅ Build Verification
Both builds were tested manually in the execution environment and compiled successfully:
- `VITE_PORTAL_TYPE=admin` created `dist-admin/` perfectly.
- `VITE_PORTAL_TYPE=user` created `dist-user/` perfectly.

> [!TIP]
> Run `vercel link` on your local machine to link the repo to the specific Vercel project before merging this so that the deployment step automatically targets the correct project!
