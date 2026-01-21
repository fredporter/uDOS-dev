<script lang="ts">
  /**
   * GridDisplay - Unified pixel-perfect grid renderer for uDOS
   *
   * Single source of truth for Terminal, Teledesk, and embedded grid displays.
   * Uses the gridSystem utilities for consistent 24x24 cell rendering.
   *
   * Features:
   * - True 24x24 pixel cell grid alignment
   * - Font-specific sizing via data-mono-variant
   * - CRT effects (scanlines, glow, curvature) - optional
   * - Independent of Tailwind - uses fixed pixel measurements
   * - Transportable - can be rendered in .udos.md code blocks
   *
   * @version 2.0.0
   */

  import type { Snippet } from "svelte";
  import { DEFAULT_GRID_SETTINGS, type GridConfig } from "$lib/util/gridSystem";
  import type { DemoLine } from "$lib/util/demoContent";

  interface Props {
    /** Grid preset name or custom config */
    preset?: "terminal" | "teledesk" | "pixelEditor";
    /** Override cols */
    cols?: number;
    /** Override rows */
    rows?: number;
    /** Cell size in pixels (default: 24) */
    cellSize?: number;
    /** Lines of text to render - can be strings or DemoLine objects */
    lines?: (string | DemoLine)[];
    /** Show CRT scanline overlay */
    showScanlines?: boolean;
    /** Show CRT phosphor glow */
    showGlow?: boolean;
    /** Glow color theme */
    glowColor?: "green" | "amber" | "cyan" | "white";
    /** Show CRT curvature vignette */
    showCurvature?: boolean;
    /** Additional CSS class */
    className?: string;
    /** Content slot for custom rendering */
    children?: Snippet;
  }

  let {
    preset = "terminal",
    cols,
    rows,
    cellSize,
    lines = [],
    showScanlines = true,
    showGlow = true,
    glowColor = "green",
    showCurvature = true,
    className = "",
    children,
  }: Props = $props();

  const hasChildren = $derived(children !== undefined);


  // Get preset config or use defaults
  const presetConfig = $derived(
    DEFAULT_GRID_SETTINGS[preset] || DEFAULT_GRID_SETTINGS.terminal
  );

  // Computed grid dimensions (props override preset)
  const gridCols = $derived(cols ?? presetConfig.cols);
  const gridRows = $derived(rows ?? presetConfig.rows);
  const gridCellSize = $derived(cellSize ?? presetConfig.cellSize);

  // Computed pixel dimensions
  const gridWidth = $derived(gridCols * gridCellSize);
  const gridHeight = $derived(gridRows * gridCellSize);

  // Glow color values (UDOS palette based)
  const glowColors = {
    green: "rgba(76, 154, 42, 0.15)", // UDOS Grass Green
    amber: "rgba(255, 190, 11, 0.15)", // UDOS Waypoint Yellow
    cyan: "rgba(0, 217, 255, 0.15)", // UDOS Objective Cyan
    white: "rgba(255, 255, 255, 0.1)", // White glow
  };

  // Helper to get font class from font type
  function getFontClass(fontType?: string): string {
    switch (fontType) {
      case "title":
        return "font-title";
      case "heading":
        return "font-heading";
      case "heading-double":
        return "font-heading-double";
      case "alt-heading":
        return "font-alt-heading";
      case "body":
      default:
        return "font-body";
    }
  }

  // Helper to extract text from line object
  function getLineText(line: string | DemoLine): string {
    return typeof line === "string" ? line : line.text;
  }

  // Helper to get font type from line object
  function getLineFont(line: string | DemoLine): string | undefined {
    return typeof line === "string" ? undefined : line.font;
  }

  // Helper to get color from line object
  function getLineColor(line: string | DemoLine): string | undefined {
    return typeof line === "string" ? undefined : line.color;
  }

  // Pad line to exact column width
  function padLine(line: string, targetCols: number): string {
    return line.padEnd(targetCols, " ").slice(0, targetCols);
  }
</script>

<div
  class="grid-display {className}"
  class:glow-effect={showGlow}
  style="
    --grid-cols: {gridCols};
    --grid-rows: {gridRows};
    --cell-size: {gridCellSize}px;
    --grid-width: {gridWidth}px;
    --grid-height: {gridHeight}px;
    --glow-color: {glowColors[glowColor]};
  "
