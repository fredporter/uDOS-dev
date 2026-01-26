/**
 * Sprite Templates - Pre-configured sprite starting points
 *
 * Quick-start templates with appropriate palette subsets
 * for each sprite category based on NetHack conventions.
 */

import type {
  NetHackSprite,
  SpriteCategory,
  MonsterType,
  ObjectType,
  DungeonType,
} from "../types/nethackSprite";
import {
  MONSTER_PALETTES,
  OBJECT_PALETTES,
  DUNGEON_PALETTES,
  createNetHackSprite,
} from "../types/nethackSprite";

// uDOS 32-color palette (hex values)
const UCODE_PALETTE: string[] = [
  "#22c55e",
  "#16a34a",
  "#2563eb",
  "#1d4ed8", // 0-3: greens, blues
  "#d97706",
  "#92400e",
  "#a8a29e",
  "#7c3aed", // 4-7: browns, stone, purple
  "#dc2626",
  "#f97316",
  "#eab308",
  "#facc15", // 8-11: red, orange, yellows
  "#06b6d4",
  "#8b5cf6",
  "#ec4899",
  "#a855f7", // 12-15: cyan, purples, pink
  "#1f2937",
  "#374151",
  "#4b5563",
  "#6b7280", // 16-19: dark greys
  "#9ca3af",
  "#d1d5db",
  "#e5e7eb",
  "#f9fafb", // 20-23: light greys
  "#fde68a",
  "#fef3c7",
  "#c4b5a0",
  "#8b7355", // 24-27: skin tones, tans
  "#991b1b",
  "#1e40af",
  "#ffffff",
  "#000000", // 28-31: deep red/blue, white, black
];

// ============================================
// MONSTER TEMPLATES
// ============================================

export interface MonsterTemplate {
  name: string;
  type: MonsterType;
  basePalette: number[];
  suggestedOutline: number;
  description: string;
}

// Only include types that exist in MonsterType
export const MONSTER_TEMPLATES: Partial<Record<MonsterType, MonsterTemplate>> =
  {
    humanoid: {
      name: "Humanoid",
      type: "humanoid",
      basePalette: [...MONSTER_PALETTES.humanoid.slice(0, 8)],
      suggestedOutline: 16, // Black
      description: "Human-like creatures: adventurers, orcs, elves, dwarves",
    },
    undead: {
      name: "Undead",
      type: "undead",
      basePalette: [...MONSTER_PALETTES.undead.slice(0, 8)],
      suggestedOutline: 17, // Dark grey
      description: "Zombies, skeletons, ghosts, vampires, liches",
    },
    animal: {
      name: "Animal",
      type: "animal",
      basePalette: [...MONSTER_PALETTES.animal.slice(0, 8)],
      suggestedOutline: 16,
      description: "Animals and natural creatures: wolves, bears, bats",
    },
    dragon: {
      name: "Dragon",
      type: "dragon",
      basePalette: [...MONSTER_PALETTES.dragon.slice(0, 8)],
      suggestedOutline: 16,
      description: "Dragons of various colors and elements",
    },
    demon: {
      name: "Demon",
      type: "demon",
      basePalette: [...MONSTER_PALETTES.demon.slice(0, 8)],
      suggestedOutline: 16,
      description: "Demons, devils, and hellish creatures",
    },
    elemental: {
      name: "Elemental",
      type: "elemental",
      basePalette: [...MONSTER_PALETTES.elemental.slice(0, 8)],
      suggestedOutline: 17,
      description: "Fire, water, air, earth elementals",
    },
    magical: {
      name: "Magical",
      type: "magical",
      basePalette: [...MONSTER_PALETTES.magical.slice(0, 8)],
      suggestedOutline: 17,
      description: "Unicorns, nymphs, and other magical beings",
    },
  };

// ============================================
// OBJECT TEMPLATES
// ============================================

export interface ObjectTemplate {
  name: string;
  type: ObjectType;
  basePalette: number[];
  suggestedOutline: number;
  description: string;
}

