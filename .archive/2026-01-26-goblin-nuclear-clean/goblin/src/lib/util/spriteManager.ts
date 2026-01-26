/**
 * NetHack Sprite Manager
 *
 * Utilities for saving, loading, and managing NetHack sprites
 */

import type {
  NetHackSprite,
  SpriteCategory,
  SpriteMetadata,
} from "$lib/types/nethackSprite";
import { invoke } from "@tauri-apps/api/core";

const SPRITE_BASE_PATH = "../memory/sandbox/sprites";

/**
 * Get path for sprite category
 */
function getCategoryPath(category: SpriteCategory): string {
  return `${SPRITE_BASE_PATH}/${category}`;
}

/**
 * Get full path for a sprite file
 */
function getSpritePath(sprite: NetHackSprite): string {
  return `${getCategoryPath(sprite.metadata.category)}/${sprite.metadata.id}.json`;
}

/**
 * Save sprite to file
 */
export async function saveSprite(sprite: NetHackSprite): Promise<void> {
  const path = getSpritePath(sprite);
  const json = JSON.stringify(sprite, null, 2);

  try {
    await invoke("write_file", { path, contents: json });
  } catch (error) {
    console.error("Failed to save sprite:", error);
    throw new Error(`Failed to save sprite: ${error}`);
  }
}

/**
 * Load sprite from file
 */
export async function loadSprite(
  category: SpriteCategory,
  id: string
): Promise<NetHackSprite> {
  const path = `${getCategoryPath(category)}/${id}.json`;

  try {
    const contents = await invoke<string>("read_file", { path });
    return JSON.parse(contents);
  } catch (error) {
    console.error("Failed to load sprite:", error);
    throw new Error(`Failed to load sprite: ${error}`);
  }
}

/**
 * List all sprites in a category
 */
export async function listSprites(
  category: SpriteCategory
): Promise<SpriteMetadata[]> {
  const path = getCategoryPath(category);

  try {
    const files = await invoke<string[]>("list_directory", { path });
    const sprites: SpriteMetadata[] = [];

    for (const file of files) {
      if (file.endsWith(".json")) {
        try {
          const sprite = await loadSprite(category, file.replace(".json", ""));
          sprites.push(sprite.metadata);
        } catch (e) {
          console.warn(`Failed to load sprite metadata: ${file}`, e);
        }
      }
    }

    return sprites;
  } catch (error) {
    console.warn("Failed to list sprites:", error);
    return [];
  }
}

/**
 * Delete sprite
 */
export async function deleteSprite(
  category: SpriteCategory,
  id: string
): Promise<void> {
  const path = `${getCategoryPath(category)}/${id}.json`;

  try {
    await invoke("delete_file", { path });
  } catch (error) {
    console.error("Failed to delete sprite:", error);
    throw new Error(`Failed to delete sprite: ${error}`);
  }
}

/**
 * Export sprite as PNG
 */
export async function exportSpritePNG(
  sprite: NetHackSprite,
  palette: string[],
  outputPath: string
): Promise<void> {
  // Create canvas and render
  const canvas = document.createElement("canvas");
  canvas.width = 24;
  canvas.height = 24;
  const ctx = canvas.getContext("2d");

  if (!ctx) throw new Error("Failed to get canvas context");

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

  // Convert to PNG and save
  const dataUrl = canvas.toDataURL("image/png");
  const base64 = dataUrl.split(",")[1];

  await invoke("write_binary_file", {
    path: outputPath,
    contents: base64,
    encoding: "base64",
  });
}

/**
 * Export all sprites in category as PNG tileset
 */
export async function exportCategoryTileset(
  category: SpriteCategory,
  palette: string[],
  outputPath: string,
  columns: number = 16
): Promise<void> {
  const sprites = await listSprites(category);
  if (sprites.length === 0) return;

  const rows = Math.ceil(sprites.length / columns);
  const canvas = document.createElement("canvas");
  canvas.width = columns * 24;
  canvas.height = rows * 24;
  const ctx = canvas.getContext("2d");

  if (!ctx) throw new Error("Failed to get canvas context");

  // Clear
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw each sprite
  for (let i = 0; i < sprites.length; i++) {
    const sprite = await loadSprite(category, sprites[i].id);
    const col = i % columns;
    const row = Math.floor(i / columns);
    const offsetX = col * 24;
    const offsetY = row * 24;

    sprite.pixels.forEach((pixelRow, y) => {
      pixelRow.forEach((paletteIndex, x) => {
        if (paletteIndex !== null && palette[paletteIndex]) {
          ctx.fillStyle = palette[paletteIndex];
          ctx.fillRect(offsetX + x, offsetY + y, 1, 1);
        }
      });
    });
  }

  // Save
  const dataUrl = canvas.toDataURL("image/png");
  const base64 = dataUrl.split(",")[1];

  await invoke("write_binary_file", {
    path: outputPath,
    contents: base64,
    encoding: "base64",
  });
}

/**
 * Import sprite from PNG (requires color quantization)
 */
export async function importSpriteFromPNG(
  imagePath: string,
  metadata: SpriteMetadata,
  quantize: (rgb: [number, number, number]) => number
): Promise<NetHackSprite> {
  // Load image
  const img = new Image();

  return new Promise((resolve, reject) => {
    img.onload = () => {
      // Create canvas
      const canvas = document.createElement("canvas");
      canvas.width = 24;
      canvas.height = 24;
      const ctx = canvas.getContext("2d");

      if (!ctx) {
        reject(new Error("Failed to get canvas context"));
        return;
      }

      // Draw and scale to 24x24
      ctx.drawImage(img, 0, 0, 24, 24);
      const imageData = ctx.getImageData(0, 0, 24, 24);

      // Convert to sprite pixels
      const pixels: (number | null)[][] = Array(24)
        .fill(null)
        .map(() => Array(24).fill(null));

      for (let y = 0; y < 24; y++) {
        for (let x = 0; x < 24; x++) {
          const i = (y * 24 + x) * 4;
          const r = imageData.data[i];
          const g = imageData.data[i + 1];
          const b = imageData.data[i + 2];
          const a = imageData.data[i + 3];

          if (a < 128) {
            pixels[y][x] = null;
          } else {
            pixels[y][x] = quantize([r, g, b]);
          }
        }
      }

      resolve({
        metadata: {
          ...metadata,
          modified: new Date().toISOString(),
        },
        pixels,
      });
    };

    img.onerror = () => reject(new Error("Failed to load image"));
    img.src = imagePath;
  });
}
