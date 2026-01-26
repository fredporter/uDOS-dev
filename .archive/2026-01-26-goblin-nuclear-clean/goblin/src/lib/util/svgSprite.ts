/**
 * SVG Sprite Utilities
 *
 * Convert between pixel grid format and SVG rect-based format
 * for use with Pixel Editor and SVG Processor
 */

import type { NetHackSprite } from "../types/nethackSprite";
import { getAllColors } from "./udosPalette";

export interface SVGSpriteOptions {
  /** Grid size (default: 24x24) */
  gridSize?: number;
  /** Optimize by combining adjacent same-color rects */
  optimize?: boolean;
  /** Add metadata as SVG title/desc elements */
  includeMetadata?: boolean;
}

/**
 * Convert pixel grid to SVG string
 */
export function pixelGridToSVG(
  sprite: NetHackSprite,
  options: SVGSpriteOptions = {}
): string {
  const { gridSize = 24, optimize = true, includeMetadata = true } = options;

  const lines: string[] = [];
  lines.push(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${gridSize} ${gridSize}">`
  );

  if (includeMetadata) {
    lines.push(`  <title>${sprite.metadata.name}</title>`);
    if (sprite.metadata.description) {
      lines.push(`  <desc>${sprite.metadata.description}</desc>`);
    }
    lines.push(`  <!-- Category: ${sprite.metadata.category} -->`);
    lines.push(`  <!-- Created: ${sprite.metadata.created} -->`);
    lines.push(`  <!-- uDOS Sprite ID: ${sprite.metadata.id} -->`);
  }

  if (optimize) {
    // Combine adjacent horizontal pixels of same color
    const rects = optimizePixelsToRects(sprite.pixels);
    rects.forEach((rect) => {
      lines.push(
        `  <rect x="${rect.x}" y="${rect.y}" width="${rect.width}" height="${rect.height}" fill="${rect.color}"/>`
      );
    });
  } else {
    // Simple: one rect per pixel
    const colors = getAllColors();
    sprite.pixels.forEach((row: (number | null)[], y: number) => {
      row.forEach((paletteIndex: number | null, x: number) => {
        if (paletteIndex !== null) {
          const color = colors[paletteIndex];
          lines.push(
            `  <rect x="${x}" y="${y}" width="1" height="1" fill="${color?.hex || "#000000"}"/>`
          );
        }
      });
    });
  }

  lines.push(`</svg>`);
  return lines.join("\n");
}

/**
 * Parse SVG string to pixel grid
 */
export function svgToPixelGrid(svgString: string): (number | null)[][] {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");
  const svg = doc.querySelector("svg");

  if (!svg) {
    throw new Error("Invalid SVG: no <svg> element found");
  }

  // Extract viewBox to determine grid size
  const viewBox = svg.getAttribute("viewBox");
  const gridSize = viewBox ? parseInt(viewBox.split(" ")[2]) : 24;

  // Initialize empty grid
  const grid: (number | null)[][] = Array(gridSize)
    .fill(null)
    .map(() => Array(gridSize).fill(null));

  // Parse rect elements
  const rects = svg.querySelectorAll("rect");
  rects.forEach((rect) => {
    const x = parseFloat(rect.getAttribute("x") || "0");
    const y = parseFloat(rect.getAttribute("y") || "0");
    const width = parseFloat(rect.getAttribute("width") || "1");
    const height = parseFloat(rect.getAttribute("height") || "1");
    const fill = rect.getAttribute("fill") || "#000000";

    // Find palette index for this color
    const paletteIndex = findPaletteIndex(fill);

    // Fill all pixels covered by this rect
    for (
      let py = Math.floor(y);
      py < Math.ceil(y + height) && py < gridSize;
      py++
    ) {
      for (
        let px = Math.floor(x);
        px < Math.ceil(x + width) && px < gridSize;
        px++
      ) {
        grid[py][px] = paletteIndex;
      }
    }
  });

  return grid;
}

/**
 * Optimize pixel grid to minimal rect set (horizontal runs)
 */
function optimizePixelsToRects(pixels: (number | null)[][]): {
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
}[] {
  const rects: {
    x: number;
    y: number;
    width: number;
    height: number;
    color: string;
  }[] = [];

  pixels.forEach((row, y) => {
    let currentColor: number | null = null;
    let runStart = 0;
    let runLength = 0;

    row.forEach((paletteIndex, x) => {
      if (paletteIndex === currentColor && paletteIndex !== null) {
        // Continue current run
        runLength++;
      } else {
        // End previous run
        if (currentColor !== null && runLength > 0) {
          rects.push({
            x: runStart,
            y,
            width: runLength,
            height: 1,
            color: getAllColors()[currentColor]?.hex || "#000000",
          });
        }
        // Start new run
        currentColor = paletteIndex;
        runStart = x;
        runLength = 1;
      }
    });

    // End final run in row
    if (currentColor !== null && runLength > 0) {
      rects.push({
        x: runStart,
        y,
        width: runLength,
        height: 1,
        color: getAllColors()[currentColor]?.hex || "#000000",
      });
    }
  });

  return rects;
}

/**
 * Find closest palette index for a hex color
 */
function findPaletteIndex(hexColor: string): number | null {
  const normalized = hexColor.toLowerCase().replace("#", "");
  const colors = getAllColors();
  const index = colors.findIndex(
    (colorDef) => colorDef.hex.toLowerCase().replace("#", "") === normalized
  );
  return index >= 0 ? index : null;
}

/**
 * Create downloadable SVG blob
 */
export function createSVGBlob(svgString: string): Blob {
  return new Blob([svgString], { type: "image/svg+xml" });
}

/**
 * Download SVG file
 */
export function downloadSVG(svgString: string, filename: string): void {
  const blob = createSVGBlob(svgString);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename.endsWith(".svg") ? filename : `${filename}.svg`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Load SVG from file
 */
export async function loadSVGFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result;
      if (typeof result === "string") {
        resolve(result);
      } else {
        reject(new Error("Failed to read file as string"));
      }
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

/**
 * Get SVG data URL for inline use
 */
export function svgToDataURL(svgString: string): string {
  const encoded = encodeURIComponent(svgString);
  return `data:image/svg+xml,${encoded}`;
}
