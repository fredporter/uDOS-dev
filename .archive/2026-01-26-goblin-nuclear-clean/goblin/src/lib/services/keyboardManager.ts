/**
 * Global Keyboard Manager for uDOS
 *
 * Handles:
 * - Function key (F1-F12) actions
 * - Command key (⌘) remapping to F keys via number keys
 * - CTRL as alias of ⌘
 * - SHIFT/OPTION toggle for keypad layers
 * - Copy buffer management (persisted to user sandbox)
 */

import { invoke } from "@tauri-apps/api/core";

export type KeypadLayer = "function" | "number" | "arrows";

export interface CopyBufferItem {
  id: string;
  text: string;
  timestamp: number;
  source?: string;
}

// Global state
let copyBuffer: CopyBufferItem[] = [];
let keypadLayer: KeypadLayer = "number";
let keypadLayerChangeCallbacks: ((layer: KeypadLayer) => void)[] = [];
let copyBufferChangeCallbacks: ((buffer: CopyBufferItem[]) => void)[] = [];
let copyBufferLoaded = false;

const MAX_COPY_BUFFER_SIZE = 50;
// Path is relative to project root, resolved by backend API
const COPY_BUFFER_PATH = "memory/sandbox/copy-buffer.json";

/**
 * F1-F12 Action Mappings
 * Based on uDOS beta version conventions
 * Each F-key has corresponding NUM key alias (Cmd/Ctrl + 1-9,0,-,=)
 */
const FUNCTION_KEY_ACTIONS: Record<string, () => void | Promise<void>> = {
  F1: () => {
    // Help / Documentation (Cmd+1)
    console.log("[Keyboard] F1/Cmd+1: Opening help");
    window.location.href = "/knowledge";
  },
  F2: () => {
    // Toggle Edit Mode (Cmd+2)
    console.log("[Keyboard] F2/Cmd+2: Toggle edit mode");
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("toggle-edit", {});
    });
  },
  F3: () => {
    // Open File Picker (Cmd+3)
    console.log("[Keyboard] F3/Cmd+3: Toggle file picker");
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("toggle-sidebar-request", {});
    });
  },
  F4: () => {
    // Cycle Mode Forward (Cmd+4)
    console.log("[Keyboard] F4/Cmd+4: Cycle mode forward");
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("cycle-mode-forward", {});
    });
  },
  F5: () => {
    // Refresh/Reload (Cmd+5)
    console.log("[Keyboard] F5/Cmd+5: Refresh page");
    window.location.reload();
  },
  F6: () => {
    // Toggle Copy Buffer (Cmd+6)
    console.log("[Keyboard] F6/Cmd+6: Toggle copy buffer");
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("toggle-copy-buffer", {});
    });
  },
  F7: () => {
    // Cycle Mode Backward (Cmd+7)
    console.log("[Keyboard] F7/Cmd+7: Cycle mode backward");
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("cycle-mode-backward", {});
    });
  },
  F8: () => {
    // Presentation Mode (Cmd+8)
    console.log("[Keyboard] F8/Cmd+8: Toggle presentation mode");
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("toggle-presentation", {});
    });
  },
  F9: () => {
    // Open Terminal (Cmd+9)
    console.log("[Keyboard] F9/Cmd+9: Open terminal");
    window.location.href = "/terminal";
  },
  F10: () => {
    // Restart App (Cmd+0)
    console.log("[Keyboard] F10/Cmd+0: Restart application");
    import("@tauri-apps/plugin-process").then(({ relaunch }) => {
      relaunch();
    });
  },
  F11: () => {
    // Toggle Fullscreen (Cmd+-)
    console.log("[Keyboard] F11/Cmd+-: Toggle fullscreen");
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      document.documentElement.requestFullscreen?.();
    }
  },
  F12: () => {
    // Debug Panel (Cmd+=)
    console.log("[Keyboard] F12/Cmd+=: Toggle debug panel");
    try {
      import("$lib/stores/debugPanel")
        .then(({ toggleDebugPanel }) => {
          toggleDebugPanel();
          console.log("[Keyboard] Debug panel toggled");
        })
        .catch((err) => {
          console.error("[Keyboard] Failed to toggle debug panel:", err);
        });
    } catch (error) {
      console.error("[Keyboard] F12 handler error:", error);
    }
  },
};

/**
 * Number key to F-key mapping
 * ⌘/CTRL + 1-9,0,-,= maps to F1-F12
 */
