/**
 * registerCommands — সমস্ত VS Code command registrations এখানে।
 * extension.ts থেকে আলাদা করা হয়েছে পরিষ্কার কোড বজায় রাখতে।
 */

import * as vscode from 'vscode';
import { SupremeAIService } from '../services/SupremeAIService';
import { AuthService } from '../services/AuthService';
import { CodeFlowHandler } from '../handlers/CodeFlowHandler';
import { VisualizationHandler } from '../handlers/VisualizationHandler';
import { EnhancedAIService } from '../ai/EnhancedAIService';
import { SecurityScanner } from '../security/SecurityScanner';
import { PerformanceMonitor } from '../performance/PerformanceMonitor';

function escapeHtml(value: string): string {
  return String(value).replace(/[&<>"']/g, (c) => {
    switch (c) {
      case '&': return '&amp;';
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '"': return '&quot;';
      case '\'': return '&#39;';
      default: return c;
    }
  });
}

export function registerCommands(
  context: vscode.ExtensionContext,
  supremeAIService: SupremeAIService,
  codeFlowHandler: CodeFlowHandler,
): void {
  // Lazily-initialized heavy services
  let visualizationHandler: VisualizationHandler | undefined;
  let enhancedAIService: EnhancedAIService | undefined;
  let securityScanner: SecurityScanner | undefined;
  let performanceMonitor: PerformanceMonitor | undefined;

  const forceLearnCommand = vscode.commands.registerCommand('supremeai.forceLearn', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showWarningMessage('No active editor to learn from'); return; }
    try {
      await supremeAIService.sendCodeAnalysis(editor.document.fileName, editor.document.getText(), editor.document.languageId);
      vscode.window.showInformationMessage('Code analysis sent for learning');
    } catch (error) {
      vscode.window.showErrorMessage(`Failed to send code analysis: ${error instanceof Error ? error.message : String(error)}`);
    }
  });

  const explainCodeCommand = vscode.commands.registerCommand('supremeai.aiExplain', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showWarningMessage('No active editor selected.'); return; }
    const text = editor.selection.isEmpty ? editor.document.getText() : editor.document.getText(editor.selection);
    if (!text.trim()) { vscode.window.showWarningMessage('No code selected to explain.'); return; }
    vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Explaining Code...', cancellable: false }, async () => {
      try {
        const response = await supremeAIService.sendChatMessage({ message: `Please explain the following code in detail:\n\n\`\`\`${editor.document.languageId}\n${text}\n\`\`\``, sessionId: supremeAIService.getSessionId() });
        const panel = vscode.window.createWebviewPanel('supremeaiExplanation', 'Code Explanation', vscode.ViewColumn.Two, {});
        panel.webview.html = `<html><body><pre style="white-space: pre-wrap; font-family: sans-serif; padding: 15px;">${escapeHtml(response.response)}</pre></body></html>`;
      } catch (error) { vscode.window.showErrorMessage(`Failed to explain code: ${error}`); }
    });
  });

  const reviewCodeCommand = vscode.commands.registerCommand('supremeai.aiReview', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showWarningMessage('No active editor selected.'); return; }
    const text = editor.selection.isEmpty ? editor.document.getText() : editor.document.getText(editor.selection);
    if (!text.trim()) { vscode.window.showWarningMessage('No code selected to review.'); return; }
    vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Reviewing Code...', cancellable: false }, async () => {
      try {
        const response = await supremeAIService.sendChatMessage({ message: `Please review the following code for bugs, style issues, and performance optimizations:\n\n\`\`\`${editor.document.languageId}\n${text}\n\`\`\``, sessionId: supremeAIService.getSessionId() });
        const panel = vscode.window.createWebviewPanel('supremeaiReview', 'Code Review', vscode.ViewColumn.Two, {});
        panel.webview.html = `<html><body><pre style="white-space: pre-wrap; font-family: sans-serif; padding: 15px;">${escapeHtml(response.response)}</pre></body></html>`;
      } catch (error) { vscode.window.showErrorMessage(`Failed to review code: ${error}`); }
    });
  });

  const loginAsGuestCommand = vscode.commands.registerCommand('supremeai.loginAsGuest', async () => {
    const auth = AuthService.getInstance();
    if (auth) await auth.loginAsGuest();
  });

  const loginCommand = vscode.commands.registerCommand('supremeai.login', async () => {
    const auth = AuthService.getInstance();
    if (auth) await auth.login();
  });

  const logoutCommand = vscode.commands.registerCommand('supremeai.logout', async () => {
    const auth = AuthService.getInstance();
    if (auth) await auth.logout();
  });

  const generateCodeCommand = vscode.commands.registerCommand('supremeai.generateCode', async () => {
    if (!enhancedAIService) enhancedAIService = new EnhancedAIService(supremeAIService);
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showWarningMessage('No active editor selected.'); return; }
    const text = editor.selection.isEmpty ? editor.document.getText() : editor.document.getText(editor.selection);
    if (!text.trim()) { vscode.window.showWarningMessage('No code selected.'); return; }
    const requirement = await vscode.window.showInputBox({ prompt: 'Enter code generation requirements:' });
    if (!requirement) return;
    vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Generating Code...', cancellable: false }, async () => {
      try {
        const generatedCode = await enhancedAIService!.generateCode(text, requirement);
        const panel = vscode.window.createWebviewPanel('supremeaiGeneratedCode', 'Generated Code', vscode.ViewColumn.Two, {});
        panel.webview.html = `<html><body><pre style="white-space: pre-wrap; font-family: sans-serif; padding: 15px;">${escapeHtml(generatedCode)}</pre></body></html>`;
      } catch (error) { vscode.window.showErrorMessage(`Failed to generate code: ${error}`); }
    });
  });

  const suggestRefactoringCommand = vscode.commands.registerCommand('supremeai.suggestRefactoring', async () => {
    if (!enhancedAIService) enhancedAIService = new EnhancedAIService(supremeAIService);
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showWarningMessage('No active editor selected.'); return; }
    const text = editor.selection.isEmpty ? editor.document.getText() : editor.document.getText(editor.selection);
    if (!text.trim()) { vscode.window.showWarningMessage('No code selected.'); return; }
    vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Analyzing Refactoring Options...', cancellable: false }, async () => {
      try {
        const suggestions = await enhancedAIService!.suggestRefactoring(text, editor.document.languageId);
        const panel = vscode.window.createWebviewPanel('supremeaiRefactoringSuggestions', 'Refactoring Suggestions', vscode.ViewColumn.Two, {});
        const suggestionsHtml = suggestions.map((s) => `<li>${escapeHtml(s)}</li>`).join('');
        panel.webview.html = `<html><body><ul>${suggestionsHtml}</ul></body></html>`;
      } catch (error) { vscode.window.showErrorMessage(`Failed to suggest refactoring: ${error}`); }
    });
  });

  const performSecurityScanCommand = vscode.commands.registerCommand('supremeai.performSecurityScan', async () => {
    if (!securityScanner) securityScanner = new SecurityScanner(supremeAIService);
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showWarningMessage('No active editor selected.'); return; }
    vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Performing Security Scan...', cancellable: false }, async () => {
      try {
        const issues = await securityScanner!.scanFile(editor.document);
        if (issues.length === 0) { vscode.window.showInformationMessage('No security issues found.'); return; }
        const panel = vscode.window.createWebviewPanel('supremeaiSecurityIssues', 'Security Issues Found', vscode.ViewColumn.Two, {});
        const issuesHtml = issues.map((i) => `<li><strong>${i.severity.toUpperCase()}:</strong> ${escapeHtml(i.description)}</li>`).join('');
        panel.webview.html = `<html><body><h3>Security Issues Found:</h3><ul>${issuesHtml}</ul></body></html>`;
      } catch (error) { vscode.window.showErrorMessage(`Failed to perform security scan: ${error}`); }
    });
  });

  const analyzePerformanceCommand = vscode.commands.registerCommand('supremeai.analyzePerformance', async () => {
    if (!performanceMonitor) performanceMonitor = new PerformanceMonitor(supremeAIService);
    const editor = vscode.window.activeTextEditor;
    if (!editor) { vscode.window.showWarningMessage('No active editor selected.'); return; }
    const text = editor.selection.isEmpty ? editor.document.getText() : editor.document.getText(editor.selection);
    if (!text.trim()) { vscode.window.showWarningMessage('No code selected.'); return; }
    vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Analyzing Performance...', cancellable: false }, async () => {
      try {
        const insights = await performanceMonitor!.analyzePerformance(text, editor.document.languageId);
        const panel = vscode.window.createWebviewPanel('supremeaiPerformanceInsights', 'Performance Insights', vscode.ViewColumn.Two, {});
        panel.webview.html = `<html><body><pre style="white-space: pre-wrap; font-family: sans-serif; padding: 15px;">${escapeHtml(JSON.stringify(insights, null, 2))}</pre></body></html>`;
      } catch (error) { vscode.window.showErrorMessage(`Failed to analyze performance: ${error}`); }
    });
  });

  const showDependencyGraphCommand = vscode.commands.registerCommand('supremeai.showDependencyGraph', async () => {
    const providers = vscode.window.visibleTextEditors;
    if (providers.length > 0) {
      await vscode.commands.executeCommand('supremeaiDependencyGraph.focus');
    } else {
      vscode.window.showInformationMessage('Dependency Graph view is registered in the sidebar.');
    }
  });

  const openChatCommand = vscode.commands.registerCommand('supremeai.openChat', () => {
    vscode.commands.executeCommand('workbench.view.extension.supremeai-sidebar');
    vscode.commands.executeCommand('supremeaiChat.focus');
  });

  const analyzeCodeFlowCommand = vscode.commands.registerCommand('supremeai.analyzeCodeFlow', () => {
    if (codeFlowHandler) codeFlowHandler.analyzeCodeFlow();
  });

  const visualizationCommand = vscode.commands.registerCommand('supremeai.visualizeCode', async () => {
    if (!visualizationHandler) {
      visualizationHandler = new VisualizationHandler(context, supremeAIService);
      visualizationHandler.register();
    }
  });

  const aiCompleteCommand = vscode.commands.registerCommand('supremeai.aiComplete', async () => {
    vscode.window.showInformationMessage('AI Code Completion is provided inline as you type. Just keep typing and suggestions appear automatically.');
  });

  const createProjectCommand = vscode.commands.registerCommand('supremeai.createProject', async () => {
    const name = await vscode.window.showInputBox({ prompt: 'Enter the new project name:' });
    if (!name) return;
    vscode.window.showInformationMessage(`Project creation ("${name}") is managed from the SupremeAI Web Dashboard. Open Settings to configure your backend.`);
  });

  const openExtensionSettingsCommand = vscode.commands.registerCommand('supremeai.openExtensionSettings', () => {
    vscode.commands.executeCommand('workbench.action.openSettings', '@ext:supremeai.supremeai-vscode');
  });

  const reportErrorCommand = vscode.commands.registerCommand('supremeai.reportError', async () => {
    try {
      const errorText = await vscode.window.showInputBox({ prompt: 'Describe the error you want to report:' });
      if (!errorText) return;
      const editor = vscode.window.activeTextEditor;
      await supremeAIService.reportError({
        errorType: 'runtime',
        errorMessage: errorText,
        filePath: editor?.document.fileName ?? 'unknown',
        lineNumber: editor ? editor.selection.active.line + 1 : 0,
        severity: 'info',
        timestamp: new Date().toISOString(),
      });
      vscode.window.showInformationMessage('Error reported to SupremeAI. Thank you!');
    } catch (error) {
      vscode.window.showErrorMessage(`Failed to report error: ${error}`);
    }
  });

  const viewHistoryCommand = vscode.commands.registerCommand('supremeai.viewHistory', () => {
    vscode.window.showInformationMessage('Learning history is available in the SupremeAI Chat panel and Web Dashboard.');
  });

  context.subscriptions.push(
    forceLearnCommand, explainCodeCommand, reviewCodeCommand,
    loginAsGuestCommand, loginCommand, logoutCommand,
    generateCodeCommand, suggestRefactoringCommand,
    performSecurityScanCommand, analyzePerformanceCommand,
    showDependencyGraphCommand, visualizationCommand,
    openChatCommand, analyzeCodeFlowCommand,
    aiCompleteCommand, createProjectCommand,
    openExtensionSettingsCommand, reportErrorCommand, viewHistoryCommand,
  );
}
