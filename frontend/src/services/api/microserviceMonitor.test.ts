import { describe, it, expect, vi } from 'vitest';

const apiClient = {
  get: vi.fn(),
};

vi.mock('../apiClient', () => ({ apiClient }));

const { fetchJavaWorkerHealth } = await import('./microserviceMonitor');

const offline = {
  status: 'OFFLINE',
  uptimeSeconds: 0,
  activeTasks: 0,
  queuedTasks: 0,
  memoryUsageMb: 0,
  cpuLoadPercentage: 0,
  totalTasksProcessed: 0,
};

describe('fetchJavaWorkerHealth', () => {
  it('returns the health payload from the api', async () => {
    const health = { status: 'OK', uptimeSeconds: 10, activeTasks: 1, queuedTasks: 0, memoryUsageMb: 5, cpuLoadPercentage: 2, totalTasksProcessed: 7 };
    apiClient.get.mockResolvedValueOnce(health);
    const res = await fetchJavaWorkerHealth();
    expect(apiClient.get).toHaveBeenCalledWith('/admin/microservices/java-worker/health');
    expect(res).toEqual(health);
  });

  it('falls back to offline status when the api returns null', async () => {
    apiClient.get.mockResolvedValueOnce(null);
    const res = await fetchJavaWorkerHealth();
    expect(res).toEqual(offline);
  });

  it('falls back to offline status when the api throws', async () => {
    apiClient.get.mockRejectedValueOnce(new Error('boom'));
    const res = await fetchJavaWorkerHealth();
    expect(res).toEqual(offline);
  });
});
