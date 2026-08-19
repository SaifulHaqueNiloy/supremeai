/**
 * SupremeAI Service — thin orchestrator.
 * সমস্ত domain logic নিজ নিজ service-এ আলাদা করা হয়েছে।
 * এই ফাইলটি backward-compatible public API বজায় রাখে।
 *
 * Sub-services:
 *   - ChatService       → chat messaging, WebSocket streaming, SSE streaming
 *   - LearningService   → code edits, errors, feedback, analysis
 *   - MemoryService     → vector memory sync, checkpoints, context
 *   - CodeAnalysisService → repository analysis, security, dependencies
 */

import axios, { AxiosInstance } from 'axios';
import { AuthService } from './AuthService';
import { ChatService } from './ChatService';
import { LearningService } from './LearningService';
import { MemoryService } from './MemoryService';
import { CodeAnalysisService } from './CodeAnalysisService';
import {
  ChatMessage,
  ChatRequest,
  ChatResponse,
  CodeEdit,
  CodeFlowAnalysis,
  CodeFlowAnalysisRequest,
  CodeFlowAnalysisResponse,
  DependencyGraph,
  ErrorReport,
  ErrorResolutionRequest,
  ErrorResolutionResponse,
  HealthScore,
  LearningResponse,
  SecurityIssue,
  SupremeAIConfig,
  SuggestionFeedback,
} from '../types';

export class SupremeAIService {
  private client: AxiosInstance;
  private config: SupremeAIConfig;
  private sessionId: string;

  // Sub-services
  private chat: ChatService;
  private learning: LearningService;
  private memory: MemoryService;
  private codeAnalysis: CodeAnalysisService;

  constructor(config: SupremeAIConfig) {
    this.config = config;
    this.sessionId = this.generateSessionId();

    this.client = axios.create({
      baseURL: config.backendUrl,
      timeout: 10000,
      headers: { 'Content-Type': 'application/json' },
    });

    // Auth interceptor
    this.client.interceptors.request.use((request) => {
      const authService = AuthService.getInstance();
      if (authService && authService.isAuthenticated()) {
        const token = authService.getToken();
        if (token) {
          request.headers['Authorization'] = `Bearer ${token}`;
        }
      }
      console.log(`[SupremeAI] Sending ${request.method?.toUpperCase()} to ${request.url}`);
      return request;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error(`[SupremeAI] API Error: ${error.message}`);
        return Promise.reject(error);
      },
    );

    // Compose sub-services
    this.chat = new ChatService(this.client, this.config, this.sessionId);
    this.learning = new LearningService(this.client, this.config, this.sessionId);
    this.memory = new MemoryService(this.client, this.sessionId);
    this.codeAnalysis = new CodeAnalysisService(this.client, this.sessionId);
  }

  // ─── Learning delegates ──────────────────────────────────────────────────────

  async sendCodeEdit(edit: CodeEdit): Promise<LearningResponse> {
    return this.learning.sendCodeEdit(edit);
  }

  async reportError(error: ErrorReport): Promise<LearningResponse> {
    return this.learning.reportError(error);
  }

  async sendFeedback(feedback: SuggestionFeedback): Promise<LearningResponse> {
    return this.learning.sendFeedback(feedback);
  }

  async sendCodeAnalysis(filePath: string, code: string, language: string): Promise<LearningResponse> {
    return this.learning.sendCodeAnalysis(filePath, code, language);
  }

  async getLearningStats(): Promise<any> {
    return this.learning.getLearningStats();
  }

