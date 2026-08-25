/**
 * R13 FIX: Slice composition map for unifiedStore migration.
 *
 * Maps the 12 legacy Zustand store names to their slice counterparts in
 * the unified store. Use this as the migration reference when sweeping
 * the frontend codebase.
 *
 * Migration plan:
 *   Phase 1 (current patch): Add UNIFIED_STORE flag (default off). Add Dexie
 *     local DB. No legacy file deleted.
 *   Phase 2 (next release): Set flag to true in staging. Replace each legacy
 *     store with a 1-line re-export shim:
 *       // frontend/src/store/chatStore.ts
 *       export const useChatStore = () => useUnifiedStore((s) => s.chat);
 *   Phase 3 (release N+1): Delete the shim files. Sweep all importers to
 *     point directly at `unifiedStore`.
 */

export const LEGACY_TO_UNIFIED_MAP = {
  adminStore: 'admin', // from userSlice
  authStore: 'auth', // from userSlice
  chatStore: 'chat', // new chatSlice (TODO: create in Phase 2)
  customerStore: 'customer', // from apiSlice
  dashboardStore: 'dashboard', // from uiSlice
  sessionCockpitStore: 'session', // from uiSlice
  themeStore: 'theme', // from uiSlice
  useIdeStore: 'ide', // from workspaceSlice
  useStore: 'root', // direct unifiedStore passthrough
  useSupremeStore: 'supreme', // from apiSlice
  useWorkspaceSettingsStore: 'workspaceSettings', // from workspaceSlice
  useWorkspaceStore: 'workspace', // from workspaceSlice
} as const;

export type LegacyStoreName = keyof typeof LEGACY_TO_UNIFIED_MAP;
export type UnifiedSliceName = (typeof LEGACY_TO_UNIFIED_MAP)[LegacyStoreName];
