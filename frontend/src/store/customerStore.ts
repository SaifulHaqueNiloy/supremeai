// apps/studio-client/src/store/customerStore.ts
// 🛡️ M0.2 MIGRATION: This store is now a backward-compat shim.
// All customer state has been merged into useSupremeStore via customerSlice.
import { useSupremeStore } from './useSupremeStore';
import type { CustomerSlice } from './slices/customerSlice';

export const useCustomerStore = useSupremeStore;
export type CustomerStoreState = CustomerSlice;

export function useHydrated(): boolean {
  return useSupremeStore((s) => s.hydrated);
}
