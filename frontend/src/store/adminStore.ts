// apps/studio-client/src/store/adminStore.ts
// 🛡️ M0.2 MIGRATION: This store is now a backward-compat shim.
// All state + auth logic has been merged into useSupremeStore via adminSlice.
// Consumers should migrate to `useSupremeStore` — this wrapper will be deprecated.
import { useSupremeStore } from './useSupremeStore';
import type { AdminSlice } from './slices/adminSlice';
export const useAdminStore = useSupremeStore;
export type AdminState = AdminSlice;

// Re-export auth helpers for any external consumers
export { decodeJwt, isTokenExpired, restoreAdminSession, buildProvisioningUri } from './slices/adminAuthHelpers';
