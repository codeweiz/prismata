import * as vscode from 'vscode';
import * as path from 'path';
import * as cp from 'child_process';
import * as WebSocket from 'ws';
import { EventEmitter } from 'events';

export class AgentService extends EventEmitter {
    private context: vscode.ExtensionContext;
    private agentProcess: cp.ChildProcess | null = null;
    private ws: WebSocket | null = null;
    private requestMap = new Map<string, { resolve: Function, reject: Function }>();
    private nextRequestId = 1;
    private _isRunning: boolean = false;
    private _history: any[] = [];

    constructor(context: vscode.ExtensionContext) {
        super();
        this.context = context;
    }

    /**
     * Start the agent process
     */
    public async startAgent(): Promise<void> {
        if (this.agentProcess) {
            return; // Already started
        }

        const config = vscode.workspace.getConfiguration('prismata');
        const agentPath = config.get<string>('agentPath');
        const serverHost = config.get<string>('serverHost') || 'localhost';
        const serverPort = config.get<number>('serverPort') || 8765;

        return new Promise<void>((resolve, reject) => {
            try {
                // If agent path is provided, start the agent as a child process
                if (agentPath) {
                    this.agentProcess = cp.spawn('python', [agentPath], {
                        cwd: path.dirname(agentPath),
                        env: { ...process.env }
                    });

                    this.agentProcess.stdout?.on('data', (data) => {
                        console.log(`Agent stdout: ${data}`);
                    });

                    this.agentProcess.stderr?.on('data', (data) => {
                        console.error(`Agent stderr: ${data}`);
                    });

                    this.agentProcess.on('error', (error) => {
                        console.error(`Agent process error: ${error}`);
                        this.agentProcess = null;
                        reject(error);
                    });

                    this.agentProcess.on('exit', (code, signal) => {
                        console.log(`Agent process exited with code ${code} and signal ${signal}`);
                        this.agentProcess = null;
                    });
                }

                // Connect to the agent via WebSocket
                setTimeout(() => {
                    this.connectWebSocket(serverHost, serverPort)
                        .then(() => {
                            this._isRunning = true;
                            this.emit('statusChange', true);
                            resolve();
                        })
                        .catch(reject);
                }, 1000); // Give the agent a second to start up
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Stop the agent process
     */
    public async stopAgent(): Promise<void> {
        // Close WebSocket connection
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        // Kill agent process
        if (this.agentProcess) {
            this.agentProcess.kill();
            this.agentProcess = null;
        }

        // Update status
        this._isRunning = false;
        this.emit('statusChange', false);
    }

    /**
     * Connect to the agent via WebSocket
     */
    private async connectWebSocket(host: string, port: number): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            try {
                const url = `ws://${host}:${port}`;
                this.ws = new WebSocket(url);

                this.ws.on('open', () => {
                    console.log(`Connected to agent at ${url}`);
                    resolve();
                });

                this.ws.on('message', (data) => {
                    try {
                        const response = JSON.parse(data.toString());
                        const id = response.id;
                        const pending = this.requestMap.get(id.toString());

                        if (pending) {
                            this.requestMap.delete(id.toString());
                            if (response.error) {
                                pending.reject(new Error(response.error.message));
                            } else {
                                pending.resolve(response.result);
                            }
                        }
                    } catch (error) {
                        console.error('Error processing WebSocket message:', error);
                    }
                });

                this.ws.on('error', (error) => {
                    console.error(`WebSocket error: ${error}`);
                    reject(error);
                });

                this.ws.on('close', () => {
                    console.log('WebSocket connection closed');
                    this.ws = null;
                });
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Send a request to the agent
     */
    public async sendRequest(method: string, params: any): Promise<any> {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('Agent not connected');
        }

        return new Promise((resolve, reject) => {
            const id = (this.nextRequestId++).toString();
            const request = {
                jsonrpc: '2.0',
                id,
                method,
                params
            };

            this.requestMap.set(id, { resolve, reject });
            this.ws!.send(JSON.stringify(request));
        });
    }

    /**
     * Generate code based on a prompt
     */
    public async generateCode(
        prompt: string,
        context?: string,
        language?: string,
        useProjectContext: boolean = true
    ): Promise<any> {
        const editor = vscode.window.activeTextEditor;
        const document = editor?.document;

        // Determine language from document if not provided
        if (!language && document) {
            language = document.languageId;
        }

        // Get selected text as context if not provided
        if (!context && editor) {
            const selection = editor.selection;
            if (!selection.isEmpty) {
                context = document?.getText(selection);
            }
        }

        // Get file path for project context
        const filePath = document?.uri.fsPath;

        return this.sendRequest('generate_code', {
            prompt,
            context,
            language: language || 'plaintext',
            file_path: filePath,
            options: {
                use_project_context: useProjectContext,
                max_context_files: 3
            }
        });
    }

    /**
     * Analyze code
     */
    public async analyzeCode(filePath?: string): Promise<any> {
        const editor = vscode.window.activeTextEditor;
        const document = editor?.document;

        // Use current file if not provided
        if (!filePath && document) {
            filePath = document.uri.fsPath;
        }

        if (!filePath) {
            throw new Error('No file to analyze');
        }

        return this.sendRequest('analyze_code', {
            file_path: filePath,
            content: document?.getText()
        });
    }

    /**
     * Analyze dependencies between multiple files
     */
    public async analyzeCrossFileDependencies(filePaths: string[]): Promise<any> {
        if (!filePaths || filePaths.length === 0) {
            throw new Error('No files to analyze');
        }

        // Read file contents
        const contentMap: Record<string, string> = {};
        for (const filePath of filePaths) {
            try {
                const document = await vscode.workspace.openTextDocument(filePath);
                contentMap[filePath] = document.getText();
            } catch (error) {
                console.error(`Error reading file ${filePath}:`, error);
                // Continue with other files
            }
        }

        return this.sendRequest('analyze_cross_file_dependencies', {
            file_paths: filePaths,
            content_map: contentMap,
            options: {}
        });
    }

    /**
     * Refactor code
     */
    public async refactorCode(
        refactoringType: string,
        filePaths: string[],
        targetSymbol?: string,
        newName?: string,
        selection?: Record<string, { start: { line: number, character: number }, end: { line: number, character: number } }>,
        options?: Record<string, any>
    ): Promise<any> {
        if (!filePaths || filePaths.length === 0) {
            throw new Error('No files to refactor');
        }

        if (refactoringType === 'rename' && (!targetSymbol || !newName)) {
            throw new Error('Rename refactoring requires target symbol and new name');
        }

        if (refactoringType === 'extract_method' && !selection) {
            throw new Error('Extract method refactoring requires a selection');
        }

        return this.sendRequest('refactor_code', {
            refactoring_type: refactoringType,
            file_paths: filePaths,
            target_symbol: targetSymbol,
            new_name: newName,
            selection: selection,
            options: options || {}
        });
    }

    /**
     * Complete code at the current position
     */
    public async completeCode(
        filePath: string,
        position: { line: number, character: number },
        prefix?: string,
        context?: string,
        options?: Record<string, any>
    ): Promise<any> {
        if (!filePath) {
            throw new Error('No file path provided');
        }

        return this.sendRequest('complete_code', {
            file_path: filePath,
            position: position,
            prefix: prefix,
            context: context,
            options: options || {}
        });
    }

    /**
     * Get operation history
     */
    public async getOperationHistory(
        operationType?: string,
        status?: string,
        limit: number = 100,
        offset: number = 0
    ): Promise<any> {
        return this.sendRequest('get_operation_history', {
            operation_type: operationType,
            status: status,
            limit: limit,
            offset: offset
        });
    }

    /**
     * Get operation details
     */
    public async getOperation(operationId: string): Promise<any> {
        if (!operationId) {
            throw new Error('No operation ID provided');
        }

        return this.sendRequest('get_operation', {
            operation_id: operationId
        });
    }

    /**
     * Retry an operation
     */
    public async retryOperation(operationId: string): Promise<any> {
        if (!operationId) {
            throw new Error('No operation ID provided');
        }

        return this.sendRequest('retry_operation', {
            operation_id: operationId
        });
    }

    /**
     * Recover an operation
     */
    public async recoverOperation(operationId: string, strategyName: string): Promise<any> {
        if (!operationId) {
            throw new Error('No operation ID provided');
        }

        if (!strategyName) {
            throw new Error('No strategy name provided');
        }

        return this.sendRequest('recover_operation', {
            operation_id: operationId,
            strategy_name: strategyName
        });
    }

    /**
     * Read a file
     */
    public async readFile(filePath?: string, encoding: string = 'utf-8'): Promise<any> {
        // Use current file if not provided
        if (!filePath) {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                filePath = editor.document.uri.fsPath;
            }
        }

        if (!filePath) {
            throw new Error('No file to read');
        }

        return this.sendRequest('read_file', {
            file_path: filePath,
            encoding
        });
    }

    /**
     * Get file metadata
     */
    public async getFileMetadata(filePath?: string): Promise<any> {
        // Use current file if not provided
        if (!filePath) {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                filePath = editor.document.uri.fsPath;
            }
        }

        if (!filePath) {
            throw new Error('No file to get metadata for');
        }

        return this.sendRequest('get_file_metadata', {
            file_path: filePath
        });
    }

    /**
     * Write to a file
     */
    public async writeFile(filePath: string, content: string, encoding: string = 'utf-8', createBackup: boolean = true): Promise<any> {
        return this.sendRequest('write_file', {
            file_path: filePath,
            content,
            encoding,
            create_backup: createBackup
        });
    }

    /**
     * Confirm a file write operation
     */
    public async confirmWriteFile(filePath: string, content: string, encoding: string = 'utf-8', createBackup: boolean = true): Promise<any> {
        return this.sendRequest('confirm_write_file', {
            file_path: filePath,
            content,
            encoding,
            create_backup: createBackup
        });
    }

    /**
     * Check if the agent is running
     */
    public isAgentRunning(): boolean {
        return this._isRunning;
    }

    /**
     * Register a status change listener
     */
    public onStatusChange(listener: (isRunning: boolean) => void): void {
        this.on('statusChange', listener);
    }

    /**
     * Register a history update listener
     */
    public onHistoryUpdate(listener: (history: any[]) => void): void {
        this.on('historyUpdate', listener);
    }

    /**
     * Get operation history
     */
    public async getHistory(): Promise<any[]> {
        // In a real implementation, this would fetch history from the agent
        // For now, we'll just return the cached history
        this.emit('historyUpdate', this._history);
        return this._history;
    }
}
