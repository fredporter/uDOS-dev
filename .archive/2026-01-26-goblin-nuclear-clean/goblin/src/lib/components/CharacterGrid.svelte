<script lang="ts">
  /**
   * CharacterGrid - True 24x24 square character block grid
   *
   * Perfect for terminal/teledesk rendering with block graphics support
   * Each character renders in an exact 24x24px cell with no gaps
   */

  interface Props {
    lines: string[];
    cols: number;
    rows?: number; // Optional - defaults to lines.length
    className?: string;
  }

  let { lines, cols, rows, className = "" }: Props = $props();

  // Use provided rows or default to lines length
  const gridRows = $derived(rows || lines.length);
</script>

<div
  class="character-grid udos-grid-line {className}"
  style="
    --grid-cols: {cols};
    --grid-rows: {gridRows};
    --cell-size: 24px;
  "
>
  {#each lines as line, rowIndex}
    {#each Array.from(line.padEnd(cols, " ")) as char, colIndex}
      <div class="char-cell" data-row={rowIndex} data-col={colIndex}>
        {char}
      </div>
    {/each}
  {/each}
</div>

<style>
  .character-grid {
    display: grid;
    grid-template-columns: repeat(var(--grid-cols), var(--cell-size));
    grid-template-rows: repeat(var(--grid-rows), var(--cell-size));
    gap: 0;
    width: fit-content;
    height: fit-content;
    font-family: var(--font-mono-variant);
    font-variant-ligatures: none;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    /* line-height and font-size controlled by data-mono-variant in app.css */
  }

  .char-cell {
    width: var(--cell-size);
    height: var(--cell-size);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
    padding: 0;
    margin: 0;
  }
</style>
