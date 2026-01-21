// @ts-nocheck
/**
 * Font Exporter Utility
 * Exports edited character data as TTF or OTF font files
 */

import type { CharacterData } from "./fontLoader";
import opentype from "opentype.js";

/**
 * Export characters as a TTF font file to sandbox/drafts
 * @param characters - Array of character data to export
 * @param fontName - Name of the font
 */
export async function exportFont(
  characters: CharacterData[],
  fontName: string
): Promise<void> {
  try {
    // Use opentype.js for TTF export
    await exportWithOpenType(characters, fontName);
  } catch (error) {
    console.error("Export error:", error);
    throw error;
  }
}

/**
 * Export using opentype.js library - TTF only for monosorts square fonts
 */
async function exportWithOpenType(
  characters: CharacterData[],
  fontName: string
): Promise<void> {
  // Determine grid size from first character
  const gridSize = characters[0]?.width || 24;

  // Convert each character to a glyph
  const glyphs: opentype.Glyph[] = [
    // First glyph is always .notdef
    new opentype.Glyph({
      name: ".notdef",
      advanceWidth: 1024,
      path: new opentype.Path(),
    }),
  ];

  for (const char of characters) {
    const path = pixelsToPath(char.pixels, gridSize);
    const glyph = new opentype.Glyph({
      name: `char${char.code}`,
      unicode: char.code,
      advanceWidth: 1024, // Square monospace
      path,
    });
    glyphs.push(glyph);
  }

  // Create a new monosorts square font
  const font = new opentype.Font({
    familyName: fontName,
    styleName: "Regular",
    unitsPerEm: 1024,
    ascender: 800,
    descender: -200,
    glyphs: glyphs,
  });

  // Download the font as TTF
  const arrayBuffer = font.toArrayBuffer();
  const blob = new Blob([arrayBuffer], { type: "font/ttf" });
  downloadBlob(blob, `${fontName}.ttf`);
}

/**
 * Convert pixel grid to OpenType path
 */
function pixelsToPath(pixels: boolean[][], gridSize: number): opentype.Path {
  const path = new opentype.Path();
  const scale = 1024 / gridSize; // Scale to font units

  // Create rectangles for each "on" pixel
  for (let y = 0; y < pixels.length; y++) {
    for (let x = 0; x < pixels[y].length; x++) {
      if (pixels[y][x]) {
        const x1 = x * scale;
        const y1 = (gridSize - y - 1) * scale; // Flip Y axis
        const x2 = (x + 1) * scale;
        const y2 = (gridSize - y) * scale;

        // Draw a rectangle
        path.moveTo(x1, y1);
        path.lineTo(x2, y1);
        path.lineTo(x2, y2);
        path.lineTo(x1, y2);
        path.closePath();
      }
    }
  }

  return path;
}

/**
 * Fallback: Export as JSON
 */
async function exportAsJSON(
  characters: CharacterData[],
  fontName: string
): Promise<void> {
  const data = {
    name: fontName,
    gridSize: 24,
    characters: characters.map((char) => ({
      code: char.code,
      char: char.char,
      pixels: char.pixels,
    })),
    metadata: {
      created: new Date().toISOString(),
      version: "1.0.0",
    },
  };

  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  downloadBlob(blob, `${fontName}.json`);
}

/**
 * Download a blob as a file
 */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Import a JSON font file
 */
export async function importJSON(file: File): Promise<CharacterData[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target?.result as string);
        const characters: CharacterData[] = json.characters.map(
          (char: any) => ({
            code: char.code,
            char: char.char,
            pixels: char.pixels,
            width: json.gridSize || 24,
            height: json.gridSize || 24,
          })
        );
        resolve(characters);
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

/**
 * Export individual character as PNG image
 */
export function exportCharacterAsPNG(
  char: CharacterData,
  scale: number = 16
): void {
  const canvas = document.createElement("canvas");
  const size = char.height * scale;
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");

  if (!ctx) return;

  // Draw pixels
  for (let y = 0; y < char.pixels.length; y++) {
    for (let x = 0; x < char.pixels[y].length; x++) {
      if (char.pixels[y][x]) {
        ctx.fillStyle = char.color || "#000000";
        ctx.fillRect(x * scale, y * scale, scale, scale);
      }
    }
  }

  // Download
  canvas.toBlob((blob) => {
    if (blob) {
      downloadBlob(blob, `char_${char.code}.png`);
    }
  });
}

/**
 * Export all characters as a sprite sheet
 */
export function exportSpriteSheet(
  characters: CharacterData[],
  cols: number = 16
): void {
  const gridSize = 24;
  const padding = 2;
  const cellSize = gridSize + padding;
  const rows = Math.ceil(characters.length / cols);

  const canvas = document.createElement("canvas");
  canvas.width = cols * cellSize;
  canvas.height = rows * cellSize;
  const ctx = canvas.getContext("2d");

  if (!ctx) return;

  // Fill background
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Draw each character
  characters.forEach((char, index) => {
    const col = index % cols;
    const row = Math.floor(index / cols);
    const offsetX = col * cellSize;
    const offsetY = row * cellSize;

    for (let y = 0; y < char.pixels.length; y++) {
      for (let x = 0; x < char.pixels[y].length; x++) {
        if (char.pixels[y][x]) {
          ctx.fillStyle = char.color || "#000000";
          ctx.fillRect(offsetX + x, offsetY + y, 1, 1);
        }
      }
    }
  });

  // Download
  canvas.toBlob((blob) => {
    if (blob) {
      downloadBlob(blob, "spritesheet.png");
    }
  });
}
