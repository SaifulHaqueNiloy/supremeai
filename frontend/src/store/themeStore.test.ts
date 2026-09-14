import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../services/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    put: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

import { useThemeStore } from './themeStore';
import { apiClient } from '../services/apiClient';

describe('themeStore', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    useThemeStore.setState({ theme: 'dark', isSyncing: false, lastSyncedAt: null });
  });

  it('toggles the theme from dark to light and syncs to backend', async () => {
    await useThemeStore.getState().toggleTheme();
    expect(useThemeStore.getState().theme).toBe('light');
    expect(apiClient.put).toHaveBeenCalled();
  });

  it('sets a valid theme, syncs, and records the sync timestamp', async () => {
    await useThemeStore.getState().setTheme('light');
    expect(useThemeStore.getState().theme).toBe('light');
    expect(useThemeStore.getState().isSyncing).toBe(false);
    expect(useThemeStore.getState().lastSyncedAt).not.toBeNull();
  });

  it('initializes the theme from backend preferences', async () => {
    (apiClient.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { theme: 'light' } });
    await useThemeStore.getState().initializeFromBackend();
    expect(useThemeStore.getState().theme).toBe('light');
  });

  it('keeps the local theme when the backend fetch fails', async () => {
    (apiClient.get as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('boom'));
    await useThemeStore.getState().initializeFromBackend();
    expect(useThemeStore.getState().theme).toBe('dark');
  });
});
