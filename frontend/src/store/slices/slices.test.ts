import { describe, it, expect } from 'vitest';
import { createApiSlice } from './apiSlice';
import { createUiSlice } from './uiSlice';
import { createUserSlice } from './userSlice';
import { createWorkspaceSlice } from './workspaceSlice';

const noop = (() => {}) as never;

describe('store slices', () => {
  it('createApiSlice exposes a null api by default', () => {
    expect(createApiSlice(noop).api).toBeNull();
  });

  it('createUiSlice exposes a null ui by default', () => {
    expect(createUiSlice(noop).ui).toBeNull();
  });

  it('createUserSlice exposes a null user by default', () => {
    expect(createUserSlice(noop).user).toBeNull();
  });

  it('createWorkspaceSlice exposes a null workspace by default', () => {
    expect(createWorkspaceSlice(noop).workspace).toBeNull();
  });
});
