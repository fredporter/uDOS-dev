/**
 * Copy Buffer Logger
 * - Logs copy buffer items to markdown files in memory/logs
 * - Dedupe via normalized hash (whitespace-insensitive)
 * - Updates usage count and lastSeen for re-snips
 * - Archives entries older than 7 days, excessively large, or high usage
 */

import { invoke } from "@tauri-apps/api/core";
import type { CopyBufferItem } from "$lib/services/keyboardManager";

interface CopyLogEntry {
  id: string; // normalized hash
  rawHash: string;
  length: number;
  excerpt: string;
  firstSeen: number; // epoch ms
  lastSeen: number; // epoch ms
  usageCount: number;
  archived?: boolean;
}

const MAX_EXCERPT_LEN = 256;
const LARGE_SNIP_LEN = 4096;
const EXCESSIVE_USE_COUNT = 10;
const RETENTION_DAYS = 7;

class CopyBufferLogger {
  private logFilePath: string;
  private archiveFilePath: string;
  private entries: Map<string, CopyLogEntry> = new Map();
  private sessionStartIso: string;

  constructor() {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, "0");
    const dd = String(now.getDate()).padStart(2, "0");
    const hh = String(now.getHours()).padStart(2, "0");
    const ss = String(now.getMinutes()).padStart(2, "0");
    this.sessionStartIso = now.toISOString();
    this.logFilePath = `copy-buffer-${yyyy}-${mm}-${dd}-${hh}-${ss}.md`;
    this.archiveFilePath = `copy-buffer-archive.md`;
    this.writeHeader();
  }

  private async writeHeader() {
    const header = [
      `# uDOS Copy Buffer Log`,
      `Session started: ${this.sessionStartIso}`,
      `Active file: ${this.logFilePath}`,
      `Retention: ${RETENTION_DAYS} days (earlier archive on large/excessive use)`,
      ``,
      `---`,
      ``,
    ].join("\n");
    try {
      await invoke("append_log_file", {
        filename: this.logFilePath,
        content: header,
      });
    } catch (e) {
      console.error("Failed to write copy buffer header", e);
    }
  }

  private normalize(text: string): string {
    return text.replace(/\s+/g, " ").trim();
  }

  private hash(text: string): string {
    let h = 0;
    for (let i = 0; i < text.length; i++) {
      h = (h << 5) - h + text.charCodeAt(i);
      h |= 0;
    }
    return Math.abs(h).toString(16);
  }

  private makeExcerpt(text: string): string {
    const trimmed = text.trim();
    if (trimmed.length <= MAX_EXCERPT_LEN) return trimmed;
    return trimmed.slice(0, MAX_EXCERPT_LEN) + "…";
  }

  private formatLine(
    type: "NEW" | "UPDATE" | "ARCHIVE",
    entry: CopyLogEntry
  ): string {
    const ts = new Date(entry.lastSeen).toISOString();
    const parts = [
      `* ${type}`,
      ts,
      `len=${entry.length}`,
      `uses=${entry.usageCount}`,
      `hash=${entry.rawHash}`,
      `excerpt: ${entry.excerpt.replace(/\n/g, " ")}`,
    ];
    return parts.join(" | ");
  }

  private async appendActive(line: string) {
    try {
      await invoke("append_log_file", {
        filename: this.logFilePath,
        content: line + "\n",
      });
    } catch (e) {
      console.error("Failed to append active copy buffer log", e);
    }
  }

  private async appendArchive(line: string) {
    try {
      await invoke("append_log_file", {
        filename: this.archiveFilePath,
        content: line + "\n",
      });
    } catch (e) {
      console.error("Failed to append archive copy buffer log", e);
    }
  }

  /** Sync current buffer items: add new or update existing. */
  async sync(items: CopyBufferItem[]) {
    const now = Date.now();
    for (const item of items) {
      const normalized = this.normalize(item.text);
      const id = this.hash(normalized);
      const rawHash = this.hash(item.text);
      const existing = this.entries.get(id);
      if (!existing) {
        const entry: CopyLogEntry = {
          id,
          rawHash,
          length: item.text.length,
          excerpt: this.makeExcerpt(item.text),
          firstSeen: now,
          lastSeen: now,
          usageCount: 1,
        };
        this.entries.set(id, entry);
        await this.appendActive(this.formatLine("NEW", entry));
      } else {
        existing.lastSeen = now;
        existing.length = item.text.length;
        existing.excerpt = this.makeExcerpt(item.text);
        existing.usageCount += 1;
        await this.appendActive(this.formatLine("UPDATE", existing));
      }
    }
  }

  /** Archive entries by policy. */
  async cleanup() {
    const now = Date.now();
    const maxAgeMs = RETENTION_DAYS * 24 * 60 * 60 * 1000;
    for (const [id, entry] of [...this.entries]) {
      const age = now - entry.firstSeen;
      const shouldArchive =
        age > maxAgeMs ||
        entry.length > LARGE_SNIP_LEN ||
        entry.usageCount > EXCESSIVE_USE_COUNT;
      if (shouldArchive && !entry.archived) {
        entry.archived = true;
        await this.appendArchive(this.formatLine("ARCHIVE", entry));
        this.entries.delete(id);
      }
    }
  }
}

export const copyBufferLogger = new CopyBufferLogger();
