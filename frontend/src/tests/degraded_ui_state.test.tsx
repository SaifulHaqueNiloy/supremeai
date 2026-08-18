import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiClient, ApiError, requestQueue, setApiConcurrency } from '../services/apiClient';

describe('Phase 3 M3.5: Degraded-State & Offline UI Resilience Tests', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
    requestQueue.clear();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('should handle 503 Service Unavailable gracefully without crashing', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: 'Backend node temporarily degraded (failover active)' }),
    } as unknown as Response);

    await expect(apiClient.get('/api/v1/health')).rejects.toThrow(ApiError);
    await expect(apiClient.get('/api/v1/health')).rejects.toMatchObject({
      status: 503,
      message: 'Backend node temporarily degraded (failover active)',
    });
  });

  it('should intercept 402 CostGuard budget exhaustion and wrap in structured ApiError', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 402,
      json: async () => ({ detail: 'Monthly budget cap $0.00 reached by CostGuard' }),
    } as unknown as Response);

    await expect(apiClient.post('/api/v1/agents/run', {})).rejects.toThrow(
      'Budget Limit Exceeded: Monthly budget cap $0.00 reached by CostGuard'
    );
  });

  it('should intercept 429 Rate Limit and provide user-friendly throttling error', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => ({ detail: 'Token bucket drained. Backoff 5s' }),
    } as unknown as Response);

    await expect(apiClient.get('/api/v1/metrics')).rejects.toMatchObject({
      status: 429,
      message: expect.stringContaining('Rate limit exceeded'),
    });
  });

  it('should handle 202 JIT-OTP interception without throwing unexpected exception', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => ({ message: 'JIT OTP required for privileged action', session_id: 'jit-999' }),
    } as unknown as Response);

    const result = await apiClient.post('/api/v1/admin/escalate', {});
    expect(result).toEqual({
      success: false,
      requiresOTP: true,
      message: 'JIT OTP required for privileged action',
      data: { message: 'JIT OTP required for privileged action', session_id: 'jit-999' },
    });
  });

  it('should dynamically adapt concurrency queue for low-bandwidth / degraded networks', () => {
    setApiConcurrency(1);
    expect(requestQueue.concurrency).toBe(1);

    setApiConcurrency(5);
    expect(requestQueue.concurrency).toBe(5);
  });

  it('should handle offline network failure (TypeError: Failed to fetch)', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(apiClient.get('/api/v1/status')).rejects.toThrow('Failed to fetch');
  });
});
