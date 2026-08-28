import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getDeviceFingerprint } from './deviceFingerprint';

describe('getDeviceFingerprint', () => {
  beforeEach(() => {
    // Reset any internal state if possible, though since cachedFingerprint is local we might just test idempotency
  });

  it('computes a stable fingerprint string', async () => {
    // Mock crypto.subtle.digest if not present in vitest/jsdom environment
    if (!window.crypto) {
      Object.defineProperty(window, 'crypto', { value: { subtle: {} } });
    }
    if (!window.crypto.subtle) {
      window.crypto.subtle = {} as any;
    }
    window.crypto.subtle.digest = vi.fn().mockResolvedValue(new ArrayBuffer(32));

    const fp1 = await getDeviceFingerprint();
    expect(fp1).toBeTypeOf('string');
    expect(fp1.length).toBeGreaterThan(0);

    // It should cache the result and return the same fingerprint
    const fp2 = await getDeviceFingerprint();
    expect(fp1).toBe(fp2);
  });
});
