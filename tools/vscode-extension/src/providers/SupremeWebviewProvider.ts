import * as vscode from 'vscode';
import axios from 'axios';

export class SupremeWebviewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'supremeai.sidebarViews';
    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // 📡 IPC মেসেজ লিসেনার
        this._setupMessageListener(webviewView.webview);

        this._fetchLiveRecipes().then(recipes => {
            webviewView.webview.postMessage({
                command: 'hydrateRecipes',
                data: recipes
            });
        });
    }

    private async _fetchLiveRecipes(): Promise<any[]> {
        try {
            const config = vscode.workspace.getConfiguration('supremeai');
            const base = config.get<string>('backendUrl', 'https://supremeai-worker.paykaribazaronline.workers.dev').replace(/\/$/, '');
            const backendUrl = `${base}/api/skills`;

            // AuthService থেকে বর্তমান টোকেন ব্যবহার করা হলো
            const { AuthService } = require('../services/AuthService');
            const authService = AuthService.getInstance();
            const token = authService?.getToken();
            const headers: Record<string, string> = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            const response = await axios.get(backendUrl, { headers });

            if (response.status === 200 && response.data) {
                return response.data.skills || response.data;
            }
            return [];
        } catch (error) {
            console.error('🔴 Failed to fetch live skills for VS Code Sidebar:', error);
            return [];
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview): string {
        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <style>
                    body { font-family: sans-serif; padding: 10px; color: var(--vscode-foreground); }
                    .recipe-card { background: var(--vscode-button-secondaryBackground); padding: 8px; margin-bottom: 8px; border-radius: 4px; border: 1px solid var(--vscode-widget-border); }
                    .btn { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 6px 12px; cursor: pointer; width: 100%; border-radius: 2px; }
                    .btn:hover { background: var(--vscode-button-hoverBackground); }
                    h4 { margin: 0 0 6px 0; color: var(--vscode-textLink-foreground); }
                </style>
            </head>
            <body>
                <h3>SupremeAI Recipe Factory</h3>
                <div id="recipe-container">Loading dynamic skills...</div>

                <script>
                    const vscode = acquireVsCodeApi();
                    const container = document.getElementById('recipe-container');

                    window.addEventListener('message', event => {
                        const message = event.data;
                        if (message.command === 'hydrateRecipes') {
                            const recipes = message.data;
                            if (!recipes || recipes.length === 0) {
                                container.innerHTML = 'No active automation recipes found.';
                                return;
                            }

                            container.innerHTML = '';
                            recipes.forEach(recipe => {
                                const card = document.createElement('div');
                                card.className = 'recipe-card';
                                card.innerHTML = \`
                                    <h4>\${recipe.skill_name}</h4>
                                    <p style="font-size:11px; margin: 0 0 8px 0;">\${recipe.description || ''}</p>
                                    <button class="btn" onclick="triggerRecipe('\${recipe.skill_name}')">Execute Automation</button>
                                \`;
                                container.appendChild(card);
                            });
                        }
                    });

                    function triggerRecipe(name) {
                        vscode.postMessage({
                            command: 'executeLocalRecipe',
                            recipeName: name
                        });
                    }
                </script>
            </body>
            </html>
        `;
    }

    private _setupMessageListener(webview: vscode.Webview) {
        webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'executeLocalRecipe':
                    vscode.window.showInformationMessage(`🚀 Triggering Recipe: ${message.recipeName}`);
                    break;
                case 'showError':
                    vscode.window.showErrorMessage(`🔴 Webview Error: ${message.text}`);
                    break;
            }
        });
    }
}
