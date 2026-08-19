/**
 * MemoryService — vector memory sync, checkpoint save/load, memory context building.
 */

import { AxiosInstance } from 'axios';

export class MemoryService {
  constructor(
    private client: AxiosInstance,
    private sessionId: string,
  ) {}

  /**
   * ভেক্টর মেমোরিতে ফাইল সিঙ্ক করার ফাংশন
   * POST /memory/ingest
   * বাংলা মন্তব্য: ব্যাকএন্ড মেমরি রাউটারের prefix "/memory" (কোনো "/api" নেই)।
   */
  async syncFileToMemory(filePath: string, content: string, language: string): Promise<any> {
    try {
      const response = await this.client.post('/memory/ingest', {
        filePath,
        content,
        language,
        sessionId: this.sessionId,
        timestamp: new Date().toISOString(),
      });
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] ভেক্টর মেমোরি সিঙ্ক ব্যর্থ হয়েছে: ${error.message}`);
      return { success: false, message: error.message };
    }
  }

  async saveCheckpoint(taskId: string, stepIndex: number, state: Record<string, any>): Promise<boolean> {
    try {
      const response = await this.client.post('/memory/checkpoint', {
        task_id: taskId,
        step_index: stepIndex,
        state,
        sessionId: this.sessionId,
      });
      return response.data?.task_id === taskId;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to save checkpoint: ${error.message}`);
      return false;
    }
  }

  async loadCheckpoint(taskId: string): Promise<any | null> {
    try {
      const response = await this.client.get(`/memory/checkpoint/${taskId}`);
      return response.data ?? null;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to load checkpoint: ${error.message}`);
      return null;
    }
  }

  async buildMemoryContext(documents: string[], query: string, sessionId: string, budget = 4000): Promise<string> {
    try {
      const response = await this.client.post('/memory/context', {
        documents,
        query,
        session_id: sessionId,
        budget,
      });
      return response.data?.context || '';
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to build memory context: ${error.message}`);
      return '';
    }
  }
}
