import * as vscode from 'vscode';
import { AgentService } from '../services/agentService';

/**
 * Completion provider for Prismata
 */
export class PrismataCompletionProvider implements vscode.CompletionItemProvider {
    private agentService: AgentService;
    private isCompletionInProgress: boolean = false;
    private lastCompletionPosition: vscode.Position | null = null;
    private lastCompletionTime: number = 0;
    private completionThrottleMs: number = 500; // Throttle completions to avoid too many requests

    constructor(agentService: AgentService) {
        this.agentService = agentService;
    }

    async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): Promise<vscode.CompletionItem[] | vscode.CompletionList | null> {
        // Get the configuration
        const config = vscode.workspace.getConfiguration('prismata');
        const enableCompletion = config.get<boolean>('enableCodeCompletion', true);

        // Skip if completion is disabled
        if (!enableCompletion) {
            return null;
        }

        // Skip if completion is already in progress or if we're throttling
        const now = Date.now();
        if (this.isCompletionInProgress ||
            (this.lastCompletionTime && now - this.lastCompletionTime < this.completionThrottleMs)) {
            return null;
        }

        // Skip if the trigger character is not appropriate
        if (context.triggerKind === vscode.CompletionTriggerKind.TriggerCharacter) {
            const triggerCharacter = context.triggerCharacter;
            // Only trigger on certain characters
            if (!triggerCharacter || !'.abcdefghijklmnopqrstuvwxyz_'.includes(triggerCharacter)) {
                return null;
            }
        }

        // Skip if the position is the same as the last completion
        if (this.lastCompletionPosition &&
            this.lastCompletionPosition.line === position.line &&
            this.lastCompletionPosition.character === position.character) {
            return null;
        }

        this.isCompletionInProgress = true;
        this.lastCompletionPosition = position;
        this.lastCompletionTime = now;

        try {
            // Get the current line up to the cursor
            const linePrefix = document.lineAt(position.line).text.substring(0, position.character);

            // Skip if the line is empty or only whitespace
            if (!linePrefix.trim()) {
                this.isCompletionInProgress = false;
                return null;
            }

            // Get the file path
            const filePath = document.uri.fsPath;

            // Get the configuration
            const config = vscode.workspace.getConfiguration('prismata');
            const useProjectContext = config.get<boolean>('useProjectContextForCompletion', true);

            // Call the agent service to get completions
            const result = await this.agentService.completeCode(
                filePath,
                { line: position.line, character: position.character },
                linePrefix,
                undefined, // Let the service extract the context
                { use_project_context: useProjectContext }
            );

            // Convert the results to completion items
            if (result && result.items && result.items.length > 0) {
                return result.items.map((item: any) => {
                    const completionItem = new vscode.CompletionItem(
                        item.label,
                        this.getCompletionItemKind(item.kind)
                    );

                    completionItem.insertText = item.insert_text;
                    completionItem.detail = item.detail;
                    completionItem.documentation = item.documentation;

                    if (item.sort_text) {
                        completionItem.sortText = item.sort_text;
                    }

                    return completionItem;
                });
            }

            return null;
        } catch (error) {
            console.error('Error providing completions:', error);
            return null;
        } finally {
            this.isCompletionInProgress = false;
        }
    }

    private getCompletionItemKind(kind?: number): vscode.CompletionItemKind {
        if (kind === undefined) {
            return vscode.CompletionItemKind.Text;
        }

        // Map the kind to VSCode's CompletionItemKind
        // This mapping should match the server's kind values
        switch (kind) {
            case 1: return vscode.CompletionItemKind.Text;
            case 2: return vscode.CompletionItemKind.Method;
            case 3: return vscode.CompletionItemKind.Function;
            case 4: return vscode.CompletionItemKind.Constructor;
            case 5: return vscode.CompletionItemKind.Field;
            case 6: return vscode.CompletionItemKind.Variable;
            case 7: return vscode.CompletionItemKind.Class;
            case 8: return vscode.CompletionItemKind.Interface;
            case 9: return vscode.CompletionItemKind.Module;
            case 10: return vscode.CompletionItemKind.Property;
            case 11: return vscode.CompletionItemKind.Unit;
            case 12: return vscode.CompletionItemKind.Value;
            case 13: return vscode.CompletionItemKind.Enum;
            case 14: return vscode.CompletionItemKind.Keyword;
            case 15: return vscode.CompletionItemKind.Snippet;
            case 16: return vscode.CompletionItemKind.Color;
            case 17: return vscode.CompletionItemKind.File;
            case 18: return vscode.CompletionItemKind.Reference;
            case 19: return vscode.CompletionItemKind.Folder;
            case 20: return vscode.CompletionItemKind.EnumMember;
            case 21: return vscode.CompletionItemKind.Constant;
            case 22: return vscode.CompletionItemKind.Struct;
            case 23: return vscode.CompletionItemKind.Event;
            case 24: return vscode.CompletionItemKind.Operator;
            case 25: return vscode.CompletionItemKind.TypeParameter;
            default: return vscode.CompletionItemKind.Text;
        }
    }
}
