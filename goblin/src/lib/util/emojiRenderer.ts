/**
 * Emoji Renderer - Convert emoji unicode to pixel grids
 *
 * Since Canvas 2D cannot capture color emoji pixels, we use alternative approaches:
 * 1. Fetch pre-rendered SVGs from Noto Emoji (primary)
 * 2. DOM-based rendering fallback (secondary)
 * 3. System emoji fallback (tertiary)
 */

export interface EmojiRenderResult {
  pixels: boolean[][] | (number | null)[][]; // boolean for fallback, palette indices for SVG
  colorMap?: (number | null)[][]; // Deprecated: use pixels directly now
  source: "svg" | "dom" | "fallback";
}

/**
 * Main function to render emoji to pixel grid
 */
export async function renderEmojiToPixelGrid(
  unicode: string,
  gridSize: number = 24
): Promise<EmojiRenderResult> {
  console.log(
    `[EmojiRenderer] Starting render for ${unicode} at ${gridSize}x${gridSize}`
  );

  // Try SVG rendering first (best quality)
  try {
    console.log(`[EmojiRenderer] Attempting SVG render for ${unicode}`);
    return await renderEmojiFromSVG(unicode, gridSize);
  } catch (svgError) {
    console.warn(`[EmojiRenderer] SVG render failed:`, svgError);
  }

  // Fallback to DOM rendering
  try {
    console.log(`[EmojiRenderer] Attempting DOM render for ${unicode}`);
    return await renderEmojiFromDOM(unicode, gridSize);
  } catch (domError) {
    console.warn(`[EmojiRenderer] DOM render failed:`, domError);
  }

  // Last resort: test pattern
  console.log(`[EmojiRenderer] Using test pattern fallback for ${unicode}`);
  return createTestPattern(unicode, gridSize);
}

/**
 * Render emoji from SVG (preferred method)
 */
async function renderEmojiFromSVG(
  unicode: string,
  gridSize: number
): Promise<EmojiRenderResult> {
  // Import svgParser's svgToPixelGrid which returns color palette indices
  const { svgToPixelGrid } = await import("./svgParser");
  const svg = await fetchNotoEmojiSVG(unicode);
  const pixels = await svgToPixelGrid(svg, gridSize, gridSize);

  console.log(`[EmojiRenderer] SVG rendered with color palette for ${unicode}`);

  return {
    pixels, // Already color-mapped palette indices
    source: "svg",
  };
}

/**
 * Fetch Noto Emoji SVG from GitHub CDN with caching
 */
async function fetchNotoEmojiSVG(unicode: string): Promise<string> {
  // Convert unicode to hex codepoint
  const codepoint = unicode.codePointAt(0);
  if (!codepoint) {
    throw new Error(`Invalid unicode: ${unicode}`);
  }

  const hex = codepoint.toString(16).toLowerCase().padStart(4, "0");

  // Check cache first
  const cacheKey = `emoji-svg-${hex}`;
  const cached = localStorage.getItem(cacheKey);
  if (cached) {
    console.log(`[EmojiRenderer] Using cached SVG for U+${hex.toUpperCase()}`);
    return cached;
  }

  // Fetch from Noto Emoji GitHub
  const url = `https://raw.githubusercontent.com/googlefonts/noto-emoji/main/svg/emoji_u${hex}.svg`;
  console.log(`[EmojiRenderer] Fetching SVG: ${url}`);

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(
      `Failed to fetch emoji SVG: ${response.status} ${response.statusText}`
    );
  }

  const svg = await response.text();

  // Cache for future use
  try {
    localStorage.setItem(cacheKey, svg);
  } catch (e) {
    console.warn("[EmojiRenderer] Failed to cache SVG:", e);
  }

  return svg;
}

/**
 * Convert SVG to pixel grid
 */
