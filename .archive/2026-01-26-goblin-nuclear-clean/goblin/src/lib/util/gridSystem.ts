/**
 * uDOS Grid System - Shared 24x24 character cell grid utilities
 *
 * Provides consistent grid calculations for Terminal, Teledesk, and Pixel Editor.
 * Independent of Tailwind styles - uses fixed pixel measurements.
 */

export interface GridConfig {
  cellSize: number; // Default 24px for uDOS standard
  cols: number; // Number of columns
  rows: number; // Number of rows
  fontFamily: string; // CSS font-family string
}

export interface GridDimensions {
  width: number;
  height: number;
  cellSize: number;
}

/**
 * Standard uDOS grid configurations
 */
export const GRID_PRESETS = {
  // Standard 24x24 pixel cells - Terminal is 40x24 (classic terminal)
  terminal: {
    cellSize: 24,
    cols: 40,
    rows: 24,
    fontFamily: "var(--font-mono-variant)",
  },
  teledesk: {
    cellSize: 24,
    cols: 40,
    rows: 24,
    fontFamily: "var(--font-mono-variant)",
  },
  pixelEditor: {
    cellSize: 24,
    cols: 24,
    rows: 24,
    fontFamily: "var(--font-mono-variant)",
  },
} as const;

/**
 * Calculate grid dimensions from config
 */
export function calculateGridDimensions(config: GridConfig): GridDimensions {
  return {
    width: config.cols * config.cellSize,
    height: config.rows * config.cellSize,
    cellSize: config.cellSize,
  };
}

/**
 * Get CSS variables for grid styling
 */
export function getGridCSSVars(config: GridConfig): Record<string, string> {
  const dims = calculateGridDimensions(config);
  return {
    "--grid-cell-size": `${config.cellSize}px`,
    "--grid-cols": `${config.cols}`,
    "--grid-rows": `${config.rows}`,
    "--grid-width": `${dims.width}px`,
    "--grid-height": `${dims.height}px`,
    "--grid-font": config.fontFamily,
  };
}

/**
 * Convert CSS vars object to inline style string
 */
export function gridCSSToStyle(vars: Record<string, string>): string {
  return Object.entries(vars)
    .map(([key, value]) => `${key}: ${value}`)
    .join("; ");
}

/**
 * Fit grid to container dimensions while maintaining cell size
 */
export function fitGridToContainer(
  containerWidth: number,
  containerHeight: number,
  cellSize: number = 24
): { cols: number; rows: number } {
  return {
    cols: Math.floor(containerWidth / cellSize),
    rows: Math.floor(containerHeight / cellSize),
  };
}

/**
 * Calculate optimal grid size for a given aspect ratio
 */
export function calculateOptimalGrid(
  targetWidth: number,
  targetHeight: number,
  cellSize: number = 24
): GridConfig {
  const cols = Math.floor(targetWidth / cellSize);
  const rows = Math.floor(targetHeight / cellSize);

  return {
    cellSize,
    cols,
    rows,
    fontFamily: "var(--font-mono-variant)",
  };
}

/**
 * Standard uDOS colors for terminal/teledesk modes
 * Based on UDOS 32-Color Palette v2.0.0
 */
export const GRID_COLORS = {
  // Text colors (using UDOS palette)
  text: {
    input: "#00D9FF", // Objective Cyan (12)
    output: "#4C9A2A", // Grass Green (1)
    error: "#DC2626", // Danger Red (8)
    system: "#666666", // Medium Grey (19)
    white: "#FFFFFF", // White (23)
    black: "#000000", // Black (16)
  },
  // Background colors (using UDOS greyscale)
  bg: {
    screen: "#000000", // Black (16)
    container: "#1A1A1A", // Dark Grey (17)
    overlay: "rgba(0, 0, 0, 0.5)",
  },
  // Glow effects (based on UDOS markers)
  glow: {
    green: "rgba(76, 154, 42, 0.15)", // Grass Green glow
    amber: "rgba(255, 190, 11, 0.15)", // Waypoint Yellow glow
    cyan: "rgba(0, 217, 255, 0.15)", // Objective Cyan glow
    white: "rgba(255, 255, 255, 0.1)", // White glow
  },
} as const;

/**
 * Get line color class based on line type
 * Uses custom CSS variables that map to UDOS palette
 */
export function getLineColorClass(type: string): string {
  switch (type) {
    case "input":
      return "text-udos-cyan"; // Objective Cyan
    case "error":
      return "text-udos-red"; // Danger Red
    case "system":
      return "text-udos-grey"; // Medium Grey
    case "output":
    default:
      return "text-udos-green"; // Grass Green
  }
}

/**
 * Get line color hex based on line type
 */
export function getLineColorHex(type: string): string {
  return (
    GRID_COLORS.text[type as keyof typeof GRID_COLORS.text] ||
    GRID_COLORS.text.output
  );
}

/**
 * Pad string to exact column width
 */
export function padLine(line: string, cols: number): string {
  return line.padEnd(cols, " ").slice(0, cols);
}

/**
 * Split text into lines that fit within column width
 */
export function wrapText(text: string, cols: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let currentLine = "";

  for (const word of words) {
    if (currentLine.length + word.length + 1 <= cols) {
      currentLine += (currentLine ? " " : "") + word;
    } else {
      if (currentLine) lines.push(currentLine);
      currentLine = word.slice(0, cols);
    }
  }

  if (currentLine) lines.push(currentLine);
  return lines;
}

