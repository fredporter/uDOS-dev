<script lang="ts">
  import { getAllColors } from "$lib/util/udosPalette";
  import { onMount } from "svelte";

  type Props = {
    pixels: boolean[][] | (number | null)[][];
    color?: string;
    onChange: (pixels: boolean[][] | (number | null)[][]) => void;
  };

  let { pixels = $bindable(), color = "#000000", onChange }: Props = $props();

  // Dynamic grid size based on pixels array
  const gridSize = $derived(pixels.length);
  // Scale cell size for better space usage: 24→20px, 48→14px
  const cellSize = $derived(gridSize === 24 ? 20 : 14);

  let isDrawing = $state(false);
  let drawMode = $state<"set" | "clear">("set");

  // Track dark mode reactively
  let isDark = $state(false);
  onMount(() => {
    const update = () => {
      const next = document.documentElement.classList.contains("dark");
      if (next !== isDark) isDark = next;
    };
    update();
    const obs = new MutationObserver(update);
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => obs.disconnect();
  });

  // Get pixel color - supports both boolean and palette indices
  const getPixelColor = (row: number, col: number): string => {
    const pixel = pixels[row]?.[col];

    // Handle color palette index (number)
    if (typeof pixel === "number" && pixel !== null) {
      const palette = getAllColors();
      return palette[pixel]?.hex || "#000000";
    }

    // Handle boolean (mono) - use proper Tailwind light/dark colors
    if (pixel === true) {
      // Foreground: visible against background in both modes
      return isDark ? "#f3f4f6" : "#1f2937"; // dark:gray-100 light:gray-800
    }

    // Background color for false/null
    return isDark ? "#1f2937" : "#f3f4f6"; // dark:gray-800 light:gray-100
  };

  const togglePixel = (row: number, col: number) => {
    const newPixels = pixels.map((r) => [...r]);
    const currentPixel = newPixels[row][col];

    // For color palette data (number), toggle between null and existing color
    if (typeof currentPixel === "number") {
      newPixels[row][col] = null;
    } else if (currentPixel === null) {
      // If previously a color pixel, we'd need to know what color - for now use white (index 23)
      newPixels[row][col] = 23; // White from greyscale
    } else {
      // Boolean toggle
      newPixels[row][col] = !currentPixel;
    }

    pixels = newPixels as typeof pixels;
    onChange(newPixels as typeof pixels);
  };

  const handleMouseDown = (row: number, col: number, e: MouseEvent) => {
    e.preventDefault();
    isDrawing = true;
    const currentPixel = pixels[row][col];
    // Set draw mode based on current pixel state
    drawMode =
      currentPixel === null || currentPixel === false ? "set" : "clear";
    togglePixel(row, col);
  };

  const handleMouseEnter = (row: number, col: number) => {
    if (!isDrawing) return;

    const newPixels = pixels.map((r) => [...r]);
    const existingValue = pixels[0][0]; // Check type from first pixel

    // Match the type of the existing pixels
    if (typeof existingValue === "number" || existingValue === null) {
      // Color palette mode
      newPixels[row][col] = drawMode === "set" ? 23 : null; // White or transparent
    } else {
      // Boolean mode
      newPixels[row][col] = drawMode === "set";
    }

    pixels = newPixels as typeof pixels;
    onChange(newPixels as typeof pixels);
  };

  const handleMouseUp = () => {
    isDrawing = false;
  };

  const handleMouseLeave = () => {
    isDrawing = false;
  };
</script>

<svelte:window onmouseup={handleMouseUp} />

<div
  class="inline-block border-2 border-gray-500 rounded shadow-lg"
  role="application"
  aria-label="{gridSize}×{gridSize} pixel editor grid"
  onmouseleave={handleMouseLeave}
>
  <div
    class="grid gap-px p-1 bg-gray-300 dark:bg-gray-600"
    style="grid-template-columns: repeat({gridSize}, {cellSize}px); grid-template-rows: repeat({gridSize}, {cellSize}px);"
  >
    {#each Array(gridSize) as _, row}
      {#each Array(gridSize) as _, col}
        <button
          class="border border-gray-500 transition-colors cursor-crosshair hover:opacity-80"
          style="
            width: {cellSize}px;
            height: {cellSize}px;
            background-color: {getPixelColor(row, col)};
          "
          onmousedown={(e) => handleMouseDown(row, col, e)}
          onmouseenter={() => handleMouseEnter(row, col)}
          aria-label="Row {row + 1}, Column {col + 1}"
          tabindex="-1"
        ></button>
      {/each}
    {/each}
  </div>

  <!-- Grid info -->
  <div
    class="px-2 py-1 text-xs text-center border-t bg-gray-100 text-gray-600 border-gray-300 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600"
  >
    {gridSize}×{gridSize} Monosorts Grid • Click and drag to draw
  </div>
</div>

<style>
  button:active {
    transform: scale(0.95);
  }
</style>