  // ─── Chat delegates ───────────────────────────────────────────────────────────

  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.chat.sendChatMessage(request);
  }

  async streamChatResponse(request: ChatRequest, onToken?: (token: string) => void): Promise<string> {
    return this.chat.streamChatResponse(request, onToken);
  }

  async streamChatOverWs(request: ChatRequest, onToken?: (token: string) => void): Promise<string> {
    return this.chat.streamChatOverWs(request, onToken);
  }

  async streamChatCompletion(request: ChatRequest, onToken?: (token: string) => void): Promise<string> {
    return this.chat.streamChatCompletion(request, onToken);
  }

  async getChatHistory(sessionId?: string): Promise<ChatMessage[]> {
    return this.chat.getChatHistory(sessionId);
  }

  async clearChatHistory(sessionId?: string): Promise<boolean> {
    return this.chat.clearChatHistory(sessionId);
  }

  // ─── Memory delegates ─────────────────────────────────────────────────────────

  async syncFileToMemory(filePath: string, content: string, language: string): Promise<any> {
    return this.memory.syncFileToMemory(filePath, content, language);
  }

  async saveCheckpoint(taskId: string, stepIndex: number, state: Record<string, any>): Promise<boolean> {
    return this.memory.saveCheckpoint(taskId, stepIndex, state);
  }

  async loadCheckpoint(taskId: string): Promise<any | null> {
    return this.memory.loadCheckpoint(taskId);
  }

  async buildMemoryContext(documents: string[], query: string, sessionId: string, budget = 4000): Promise<string> {
    return this.memory.buildMemoryContext(documents, query, sessionId, budget);
  }

  // ─── Inline completions ───────────────────────────────────────────────────────

  async getInlineCompletions(
    prefix: string,
    suffix: string,
    filePath: string,
    language: string,
  ): Promise<{ success: boolean; suggestions: string[] }> {
    try {
      const response = await this.client.post<{ success: boolean; suggestions: string[] }>('/api/chat/completion', {
        prefix,
        suffix,
        filePath,
        language,
        sessionId: this.sessionId,
      });
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Inline completion request failed: ${error.message}`);
      return { success: false, suggestions: [] };
    }
  }

  // ─── Self-healing ─────────────────────────────────────────────────────────────

  async requestSelfHealing(payload: {
    filePath: string;
    message: string;
    lineNumber: number;
    codeContext: string;
    languageId: string;
  }): Promise<{ fixedCode?: string; success: boolean; message?: string }> {
    try {
      const response = await this.client.post('/api/v1/swarm/execute-healing', payload);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 429) {
        return { success: false, message: 'Rate limit exceeded (Cooldown Active). Please wait.' };
      }
      console.error(`[SupremeAI] Failed to request self-healing: ${error.message}`);
      return { success: false, message: error.message };
    }
  }

  // ─── Code analysis delegates ──────────────────────────────────────────────────

  async analyzeRepository(request: CodeFlowAnalysisRequest): Promise<CodeFlowAnalysisResponse> {
    return this.codeAnalysis.analyzeRepository(request);
  }

  async getAnalysisResults(analysisId: string): Promise<CodeFlowAnalysis | null> {
    return this.codeAnalysis.getAnalysisResults(analysisId);
  }

  async getRepositoryAnalysis(repositoryId: string): Promise<CodeFlowAnalysis | null> {
    return this.codeAnalysis.getRepositoryAnalysis(repositoryId);
  }

  async resolveError(request: ErrorResolutionRequest): Promise<ErrorResolutionResponse> {
    return this.codeAnalysis.resolveError(request);
  }

  async getSecurityIssues(repositoryId: string, severity?: string): Promise<SecurityIssue[]> {
    return this.codeAnalysis.getSecurityIssues(repositoryId, severity);
  }

  async getDependencyGraph(repositoryId: string): Promise<DependencyGraph | null> {
    return this.codeAnalysis.getDependencyGraph(repositoryId);
  }

  async getHealthScore(repositoryId: string): Promise<HealthScore | null> {
    return this.codeAnalysis.getHealthScore(repositoryId);
  }

  async registerProposedFeature(feature: any): Promise<any> {
    return this.codeAnalysis.registerProposedFeature(feature);
  }

  // ─── Utilities ────────────────────────────────────────────────────────────────

  updateConfig(newConfig: Partial<SupremeAIConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  getSessionId(): string {
    return this.sessionId;
  }

  private generateSessionId(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(7);
    return `vscode-${timestamp}-${random}`;
  }
}

// ─── Singleton ────────────────────────────────────────────────────────────────

let supremeAIService: SupremeAIService | null = null;

export function getSupremeAIService(config?: SupremeAIConfig): SupremeAIService {
  if (!supremeAIService && config) {
    supremeAIService = new SupremeAIService(config);
  }
  if (!supremeAIService) {
    throw new Error('SupremeAIService not initialized. Call getSupremeAIService(config) first.');
  }
  return supremeAIService;
}

export function setSupremeAIService(service: SupremeAIService): void {
  supremeAIService = service;
}
