/**
 * NetHack Sprite Generator Types
 *
 * Types and utilities for creating NetHack-style sprites
 * using the uDOS 24x24 tile format and 32-color palette
 */

/**
 * Sprite categories following NetHack conventions
 */
export type SpriteCategory = "monsters" | "objects" | "dungeon" | "effects";

/**
 * Monster subcategories for color guidance
 */
export type MonsterType =
  | "humanoid" // goblins, orcs, humans
  | "animal" // dogs, cats, horses
  | "undead" // zombies, wraiths, vampires
  | "elemental" // fire, ice, earth elementals
  | "dragon" // all dragons
  | "demon" // demons, devils
  | "magical"; // unicorns, nymphs, etc.

/**
 * Object subcategories
 */
export type ObjectType =
  | "weapon" // swords, axes, bows
  | "armor" // helmets, shields, mail
  | "potion" // bottles with liquids
  | "scroll" // rolled parchment
  | "ring" // finger rings
  | "wand" // magical sticks
  | "food" // rations, fruit
  | "tool" // picks, keys, lamps
  | "gem" // gems and stones
  | "gold"; // currency

/**
 * Dungeon tile types
 */
export type DungeonType =
  | "floor" // walkable surfaces
  | "wall" // barriers
  | "door" // doors (open/closed)
  | "stairs" // up/down transitions
  | "trap" // hidden dangers
  | "altar" // religious sites
  | "fountain" // water sources
  | "special"; // thrones, graves, etc.

/**
 * Sprite metadata
 */
export interface SpriteMetadata {
  id: string; // Unique identifier (e.g., "goblin", "potion_clear")
  name: string; // Display name
  category: SpriteCategory;
  subtype?: MonsterType | ObjectType | DungeonType;
  nethackName?: string; // Original NetHack name for attribution
  description?: string;
  palette: number[]; // Suggested palette indices for this sprite
  created: string;
  modified: string;
}

/**
 * Complete sprite definition
 */
export interface NetHackSprite {
  metadata: SpriteMetadata;
  pixels: (number | null)[][]; // 24x24 grid with palette indices (null = transparent)
}

/**
 * Palette presets for different entity types
 */
export const MONSTER_PALETTES: Record<MonsterType, number[]> = {
  humanoid: [16, 17, 18, 19, 20, 24, 25, 26, 27, 4, 5], // greys, skin tones, earth
  animal: [0, 1, 4, 5, 6, 16, 17, 18, 19, 20, 21], // greens, browns, greys
  undead: [12, 13, 16, 17, 18, 19, 20, 29], // cyan, purple, greys, ice
  elemental: [8, 9, 10, 12, 28, 29, 30], // reds, cyan, specials
  dragon: [0, 1, 8, 9, 10, 12, 13, 28, 30], // varied by dragon color
  demon: [8, 13, 14, 15, 16, 28], // reds, purples, magentas
  magical: [10, 11, 12, 13, 23, 29, 30], // bright, magical colors
};

export const OBJECT_PALETTES: Record<ObjectType, number[]> = {
  weapon: [6, 16, 17, 18, 19, 20, 21, 4], // metals, greys
  armor: [6, 16, 17, 18, 19, 20, 21, 4, 5], // metals, leather
  potion: [2, 3, 8, 10, 12, 13, 14, 23], // blues, colors, glass
  scroll: [5, 20, 21, 22, 23, 4], // parchment tones
  ring: [10, 17, 18, 19, 20], // metallic with gem
  wand: [4, 5, 12, 13, 17, 18, 19], // wood, magical
  food: [4, 5, 9, 10, 0, 1], // browns, organics
  tool: [4, 6, 17, 18, 19, 20], // wood, metal
  gem: [8, 10, 11, 12, 13, 14, 23, 30], // bright colors
  gold: [10, 9, 5], // yellows, tans
};