// Only include object types that exist in ObjectType
export const OBJECT_TEMPLATES: Partial<Record<ObjectType, ObjectTemplate>> = {
  weapon: {
    name: "Weapon",
    type: "weapon",
    basePalette: [...OBJECT_PALETTES.weapon.slice(0, 8)],
    suggestedOutline: 17,
    description: "Swords, axes, bows, daggers, polearms",
  },
  armor: {
    name: "Armor",
    type: "armor",
    basePalette: [...OBJECT_PALETTES.armor.slice(0, 8)],
    suggestedOutline: 17,
    description: "Helmets, shields, body armor, boots",
  },
  potion: {
    name: "Potion",
    type: "potion",
    basePalette: [...OBJECT_PALETTES.potion.slice(0, 8)],
    suggestedOutline: 16,
    description: "Colorful bottles with magical liquids",
  },
  scroll: {
    name: "Scroll",
    type: "scroll",
    basePalette: [...OBJECT_PALETTES.scroll.slice(0, 8)],
    suggestedOutline: 4, // Brown
    description: "Parchment scrolls with magical writings",
  },
  wand: {
    name: "Wand",
    type: "wand",
    basePalette: [...OBJECT_PALETTES.wand.slice(0, 8)],
    suggestedOutline: 17,
    description: "Magical wands and staffs",
  },
  ring: {
    name: "Ring",
    type: "ring",
    basePalette: [...OBJECT_PALETTES.ring.slice(0, 8)],
    suggestedOutline: 16,
    description: "Magical rings and jewelry",
  },
  food: {
    name: "Food",
    type: "food",
    basePalette: [...OBJECT_PALETTES.food.slice(0, 8)],
    suggestedOutline: 4,
    description: "Edible items: rations, corpses, fruit",
  },
  tool: {
    name: "Tool",
    type: "tool",
    basePalette: [...OBJECT_PALETTES.tool.slice(0, 8)],
    suggestedOutline: 17,
    description: "Keys, lamps, pickaxes, instruments",
  },
  gem: {
    name: "Gem",
    type: "gem",
    basePalette: [...OBJECT_PALETTES.gem.slice(0, 8)],
    suggestedOutline: 16,
    description: "Precious stones and diamonds",
  },
  gold: {
    name: "Gold",
    type: "gold",
    basePalette: [...OBJECT_PALETTES.gold.slice(0, 8)],
    suggestedOutline: 10, // Dark orange
    description: "Gold coins and treasure piles",
  },
};

// ============================================
// DUNGEON TEMPLATES
// ============================================

export interface DungeonTemplate {
  name: string;
  type: DungeonType;
  basePalette: number[];
  suggestedOutline: number;
  description: string;
}

export const DUNGEON_TEMPLATES: Partial<Record<DungeonType, DungeonTemplate>> =
  {
    floor: {
      name: "Floor",
      type: "floor",
      basePalette: [...DUNGEON_PALETTES.floor.slice(0, 8)],
      suggestedOutline: 17,
      description: "Stone, dirt, grass floor tiles",
    },
    wall: {
      name: "Wall",
      type: "wall",
      basePalette: [...DUNGEON_PALETTES.wall.slice(0, 8)],
      suggestedOutline: 17,
      description: "Solid stone and brick walls",
    },
    door: {
      name: "Door",
      type: "door",
      basePalette: [...DUNGEON_PALETTES.door.slice(0, 8)],
      suggestedOutline: 4,
      description: "Open, closed, locked, secret doors",
    },
    stairs: {
      name: "Stairs",
      type: "stairs",
      basePalette: [...DUNGEON_PALETTES.stairs.slice(0, 8)],
      suggestedOutline: 17,
      description: "Up and down staircases",
    },
    trap: {
      name: "Trap",
      type: "trap",
      basePalette: [...DUNGEON_PALETTES.trap.slice(0, 8)],
      suggestedOutline: 8, // Danger red
      description: "Pit traps, dart traps, teleporters",
    },
    altar: {
      name: "Altar",
      type: "altar",
      basePalette: [...DUNGEON_PALETTES.altar.slice(0, 8)],
      suggestedOutline: 17,
      description: "Altars for gods and sacrifice",
    },
    fountain: {
      name: "Fountain",
      type: "fountain",
      basePalette: [...DUNGEON_PALETTES.fountain.slice(0, 8)],
      suggestedOutline: 19,
      description: "Water fountains and springs",
    },
    special: {
      name: "Special",
      type: "special",
      basePalette: [...DUNGEON_PALETTES.special.slice(0, 8)],
      suggestedOutline: 16,
      description: "Thrones, graves, magic portals",
    },
  };

