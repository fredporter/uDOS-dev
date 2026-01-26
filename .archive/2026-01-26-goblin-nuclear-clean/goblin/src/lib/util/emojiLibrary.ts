// @ts-nocheck
/**
 * Emoji and Icon Library System
 *
 * Lightweight emoji/icon database with GitHub shortcodes
 */

export interface EmojiData {
  shortcode: string; // e.g., ":heart:"
  unicode: string; // e.g., "❤️"
  category: string; // e.g., "smileys"
  keywords: string[]; // Search terms
  svg?: string; // Optional SVG representation
  colorPaletteIndices?: number[]; // uDOS palette indices for color version
}

export interface IconData {
  id: string; // Unique identifier
  name: string; // Human-readable name
  tags: string[]; // Search tags
  svg?: string; // SVG markup (optional for emoji)
  unicode?: string; // Unicode character for emoji
  shortcode?: string; // Emoji shortcode (e.g., ":heart:")
  category?: string; // Category for grouping
  source: "nounproject" | "custom" | "mono-font" | "emoji"; // Source type
  attribution?: string; // License/attribution
  mono?: boolean; // Monochrome icon
}

/**
 * Common emoji shortcodes (lightweight subset)
 * Based on GitHub emoji shortcodes
 */
export const COMMON_EMOJI: EmojiData[] = [
  // Smileys
  {
    shortcode: ":smile:",
    unicode: "😄",
    category: "smileys",
    keywords: ["happy", "joy"],
  },
  {
    shortcode: ":heart:",
    unicode: "❤️",
    category: "smileys",
    keywords: ["love", "like"],
  },
  {
    shortcode: ":thinking:",
    unicode: "🤔",
    category: "smileys",
    keywords: ["think", "hmm"],
  },
  {
    shortcode: ":tada:",
    unicode: "🎉",
    category: "smileys",
    keywords: ["party", "celebrate"],
  },
  {
    shortcode: ":fire:",
    unicode: "🔥",
    category: "smileys",
    keywords: ["hot", "burn"],
  },
  {
    shortcode: ":star:",
    unicode: "⭐",
    category: "smileys",
    keywords: ["favorite", "star"],
  },
  {
    shortcode: ":rocket:",
    unicode: "🚀",
    category: "travel",
    keywords: ["launch", "space"],
  },
  {
    shortcode: ":eyes:",
    unicode: "👀",
    category: "smileys",
    keywords: ["look", "watch"],
  },

  // Objects
  {
    shortcode: ":computer:",
    unicode: "💻",
    category: "objects",
    keywords: ["laptop", "code"],
  },
  {
    shortcode: ":file:",
    unicode: "📄",
    category: "objects",
    keywords: ["document", "page"],
  },
  {
    shortcode: ":folder:",
    unicode: "📁",
    category: "objects",
    keywords: ["directory", "files"],
  },
  {
    shortcode: ":save:",
    unicode: "💾",
    category: "objects",
    keywords: ["disk", "floppy"],
  },
  {
    shortcode: ":hammer:",
    unicode: "🔨",
    category: "objects",
    keywords: ["tool", "build"],
  },
  {
    shortcode: ":wrench:",
    unicode: "🔧",
    category: "objects",
    keywords: ["tool", "fix"],
  },
  {
    shortcode: ":mag:",
    unicode: "🔍",
    category: "objects",
    keywords: ["search", "find"],
  },
  {
    shortcode: ":lightbulb:",
    unicode: "💡",
    category: "objects",
    keywords: ["idea", "light"],
  },
  {
    shortcode: ":bell:",
    unicode: "🔔",
    category: "objects",
    keywords: ["notify", "alert"],
  },
  {
    shortcode: ":lock:",
    unicode: "🔒",
    category: "objects",
    keywords: ["secure", "private"],
  },
  {
    shortcode: ":key:",
    unicode: "🔑",
    category: "objects",
    keywords: ["password", "unlock"],
  },

  // Symbols
  {
    shortcode: ":check:",
    unicode: "✅",
    category: "symbols",
    keywords: ["done", "complete"],
  },
  {
    shortcode: ":x:",
    unicode: "❌",
    category: "symbols",
    keywords: ["no", "error"],
  },
  {
    shortcode: ":warning:",
    unicode: "⚠️",
    category: "symbols",
    keywords: ["caution", "alert"],
  },
  {
    shortcode: ":info:",
    unicode: "ℹ️",
    category: "symbols",
    keywords: ["information", "help"],
  },
  {
    shortcode: ":question:",
    unicode: "❓",
    category: "symbols",
    keywords: ["help", "unknown"],
  },
  {
    shortcode: ":plus:",
    unicode: "➕",
    category: "symbols",
    keywords: ["add", "new"],
  },
  {
    shortcode: ":minus:",
    unicode: "➖",
    category: "symbols",
    keywords: ["remove", "subtract"],
  },
  {
    shortcode: ":arrow_right:",
    unicode: "➡️",
    category: "symbols",
    keywords: ["next", "forward"],
  },
  {
    shortcode: ":arrow_left:",
    unicode: "⬅️",
    category: "symbols",
    keywords: ["back", "previous"],
  },
  {
    shortcode: ":arrow_up:",
    unicode: "⬆️",
    category: "symbols",
    keywords: ["up", "increase"],
  },
  {
    shortcode: ":arrow_down:",
    unicode: "⬇️",
    category: "symbols",
    keywords: ["down", "decrease"],
  },
];

