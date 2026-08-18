// apps/studio-client/src/store/useStore.ts
// 🛡️ M0.2 MIGRATION: This store is now a backward-compat shim.
// All app/evolution/deployGate state has been merged into useSupremeStore via coreSlice.
import { useSupremeStore } from './useSupremeStore';
import type { CoreSlice, ChatMessage, DeployGateInfo } from './slices/coreSlice';

export type { ChatMessage, DeployGateInfo };
export const useStore = useSupremeStore;
export type SupremeState = CoreSlice;
