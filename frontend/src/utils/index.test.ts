/**
 * Tests for utils/ — Shared utilities.
 */
import { describe, it, expect } from 'vitest';

describe('utils', () => {
  it('module loads', async () => {
    const mod = await import('.');
    expect(mod).toBeDefined();
  });
});
