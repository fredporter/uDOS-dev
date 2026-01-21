/**
 * Format Converters
 *
 * Convert between ASCII art, SVG, Markdown diagrams, Teletext, and pixel grids
 */

import { UDOS_PALETTE } from "$lib/util/colorQuantizer";
import type { Tile, Layer } from "$lib/types/layer";

/**
 * Convert 24x24 pixel grid to ASCII block art
 */
export function pixelGridToAscii(
  pixels: (number | null)[][],
  palette: string[] = UDOS_PALETTE
): string {
  const height = pixels.length;
  const width = pixels[0]?.length || 0;

  // Map to block characters based on density
  const lines: string[] = [];

  for (let y = 0; y < height; y += 2) {
    let line = "";
    for (let x = 0; x < width; x++) {
      const top = pixels[y]?.[x] !== null;
      const bottom = pixels[y + 1]?.[x] !== null;

      if (top && bottom) {
        line += "█"; // Full block
      } else if (top) {
        line += "▀"; // Upper half
      } else if (bottom) {
        line += "▄"; // Lower half
      } else {
        line += " "; // Empty
      }
    }
    lines.push(line);
  }

  return lines.join("\n");
}

/**
 * Convert ASCII art to pixel grid
 */
export function asciiToPixelGrid(
  ascii: string,
  width: number = 24,
  height: number = 24
): (number | null)[][] {
  const lines = ascii.split("\n");
  const pixels: (number | null)[][] = Array(height)
    .fill(null)
    .map(() => Array(width).fill(null));

  // Character density map
  const densityMap: Record<string, number> = {
    " ": 0,
    "░": 0.25,
    "▒": 0.5,
    "▓": 0.75,
    "█": 1,
    "▀": 0.5,
    "▄": 0.5,
    "▌": 0.5,
    "▐": 0.5,
  };

  lines.forEach((line, y) => {
    if (y >= height) return;
    Array.from(line).forEach((char, x) => {
      if (x >= width) return;
      const density = densityMap[char] ?? (char.trim() ? 1 : 0);
      if (density > 0) {
        // Map to greyscale palette index (16-23)
        const greyIndex = Math.floor(16 + density * 7);
        pixels[y][x] = greyIndex;
      }
    });
  });

  return pixels;
}

/**
 * Convert Layer to ASCII art
 */
export function layerToAscii(layer: Layer): string {
  const lines: string[] = [];

  layer.tiles.forEach((row) => {
    const line = row.map((tile) => tile.char).join("");
    lines.push(line);
  });

  return lines.join("\n");
}

/**
 * Convert ASCII art to Layer tiles
 */
export function asciiToLayer(
  ascii: string,
  width: number = 60,
  height: number = 20
): Tile[][] {
  const lines = ascii.split("\n");
  const tiles: Tile[][] = [];

  for (let y = 0; y < height; y++) {
    const row: Tile[] = [];
    const line = lines[y] || "";

    for (let x = 0; x < width; x++) {
      const char = line[x] || " ";
      row.push({
        char,
        code: char.charCodeAt(0),
      });
    }

    tiles.push(row);
  }

  return tiles;
}

/**
 * Convert Mermaid diagram to ASCII art (simplified)
 */
export function mermaidToAscii(mermaid: string): string {
  // Simple box and arrow converter
  // Full Mermaid parsing would require a library

  const lines = mermaid.split("\n");
  const result: string[] = [];

  lines.forEach((line) => {
    const trimmed = line.trim();

    // Node definitions
    if (trimmed.match(/^[A-Z]+\[.+\]$/)) {
      const match = trimmed.match(/^([A-Z]+)\[(.+)\]$/);
      if (match) {
        const [, id, label] = match;
        result.push(`┌─────────────┐`);
        result.push(`│ ${label.padEnd(11)} │`);
        result.push(`└─────────────┘`);
      }
    }

    // Connections
    else if (trimmed.includes("-->")) {
      result.push(`      ↓`);
    }
  });

  return result.join("\n");
}

/**
 * Convert ASCII flowchart to Mermaid
 */
export function asciiToMermaid(ascii: string): string {
  // Detect boxes and arrows, convert to Mermaid syntax
  const lines = ascii.split("\n");
  const nodes: string[] = [];
  const connections: string[] = [];

  let nodeId = 0;
  const nodeMap = new Map<number, string>();

  lines.forEach((line, y) => {
    // Detect box start (┌─)
    if (line.includes("┌─")) {
      const labelLine = lines[y + 1];
      if (labelLine) {
        const label = labelLine.replace(/[│┌┐└┘]/g, "").trim();
        const id = `N${nodeId++}`;
        nodeMap.set(y, id);
        nodes.push(`${id}[${label}]`);
      }
    }

    // Detect arrows
    if (line.includes("↓") || line.includes("→")) {
      // Simple connection detection
      // Would need more sophisticated parsing for real diagrams
    }
  });

  return `graph TD\n  ${nodes.join("\n  ")}\n  ${connections.join("\n  ")}`;
}

