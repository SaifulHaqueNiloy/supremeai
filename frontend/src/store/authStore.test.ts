import { describe, it, expect, vi, beforeEach } from 'vitest';

const { postMock, getMock, updateTokenCache } = vi.hoisted(() => ({
  postMock: vi.fn(),
  getMock: vi.fn(),
  updateTokenCache: vi.fn(),
}));

vi.mock('../services/apiClient', () => ({
  apiClient: {
    post: (...args: unknown[]) => postMock(...args),
    get: (...args: unknown[]) => getMock(...args),
  },
  updateTokenCache,
}));

import { useAuthStore, AuthStatus } from './authStore';

const token = (payload: Record<string, unknown>) =>
  `header.${Buffer.from(JSON.stringify(payload)).toString('base64').replace(/=/g, '')}.sig`;

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    useAuthStore.setState({ status: AuthStatus.UNINITIALIZED, user: null });
  });

  it('logs in, stores the token and sets the user', async () => {
    postMock.mockResolvedValue({ access_token: 'tok', user_id: 'u1' });
    await useAuthStore.getState().login('a@b.com', 'pw');
    expect(localStorage.getItem('supremeai_auth_token')).toBe('tok');
    expect(updateTokenCache).toHaveBeenCalledWith('tok');
    expect(useAuthStore.getState().status).toBe(AuthStatus.LOGGED_IN);
    expect(useAuthStore.getState().user?.email).toBe('a@b.com');
  });

  it('registers and logs the user in', async () => {
    postMock.mockResolvedValue({ access_token: 'tok2', user_id: 'u2' });
    await useAuthStore.getState().register('a@b.com', 'Alice', 'pw');
    expect(useAuthStore.getState().status).toBe(AuthStatus.LOGGED_IN);
    expect(useAuthStore.getState().user?.name).toBe('Alice');
  });

  it('propagates login errors', async () => {
    postMock.mockRejectedValue(new Error('bad creds'));
    await expect(useAuthStore.getState().login('a@b.com', 'pw')).rejects.toThrow('bad creds');
    expect(useAuthStore.getState().status).toBe(AuthStatus.UNINITIALIZED);
  });

  it('logs out and clears persisted state', async () => {
    postMock.mockResolvedValue({ access_token: 'tok', user_id: 'u1' });
    await useAuthStore.getState().login('a@b.com', 'pw');
    useAuthStore.getState().logout();
    expect(localStorage.getItem('supremeai_auth_token')).toBeNull();
    expect(updateTokenCache).toHaveBeenCalledWith(null);
    expect(useAuthStore.getState().status).toBe(AuthStatus.LOGGED_OUT);
    expect(useAuthStore.getState().user).toBeNull();
  });

  it('initializes as logged out when no token exists', async () => {
    await useAuthStore.getState().initialize();
    expect(useAuthStore.getState().status).toBe(AuthStatus.LOGGED_OUT);
  });

  it('initializes optimistically from a valid token and refreshes via /me', async () => {
    const tok = token({ email: 'me@x.com', name: 'Me', sub: 'u9' });
    localStorage.setItem('supremeai_auth_token', tok);
    getMock.mockResolvedValue({ email: 'me@x.com', user_id: 'u9', role: 'admin' });
    await useAuthStore.getState().initialize();
    expect(useAuthStore.getState().status).toBe(AuthStatus.LOGGED_IN);
    expect(useAuthStore.getState().user?.email).toBe('me@x.com');
  });

  it('logs out on initialize when /me returns 401', async () => {
    const tok = token({ email: 'me@x.com' });
    localStorage.setItem('supremeai_auth_token', tok);
    getMock.mockRejectedValue({ status: 401 });
    await useAuthStore.getState().initialize();
    expect(useAuthStore.getState().status).toBe(AuthStatus.LOGGED_OUT);
  });

  it('keeps the session on a transient initialize error', async () => {
    const tok = token({ email: 'me@x.com', name: 'Me' });
    localStorage.setItem('supremeai_auth_token', tok);
    getMock.mockRejectedValue({ status: 500 });
    await useAuthStore.getState().initialize();
    expect(useAuthStore.getState().status).toBe(AuthStatus.LOGGED_IN);
  });
});
