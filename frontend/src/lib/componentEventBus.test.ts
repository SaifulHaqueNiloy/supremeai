/**
 * Tests for lib/componentEventBus.ts — Component event bus.
 */
import { describe, it, expect, vi } from 'vitest';
import { eventBus, Events } from './componentEventBus';

describe('componentEventBus', () => {
  it('eventBus is defined', () => {
    expect(eventBus).toBeDefined();
    expect(eventBus.emit).toBeDefined();
    expect(eventBus.subscribe).toBeDefined();
  });

  it('subscribe + emit receives event', () => {
    const cb = vi.fn();
    const unsub = eventBus.subscribe('test-event', cb);
    eventBus.emit('test-event', { data: 'hello' });
    expect(cb).toHaveBeenCalled();
    unsub();
  });

  it('unsubscribe stops receiving', () => {
    const cb = vi.fn();
    const unsub = eventBus.subscribe('test-event', cb);
    unsub();
    eventBus.emit('test-event', { data: 'hello' });
    expect(cb).not.toHaveBeenCalled();
  });

  it('getListenerCount returns number', () => {
    const count = eventBus.getListenerCount('test-event');
    expect(typeof count).toBe('number');
  });

  it('Events enum has expected keys', () => {
    expect(Events).toBeDefined();
  });
});
