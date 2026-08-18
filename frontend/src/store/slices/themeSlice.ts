import type { StateCreator } from 'zustand';
import type { SupremeStore } from '../useSupremeStore';

export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeSlice {
  theme: ThemeMode;
  toggleTheme: () => void;
  setTheme: (theme: ThemeMode) => void;
}

export const createThemeSlice: StateCreator<SupremeStore, [], [], ThemeSlice> = (set, get) => ({
  theme: 'system',
  toggleTheme: () => {
    const currentTheme = get().theme;
    const newTheme: ThemeMode =
      currentTheme === 'light' ? 'dark' : currentTheme === 'dark' ? 'system' : 'light';
    set({ theme: newTheme });
  },
  setTheme: (theme) => set({ theme }),
});
