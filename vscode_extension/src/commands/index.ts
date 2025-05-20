import * as vscode from 'vscode';
import { AgentService } from '../services/agentService';

/**
 * Register all commands for the extension
 */
export function registerCommands(agentService: AgentService): vscode.Disposable[] {
    const disposables: vscode.Disposable[] = [];

    // Start Agent command
    disposables.push(
        vscode.commands.registerCommand('prismata.startAgent', async () => {
            try {
                await agentService.startAgent();
                vscode.window.showInformationMessage('Prismata Agent started successfully');
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to start Prismata Agent: ${error}`);
            }
        })
    );

    // Generate Code command
    disposables.push(
        vscode.commands.registerCommand('prismata.generateCode', async () => {
            try {
                const prompt = await vscode.window.showInputBox({
                    prompt: 'Enter a description of the code you want to generate',
                    placeHolder: 'E.g., Create a function that sorts an array'
                });

                if (!prompt) {
                    return; // User cancelled
                }

                vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Generating code...',
                    cancellable: false
                }, async (progress) => {
                    try {
                        const result = await agentService.generateCode(prompt);
                        
                        if (result && result.code) {
                            // Show preview
                            const document = await vscode.workspace.openTextDocument({
                                content: result.code,
                                language: result.language || 'plaintext'
                            });
                            
                            await vscode.window.showTextDocument(document);
                            
                            // Show explanation if available
                            if (result.explanation) {
                                vscode.window.showInformationMessage(result.explanation);
                            }
                        } else {
                            vscode.window.showWarningMessage('No code was generated');
                        }
                    } catch (error) {
                        vscode.window.showErrorMessage(`Error generating code: ${error}`);
                    }
                });
            } catch (error) {
                vscode.window.showErrorMessage(`Error: ${error}`);
            }
        })
    );

    // Analyze Code command
    disposables.push(
        vscode.commands.registerCommand('prismata.analyzeCode', async () => {
            try {
                vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Analyzing code...',
                    cancellable: false
                }, async (progress) => {
                    try {
                        const result = await agentService.analyzeCode();
                        
                        // Create a webview to display the analysis results
                        const panel = vscode.window.createWebviewPanel(
                            'prismataAnalysis',
                            'Code Analysis',
                            vscode.ViewColumn.Beside,
                            { enableScripts: true }
                        );
                        
                        // Format the analysis results as HTML
                        panel.webview.html = formatAnalysisResults(result);
                    } catch (error) {
                        vscode.window.showErrorMessage(`Error analyzing code: ${error}`);
                    }
                });
            } catch (error) {
                vscode.window.showErrorMessage(`Error: ${error}`);
            }
        })
    );

    return disposables;
}

/**
 * Format analysis results as HTML
 */
function formatAnalysisResults(results: any): string {
    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Code Analysis</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 20px;
                }
                h1, h2, h3 {
                    color: var(--vscode-editor-foreground);
                }
                .symbol {
                    margin-bottom: 10px;
                    padding: 5px;
                    border-left: 3px solid var(--vscode-activityBarBadge-background);
                }
                .symbol-name {
                    font-weight: bold;
                }
                .symbol-kind {
                    color: var(--vscode-descriptionForeground);
                    margin-left: 10px;
                }
                .symbol-detail {
                    margin-top: 5px;
                    color: var(--vscode-descriptionForeground);
                }
                .imports {
                    margin-top: 20px;
                }
                .import-item {
                    margin-bottom: 5px;
                }
                .error {
                    color: var(--vscode-errorForeground);
                }
            </style>
        </head>
        <body>
            <h1>Code Analysis Results</h1>
            
            ${results.file_path ? `<h2>File: ${results.file_path}</h2>` : ''}
            
            ${results.language ? `<p>Language: ${results.language}</p>` : ''}
            
            <h3>Symbols</h3>
            ${results.symbols && results.symbols.length > 0 
                ? formatSymbols(results.symbols) 
                : '<p>No symbols found</p>'}
            
            ${results.imports && results.imports.length > 0 
                ? `<div class="imports">
                    <h3>Imports</h3>
                    <ul>
                        ${results.imports.map((imp: string) => `<li class="import-item">${imp}</li>`).join('')}
                    </ul>
                  </div>`
                : ''}
            
            ${results.errors && results.errors.length > 0 
                ? `<div class="errors">
                    <h3>Errors</h3>
                    <ul>
                        ${results.errors.map((err: any) => `<li class="error">${err.message || err}</li>`).join('')}
                    </ul>
                  </div>`
                : ''}
        </body>
        </html>
    `;
}

/**
 * Format symbols recursively
 */
function formatSymbols(symbols: any[]): string {
    return `
        <ul>
            ${symbols.map(symbol => `
                <li class="symbol">
                    <div>
                        <span class="symbol-name">${symbol.name}</span>
                        <span class="symbol-kind">${symbol.kind}</span>
                    </div>
                    ${symbol.detail ? `<div class="symbol-detail">${symbol.detail}</div>` : ''}
                    ${symbol.children && symbol.children.length > 0 ? formatSymbols(symbol.children) : ''}
                </li>
            `).join('')}
        </ul>
    `;
}
