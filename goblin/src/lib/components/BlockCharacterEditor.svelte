<script lang="ts">
  /**
   * BlockCharacterEditor - 24x24 pixel block character editor
   *
   * For designing teletext/ASCII block graphics
   * Visual editor for creating custom characters on the 24x24 grid
   */

  interface Props {
    onSave?: (character: string, bitmap: boolean[][]) => void;
  }

  let { onSave }: Props = $props();

  // 24x24 pixel grid for character design
  let bitmap = $state<boolean[][]>(
    Array(24)
      .fill(null)
      .map(() => Array(24).fill(false))
  );

  let selectedChar = $state("█"); // Current character to test
  let isDrawing = $state(false);
  let drawMode = $state<"fill" | "erase">("fill");

  // Standard teletext block characters for reference
  const blockChars = [
    "█",
    "▀",
    "▄",
    "▌",
    "▐",
    "░",
    "▒",
    "▓",
    "■",
    "□",
    "▪",
    "▫",
    "▬",
    "▭",
    "▮",
    "▯",
    "▰",
    "▱",
    "▲",
    "►",
    "▼",
    "◄",
    "◆",
    "◇",
  ];

  function togglePixel(row: number, col: number) {
    if (drawMode === "fill") {
      bitmap[row][col] = true;
    } else {
      bitmap[row][col] = false;
    }
  }

  function handleMouseDown(row: number, col: number) {
    isDrawing = true;
    togglePixel(row, col);
  }

  function handleMouseEnter(row: number, col: number) {
    if (isDrawing) {
      togglePixel(row, col);
    }
  }

  function handleMouseUp() {
    isDrawing = false;
  }

  function clearGrid() {
    bitmap = Array(24)
      .fill(null)
      .map(() => Array(24).fill(false));
  }

  function fillGrid() {
    bitmap = Array(24)
      .fill(null)
      .map(() => Array(24).fill(true));
  }

  function saveCharacter() {
    if (onSave) {
      onSave(selectedChar, bitmap);
    }
  }

  function testCharacter(char: string) {
    selectedChar = char;
  }

  // Generate CSS for the character preview
  const characterPreview = $derived(() => {
    return bitmap
      .map((row) => row.map((pixel) => (pixel ? "█" : " ")).join(""))
      .join("\n");
  });
</script>

<svelte:window on:mouseup={handleMouseUp} />

<div class="editor-container">
  <div class="editor-header">
    <h2 class="text-2xl font-bold mb-4">24×24 Block Character Editor</h2>
    <div class="flex gap-2 mb-4">
      <button
        class="btn {drawMode === 'fill' ? 'active' : ''}"
        onclick={() => (drawMode = "fill")}
      >
        ✏️ Draw
      </button>
      <button
        class="btn {drawMode === 'erase' ? 'active' : ''}"
        onclick={() => (drawMode = "erase")}
      >
        🧹 Erase
      </button>
      <button class="btn" onclick={clearGrid}>Clear</button>
      <button class="btn" onclick={fillGrid}>Fill</button>
      <button class="btn btn-primary" onclick={saveCharacter}
        >Save Character</button
      >
    </div>
  </div>

  <div class="editor-main">
    <!-- Pixel Grid Editor -->
    <div class="pixel-grid-container">
      <h3 class="text-sm font-bold mb-2">Pixel Grid (24×24)</h3>
      <div class="pixel-grid">
        {#each bitmap as row, rowIndex}
          {#each row as pixel, colIndex}
            <button
              class="pixel {pixel ? 'filled' : ''}"
              onmousedown={() => handleMouseDown(rowIndex, colIndex)}
              onmouseenter={() => handleMouseEnter(rowIndex, colIndex)}
              aria-label="Pixel {rowIndex},{colIndex}"
            ></button>
          {/each}
        {/each}
      </div>
    </div>

    <!-- Character Preview -->
    <div class="preview-container">
      <h3 class="text-sm font-bold mb-2">Preview (Selected: {selectedChar})</h3>

      <!-- 24x24 actual size preview -->
      <div class="preview-box">
        <div
          class="character-preview"
          style="font-family: var(--font-mono-variant);"
        >
          {selectedChar}
        </div>
      </div>

      <!-- Reference Characters -->
      <h3 class="text-sm font-bold mt-4 mb-2">Block Characters</h3>
      <div class="char-palette">
        {#each blockChars as char}
          <button
            class="char-btn {selectedChar === char ? 'selected' : ''}"
            onclick={() => testCharacter(char)}
            style="font-family: var(--font-mono-variant);"
          >
            {char}
          </button>
        {/each}
      </div>

      <!-- Test Area -->
      <h3 class="text-sm font-bold mt-4 mb-2">Test Grid (5×5)</h3>
      <div class="test-grid">
        {#each Array(5) as _, row}
          {#each Array(5) as _, col}
            <div
              class="test-cell"
              style="font-family: var(--font-mono-variant);"
            >
              {selectedChar}
            </div>
          {/each}
        {/each}
      </div>
    </div>
  </div>
</div>

<style>
  .editor-container {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  .editor-main {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 2rem;
  }

  .btn {
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    border: 1px solid #374151;
    background: #1f2937;
    color: white;
    cursor: pointer;
    transition: all 150ms;
  }

  .btn:hover {
    background: #374151;
  }

  .btn.active,
  .btn.btn-primary {
    background: #3b82f6;
    border-color: #2563eb;
  }

  /* Pixel Grid */
  .pixel-grid {
    display: grid;
    grid-template-columns: repeat(24, 16px);
    grid-template-rows: repeat(24, 16px);
    gap: 1px;
    background: #374151;
    padding: 1px;
    border: 2px solid #4b5563;
  }

  .pixel {
    width: 16px;
    height: 16px;
    background: #1f2937;
    border: none;
    cursor: pointer;
    transition: background 50ms;
  }

  .pixel:hover {
    background: #374151;
  }

  .pixel.filled {
    background: #10b981;
  }

  .pixel.filled:hover {
    background: #059669;
  }

  /* Character Preview */
  .preview-box {
    width: 24px;
    height: 24px;
    border: 2px solid #3b82f6;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .character-preview {
    font-size: 24px;
    line-height: 1;
    color: #10b981;
  }

  /* Character Palette */
  .char-palette {
    display: grid;
    grid-template-columns: repeat(8, 32px);
    gap: 4px;
  }

  .char-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #374151;
    background: #1f2937;
    color: #10b981;
    font-size: 24px;
    line-height: 1;
    cursor: pointer;
    transition: all 150ms;
  }

  .char-btn:hover {
    background: #374151;
    border-color: #3b82f6;
  }

  .char-btn.selected {
    background: #1e40af;
    border-color: #3b82f6;
  }

  /* Test Grid */
  .test-grid {
    display: grid;
    grid-template-columns: repeat(5, 24px);
    grid-template-rows: repeat(5, 24px);
    gap: 0;
    background: #000;
    border: 2px solid #374151;
  }

  .test-cell {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    line-height: 1;
    color: #10b981;
  }
</style>
