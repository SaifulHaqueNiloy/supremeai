import { describe, it, expect, vi, afterEach } from 'vitest';
import { startAntiSleepHeartbeat } from './heartbeat';

describe('heartbeat — startAntiSleepHeartbeat', () => {
  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('pings the live endpoint after the initial 10s delay', () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200 });
    vi.stubGlobal('fetch', fetchMock);
    vi.useFakeTimers();

    startAntiSleepHeartbeat();
    expect(fetchMock).not.toHaveBeenCalled();

    vi.advanceTimersByTime(10_000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/live'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('continues pinging on the interval', () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200 });
    vi.stubGlobal('fetch', fetchMock);
    vi.useFakeTimers();

    startAntiSleepHeartbeat();
    vi.advanceTimersByTime(10 * 60 * 1000 + 10_000);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
