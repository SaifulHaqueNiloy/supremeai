import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { startAntiSleepHeartbeat, pingServers } from './heartbeat';

vi.mock('../utils/api', () => ({
  getApiBaseUrl: vi.fn(() => 'https://api.test-domain.com'),
}));

describe('heartbeat', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    (global as { fetch: ReturnType<typeof vi.fn> }).fetch = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns timeout and interval ids', () => {
    const result = startAntiSleepHeartbeat();
    expect(result.timeoutId).toBeDefined();
    expect(result.intervalId).toBeDefined();
  });

  it('pings the health endpoint on schedule', async () => {
    const mockFetch = (global as { fetch: ReturnType<typeof vi.fn> }).fetch;
    mockFetch.mockResolvedValue({ ok: true } as Response);

    startAntiSleepHeartbeat();
    expect(mockFetch).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(10_000);
    expect(mockFetch).toHaveBeenCalledWith(
      'https://api.test-domain.com/api/v1/live',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('logs a warning when the health endpoint returns non-ok', async () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const mockFetch = (global as { fetch: ReturnType<typeof vi.fn> }).fetch;
    mockFetch.mockResolvedValue({ ok: false, status: 500 } as Response);

    startAntiSleepHeartbeat();
    await vi.advanceTimersByTimeAsync(10_000);

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('500')
    );
    consoleSpy.mockRestore();
  });

  it('logs a warning when the fetch throws', async () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const mockFetch = (global as { fetch: ReturnType<typeof vi.fn> }).fetch;
    mockFetch.mockRejectedValue(new Error('network down'));

    startAntiSleepHeartbeat();
    await vi.advanceTimersByTimeAsync(10_000);

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Could not reach')
    );
    consoleSpy.mockRestore();
  });
});
