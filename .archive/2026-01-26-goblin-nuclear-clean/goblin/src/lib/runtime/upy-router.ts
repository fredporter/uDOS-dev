/**
 * Hybrid uPY Execution Router
 *
 * Routes uPY execution between:
 * - Client-side runtime (fast, no network)
 * - API-based execution (file I/O, mesh, system commands)
 */

import { parse, requiresAPI, type ASTNode } from "./upy-parser";
import { ClientUPYRuntime, type ExecutionResult } from "./upy-runtime";
import { apiRequest, isApiAvailable } from "$lib";

export interface HybridExecutionResult extends ExecutionResult {
  executedOn: "client" | "api" | "hybrid";
  apiCalls?: number;
}

/**
 * Hybrid execution router
 */
export class HybridUPYRouter {
  private clientRuntime: ClientUPYRuntime;
  private apiAvailable: boolean = false;

  constructor(initialState: Record<string, any> = {}) {
    this.clientRuntime = new ClientUPYRuntime(initialState);
  }

  /**
   * Check API availability
   */
  async checkAPI(): Promise<boolean> {
    this.apiAvailable = await isApiAvailable();
    return this.apiAvailable;
  }

  /**
   * Execute uPY code with smart routing
   */
  async execute(source: string): Promise<HybridExecutionResult> {
    try {
      const ast = parse(source);
      const needsAPI = requiresAPI(ast);

      // If code needs API but API unavailable, return error
      if (needsAPI && !this.apiAvailable) {
        await this.checkAPI(); // Re-check
        if (!this.apiAvailable) {
          return {
            success: false,
            output: [],
            state: this.clientRuntime.getState(),
            error:
              "API required but unavailable. Operations like FILE, MESH, BACKUP need the API server.",
            executedOn: "client",
          };
        }
      }

      // Pure client-side execution
      if (!needsAPI) {
        const result = this.clientRuntime.execute(source);
        return {
          ...result,
          executedOn: "client",
        };
      }

      // API-based execution
      return await this.executeViaAPI(source);
    } catch (error) {
      return {
        success: false,
        output: [],
        state: this.clientRuntime.getState(),
        error: error instanceof Error ? error.message : String(error),
        executedOn: "client",
      };
    }
  }

  /**
   * Execute code via API
   */
  private async executeViaAPI(source: string): Promise<HybridExecutionResult> {
    try {
      const response = await apiRequest<{
        success: boolean;
        output: string;
        error?: string;
        state?: Record<string, any>;
      }>("/api/upy/execute", {
        method: "POST",
        body: JSON.stringify({
          code: source,
          state: this.clientRuntime.getState(),
        }),
      });

      if (response.ok && response.data) {
        // Sync state from API
        if (response.data.state) {
          this.clientRuntime.setState(response.data.state);
        }

        return {
          success: response.data.success,
          output: response.data.output?.split("\n") || [],
          state: this.clientRuntime.getState(),
          error: response.data.error,
          executedOn: "api",
          apiCalls: 1,
        };
      }

      return {
        success: false,
        output: [],
        state: this.clientRuntime.getState(),
        error: response.error || "API request failed",
        executedOn: "api",
        apiCalls: 1,
      };
    } catch (error) {
      return {
        success: false,
        output: [],
        state: this.clientRuntime.getState(),
        error: error instanceof Error ? error.message : "API execution failed",
        executedOn: "api",
        apiCalls: 1,
      };
    }
  }

  /**
   * Execute a single command (for terminal use)
   */
  async executeCommand(command: string): Promise<HybridExecutionResult> {
    // Check if it's a native TUI command (uppercase, no uPY syntax)
    const isNativeCommand = /^[A-Z]+(\s|$)/.test(command.trim());

    if (isNativeCommand) {
      // Always route native commands to API
      return this.executeNativeCommand(command);
    }

    // Otherwise treat as uPY code
    return this.execute(command);
  }

  /**
   * Execute native TUI command via API
   */
  private async executeNativeCommand(
    command: string
  ): Promise<HybridExecutionResult> {
    if (!this.apiAvailable) {
      await this.checkAPI();
    }

    if (!this.apiAvailable) {
      return {
        success: false,
        output: ["Error: API server offline"],
        state: this.clientRuntime.getState(),
        error: "API server required for native commands",
        executedOn: "api",
      };
    }

    try {
      const response = await apiRequest<{
        output: string;
        error?: string;
      }>("/api/tui/command", {
        method: "POST",
        body: JSON.stringify({ command }),
      });

      if (response.ok && response.data) {
        return {
          success: !response.data.error,
          output: response.data.output?.split("\n") || [],
          state: this.clientRuntime.getState(),
          error: response.data.error,
          executedOn: "api",
          apiCalls: 1,
        };
      }

      return {
        success: false,
        output: [],
        state: this.clientRuntime.getState(),
        error: response.error || "Command failed",
        executedOn: "api",
        apiCalls: 1,
      };
    } catch (error) {
      return {
        success: false,
        output: [],
        state: this.clientRuntime.getState(),
        error: error instanceof Error ? error.message : "Command failed",
        executedOn: "api",
        apiCalls: 1,
      };
    }
  }

  /**
   * Get current state
   */
  getState(): Record<string, any> {
    return this.clientRuntime.getState();
  }

  /**
   * Set state
   */
  setState(state: Record<string, any>): void {
    this.clientRuntime.setState(state);
  }

  /**
   * Check if API is available
   */
  isAPIAvailable(): boolean {
    return this.apiAvailable;
  }
}

/**
 * Create a hybrid router instance
 */
export async function createHybridRouter(
  initialState: Record<string, any> = {}
): Promise<HybridUPYRouter> {
  const router = new HybridUPYRouter(initialState);
  await router.checkAPI();
  return router;
}
