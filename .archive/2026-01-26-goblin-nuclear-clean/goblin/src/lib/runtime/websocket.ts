/**
 * WebSocket client for real-time terminal streaming
 *
 * Connects to uDOS API WebSocket for:
 * - Live command output
 * - Log streaming
 * - System events
 */

export interface WSMessage {
  type: "output" | "error" | "status" | "log" | "event";
  data: string;
  timestamp?: string;
  source?: string;
}

export interface WSConnectionState {
  connected: boolean;
  reconnecting: boolean;
  error?: string;
}

type MessageHandler = (message: WSMessage) => void;
type StateHandler = (state: WSConnectionState) => void;

/**
 * WebSocket client for terminal/log streaming
 */
export class TerminalWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Set<MessageHandler> = new Set();
  private stateHandlers: Set<StateHandler> = new Set();
  private state: WSConnectionState = { connected: false, reconnecting: false };
  private hasLoggedConnectionError = false;

  constructor(url: string = "ws://localhost:8765/ws/tui") {
    this.url = url;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        let settled = false; // Track if promise is already resolved/rejected

        this.ws.onopen = () => {
          if (settled) return;
          settled = true;
          this.reconnectAttempts = 0;
          this.hasLoggedConnectionError = false; // Reset on successful connection
          this.updateState({ connected: true, reconnecting: false });
          console.log("[WebSocket] Connected to", this.url);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data);
            this.notifyMessage(message);
          } catch {
            // Plain text message
            this.notifyMessage({
              type: "output",
              data: event.data,
            });
          }
        };

        this.ws.onerror = (error) => {
          // Only log once to avoid console spam
          if (!this.hasLoggedConnectionError) {
            console.log(
              "[WebSocket] Unable to connect to API server on",
              this.url,
              "- using fallback mode"
            );
            this.hasLoggedConnectionError = true;
          }
          this.updateState({
            connected: false,
            reconnecting: false,
            error: "Connection error",
          });
          // Reject the promise if not yet settled (initial connection attempt)
          if (!settled) {
            settled = true;
            reject(new Error("WebSocket connection failed"));
          }
        };

        this.ws.onclose = () => {
          this.updateState({ connected: false, reconnecting: false });
          // Only reject if this is the initial connection attempt
          if (!settled) {
            settled = true;
            reject(new Error("WebSocket connection closed"));
          } else {
            // For subsequent disconnects, try to reconnect
            this.attemptReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.updateState({ connected: false, reconnecting: false });
  }

  /**
   * Send a command to execute
   */
  sendCommand(command: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "command",
          data: command,
        })
      );
    }
  }

  /**
   * Send raw text
   */
  send(data: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    }
  }

  /**
   * Subscribe to messages
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  /**
   * Subscribe to connection state changes
   */
  onStateChange(handler: StateHandler): () => void {
    this.stateHandlers.add(handler);
    // Immediately notify of current state
    handler(this.state);
    return () => this.stateHandlers.delete(handler);
  }

  /**
   * Get current connection state
   */
  getState(): WSConnectionState {
    return { ...this.state };
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private notifyMessage(message: WSMessage): void {
    this.messageHandlers.forEach((handler) => handler(message));
  }

  private updateState(state: WSConnectionState): void {
    this.state = state;
    this.stateHandlers.forEach((handler) => handler(state));
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      if (!this.hasLoggedConnectionError) {
        console.log(
          "[WebSocket] Max reconnection attempts reached - API server offline"
        );
        this.hasLoggedConnectionError = true;
      }
      this.updateState({
        connected: false,
        reconnecting: false,
        error: "Max reconnection attempts reached",
      });
      return;
    }

    this.reconnectAttempts++;
    this.updateState({ connected: false, reconnecting: true });

    setTimeout(() => {
      // Only log first reconnection attempt
      if (this.reconnectAttempts === 1) {
        console.log(`[WebSocket] Attempting to reconnect to API server...`);
      }
      this.connect().catch(() => {
        // Will trigger onclose and retry
      });
    }, this.reconnectDelay * this.reconnectAttempts);
  }
}

/**
 * Create a terminal WebSocket instance
 */
export function createTerminalSocket(url?: string): TerminalWebSocket {
  return new TerminalWebSocket(url);
}

/**
 * Svelte store for WebSocket state
 */
import { writable, type Writable } from "svelte/store";

export interface TerminalWSStore {
  socket: TerminalWebSocket;
  state: Writable<WSConnectionState>;
  messages: Writable<WSMessage[]>;
  connect: () => Promise<void>;
  disconnect: () => void;
  sendCommand: (command: string) => void;
  clearMessages: () => void;
}

/**
 * Create a Svelte store for terminal WebSocket
 */
export function createTerminalWSStore(url?: string): TerminalWSStore {
  const socket = createTerminalSocket(url);
  const state = writable<WSConnectionState>({
    connected: false,
    reconnecting: false,
  });
  const messages = writable<WSMessage[]>([]);

  // Sync state
  socket.onStateChange((s) => state.set(s));

  // Collect messages
  socket.onMessage((msg) => {
    messages.update((msgs) => [...msgs, msg]);
  });

  return {
    socket,
    state,
    messages,
    connect: () => socket.connect(),
    disconnect: () => socket.disconnect(),
    sendCommand: (cmd) => socket.sendCommand(cmd),
    clearMessages: () => messages.set([]),
  };
}
