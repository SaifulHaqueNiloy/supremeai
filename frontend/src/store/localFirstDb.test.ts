/**
 * Tests for store/localFirstDb.ts — Local-first database (offline).
 */
import { describe, it, expect } from 'vitest';

describe('localFirstDb', () => {
  it('module loads without crash', async () => {
    const mod = await import('./localFirstDb');
    expect(mod).toBeDefined();
  });

  it('exports database-related functions', async () => {
    const mod = await import('./localFirstDb');
    const keys = Object.keys(mod);
    expect(keys.length).toBeGreaterThan(0);
  });
});
