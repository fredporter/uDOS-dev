// @ts-nocheck
/**
 * Font Loader Utility
 * Loads TTF/OTF fonts and extracts character bitmap data for editing
 *
 * Centering Algorithm:
 * 1. Render character at high resolution (4x) for accurate measurement
 * 2. Find actual ink bounds (ignoring whitespace)
 * 3. Calculate center of ink area
 * 4. Place so ink center aligns with tile center
 * 5. Round to whole pixels for crisp rendering
 * 6. Ensure minimum 1px margin when possible
 */

import { renderEmojiToPixelGrid, isEmojiUnicode } from "./emojiRenderer";

export interface CharacterData {
  code: number;
  char: string;
  pixels: boolean[][] | (number | null)[][]; // boolean for mono, palette indices for color
  width: number;
  height: number;
  color?: string;
  asciiMapping?: string; // ASCII fallback representation
  isColor?: boolean; // Flag to indicate if pixels contain color palette indices
}

/**
 * Load a font file and extract character data
 * @param fontPath - Path to the font file (TTF or OTF)
 * @param gridSize - Size of the pixel grid (24 or 48)
 * @param codes - Optional array of character codes to load (defaults to ASCII 32-126)
 * @param noMargin - If true, characters fill entire grid (for block graphics). Default false.
 * @returns Array of character data with square pixel grids
 */
export interface LoadFontResult {
  characters: CharacterData[];
  fontName: string;
}

// Check if font needs vertical offset adjustment
// Teletext50 renders characters too high, need to shift down
// PressStart2P also renders too high
function getFontVerticalOffset(fontPath: string, gridSize: number): number {
  const pathLower = fontPath.toLowerCase();
  if (pathLower.includes("teletext50")) {
    // Move down by 1 pixel in target resolution
    // At 4x hi-res, this is 4 pixels
    return gridSize === 24 ? 1 : 2; // 1px for 24x24, 2px for 48x48
  }
  if (pathLower.includes("pressstart") || pathLower.includes("press-start")) {
    // PressStart2P needs slight downward adjustment
    return gridSize === 24 ? 2 : 3; // 2px for 24x24, 3px for 48x48
  }
  return 0;
}

// Check if a character code is an emoji
function isEmojiCode(code: number): boolean {
  const char = String.fromCodePoint(code);
  return isEmojiUnicode(char);
}

