/**
 * Tests for store/workspaceUiState.ts — Workspace UI state.
 */
import { describe, it, expect } from 'vitest';

describe('workspaceUiStateStore', () => {
  it('module loads', async () => {
    const mod = await import('./workspaceUiStateStore');
    expect(mod).toBeDefined();
  });
});