>
  <!-- Main screen container -->
  <div class="grid-screen">
    <!-- Content area - uses udos-grid-line for font control -->
    <div class="grid-content">
      {#if hasChildren && children}
        {@render (children as any)()}
      {:else if lines.length > 0}
        {#each lines as line}
          <div
            class="udos-grid-line {getFontClass(
              getLineFont(line)
            )} color-{getLineColor(line) || 'green'}"
          >
            {padLine(getLineText(line), gridCols)}
          </div>
        {/each}
      {/if}
    </div>

    <!-- CRT Effects Layer -->
    {#if showScanlines}
      <div class="crt-scanlines"></div>
    {/if}

    {#if showCurvature}
      <div class="crt-curvature"></div>
    {/if}
  </div>
</div>

<style>
  /* ========================================
     GRID DISPLAY - Unified Renderer
     Independent of Tailwind, uses fixed pixels
     ======================================== */

  .grid-display {
    position: relative;
    width: var(--grid-width);
    height: var(--grid-height);
    background-color: #000;
    overflow: hidden;
    max-width: var(--grid-width);
    max-height: var(--grid-height);
    flex-shrink: 0;
  }

  .glow-effect {
    box-shadow: 0 0 18px 4px var(--glow-color);
  }

  .grid-screen {
    position: relative;
    width: 100%;
    height: 100%;
    background: #000;
    display: flex;
    flex-direction: column;
  }

  .grid-content {
    position: relative;
    z-index: 1;
    width: var(--grid-width);
    height: var(--grid-height);
    max-width: var(--grid-width);
    max-height: var(--grid-height);
    overflow: hidden;
    /* Font rendering optimization */
    font-family: var(--font-family-teletext);
    font-size: var(--cell-size);
    font-variant-ligatures: none;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: geometricPrecision;
    /* Subtle phosphor flicker */
    animation: phosphor-flicker 0.1s infinite;
  }

  /* ========================================
     CRT EFFECTS
     ======================================== */

  .crt-scanlines {
    position: absolute;
    inset: 0;
    z-index: 2;
    pointer-events: none;
    background: repeating-linear-gradient(
      0deg,
      rgba(0, 0, 0, 0.15),
      rgba(0, 0, 0, 0.15) 1px,
      transparent 1px,
      transparent 2px
    );
  }

  .crt-curvature {
    position: absolute;
    inset: 0;
    z-index: 3;
    pointer-events: none;
    background: radial-gradient(
      ellipse at center,
      transparent 60%,
      rgba(0, 0, 0, 0.4) 100%
    );
  }

  @keyframes phosphor-flicker {
    0% {
      opacity: 0.97;
    }
    50% {
      opacity: 1;
    }
    100% {
      opacity: 0.98;
    }
  }

  /* ========================================
     GRID LINE STYLING
     Uses udos-grid-line from app.css for
     font-size control via data-mono-variant
     ======================================== */

  /* These are fallback styles - app.css provides the font-specific sizing */
  .grid-content :global(.udos-grid-line) {
    display: block;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
    margin: 0;
    padding: 0;
    overflow: visible;
    height: auto;
    line-height: var(--cell-size);
    font-family: inherit;
    font-size: inherit;
    font-variant-ligatures: none;
    word-spacing: 0;
    letter-spacing: 0;
    color: #06ffa5; /* uDOS grass green */
    max-width: 100%;
    width: 100%;
  }

  /* Font-specific variants */
  .grid-content :global(.font-body) {
    font-family: var(--font-family-teletext);
    font-size: var(--cell-size);
    max-width: 100%;
    width: 100%;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  .grid-content :global(.font-title) {
    font-family: var(--font-family-c64);
    font-size: calc(var(--cell-size) * 2);
    height: auto;
    line-height: calc(var(--cell-size) * 2);
    max-width: 100%;
    width: 100%;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  .grid-content :global(.font-heading) {
    font-family: var(--font-family-pressstart);
    font-size: var(--cell-size);
    max-width: 100%;
    width: 100%;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  /* Color variants using uDOS palette */
  .grid-content :global(.color-green) {
    color: #06ffa5; /* uDOS grass green */
  }

  .grid-content :global(.color-cyan) {
    color: #00d9ff; /* uDOS objective cyan */
  }

  .grid-content :global(.color-orange) {
    color: #fb5607; /* uDOS heat orange */
  }

  .grid-content :global(.color-yellow) {
    color: #ffbe0b; /* uDOS waypoint yellow */
  }

  .grid-content :global(.color-red) {
    color: #ff006e; /* uDOS danger magenta */
  }

  .grid-content :global(.color-white) {
    color: #ffffff;
  }
</style>
