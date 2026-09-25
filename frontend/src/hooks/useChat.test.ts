/**
 * Tests for hooks/useChat.ts — Chat hook.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';

// Mock apiClient
vi.mock('../services/apiClient', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    constructor(msg: string, status: number) { super(msg); this.status = status; }
  },
}));

import { apiClient } from '../services/apiClient';

describe('useChat', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('initializes with empty messages', async () => {
    const { useChat } = await import('./useChat');
    const { result } = renderHook(() => useChat());
    expect(result.current.messages).toEqual([]);
  });

  it('sendMessage adds user message', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ reply: 'Hello back' });
    const { useChat } = await import('./useChat');
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    expect(result.current.messages.length).toBeGreaterThan(0);
  });

  it('handles error gracefully', async () => {
    vi.mocked(apiClient.post).mockRejectedValueOnce(new Error('Network'));
    const { useChat } = await import('./useChat');
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('test');
    });

    expect(result.current.error).toBeTruthy();
  });
});
