import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { usePlugins } from './usePlugins';

vi.mock('../utils/api', () => ({
  getApiBaseUrl: vi.fn(() => 'http://localhost:8080'),
}));

vi.mock('../services/apiClient', () => ({
  getAuthHeaders: vi.fn(async () => ({ Authorization: 'Bearer mock-token' })),
}));

describe('usePlugins hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches marketplace and installed plugins on mount', async () => {
    const mockMarketplace = [{ id: 'p1', name: 'Plugin 1', description: 'Desc 1', category: 'tools' }];
    const mockInstalled = [{ id: 'i1', plugin_id: 'p1', status: 'active', is_enabled: true }];

    global.fetch = vi.fn((url: string) => {
      if (url.includes('/marketplace')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ plugins: mockMarketplace }),
        } as Response);
      }
      if (url.includes('/installed')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ installations: mockInstalled }),
        } as Response);
      }
      return Promise.reject(new Error('Unknown url'));
    }) as any;

    const { result } = renderHook(() => usePlugins());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.marketplacePlugins).toEqual(mockMarketplace);
    expect(result.current.installedPlugins).toEqual(mockInstalled);
    expect(result.current.error).toBeNull();
  });

  it('handles fetch errors gracefully', async () => {
    global.fetch = vi.fn(() => Promise.reject(new Error('Network error'))) as any;

    const { result } = renderHook(() => usePlugins());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
  });

  it('installs a plugin successfully and refreshes list', async () => {
    global.fetch = vi.fn((url: string, opts?: RequestInit) => {
      if (opts?.method === 'POST') {
        return Promise.resolve({ ok: true, json: async () => ({ success: true }) } as Response);
      }
      return Promise.resolve({ ok: true, json: async () => ({ plugins: [], installations: [] }) } as Response);
    }) as any;

    const { result } = renderHook(() => usePlugins());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.installPlugin('p1', ['read']);
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/plugins/install'),
      expect.objectContaining({ method: 'POST' })
    );
  });
});
