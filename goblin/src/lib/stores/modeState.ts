/**
 * Mode State Manager - Persistent state across mode switches
 *
 * Stores and retrieves mode-specific settings and the last opened file
 * Syncs to file system via API for cross-instance persistence
 */

import { apiRequest, isApiAvailable } from "./api";
import type { ModeState } from "../types/modes";

export type { ModeState } from "../types/modes";

const DEFAULT_STATE: ModeState = {
  lastFile: null,
  lastMode: "desktop",
  desktop: {
    pattern: "pattern-checkerboard",
    sidebarOpen: false,
    darkMode: true,
    fontSize: 20,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  markdown: {
    fontSize: 20,
    proseSizeIndex: 1,
    headingFont: "sans",
    bodyFont: "sans",
    color: 0,
    viewType: "document",
    sidebarOpen: true,
    viewMode: false,
    darkMode: true,
    monoVariant: "jetbrains",
  },
  read: {
    fontSize: 20,
    proseSizeIndex: 1,
    headingFont: "sans",
    bodyFont: "sans",
    theme: "light",
    viewType: "document",
    viewMode: false,
    sidebarOpen: false,
    darkMode: true,
    monoVariant: "jetbrains",
  },
  table: {
    sortColumn: null,
    sortDirection: "asc",
    sidebarOpen: false,
    darkMode: true,
    fontSize: 20,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  terminal: {
    sidebarOpen: false,
    darkMode: true,
    fontSize: 24,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  teledesk: {
    sidebarOpen: false,
    darkMode: true,
    fontSize: 24,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  blocks: {
    sidebarOpen: false,
    darkMode: true,
    fontSize: 20,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  dashboard: {
    sidebarOpen: false,
    darkMode: true,
    fontSize: 20,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  "pixel-editor": {
    sidebarOpen: true,
    darkMode: true,
    fontSize: 20,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  "layer-editor": {
    sidebarOpen: true,
    darkMode: true,
    fontSize: 20,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  "svg-processor": {
    sidebarOpen: true,
    darkMode: true,
    fontSize: 20,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  knowledge: {
    sidebarOpen: false,
    darkMode: true,
    fontSize: 20,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  present: {
    sidebarOpen: false,
    darkMode: true,
    fontSize: 20,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  grid: {
    sidebarOpen: false,
    darkMode: true,
    fontSize: 24,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
  sprites: {
    sidebarOpen: true,
    darkMode: true,
    fontSize: 20,
    headingFont: "sans",
    bodyFont: "sans",
    monoVariant: "jetbrains",
  },
};

const STORAGE_KEY = "udos-mode-state";
const LAST_FILE_KEY = "udos-last-file";
// Bump version to force re-run of normalization for legacy teletext/pressstart fonts
const MIGRATION_APPLIED_KEY = "udos-mode-state-migrated-v2";

function normalizeState(state: ModeState): {
  state: ModeState;
  changed: boolean;
} {
  let changed = false;

  const forceJetbrains = (modeKey: keyof ModeState) => {
    const mode = state[modeKey] as any;
    if (!mode) return;

    // Mono font must be jetbrains everywhere
    if (mode.monoVariant && mode.monoVariant !== "jetbrains") {
      mode.monoVariant = "jetbrains";
      changed = true;
    }

    // Heading/body fonts revert to sans defaults
    if (mode.headingFont && mode.headingFont !== "sans") {
      mode.headingFont = "sans";
      changed = true;
    }
    if (mode.bodyFont && mode.bodyFont !== "sans") {
      mode.bodyFont = "sans";
      changed = true;
    }
  };

  forceJetbrains("desktop");
  forceJetbrains("markdown");
  forceJetbrains("read");
  forceJetbrains("table");
  forceJetbrains("terminal");
  forceJetbrains("teledesk");
  forceJetbrains("blocks");
  forceJetbrains("pixel-editor");
  forceJetbrains("layer-editor");
  forceJetbrains("knowledge");
  forceJetbrains("svg-processor");
  forceJetbrains("present");
  forceJetbrains("grid");
  forceJetbrains("sprites");

  return { state, changed };
}

let cachedState: ModeState | null = null;

/**
 * Load mode state from API file system (call on app init)
 */
export async function loadModeStateFromAPI(): Promise<boolean> {
  try {
    const available = await isApiAvailable();
    if (!available) {
      console.log("[ModeState] API unavailable - using localStorage only");
      return false;
    }

    const response = await apiRequest<{ state: ModeState }>(
      "/api/settings/mode-state"
    );

    if (response.success && response.data?.state) {
      console.log("[ModeState] Loaded from API file system");
      let loaded = response.data.state;
      // Normalize fonts to JetBrains/sans even for API-loaded state
      const normalized = normalizeState(loaded);
      loaded = normalized.state;

      // Save directly to localStorage without triggering API sync
      if (typeof localStorage !== "undefined") {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(loaded));
        localStorage.setItem(MIGRATION_APPLIED_KEY, "true");
        cachedState = loaded;
      }
      return true;
    }
  } catch (e) {
    console.warn("[ModeState] Failed to load from API:", e);
  }
  return false;
}

/**
 * Sync mode state to API file system
 */
async function syncModeStateToAPI(state: ModeState): Promise<void> {
  const available = await isApiAvailable();
  if (!available) return;

  await apiRequest("/api/settings/mode-state", {
    method: "PUT",
    body: { state },
  });
}

/**
 * Get the complete mode state
 */
export function getModeState(): ModeState {
  if (typeof localStorage === "undefined") return DEFAULT_STATE;

  // Return cached state if available
  if (cachedState) {
    return cachedState;
  }

  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const state = { ...DEFAULT_STATE, ...JSON.parse(saved) };
      const migrationApplied = localStorage.getItem(MIGRATION_APPLIED_KEY);

      // Always normalize; track if any change made
      let needsMigration = false;

      // Migration: Fix any fontSize values that are too small (legacy bug where fontSize was 1)
      if (state.markdown && state.markdown.fontSize < 10) {
        state.markdown.fontSize = 16;
        needsMigration = true;
      }
      if (state.read && state.read.fontSize < 10) {
        state.read.fontSize = 16;
        needsMigration = true;
      }
      if (state.table && state.table.fontSize < 10) {
        state.table.fontSize = 16;
        needsMigration = true;
      }
      if (state.desktop && state.desktop.fontSize < 10) {
        state.desktop.fontSize = 16;
        needsMigration = true;
      }
      if (state.terminal && state.terminal.fontSize < 10) {
        state.terminal.fontSize = 24;
        needsMigration = true;
      }
      if (state.teledesk && state.teledesk.fontSize < 10) {
        state.teledesk.fontSize = 24;
        needsMigration = true;
      }

      // Migration: Update desktop fontSize to 20 for Tailwind alignment (0.7 × 20 = 14px = text-sm)
      if (
        state.desktop &&
        (state.desktop.fontSize === 16 || state.desktop.fontSize === 24)
      ) {
        state.desktop.fontSize = 20;
        needsMigration = true;
      }

      // Ensure terminal and teledesk have proper defaults if missing
      if (!state.terminal) {
        state.terminal = DEFAULT_STATE.terminal;
        needsMigration = true;
      }
      if (!state.teledesk) {
        state.teledesk = DEFAULT_STATE.teledesk;
        needsMigration = true;
      }

      // Normalize fonts to jetbrains/sans for all modes
      const normalized = normalizeState(state);
      needsMigration =
        needsMigration || normalized.changed || !migrationApplied;

      // Save the migrated state only if changes were made
      if (needsMigration) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized.state));
        localStorage.setItem(MIGRATION_APPLIED_KEY, "true");
        console.log("[ModeState] Migrations applied and saved");
      } else {
        localStorage.setItem(MIGRATION_APPLIED_KEY, "true");
      }

      cachedState = normalized.state;
      return normalized.state;
    }
  } catch (e) {
    console.error("Failed to load mode state:", e);
  }

  return DEFAULT_STATE;
}

/**
 * Save the complete mode state (localStorage + API sync)
 */
export function saveModeState(state: ModeState): void {
  if (typeof localStorage === "undefined") return;

  try {
    // Save to localStorage immediately (instant)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    cachedState = state; // Update cache

    // Sync to file system via API (async, non-blocking)
    syncModeStateToAPI(state).catch((err) => {
      console.warn("[ModeState] API sync failed (non-critical):", err);
    });
  } catch (e) {
    console.error("Failed to save mode state:", e);
  }
}

/**
 * Update a specific mode's state
 */
export function updateModeState<
  K extends keyof Omit<ModeState, "lastFile" | "lastMode">,
>(mode: K, updates: Partial<ModeState[K]>): void {
  const state = getModeState();
  state[mode] = { ...state[mode], ...updates };
  state.lastMode = mode;
  saveModeState(state);
}

/**
 * Get the last opened file path
 */
export function getLastFile(): string | null {
  if (typeof localStorage === "undefined") return null;

  try {
    return localStorage.getItem(LAST_FILE_KEY);
  } catch {
    return null;
  }
}

/**
 * Save the last opened file path
 */
export function setLastFile(path: string | null): void {
  if (typeof localStorage === "undefined") return;

  try {
    if (path) {
      localStorage.setItem(LAST_FILE_KEY, path);
    } else {
      localStorage.removeItem(LAST_FILE_KEY);
    }

    // Also update in mode state
    const state = getModeState();
    state.lastFile = path;
    saveModeState(state);
  } catch (e) {
    console.error("Failed to save last file:", e);
  }
}

/**
 * Get state for a specific mode
 */
export function getStateForMode<
  K extends keyof Omit<ModeState, "lastFile" | "lastMode">,
>(mode: K): ModeState[K] {
  const state = getModeState();
  return state[mode];
}

/**
 * Navigate to a mode with optional file
 */
export function navigateToMode(mode: string, filePath?: string): void {
  if (filePath) {
    setLastFile(filePath);
  }

  const state = getModeState();
  state.lastMode = mode;
  saveModeState(state);

  // Navigate
  const url = filePath
    ? `/${mode}?file=${encodeURIComponent(filePath)}`
    : `/${mode}`;
  window.location.href = url;
}

/**
 * Reset the current mode to default display settings
 */
export function resetModeDisplay<
  K extends keyof Omit<ModeState, "lastFile" | "lastMode">,
>(mode: K): void {
  const state = getModeState();
  state[mode] = { ...DEFAULT_STATE[mode] };
  const normalized = normalizeState(state);
  saveModeState(normalized.state);
}

/**
 * Toggle sidebar for a specific mode
 */
export function toggleSidebar<
  K extends keyof Omit<ModeState, "lastFile" | "lastMode">,
>(mode: K): void {
  const state = getModeState();
  const modeState = state[mode];
  if ("sidebarOpen" in modeState) {
    (modeState as { sidebarOpen: boolean }).sidebarOpen =
      !modeState.sidebarOpen;
    saveModeState(state);
  }
}

/**
 * Toggle dark mode for a specific mode
 */
export function toggleDarkMode<
  K extends keyof Omit<ModeState, "lastFile" | "lastMode">,
>(mode: K): void {
  const state = getModeState();
  const modeState = state[mode];
  if ("darkMode" in modeState) {
    (modeState as { darkMode: boolean }).darkMode = !modeState.darkMode;
    saveModeState(state);
  }
}

/**
 * Update font settings for a specific mode
 */
export function updateFontSettings<
  K extends keyof Omit<ModeState, "lastFile" | "lastMode">,
>(
  mode: K,
  settings: Partial<{
    headingFont: ModeState[K] extends { headingFont: infer T } ? T : never;
    bodyFont: ModeState[K] extends { bodyFont: infer T } ? T : never;
    monoVariant: ModeState[K] extends { monoVariant: infer T } ? T : never;
    fontSize: ModeState[K] extends { fontSize: infer T } ? T : never;
  }>
): void {
  const state = getModeState();
  state[mode] = { ...state[mode], ...settings } as ModeState[K];
  saveModeState(state);
}