export async function loadFont(
  fontPath: string,
  gridSize: number = 24,
  codes?: number[],
  noMargin: boolean = false
): Promise<LoadFontResult> {
  try {
    // In Tauri v2, paths starting with / are served from the app's root directory
    // No conversion needed - SvelteKit adapter-static puts everything in build/
    // and Tauri serves it directly
    const finalPath = fontPath;

    // Load the font file
    console.log(`[FontLoader] Fetching font from: ${finalPath}`);
    const response = await fetch(finalPath);
    if (!response.ok) {
      const errorMsg = `Failed to load font from ${finalPath}: ${response.status} ${response.statusText}`;
      console.error(`[FontLoader] ${errorMsg}`);
      throw new Error(errorMsg);
    }

    const arrayBuffer = await response.arrayBuffer();
    console.log(`[FontLoader] Font loaded: ${arrayBuffer.byteLength} bytes`);

    // Create a font face to render characters
    const fontName = `LoadedFont_${Date.now()}`;
    const isEmojiFont = fontPath.toLowerCase().includes("emoji");

    // For emoji fonts, extract glyphs as SVG and process through SVG processor
    if (isEmojiFont && codes && codes.length > 0) {
      console.log(
        `[FontLoader] Emoji font detected, using SVG extraction pipeline`
      );
      try {
        const { extractGlyphsFromFont } = await import("./fontToSvg");
        const { svgToPixelGrid } = await import("./svgParser");

        const glyphSvgs = await extractGlyphsFromFont(
          fontPath,
          Array.from(codes)
        );
        const characters: CharacterData[] = [];

        for (const glyphSvg of glyphSvgs) {
          try {
            // Process SVG through the SVG processor (preserves color palette)
            const pixelGrid = await svgToPixelGrid(
              glyphSvg.svg,
              gridSize,
              gridSize
            );

            characters.push({
              char: glyphSvg.char,
              code: glyphSvg.unicode,
              pixels: pixelGrid, // Keep color palette indices
              width: gridSize,
              height: gridSize,
              isColor: true, // Mark as color data
            });

            console.log(
              `[FontLoader] Processed emoji ${glyphSvg.char} through SVG pipeline with colors`
            );
          } catch (svgError) {
            console.warn(
              `[FontLoader] Failed to process SVG for ${glyphSvg.char}:`,
              svgError
            );
          }
        }

        console.log(
          `[FontLoader] Generated ${characters.length} emoji characters via SVG extraction`
        );

        // Show user-friendly toast notification
        if (characters.length > 0) {
          const { toastStore } = await import("../stores/toastStore");
          toastStore.success(
            `Loaded ${characters.length} emoji characters from ${fontPath.split("/").pop()}`,
            3000
          );
        }

        return {
          characters,
          fontName: "Emoji SVG Processed",
          originalCodes: Array.from(codes),
        };
      } catch (emojiError: any) {
        console.warn(
          `[FontLoader] SVG extraction failed, falling back:`,
          emojiError
        );

        // For CBDT color emoji, try system emoji renderer
        const { toastStore } = await import("../stores/toastStore");
        if (emojiError.message?.includes("CBDT bitmap")) {
          console.log(
            `[FontLoader] CBDT color emoji detected, using system emoji renderer`
          );
          try {
            const { renderEmojiToPixelGrid } = await import("./emojiRenderer");
            const characters: CharacterData[] = [];

            for (const code of codes) {
              const char = String.fromCodePoint(code);
              try {
                const result = await renderEmojiToPixelGrid(char, gridSize);
                characters.push({
                  char,
                  code,
                  pixels: result.pixels, // Now contains color palette indices
                  width: gridSize,
                  height: gridSize,
                  isColor: result.source === "svg", // SVG source has color data
                });
                console.log(
                  `[FontLoader] Rendered color emoji ${char} via system renderer`
                );
              } catch (renderError) {
                console.warn(
                  `[FontLoader] Failed to render ${char}:`,
                  renderError
                );
              }
            }

            if (characters.length > 0) {
              toastStore.success(
                `Loaded ${characters.length} color emoji via system renderer`,
                3000
              );
              return {
                characters,
                fontName: "System Color Emoji",
                originalCodes: Array.from(codes),
              };
            }
          } catch (rendererError) {
            console.warn(
              `[FontLoader] System emoji renderer failed:`,
              rendererError
            );
          }
        }

        // Show error for other failures
        if (emojiError.message?.includes("Unsupported OpenType")) {
          toastStore.error(
            `Font format not supported. Try downloading uncompressed TTF version.`,
            5000
          );
        } else if (!emojiError.message?.includes("CBDT bitmap")) {
          toastStore.error(
            `Failed to extract emoji: ${emojiError.message}`,
            5000
          );
        }

        // Fall through to regular font loading
      }
    }

    try {
      const fontFace = new FontFace(fontName, arrayBuffer);
      await fontFace.load();
      document.fonts.add(fontFace);
      console.log(`[FontLoader] Font face loaded and added: ${fontName}`);
    } catch (fontError) {
      console.warn(
        `[FontLoader] Failed to load ${fontPath} as FontFace:`,
        fontError
      );

      // For emoji fonts, fall back to using system emoji fonts
      if (isEmojiFont) {
        console.log(`[FontLoader] Using system emoji fonts as fallback`);
        // Return empty result - CharacterLibrary will use emoji fallback rendering
        return {
          characters: [],
          fontName: "System Emoji Fonts",
          originalCodes: codes ? Array.from(codes) : [],
        };
      }
      throw fontError;
    }

    // Wait for font to be fully loaded
    await document.fonts.ready;
    await new Promise((resolve) => setTimeout(resolve, 150));

    // Use provided codes or default to ASCII printable characters (32-126)
    // Be tolerant of proxied arrays: rely on length if present
    const codesProvided =
      codes &&
      typeof (codes as any).length === "number" &&
      (codes as any).length > 0
        ? Array.from(codes as number[])
        : undefined;
    console.log(
      `[FontLoader] codes provided? ${codesProvided ? "yes" : "no"}, length=${codesProvided?.length}, isEmojiFont=${isEmojiFont}`
    );

    if (isEmojiFont && (!codesProvided || codesProvided.length === 0)) {
      throw new Error(
        `Emoji font requested but no character codes were supplied; refusing ASCII fallback for ${fontPath}`
      );
    }

    const codesToLoad =
      codesProvided && codesProvided.length > 0
        ? codesProvided
        : Array.from({ length: 95 }, (_, i) => i + 32);

    // Calculate margins and usable area
    // 24×24 mode: 1px margin all around = 22×22 usable
    // 48×48 mode: 2px margin all around = 44×44 usable
    // Block graphics: 0px margin = full grid
    const margin = noMargin ? 0 : gridSize === 24 ? 1 : 2;
    const usableSize = gridSize - margin * 2;

    // Measure largest capital letter to determine scaling
    const maxFontSize = await findOptimalFontSize(fontName, usableSize);

    console.log(
      `[FontLoader] Loading ${fontPath}: codes=${codesToLoad.length}, gridSize=${gridSize}, margin=${margin}, usableSize=${usableSize}, maxFontSize=${maxFontSize}`
    );

    // Generate character data
    const characters: CharacterData[] = [];

    // Get font-specific vertical offset
    const verticalOffset = getFontVerticalOffset(fontPath, gridSize);
    console.log(`[FontLoader] Vertical offset: ${verticalOffset}`);

    for (const code of codesToLoad) {
      const char = String.fromCodePoint(code);
      const isEmoji = isEmojiCode(code);

      let pixels: boolean[][];

      if (isEmoji) {
        // Use new emoji renderer instead of creating empty arrays
        console.log(
          `[FontLoader] Rendering emoji ${char} (U+${code.toString(16)}) with emoji renderer`
        );
        try {
          // Render emoji without timeout - let it take as long as needed
          const result = await renderEmojiToPixelGrid(char, gridSize);
          pixels = result.pixels;
          console.log(
            `[FontLoader] Emoji rendered successfully via ${result.source}`
          );
        } catch (error) {
          console.warn(
            `[FontLoader] Emoji rendering failed/timeout for ${char}, using test pattern:`,
            error
          );
          // Create a simple test pattern instead of empty grid
          pixels = Array(gridSize)
            .fill(null)
            .map((_, y) =>
              Array(gridSize)
                .fill(false)
                .map((_, x) => {
                  // Create a simple emoji placeholder pattern
                  const centerX = gridSize / 2;
                  const centerY = gridSize / 2;
                  const dist = Math.sqrt(
                    Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2)
                  );
                  const radius = gridSize / 3;
                  return dist < radius && dist > radius - 2;
                })
            );
        }
      } else {
        const renderResult = await renderCharacterToPixels(
          char,
          fontName,
          gridSize,
          maxFontSize,
          margin,
          false,
          verticalOffset
        );
        pixels = renderResult.pixels;
      }

      characters.push({
        code,
        char,
        pixels,
        width: gridSize,
        height: gridSize,
      });
    }

    console.log(
      `[FontLoader] Generated ${characters.length} characters from ${codesToLoad.length} codes`
    );
    return { characters, fontName };
  } catch (error) {
    console.error("Error loading font:", error);
    throw error;
  }
}

