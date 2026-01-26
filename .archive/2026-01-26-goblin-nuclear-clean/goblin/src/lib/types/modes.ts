/**
 * Mode State Type Definitions
 *
 * Hierarchical type structure for mode-specific settings.
 * Uses inheritance to reduce repetition and improve maintainability.
 */

import type { FontFamily, MonoVariant } from "./fonts";

/**
 * Base settings shared across all modes
 */
export interface BaseModeSettings {
  sidebarOpen: boolean;
  darkMode: boolean;
  fontSize: number;
  headingFont: FontFamily;
  bodyFont: FontFamily;
  monoVariant: MonoVariant;
}

/**
 * Desktop mode settings
 */
export interface DesktopModeSettings extends BaseModeSettings {
  pattern: string;
}

/**
 * Settings for document-based modes (editor, reader, slides)
 */
export interface DocumentModeSettings extends BaseModeSettings {
  proseSizeIndex: number;
  viewType: "document" | "slideshow";
  viewMode: boolean;
}

/**
 * Markdown editor specific settings
 */
export interface MarkdownModeSettings extends DocumentModeSettings {
  color: number;
}

/**
 * Reader mode specific settings
 */
export interface ReadModeSettings extends DocumentModeSettings {
  theme: string;
}

/**
 * Table mode settings
 */
export interface TableModeSettings extends BaseModeSettings {
  sortColumn: string | null;
  sortDirection: "asc" | "desc";
}

/**
 * Mode names as union type
 */
export type ModeName =
  | "desktop"
  | "markdown"
  | "read"
  | "table"
  | "dashboard"
  | "terminal"
  | "teledesk"
  | "blocks"
  | "pixel-editor"
  | "layer-editor"
  | "svg-processor";

/**
 * Complete mode state structure
 */
export interface ModeState {
  lastFile: string | null;
  lastMode: string;
  desktop: DesktopModeSettings;
  markdown: MarkdownModeSettings;
  read: ReadModeSettings;
  table: TableModeSettings;
  dashboard: BaseModeSettings;
  terminal: BaseModeSettings;
  teledesk: BaseModeSettings;
  blocks: BaseModeSettings;
  "pixel-editor": BaseModeSettings;
  "svg-processor": BaseModeSettings;
  "layer-editor": BaseModeSettings;
  knowledge: BaseModeSettings;
  present: BaseModeSettings;
  grid: BaseModeSettings;
  sprites: BaseModeSettings;
}
