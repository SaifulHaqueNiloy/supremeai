/**
 * LearningService — code edit, error reporting, feedback, and learning stats.
 */

import { AxiosInstance } from 'axios';
import {
  CodeEdit,
  ErrorReport,
  LearningResponse,
  LearningUpload,
  SupremeAIConfig,
  SuggestionFeedback,
} from '../types';

export class LearningService {
  constructor(
    private client: AxiosInstance,
    private config: SupremeAIConfig,
    private sessionId: string,
  ) {}

  /**
   * Send code edit event for learning
   * POST /api/knowledge/learn
   */
  async sendCodeEdit(edit: CodeEdit): Promise<LearningResponse> {
    if (!this.config.enableRealTimeLearning) {
      return { success: false, message: 'Real-time learning disabled' };
    }
    try {
      const payload: LearningUpload = {
        type: 'CODE_EDIT',
        data: edit,
        sessionId: this.sessionId,
      };
      const response = await this.client.post<LearningResponse>('/api/knowledge/learn', payload);
      console.log(`[SupremeAI] Code edit learned: ${edit.taskId}`);
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to send code edit: ${error.message}`);
      return { success: false, message: error.message || 'Failed to send code edit' };
    }
  }

  /**
   * Report error for learning
   * POST /api/knowledge/failure
   */
  async reportError(error: ErrorReport): Promise<LearningResponse> {
    if (!this.config.autoReportErrors) {
      return { success: false, message: 'Auto-error reporting disabled' };
    }
    try {
      const payload: LearningUpload = {
        type: 'ERROR_REPORT',
        data: error,
        sessionId: this.sessionId,
      };
      const response = await this.client.post<LearningResponse>('/api/knowledge/failure', payload);
      console.log(`[SupremeAI] Error reported: ${error.errorType} at ${error.filePath}:${error.lineNumber}`);
      return response.data;
    } catch (err: any) {
      console.error(`[SupremeAI] Failed to report error: ${err.message}`);
      return { success: false, message: err.message || 'Failed to report error' };
    }
  }

  /**
   * Send suggestion feedback (accept/reject)
   * POST /api/knowledge/feedback
   */
  async sendFeedback(feedback: SuggestionFeedback): Promise<LearningResponse> {
    try {
      const payload: LearningUpload = {
        type: 'SUGGESTION_FEEDBACK',
        data: feedback,
        sessionId: this.sessionId,
      };
      const response = await this.client.post<LearningResponse>('/api/knowledge/feedback', payload);
      console.log(`[SupremeAI] Feedback sent: ${feedback.accepted ? 'accepted' : 'rejected'}`);
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to send feedback: ${error.message}`);
      return { success: false, message: error.message || 'Failed to send feedback' };
    }
  }

  /**
   * Send code analysis snapshot
   * POST /api/knowledge/analysis
   */
  async sendCodeAnalysis(filePath: string, code: string, language: string): Promise<LearningResponse> {
    if (!this.config.enableRealTimeLearning) {
      return { success: false, message: 'Real-time learning disabled' };
    }
    try {
      const analysis = {
        filePath,
        code,
        language,
        timestamp: new Date().toISOString(),
        metrics: this.analyzeCodeMetrics(code, language),
      };
      const response = await this.client.post<LearningResponse>('/api/knowledge/analysis', {
        ...analysis,
        sessionId: this.sessionId,
      });
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to send analysis: ${error.message}`);
      return { success: false, message: error.message };
    }
  }

  /**
   * Get learning statistics
   * GET /api/knowledge/stats
   */
  async getLearningStats(): Promise<any> {
    try {
      const response = await this.client.get('/api/knowledge/stats');
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to get stats: ${error.message}`);
      return null;
    }
  }

  analyzeCodeMetrics(code: string, language: string): Record<string, number> {
    const lines = code.split('\n');
    return {
      linesOfCode: lines.length,
      nonEmptyLines: lines.filter((l) => l.trim().length > 0).length,
      commentLines:
        language === 'typescript' || language === 'javascript'
          ? lines.filter((l) => l.trim().startsWith('//') || l.trim().startsWith('/*')).length
          : 0,
      complexityEstimate: this.estimateComplexity(code),
    };
  }

  estimateComplexity(code: string): number {
    const decisionPoints = (code.match(/\b(if|else|for|while|switch|case|catch)\b/g) || []).length;
    return decisionPoints + 1;
  }
}
