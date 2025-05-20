import * as vscode from 'vscode';
import { AgentService } from './services/agentService';
import { ErrorHandlingService } from './services/errorHandlingService';
import { registerCommands } from './commands';
import { registerRefactorCommands } from './commands/refactorCommands';
import { PrismataCompletionProvider } from './providers/completionProvider';
import { StatusBarManager } from './ui/statusBar';
import { PrismataSidebarProvider } from './ui/sidebarView';
import { QuickMenu } from './ui/quickMenu';
import { NotificationManager } from './ui/notifications';

let agentService: AgentService;

export async function activate(context: vscode.ExtensionContext) {
    console.log('Activating Prismata extension');

    // Initialize the agent service
    agentService = new AgentService(context);

    // Register commands
    const disposables = registerCommands(agentService);
    const refactorDisposables = registerRefactorCommands(context, agentService);

    // Register completion provider
    const completionProvider = new PrismataCompletionProvider(agentService);
    const completionDisposable = vscode.languages.registerCompletionItemProvider(
        ['*'], // Register for all languages
        completionProvider,
        '.', '_', 'abcdefghijklmnopqrstuvwxyz'.split('') // Trigger characters
    );

    // Register UI components
    const statusBar = new StatusBarManager(agentService);

    // Register sidebar view
    const sidebarProvider = new PrismataSidebarProvider(context.extensionUri, agentService);
    const sidebarDisposable = vscode.window.registerWebviewViewProvider(
        PrismataSidebarProvider.viewType,
        sidebarProvider
    );

    // Register quick menu command
    const quickMenu = new QuickMenu(agentService);
    const quickMenuDisposable = vscode.commands.registerCommand('prismata.showMenu', () => {
        quickMenu.show();
    });

    // Register context menu command
    const contextMenuDisposable = vscode.commands.registerCommand('prismata.showContextMenu', () => {
        quickMenu.showContextMenu();
    });

    // Initialize notification manager
    NotificationManager.getInstance();

    // Initialize error handling service
    const errorHandlingService = new ErrorHandlingService(agentService);

    // Register global error handler
    const errorHandler = vscode.window.onDidShowMessage(message => {
        if (message.severity === vscode.MessageSeverity.Error) {
            // Extract operation ID if present
            const operationIdMatch = /Operation ID: ([a-f0-9-]+)/.exec(message.message);
            const operationId = operationIdMatch ? operationIdMatch[1] : undefined;

            if (operationId) {
                errorHandlingService.handleError(message.message, operationId);
            }
        }
    });

    context.subscriptions.push(
        ...disposables,
        ...refactorDisposables,
        completionDisposable,
        sidebarDisposable,
        quickMenuDisposable,
        contextMenuDisposable,
        statusBar,
        errorHandler
    );

    // Auto-start the agent if configured
    const config = vscode.workspace.getConfiguration('prismata');
    if (config.get<boolean>('autoStart')) {
        try {
            await agentService.startAgent();
            vscode.window.showInformationMessage('Prismata Agent started successfully');
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to start Prismata Agent: ${error}`);
        }
    }
}

export function deactivate() {
    console.log('Deactivating Prismata extension');

    // Stop the agent service
    if (agentService) {
        return agentService.stopAgent();
    }
}
