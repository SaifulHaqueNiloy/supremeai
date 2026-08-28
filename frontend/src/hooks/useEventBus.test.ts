import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

const { mockEmit, mockSubscribe, mockGetListenerCount } = vi.hoisted(() => ({
  mockEmit: vi.fn(),
  mockSubscribe: vi.fn(() => vi.fn()),
  mockGetListenerCount: vi.fn(() => 0),
}));

vi.mock('../lib/componentEventBus', () => ({
  eventBus: {
    emit: (...args: unknown[]) => mockEmit(...args),
    subscribe: (...args: unknown[]) => mockSubscribe(...args),
    getListenerCount: (...args: unknown[]) => mockGetListenerCount(...args),
  },
  Events: {},
}));

import { useEventBus, useEventEmitter, useEventBusMulti } from './useEventBus';

describe('useEventBus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('subscribes on mount and forwards events to the callback', () => {
    const cb = vi.fn();
    const { unmount } = renderHook(() => useEventBus('TEST_EVENT', cb));
    expect(mockSubscribe).toHaveBeenCalled();
    const wrapper = mockSubscribe.mock.calls[0][1] as (data: unknown) => void;
    act(() => {
      wrapper('payload');
    });
    expect(cb).toHaveBeenCalledWith('payload');
    unmount();
  });

  it('emit proxies to eventBus.emit', () => {
    const { result } = renderHook(() => useEventBus('E', vi.fn()));
    act(() => {
      result.current.emit('E', { a: 1 });
    });
    expect(mockEmit).toHaveBeenCalledWith('E', { a: 1 });
  });

  it('subscribe and getListenerCount proxy to eventBus', () => {
    const { result } = renderHook(() => useEventBus('E', vi.fn()));
    act(() => {
      result.current.subscribe('E', vi.fn());
      result.current.getListenerCount('E');
    });
    expect(mockSubscribe).toHaveBeenCalledWith('E', expect.any(Function));
    expect(mockGetListenerCount).toHaveBeenCalledWith('E');
  });

  it('useEventEmitter emits via eventBus', () => {
    const { result } = renderHook(() => useEventEmitter());
    act(() => {
      result.current.emit('E2', 5);
    });
    expect(mockEmit).toHaveBeenCalledWith('E2', 5);
  });

  it('useEventBusMulti subscribes to every provided event and cleans up', () => {
    const subs = [
      { event: 'A', handler: vi.fn() },
      { event: 'B', handler: vi.fn() },
    ];
    const { unmount } = renderHook(() => useEventBusMulti(subs));
    expect(mockSubscribe).toHaveBeenCalledTimes(2);
    unmount();
  });
});
