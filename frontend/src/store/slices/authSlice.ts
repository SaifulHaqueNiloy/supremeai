import type { StateCreator } from 'zustand';
import type { SupremeStore } from '../useSupremeStore';
import type { User } from './types';

export interface AuthSlice {
  isAuthenticated: boolean;
  user: User | null;
  login: (userData: User) => void;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
}

export const createAuthSlice: StateCreator<SupremeStore, [], [], AuthSlice> = (set, get) => ({
  isAuthenticated: false,
  user: null,
  login: (userData) => set({ isAuthenticated: true, user: userData }),
  logout: () => set({ isAuthenticated: false, user: null }),
  updateUser: (userData) => set({ user: { ...get().user, ...userData } }),
});
