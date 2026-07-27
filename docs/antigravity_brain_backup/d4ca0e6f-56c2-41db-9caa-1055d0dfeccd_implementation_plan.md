# Reorganize Root Directory

The root directory currently contains over 40 individual files and folders, which makes it look cluttered and unorganized. A well-organized monorepo should keep the root directory strictly for essential configuration, entry points, and high-level documentation.

## Proposed Changes

Here is a plan to cleanly organize the repository without breaking any configurations.

### 1. Move Agent/AI Customization Files
According to standard customization rules, workspace-level agents and rules should live in a specific `.agents/` folder.
- [NEW] `c:\Users\n\supremeai\supremeai_2.0\.agents\` (Create Directory)
- [MODIFY] Move `AGENTS.md` -> `.agents/AGENTS.md`
- [MODIFY] Move `100+rules_for_agent.md` -> `.agents/100+rules_for_agent.md`
- [MODIFY] Move `.agent` and `.antigravity` -> `.agents/` (if they are agent config files)

### 2. Move General Documentation
- [MODIFY] Move `TECH_DEBT.md` -> `docs/TECH_DEBT.md`
*(We will leave `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `CHANGELOG.md` in the root, as this is standard practice for open-source/GitHub repositories).*

### 3. Organize Infrastructure & DevOps
Currently, Docker and server files are cluttering the root.
- [MODIFY] Move `nginx/` (folder) -> `infrastructure/nginx/`
- [MODIFY] Move `docker-compose.yml` -> `infrastructure/docker-compose.yml`
- [MODIFY] Move `docker-compose.prod.yml` -> `infrastructure/docker-compose.prod.yml`
*(We will leave `Dockerfile` and `Dockerfile.backend` in the root for now unless you want them moved, as some automated build systems expect them at the root).*

### 4. Clean Up Temporary/Local Folders
- [DELETE] `scratch/` (If it only contains temporary throwaway scripts, we can delete it or add it to `.gitignore` so it doesn't pollute the repo).

### 5. Keep Essential Configs at Root
We will strictly keep only the following at the root:
- Package management: `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `turbo.json`
- Framework configs: `playwright.config.ts`, `firebase.json`, `vercel.json`, `render.yaml`
- Git/Env: `.env*`, `.gitignore`, `.dockerignore`, `.gcloudignore`

## User Review Required

> [!IMPORTANT]
> **Please review the above moves.** 
> 1. Do you want to move the Dockerfiles to `infrastructure/` as well?
> 2. Are you okay with moving the `nginx` folder into `infrastructure/nginx`?
> 3. Should I delete the `scratch/` folder, or just make sure it is in `.gitignore`?

Once you approve, I will automatically execute these moves and update any necessary file paths.