/**
 * Find the optimal font size by measuring the largest capital letter
 * @param fontFamily - Font family name
 * @param usableSize - Maximum size available (grid size minus margins)
 * @returns Optimal font size in pixels
 */
async function findOptimalFontSize(
  fontFamily: string,
  usableSize: number
): Promise<number> {
  const canvas = document.createElement("canvas");
  canvas.width = 200;
  canvas.height = 200;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });

  if (!ctx) {
    throw new Error("Could not get canvas context");
  }

  // Test capital letters that are typically the widest/tallest
  const testChars = ["W", "M", "Q", "H", "A", "B"];

  // Binary search for the optimal font size
  let low = usableSize * 0.5;
  let high = usableSize * 1.5;
  let bestSize = usableSize;

  // Test to find the largest size where the biggest character fits
  for (let iteration = 0; iteration < 20; iteration++) {
    const testSize = (low + high) / 2;
    ctx.font = `${testSize}px "${fontFamily}"`;

    let maxRenderedHeight = 0;
    let maxRenderedWidth = 0;

    // Render each test character and measure actual pixel bounds
    for (const char of testChars) {
      ctx.clearRect(0, 0, 200, 200);
      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(0, 0, 200, 200);
      ctx.fillStyle = "#000000";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(char, 100, 100);

      // Measure actual rendered bounds
      const imageData = ctx.getImageData(0, 0, 200, 200);
      let minY = 200,
        maxY = 0,
        minX = 200,
        maxX = 0;
      let hasPixels = false;

      for (let y = 0; y < 200; y++) {
        for (let x = 0; x < 200; x++) {
          const index = (y * 200 + x) * 4;
          const r = imageData.data[index];
          const g = imageData.data[index + 1];
          const b = imageData.data[index + 2];
          const alpha = imageData.data[index + 3];

          if ((r + g + b) / 3 < 200 && alpha > 50) {
            hasPixels = true;
            minY = Math.min(minY, y);
            maxY = Math.max(maxY, y);
            minX = Math.min(minX, x);
            maxX = Math.max(maxX, x);
          }
        }
      }

      if (hasPixels) {
        const height = maxY - minY + 1;
        const width = maxX - minX + 1;
        maxRenderedHeight = Math.max(maxRenderedHeight, height);
        maxRenderedWidth = Math.max(maxRenderedWidth, width);
      }
    }

    // Check if this size fits within usable area
    const maxDimension = Math.max(maxRenderedHeight, maxRenderedWidth);

    if (maxDimension <= usableSize) {
      // This size fits, try larger
      bestSize = testSize;
      low = testSize;
    } else {
      // Too big, try smaller
      high = testSize;
    }

    // If we've converged, stop
    if (high - low < 0.5) {
      break;
    }
  }

  return bestSize;
}

