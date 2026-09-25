/**
 * Tests for hooks/useWebSocket.ts — WebSocket hook.
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  readyState = 0;
  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(public url: string) { MockWebSocket.instances.push(this); }
  send() {}
  close() { this.readyState = 3; this.onclose?.(); }
}

vi.stubGlobal('WebSocket', MockWebSocket);

describe('useWebSocket', () => {
  it('initializes without crash', async () => {
    const { useWebSocket } = await import('./useWebSocket');
    const { result } = renderHook(() => useWebSocket('ws://localhost'));
    expect(result.current).toBeDefined();
  });

  it('exposes send function', async () => {
    const { useWebSocket } = await import('./useWebSocket');
    const { result } = renderHook(() => useWebSocket('ws://localhost'));
    expect(result.current.send).toBeDefined();
    expect(typeof result.current.send).toBe('function');
  });

  it('exposes connection status', async () => {
    const { useWebSocket } = await import('./useWebSocket');
    const { result } = renderHook(() => useWebSocket('ws://localhost'));
    expect(result.current.isConnected).toBeDefined();
  });
});
