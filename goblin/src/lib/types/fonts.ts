/**
 * Shared Font Type Definitions
 *
 * Single source of truth for font-related types used across the application.
 * Import these types instead of redefining them in multiple files.
 */

/**
 * Available font families in uDOS
 * Includes system fonts, custom fonts, and retro fonts
 */
export type FontFamily =
  | "sans"
  | "serif"
  | "mono"
  | "sfmono"
  | "chicagoflf"
  | "losaltos"
  | "monaco"
  | "sanfrisco"
  | "playfair"
  | "unifraktur"
  | "unifrakturmaguntia"
  | "vag"
  | "librebaskerville"
  | "greatvibes";

/**
 * Monospace font variants
 * Used for code blocks, terminal displays, and technical content (M button in Pixel Editor)
 */
export type MonoVariant =
  | "jetbrains"
  | "pressstart"
  | "c64"
  | "teletext"
  | "monaco";

/**
 * Font collection categories
 */
export type FontCollectionID = "base" | "retro" | "system" | "custom";

/**
 * Font metadata structure
 */
export interface FontMetadata {
  id: string;
  name: string;
  category: FontCollectionID;
  cssName?: string;
  variants?: MonoVariant[];
  description?: string;
  source?: string;
  license?: string;
}
