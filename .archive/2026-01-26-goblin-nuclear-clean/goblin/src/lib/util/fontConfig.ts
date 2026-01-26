/**
 * Font Configuration - Single source of truth for all font metadata
 *
 * This file consolidates font information from static/fonts/udos.md
 * and provides type-safe access to font definitions and CSS mappings.
 *
 * User customizations can optionally be stored in memory/udos.md,
 * but this file provides all defaults needed for the app to function.
 *
 * All font-related code should import from here instead of hardcoding.
 */

import type { FontFamily, MonoVariant } from "../types/fonts";

/**
 * Font metadata structure matching udos.md JSON
 */
export interface FontMetadata {
  name: string;
  role: string; // "H" = heading, "B" = body, "M" = mono
  type: string;
  path: string;
  files: Record<string, string>;
  sizing: {
    base: string;
    ratio_24x24: string;
    line_height: string;
    letter_spacing?: string;
  };
  colorSupport: string;
  pixelGrid?: string;
  blockGraphics?: boolean;
  license: string;
  credits: string;
  url: string;
}

/**
 * Font metadata registry from static/fonts/udos.md
 * This is the single source of truth for font information
 */
export const FONT_METADATA: Record<string, FontMetadata> = {
  inter: {
    name: "Inter",
    role: "H,B",
    type: "sans-serif",
    path: "/fonts/tailwind/sans/",
    files: {
      regular: "Inter-Regular.woff2",
      medium: "Inter-Medium.woff2",
      semibold: "Inter-SemiBold.woff2",
      bold: "Inter-Bold.woff2",
    },
    sizing: {
      base: "16px",
      ratio_24x24: "1.5",
      line_height: "1.5",
    },
    colorSupport: "mono",
    license: "SIL Open Font License 1.1",
    credits: "Rasmus Andersson",
    url: "https://rsms.me/inter/",
  },
  merriweather: {
    name: "Merriweather",
    role: "H,B",
    type: "serif",
    path: "/fonts/tailwind/serif/",
    files: {
      regular: "Merriweather-Regular.woff2",
      bold: "Merriweather-Bold.woff2",
      italic: "Merriweather-Italic.woff2",
    },
    sizing: {
      base: "16px",
      ratio_24x24: "1.5",
      line_height: "1.6",
    },
    colorSupport: "mono",
    license: "SIL Open Font License 1.1",
    credits: "Sorkin Type",
    url: "https://fonts.google.com/specimen/Merriweather",
  },
  jetbrains: {
    name: "JetBrains Mono",
    role: "M",
    type: "monospace",
    path: "/fonts/tailwind/mono/",
    files: {
      regular: "JetBrainsMono-Regular.woff2",
      medium: "JetBrainsMono-Medium.woff2",
      bold: "JetBrainsMono-Bold.woff2",
    },
    sizing: {
      base: "14px",
      ratio_24x24: "1.714",
      line_height: "1.5",
      letter_spacing: "0",
    },
    colorSupport: "mono",
    license: "SIL Open Font License 1.1",
    credits: "JetBrains",
    url: "https://www.jetbrains.com/lp/mono/",
  },
  pressstart: {
    name: "Press Start 2P",
    role: "M",
    type: "pixel",
    path: "/fonts/retro/",
    files: {
      regular: "PressStart2P-Regular.ttf",
    },
    sizing: {
      base: "8px",
      ratio_24x24: "3.0",
      line_height: "1.8",
    },
    colorSupport: "mono",
    pixelGrid: "8x8",
    license: "SIL Open Font License 1.1",
    credits: "Codeman38",
    url: "https://fonts.google.com/specimen/Press+Start+2P",
  },
  c64: {
    name: "PetMe64",
    role: "M",
    type: "pixel",
    path: "/fonts/retro/c64/",
    files: {
      regular: "PetMe64.ttf",
    },
    sizing: {
      base: "8px",
      ratio_24x24: "3.0",
      line_height: "1.5",
    },
    colorSupport: "mono",
    pixelGrid: "8x8",
    license: "Kreative Software Free Use License v1.2f",
    credits: "Kreative Software",
    url: "https://www.kreativekorp.com/software/fonts/c64.shtml",
  },
  teletext: {
    name: "Teletext50",
    role: "M",
    type: "teletext",
    path: "/fonts/retro/teletext/",
    files: {
      regular: "Teletext50.otf",
    },
    sizing: {
      base: "18px",
      ratio_24x24: "1.333",
      line_height: "1.2",
    },
    colorSupport: "mono",
    pixelGrid: "5x9",
    blockGraphics: true,
    license: "Free for personal use",
    credits: "Galax (Teletext community)",
    url: "https://github.com/galax-io/Teletext50",
  },
  chicago: {
    name: "Chicago",
    role: "H,B,M",
    type: "bitmap",
    path: "/fonts/retro/apple/",
    files: {
      regular: "Chicago.ttf",
      flf: "ChicagoFLF.ttf",
    },
    sizing: {
      base: "12px",
      ratio_24x24: "2.0",
      line_height: "1.4",
    },
    colorSupport: "mono",
    pixelGrid: "variable",
    license: "Freeware (recreation)",
    credits: "Original: Susan Kare (Apple, 1984)",
    url: "https://en.wikipedia.org/wiki/Chicago_(typeface)",
  },
  monaco: {
    name: "Monaco",
    role: "M",
    type: "bitmap",
    path: "/fonts/retro/apple/",
    files: {
      regular: "monaco.ttf",
    },
    sizing: {
      base: "10px",
      ratio_24x24: "2.4",
      line_height: "1.4",
    },
    colorSupport: "mono",
    pixelGrid: "variable",
    license: "Freeware (recreation)",
    credits: "Original: Susan Kare & Kris Holmes (Apple)",
    url: "https://en.wikipedia.org/wiki/Monaco_(typeface)",
  },
  sfmono: {
    name: "SF Mono",
    role: "M",
    type: "monospace",
    path: "/fonts/retro/apple/",
    files: {
      regular: "SFMono-Regular.otf",
    },
    sizing: {
      base: "14px",
      ratio_24x24: "1.714",
      line_height: "1.5",
    },
    colorSupport: "mono",
    license: "Apple Inc.",
    credits: "Apple Inc.",
    url: "https://developer.apple.com/fonts/",
  },
  unifraktur: {
    name: "UnifrakturCook",
    role: "H",
    type: "blackletter",
    path: "/fonts/UnifrakturCook/",
    files: {
      regular: "UnifrakturCook-Bold.ttf",
    },
    sizing: {
      base: "16px",
      ratio_24x24: "1.6",
      line_height: "1.5",
    },
    colorSupport: "mono",
    license: "SIL Open Font License 1.1",
    credits: "j. 'mach' wust",
    url: "https://fonts.google.com/specimen/UnifrakturCook",
  },
  vag: {
    name: "VAG Primer",
    role: "H,B",
    type: "sans-serif",
    path: "/fonts/",
    files: {
      regular: "vag_primer_by_liam_butler_deqszdu.ttf",
    },
    sizing: {
      base: "16px",
      ratio_24x24: "1.5",
      line_height: "1.5",
    },
    colorSupport: "mono",
    license: "Freeware (artist release)",
    credits: "Liam Butler",
    url: "https://www.dafont.com/vag-primer.font",
  },
  librebaskerville: {
    name: "Libre Baskerville",
    role: "H,B",
    type: "serif",
    path: "/fonts/Libre_Baskerville/",
    files: {
      variable: "LibreBaskerville-VariableFont_wght.ttf",
      italicVariable: "LibreBaskerville-Italic-VariableFont_wght.ttf",
      regular: "static/LibreBaskerville-Regular.ttf",
      bold: "static/LibreBaskerville-Bold.ttf",
      italic: "static/LibreBaskerville-Italic.ttf",
    },
    sizing: {
      base: "16px",
      ratio_24x24: "1.6",
      line_height: "1.6",
    },
    colorSupport: "mono",
    license: "SIL Open Font License 1.1",
    credits: "Pablo Impallari, Rodrigo Fuenzalida",
    url: "https://fonts.google.com/specimen/Libre+Baskerville",
  },
  unifrakturmaguntia: {
    name: "UnifrakturMaguntia",
    role: "H",
    type: "blackletter",
    path: "/fonts/UnifrakturMaguntia/",
    files: {
      regular: "UnifrakturMaguntia-Regular.ttf",
    },
    sizing: {
      base: "16px",
      ratio_24x24: "1.7",
      line_height: "1.5",
    },
    colorSupport: "mono",
    license: "SIL Open Font License 1.1",
    credits: "Peter Wiegel",
    url: "https://www.fontsquirrel.com/fonts/unifrakturmaguntia",
  },
  greatvibes: {
    name: "Great Vibes",
    role: "H",
    type: "script",
    path: "/fonts/Great_Vibes/",
    files: {
      regular: "GreatVibes-Regular.ttf",
    },
    sizing: {
      base: "16px",
      ratio_24x24: "1.6",
      line_height: "1.5",
      letter_spacing: "0.01em",
    },
    colorSupport: "mono",
    license: "SIL Open Font License 1.1",
    credits: "TypeSETit (Brian J. Bonislawsky)",
    url: "https://fonts.google.com/specimen/Great+Vibes",
  },
};