async function svgToPixelGrid(
  svg: string,
  gridSize: number
): Promise<boolean[][]> {
  // Create offscreen canvas
  const canvas = document.createElement("canvas");
  canvas.width = gridSize * 4; // 4x supersampling
  canvas.height = gridSize * 4;
  const ctx = canvas.getContext("2d");

  if (!ctx) {
    throw new Error("Could not get canvas context");
  }

  // Create SVG blob and image
  const blob = new Blob([svg], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);

  try {
    const img = new Image();
    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = reject;
      img.src = url;
    });

    // Clear canvas with white background
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw SVG to canvas
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // Convert to pixel grid with downsampling
    return canvasToPixelGrid(ctx, gridSize);
  } finally {
    URL.revokeObjectURL(url);
  }
}

/**
 * Fallback: Render emoji using DOM and system fonts
 */
async function renderEmojiFromDOM(
  unicode: string,
  gridSize: number
): Promise<EmojiRenderResult> {
  // Create temporary DOM element
  const div = document.createElement("div");
  div.style.position = "absolute";
  div.style.left = "-9999px";
  div.style.fontSize = `${gridSize * 2}px`;
  div.style.fontFamily =
    '"Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji"';
  div.style.width = `${gridSize * 4}px`;
  div.style.height = `${gridSize * 4}px`;
  div.style.display = "flex";
  div.style.alignItems = "center";
  div.style.justifyContent = "center";
  div.style.background = "white";
  div.textContent = unicode;

  document.body.appendChild(div);

  try {
    // Use html2canvas or similar technique
    // For now, use a simpler canvas-based approach
    const canvas = document.createElement("canvas");
    canvas.width = gridSize * 4;
    canvas.height = gridSize * 4;
    const ctx = canvas.getContext("2d");

    if (!ctx) {
      throw new Error("Could not get canvas context");
    }

    // Clear background
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw text (will be monochrome but better than nothing)
    ctx.fillStyle = "#000000";
    ctx.font = `${gridSize * 2}px "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji"`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(unicode, canvas.width / 2, canvas.height / 2);

    const pixels = canvasToPixelGrid(ctx, gridSize);

    return {
      pixels,
      source: "dom",
    };
  } finally {
    document.body.removeChild(div);
  }
}

/**
 * Convert canvas ImageData to boolean pixel grid with downsampling
 */
function canvasToPixelGrid(
  ctx: CanvasRenderingContext2D,
  targetSize: number
): boolean[][] {
  const canvas = ctx.canvas;
  const sourceSize = canvas.width; // Should be targetSize * 4
  const scale = Math.floor(sourceSize / targetSize);

  const imageData = ctx.getImageData(0, 0, sourceSize, sourceSize);
  const data = imageData.data;

  const pixels: boolean[][] = Array(targetSize)
    .fill(null)
    .map(() => Array(targetSize).fill(false));

  // Downsample with threshold
  for (let y = 0; y < targetSize; y++) {
    for (let x = 0; x < targetSize; x++) {
      let colorCount = 0;
      let totalSamples = 0;

      // Sample the scale×scale block
      for (let dy = 0; dy < scale; dy++) {
        for (let dx = 0; dx < scale; dx++) {
          const sourceX = x * scale + dx;
          const sourceY = y * scale + dy;

          if (sourceX < sourceSize && sourceY < sourceSize) {
            const index = (sourceY * sourceSize + sourceX) * 4;
            const r = data[index];
            const g = data[index + 1];
            const b = data[index + 2];
            const alpha = data[index + 3];

            totalSamples++;

            // Check if pixel has color (not white/transparent)
            const brightness = (r + g + b) / 3;
            if (brightness < 240 && alpha > 50) {
              colorCount++;
            }
          }
        }
      }

      // Pixel is "on" if enough samples have color
      const threshold = Math.max(1, Math.floor(totalSamples * 0.3));
      pixels[y][x] = colorCount >= threshold;
    }
  }

  return pixels;
}

/**
 * Utility: Check if a character is an emoji
 */
