/**
 * Tests for store/sessionCockpitStore.ts — Session cockpit state.
 */
import { describe, it, expect } from 'vitest';

describe('sessionCockpitStore', () => {
  it('module loads', async () => {
    const mod = await import('./sessionCockpitStore');
    expect(mod).toBeDefined();
  });
});
