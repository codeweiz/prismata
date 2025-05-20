import * as vscode from 'vscode';
import * as path from 'path';
import * as cp from 'child_process';
import * as WebSocket from 'ws';

export class AgentService {
    private context: vscode.ExtensionContext;
    private agentProcess: cp.ChildProcess | null = null;
    private ws: WebSocket | null = null;
    private requestMap = new Map<string, { resolve: Function, reject: Function }>();
    private nextRequestId = 1;

    constructor(context: vscode.ExtensionContext) {
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
                        .then(resolve)
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
    public async generateCode(prompt: string, context?: string, language?: string): Promise<any> {
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

        return this.sendRequest('generate_code', {
            prompt,
            context,
            language: language || 'plaintext',
            options: {}
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
}