// ============================================
// TEMPLATE FACTORY FUNCTIONS
// ============================================

/**
 * Create a new monster sprite from template
 */
export function createMonsterFromTemplate(
  type: MonsterType,
  name: string,
  attribution?: string
): NetHackSprite {
  const template = MONSTER_TEMPLATES[type];
  const palette = template
    ? [...template.basePalette]
    : MONSTER_PALETTES.humanoid.slice(0, 8);

  return createNetHackSprite(
    name.toLowerCase().replace(/\s+/g, "_"),
    "monsters",
    {
      name,
      subtype: type,
      nethackName: attribution,
      palette,
    }
  );
}

/**
 * Create a new object sprite from template
 */
export function createObjectFromTemplate(
  type: ObjectType,
  name: string,
  attribution?: string
): NetHackSprite {
  const template = OBJECT_TEMPLATES[type];
  const palette = template
    ? [...template.basePalette]
    : OBJECT_PALETTES.weapon.slice(0, 8);

  return createNetHackSprite(
    name.toLowerCase().replace(/\s+/g, "_"),
    "objects",
    {
      name,
      subtype: type,
      nethackName: attribution,
      palette,
    }
  );
}

/**
 * Create a new dungeon sprite from template
 */
export function createDungeonFromTemplate(
  type: DungeonType,
  name: string,
  attribution?: string
): NetHackSprite {
  const template = DUNGEON_TEMPLATES[type];
  const palette = template
    ? [...template.basePalette]
    : DUNGEON_PALETTES.floor.slice(0, 8);

  return createNetHackSprite(
    name.toLowerCase().replace(/\s+/g, "_"),
    "dungeon",
    {
      name,
      subtype: type,
      nethackName: attribution,
      palette,
    }
  );
}

/**
 * Get template info for display in UI
 */
export function getTemplateInfo(
  category: SpriteCategory,
  subtype: string
): {
  name: string;
  palette: number[];
  outline: number;
  description: string;
  colors: Array<{ index: number; hex: string; name: string }>;
} | null {
  let template: MonsterTemplate | ObjectTemplate | DungeonTemplate | undefined;

  switch (category) {
    case "monsters":
      template = MONSTER_TEMPLATES[subtype as MonsterType];
      break;
    case "objects":
      template = OBJECT_TEMPLATES[subtype as ObjectType];
      break;
    case "dungeon":
      template = DUNGEON_TEMPLATES[subtype as DungeonType];
      break;
    default:
      return null;
  }

  if (!template) return null;

  // Map palette indices to color info
  const colors = template.basePalette.map((index) => ({
    index,
    hex: UCODE_PALETTE[index],
    name: getColorName(index),
  }));

  return {
    name: template.name,
    palette: template.basePalette,
    outline: template.suggestedOutline,
    description: template.description,
    colors,
  };
}

/**
 * Get human-readable color name
 */
function getColorName(index: number): string {
  const names: Record<number, string> = {
    0: "Transparent",
    1: "Cyan",
    2: "Light Blue",
    3: "Dark Blue",
    4: "Light Brown",
    5: "Dark Brown",
    6: "Tan/Stone",
    7: "Purple",
    8: "Red",
    9: "Light Red",
    10: "Dark Orange",
    11: "Orange",
    12: "Yellow",
    13: "Light Yellow",
    14: "Green",
    15: "Dark Green",
    16: "Black",
    17: "Dark Grey",
    18: "Grey",
    19: "Medium Grey",
    20: "Light Grey",
    21: "Lighter Grey",
    22: "Near White",
    23: "White",
  };
  return names[index] || `Color ${index}`;
}

/**
 * List all available templates
 */
export function listAllTemplates(): {
  monsters: MonsterTemplate[];
  objects: ObjectTemplate[];
  dungeon: DungeonTemplate[];
} {
  return {
    monsters: Object.values(MONSTER_TEMPLATES),
    objects: Object.values(OBJECT_TEMPLATES),
    dungeon: Object.values(DUNGEON_TEMPLATES),
  };
}
