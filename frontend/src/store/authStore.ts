// apps/studio-client/src/store/authStore.ts
// 🛡️ M0.2 MIGRATION: This store is now a backward-compat shim.
// All auth state and methods have been merged into useSupremeStore via authSlice.
import { useSupremeStore } from './useSupremeStore';
import { AuthStatus, type AuthSlice, type UserProfile } from './slices/authSlice';

export { AuthStatus };
export type { UserProfile };
export const useAuthStore = useSupremeStore;
export type AuthState = AuthSlice;