const NUMBER_TO_FKEY: Record<string, string> = {
  "1": "F1",
  "2": "F2",
  "3": "F3",
  "4": "F4",
  "5": "F5",
  "6": "F6",
  "7": "F7",
  "8": "F8",
  "9": "F9",
  "0": "F10",
  "-": "F11",
  "=": "F12",
};

/**
 * Additional global shortcuts
 * ⌘/CTRL + K/T/B/P for UI controls
 */
const GLOBAL_SHORTCUTS: Record<string, () => void> = {
  k: () => {
    // Command Palette (Flyin)
    console.log("[Keyboard] Cmd+K: Toggle command palette");
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("toggle-flyin", {});
    });
  },
  t: () => {
    // Cycle ticker mode
    console.log("[Keyboard] Cmd+T: Cycle ticker mode");
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("cycle-ticker-mode", {});
    });
  },
  b: () => {
    // Toggle sidebar
    console.log("[Keyboard] Cmd+B: Toggle sidebar");
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("toggle-sidebar-request", {});
    });
  },
  p: () => {
    // Toggle keypad
    console.log("[Keyboard] Cmd+P: Toggle keypad");
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("toggle-keypad", {});
    });
  },
};

/**
 * Initialize global keyboard handler
 */
export function initKeyboardManager() {
  console.log("[KeyboardManager] Initializing global keyboard manager");

  // Load copy buffer from persistent storage
  loadCopyBuffer();

  document.addEventListener("keydown", handleGlobalKeydown);

  return () => {
    document.removeEventListener("keydown", handleGlobalKeydown);
  };
}

/**
 * Load copy buffer from user sandbox
 */
async function loadCopyBuffer() {
  if (copyBufferLoaded) return;

  try {
    const content = await invoke<string>("read_file", {
      path: COPY_BUFFER_PATH,
    });
    const data = JSON.parse(content);
    if (Array.isArray(data)) {
      copyBuffer = data;
      copyBufferLoaded = true;
      console.log(
        "[KeyboardManager] Loaded copy buffer:",
        copyBuffer.length,
        "items",
      );
      // Notify listeners
      copyBufferChangeCallbacks.forEach((cb) => cb([...copyBuffer]));
    }
  } catch (err) {
    // File may not exist yet, that's OK
    console.log(
      "[KeyboardManager] No existing copy buffer found, starting fresh",
    );
    copyBufferLoaded = true;
  }
}

/**
 * Save copy buffer to user sandbox
 */
async function saveCopyBuffer() {
  try {
    await invoke("write_file", {
      path: COPY_BUFFER_PATH,
      content: JSON.stringify(copyBuffer, null, 2),
    });
    console.log(
      "[KeyboardManager] Saved copy buffer:",
      copyBuffer.length,
      "items",
    );
  } catch (err) {
    console.error("[KeyboardManager] Failed to save copy buffer:", err);
  }
}

/**
 * Global keydown handler
 */
function handleGlobalKeydown(e: KeyboardEvent) {
  const isCmd = e.metaKey || e.ctrlKey; // ⌘ or CTRL (aliases)
  const isShift = e.shiftKey || e.altKey; // SHIFT or OPTION (aliases)

  // Handle ⌘/CTRL + Letter shortcuts (K/T/B/P)
  if (isCmd && GLOBAL_SHORTCUTS[e.key.toLowerCase()]) {
    e.preventDefault();
    console.log(
      `[KeyboardManager] ${e.metaKey ? "⌘" : "CTRL"} + ${e.key.toUpperCase()}`,
    );
    GLOBAL_SHORTCUTS[e.key.toLowerCase()]();
    return;
  }

  // Handle ⌘/CTRL + Number keys (F1-F12 aliases)
  if (isCmd && NUMBER_TO_FKEY[e.key]) {
    e.preventDefault();
    const fKey = NUMBER_TO_FKEY[e.key];
    console.log(
      `[KeyboardManager] ${e.metaKey ? "⌘" : "CTRL"} + ${e.key} → ${fKey}`,
    );
    executeFunctionKey(fKey);
    return;
  }

  // Handle direct F1-F12 keys with ⌘/CTRL
  if (isCmd && e.key.startsWith("F") && FUNCTION_KEY_ACTIONS[e.key]) {
    e.preventDefault();
    console.log(`[KeyboardManager] ${e.metaKey ? "⌘" : "CTRL"} + ${e.key}`);
    executeFunctionKey(e.key);
    return;
  }

  // Note: F12 opens browser DevTools (Cmd+Option+I)
  // Cannot be programmatically triggered for security reasons

  // Handle bare F1-F12 keys (without modifiers)
  if (e.key.startsWith("F") && FUNCTION_KEY_ACTIONS[e.key]) {
    e.preventDefault();
    console.log(`[KeyboardManager] ${e.key} (bare)`);
    executeFunctionKey(e.key);
    return;
  }

  // Handle SHIFT/OPTION toggle for keypad layer
  if (e.key === "Shift" || e.key === "Alt") {
    toggleKeypadLayer();
  }
}

