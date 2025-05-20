import * as vscode from 'vscode';
import { AgentService } from '../services/agentService';

/**
 * Register refactoring commands
 */
export function registerRefactorCommands(
    context: vscode.ExtensionContext,
    agentService: AgentService
): vscode.Disposable[] {
    const disposables: vscode.Disposable[] = [];

    // Rename Symbol command
    disposables.push(
        vscode.commands.registerCommand('prismata.renameSymbol', async () => {
            try {
                const editor = vscode.window.activeTextEditor;
                if (!editor) {
                    vscode.window.showErrorMessage('No active editor');
                    return;
                }

                const document = editor.document;
                const filePath = document.uri.fsPath;
                const selection = editor.selection;
                const selectedText = document.getText(selection);

                // Get the symbol to rename
                let targetSymbol = selectedText.trim();
                if (!targetSymbol) {
                    targetSymbol = await vscode.window.showInputBox({
                        prompt: 'Enter the symbol to rename',
                        placeHolder: 'e.g., MyClass, my_function'
                    }) || '';
                }

                if (!targetSymbol) {
                    return; // User cancelled
                }

                // Get the new name
                const newName = await vscode.window.showInputBox({
                    prompt: `Enter the new name for "${targetSymbol}"`,
                    placeHolder: 'e.g., NewClass, new_function'
                });

                if (!newName) {
                    return; // User cancelled
                }

                // Ask if user wants to refactor across multiple files
                const refactorScope = await vscode.window.showQuickPick(
                    [
                        { label: 'Current file only', description: 'Rename only in this file' },
                        { label: 'Project-wide', description: 'Rename across all related files' }
                    ],
                    { placeHolder: 'Select refactoring scope' }
                );

                if (!refactorScope) {
                    return; // User cancelled
                }

                let filePaths: string[] = [filePath];

                // If project-wide, ask for additional files
                if (refactorScope.label === 'Project-wide') {
                    // First analyze dependencies to find related files
                    vscode.window.showInformationMessage('Analyzing project dependencies...');
                    
                    try {
                        const analysisResult = await agentService.analyzeCrossFileDependencies([filePath]);
                        const relatedFiles = analysisResult.files || [];
                        
                        // Filter out the current file
                        const additionalFiles = relatedFiles.filter(f => f !== filePath);
                        
                        if (additionalFiles.length > 0) {
                            // Ask user to select which files to include
                            const selectedFiles = await vscode.window.showQuickPick(
                                [
                                    { label: 'All related files', description: `Include all ${additionalFiles.length} related files` },
                                    ...additionalFiles.map(f => ({ label: f, description: 'Related file' }))
                                ],
                                { placeHolder: 'Select files to include in refactoring', canPickMany: true }
                            );
                            
                            if (selectedFiles) {
                                if (selectedFiles.some(f => f.label === 'All related files')) {
                                    filePaths = [filePath, ...additionalFiles];
                                } else {
                                    filePaths = [filePath, ...selectedFiles.map(f => f.label)];
                                }
                            }
                        }
                    } catch (error) {
                        console.error('Error analyzing dependencies:', error);
                        vscode.window.showWarningMessage('Could not analyze project dependencies. Proceeding with current file only.');
                    }
                }

                // Perform the refactoring
                vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: `Renaming "${targetSymbol}" to "${newName}"...`,
                    cancellable: false
                }, async (progress) => {
                    try {
                        const result = await agentService.refactorCode(
                            'rename',
                            filePaths,
                            targetSymbol,
                            newName
                        );

                        if (result && result.changes) {
                            // Apply changes
                            const workspaceEdit = new vscode.WorkspaceEdit();
                            
                            for (const [path, newContent] of Object.entries(result.changes)) {
                                const uri = vscode.Uri.file(path);
                                
                                // Read the current content
                                const document = await vscode.workspace.openTextDocument(uri);
                                const currentContent = document.getText();
                                
                                // Only apply changes if content is different
                                if (currentContent !== newContent) {
                                    const fullRange = new vscode.Range(
                                        document.positionAt(0),
                                        document.positionAt(currentContent.length)
                                    );
                                    workspaceEdit.replace(uri, fullRange, newContent as string);
                                }
                            }
                            
                            // Apply the edits
                            const success = await vscode.workspace.applyEdit(workspaceEdit);
                            
                            if (success) {
                                vscode.window.showInformationMessage(
                                    `Successfully renamed "${targetSymbol}" to "${newName}" in ${Object.keys(result.changes).length} file(s)`
                                );
                            } else {
                                vscode.window.showErrorMessage('Failed to apply refactoring changes');
                            }
                        } else if (result.errors && result.errors.length > 0) {
                            vscode.window.showErrorMessage(`Refactoring failed: ${result.errors[0]}`);
                        } else {
                            vscode.window.showWarningMessage('No changes were made during refactoring');
                        }
                    } catch (error) {
                        vscode.window.showErrorMessage(`Error during refactoring: ${error}`);
                    }
                });
            } catch (error) {
                vscode.window.showErrorMessage(`Error: ${error}`);
            }
        })
    );

    // Extract Method command
    disposables.push(
        vscode.commands.registerCommand('prismata.extractMethod', async () => {
            try {
                const editor = vscode.window.activeTextEditor;
                if (!editor) {
                    vscode.window.showErrorMessage('No active editor');
                    return;
                }

                const document = editor.document;
                const filePath = document.uri.fsPath;
                const selection = editor.selection;
                
                // Ensure there is a selection
                if (selection.isEmpty) {
                    vscode.window.showErrorMessage('Please select the code to extract');
                    return;
                }

                // Get the method name
                const methodName = await vscode.window.showInputBox({
                    prompt: 'Enter the name for the extracted method',
                    placeHolder: 'e.g., calculate_total, processData'
                });

                if (!methodName) {
                    return; // User cancelled
                }

                // Convert selection to range object for the API
                const selectionRange = {
                    start: { line: selection.start.line, character: selection.start.character },
                    end: { line: selection.end.line, character: selection.end.character }
                };

                // Create selection object with file path as key
                const selectionObj: Record<string, any> = {};
                selectionObj[filePath] = selectionRange;

                // Perform the refactoring
                vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: `Extracting method "${methodName}"...`,
                    cancellable: false
                }, async (progress) => {
                    try {
                        const result = await agentService.refactorCode(
                            'extract_method',
                            [filePath],
                            undefined,
                            methodName,
                            selectionObj
                        );

                        if (result && result.changes) {
                            // Apply changes
                            const workspaceEdit = new vscode.WorkspaceEdit();
                            
                            for (const [path, newContent] of Object.entries(result.changes)) {
                                const uri = vscode.Uri.file(path);
                                
                                // Read the current content
                                const document = await vscode.workspace.openTextDocument(uri);
                                const currentContent = document.getText();
                                
                                // Only apply changes if content is different
                                if (currentContent !== newContent) {
                                    const fullRange = new vscode.Range(
                                        document.positionAt(0),
                                        document.positionAt(currentContent.length)
                                    );
                                    workspaceEdit.replace(uri, fullRange, newContent as string);
                                }
                            }
                            
                            // Apply the edits
                            const success = await vscode.workspace.applyEdit(workspaceEdit);
                            
                            if (success) {
                                vscode.window.showInformationMessage(
                                    `Successfully extracted method "${methodName}"`
                                );
                            } else {
                                vscode.window.showErrorMessage('Failed to apply refactoring changes');
                            }
                        } else if (result.errors && result.errors.length > 0) {
                            vscode.window.showErrorMessage(`Refactoring failed: ${result.errors[0]}`);
                        } else {
                            vscode.window.showWarningMessage('No changes were made during refactoring');
                        }
                    } catch (error) {
                        vscode.window.showErrorMessage(`Error during refactoring: ${error}`);
                    }
                });
            } catch (error) {
                vscode.window.showErrorMessage(`Error: ${error}`);
            }
        })
    );

    return disposables;
}
