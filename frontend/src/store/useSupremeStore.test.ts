import { describe, it, expect } from 'vitest';
import { useSupremeStore } from './useSupremeStore';

describe('useSupremeStore', () => {
  it('combines the user, workspace, ui and api slices', () => {
    const state = useSupremeStore.getState();
    expect(state).toHaveProperty('user');
    expect(state).toHaveProperty('workspace');
    expect(state).toHaveProperty('ui');
    expect(state).toHaveProperty('api');
  });
});