/**
 * Search emoji by keyword or shortcode
 */
export function searchEmoji(query: string): EmojiData[] {
  const lowerQuery = query.toLowerCase();
  return COMMON_EMOJI.filter(
    (emoji) =>
      emoji.shortcode.includes(lowerQuery) ||
      emoji.keywords.some((kw) => kw.includes(lowerQuery)) ||
      emoji.category.includes(lowerQuery)
  );
}

/**
 * Get emoji by shortcode
 */
export function getEmoji(shortcode: string): EmojiData | undefined {
  return COMMON_EMOJI.find((e) => e.shortcode === shortcode);
}

/**
 * Parse shortcodes in text and replace with unicode
 */
export function parseShortcodes(text: string): string {
  let result = text;
  COMMON_EMOJI.forEach((emoji) => {
    result = result.replace(new RegExp(emoji.shortcode, "g"), emoji.unicode);
  });
  return result;
}

/**
 * Convert unicode emoji to shortcode
 */
export function unicodeToShortcode(unicode: string): string | undefined {
  const emoji = COMMON_EMOJI.find((e) => e.unicode === unicode);
  return emoji?.shortcode;
}

/**
 * Icon library storage
 */
class IconLibrary {
  private icons: Map<string, IconData> = new Map();

  addIcon(icon: IconData) {
    this.icons.set(icon.id, icon);
  }

  getIcon(id: string): IconData | undefined {
    return this.icons.get(id);
  }

  searchIcons(query: string): IconData[] {
    const lowerQuery = query.toLowerCase();
    return Array.from(this.icons.values()).filter(
      (icon) =>
        icon.name.toLowerCase().includes(lowerQuery) ||
        icon.tags.some((tag) => tag.toLowerCase().includes(lowerQuery))
    );
  }

  listIcons(): IconData[] {
    return Array.from(this.icons.values());
  }

  removeIcon(id: string) {
    this.icons.delete(id);
  }

  clear() {
    this.icons.clear();
  }

  toJSON(): Record<string, IconData> {
    return Object.fromEntries(this.icons);
  }

  fromJSON(data: Record<string, IconData>) {
    this.icons.clear();
    Object.values(data).forEach((icon) => this.addIcon(icon));
  }
}

export const iconLibrary = new IconLibrary();

/**
 * Convert IconData to CharacterData for Pixel Editor
 */
export async function iconDataToCharacterData(
  icon: IconData,
  gridSize: number = 24
): Promise<import("./fontLoader").CharacterData> {
  // Get pixel data from emoji unicode or SVG
  let pixels: boolean[][];

  if (icon.unicode) {
    // Emoji-based icon
    const { renderEmojiToPixelGrid } = await import("./emojiRenderer");
    const result = await renderEmojiToPixelGrid(icon.unicode, gridSize);
    pixels = result.pixels;
  } else if (icon.svg) {
    // SVG-based icon - use SVG processor to convert to pixel grid
    console.log(
      `[EmojiLibrary] Processing SVG for icon: ${icon.id} (${gridSize}x${gridSize})`
    );
    const { svgToPixelGrid } = await import("./svgParser");

    try {
      // Convert SVG to color-indexed pixel grid
      const colorGrid = await svgToPixelGrid(icon.svg, gridSize, gridSize);

      // Convert from color palette indices to boolean grid
      // Any non-null, non-transparent pixel becomes true
      pixels = colorGrid.map((row) =>
        row.map((paletteIndex) => paletteIndex !== null && paletteIndex !== 0)
      );

      console.log(`[EmojiLibrary] Successfully processed SVG icon: ${icon.id}`);
    } catch (error) {
      console.error(
        `[EmojiLibrary] Failed to process SVG for icon ${icon.id}:`,
        error
      );
      // Fallback to empty grid
      pixels = Array(gridSize)
        .fill(null)
        .map(() => Array(gridSize).fill(false));
    }
  } else {
    // Empty/unknown
    pixels = Array(gridSize)
      .fill(null)
      .map(() => Array(gridSize).fill(false));
  }

  const code =
    icon.unicode?.codePointAt(0) || 0xe000 + Math.floor(Math.random() * 1000); // Private use area

  return {
    code,
    char: icon.unicode || icon.id,
    pixels,
    width: gridSize,
    height: gridSize,
  };
}

