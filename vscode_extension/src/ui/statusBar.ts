import * as vscode from 'vscode';
import { AgentService } from '../services/agentService';

/**
 * Status bar manager for Prismata
 */
export class StatusBarManager {
    private statusBarItem: vscode.StatusBarItem;
    private agentService: AgentService;
    private isAgentRunning: boolean = false;

    constructor(agentService: AgentService) {
        this.agentService = agentService;
        
        // Create status bar item
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.command = 'prismata.showMenu';
        this.updateStatusBar(false);
        this.statusBarItem.show();
        
        // Listen for agent status changes
        this.agentService.onStatusChange((isRunning: boolean) => {
            this.isAgentRunning = isRunning;
            this.updateStatusBar(isRunning);
        });
    }

    /**
     * Update the status bar item
     */
    public updateStatusBar(isRunning: boolean, isBusy: boolean = false): void {
        if (isRunning) {
            if (isBusy) {
                this.statusBarItem.text = '$(sync~spin) Prismata';
                this.statusBarItem.tooltip = 'Prismata is processing a request...';
            } else {
                this.statusBarItem.text = '$(check) Prismata';
                this.statusBarItem.tooltip = 'Prismata is running. Click to show menu.';
            }
            this.statusBarItem.backgroundColor = undefined;
        } else {
            this.statusBarItem.text = '$(stop) Prismata';
            this.statusBarItem.tooltip = 'Prismata is not running. Click to start.';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        }
    }

    /**
     * Set the status bar to busy state
     */
    public setBusy(isBusy: boolean): void {
        this.updateStatusBar(this.isAgentRunning, isBusy);
    }

    /**
     * Dispose the status bar item
     */
    public dispose(): void {
        this.statusBarItem.dispose();
    }
}
