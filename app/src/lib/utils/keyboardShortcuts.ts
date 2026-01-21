/**
 * Keyboard Shortcuts Manager
 * Handles macOS global keyboard shortcuts
 */

export interface KeyboardShortcut {
  name: string;
  keys: string;
  description: string;
  handler: () => void;
}

export const keyboardShortcuts = {
  shortcuts: new Map<string, KeyboardShortcut>(),

  /**
   * Register a keyboard shortcut
   */
  register(id: string, shortcut: KeyboardShortcut): void {
    this.shortcuts.set(id, shortcut);
  },

  /**
   * Handle keyboard event
   */
  handleKeyDown(event: KeyboardEvent): void {
    const isMacOS = /Mac|iPhone|iPad|iPod/.test(navigator.platform);
    const isCmd = event.metaKey; // Cmd on macOS
    const isCtrl = event.ctrlKey;
    const isShift = event.shiftKey;
    const key = event.key.toLowerCase();

    // Cmd+N: New document
    if (isCmd && key === "n") {
      event.preventDefault();
      const shortcut = this.shortcuts.get("cmd-n");
      if (shortcut) shortcut.handler();
    }
    // Cmd+O: Open file
    else if (isCmd && key === "o") {
      event.preventDefault();
      const shortcut = this.shortcuts.get("cmd-o");
      if (shortcut) shortcut.handler();
    }
    // Cmd+S: Save file
    else if (isCmd && key === "s") {
      event.preventDefault();
      const shortcut = this.shortcuts.get("cmd-s");
      if (shortcut) shortcut.handler();
    }
    // Cmd+Shift+S: Save As
    else if (isCmd && isShift && key === "s") {
      event.preventDefault();
      const shortcut = this.shortcuts.get("cmd-shift-s");
      if (shortcut) shortcut.handler();
    }
    // Cmd+K: Command palette
    else if (isCmd && key === "k") {
      event.preventDefault();
      const shortcut = this.shortcuts.get("cmd-k");
      if (shortcut) shortcut.handler();
    }
    // Cmd+,: Settings
    else if (isCmd && key === ",") {
      event.preventDefault();
      const shortcut = this.shortcuts.get("cmd-comma");
      if (shortcut) shortcut.handler();
    }
    // Cmd+H: Hide window
    else if (isCmd && key === "h") {
      event.preventDefault();
      const shortcut = this.shortcuts.get("cmd-h");
      if (shortcut) shortcut.handler();
    }
    // Cmd+Q: Quit application
    else if (isCmd && key === "q") {
      event.preventDefault();
      const shortcut = this.shortcuts.get("cmd-q");
      if (shortcut) shortcut.handler();
    }
  },

  /**
   * Get all registered shortcuts
   */
  getAll(): KeyboardShortcut[] {
    return Array.from(this.shortcuts.values());
  },

  /**
   * Clear all shortcuts
   */
  clear(): void {
    this.shortcuts.clear();
  },
};

/**
 * Initialize keyboard shortcuts system
 */
export function initKeyboardShortcuts(): void {
  if (typeof window !== "undefined") {
    document.addEventListener("keydown", (e) => keyboardShortcuts.handleKeyDown(e));
  }
}

/**
 * Get shortcut help text
 */
export const SHORTCUTS_HELP = [
  { keys: "Cmd+N", action: "New document" },
  { keys: "Cmd+O", action: "Open file" },
  { keys: "Cmd+S", action: "Save file" },
  { keys: "Cmd+Shift+S", action: "Save As..." },
  { keys: "Cmd+K", action: "Command palette" },
  { keys: "Cmd+,", action: "Settings" },
  { keys: "Cmd+H", action: "Hide window" },
  { keys: "Cmd+Q", action: "Quit application" },
  { keys: "Esc", action: "Toggle editor/preview" },
];
