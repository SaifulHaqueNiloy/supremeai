# Repository Reorganization Complete

The root directory of your repository has been successfully cleaned and organized.

## What was changed?
- **Agent Rules:** Moved all agent configuration and rule files (`AGENTS.md`, `100+rules_for_agent.md`, `.agent`, `.antigravity`) into a dedicated `.agents/` directory, following standard AI workspace conventions.
- **Documentation:** Moved `TECH_DEBT.md` into the `docs/` folder.
- **Infrastructure:** Moved `nginx/` config and `docker-compose*.yml` files into the `infrastructure/` directory to declutter the root.
- **Cleanup:** Added `scratch/` to `.gitignore` and removed it from Git tracking so local temporary scripts don't pollute the repository.

## Validation
- [x] Workspace is clean.
- [x] All moves were performed using `git mv` to preserve commit history.
- [x] Changes pushed successfully to GitHub on `refactor/core-migration`.
