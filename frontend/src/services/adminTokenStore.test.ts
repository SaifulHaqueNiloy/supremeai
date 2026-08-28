import { describe, it, expect, beforeEach } from 'vitest';

import { adminTokenStore } from './adminTokenStore';

function base64Url(obj: unknown): string {
  const json = JSON.stringify(obj);
  return Buffer.from(json)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

describe('adminTokenStore', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('getRawToken returns null when no token is stored', () => {
    expect(adminTokenStore.getRawToken()).toBeNull();
  });

  it('getRawToken returns the stored token', () => {
    localStorage.setItem('supreme_admin_jwt', 'raw.jwt.value');
    expect(adminTokenStore.getRawToken()).toBe('raw.jwt.value');
  });

  it('getDecodedToken returns null when no token is stored', () => {
    expect(adminTokenStore.getDecodedToken()).toBeNull();
  });

  it('getDecodedToken decodes a valid three-part JWT', () => {
    const token = `header.${base64Url({ sub: 'u1', role: 'admin' })}.sig`;
    localStorage.setItem('supreme_admin_jwt', token);
    const decoded = adminTokenStore.getDecodedToken();
    expect(decoded).not.toBeNull();
    expect(decoded?.sub).toBe('u1');
    expect(decoded?.role).toBe('admin');
  });

  it('getDecodedToken returns null for a malformed token', () => {
    localStorage.setItem('supreme_admin_jwt', 'not-three-parts');
    expect(adminTokenStore.getDecodedToken()).toBeNull();
  });
});
