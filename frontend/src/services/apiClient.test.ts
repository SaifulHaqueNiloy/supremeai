import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient, setApiConcurrency } from './apiClient';

// Mock getApiBaseUrl
vi.mock('../utils/api', () => ({
  getApiBaseUrl: () => 'https://api.test-domain.com'
}));

// Mock useAdminStore
vi.mock('../store/adminStore', () => ({
  useAdminStore: {
    getState: vi.fn(() => ({
      adminAuthenticated: true,
      handleAdminLogout: vi.fn(),
    }))
  }
}));

describe('apiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    setApiConcurrency(3);
  });

  it('should include credentials and process successful response', async () => {
    const mockResponse = { data: 'success' };
     
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await apiClient.get('/test');

    expect(global.fetch).toHaveBeenCalledWith('https://api.test-domain.com/test', expect.objectContaining({
      credentials: 'include',
      headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      method: 'GET'
    }));
    expect(result).toEqual(mockResponse);
  });

  it('should throw ApiError with status 401 on unauthorized access', async () => {
     
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Unauthorized' }),
    });

    await expect(apiClient.get('/secure')).rejects.toThrow('Unauthorized');
  });

  it('does not clear the persisted login for a feature endpoint 401', async () => {
    localStorage.setItem('supremeai_auth_token', 'persisted-token');
     
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 401,
      url: 'https://api.test-domain.com/api/v1/projects',
      json: async () => ({ detail: 'Unauthorized' }),
    });

    await expect(apiClient.get('/api/v1/projects')).rejects.toThrow('Unauthorized');
    expect(localStorage.getItem('supremeai_auth_token')).toBe('persisted-token');
  });

  it('clears the persisted login when auth validation returns 401', async () => {
    localStorage.setItem('supremeai_auth_token', 'expired-token');
     
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 401,
      url: 'https://api.test-domain.com/api/v1/auth/me',
      json: async () => ({ detail: 'Unauthorized' }),
    });

    await expect(apiClient.get('/api/v1/auth/me')).rejects.toThrow('Unauthorized');
    expect(localStorage.getItem('supremeai_auth_token')).toBeNull();
  });

  it('should throw ApiError with status 429 on rate limit', async () => {
     
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 429,
      json: async () => ({ detail: 'Too Many Requests' }),
    });

    await expect(apiClient.get('/rate-limit')).rejects.toThrow(/Rate limit exceeded/);
  });
});
