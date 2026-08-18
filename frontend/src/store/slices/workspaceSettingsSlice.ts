import type { StateCreator } from 'zustand';
import { getApiBaseUrl } from '../../utils/api';
import type { SupremeStore } from '../useSupremeStore';

export interface WorkspaceSettingsSlice {
  settings: Record<string, unknown>;
  updateSetting: (key: string, value: unknown) => void;
  resetSettings: () => void;
  saveSettings: () => Promise<void>;
  loadSettings: () => Promise<void>;
}

export const createWorkspaceSettingsSlice: StateCreator<SupremeStore, [], [], WorkspaceSettingsSlice> = (
  set,
  get,
) => ({
  settings: {},
  updateSetting: (key, value) => set((state) => ({ settings: { ...state.settings, [key]: value } })),
  resetSettings: () => set({ settings: {} }),
  saveSettings: async () => {
    set({ loading: true, error: null });
    try {
      await fetch(`${getApiBaseUrl()}/admin-api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(get().settings),
      });
    } catch {
      set({ error: 'Failed to save settings' });
    } finally {
      set({ loading: false });
    }
  },
  loadSettings: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${getApiBaseUrl()}/admin-api/settings`);
      const settings = await response.json();
      set({ settings });
    } catch {
      set({ error: 'Failed to load settings' });
    } finally {
      set({ loading: false });
    }
  },
});
