import * as vscode from 'vscode';
import { AgentService } from './services/agentService';
import { registerCommands } from './commands';

let agentService: AgentService;

export async function activate(context: vscode.ExtensionContext) {
    console.log('Activating Prismata extension');

    // Initialize the agent service
    agentService = new AgentService(context);
    
    // Register commands
    const disposables = registerCommands(agentService);
    context.subscriptions.push(...disposables);
    
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
