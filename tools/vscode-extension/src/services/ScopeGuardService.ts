/**
 * Scope Guard Service for SupremeAI VS Code Extension.
 *
 * Enforces permission scope checks (READ_ONLY vs FULL_CONTROL) on active workspaces.
 * Prevents unauthorized code edits/commits on protected primary repositories.
 */

import * as vscode from 'vscode';
import { apiBridge } from './apiBridge';

export enum PermissionScope {
  READ_ONLY = 'READ_ONLY',
  FULL_CONTROL = 'FULL_CONTROL',
}

export interface TargetPlatformInfo {
  id: string;
  name: string;
  scope: PermissionScope;
  isReadOnly: boolean;
  canWrite: boolean;
}

export class ScopeGuardService {
  private static instance: ScopeGuardService;
  private currentScope: PermissionScope = PermissionScope.READ_ONLY;
  private currentTargetId: string = 'main-repository';

  private constructor() {
    this.detectCurrentScope();
  }

  public static getInstance(): ScopeGuardService {
    if (!ScopeGuardService.instance) {
      ScopeGuardService.instance = new ScopeGuardService();
    }
    return ScopeGuardService.instance;
  }

  /**
   * Detects permission scope for current active workspace folder.
   */
  public async detectCurrentScope(): Promise<PermissionScope> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
      this.currentScope = PermissionScope.READ_ONLY;
      return this.currentScope;
    }

    try {
      const targets = await apiBridge.fetchTargetRepositories();
      const folderPath = workspaceFolder.uri.fsPath.toLowerCase();

      // Check if current workspace matches any registered target entity
      const matched = targets.find((t: any) => 
        t.id.toLowerCase().includes('main') || folderPath.includes('main')
      );

      if (matched && matched.scope === 'READ_ONLY') {
        this.currentScope = PermissionScope.READ_ONLY;
        this.currentTargetId = matched.id;
      } else {
        // Default to FULL_CONTROL for isolated agent workspaces
        this.currentScope = PermissionScope.FULL_CONTROL;
        this.currentTargetId = matched?.id || 'agent-workspace';
      }
    } catch (e) {
      // Offline fallback: Default to READ_ONLY for security
      this.currentScope = PermissionScope.READ_ONLY;
    }

    return this.currentScope;
  }

  public isReadOnly(): boolean {
    return this.currentScope === PermissionScope.READ_ONLY;
  }

  public canWrite(): boolean {
    return this.currentScope === PermissionScope.FULL_CONTROL;
  }

  /**
   * Enforces scope check before any write or patch execution.
   * Prompts user with explanation if write is blocked on a READ_ONLY target.
   */
  public async validateWriteOperation(operationName: string): Promise<boolean> {
    await this.detectCurrentScope();

    if (this.isReadOnly()) {
      vscode.window.showWarningMessage(
        `🛡️ Scope Guard: Write operation '${operationName}' blocked on READ_ONLY target '${this.currentTargetId}'. Suggestions can only be applied as Pull Requests or copied code.`,
        'Copy Code to Clipboard',
        'Create Draft PR'
      ).then((selection) => {
        if (selection === 'Copy Code to Clipboard') {
          vscode.commands.executeCommand('editor.action.clipboardCopyAction');
        }
      });
      return false;
    }

    return true;
  }
}

export const scopeGuard = ScopeGuardService.getInstance();
