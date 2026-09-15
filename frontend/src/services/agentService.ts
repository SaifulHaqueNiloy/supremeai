// Agent Operations Service for SupremeAI 2.0
// বাংলা মন্তব্য: এজেন্ট ডিপার্টমেন্ট, টাস্ক এক্সেকিউশন ও এজেন্টদের তথ্য আনার জন্য ব্যবহৃত সার্ভিস।

import { apiClient } from './apiClient';

export interface AgentTask {
  id?: string;
  name?: string;
  status: string;
  result?: string;
  message?: string;
  code?: string;
  source?: 'ai_api' | 'memory';
}

export const agentService = {
  // বাংলা মন্তব্য: ফিক্স (ERR-A02, defect register 2026-09-15) — ব্যাকএন্ড রাউটার prefix প্লুরাল
  // `/api/v1/agents` (backend/api/routes/agent.py), তাই সিঙ্গুলার URL 404 দিত। এখন প্লুরাল
  // এন্ডপয়েন্ট ব্যবহার হচ্ছে এবং backend AgentTaskRequest contract অনুযায়ী বাধ্যতামূলক
  // `task_id` পাঠানো হচ্ছে (agentId + per-execution UUID দিয়ে ইউনিক correlation)।
  executeAgentTask: async (agentId: string, instruction: string): Promise<AgentTask> => {
    return apiClient.post<AgentTask>('/api/v1/agents/execute', {
      task_id: `${agentId}-${crypto.randomUUID()}`,
      prompt: instruction,
      auto_execute: false,
    });
  },

  listAgents: async (): Promise<unknown[]> => {
    return apiClient.get<{ agents: unknown[] }>('/api/agents/').then((response) => response.agents);
  },

  getAgentStatus: async (agentId: string): Promise<{ status: string }> => {
    return apiClient.get<{ status: string }>(`/api/agents/${agentId}/status`);
  },
};
