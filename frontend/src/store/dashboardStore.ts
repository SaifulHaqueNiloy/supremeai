// apps/studio-client/src/store/dashboardStore.ts
// 🛡️ M0.2 MIGRATION: This store is now a backward-compat shim.
// All dashboard state has been merged into useSupremeStore via dashboardSlice.
import { useSupremeStore } from './useSupremeStore';
import type { DashboardSlice } from './slices/dashboardSlice';

export const useDashboardStore = useSupremeStore;
export type DashboardState = DashboardSlice;