export const DUNGEON_PALETTES: Record<DungeonType, number[]> = {
  floor: [4, 5, 6, 17, 18, 19, 20], // stone, earth
  wall: [6, 16, 17, 18, 19, 20], // grey stone
  door: [4, 5, 6, 17, 18, 19], // wood, iron
  stairs: [6, 16, 17, 18, 19, 20], // stone
  trap: [8, 9, 16, 17, 18, 4], // danger colors
  altar: [6, 17, 18, 19, 20, 23], // stone, white
  fountain: [2, 3, 6, 17, 18, 19, 23], // water, stone
  special: [10, 13, 17, 18, 19, 20, 23], // varied
};

/**
 * Create empty 24x24 sprite grid
 */
export function createEmptySprite(): (number | null)[][] {
  return Array(24)
    .fill(null)
    .map(() => Array(24).fill(null));
}

/**
 * Create sprite metadata with defaults
 */
export function createSpriteMetadata(
  id: string,
  category: SpriteCategory,
  options: Partial<SpriteMetadata> = {}
): SpriteMetadata {
  const now = new Date().toISOString();
  return {
    id,
    name: options.name || id.replace(/_/g, " "),
    category,
    subtype: options.subtype,
    nethackName: options.nethackName,
    description: options.description,
    palette: options.palette || [],
    created: now,
    modified: now,
  };
}

/**
 * Create new NetHack sprite
 */
export function createNetHackSprite(
  id: string,
  category: SpriteCategory,
  options: Partial<SpriteMetadata> = {}
): NetHackSprite {
  return {
    metadata: createSpriteMetadata(id, category, options),
    pixels: createEmptySprite(),
  };
}

/**
 * Get suggested palette for sprite type
 */
export function getSuggestedPalette(
  category: SpriteCategory,
  subtype?: string
): number[] {
  switch (category) {
    case "monsters":
      return (
        MONSTER_PALETTES[subtype as MonsterType] || MONSTER_PALETTES.humanoid
      );
    case "objects":
      return OBJECT_PALETTES[subtype as ObjectType] || OBJECT_PALETTES.weapon;
    case "dungeon":
      return DUNGEON_PALETTES[subtype as DungeonType] || DUNGEON_PALETTES.floor;
    case "effects":
      return [8, 9, 10, 11, 12, 13, 14, 15, 30]; // Bright, magical colors
    default:
      return [16, 17, 18, 19, 20, 21, 22, 23]; // Greyscale fallback
  }
}

/**
 * Validate sprite meets NetHack brief requirements
 */
export function validateSprite(sprite: NetHackSprite): string[] {
  const errors: string[] = [];

  // Check dimensions
  if (sprite.pixels.length !== 24) {
    errors.push("Sprite must be 24 pixels tall");
  }
  if (sprite.pixels.some((row) => row.length !== 24)) {
    errors.push("Sprite must be 24 pixels wide");
  }

  // Check palette usage
  const usedColors = new Set<number>();
  sprite.pixels.forEach((row) => {
    row.forEach((pixel) => {
      if (pixel !== null) usedColors.add(pixel);
    });
  });

  // Check for invalid palette indices
  usedColors.forEach((color) => {
    if (color < 0 || color > 31) {
      errors.push(`Invalid palette index: ${color} (must be 0-31)`);
    }
  });

  // Check if sprite is empty
  if (usedColors.size === 0) {
    errors.push("Sprite is empty");
  }

  return errors;
}

/**
 * Convert sprite to PNG data URL
 */
export function spriteToPNG(sprite: NetHackSprite, palette: string[]): string {
  const canvas = document.createElement("canvas");
  canvas.width = 24;
  canvas.height = 24;
  const ctx = canvas.getContext("2d");

  if (!ctx) return "";

  // Clear to transparent
  ctx.clearRect(0, 0, 24, 24);

  // Draw pixels
  sprite.pixels.forEach((row, y) => {
    row.forEach((paletteIndex, x) => {
      if (paletteIndex !== null && palette[paletteIndex]) {
        ctx.fillStyle = palette[paletteIndex];
        ctx.fillRect(x, y, 1, 1);
      }
    });
  });

  return canvas.toDataURL("image/png");
}
