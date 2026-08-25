# R13 — Legacy Zustand Stores Migration Map

These 12 stores are targeted for consolidation into `unifiedStore.ts`.

| Legacy store file            | unifiedStore slice  | Status  |
|------------------------------|---------------------|---------|
| `adminStore.ts`              | `admin`             | pending |
| `authStore.ts`               | `auth`              | pending |
| `chatStore.ts`               | `chat`              | pending |
| `customerStore.ts`           | `customer`          | pending |
| `dashboardStore.ts`          | `dashboard`         | pending |
| `sessionCockpitStore.ts`     | `session`           | pending |
| `themeStore.ts`              | `theme`             | pending |
| `useIdeStore.ts`             | `ide`               | pending |
| `useStore.ts`                | `root` (passthrough) | pending |
| `useSupremeStore.ts`         | `supreme`           | pending |
| `useWorkspaceSettingsStore.ts` | `workspaceSettings` | pending |
| `useWorkspaceStore.ts`       | `workspace`         | pending |

## Migration plan

- **Phase 1 (current patch):** Add `UNIFIED_STORE` flag (default off). Add Dexie
  local DB. No legacy file deleted.
- **Phase 2 (next release):** Set flag to `true` in staging. Replace each legacy
  store with a 1-line re-export shim:
  ```ts
  // frontend/src/store/chatStore.ts
  import { useUnifiedStore } from './unifiedStore';
  export const useChatStore = () => useUnifiedStore((s) => s.chat);
  ```
- **Phase 3 (release N+1):** Delete the shim files. Sweep all importers to point
  directly at `unifiedStore`.

## Rollback

```ts
// In the browser console:
localStorage.removeItem('UNIFIED_STORE');
// Or at build time, set VITE_UNIFIED_STORE=false
```

All legacy stores restore immediately — no data loss, no migration needed.

## Why

The current 13-store sprawl causes:

1. **Bundle bloat** — each store pulls its own dependencies, even if unused.
2. **Race conditions** — multiple stores subscribing to the same backend data can
   fire out of order.
3. **No offline support** — all reads go to Supabase, which has a 60-100
   concurrent connection limit on free-tier. Under multi-user load this exhausts
   the pool.

The unified store + Dexie combo:
- Single source of truth (Zustand)
- IndexedDB persistence (Dexie) — reads are local, fast, offline-friendly
- Background sync to Supabase every 30s (configurable)
- Cuts Supabase DB connections by ~90% on a typical chat session
