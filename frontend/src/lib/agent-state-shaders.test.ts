/**
 * Tests for lib/agent-state-shaders.ts — Agent state visual shaders.
 */
import { describe, it, expect } from 'vitest';

describe('agent-state-shaders', () => {
  it('module loads without crash', async () => {
    const mod = await import('./agent-state-shaders');
    expect(mod).toBeDefined();
  });
});
