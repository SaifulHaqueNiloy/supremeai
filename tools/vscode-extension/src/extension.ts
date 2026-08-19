/**
 * SupremeAI VS Code Extension — Thin Entry Point
 * সমস্ত command ও provider registration এখন activation/ মডিউলে।
 */

import * as vscode from 'vscode';
import { SupremeAIService, setSupremeAIService } from './services/SupremeAIService';
import { AuthService } from './services/AuthService';
import { AuthHandler } from './handlers/AuthHandler';
import { CodeEditHandler } from './handlers/CodeEditHandler';
import { ErrorHandler } from './handlers/ErrorHandler';
import { FeedbackHandler } from './handlers/FeedbackHandler';
import { CodeFlowHandler, setCodeFlowHandler } from './handlers/CodeFlowHandler';
import { SupremeAIConfig } from './types';
import { SupremeWebviewProvider } from './providers/SupremeWebviewProvider';
import { AIService, getAIService, setAIService } from './ai/AIService';
import { CodeGenerationService, setCodeGenerationService } from './ai/CodeGenerationService';
import { CodeReviewService, setCodeReviewService } from './ai/CodeReviewService';
import { detectOtherAiAgents } from './agentDetector';
import { registerSwarmCommands } from './services/SwarmPipelineProvider';
import { registerCommands } from './activation/registerCommands';
import { registerChatProvider, registerStatusBar, registerInlineCompletionProvider } from './activation/registerProviders';

let isInitialized = false;

export async function activate(context: vscode.ExtensionContext) {
  console.log('[SupremeAI] VS Code Extension activating...');

  if (isInitialized) {
    console.log('[SupremeAI] Extension already initialized, skipping duplicate activation');
    return;
  }

  const config = vscode.workspace.getConfiguration('supremeai');
  const backendUrl = config.get<string>('backendUrl', 'https://supremeai-worker.paykaribazaronline.workers.dev');

  const supremeConfig: SupremeAIConfig = {
    backendUrl,
    enableRealTimeLearning: config.get<boolean>('enableRealTimeLearning', true),
    autoReportErrors: config.get<boolean>('autoReportErrors', true),
  };

  const supremeAIService = new SupremeAIService(supremeConfig);
  setSupremeAIService(supremeAIService);

  const aiService = getAIService();
  setAIService(aiService);
  setCodeGenerationService(new CodeGenerationService());
  setCodeReviewService(new CodeReviewService());

  // Auth initialization — NON-BLOCKING
  // ⚠️ Do NOT await — Render backend cold start can take 60+ seconds
  const auth = AuthService.getInstance(supremeConfig, context.secrets);
  Promise.race([
    auth.initialize().then(() => auth.loginAsGuest()),
    new Promise<void>((resolve) => setTimeout(resolve, 5000)),
  ]).catch((err) => {
    console.warn('[SupremeAI] Auth init warning (non-critical):', err);
  });

  AuthHandler.registerAuthCallback(context);

  // Core handlers
  const editHandler = new CodeEditHandler(context);
  const errHandler = new ErrorHandler(context);
  const fbHandler = new FeedbackHandler(context);
  const codeFlowHandler = new CodeFlowHandler(context);
  setCodeFlowHandler(codeFlowHandler);

  editHandler.register();
  errHandler.register();
  fbHandler.register();
  codeFlowHandler.register();

  // Providers
  registerChatProvider(context);
  registerInlineCompletionProvider(context, supremeAIService, fbHandler);
  registerStatusBar(context);

  // Recipe / webview provider
  const recipeProvider = new SupremeWebviewProvider(context.extensionUri);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(SupremeWebviewProvider.viewType, recipeProvider),
  );

  // Commands & Swarm
  registerCommands(context, supremeAIService, codeFlowHandler);
  registerSwarmCommands(context);

  // Auto-focus chat panel
  setTimeout(() => {
    vscode.commands.executeCommand('supremeaiChat.focus');
  }, 1500);

  // Optional: agent detection
  if (config.get<boolean>('enableAgentDetection', false)) {
    setTimeout(() => {
      const agents = detectOtherAiAgents();
      if (agents.length > 0) {
        supremeAIService.sendCodeAnalysis(
          'env-discovery',
          `Detected AI Agents in environment: ${agents.join(', ')}`,
          'system-meta',
        );
      }
    }, 5000);
  }

  isInitialized = true;
  console.log('[SupremeAI] Extension activated with essential services only');
}

export function deactivate() {
  console.log('[SupremeAI] VS Code Extension deactivating...');
  isInitialized = false;
}