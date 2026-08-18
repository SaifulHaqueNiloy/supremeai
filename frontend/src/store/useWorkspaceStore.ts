// apps/studio-client/src/store/useWorkspaceStore.ts
// 🛡️ M0.2 MIGRATION: This store is now a backward-compat shim.
// All workspace/integration state has been merged into useSupremeStore via workspaceSlice.
import { useSupremeStore } from './useSupremeStore';
import type { WorkspaceSlice } from './slices/workspaceSlice';
import type { DockIntegration, Notification } from './slices/types';

export type { DockIntegration, Notification };
export const useWorkspaceStore = useSupremeStore;
export type WorkspaceState = WorkspaceSlice;

export { DEFAULT_INTEGRATIONS } from './slices/workspaceSlice';
