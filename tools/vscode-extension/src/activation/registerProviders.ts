/**
 * registerProviders — chat provider, status bar, and inline completion provider.
 * extension.ts থেকে আলাদা করা হয়েছে।
 */

import * as vscode from 'vscode';
import { SupremeAIService } from '../services/SupremeAIService';
import { FeedbackHandler } from '../handlers/FeedbackHandler';
import { SupremeAIChatProvider } from '../providers/SupremeAIChatProvider';
import { SupremeAIAdminDashboardProvider } from '../providers/SupremeAIAdminDashboardProvider';
import { SupremeAICustomerDashboardProvider } from '../providers/SupremeAICustomerDashboardProvider';

export function registerChatProvider(
  context: vscode.ExtensionContext,
): void {
  const chatProvider = new SupremeAIChatProvider(context);
  const adminDashboardProvider = new SupremeAIAdminDashboardProvider(context.extensionUri);
  const customerDashboardProvider = new SupremeAICustomerDashboardProvider(context.extensionUri);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider('supremeaiChat', chatProvider),
    vscode.window.registerWebviewViewProvider('supremeaiAdminDashboard', adminDashboardProvider),
    vscode.window.registerWebviewViewProvider('supremeaiCustomerDashboard', customerDashboardProvider),
    vscode.commands.registerCommand('supremeai.sendMessageToChat', (message?: string) => {
      let finalMessage = message;
      if (!finalMessage) {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
          const text = editor.document.getText(editor.selection);
          if (text) {
            finalMessage = `Please check this code:\n\n\`\`\`${editor.document.languageId}\n${text}\n\`\`\``;
          }
        }
      }
      if (finalMessage) {
        chatProvider.postMessageToChat(finalMessage);
      } else {
        vscode.window.showWarningMessage('No message or selection found to send to chat.');
      }
    }),
  );
}

export function registerStatusBar(context: vscode.ExtensionContext): void {
  const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.text = '$(brain) SupremeAI';
  statusBarItem.tooltip = 'SupremeAI Assistant (Chat)';
  statusBarItem.command = 'supremeai.openChat';
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);
}

export function registerInlineCompletionProvider(
  context: vscode.ExtensionContext,
  supremeAIService: SupremeAIService,
  fbHandler: FeedbackHandler,
): void {
  const config = vscode.workspace.getConfiguration('supremeai');
  const enableRealTimeLearning = config.get<boolean>('enableRealTimeLearning', true);
  if (!enableRealTimeLearning) {
    console.log('[SupremeAI] Real-time learning disabled, skipping inline completion provider');
    return;
  }

  let debounceTimeout: NodeJS.Timeout | undefined;

  const provider: vscode.InlineCompletionItemProvider = {
    async provideInlineCompletionItems(
      document: vscode.TextDocument,
      position: vscode.Position,
      _context: vscode.InlineCompletionContext,
      token: vscode.CancellationToken,
    ): Promise<vscode.InlineCompletionList | vscode.InlineCompletionItem[] | undefined> {
      const currentConfig = vscode.workspace.getConfiguration('supremeai');
      const debounceDelay = currentConfig.get<number>('inlineCompletionDebounce', 800);

      if (debounceTimeout) clearTimeout(debounceTimeout);

      return new Promise<vscode.InlineCompletionList | undefined>((resolve) => {
        debounceTimeout = setTimeout(async () => {
          if (token.isCancellationRequested) { resolve(undefined); return; }
          if (!currentConfig.get<boolean>('enableRealTimeLearning', true)) { resolve(undefined); return; }

          try {
            const docText = document.getText();
            const offset = document.offsetAt(position);
            const prefix = docText.substring(0, offset);
            const suffix = docText.substring(offset);

            const response = await supremeAIService.getInlineCompletions(
              prefix, suffix, document.fileName, document.languageId,
            );

            if (token.isCancellationRequested || !response.suggestions?.length) {
              resolve(undefined); return;
            }

            const items: vscode.InlineCompletionItem[] = response.suggestions.map((text) => {
              const item = new vscode.InlineCompletionItem(text);
              const suggestionId = `inline-${Date.now()}`;
              fbHandler.captureSuggestionContext(
                suggestionId, `completion-${Date.now()}`, '', text, `File: ${document.uri.fsPath}`, position,
              );
              item.command = {
                title: 'Accept Suggestion',
                command: 'supremeai.acceptSuggestion',
                arguments: [document.fileName, text, document.languageId],
              };
              return item;
            });
            resolve({ items });
          } catch (error) {
            console.error('[SupremeAI] Error fetching inline completion:', error);
            resolve(undefined);
          }
        }, debounceDelay);
      });
    },
  };

  context.subscriptions.push(vscode.languages.registerInlineCompletionItemProvider({ pattern: '**' }, provider));
  console.log('[SupremeAI] InlineCompletionItemProvider registered with optimized debounce');
}
