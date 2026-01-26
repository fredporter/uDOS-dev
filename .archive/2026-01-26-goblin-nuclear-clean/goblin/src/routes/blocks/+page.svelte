<script lang="ts">
  import BlockCharacterEditor from "$lib/components/BlockCharacterEditor.svelte";
  import CharacterGrid from "$lib/components/CharacterGrid.svelte";
  import { onMount } from "svelte";

  let savedCharacters = $state<Array<{ char: string; bitmap: boolean[][] }>>(
    []
  );
  let testLines = $state<string[]>([
    "╔════════════════════════════════════════╗",
    "║  24×24 Block Character Test Grid      ║",
    "║                                        ║",
    "║  █▀▀▀█ ▀█▀ ▀▀█▀▀ ▀█▀                   ║",
    "║  █   █  █    █    █                    ║",
    "║  █▀▀▀█  █    █    █                    ║",
    "║                                        ║",
    "║  Block Graphics: ░░▒▒▓▓██              ║",
    "║  Arrows: ▲►▼◄ ▶◀                       ║",
    "║  Shapes: ■□◆◇●○                        ║",
    "╚════════════════════════════════════════╝",
  ]);

  function handleSave(character: string, bitmap: boolean[][]) {
    savedCharacters = [...savedCharacters, { char: character, bitmap }];
    console.log("Character saved:", character);
    console.log("Bitmap:", bitmap);
  }

  // Font testing grid
  const fonts = ["jetbrains", "teletext", "c64", "pressstart"];
  let currentFont = $state(0);

  function cycleFont() {
    currentFont = (currentFont + 1) % fonts.length;
    document.documentElement.setAttribute(
      "data-mono-variant",
      fonts[currentFont]
    );
  }
</script>

<svelte:head>
  <title>Block Character Editor - Markdown</title>
</svelte:head>

<div class="page-container">
  <div class="header">
    <h1 class="text-3xl font-bold mb-2">24×24 Block Character System</h1>
    <p class="text-gray-400 mb-4">
      Design and test teletext/ASCII block graphics with perfect 24×24 pixel
      alignment
    </p>

    <div class="flex gap-4 mb-6">
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        onclick={cycleFont}
      >
        Font: {fonts[currentFont]} ▶
      </button>
      <div class="px-4 py-2 bg-gray-800 rounded">
        Current: <span
          class="font-mono"
          style="font-family: var(--font-mono-variant);">█▀▄░</span
        >
      </div>
    </div>
  </div>

  <!-- Block Character Editor -->
  <section class="mb-8">
    <BlockCharacterEditor onSave={handleSave} />
  </section>

  <!-- Test Grids -->
  <section class="mb-8">
    <h2 class="text-2xl font-bold mb-4">Character Grid Tests</h2>

    <div class="grid-comparison">
      <!-- Old Method (with letter-spacing gaps) -->
      <div>
        <h3 class="text-sm font-bold mb-2">Old Method (letter-spacing)</h3>
        <div class="old-grid bg-black p-4 border border-gray-700">
          {#each testLines as line}
            <div
              class="udos-grid-line text-green-400"
              style="font-family: var(--font-mono-variant);"
            >
              {line}
            </div>
          {/each}
        </div>
      </div>

      <!-- New Method (true 24x24 grid) -->
      <div>
        <h3 class="text-sm font-bold mb-2">New Method (CharacterGrid)</h3>
        <div class="new-grid bg-black p-4 border border-blue-600">
          <CharacterGrid
            lines={testLines}
            cols={42}
            rows={11}
            className="text-green-400"
          />
        </div>
      </div>
    </div>
  </section>

  <!-- Saved Characters -->
  {#if savedCharacters.length > 0}
    <section class="mb-8">
      <h2 class="text-2xl font-bold mb-4">
        Saved Characters ({savedCharacters.length})
      </h2>
      <div class="saved-chars">
        {#each savedCharacters as saved, idx}
          <div class="saved-char-box">
            <div
              class="char-display"
              style="font-family: var(--font-mono-variant);"
            >
              {saved.char}
            </div>
            <div class="text-xs text-gray-500">#{idx + 1}</div>
          </div>
        {/each}
      </div>
    </section>
  {/if}

  <!-- Documentation -->
  <section class="documentation">
    <h2 class="text-2xl font-bold mb-4">Implementation Notes</h2>
    <div class="prose prose-invert">
      <h3>The Gap Problem</h3>
      <p>
        Monospace fonts don't have 1:1 aspect ratios. Most are ~0.6:1
        (width:height). Using letter-spacing creates visible gaps between
        characters, breaking block graphics.
      </p>

      <h3>The Solution: CharacterGrid</h3>
      <ul>
        <li>
          <strong>CSS Grid:</strong> Each character in explicit 24×24px cell
        </li>
        <li>
          <strong>No gaps:</strong> grid-gap: 0 ensures seamless block graphics
        </li>
        <li>
          <strong>Centered chars:</strong> Flex centering within each cell
        </li>
        <li><strong>Font-agnostic:</strong> Works with any monospace font</li>
      </ul>

      <h3>Block Character Library</h3>
      <p>Standard teletext/ASCII block drawing characters:</p>
      <code style="font-family: var(--font-mono-variant);">
        █ ▀ ▄ ▌ ▐ ░ ▒ ▓ ■ □ ▪ ▫ ▬ ▭ ▮ ▯ ▰ ▱ ▲ ► ▼ ◄ ◆ ◇
      </code>

      <h3>Next Steps</h3>
      <ol>
        <li>Replace .udos-grid-line with CharacterGrid in terminal/teledesk</li>
        <li>Create custom font with perfectly square glyphs</li>
        <li>Build character palette component for easy access</li>
        <li>Add color support for each character cell</li>
      </ol>
    </div>
  </section>
</div>

<style>
  .page-container {
    padding: 2rem;
    max-width: 1600px;
    margin: 0 auto;
    background: #0f172a;
    height: 100%;
    overflow-y: auto;
    color: white;
  }

  .grid-comparison {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }

  .saved-chars {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(48px, 1fr));
    gap: 0.5rem;
  }

  .saved-char-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    padding: 0.5rem;
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 0.375rem;
  }

  .char-display {
    font-size: 24px;
    line-height: 1;
    color: #10b981;
  }

  .documentation {
    background: #1e293b;
    padding: 2rem;
    border-radius: 0.5rem;
    border: 1px solid #334155;
  }

  .prose {
    color: #e2e8f0;
  }

  .prose h3 {
    color: #60a5fa;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
  }

  .prose code {
    background: #0f172a;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 18px;
  }

  .prose ul,
  .prose ol {
    margin-left: 1.5rem;
  }

  .prose li {
    margin: 0.5rem 0;
  }
</style>
