/**
 * Sprite Library Manager
 *
 * Central registry for all SVG sprites in the uDOS system
 */

export interface SpriteMetadata {
  id: string;
  name: string;
  category: "monsters" | "objects" | "dungeon" | "effects" | "emoji";
  path: string;
  description?: string;
  tags?: string[];
}

export const SPRITE_LIBRARY: SpriteMetadata[] = [
  // Monsters
  {
    id: "dog",
    name: "Dog",
    category: "monsters",
    path: "/sprites/monsters/dog.svg",
    description: "Friendly companion animal",
    tags: ["animal", "pet", "friendly"],
  },

  // Objects
  {
    id: "sword",
    name: "Iron Sword",
    category: "objects",
    path: "/sprites/objects/sword.svg",
    description: "Basic melee weapon",
    tags: ["weapon", "blade", "metal"],
  },

  // Dungeon
  {
    id: "door_closed",
    name: "Closed Door",
    category: "dungeon",
    path: "/sprites/dungeon/door_closed.svg",
    description: "Wooden door (closed)",
    tags: ["door", "entrance", "wood"],
  },

  // Emoji
  {
    id: "rocket",
    name: "Rocket",
    category: "emoji",
    path: "/sprites/emoji/rocket.svg",
    description: "🚀 Rocket emoji",
    tags: ["emoji", "space", "rocket"],
  },
  {
    id: "fire",
    name: "Fire",
    category: "emoji",
    path: "/sprites/emoji/fire.svg",
    description: "🔥 Fire emoji",
    tags: ["emoji", "flame", "hot"],
  },
];

/**
 * Get sprite by ID
 */
export function getSpriteById(id: string): SpriteMetadata | undefined {
  return SPRITE_LIBRARY.find((sprite) => sprite.id === id);
}

/**
 * Get all sprites in a category
 */
export function getSpritesByCategory(
  category: SpriteMetadata["category"]
): SpriteMetadata[] {
  return SPRITE_LIBRARY.filter((sprite) => sprite.category === category);
}

/**
 * Search sprites by tag
 */
export function searchSpritesByTag(tag: string): SpriteMetadata[] {
  return SPRITE_LIBRARY.filter((sprite) =>
    sprite.tags?.some((t) => t.toLowerCase().includes(tag.toLowerCase()))
  );
}

/**
 * Load sprite SVG content
 */
export async function loadSprite(id: string): Promise<string> {
  const sprite = getSpriteById(id);
  if (!sprite) {
    throw new Error(`Sprite not found: ${id}`);
  }

  const response = await fetch(sprite.path);
  if (!response.ok) {
    throw new Error(`Failed to load sprite: ${sprite.path}`);
  }

  return response.text();
}

/**
 * Get all sprite categories
 */
export function getCategories(): SpriteMetadata["category"][] {
  return ["monsters", "objects", "dungeon", "effects", "emoji"];
}

/**
 * Get sprite count by category
 */
export function getCategoryCounts(): Record<string, number> {
  const counts: Record<string, number> = {};
  getCategories().forEach((category) => {
    counts[category] = getSpritesByCategory(category).length;
  });
  return counts;
}