/**
 * Execute a function key action
 */
function executeFunctionKey(key: string) {
  const action = FUNCTION_KEY_ACTIONS[key];
  if (action) {
    action();
  } else {
    console.warn(`[KeyboardManager] No action defined for ${key}`);
  }
}

/**
 * Toggle between keypad layers
 */
export function toggleKeypadLayer() {
  const layers: KeypadLayer[] = ["function", "number", "arrows"];
  const currentIndex = layers.indexOf(keypadLayer);
  keypadLayer = layers[(currentIndex + 1) % layers.length];

  console.log("[KeyboardManager] Keypad layer:", keypadLayer);

  // Notify all listeners
  keypadLayerChangeCallbacks.forEach((cb) => cb(keypadLayer));
}

/**
 * Get current keypad layer
 */
export function getKeypadLayer(): KeypadLayer {
  return keypadLayer;
}

/**
 * Set keypad layer
 */
export function setKeypadLayer(layer: KeypadLayer) {
  keypadLayer = layer;
  keypadLayerChangeCallbacks.forEach((cb) => cb(layer));
}

/**
 * Subscribe to keypad layer changes
 */
export function onKeypadLayerChange(
  callback: (layer: KeypadLayer) => void,
): () => void {
  keypadLayerChangeCallbacks.push(callback);
  return () => {
    keypadLayerChangeCallbacks = keypadLayerChangeCallbacks.filter(
      (cb) => cb !== callback,
    );
  };
}

/**
 * Add item to copy buffer
 */
export function addToCopyBuffer(text: string, source?: string) {
  if (!text || text.trim().length === 0) return;

  const item: CopyBufferItem = {
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    text: text.trim(),
    timestamp: Date.now(),
    source,
  };

  // Add to beginning of buffer
  copyBuffer.unshift(item);

  // Trim to max size
  if (copyBuffer.length > MAX_COPY_BUFFER_SIZE) {
    copyBuffer = copyBuffer.slice(0, MAX_COPY_BUFFER_SIZE);
  }

  console.log(
    "[KeyboardManager] Added to copy buffer:",
    text.substring(0, 50) + (text.length > 50 ? "..." : ""),
  );

  // Notify listeners
  copyBufferChangeCallbacks.forEach((cb) => cb([...copyBuffer]));

  // Persist to storage
  saveCopyBuffer();
}

/**
 * Get copy buffer
 */
export function getCopyBuffer(): CopyBufferItem[] {
  return [...copyBuffer];
}

/**
 * Clear copy buffer
 */
export function clearCopyBuffer() {
  copyBuffer = [];
  copyBufferChangeCallbacks.forEach((cb) => cb([]));
  saveCopyBuffer();
}

/**
 * Remove item from copy buffer
 */
export function removeFromCopyBuffer(id: string) {
  copyBuffer = copyBuffer.filter((item) => item.id !== id);
  copyBufferChangeCallbacks.forEach((cb) => cb([...copyBuffer]));
  saveCopyBuffer();
}

/**
 * Subscribe to copy buffer changes
 */
export function onCopyBufferChange(
  callback: (buffer: CopyBufferItem[]) => void,
): () => void {
  copyBufferChangeCallbacks.push(callback);
  // Call immediately with current buffer
  callback([...copyBuffer]);
  return () => {
    copyBufferChangeCallbacks = copyBufferChangeCallbacks.filter(
      (cb) => cb !== callback,
    );
  };
}

/**
 * Copy item to clipboard
 */
export async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    console.log(
      "[KeyboardManager] Copied to clipboard:",
      text.substring(0, 50) + (text.length > 50 ? "..." : ""),
    );
  } catch (err) {
    console.error("[KeyboardManager] Failed to copy to clipboard:", err);
  }
}
