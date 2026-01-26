/**
 * uDOS Library - Centralized Exports
 *
 * This file provides a single import point for commonly used utilities,
 * types, and services across the application.
 *
 * @module $lib
 * @example
 * ```typescript
 * // Instead of:
 * import { eventBus } from '$lib/services/eventBus';
 * import type { FontFamily } from '$lib/types/fonts';
 *
 * // Use:
 * import { eventBus } from '$lib';
 * import type { FontFamily } from '$lib';
 * ```
 */

// uDOS Tauri App v1.0.0.43+

// ═══════════════════════════════════════════════════════════════
// Services
// ═══════════════════════════════════════════════════════════════
export { moveLogger } from "./services/moveLogger";
// Central exports for $lib alias

// ============================================================================
// Stores & State Management
// ============================================================================

/** All Svelte stores (reactive state containers) */
export * from "./stores";

/** API request utilities for backend communication */
export { apiRequest, isApiAvailable } from "./stores/api";

/**
 * Mode-specific state management
 *
 * Functions for persisting and retrieving settings per mode:
 * - getStateForMode: Load saved settings for a mode
 * - updateModeState: Save settings for current mode
 * - toggleSidebar: Toggle sidebar and persist state
 * - toggleDarkMode: Toggle dark mode and persist state
 * - updateFontSettings: Update fonts and persist
 */
export {
  getStateForMode,
  updateModeState,
  getModeState,
  saveModeState,
  toggleSidebar,
  toggleDarkMode,
  updateFontSettings,
} from "./stores/modeState";

// ============================================================================
// Type Definitions
// ============================================================================

/** Font-related types (families, variants, metadata) */
export type {
  FontFamily,
  MonoVariant,
  FontMetadata,
  FontCollectionID,
} from "./types/fonts";

/** Mode settings type hierarchy (base + mode-specific) */
export type {
  ModeState,
  BaseModeSettings,
  DesktopModeSettings,
  DocumentModeSettings,
  MarkdownModeSettings,
  ReadModeSettings,
  TableModeSettings,
  ModeName,
} from "./types/modes";

/** Event type definitions for type-safe event bus */
export type { AppEventName, AppEventPayload } from "./types/events";

// ============================================================================
// Services
// ============================================================================

/**
 * Type-safe event bus for cross-component communication
 *
 * @example
 * ```typescript
 * import { eventBus } from '$lib';
 *
 * // Emit
 * eventBus.emit('file-opened', { path: '/foo.md', content: '...' });
 *
 * // Subscribe
 * const unsubscribe = eventBus.on('file-opened', (data) => {
 *   console.log(data.path);
 * });
 * ```
 */
export { eventBus } from "./services/eventBus";

// ============================================================================
// Shared UI Components
// ============================================================================

/** Standardized button component and page layout template */
export { default as UButton } from "./components/base/UButton.svelte";
export { default as PageLayout } from "./components/base/PageLayout.svelte";

// ============================================================================
// Font Configuration
// ============================================================================

/**
 * Font configuration and metadata
 *
 * Single source of truth for:
 * - CSS font-family declarations
 * - Font metadata from udos.md
 * - Utility functions for font queries
 */
export {
  FONT_CSS,
  MONO_VARIANT_CSS,
  FONT_METADATA,
  getFontCSS,
  getMonoVariantCSS,
  getFontMetadata,
  getFontsByRole,
} from "./util/fontConfig";

// ============================================================================
// Grid System
// ============================================================================

/**
 * Grid system utilities for 24×24 pixel grid modes
 *
 * Default: 24 cols × 24 rows, 24px per cell = 576×576px
 */
export { DEFAULT_GRID_SETTINGS } from "./util/gridSystem";

// ============================================================================
// Color Palette
// ============================================================================

/**
 * uDOS Standard 32-Color Palette
 *
 * Organized in 4 groups:
 * - Terrain (0-7): Natural map colors
 * - Markers (8-15): Bright UI colors
 * - Greyscale (16-23): Monochrome scale
 * - Accents (24-31): Skin tones + effects
 *
 * @example
 * ```typescript
 * import { getColorById, getColorHex } from '$lib';
 *
 * const grassGreen = getColorById(1);
 * const dangerRed = getColorHex(8); // "#DC2626"
 * ```
 */
export {
  UDOS_PALETTE,
  getAllColors,
  getColorById,
  getColorByName,
  getColorByIndex,
  getColorHex,
  getColorRGB,
  getColorGroup,
  isValidColorId,
  exportPaletteAsJSON,
  type ColorDefinition,
  type UDOSPalette,
} from "./util/udosPalette";