/**
 * Convert Teletext blocks to pixel grid
 */
export function teletextToPixelGrid(
  teletext: string,
  width: number = 24,
  height: number = 24
): (number | null)[][] {
  // Teletext uses specific block characters
  const lines = teletext.split("\n");
  const pixels: (number | null)[][] = Array(height)
    .fill(null)
    .map(() => Array(width).fill(null));

  // Teletext character mappings (simplified)
  const teletextMap: Record<string, boolean[][]> = {
    "█": Array(4)
      .fill(null)
      .map(() => Array(2).fill(true)),
    "▀": [
      [true, true],
      [true, true],
      [false, false],
      [false, false],
    ],
    "▄": [
      [false, false],
      [false, false],
      [true, true],
      [true, true],
    ],
    "▌": Array(4)
      .fill(null)
      .map(() => [true, false]),
    "▐": Array(4)
      .fill(null)
      .map(() => [false, true]),
  };

  lines.forEach((line, cy) => {
    const charY = cy * 4; // Each char is 4 pixels high
    Array.from(line).forEach((char, cx) => {
      const charX = cx * 2; // Each char is 2 pixels wide
      const pattern = teletextMap[char];
      if (pattern) {
        pattern.forEach((row, py) => {
          row.forEach((filled, px) => {
            const y = charY + py;
            const x = charX + px;
            if (y < height && x < width && filled) {
              pixels[y][x] = 16; // Black (greyscale)
            }
          });
        });
      }
    });
  });

  return pixels;
}

/**
 * Convert pixel grid to Teletext blocks
 */
export function pixelGridToTeletext(pixels: (number | null)[][]): string {
  const height = pixels.length;
  const width = pixels[0]?.length || 0;
  const lines: string[] = [];

  // Process in 4x2 blocks (teletext char size)
  for (let y = 0; y < height; y += 4) {
    let line = "";
    for (let x = 0; x < width; x += 2) {
      const tl = pixels[y]?.[x] !== null;
      const tr = pixels[y]?.[x + 1] !== null;
      const ml1 = pixels[y + 1]?.[x] !== null;
      const mr1 = pixels[y + 1]?.[x + 1] !== null;
      const ml2 = pixels[y + 2]?.[x] !== null;
      const mr2 = pixels[y + 2]?.[x + 1] !== null;
      const bl = pixels[y + 3]?.[x] !== null;
      const br = pixels[y + 3]?.[x + 1] !== null;

      const top = tl || tr || ml1 || mr1;
      const bottom = ml2 || mr2 || bl || br;
      const left = tl || ml1 || ml2 || bl;
      const right = tr || mr1 || mr2 || br;

      if (top && bottom && left && right) {
        line += "█";
      } else if (top && !bottom) {
        line += "▀";
      } else if (!top && bottom) {
        line += "▄";
      } else if (left && !right) {
        line += "▌";
      } else if (!left && right) {
        line += "▐";
      } else {
        line += " ";
      }
    }
    lines.push(line);
  }

  return lines.join("\n");
}

/**
 * Generate Markdown code block for graphics
 */
export function wrapInCodeBlock(
  content: string,
  type: "ascii" | "teletext" | "diagram" = "ascii"
): string {
  const lang = type === "diagram" ? "mermaid" : type;
  return `\`\`\`${lang}\n${content}\n\`\`\``;
}

/**
 * Extract graphics from Markdown code blocks
 */
export function extractFromMarkdown(markdown: string): Array<{
  type: string;
  content: string;
  startLine: number;
}> {
  const blocks: Array<{ type: string; content: string; startLine: number }> =
    [];
  const lines = markdown.split("\n");
  let inBlock = false;
  let blockType = "";
  let blockContent: string[] = [];
  let blockStart = 0;

  lines.forEach((line, i) => {
    if (line.startsWith("```")) {
      if (!inBlock) {
        // Start of block
        inBlock = true;
        blockType = line.slice(3).trim() || "text";
        blockContent = [];
        blockStart = i;
      } else {
        // End of block
        inBlock = false;
        blocks.push({
          type: blockType,
          content: blockContent.join("\n"),
          startLine: blockStart,
        });
      }
    } else if (inBlock) {
      blockContent.push(line);
    }
  });

  return blocks;
}
