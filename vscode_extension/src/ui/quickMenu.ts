import * as vscode from 'vscode';
import { AgentService } from '../services/agentService';

/**
 * Quick menu for Prismata
 */
export class QuickMenu {
    private agentService: AgentService;

    constructor(agentService: AgentService) {
        this.agentService = agentService;
    }

    /**
     * Show the quick menu
     */
    public async show(): Promise<void> {
        const isAgentRunning = await this.agentService.isAgentRunning();
        
        const items: vscode.QuickPickItem[] = [
            {
                label: isAgentRunning ? '$(stop) Stop Agent' : '$(play) Start Agent',
                description: isAgentRunning ? 'Stop the Prismata agent' : 'Start the Prismata agent',
                detail: isAgentRunning ? 'Stops the Prismata agent process' : 'Starts the Prismata agent process'
            },
            {
                label: '$(code) Generate Code',
                description: 'Generate code based on a prompt',
                detail: 'Uses AI to generate code based on your description'
            },
            {
                label: '$(search) Analyze Code',
                description: 'Analyze the current file',
                detail: 'Analyzes the current file and provides insights'
            },
            {
                label: '$(references) Analyze Dependencies',
                description: 'Analyze dependencies between files',
                detail: 'Analyzes dependencies between multiple files'
            },
            {
                label: '$(symbol-method) Rename Symbol',
                description: 'Rename a symbol across files',
                detail: 'Intelligently renames a symbol across multiple files'
            },
            {
                label: '$(symbol-class) Extract Method',
                description: 'Extract selected code into a method',
                detail: 'Extracts the selected code into a new method'
            },
            {
                label: '$(gear) Settings',
                description: 'Configure Prismata settings',
                detail: 'Opens the Prismata settings page'
            },
            {
                label: '$(info) About',
                description: 'About Prismata',
                detail: 'Shows information about Prismata'
            }
        ];

        const selectedItem = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a Prismata action',
            matchOnDescription: true,
            matchOnDetail: true
        });

        if (!selectedItem) {
            return; // User cancelled
        }

        // Handle the selected action
        switch (selectedItem.label) {
            case '$(stop) Stop Agent':
                await this.agentService.stopAgent();
                vscode.window.showInformationMessage('Prismata agent stopped');
                break;
            case '$(play) Start Agent':
                await this.agentService.startAgent();
                vscode.window.showInformationMessage('Prismata agent started');
                break;
            case '$(code) Generate Code':
                vscode.commands.executeCommand('prismata.generateCode');
                break;
            case '$(search) Analyze Code':
                vscode.commands.executeCommand('prismata.analyzeCode');
                break;
            case '$(references) Analyze Dependencies':
                vscode.commands.executeCommand('prismata.analyzeCrossFileDependencies');
                break;
            case '$(symbol-method) Rename Symbol':
                vscode.commands.executeCommand('prismata.renameSymbol');
                break;
            case '$(symbol-class) Extract Method':
                vscode.commands.executeCommand('prismata.extractMethod');
                break;
            case '$(gear) Settings':
                vscode.commands.executeCommand('workbench.action.openSettings', 'prismata');
                break;
            case '$(info) About':
                this.showAbout();
                break;
        }
    }

    /**
     * Show the context menu
     */
    public async showContextMenu(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const hasSelection = !editor.selection.isEmpty;
        
        const items: vscode.QuickPickItem[] = [
            {
                label: '$(code) Generate Code Here',
                description: 'Generate code at cursor position',
                detail: 'Generates code at the current cursor position'
            },
            {
                label: '$(search) Analyze Selection',
                description: 'Analyze the selected code',
                detail: 'Analyzes the selected code and provides insights',
                picked: hasSelection
            },
            {
                label: '$(symbol-method) Rename Symbol',
                description: 'Rename the selected symbol',
                detail: 'Renames the selected symbol across files',
                picked: hasSelection
            },
            {
                label: '$(symbol-class) Extract Method',
                description: 'Extract selection into a method',
                detail: 'Extracts the selected code into a new method',
                picked: hasSelection
            }
        ];

        const selectedItem = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a Prismata action for this context',
            matchOnDescription: true,
            matchOnDetail: true
        });

        if (!selectedItem) {
            return; // User cancelled
        }

        // Handle the selected action
        switch (selectedItem.label) {
            case '$(code) Generate Code Here':
                // Implement inline code generation
                const prompt = await vscode.window.showInputBox({
                    prompt: 'Enter a description of the code you want to generate',
                    placeHolder: 'E.g., Create a function that sorts an array'
                });
                
                if (prompt) {
                    // Get the current position
                    const position = editor.selection.active;
                    
                    // Generate code and insert at position
                    try {
                        vscode.window.withProgress({
                            location: vscode.ProgressLocation.Notification,
                            title: 'Generating code...',
                            cancellable: false
                        }, async (progress) => {
                            const result = await this.agentService.generateCode(prompt);
                            
                            if (result && result.code) {
                                // Insert the generated code at the cursor position
                                editor.edit(editBuilder => {
                                    editBuilder.insert(position, result.code);
                                });
                                
                                // Show explanation if available
                                if (result.explanation) {
                                    vscode.window.showInformationMessage(result.explanation);
                                }
                            }
                        });
                    } catch (error) {
                        vscode.window.showErrorMessage(`Error generating code: ${error}`);
                    }
                }
                break;
                
            case '$(search) Analyze Selection':
                if (hasSelection) {
                    vscode.commands.executeCommand('prismata.analyzeCode');
                } else {
                    vscode.window.showErrorMessage('Please select some code to analyze');
                }
                break;
                
            case '$(symbol-method) Rename Symbol':
                vscode.commands.executeCommand('prismata.renameSymbol');
                break;
                
            case '$(symbol-class) Extract Method':
                if (hasSelection) {
                    vscode.commands.executeCommand('prismata.extractMethod');
                } else {
                    vscode.window.showErrorMessage('Please select code to extract');
                }
                break;
        }
    }

    /**
     * Show the about dialog
     */
    private showAbout(): void {
        const panel = vscode.window.createWebviewPanel(
            'prismataAbout',
            'About Prismata',
            vscode.ViewColumn.One,
            { enableScripts: true }
        );

        panel.webview.html = `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>About Prismata</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .logo {
                    font-size: 3em;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .tagline {
                    font-size: 1.2em;
                    color: var(--vscode-descriptionForeground);
                    margin-bottom: 20px;
                }
                .section {
                    margin-bottom: 30px;
                }
                .section-title {
                    font-size: 1.5em;
                    font-weight: bold;
                    margin-bottom: 10px;
                    border-bottom: 1px solid var(--vscode-panel-border);
                    padding-bottom: 5px;
                }
                .feature {
                    margin-bottom: 15px;
                }
                .feature-title {
                    font-weight: bold;
                }
                .feature-description {
                    margin-top: 5px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">Prismata</div>
                <div class="tagline">AI-powered coding assistant</div>
            </div>
            
            <div class="section">
                <div class="section-title">Features</div>
                
                <div class="feature">
                    <div class="feature-title">Code Generation</div>
                    <div class="feature-description">
                        Generate code based on natural language descriptions, with context awareness.
                    </div>
                </div>
                
                <div class="feature">
                    <div class="feature-title">Code Analysis</div>
                    <div class="feature-description">
                        Analyze code to understand its structure, functionality, and potential issues.
                    </div>
                </div>
                
                <div class="feature">
                    <div class="feature-title">Cross-File Analysis</div>
                    <div class="feature-description">
                        Analyze dependencies between multiple files to understand project structure.
                    </div>
                </div>
                
                <div class="feature">
                    <div class="feature-title">Code Refactoring</div>
                    <div class="feature-description">
                        Refactor code with intelligent operations like rename and extract method.
                    </div>
                </div>
                
                <div class="feature">
                    <div class="feature-title">Code Completion</div>
                    <div class="feature-description">
                        Get intelligent code completion suggestions as you type.
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Version</div>
                <p>Prismata v0.1.0</p>
            </div>
        </body>
        </html>`;
    }
}
