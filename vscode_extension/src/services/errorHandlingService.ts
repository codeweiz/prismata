import * as vscode from 'vscode';
import { AgentService } from './agentService';
import { NotificationManager } from '../ui/notifications';

/**
 * Error handling service for Prismata
 */
export class ErrorHandlingService {
    private agentService: AgentService;
    private notificationManager: NotificationManager;

    constructor(agentService: AgentService) {
        this.agentService = agentService;
        this.notificationManager = NotificationManager.getInstance();
    }

    /**
     * Handle an error
     */
    public async handleError(error: any, operationId?: string, context?: any): Promise<void> {
        console.error('Error:', error, 'Context:', context);

        // If we have an operation ID, try to get more details
        if (operationId) {
            try {
                const operation = await this.agentService.getOperation(operationId);
                
                // Show error details
                this.showErrorDetails(operation);
                
                // Offer recovery options if available
                if (operation.error && operation.error.recovery_options && operation.error.recovery_options.length > 0) {
                    this.offerRecoveryOptions(operation);
                }
                
                return;
            } catch (e) {
                console.error('Error getting operation details:', e);
                // Fall back to generic error handling
            }
        }

        // Generic error handling
        const errorMessage = error.message || error.toString();
        vscode.window.showErrorMessage(`Error: ${errorMessage}`);
    }

    /**
     * Show error details
     */
    private showErrorDetails(operation: any): void {
        const error = operation.error;
        if (!error) {
            return;
        }

        // Create a webview panel to show error details
        const panel = vscode.window.createWebviewPanel(
            'prismataError',
            'Prismata Error Details',
            vscode.ViewColumn.One,
            { enableScripts: true }
        );

        // Format the error details
        const errorMessage = error.message || 'Unknown error';
        const errorCategory = error.category || 'unknown';
        const errorSeverity = error.severity || 'error';
        const errorDetails = JSON.stringify(error.details || {}, null, 2);
        const stackTrace = error.stack_trace || '';
        const recoveryOptions = error.recovery_options || [];

        panel.webview.html = `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error Details</title>
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
                    color: var(--vscode-errorForeground);
                }
                .subtitle {
                    color: var(--vscode-descriptionForeground);
                    margin-bottom: 5px;
                }
                .section {
                    margin-bottom: 20px;
                }
                .section-title {
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                pre {
                    background-color: var(--vscode-editor-background);
                    padding: 10px;
                    border-radius: 5px;
                    overflow: auto;
                    white-space: pre-wrap;
                }
                .recovery-options {
                    margin-top: 20px;
                }
                .recovery-option {
                    margin-bottom: 10px;
                    padding: 10px;
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border-radius: 5px;
                    cursor: pointer;
                }
                .recovery-option:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
                .operation-info {
                    margin-top: 20px;
                    padding: 10px;
                    background-color: var(--vscode-inputValidation-infoBackground);
                    border-left: 3px solid var(--vscode-inputValidation-infoBorder);
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">Error: ${this.escapeHtml(errorMessage)}</div>
                <div class="subtitle">Category: ${errorCategory} | Severity: ${errorSeverity}</div>
                <div class="subtitle">Operation ID: ${operation.operation_id}</div>
                <div class="subtitle">Operation Type: ${operation.operation_type}</div>
                <div class="subtitle">Time: ${new Date(operation.timestamp).toLocaleString()}</div>
            </div>
            
            <div class="section">
                <div class="section-title">Details:</div>
                <pre>${errorDetails}</pre>
            </div>
            
            ${stackTrace ? `
            <div class="section">
                <div class="section-title">Stack Trace:</div>
                <pre>${stackTrace}</pre>
            </div>
            ` : ''}
            
            ${recoveryOptions.length > 0 ? `
            <div class="recovery-options">
                <div class="section-title">Recovery Options:</div>
                ${recoveryOptions.map((option: any) => `
                    <div class="recovery-option" data-name="${option.name}">
                        <div><strong>${option.name}</strong></div>
                        <div>${option.description}</div>
                    </div>
                `).join('')}
            </div>
            
            <script>
                (function() {
                    const vscode = acquireVsCodeApi();
                    
                    // Recovery option buttons
                    document.querySelectorAll('.recovery-option').forEach(button => {
                        button.addEventListener('click', () => {
                            const strategyName = button.getAttribute('data-name');
                            vscode.postMessage({ 
                                type: 'recover', 
                                operationId: '${operation.operation_id}',
                                strategyName: strategyName
                            });
                        });
                    });
                })();
            </script>
            ` : ''}
            
            <div class="operation-info">
                You can retry this operation or apply a recovery strategy from the Operations panel.
            </div>
        </body>
        </html>`;

        // Handle messages from the webview
        panel.webview.onDidReceiveMessage(async (message) => {
            if (message.type === 'recover') {
                await this.recoverOperation(message.operationId, message.strategyName);
            }
        });
    }

    /**
     * Offer recovery options
     */
    private async offerRecoveryOptions(operation: any): Promise<void> {
        const error = operation.error;
        if (!error || !error.recovery_options || error.recovery_options.length === 0) {
            return;
        }

        const options = error.recovery_options.map((option: any) => ({
            label: option.name,
            description: option.description
        }));

        options.push({
            label: 'Retry Operation',
            description: 'Retry the failed operation'
        });

        const selectedOption = await vscode.window.showQuickPick(options, {
            placeHolder: 'Select a recovery option',
            ignoreFocusOut: true
        });

        if (!selectedOption) {
            return; // User cancelled
        }

        if (selectedOption.label === 'Retry Operation') {
            await this.retryOperation(operation.operation_id);
        } else {
            await this.recoverOperation(operation.operation_id, selectedOption.label);
        }
    }

    /**
     * Retry an operation
     */
    private async retryOperation(operationId: string): Promise<void> {
        try {
            const result = await this.agentService.retryOperation(operationId);
            
            if (result.success) {
                vscode.window.showInformationMessage(`Operation ${operationId} retried successfully`);
            } else {
                vscode.window.showErrorMessage(`Failed to retry operation: ${result.error?.message || 'Unknown error'}`);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Error retrying operation: ${error}`);
        }
    }

    /**
     * Recover an operation
     */
    private async recoverOperation(operationId: string, strategyName: string): Promise<void> {
        try {
            const result = await this.agentService.recoverOperation(operationId, strategyName);
            
            if (result.success) {
                vscode.window.showInformationMessage(`Recovery strategy '${strategyName}' applied successfully`);
            } else {
                vscode.window.showErrorMessage(`Failed to apply recovery strategy: ${result.error?.message || 'Unknown error'}`);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Error applying recovery strategy: ${error}`);
        }
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
