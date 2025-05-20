import * as vscode from 'vscode';
import { AgentService } from '../services/agentService';

/**
 * History item for the sidebar view
 */
interface HistoryItem {
    id: string;
    type: string;
    timestamp: number;
    description: string;
    status: string;
    details?: any;
}

/**
 * Sidebar provider for Prismata
 */
export class PrismataSidebarProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'prismata.sidebar';
    
    private _view?: vscode.WebviewView;
    private _historyItems: HistoryItem[] = [];
    private _agentService: AgentService;

    constructor(private readonly _extensionUri: vscode.Uri, agentService: AgentService) {
        this._agentService = agentService;
        
        // Listen for operation history updates
        this._agentService.onHistoryUpdate((historyItems: any[]) => {
            this._historyItems = historyItems.map(item => ({
                id: item.id || `op-${Date.now()}`,
                type: item.type || 'unknown',
                timestamp: item.timestamp || Date.now(),
                description: item.description || 'Operation',
                status: item.status || 'completed',
                details: item.details
            }));
            this._update();
        });
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'refresh':
                    await this._agentService.getHistory();
                    break;
                case 'clear':
                    this._historyItems = [];
                    this._update();
                    break;
                case 'viewDetails':
                    this._showDetails(data.id);
                    break;
                case 'retry':
                    this._retryOperation(data.id);
                    break;
            }
        });
        
        // Initial load of history
        this._agentService.getHistory().catch(err => {
            console.error('Failed to load history:', err);
        });
    }

    private _update() {
        if (this._view) {
            this._view.webview.html = this._getHtmlForWebview(this._view.webview);
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        // Sort history items by timestamp (newest first)
        const sortedItems = [...this._historyItems].sort((a, b) => b.timestamp - a.timestamp);
        
        // Format timestamp
        const formatTimestamp = (timestamp: number) => {
            const date = new Date(timestamp);
            return date.toLocaleTimeString();
        };
        
        // Get status icon
        const getStatusIcon = (status: string) => {
            switch (status) {
                case 'completed': return '✅';
                case 'error': return '❌';
                case 'in_progress': return '⏳';
                case 'pending': return '⏳';
                default: return '❓';
            }
        };
        
        // Generate history items HTML
        const historyItemsHtml = sortedItems.map(item => `
            <div class="history-item ${item.status}">
                <div class="history-item-header">
                    <span class="history-item-icon">${getStatusIcon(item.status)}</span>
                    <span class="history-item-type">${item.type}</span>
                    <span class="history-item-time">${formatTimestamp(item.timestamp)}</span>
                </div>
                <div class="history-item-description">${item.description}</div>
                <div class="history-item-actions">
                    <button class="action-button" data-id="${item.id}" data-action="viewDetails">Details</button>
                    ${item.status === 'error' ? `<button class="action-button" data-id="${item.id}" data-action="retry">Retry</button>` : ''}
                </div>
            </div>
        `).join('');

        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Prismata</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 10px;
                    color: var(--vscode-foreground);
                }
                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                }
                .title {
                    font-size: 1.2em;
                    font-weight: bold;
                }
                .actions {
                    display: flex;
                    gap: 8px;
                }
                .button {
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    padding: 4px 8px;
                    border-radius: 2px;
                    cursor: pointer;
                }
                .button:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
                .history-item {
                    margin-bottom: 12px;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: var(--vscode-editor-background);
                    border-left: 3px solid var(--vscode-activityBarBadge-background);
                }
                .history-item.error {
                    border-left-color: var(--vscode-errorForeground);
                }
                .history-item.completed {
                    border-left-color: var(--vscode-terminal-ansiGreen);
                }
                .history-item.in_progress, .history-item.pending {
                    border-left-color: var(--vscode-terminal-ansiYellow);
                }
                .history-item-header {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 4px;
                }
                .history-item-icon {
                    margin-right: 6px;
                }
                .history-item-type {
                    font-weight: bold;
                }
                .history-item-time {
                    font-size: 0.8em;
                    color: var(--vscode-descriptionForeground);
                }
                .history-item-description {
                    margin-bottom: 8px;
                }
                .history-item-actions {
                    display: flex;
                    gap: 8px;
                }
                .action-button {
                    background-color: transparent;
                    color: var(--vscode-textLink-foreground);
                    border: none;
                    padding: 2px 4px;
                    cursor: pointer;
                    font-size: 0.9em;
                }
                .action-button:hover {
                    text-decoration: underline;
                }
                .empty-state {
                    text-align: center;
                    padding: 20px;
                    color: var(--vscode-descriptionForeground);
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">Prismata Operations</div>
                <div class="actions">
                    <button class="button refresh-button">Refresh</button>
                    <button class="button clear-button">Clear</button>
                </div>
            </div>
            
            <div class="history-container">
                ${historyItemsHtml.length > 0 ? historyItemsHtml : '<div class="empty-state">No operations yet</div>'}
            </div>

            <script>
                (function() {
                    const vscode = acquireVsCodeApi();
                    
                    // Refresh button
                    document.querySelector('.refresh-button').addEventListener('click', () => {
                        vscode.postMessage({ type: 'refresh' });
                    });
                    
                    // Clear button
                    document.querySelector('.clear-button').addEventListener('click', () => {
                        vscode.postMessage({ type: 'clear' });
                    });
                    
                    // Action buttons
                    document.querySelectorAll('.action-button').forEach(button => {
                        button.addEventListener('click', () => {
                            const action = button.getAttribute('data-action');
                            const id = button.getAttribute('data-id');
                            vscode.postMessage({ type: action, id });
                        });
                    });
                })();
            </script>
        </body>
        </html>`;
    }

    private _showDetails(id: string) {
        const item = this._historyItems.find(item => item.id === id);
        if (!item) {
            return;
        }

        // Create a webview panel to show details
        const panel = vscode.window.createWebviewPanel(
            'prismataDetails',
            `Prismata: ${item.type} Details`,
            vscode.ViewColumn.One,
            { enableScripts: true }
        );

        // Format the details as JSON
        const detailsJson = JSON.stringify(item.details || {}, null, 2);

        panel.webview.html = `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Operation Details</title>
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
                .subtitle {
                    color: var(--vscode-descriptionForeground);
                    margin-bottom: 5px;
                }
                pre {
                    background-color: var(--vscode-editor-background);
                    padding: 10px;
                    border-radius: 5px;
                    overflow: auto;
                    white-space: pre-wrap;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">${item.type} Operation</div>
                <div class="subtitle">Status: ${item.status}</div>
                <div class="subtitle">Time: ${new Date(item.timestamp).toLocaleString()}</div>
                <div class="subtitle">Description: ${item.description}</div>
            </div>
            
            <h3>Details:</h3>
            <pre>${detailsJson}</pre>
        </body>
        </html>`;
    }

    private _retryOperation(id: string) {
        const item = this._historyItems.find(item => item.id === id);
        if (!item || item.status !== 'error') {
            return;
        }

        // Implement retry logic based on operation type
        vscode.window.showInformationMessage(`Retrying ${item.type} operation...`);
        
        // This is a placeholder. In a real implementation, you would call the appropriate
        // method on the agent service to retry the operation.
        // For example:
        // if (item.type === 'generate_code') {
        //     this._agentService.generateCode(...);
        // }
    }
}
