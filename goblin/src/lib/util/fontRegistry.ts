/**
 * Font Registry Utilities
 *
 * Functions for loading, querying, and working with the font registry.
 */

import { invoke } from "@tauri-apps/api/core";
import type {
  FontRegistry,
  RegisteredFont,
  FontRegistryRole,
  FontRegistryQuery,
  FontRegistryFiles,
  ResolvedRegistryFont,
} from "../types/fontRegistry";

// ============================================
// FONT REGISTRY LOADING
// ============================================

let cachedRegistry: FontRegistry | null = null;

/**
 * Load font registry from JSON file
 */
export async function loadFontRegistry(
  forceReload = false
): Promise<FontRegistry> {
  if (cachedRegistry && !forceReload) {
    return cachedRegistry;
  }

  try {
    // Try loading from fonts.json first
    const jsonPath = "/fonts/fonts.json";
    const content = await invoke<string>("read_file", { path: jsonPath });
    cachedRegistry = JSON.parse(content) as FontRegistry;
    return cachedRegistry;
  } catch {
    // Fallback: return empty registry
    console.warn("Could not load font registry, using defaults");
    cachedRegistry = { fonts: [] };
    return cachedRegistry;
  }
}

/**
 * Clear cached registry
 */
export function clearFontRegistryCache(): void {
  cachedRegistry = null;
}

// ============================================
// QUERY HELPERS
// ============================================

/**
 * Parse font roles from string (e.g., "H,B,M" -> ['H', 'B', 'M'])
 */
export function parseRoles(roleString: string): FontRegistryRole[] {
  return roleString.split(",").map((r) => r.trim() as FontRegistryRole);
}

/**
 * Check if font has a specific role
 */
export function hasRole(font: RegisteredFont, role: FontRegistryRole): boolean {
  return parseRoles(font.role).includes(role);
}

/**
 * Filter fonts by query parameters
 */
export function filterFonts(
  fonts: RegisteredFont[],
  query: FontRegistryQuery
): RegisteredFont[] {
  return fonts.filter((font) => {
    if (query.role && !hasRole(font, query.role)) return false;
    if (query.type && font.type !== query.type) return false;
    if (query.colorSupport && font.colorSupport !== query.colorSupport)
      return false;
    if (query.pixelFont !== undefined) {
      const isPixel = [
        "pixel",
        "bitmap",
        "teletext",
        "block-graphics",
      ].includes(font.type);
      if (query.pixelFont !== isPixel) return false;
    }
    return true;
  });
}

// ============================================
// PATH & CSS HELPERS
// ============================================

/**
 * Get full path to a font file
 */
export function getFontPath(
  font: RegisteredFont,
  variant: keyof FontRegistryFiles = "regular"
): string {
  const filename = font.files[variant];
  if (!filename) return "";
  return `${font.path}${filename}`;
}

/**
 * Get CSS font-family declaration with fallbacks
 */
export function getCSSFamily(font: RegisteredFont): string {
  const fallbacks: Record<string, string> = {
    "sans-serif": "system-ui, sans-serif",
    serif: "Georgia, serif",
    monospace: "ui-monospace, monospace",
    pixel: "monospace",
    bitmap: "monospace",
    teletext: "monospace",
    emoji: "sans-serif",
    "block-graphics": "monospace",
    "map-tiles": "monospace",
  };

  return `"${font.name}", ${fallbacks[font.type] || "sans-serif"}`;
}

/**
 * Calculate pixel size for 24x24 grid alignment
 */
export function getGridSize(font: RegisteredFont): number {
  const base = parseInt(font.sizing.base);
  const ratio = parseFloat(font.sizing.ratio_24x24 || "1");
  return Math.round(base * ratio);
}

/**
 * Generate @font-face CSS for a font
 */
export function generateFontFace(
  font: RegisteredFont,
  variant: keyof FontRegistryFiles = "regular"
): string {
  const path = getFontPath(font, variant);
  if (!path) return "";

  const format = path.endsWith(".woff2")
    ? "woff2"
    : path.endsWith(".woff")
      ? "woff"
      : path.endsWith(".ttf")
        ? "truetype"
        : path.endsWith(".otf")
          ? "opentype"
          : "truetype";

  const weight =
    variant === "bold"
      ? "700"
      : variant === "semibold"
        ? "600"
        : variant === "medium"
          ? "500"
          : "400";

  const style = variant === "italic" ? "italic" : "normal";

  return `@font-face {
  font-family: "${font.name}";
  src: url("${path}") format("${format}");
  font-weight: ${weight};
  font-style: ${style};
  font-display: swap;
}`;
}

// ============================================
// FONT CATEGORY GETTERS
// ============================================

/**
 * Get all fonts from registry
 */
export function getAllFonts(registry: FontRegistry): RegisteredFont[] {
  return [...registry.fonts, ...(registry.customFonts || [])];
}

/**
 * Get fonts suitable for code/terminal (Monospace role)
 */
export function getMonospaceFonts(registry: FontRegistry): RegisteredFont[] {
  return filterFonts(getAllFonts(registry), { role: "M" });
}

/**
 * Get fonts suitable for headings
 */
export function getHeaderFonts(registry: FontRegistry): RegisteredFont[] {
  return filterFonts(getAllFonts(registry), { role: "H" });
}

/**
 * Get fonts suitable for body text
 */
export function getBodyFonts(registry: FontRegistry): RegisteredFont[] {
  return filterFonts(getAllFonts(registry), { role: "B" });
}

/**
 * Get pixel fonts for retro rendering
 */
export function getPixelFonts(registry: FontRegistry): RegisteredFont[] {
  return filterFonts(getAllFonts(registry), { pixelFont: true });
}

/**
 * Get fonts with emoji/color support
 */
export function getColorFonts(registry: FontRegistry): RegisteredFont[] {
  return getAllFonts(registry).filter(
    (f) => f.colorSupport && f.colorSupport !== "mono"
  );
}

/**
 * Get custom fonts (in development)
 */
export function getCustomFonts(registry: FontRegistry): RegisteredFont[] {
  return registry.customFonts || [];
}

// ============================================
// FONT RESOLUTION
// ============================================

/**
 * Resolve a font to full rendering details
 */
export function resolveFont(
  font: RegisteredFont,
  variant: keyof FontRegistryFiles = "regular"
): ResolvedRegistryFont {
  return {
    font,
    variant,
    fullPath: getFontPath(font, variant),
    cssFamily: getCSSFamily(font),
    cssSize: `${getGridSize(font)}px`,
  };
}

/**
 * Find font by name
 */
export function findFontByName(
  registry: FontRegistry,
  name: string
): RegisteredFont | undefined {
  return getAllFonts(registry).find(
    (f) => f.name.toLowerCase() === name.toLowerCase()
  );
}

/**
 * Find fonts by type
 */
export function findFontsByType(
  registry: FontRegistry,
  type: string
): RegisteredFont[] {
  return getAllFonts(registry).filter((f) => f.type === type);
}
