/**
 * Font Collections - Unified font + character set pairings for pixel editor
 *
 * Structure:
 * - Core fonts use their native ASCII characters
 * - Teletext50 is the designated block/drawing font (has native support)
 * - Map symbols for terrain/survival applications
 */

import type { CharacterSet } from "./characterDatasets";
import {
  ASCII_PRINTABLE,
  TELETEXT_BLOCK_GRAPHICS,
  MAP_SYMBOLS,
} from "./characterDatasets";

export interface FontCollection {
  id: string;
  name: string;
  path: string;
  type: "mono" | "color";
  characterSet: CharacterSet;
  description: string;
}

// Emoji character sets
const EMOJI_COLOR_SET: CharacterSet = {
  name: "Color Emoji",
  description: "Full-color emoji from Google Noto",
  type: "emoji",
  codes: [
    0x1f604, // 😄 grinning face with smiling eyes
    0x2764, // ❤ red heart
    0x1f914, // 🤔 thinking face
    0x1f389, // 🎉 party popper
    0x1f525, // 🔥 fire
    0x2b50, // ⭐ star
    0x1f680, // 🚀 rocket
    0x1f440, // 👀 eyes
    0x1f4bb, // 💻 laptop
    0x1f4c4, // 📄 page facing up
    0x1f4c1, // 📁 file folder
    0x1f4c5, // 📅 calendar
    0x1f4c8, // 📈 chart increasing
    0x1f4dd, // 📝 memo
    0x1f50d, // 🔍 magnifying glass left
    0x1f517, // 🔗 link
    0x1f4a1, // 💡 light bulb
    0x26a0, // ⚠ warning
    0x2705, // ✅ check mark button
    0x274c, // ❌ cross mark
    0x2753, // ❓ question mark
    0x203c, // ‼ double exclamation
    0x27a1, // ➡ right arrow
    0x2b05, // ⬅ left arrow
    0x2b06, // ⬆ up arrow
    0x2b07, // ⬇ down arrow
    0x1f3e0, // 🏠 house
    0x1f333, // 🌳 deciduous tree
    0x26f0, // ⛰ mountain
    0x1f30a, // 🌊 water wave
  ],
  pairedSet: "emoji-mono",
};

const EMOJI_MONO_SET: CharacterSet = {
  name: "Mono Emoji",
  description: "Monochrome emoji line-art from Google Noto",
  type: "emoji",
  codes: [
    0x1f604, // 😄 grinning face with smiling eyes
    0x2764, // ❤ red heart
    0x1f914, // 🤔 thinking face
    0x1f389, // 🎉 party popper
    0x1f525, // 🔥 fire
    0x2b50, // ⭐ star
    0x1f680, // 🚀 rocket
    0x1f440, // 👀 eyes
    0x1f4bb, // 💻 laptop
    0x1f4c4, // 📄 page facing up
    0x1f4c1, // 📁 file folder
    0x1f4c5, // 📅 calendar
    0x1f4c8, // 📈 chart increasing
    0x1f4dd, // 📝 memo
    0x1f50d, // 🔍 magnifying glass left
    0x1f517, // 🔗 link
    0x1f4a1, // 💡 light bulb
    0x26a0, // ⚠ warning
    0x2705, // ✅ check mark button
    0x274c, // ❌ cross mark
    0x2753, // ❓ question mark
    0x203c, // ‼ double exclamation
    0x27a1, // ➡ right arrow
    0x2b05, // ⬅ left arrow
    0x2b06, // ⬆ up arrow
    0x2b07, // ⬇ down arrow
    0x1f3e0, // 🏠 house
    0x1f333, // 🌳 deciduous tree
    0x26f0, // ⛰ mountain
    0x1f30a, // 🌊 water wave
    0x2699, // ⚙ gear
    0x1f512, // 🔒 locked
    0x1f511, // 🔑 key
    0x1f514, // 🔔 bell
    0x1f550, // 🕐 one o'clock
    0x1f516, // 🔖 bookmark
  ],
  pairedSet: "emoji-color",
};

/**
 * Core font collections
 *
 * Design:
 * - Each font paired with its native character support
 * - One block/drawing collection (Teletext50) - has proper glyph support
 * - Two emoji sets: Color (NotoColorEmoji) and Mono (EmojiIconFont)
 * - Map symbols use Teletext50 as the rendering font
 */
export const FONT_COLLECTIONS: FontCollection[] = [
  // === RETRO PIXEL FONTS (Native ASCII) ===
  {
    id: "c64",
    name: "C64 (PetMe64)",
    path: "/fonts/retro/c64/PetMe64.ttf",
    type: "mono",
    characterSet: ASCII_PRINTABLE,
    description: "Classic Commodore 64 font",
  },
  {
    id: "pressstart",
    name: "Press Start 2P",
    path: "/fonts/retro/PressStart2P-Regular.ttf",
    type: "mono",
    characterSet: ASCII_PRINTABLE,
    description: "Arcade-style pixel font",
  },
  {
    id: "teletext50",
    name: "Teletext50",
    path: "/fonts/retro/teletext/Teletext50.otf",
    type: "mono",
    characterSet: ASCII_PRINTABLE,
    description: "British teletext broadcast font",
  },

  // === BLOCK & DRAWING CHARACTERS (Teletext50 only) ===
  {
    id: "blocks",
    name: "Block Graphics",
    path: "/fonts/retro/teletext/Teletext50.otf",
    type: "mono",
    characterSet: TELETEXT_BLOCK_GRAPHICS,
    description: "8×8 blocks, box drawing, shading patterns",
  },

  // === MAP SYMBOLS (Teletext50) ===
  {
    id: "map-symbols",
    name: "Map Symbols",
    path: "/fonts/retro/teletext/Teletext50.otf",
    type: "mono",
    characterSet: MAP_SYMBOLS,
    description: "Terrain markers, waypoints, survival icons",
  },

  // === MODERN MONO FONTS (Native ASCII) ===
  {
    id: "sfmono",
    name: "SF Mono",
    path: "/fonts/retro/apple/SFMono-Regular.otf",
    type: "mono",
    characterSet: ASCII_PRINTABLE,
    description: "Apple SF Mono - clean modern mono",
  },

  // === EMOJI FONTS ===
  {
    id: "emoji-color",
    name: "Color Emoji (Noto)",
    path: "/fonts/NotoColorEmoji.ttf",
    type: "color",
    characterSet: EMOJI_COLOR_SET,
    description: "Full-color emoji set from Google Noto",
  },
  {
    id: "emoji-mono",
    name: "Mono Emoji (Noto)",
    path: "/fonts/NotoEmoji-Regular.ttf",
    type: "mono",
    characterSet: EMOJI_MONO_SET,
    description: "Monochrome emoji line-art from Google Noto",
  },
];

/**
 * Get font collection by ID
 */
export function getFontCollection(id: string): FontCollection | undefined {
  return FONT_COLLECTIONS.find((fc) => fc.id === id);
}

/**
 * Get all font collections by type
 */
export function getFontCollectionsByType(
  type: "mono" | "color"
): FontCollection[] {
  return FONT_COLLECTIONS.filter((fc) => fc.type === type);
}

/**
 * Get default font collection
 */
export function getDefaultFontCollection(): FontCollection {
  return FONT_COLLECTIONS[2]; // Teletext50 ASCII
}
