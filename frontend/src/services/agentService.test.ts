import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./apiClient', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

import { agentService } from './agentService';
import { apiClient } from './apiClient';

describe('agentService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('executeAgentTask posts the instruction', async () => {
    (apiClient.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: '1',
      name: 't',
      status: 'done',
    });
    const res = await agentService.executeAgentTask('a1', 'do it');
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/agent/execute', {
      prompt: 'do it',
      project_id: 'a1',
    });
    expect(res.status).toBe('done');
  });

  it('listAgents gets the agents endpoint', async () => {
    (apiClient.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      agents: [{ id: 'a' }],
    });
    const res = await agentService.listAgents();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/agents/');
    expect(res).toHaveLength(1);
  });

  it('getAgentStatus hits the status endpoint', async () => {
    (apiClient.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      status: 'running',
    });
    const res = await agentService.getAgentStatus('a1');
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/agents/a1/status');
    expect(res.status).toBe('running');
  });
});