/**
 * Render a character to a square pixel grid with perfect center alignment
 *
 * Algorithm for pixel-perfect centering:
 * 1. Render at 4x resolution for accurate ink detection
 * 2. Find exact ink bounds (first/last non-white pixels)
 * 3. Calculate ink center point
 * 4. Compute offset to align ink center with tile center
 * 5. Round offset to whole pixels to avoid subpixel blur
 * 6. Re-render with calculated offset
 * 7. Downsample to target resolution
 *
 * @param char - Character to render
 * @param fontFamily - Font family name
 * @param size - Grid size (24 or 48)
 * @param fontSize - Optimal font size calculated based on largest character
 * @param margin - Margin in pixels (1 for 24×24, 2 for 48×48)
 * @returns Object with boolean pixels array
 */
interface RenderResult {
  pixels: boolean[][];
}

async function renderCharacterToPixels(
  char: string,
  fontFamily: string,
  size: number,
  fontSize: number,
  margin: number,
  _isEmojiChar: boolean = false,
  fontVerticalOffset: number = 0
): Promise<RenderResult> {
  // Use higher resolution for accurate measurement (4x supersampling)
  const scale = 4;
  const hiResSize = size * scale;
  const hiFontSize = fontSize * scale;

  const canvas = document.createElement("canvas");
  canvas.width = hiResSize;
  canvas.height = hiResSize;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });

  if (!ctx) {
    throw new Error("Could not get canvas context");
  }

  const fontString = `${hiFontSize}px "${fontFamily}"`;

  // Clear canvas with white background
  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(0, 0, hiResSize, hiResSize);

  // Render character at center for measurement
  ctx.font = fontString;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillStyle = "#000000";
  ctx.fillText(char, hiResSize / 2, hiResSize / 2);

  // Get the actual rendered pixel bounds
  const imageData = ctx.getImageData(0, 0, hiResSize, hiResSize);
  let minY = hiResSize;
  let maxY = 0;
  let minX = hiResSize;
  let maxX = 0;
  let hasPixels = false;

  // Find ink bounds
  for (let y = 0; y < hiResSize; y++) {
    for (let x = 0; x < hiResSize; x++) {
      const index = (y * hiResSize + x) * 4;
      const r = imageData.data[index];
      const g = imageData.data[index + 1];
      const b = imageData.data[index + 2];
      const alpha = imageData.data[index + 3];

      // Check for any non-white pixels (handles antialiasing and color)
      const isInk = (r + g + b) / 3 < 250 || alpha < 255;

      if (isInk && alpha > 10) {
        hasPixels = true;
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
      }
    }
  }

  // If no pixels found, return empty grid
  if (!hasPixels) {
    return {
      pixels: Array(size)
        .fill(null)
        .map(() => Array(size).fill(false)),
      isColorChar: false,
    };
  }

  // Calculate ink dimensions and center
  const inkWidth = maxX - minX + 1;
  const inkHeight = maxY - minY + 1;
  const inkCenterX = minX + inkWidth / 2;
  const inkCenterY = minY + inkHeight / 2;

  // Target center of the tile (in hi-res coordinates)
  const tileCenterX = hiResSize / 2;
  const tileCenterY = hiResSize / 2;

  // For noMargin (block graphics), don't center - render edge-to-edge
  // For regular characters, center within the margin-bounded area
  let xOffsetHiRes, yOffsetHiRes;

  if (margin === 0) {
    // Block graphics: no centering offset, render as-is
    xOffsetHiRes = 0;
    yOffsetHiRes = 0;
  } else {
    // Regular characters: center within usable area, respect margins
    // Calculate offset to move ink center to tile center
    // Round to whole scale units for pixel-perfect alignment
    xOffsetHiRes = Math.round((tileCenterX - inkCenterX) / scale) * scale;
    yOffsetHiRes = Math.round((tileCenterY - inkCenterY) / scale) * scale;

    // Apply font-specific vertical offset (e.g., Teletext50 adjustment)
    // Scale offset to hi-res (4x)
    yOffsetHiRes += fontVerticalOffset * scale;
  }

  // Clear and re-render with proper centering
  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(0, 0, hiResSize, hiResSize);
  ctx.font = fontString;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  // For color emoji: don't set fillStyle, let emoji render with natural colors
  // For mono: use black
  if (!_isEmojiChar) {
    ctx.fillStyle = "#000000";
  }
  ctx.fillText(
    char,
    hiResSize / 2 + xOffsetHiRes,
    hiResSize / 2 + yOffsetHiRes
  );

  // Get final hi-res image
  const finalImageData = ctx.getImageData(0, 0, hiResSize, hiResSize);

  // Downsample to target resolution using area averaging
  const pixels: boolean[][] = Array(size)
    .fill(null)
    .map(() => Array(size).fill(false));

  const threshold = 8;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      // Sample the 4x4 block
      let colorCount = 0;

      for (let dy = 0; dy < scale; dy++) {
        for (let dx = 0; dx < scale; dx++) {
          const hiX = x * scale + dx;
          const hiY = y * scale + dy;
          const index = (hiY * hiResSize + hiX) * 4;
          const r = finalImageData.data[index];
          const g = finalImageData.data[index + 1];
          const b = finalImageData.data[index + 2];
          const alpha = finalImageData.data[index + 3];

          // Check darkness
          if ((r + g + b) / 3 < 200 && alpha > 50) {
            colorCount++;
          }
        }
      }

      // Pixel is "on" if enough of the hi-res block has color/ink
      pixels[y][x] = colorCount >= threshold;
    }
  }

  return { pixels };
}

