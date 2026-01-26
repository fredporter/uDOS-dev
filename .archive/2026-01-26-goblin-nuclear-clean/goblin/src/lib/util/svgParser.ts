/**
 * SVG Parser and Utilities
 *
 * Parse, manipulate, and rasterize SVG for the SVG Processor
 */

import {
  quantizeToUdosPalette,
  hexToRgb,
  UDOS_PALETTE,
  type RGB,
} from "$lib/util/colorQuantizer";

/**
 * SVG document metadata
 */
export interface SVGMetadata {
  width: number;
  height: number;
  viewBox?: string;
  title?: string;
  description?: string;
}

/**
 * Parse SVG string and extract metadata
 */
export function parseSVGMetadata(svgString: string): SVGMetadata {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");
  const svg = doc.querySelector("svg");

  if (!svg) {
    throw new Error("Invalid SVG: No <svg> element found");
  }

  const width = parseInt(svg.getAttribute("width") || "24");
  const height = parseInt(svg.getAttribute("height") || "24");
  const viewBox = svg.getAttribute("viewBox") || undefined;
  const title = doc.querySelector("title")?.textContent || undefined;
  const description = doc.querySelector("desc")?.textContent || undefined;

  return { width, height, viewBox, title, description };
}

/**
 * Rasterize SVG to ImageData
 * Uses canvas to convert SVG to pixels
 */
export async function rasterizeSVG(
  svgString: string,
  targetWidth: number,
  targetHeight: number
): Promise<ImageData> {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement("canvas");
    canvas.width = targetWidth;
    canvas.height = targetHeight;
    const ctx = canvas.getContext("2d");

    if (!ctx) {
      reject(new Error("Failed to get canvas context"));
      return;
    }

    const img = new Image();
    const blob = new Blob([svgString], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);

    img.onload = () => {
      ctx.clearRect(0, 0, targetWidth, targetHeight);
      ctx.drawImage(img, 0, 0, targetWidth, targetHeight);
      const imageData = ctx.getImageData(0, 0, targetWidth, targetHeight);
      URL.revokeObjectURL(url);
      resolve(imageData);
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Failed to load SVG image"));
    };

    img.src = url;
  });
}

/**
 * Convert SVG to uDOS palette pixel grid
 */
export async function svgToPixelGrid(
  svgString: string,
  width: number = 24,
  height: number = 24
): Promise<(number | null)[][]> {
  const imageData = await rasterizeSVG(svgString, width, height);
  const pixels: (number | null)[][] = Array(height)
    .fill(null)
    .map(() => Array(width).fill(null));

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const i = (y * width + x) * 4;
      const r = imageData.data[i];
      const g = imageData.data[i + 1];
      const b = imageData.data[i + 2];
      const a = imageData.data[i + 3];

      if (a < 128) {
        pixels[y][x] = null; // Transparent
      } else {
        pixels[y][x] = quantizeToUdosPalette([r, g, b]);
      }
    }
  }

  return pixels;
}

/**
 * Extract colors from SVG
 */
export function extractSVGColors(svgString: string): string[] {
  const colorSet = new Set<string>();
  const colorRegex =
    /#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|rgb\([^)]+\)|rgba\([^)]+\)/g;
  const matches = svgString.match(colorRegex);

  if (matches) {
    matches.forEach((color) => {
      // Normalize to hex
      if (color.startsWith("rgb")) {
        // Parse rgb/rgba to hex
        const nums = color.match(/\d+/g);
        if (nums && nums.length >= 3) {
          const r = parseInt(nums[0]);
          const g = parseInt(nums[1]);
          const b = parseInt(nums[2]);
          const hex =
            "#" +
            [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
          colorSet.add(hex);
        }
      } else {
        colorSet.add(color);
      }
    });
  }

  return Array.from(colorSet);
}

/**
 * Replace colors in SVG with uDOS palette
 */
export function remapSVGColors(svgString: string): string {
  const colors = extractSVGColors(svgString);
  let result = svgString;

  colors.forEach((color) => {
    try {
      const rgb = hexToRgb(color);
      const paletteIndex = quantizeToUdosPalette(rgb);
      const paletteColor = UDOS_PALETTE[paletteIndex];

      // Replace all instances
      result = result.replace(new RegExp(color, "gi"), paletteColor);
    } catch (e) {
      console.warn(`Failed to remap color: ${color}`, e);
    }
  });

  return result;
}

/**
 * Optimize SVG (remove unnecessary attributes, comments)
 */
export function optimizeSVG(svgString: string): string {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");
  const svg = doc.querySelector("svg");

  if (!svg) return svgString;

  // Remove comments
  const removeComments = (node: Node) => {
    const children = Array.from(node.childNodes);
    children.forEach((child) => {
      if (child.nodeType === Node.COMMENT_NODE) {
        node.removeChild(child);
      } else {
        removeComments(child);
      }
    });
  };
  removeComments(svg);

  // Remove unnecessary attributes
  const unnecessaryAttrs = ["id", "class", "data-name"];
  const removeAttrs = (element: Element) => {
    unnecessaryAttrs.forEach((attr) => {
      element.removeAttribute(attr);
    });
    Array.from(element.children).forEach((child) => removeAttrs(child));
  };
  removeAttrs(svg);

  return new XMLSerializer().serializeToString(svg);
}

/**
 * Create SVG from pixel grid
 */
export function pixelGridToSVG(
  pixels: (number | null)[][],
  palette: string[],
  cellSize: number = 1
): string {
  const height = pixels.length;
  const width = pixels[0]?.length || 0;

  let rects = "";
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const paletteIndex = pixels[y][x];
      if (paletteIndex !== null) {
        const color = palette[paletteIndex];
        rects += `  <rect x="${x * cellSize}" y="${y * cellSize}" width="${cellSize}" height="${cellSize}" fill="${color}"/>\n`;
      }
    }
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width * cellSize}" height="${height * cellSize}" viewBox="0 0 ${width * cellSize} ${height * cellSize}">
${rects}</svg>`;
}

/**
 * Convert ASCII art to SVG
 */
export function asciiToSVG(ascii: string, charSize: number = 10): string {
  const lines = ascii.split("\n");
  const height = lines.length;
  const width = Math.max(...lines.map((l) => l.length));

  let text = "";
  lines.forEach((line, y) => {
    Array.from(line).forEach((char, x) => {
      if (char.trim()) {
        text += `  <text x="${x * charSize}" y="${(y + 1) * charSize}" font-family="monospace" font-size="${charSize}" fill="black">${char}</text>\n`;
      }
    });
  });

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width * charSize}" height="${height * charSize}">
${text}</svg>`;
}

/**
 * Validate SVG string
 */
export function isValidSVG(svgString: string): boolean {
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(svgString, "image/svg+xml");
    const parserError = doc.querySelector("parsererror");
    return !parserError && !!doc.querySelector("svg");
  } catch {
    return false;
  }
}
