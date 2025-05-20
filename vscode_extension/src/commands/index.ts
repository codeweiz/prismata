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

    // Read File command
    disposables.push(
        vscode.commands.registerCommand('prismata.readFile', async () => {
            try {
                // Ask for file path if needed
                const filePathOptions = await vscode.window.showOpenDialog({
                    canSelectFiles: true,
                    canSelectFolders: false,
                    canSelectMany: false,
                    openLabel: 'Select File to Read'
                });

                if (!filePathOptions || filePathOptions.length === 0) {
                    return; // User cancelled
                }

                const filePath = filePathOptions[0].fsPath;

                vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Reading file...',
                    cancellable: false
                }, async (progress) => {
                    try {
                        const result = await agentService.readFile(filePath);

                        if (result && result.content) {
                            // Show file content in a new editor
                            const document = await vscode.workspace.openTextDocument({
                                content: result.content,
                                language: 'plaintext'
                            });

                            await vscode.window.showTextDocument(document);

                            // Show metadata in output channel
                            const outputChannel = vscode.window.createOutputChannel('Prismata File Info');
                            outputChannel.appendLine('File Metadata:');
                            for (const [key, value] of Object.entries(result.metadata)) {
                                outputChannel.appendLine(`${key}: ${JSON.stringify(value)}`);
                            }
                            outputChannel.show();
                        } else {
                            vscode.window.showWarningMessage('No content was read from the file');
                        }
                    } catch (error) {
                        vscode.window.showErrorMessage(`Error reading file: ${error}`);
                    }
                });
            } catch (error) {
                vscode.window.showErrorMessage(`Error: ${error}`);
            }
        })
    );

    // Get File Metadata command
    disposables.push(
        vscode.commands.registerCommand('prismata.getFileMetadata', async () => {
            try {
                // Ask for file path if needed
                const filePathOptions = await vscode.window.showOpenDialog({
                    canSelectFiles: true,
                    canSelectFolders: true,
                    canSelectMany: false,
                    openLabel: 'Select File or Folder'
                });

                if (!filePathOptions || filePathOptions.length === 0) {
                    return; // User cancelled
                }

                const filePath = filePathOptions[0].fsPath;

                vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Getting file metadata...',
                    cancellable: false
                }, async (progress) => {
                    try {
                        const metadata = await agentService.getFileMetadata(filePath);

                        // Show metadata in output channel
                        const outputChannel = vscode.window.createOutputChannel('Prismata File Metadata');
                        outputChannel.appendLine(`Metadata for: ${filePath}`);
                        outputChannel.appendLine('----------------------------');
                        for (const [key, value] of Object.entries(metadata)) {
                            outputChannel.appendLine(`${key}: ${JSON.stringify(value)}`);
                        }
                        outputChannel.show();
                    } catch (error) {
                        vscode.window.showErrorMessage(`Error getting file metadata: ${error}`);
                    }
                });
            } catch (error) {
                vscode.window.showErrorMessage(`Error: ${error}`);
            }
        })
    );

    // Write File command
    disposables.push(
        vscode.commands.registerCommand('prismata.writeFile', async () => {
            try {
                // Ask for file path
                const filePathOptions = await vscode.window.showSaveDialog({
                    saveLabel: 'Select File to Write'
                });

                if (!filePathOptions) {
                    return; // User cancelled
                }

                const filePath = filePathOptions.fsPath;

                // Ask for content
                const content = await vscode.window.showInputBox({
                    prompt: 'Enter content to write to the file',
                    placeHolder: 'File content',
                    multiline: true
                });

                if (content === undefined) {
                    return; // User cancelled
                }

                vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Writing file...',
                    cancellable: false
                }, async (progress) => {
                    try {
                        const result = await agentService.writeFile(filePath, content);

                        // Check if confirmation is required
                        if (result.requires_confirmation) {
                            // Show preview
                            const previewContent = result.preview.content;
                            const previewOperation = result.preview.operation;
                            const previewDiff = result.preview.diff;

                            // Create a webview to display the preview
                            const panel = vscode.window.createWebviewPanel(
                                'prismataFilePreview',
                                'File Write Preview',
                                vscode.ViewColumn.Beside,
                                { enableScripts: true }
                            );

                            // Format the preview as HTML
                            panel.webview.html = formatFilePreview(result.preview, filePath);

                            // Ask for confirmation
                            const confirm = await vscode.window.showInformationMessage(
                                `Confirm writing to ${filePath}?`,
                                { modal: true },
                                'Yes', 'No'
                            );

                            if (confirm === 'Yes') {
                                // Confirm the write operation
                                const confirmResult = await agentService.confirmWriteFile(filePath, content);
                                vscode.window.showInformationMessage(`File ${previewOperation === 'create' ? 'created' : 'updated'} successfully.`);
                            } else {
                                vscode.window.showInformationMessage('File write operation cancelled.');
                            }
                        } else {
                            vscode.window.showInformationMessage(`File written successfully.`);
                        }
                    } catch (error) {
                        vscode.window.showErrorMessage(`Error writing file: ${error}`);
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
 * Format file preview as HTML
 */
function formatFilePreview(preview: any, filePath: string): string {
    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>File Write Preview</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 20px;
                }
                h1, h2, h3 {
                    color: var(--vscode-editor-foreground);
                }
                pre {
                    background-color: var(--vscode-editor-background);
                    padding: 10px;
                    border-radius: 5px;
                    overflow: auto;
                    white-space: pre-wrap;
                }
                .diff {
                    background-color: var(--vscode-diffEditor-diagonalFill);
                }
                .diff-add {
                    color: var(--vscode-diffEditor-insertedTextBackground);
                }
                .diff-remove {
                    color: var(--vscode-diffEditor-removedTextBackground);
                }
                .operation {
                    font-weight: bold;
                    color: var(--vscode-statusBarItem-prominentBackground);
                }
            </style>
        </head>
        <body>
            <h1>File Write Preview</h1>

            <h2>File: ${filePath}</h2>

            <p>Operation: <span class="operation">${preview.operation}</span></p>

            <h3>Content</h3>
            <pre>${escapeHtml(preview.content)}</pre>

            ${preview.old_content ? `
                <h3>Original Content</h3>
                <pre>${escapeHtml(preview.old_content)}</pre>
            ` : ''}

            ${preview.diff ? `
                <h3>Diff</h3>
                <pre class="diff">${formatDiff(preview.diff)}</pre>
            ` : ''}

            <p>Please confirm this operation using the notification.</p>
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

/**
 * Escape HTML special characters
 */
function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Format diff output with colors
 */
function formatDiff(diff: string): string {
    if (!diff) {
        return '';
    }

    return diff.split('\n')
        .map(line => {
            if (line.startsWith('+')) {
                return `<span class="diff-add">${escapeHtml(line)}</span>`;
            } else if (line.startsWith('-')) {
                return `<span class="diff-remove">${escapeHtml(line)}</span>`;
            } else {
                return escapeHtml(line);
            }
        })
        .join('\n');
}
