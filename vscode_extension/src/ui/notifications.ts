import * as vscode from 'vscode';

/**
 * Notification manager for Prismata
 */
export class NotificationManager {
    private static instance: NotificationManager;
    private activeNotifications: Map<string, vscode.Progress<{ message?: string; increment?: number }>> = new Map();
    private activeTokens: Map<string, vscode.CancellationTokenSource> = new Map();

    /**
     * Get the notification manager instance
     */
    public static getInstance(): NotificationManager {
        if (!NotificationManager.instance) {
            NotificationManager.instance = new NotificationManager();
        }
        return NotificationManager.instance;
    }

    /**
     * Show a progress notification
     */
    public async showProgress(
        id: string,
        title: string,
        task: (
            progress: vscode.Progress<{ message?: string; increment?: number }>,
            token: vscode.CancellationToken
        ) => Promise<any>
    ): Promise<any> {
        // Cancel any existing notification with the same ID
        this.cancelNotification(id);

        // Create a new cancellation token source
        const tokenSource = new vscode.CancellationTokenSource();
        this.activeTokens.set(id, tokenSource);

        try {
            return await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title,
                    cancellable: true
                },
                async (progress, token) => {
                    // Store the progress object
                    this.activeNotifications.set(id, progress);

                    // Link the cancellation token
                    token.onCancellationRequested(() => {
                        tokenSource.cancel();
                    });

                    // Run the task
                    try {
                        const result = await task(progress, tokenSource.token);
                        return result;
                    } finally {
                        // Clean up
                        this.activeNotifications.delete(id);
                        this.activeTokens.delete(id);
                    }
                }
            );
        } catch (error) {
            // Clean up on error
            this.activeNotifications.delete(id);
            this.activeTokens.delete(id);
            throw error;
        }
    }

    /**
     * Update an existing progress notification
     */
    public updateProgress(id: string, message: string, increment?: number): void {
        const progress = this.activeNotifications.get(id);
        if (progress) {
            progress.report({ message, increment });
        }
    }

    /**
     * Cancel a notification
     */
    public cancelNotification(id: string): void {
        const tokenSource = this.activeTokens.get(id);
        if (tokenSource) {
            tokenSource.cancel();
            this.activeTokens.delete(id);
        }
        this.activeNotifications.delete(id);
    }

    /**
     * Show a result in a webview panel
     */
    public showResult(title: string, result: any, type: string = 'json'): void {
        // Create a webview panel
        const panel = vscode.window.createWebviewPanel(
            'prismataResult',
            title,
            vscode.ViewColumn.Two,
            { enableScripts: true }
        );

        // Format the result based on type
        let formattedResult: string;
        if (type === 'json') {
            formattedResult = JSON.stringify(result, null, 2);
        } else if (type === 'code') {
            formattedResult = result.code || '';
        } else {
            formattedResult = String(result);
        }

        // Determine the language for syntax highlighting
        let language = 'json';
        if (type === 'code') {
            language = result.language || 'plaintext';
        }

        // Generate HTML
        panel.webview.html = `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>${title}</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 20px;
                }
                .header {
                    margin-bottom: 20px;
                }
                .title {
                    font-size: 1.5em;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                pre {
                    background-color: var(--vscode-editor-background);
                    padding: 10px;
                    border-radius: 5px;
                    overflow: auto;
                    white-space: pre-wrap;
                }
                .explanation {
                    margin-top: 20px;
                    padding: 10px;
                    background-color: var(--vscode-inputValidation-infoBackground);
                    border-left: 3px solid var(--vscode-inputValidation-infoBorder);
                }
                .actions {
                    margin-top: 20px;
                    display: flex;
                    gap: 10px;
                }
                button {
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 6px 12px;
                    border-radius: 2px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">${title}</div>
            </div>
            
            <pre><code class="language-${language}">${this.escapeHtml(formattedResult)}</code></pre>
            
            ${result.explanation ? `<div class="explanation">${result.explanation}</div>` : ''}
            
            <div class="actions">
                <button id="copyBtn">Copy to Clipboard</button>
                ${type === 'code' ? '<button id="insertBtn">Insert into Editor</button>' : ''}
            </div>

            <script>
                (function() {
                    const vscode = acquireVsCodeApi();
                    
                    // Copy button
                    document.getElementById('copyBtn').addEventListener('click', () => {
                        vscode.postMessage({ 
                            type: 'copy', 
                            content: ${JSON.stringify(formattedResult)}
                        });
                    });
                    
                    // Insert button
                    ${type === 'code' ? `
                    document.getElementById('insertBtn').addEventListener('click', () => {
                        vscode.postMessage({ 
                            type: 'insert', 
                            content: ${JSON.stringify(formattedResult)}
                        });
                    });
                    ` : ''}
                })();
            </script>
        </body>
        </html>`;

        // Handle messages from the webview
        panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.type) {
                case 'copy':
                    await vscode.env.clipboard.writeText(message.content);
                    vscode.window.showInformationMessage('Copied to clipboard');
                    break;
                case 'insert':
                    const editor = vscode.window.activeTextEditor;
                    if (editor) {
                        editor.edit(editBuilder => {
                            editBuilder.insert(editor.selection.active, message.content);
                        });
                        vscode.window.showInformationMessage('Inserted into editor');
                    } else {
                        vscode.window.showErrorMessage('No active editor');
                    }
                    break;
            }
        });
    }

    /**
     * Escape HTML special characters
     */
    private escapeHtml(text: string): string {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}
