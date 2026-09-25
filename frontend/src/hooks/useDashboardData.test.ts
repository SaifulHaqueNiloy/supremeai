/**
 * Tests for hooks/useDashboardData.ts — Dashboard data hook.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

vi.mock('../services/apiClient', () => ({
  apiClient: { get: vi.fn() },
  ApiError: class ApiError extends Error { status: number; },
}));

import { apiClient } from '../services/apiClient';

describe('useDashboardData', () => {
  beforeEach(() => vi.clearAllMocks());

  it('initializes with null data', async () => {
    const { useDashboardData } = await import('./useDashboardData');
    const { result } = renderHook(() => useDashboardData());
    expect(result.current.data).toBeNull();
  });

  it('fetches dashboard data', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ metrics: {} });
    const { useDashboardData } = await import('./useDashboardData');
    const { result } = renderHook(() => useDashboardData());
    await act(async () => { await result.current.refresh(); });
    expect(result.current.data).not.toBeNull();
  });
});
