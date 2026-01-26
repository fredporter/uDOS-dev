/**
 * Move Logger Service
 * Tracks all user actions/moves across the app
 * - Logs to memory/logs/app-moves-YYYY-MM-DD-HH-SS.md
 * - New log per session (restart/startup) or every 24 hours (midnight reset)
 * - Shows toast notifications for user feedback
 * - Hashes sensitive information
 * - One-line condensed format for step-by-step I/O tracking
 */

import { toastStore } from "$lib/stores/toastStore";
import { invoke } from "@tauri-apps/api/core";
import { writable, type Writable } from "svelte/store";

interface MoveLogEntry {
  timestamp: string;
  action: string;
  context?: string;
  status: "success" | "error" | "info" | "warning";
  metadata?: Record<string, any>;
}

class MoveLogger {
  private logFilePath: string;
  private sessionStartDate: string;
  private maxEntries = 500;
  public store: Writable<MoveLogEntry[]> = writable([]);

  constructor() {
    this.sessionStartDate = this.getCurrentDate();
    this.logFilePath = this.generateLogFilename();
    this.logSessionStart();
  }

  /**
   * Get current date string (YYYY-MM-DD)
   */
  private getCurrentDate(): string {
    return new Date().toISOString().split("T")[0];
  }

  /**
   * Generate log filename with session timestamp
   */
  private generateLogFilename(): string {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, "0");
    const dd = String(now.getDate()).padStart(2, "0");
    const hh = String(now.getHours()).padStart(2, "0");
    const ss = String(now.getMinutes()).padStart(2, "0");
    return `app-moves-${yyyy}-${mm}-${dd}-${hh}-${ss}.md`;
  }

  /**
   * Check if we need to rotate log (new day)
   */
  private checkLogRotation(): void {
    const currentDate = this.getCurrentDate();
    if (currentDate !== this.sessionStartDate) {
      // New day - rotate log file
      this.sessionStartDate = currentDate;
      this.logFilePath = this.generateLogFilename();
      this.logSessionStart();
    }
  }

  /**
   * Log session start marker
   */
  private async logSessionStart(): Promise<void> {
    const header = [
      `# uDOS Move Log`,
      `Session started: ${new Date().toISOString()}`,
      `Log file: ${this.logFilePath}`,
      ``,
      `---`,
      ``,
    ].join("\n");

    try {
      await invoke("append_log_file", {
        filename: this.logFilePath,
        content: header,
      });
    } catch (error) {
      console.error("Failed to write session start:", error);
    }

    // Seed store with session header entry (info)
    const entry: MoveLogEntry = {
      timestamp: new Date().toISOString(),
      action: "Session Start",
      context: this.logFilePath,
      status: "info",
    };
    this.pushToStore(entry);
  }

  /**
   * Hash sensitive information using simple hash
   */
  private hashSensitive(data: string): string {
    if (!data || data.length === 0) return "[empty]";

    // Simple hash for logging (not cryptographic)
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return `[hash:${Math.abs(hash).toString(16)}]`;
  }

  /**
   * Sanitize data by hashing anything that looks sensitive
   */
  private sanitizeData(data: any): any {
    if (typeof data === "string") {
      // Hash if it looks like a path, email, or long content
      if (data.includes("/Users/") || data.includes("@") || data.length > 100) {
        return this.hashSensitive(data);
      }
      return data;
    }
    if (typeof data === "object" && data !== null) {
      const sanitized: Record<string, any> = {};
      for (const [key, value] of Object.entries(data)) {
        if (
          key.toLowerCase().includes("password") ||
          key.toLowerCase().includes("token") ||
          key.toLowerCase().includes("secret") ||
          key.toLowerCase().includes("key")
        ) {
          sanitized[key] = this.hashSensitive(String(value));
        } else {
          sanitized[key] = this.sanitizeData(value);
        }
      }
      return sanitized;
    }
    return data;
  }

  /**
   * Format log entry as one-line string
   */
  private formatLogLine(entry: MoveLogEntry): string {
    const sanitizedContext = entry.context
      ? this.sanitizeData(entry.context)
      : "";
    const metadataStr = entry.metadata
      ? JSON.stringify(this.sanitizeData(entry.metadata))
      : "";

    const parts = [
      entry.timestamp,
      entry.status.toUpperCase(),
      entry.action,
      sanitizedContext,
      metadataStr,
    ].filter((p) => p);

    return parts.join(" | ");
  }

  private pushToStore(entry: MoveLogEntry) {
    // sanitize metadata before storing
    const sanitizedEntry: MoveLogEntry = {
      timestamp: entry.timestamp,
      action: entry.action,
      context: entry.context
        ? String(this.sanitizeData(entry.context))
        : undefined,
      status: entry.status,
      metadata: entry.metadata ? this.sanitizeData(entry.metadata) : undefined,
    };

    this.store.update((arr) => {
      const next = [...arr, sanitizedEntry];
      if (next.length > this.maxEntries) next.shift();
      return next;
    });

    // notify UI of new entry (link to session log)
    try {
      window.dispatchEvent(
        new CustomEvent("session-log:new-entry", { detail: sanitizedEntry })
      );
    } catch {
      // ignore SSR/window absence
    }
  }

  /**
   * Write log entry to file
   */
  private async writeToFile(logLine: string): Promise<void> {
    // Check for log rotation (midnight reset)
    this.checkLogRotation();
    // Check for log rotation (midnight reset)
    this.checkLogRotation();

    try {
      await invoke("append_log_file", {
        filename: this.logFilePath,
        content: logLine + "\n",
      });
    } catch (error) {
      console.error("Failed to write move log:", error);
    }
  }

  /**
   * Log a move/action
   */
  async log(
    action: string,
    context?: string,
    status: MoveLogEntry["status"] = "info",
    metadata?: Record<string, any>,
    showToast: boolean = true
  ): Promise<void> {
    const entry: MoveLogEntry = {
      timestamp: new Date().toISOString(),
      action,
      context,
      status,
      metadata,
    };

    const logLine = this.formatLogLine(entry);

    // Write to file
    await this.writeToFile(logLine);

    // Push to in-memory store
    this.pushToStore(entry);

    // Show toast notification
    if (showToast) {
      const message = context ? `${action}: ${context}` : action;
      switch (status) {
        case "success":
          toastStore.success(message, 2000);
          break;
        case "error":
          // Mention external error log generically without file path
          toastStore.error(`${message} (see error log)`, 3000);
          break;
        case "warning":
          toastStore.warning(message, 2500);
          break;
        case "info":
          toastStore.info(message, 2000);
          break;
      }
    }
  }

  /**
   * Convenience methods for common log types
   */
  async success(action: string, context?: string, showToast = true) {
    return this.log(action, context, "success", undefined, showToast);
  }

  async error(action: string, context?: string, showToast = true) {
    return this.log(action, context, "error", undefined, showToast);
  }

  async info(action: string, context?: string, showToast = false) {
    return this.log(action, context, "info", undefined, showToast);
  }

  async warning(action: string, context?: string, showToast = true) {
    return this.log(action, context, "warning", undefined, showToast);
  }

  /**
   * Log file operations
   */
  async fileOperation(
    operation: string,
    filepath: string,
    status: "success" | "error" = "success"
  ) {
    const hashedPath = this.hashSensitive(filepath);
    return this.log(`File ${operation}`, hashedPath, status);
  }

  /**
   * Log mode switches
   */
  async modeSwitch(fromMode: string, toMode: string) {
    return this.log("Mode Switch", `${fromMode} → ${toMode}`, "info");
  }

  /**
   * Log button/action clicks
   */
  async action(actionName: string, details?: string) {
    return this.log(
      "Action",
      `${actionName}${details ? `: ${details}` : ""}`,
      "info",
      undefined,
      false
    );
  }
}

// Export singleton instance
export const moveLogger = new MoveLogger();