/**
 * Load icon library into Pixel Editor format
 */
export async function loadIconLibraryToEditor(
  libraryPath: string,
  gridSize: number = 24
): Promise<import("./fontLoader").CharacterData[]> {
  await importIconLibrary(libraryPath);

  const icons = iconLibrary.listIcons();
  const characters: import("./fontLoader").CharacterData[] = [];

  console.log(
    `[EmojiLibrary] Converting ${icons.length} icons to character data`
  );

  for (let i = 0; i < icons.length; i++) {
    const icon = icons[i];
    try {
      const charData = await iconDataToCharacterData(icon, gridSize);
      characters.push(charData);
      console.log(
        `[EmojiLibrary] Converted icon ${icon.id}: ${icon.unicode || icon.name}`
      );
    } catch (error) {
      console.error(`[EmojiLibrary] Failed to convert icon ${icon.id}:`, error);
      // Add empty character to maintain array indexes
      characters.push({
        code: 0xe000 + i,
        char: `?${i}`,
        pixels: Array(gridSize)
          .fill(null)
          .map(() => Array(gridSize).fill(false)),
        width: gridSize,
        height: gridSize,
      });
    }
  }

  console.log(
    `[EmojiLibrary] Successfully converted ${characters.length} icons`
  );
  return characters;
}

/**
 * Load custom icon from file
 */
export async function loadCustomIcon(
  filePath: string,
  name: string,
  tags: string[] = []
): Promise<IconData> {
  try {
    const { readTextFile } = await import("@tauri-apps/plugin-fs");
    const svg = await readTextFile(filePath);

    const id = `custom-${Date.now()}`;
    const icon: IconData = {
      id,
      name,
      tags,
      svg,
      source: "custom",
      mono: !svg.includes("fill=") || svg.includes('fill="none"'),
    };

    iconLibrary.addIcon(icon);
    return icon;
  } catch (error) {
    throw new Error(`Failed to load icon: ${error}`);
  }
}

/**
 * Export icon library to JSON
 */
export async function exportIconLibrary(filePath: string): Promise<void> {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    const data = iconLibrary.toJSON();
    await invoke("write_file", {
      path: filePath,
      contents: JSON.stringify(data, null, 2),
    });
  } catch (error) {
    throw new Error(`Failed to export icon library: ${error}`);
  }
}

/**
 * Import icon library from JSON
 */
export async function importIconLibrary(filePath: string): Promise<void> {
  try {
    console.log(`[EmojiLibrary] Fetching icon library from: ${filePath}`);

    // Try browser fetch first, fallback to Tauri if needed
    let json: string;
    try {
      const response = await fetch(filePath);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      json = await response.text();
      console.log(`[EmojiLibrary] Loaded via fetch: ${json.length} characters`);
    } catch (fetchError) {
      console.log(
        `[EmojiLibrary] Fetch failed, trying Tauri filesystem:`,
        fetchError
      );
      // Fallback to Tauri filesystem API if fetch fails
      const { readTextFile } = await import("@tauri-apps/plugin-fs");
      json = await readTextFile(filePath);
      console.log(`[EmojiLibrary] Loaded via Tauri: ${json.length} characters`);
    }

    const parsed = JSON.parse(json);
    console.log(`[EmojiLibrary] Parsed JSON:`, Object.keys(parsed));

    // Handle both formats: {icons: [...]} or {id: {...}, id2: {...}}
    let data: Record<string, IconData>;
    if (Array.isArray(parsed.icons)) {
      // Convert array to object keyed by id
      data = Object.fromEntries(
        parsed.icons.map((icon: IconData) => [icon.id, icon])
      );
      console.log(
        `[EmojiLibrary] Converted ${parsed.icons.length} icons from array format`
      );
    } else {
      data = parsed;
      console.log(
        `[EmojiLibrary] Using ${Object.keys(data).length} icons from object format`
      );
    }

    iconLibrary.fromJSON(data);
    console.log(
      `[EmojiLibrary] Successfully imported ${Object.keys(data).length} icons`
    );
  } catch (error) {
    console.error(`[EmojiLibrary] Import failed:`, error);
    throw new Error(`Failed to import icon library from ${filePath}: ${error}`);
  }
}

/**
 * Convert SVG file directly to CharacterData for Pixel Editor
 * @param svgContent - SVG markup string
 * @param gridSize - Target pixel grid size (24 or 48)
 * @param name - Optional name for the icon
 * @returns CharacterData ready for pixel editor
 */
export async function svgToCharacterData(
  svgContent: string,
  gridSize: number = 24,
  name: string = "svg-icon"
): Promise<import("./fontLoader").CharacterData> {
  const icon: IconData = {
    id: name,
    name,
    tags: ["svg", "custom"],
    svg: svgContent,
    source: "custom",
    mono: true,
  };

  return await iconDataToCharacterData(icon, gridSize);
}
