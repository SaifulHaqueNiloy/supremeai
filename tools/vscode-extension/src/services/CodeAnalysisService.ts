/**
 * CodeAnalysisService — repository analysis, error resolution, security,
 * dependency graph, health scores, and feature proposals.
 */

import { AxiosInstance } from 'axios';
import {
  CodeFlowAnalysis,
  CodeFlowAnalysisRequest,
  CodeFlowAnalysisResponse,
  DependencyGraph,
  ErrorResolutionRequest,
  ErrorResolutionResponse,
  HealthScore,
  SecurityIssue,
} from '../types';

export class CodeAnalysisService {
  constructor(
    private client: AxiosInstance,
    private sessionId: string,
  ) {}

  /**
   * Run CodeFlow analysis on repository
   * POST /api/codeflow/analyze
   */
  async analyzeRepository(request: CodeFlowAnalysisRequest): Promise<CodeFlowAnalysisResponse> {
    try {
      const response = await this.client.post<CodeFlowAnalysisResponse>('/api/codeflow/analyze', {
        ...request,
        sessionId: this.sessionId,
      });
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] CodeFlow analysis failed: ${error.message}`);
      return {
        success: false,
        analysisId: '',
        data: {
          repositoryId: '',
          files: [],
          dependencies: { nodes: [], edges: [] },
          patterns: [],
          securityIssues: [],
          healthScore: {
            score: 0,
            grade: 'F',
            breakdown: { security: 0, maintainability: 0, complexity: 0, documentation: 0, testing: 0 },
            details: [],
          },
          analysisTimestamp: new Date().toISOString(),
          status: 'failed',
        },
        message: error.message,
      };
    }
  }

  async getAnalysisResults(analysisId: string): Promise<CodeFlowAnalysis | null> {
    try {
      const response = await this.client.get<CodeFlowAnalysis>(`/api/codeflow/analysis/${analysisId}`);
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to get analysis results: ${error.message}`);
      return null;
    }
  }

  async getRepositoryAnalysis(repositoryId: string): Promise<CodeFlowAnalysis | null> {
    try {
      const response = await this.client.get<CodeFlowAnalysis>(`/api/codeflow/repository/${repositoryId}/analysis`);
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to get repository analysis: ${error.message}`);
      return null;
    }
  }

  async resolveError(request: ErrorResolutionRequest): Promise<ErrorResolutionResponse> {
    try {
      const response = await this.client.post<ErrorResolutionResponse>('/api/codeflow/error/resolve', {
        ...request,
        sessionId: this.sessionId,
      });
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Error resolution failed: ${error.message}`);
      return {
        success: false,
        rootCause: 'Unable to determine root cause',
        affectedFiles: [],
        blastRadius: [],
        suggestedFixes: [],
        confidence: 0,
      };
    }
  }

  async getSecurityIssues(repositoryId: string, severity?: string): Promise<SecurityIssue[]> {
    try {
      const response = await this.client.get<SecurityIssue[]>(
        `/api/codeflow/repository/${repositoryId}/security`,
        { params: { severity } },
      );
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to get security issues: ${error.message}`);
      return [];
    }
  }

  async getDependencyGraph(repositoryId: string): Promise<DependencyGraph | null> {
    try {
      const response = await this.client.get<DependencyGraph>(
        `/api/codeflow/repository/${repositoryId}/dependencies`,
      );
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to get dependency graph: ${error.message}`);
      return null;
    }
  }

  async getHealthScore(repositoryId: string): Promise<HealthScore | null> {
    try {
      const response = await this.client.get<HealthScore>(
        `/api/codeflow/repository/${repositoryId}/health`,
      );
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to get health score: ${error.message}`);
      return null;
    }
  }

  async registerProposedFeature(feature: any): Promise<any> {
    try {
      const response = await this.client.post('/api/features/propose', feature);
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to register proposed feature: ${error.message}`);
      return { success: false, message: error.message };
    }
  }
}
