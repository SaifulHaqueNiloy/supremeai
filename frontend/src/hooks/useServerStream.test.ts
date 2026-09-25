/**
 * Tests for hooks/useServerStream.ts — SSE streaming hook.
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';

vi.mock('../lib/secureSse', () => ({
  createSecureEventSource: vi.fn(() => ({ close: vi.fn() })),
}));

describe('useServerStream', () => {
  it('initializes without crash', async () => {
    const { useServerStream } = await import('./useServerStream');
    const { result } = renderHook(() => useServerStream('/api/stream', 'token'));
    expect(result.current).toBeDefined();
  });

  it('exposes events array', async () => {
    const { useServerStream } = await import('./useServerStream');
    const { result } = renderHook(() => useServerStream('/api/stream', 'token'));
    expect(result.current.events).toBeDefined();
    expect(Array.isArray(result.current.events)).toBe(true);
  });
});