export function isEmojiUnicode(unicode: string): boolean {
  const code = unicode.codePointAt(0);
  if (!code) return false;

  return (
    code >= 0x1f300 || // Misc symbols and pictographs, emoticons, etc.
    (code >= 0x2600 && code <= 0x26ff) || // Misc symbols
    (code >= 0x2700 && code <= 0x27bf) || // Dingbats
    (code >= 0x231a && code <= 0x23f3) || // Watch, hourglass, etc.
    (code >= 0x2300 && code <= 0x23ff) || // Misc Technical
    (code >= 0x2b50 && code <= 0x2b55) // Stars and circles
  );
}

/**
 * Batch render multiple emoji (for performance)
 */
export async function renderMultipleEmoji(
  unicodes: string[],
  gridSize: number = 24,
  onProgress?: (completed: number, total: number) => void
): Promise<Map<string, EmojiRenderResult>> {
  const results = new Map<string, EmojiRenderResult>();

  for (let i = 0; i < unicodes.length; i++) {
    const unicode = unicodes[i];
    try {
      const result = await renderEmojiToPixelGrid(unicode, gridSize);
      results.set(unicode, result);
    } catch (error) {
      console.error(`[EmojiRenderer] Failed to render ${unicode}:`, error);
      // Store fallback result
      results.set(unicode, {
        pixels: Array(gridSize)
          .fill(null)
          .map(() => Array(gridSize).fill(false)),
        source: "fallback",
      });
    }

    if (onProgress) {
      onProgress(i + 1, unicodes.length);
    }
  }

  return results;
}

/**
 * Create a test pattern for emoji (for debugging/fallback)
 */
function createTestPattern(
  unicode: string,
  gridSize: number
): EmojiRenderResult {
  const pixels: boolean[][] = Array(gridSize)
    .fill(null)
    .map(() => Array(gridSize).fill(false));

  // Create a simple pattern based on unicode codepoint
  const codepoint = unicode.codePointAt(0) || 0;
  const pattern = codepoint % 4;

  console.log(
    `[EmojiRenderer] Creating pattern ${pattern} for ${unicode} (U+${codepoint.toString(16)})`
  );

  // Different patterns for different emoji - make them more visible
  switch (pattern) {
    case 0: // Diagonal line
      for (let i = 0; i < gridSize; i++) {
        if (i < gridSize) {
          pixels[i][i] = true;
          if (i > 0) pixels[i][i - 1] = true; // Make thicker
        }
      }
      break;
    case 1: // Border
      for (let i = 0; i < gridSize; i++) {
        pixels[0][i] = true;
        pixels[1][i] = true; // Make thicker
        pixels[gridSize - 1][i] = true;
        pixels[gridSize - 2][i] = true; // Make thicker
        pixels[i][0] = true;
        pixels[i][1] = true; // Make thicker
        pixels[i][gridSize - 1] = true;
        pixels[i][gridSize - 2] = true; // Make thicker
      }
      break;
    case 2: // Cross
      const center = Math.floor(gridSize / 2);
      for (let i = 0; i < gridSize; i++) {
        pixels[center][i] = true;
        pixels[center - 1][i] = true; // Make thicker
        pixels[center + 1][i] = true; // Make thicker
        pixels[i][center] = true;
        pixels[i][center - 1] = true; // Make thicker
        pixels[i][center + 1] = true; // Make thicker
      }
      break;
    case 3: // Checkerboard
      for (let i = 0; i < gridSize; i += 3) {
        for (let j = 0; j < gridSize; j += 3) {
          pixels[i][j] = true;
          if (i + 1 < gridSize) pixels[i + 1][j] = true;
          if (j + 1 < gridSize) pixels[i][j + 1] = true;
        }
      }
      break;
  }

  // Count pixels for verification
  const pixelCount = pixels.flat().filter(Boolean).length;
  console.log(
    `[EmojiRenderer] Created test pattern ${pattern} for ${unicode}, pixels: ${pixelCount}/${gridSize * gridSize}`
  );

  return {
    pixels,
    source: "fallback",
  };
}
