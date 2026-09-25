/**
 * Tests for hooks/useAdminApi.ts — Admin API hook.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';

vi.mock('../services/apiClient', () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
  ApiError: class ApiError extends Error { status: number; constructor(m: string, s: number) { super(m); this.status = s; } },
}));

import { apiClient } from '../services/apiClient';

describe('useAdminApi', () => {
  beforeEach(() => vi.clearAllMocks());

  it('initializes with idle state', async () => {
    const { useAdminApi } = await import('./useAdminApi');
    const { result } = renderHook(() => useAdminApi());
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('fetches admin data', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ users: [] });
    const { useAdminApi } = await import('./useAdminApi');
    const { result } = renderHook(() => useAdminApi());
    await act(async () => { await result.current.fetch('/admin/stats'); });
    expect(result.current.data).not.toBeNull();
  });

  it('handles error', async () => {
    vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('fail'));
    const { useAdminApi } = await import('./useAdminApi');
    const { result } = renderHook(() => useAdminApi());
    await act(async () => { await result.current.fetch('/admin/stats'); });
    expect(result.current.error).toBeTruthy();
  });
});