/**
 * CSS font-family declarations - Single source of truth
 * Import from here instead of duplicating in styleManager.ts
 */
export const FONT_CSS: Record<FontFamily, string> = {
  sans: "'Inter', system-ui, sans-serif",
  serif: "'Merriweather', Georgia, serif",
  mono: "'JetBrains Mono', monospace",
  sfmono: "'SF Mono', Monaco, monospace",
  chicagoflf: "'ChicagoFLF', monospace",
  losaltos: "'Los Altos', cursive",
  monaco: "'Monaco', monospace",
  sanfrisco: "'Sanfrisco', fantasy",
  playfair: "'Playfair Display', Georgia, serif",
  unifraktur: "'UnifrakturCook', serif",
  unifrakturmaguntia: "'UnifrakturMaguntia', serif",
  vag: "'VAG Primer', 'VAG Rounded', 'Inter', sans-serif",
  librebaskerville: "'Libre Baskerville', 'Playfair Display', Georgia, serif",
  greatvibes: "'Great Vibes', cursive",
};

/**
 * Monospace variant CSS declarations
 */
export const MONO_VARIANT_CSS: Record<MonoVariant, string> = {
  jetbrains: "'JetBrains Mono', monospace",
  pressstart: "'PressStart2P', monospace",
  c64: "'PetMe64', monospace",
  teletext: "'Teletext50', monospace",
  monaco: "'Monaco', monospace",
};

/**
 * Get CSS font-family string for a font
 */
export function getFontCSS(font: FontFamily): string {
  return FONT_CSS[font];
}

/**
 * Get CSS font-family string for a mono variant
 */
export function getMonoVariantCSS(variant: MonoVariant): string {
  return MONO_VARIANT_CSS[variant];
}

/**
 * Get font metadata by key
 */
export function getFontMetadata(key: string): FontMetadata | undefined {
  return FONT_METADATA[key];
}

/**
 * Get all fonts that support a specific role
 */
export function getFontsByRole(role: "H" | "B" | "M"): FontMetadata[] {
  return Object.values(FONT_METADATA).filter((font) =>
    font.role.includes(role)
  );
}

/**
 * Export font metadata as JSON for static/fonts/udos.md
 */
export function exportFontMetadataJSON(): string {
  const fonts = Object.values(FONT_METADATA);
  return JSON.stringify({ fonts }, null, 2);
}