/**
 * Load an icon set and convert to character data
 * @param iconPath - Path to icon font or directory
 * @param isColor - Whether icons are color or monochrome
 * @returns Array of character data
 */
export async function loadIconSet(
  iconPath: string,
  isColor: boolean = false
): Promise<CharacterData[]> {
  // Use the same loading mechanism as fonts
  const result = await loadFont(iconPath);
  return result.characters;
}

/**
 * Create a blank character template
 * @param code - ASCII code
 * @returns Empty character data
 */
export function createBlankCharacter(code: number): CharacterData {
  return {
    code,
    char: String.fromCodePoint(code),
    pixels: Array(24)
      .fill(null)
      .map(() => Array(24).fill(false)),
    width: 24,
    height: 24,
  };
}

/**
 * Get block graphics characters (ASCII 176-223)
 * These are commonly used for drawing boxes and patterns
 */
export function getBlockGraphicsCharacters(): number[] {
  return Array.from({ length: 48 }, (_, i) => i + 176);
}

/**
 * Duplicate a character to a new ASCII code
 */
export function duplicateCharacter(
  char: CharacterData,
  newCode: number
): CharacterData {
  return {
    ...char,
    code: newCode,
    char: String.fromCodePoint(newCode),
    pixels: char.pixels.map((row) => [...row]),
  };
}
