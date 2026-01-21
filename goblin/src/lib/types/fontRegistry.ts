/**
 * uDOS Font Registry Types
 *
 * TypeScript interfaces matching the fonts.schema.json
 * for type-safe font handling with the font metadata system.
 */

// ============================================
// FONT REGISTRY TYPE DEFINITIONS
// ============================================

export type FontRegistryRole = "H" | "B" | "M"; // Header, Body, Monospace

export type FontRegistryType =
  | "sans-serif"
  | "serif"
  | "monospace"
  | "pixel"
  | "bitmap"
  | "teletext"
  | "emoji"
  | "block-graphics"
  | "map-tiles";

export type FontColorSupport = "mono" | "full" | "32col";

export type FontRegistryStatus = "STABLE" | "IN_DEVELOPMENT" | "DEPRECATED";

// ============================================
// FONT FILE VARIANTS
// ============================================

export interface FontRegistryFiles {
  regular: string;
  medium?: string;
  semibold?: string;
  bold?: string;
  italic?: string;
  flf?: string;
  [key: string]: string | undefined;
}

// ============================================
// FONT SIZING
// ============================================

export interface FontRegistrySizing {
  /** Base font size (e.g., "16px", "14px") */
  base: string;

  /** Scaling ratio to fill 24x24 grid */
  ratio_24x24?: string;

  /** Line height multiplier */
  line_height?: string;

  /** Letter spacing value */
  letter_spacing?: string;
}

// ============================================
// MATHEMATICAL BASIS (for procedural fonts)
// ============================================

export interface FontMathematicalBasis {
  /** Number of base pixels in design grid */
  basePixels?: number;

  /** Maximum theoretical pattern combinations */
  theoreticalCombinations?: string;

  /** Number of useful practical patterns */
  practicalPatterns?: string;

  /** Integer scaling factor */
  scalingFactor?: number;

  /** Division explanation */
  perfectDivisibility?: string;

  /** Historical context for resolution choice */
  classicResolution?: string;
}

// ============================================
// REGISTERED FONT ENTRY
// ============================================

export interface RegisteredFont {
  /** Human-readable font name */
  name: string;

  /** Font roles: H=Header, B=Body, M=Monospace (comma-separated) */
  role: string;

  /** Font category type */
  type: FontRegistryType;

  /** Relative path from static root to font files */
  path: string;

  /** Font file variants */
  files: FontRegistryFiles;

  /** Font sizing configuration */
  sizing: FontRegistrySizing;

  /** Color capability */
  colorSupport?: FontColorSupport;

  /** Pixel grid dimensions for bitmap/pixel fonts */
  pixelGrid?: string;

  /** Whether font supports teletext-style block graphics */
  blockGraphics?: boolean;

  /** Unicode range coverage */
  unicodeRange?: string;

  /** ASCII code range for custom characters */
  asciiRange?: string;

  /** Reference to a named palette for colored fonts */
  paletteRef?: string;

  /** Original design resolution before scaling */
  designResolution?: string;

  /** Scaling factor description */
  scaling?: string;

  /** Mathematical properties for procedurally generated fonts */
  mathematicalBasis?: FontMathematicalBasis;

  /** Pattern categories for block graphics fonts */
  patternCategories?: string[];

  /** List of font features and capabilities */
  features?: string[];

  /** Font license type */
  license: string;

  /** Font creator or source attribution */
  credits?: string;

  /** URL for font source or documentation */
  url?: string;

  /** Development status for custom fonts */
  status?: FontRegistryStatus;
}

// ============================================
// FONT REGISTRY
// ============================================

export interface FontRegistry {
  /** Array of bundled system fonts */
  fonts: RegisteredFont[];

  /** Array of custom/user-defined fonts */
  customFonts?: RegisteredFont[];
}

// ============================================
// FONT QUERY
// ============================================

export interface FontRegistryQuery {
  role?: FontRegistryRole;
  type?: FontRegistryType;
  colorSupport?: FontColorSupport;
  pixelFont?: boolean;
}

// ============================================
// RESOLVED FONT FOR RENDERING
// ============================================

export interface ResolvedRegistryFont {
  font: RegisteredFont;
  variant: keyof FontRegistryFiles;
  fullPath: string;
  cssFamily: string;
  cssSize: string;
}