/**
 * Default grid settings for reset functionality
 */
export const DEFAULT_GRID_SETTINGS = {
  terminal: {
    cols: 40,
    rows: 24,
    cellSize: 24,
    glowColor: "green" as const,
    showScanlines: false,
  },
  teledesk: {
    cols: 40,
    rows: 24,
    cellSize: 24,
    glowColor: "cyan" as const,
    showScanlines: true,
  },
  pixelEditor: {
    cols: 24,
    rows: 24,
    cellSize: 24,
    showGrid: true,
  },
};

// ============================================================================
// CHARACTER CENTERING UTILITIES
// ============================================================================

/**
 * Bounds of rendered ink (non-whitespace pixels)
 */
export interface InkBounds {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
  width: number;
  height: number;
  centerX: number;
  centerY: number;
  hasPixels: boolean;
}

/**
 * Character placement offset for centering
 */
export interface CenteringOffset {
  x: number;
  y: number;
  // For debugging/display
  inkBounds: InkBounds;
}

/**
 * Calculate ink bounds from a boolean pixel grid
 * Returns the bounding box of all "on" pixels
 */
export function calculateInkBounds(pixels: boolean[][]): InkBounds {
  const height = pixels.length;
  const width = height > 0 ? pixels[0].length : 0;

  let minX = width;
  let maxX = 0;
  let minY = height;
  let maxY = 0;
  let hasPixels = false;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (pixels[y][x]) {
        hasPixels = true;
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
      }
    }
  }

  if (!hasPixels) {
    return {
      minX: 0,
      maxX: 0,
      minY: 0,
      maxY: 0,
      width: 0,
      height: 0,
      centerX: width / 2,
      centerY: height / 2,
      hasPixels: false,
    };
  }

  const inkWidth = maxX - minX + 1;
  const inkHeight = maxY - minY + 1;

  return {
    minX,
    maxX,
    minY,
    maxY,
    width: inkWidth,
    height: inkHeight,
    centerX: minX + inkWidth / 2,
    centerY: minY + inkHeight / 2,
    hasPixels: true,
  };
}

/**
 * Calculate offset needed to center a character within a tile
 *
 * Algorithm:
 * 1. Find the ink bounds (actual drawn pixels)
 * 2. Calculate ink center
 * 3. Calculate tile center
 * 4. Return offset that moves ink center to tile center
 * 5. Round to whole pixels for crisp rendering
 *
 * @param inkBounds - Pre-calculated ink bounds
 * @param tileSize - Size of the target tile (e.g., 24)
 * @returns Offset to apply when rendering
 */
export function calculateCenteringOffset(
  inkBounds: InkBounds,
  tileSize: number
): CenteringOffset {
  if (!inkBounds.hasPixels) {
    return { x: 0, y: 0, inkBounds };
  }

  const tileCenter = tileSize / 2;

  // Calculate how far off-center the ink currently is
  const xDelta = tileCenter - inkBounds.centerX;
  const yDelta = tileCenter - inkBounds.centerY;

  // Round to nearest whole pixel for crisp rendering
  // Use Math.round for symmetric rounding (not floor/ceil)
  const x = Math.round(xDelta);
  const y = Math.round(yDelta);

  return { x, y, inkBounds };
}

/**
 * Apply centering offset to shift pixels within a grid
 * Creates a new pixel array with the character centered
 *
 * @param pixels - Original pixel data
 * @param offset - Centering offset to apply
 * @returns New pixel array with character centered
 */
export function applyCharacterCentering(
  pixels: boolean[][],
  offset: CenteringOffset
): boolean[][] {
  const height = pixels.length;
  const width = height > 0 ? pixels[0].length : 0;

  // Create new grid
  const centered: boolean[][] = Array(height)
    .fill(null)
    .map(() => Array(width).fill(false));

  // Copy pixels with offset
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (pixels[y][x]) {
        const newX = x + offset.x;
        const newY = y + offset.y;

        // Only set if within bounds
        if (newX >= 0 && newX < width && newY >= 0 && newY < height) {
          centered[newY][newX] = true;
        }
      }
    }
  }

  return centered;
}

/**
 * Center a character within a tile in one step
 * Combines bounds calculation, offset calculation, and pixel shifting
 */
export function centerCharacterInTile(
  pixels: boolean[][],
  tileSize?: number
): boolean[][] {
  const size = tileSize || pixels.length;
  const bounds = calculateInkBounds(pixels);
  const offset = calculateCenteringOffset(bounds, size);
  return applyCharacterCentering(pixels, offset);
}

/**
 * Check if a character has minimum margin on all sides
 * Useful for validating that centering worked properly
 */
export function hasMinimumMargin(
  pixels: boolean[][],
  minMargin: number = 1
): {
  valid: boolean;
  margins: { top: number; bottom: number; left: number; right: number };
} {
  const bounds = calculateInkBounds(pixels);

  if (!bounds.hasPixels) {
    return { valid: true, margins: { top: 0, bottom: 0, left: 0, right: 0 } };
  }

  const height = pixels.length;
  const width = height > 0 ? pixels[0].length : 0;

  const margins = {
    top: bounds.minY,
    bottom: height - 1 - bounds.maxY,
    left: bounds.minX,
    right: width - 1 - bounds.maxX,
  };

  const valid =
    margins.top >= minMargin &&
    margins.bottom >= minMargin &&
    margins.left >= minMargin &&
    margins.right >= minMargin;

  return { valid, margins };
}
