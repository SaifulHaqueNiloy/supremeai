// apps/studio-client/src/store/useIdeStore.ts
// 🛡️ M0.2 MIGRATION: This store is now a backward-compat shim.
// All IDE state has been merged into useSupremeStore via ideSlice.
import { useSupremeStore } from './useSupremeStore';
import type { IdeSlice, IdeFile } from './slices/ideSlice';

export type { IdeFile };
export const useIdeStore = useSupremeStore;
export type IdeState = IdeSlice;
