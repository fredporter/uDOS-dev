<script lang="ts">
  import { onMount } from "svelte";
  import {
    SPRITE_LIBRARY,
    getSpritesByCategory,
    loadSprite,
    type SpriteMetadata,
  } from "$lib/stores/spriteLibrary";

  let selectedCategory: SpriteMetadata["category"] = "emoji";
  let selectedSprite: SpriteMetadata | null = null;
  let spriteSvg: string = "";
  let spriteSize = 48;

  $: filteredSprites = getSpritesByCategory(selectedCategory);

  async function selectSprite(sprite: SpriteMetadata) {
    selectedSprite = sprite;
    spriteSvg = await loadSprite(sprite.id);
  }

  onMount(async () => {
    // Load first emoji by default
    if (filteredSprites.length > 0) {
      await selectSprite(filteredSprites[0]);
    }
  });
</script>

<div class="sprite-browser">
  <h1>🎨 SVG Sprite Browser</h1>

  <div class="controls">
    <label>
      Category:
      <select bind:value={selectedCategory}>
        <option value="emoji">Emoji</option>
        <option value="monsters">Monsters</option>
        <option value="objects">Objects</option>
        <option value="dungeon">Dungeon</option>
        <option value="effects">Effects</option>
      </select>
    </label>

    <label>
      Size: {spriteSize}px
      <input type="range" bind:value={spriteSize} min="16" max="192" step="8" />
    </label>
  </div>

  <div class="content">
    <!-- Sprite Gallery -->
    <div class="gallery">
      <h2>{selectedCategory}</h2>
      <div class="grid">
        {#each filteredSprites as sprite}
          <button
            class="sprite-card"
            class:selected={selectedSprite?.id === sprite.id}
            on:click={() => selectSprite(sprite)}
          >
            <img src={sprite.path} alt={sprite.name} width="48" height="48" />
            <span class="sprite-name">{sprite.name}</span>
          </button>
        {/each}

        {#if filteredSprites.length === 0}
          <p class="empty">No sprites in this category yet.</p>
        {/if}
      </div>
    </div>

    <!-- Preview Panel -->
    <div class="preview">
      {#if selectedSprite}
        <h2>{selectedSprite.name}</h2>
        <p class="description">{selectedSprite.description}</p>

        <div class="preview-area">
          <div class="checkerboard">
            <img
              src={selectedSprite.path}
              alt={selectedSprite.name}
              width={spriteSize}
              height={spriteSize}
            />
          </div>
        </div>

        <div class="info">
          <p><strong>ID:</strong> <code>{selectedSprite.id}</code></p>
          <p><strong>Path:</strong> <code>{selectedSprite.path}</code></p>
          {#if selectedSprite.tags}
            <p><strong>Tags:</strong> {selectedSprite.tags.join(", ")}</p>
          {/if}
        </div>

        <div class="size-examples">
          <h3>Size Examples</h3>
          <div class="sizes">
            <div class="size-demo">
              <img src={selectedSprite.path} alt="" width="24" height="24" />
              <span>24×24</span>
            </div>
            <div class="size-demo">
              <img src={selectedSprite.path} alt="" width="48" height="48" />
              <span>48×48</span>
            </div>
            <div class="size-demo">
              <img src={selectedSprite.path} alt="" width="96" height="96" />
              <span>96×96</span>
            </div>
          </div>
        </div>

        <details class="svg-source">
          <summary>View SVG Source</summary>
          <pre><code>{spriteSvg}</code></pre>
        </details>
      {:else}
        <p class="empty">Select a sprite to preview</p>
      {/if}
    </div>
  </div>
</div>

<style>
  .sprite-browser {
    min-height: 100vh;
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  h1 {
    font-family: "Press Start 2P", monospace;
    font-size: 1.5rem;
    margin-bottom: 2rem;
  }

  .controls {
    display: flex;
    gap: 2rem;
    margin-bottom: 2rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  select,
  input[type="range"] {
    padding: 0.5rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    border-radius: 4px;
  }

  .content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }

  .gallery {
    background: rgba(255, 255, 255, 0.05);
    padding: 1.5rem;
    border-radius: 8px;
    max-height: 80vh;
    overflow-y: auto;
  }

  .gallery h2 {
    text-transform: capitalize;
    margin-bottom: 1rem;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 1rem;
  }

  .sprite-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    background: rgba(0, 0, 0, 0.3);
    border: 2px solid transparent;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .sprite-card:hover {
    background: rgba(0, 0, 0, 0.5);
    border-color: rgba(255, 255, 255, 0.3);
  }

  .sprite-card.selected {
    border-color: #00ffff;
    background: rgba(0, 255, 255, 0.1);
  }

  .sprite-name {
    font-size: 0.75rem;
    text-align: center;
  }

  .preview {
    background: rgba(255, 255, 255, 0.05);
    padding: 1.5rem;
    border-radius: 8px;
    max-height: 80vh;
    overflow-y: auto;
  }

  .preview h2 {
    margin-bottom: 0.5rem;
  }

  .description {
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 1.5rem;
  }

  .preview-area {
    margin: 2rem 0;
    display: flex;
    justify-content: center;
  }

  .checkerboard {
    background-image:
      linear-gradient(45deg, #333 25%, transparent 25%),
      linear-gradient(-45deg, #333 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #333 75%),
      linear-gradient(-45deg, transparent 75%, #333 75%);
    background-size: 16px 16px;
    background-position:
      0 0,
      0 8px,
      8px -8px,
      -8px 0px;
    padding: 2rem;
    border-radius: 8px;
  }

  .info {
    margin: 1.5rem 0;
    padding: 1rem;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 4px;
  }

  .info p {
    margin: 0.5rem 0;
  }

  code {
    background: rgba(0, 0, 0, 0.5);
    padding: 0.25rem 0.5rem;
    border-radius: 3px;
    font-family: "SF Mono", monospace;
  }

  .size-examples {
    margin: 1.5rem 0;
  }

  .size-examples h3 {
    margin-bottom: 1rem;
    font-size: 1rem;
  }

  .sizes {
    display: flex;
    gap: 2rem;
    padding: 1rem;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 4px;
  }

  .size-demo {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .size-demo span {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.6);
  }

  .svg-source {
    margin-top: 1.5rem;
  }

  .svg-source summary {
    cursor: pointer;
    padding: 0.5rem;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 4px;
    user-select: none;
  }

  .svg-source summary:hover {
    background: rgba(0, 0, 0, 0.5);
  }

  .svg-source pre {
    margin-top: 1rem;
    padding: 1rem;
    background: rgba(0, 0, 0, 0.5);
    border-radius: 4px;
    overflow-x: auto;
    font-size: 0.75rem;
    line-height: 1.4;
  }

  .empty {
    color: rgba(255, 255, 255, 0.5);
    text-align: center;
    padding: 2rem;
  }

  @media (max-width: 900px) {
    .content {
      grid-template-columns: 1fr;
    }
  }
</style>
