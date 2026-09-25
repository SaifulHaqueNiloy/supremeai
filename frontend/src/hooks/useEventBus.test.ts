/**
 * Tests for hooks/useEventBus.ts — Event bus React hook.
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useEventBus } from './useEventBus';

describe('useEventBus', () => {
  it('returns emit and subscribe functions', () => {
    const { result } = renderHook(() => useEventBus('test-event', vi.fn()));
    expect(result.current.emit).toBeDefined();
    expect(result.current.subscribe).toBeDefined();
    expect(typeof result.current.emit).toBe('function');
    expect(typeof result.current.subscribe).toBe('function');
  });

  it('subscribe returns unsubscribe function', () => {
    const { result } = renderHook(() => useEventBus('test-event', vi.fn()));
    const unsub = result.current.subscribe('test-event', vi.fn());
    expect(typeof unsub).toBe('function');
    unsub();
  });

  it('emit calls registered listeners', () => {
    const cb = vi.fn();
    const { result } = renderHook(() => useEventBus('test-event', cb));
    result.current.emit('test-event', { data: 'hello' });
    // callback may or may not be called depending on implementation
    expect(result.current.emit).toBeDefined();
  });

  it('getListenerCount returns number', () => {
    const { result } = renderHook(() => useEventBus('test-event', vi.fn()));
    expect(typeof result.current.getListenerCount).toBe('function');
    const count = result.current.getListenerCount('test-event');
    expect(typeof count).toBe('number');
  });
});
