<script lang="ts">
  import {
    searchEmoji,
    parseShortcodes,
    type EmojiData,
  } from "$lib/util/emojiLibrary";
  import { iconLibrary, type IconData } from "$lib/util/emojiLibrary";

  interface EmojiPickerProps {
    onSelect: (emoji: EmojiData | IconData) => void;
  }

  let { onSelect }: EmojiPickerProps = $props();

  let searchQuery = $state("");
  let activeTab = $state<"emoji" | "icons">("emoji");
  let emojiResults = $state<EmojiData[]>([]);
  let iconResults = $state<IconData[]>([]);

  /**
   * Search emoji and icons
   */
  function search() {
    if (!searchQuery.trim()) {
      emojiResults = [];
      iconResults = [];
      return;
    }

    emojiResults = searchEmoji(searchQuery);
    iconResults = iconLibrary.searchIcons(searchQuery);
  }

  /**
   * Handle emoji click
   */
  function handleEmojiClick(emoji: EmojiData) {
    onSelect(emoji);
  }

  /**
   * Handle icon click
   */
  function handleIconClick(icon: IconData) {
    onSelect(icon);
  }

  /**
   * Clear search
   */
  function clearSearch() {
    searchQuery = "";
    emojiResults = [];
    iconResults = [];
  }

  // Auto-search on query change
  $effect(() => {
    if (searchQuery) {
      search();
    } else {
      clearSearch();
    }
  });
</script>

<div class="emoji-picker">
  <!-- Search Bar -->
  <div class="search-bar">
    <input
      type="text"
      bind:value={searchQuery}
      placeholder="Search emoji or icons..."
      class="search-input"
    />
    {#if searchQuery}
      <button onclick={clearSearch} class="clear-btn">✕</button>
    {/if}
  </div>

  <!-- Tabs -->
  <div class="tabs">
    <button
      class="tab"
      class:active={activeTab === "emoji"}
      onclick={() => (activeTab = "emoji")}
    >
      Emoji ({emojiResults.length})
    </button>
    <button
      class="tab"
      class:active={activeTab === "icons"}
      onclick={() => (activeTab = "icons")}
    >
      Icons ({iconResults.length})
    </button>
  </div>

  <!-- Results -->
  <div class="results">
    {#if activeTab === "emoji"}
      {#if emojiResults.length > 0}
        <div class="emoji-grid">
          {#each emojiResults as emoji}
            <button
              class="emoji-item"
              onclick={() => handleEmojiClick(emoji)}
              title={emoji.shortcode}
            >
              <span class="emoji-char">{emoji.unicode}</span>
              <span class="emoji-name">{emoji.shortcode.replace(/:/g, "")}</span
              >
            </button>
          {/each}
        </div>
      {:else if searchQuery}
        <p class="no-results">No emoji found for "{searchQuery}"</p>
      {:else}
        <p class="hint">Type to search emoji...</p>
      {/if}
    {:else if iconResults.length > 0}
      <div class="icon-grid">
        {#each iconResults as icon}
          <button
            class="icon-item"
            onclick={() => handleIconClick(icon)}
            title={icon.name}
          >
            <div class="icon-preview">
              {@html icon.svg}
            </div>
            <span class="icon-name">{icon.name}</span>
          </button>
        {/each}
      </div>
    {:else if searchQuery}
      <p class="no-results">No icons found for "{searchQuery}"</p>
    {:else}
      <p class="hint">Type to search icons...</p>
    {/if}
  </div>
</div>

<style>
  .emoji-picker {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #1a1a1a;
    border-radius: 8px;
    overflow: hidden;
  }

  .search-bar {
    display: flex;
    align-items: center;
    padding: 12px;
    border-bottom: 1px solid #333;
    position: relative;
  }

  .search-input {
    flex: 1;
    padding: 8px 32px 8px 12px;
    background: #222;
    border: 1px solid #444;
    border-radius: 4px;
    color: #fff;
    font-size: 14px;
  }

  .search-input:focus {
    outline: none;
    border-color: #00ff00;
  }

  .clear-btn {
    position: absolute;
    right: 20px;
    background: none;
    border: none;
    color: #888;
    cursor: pointer;
    font-size: 18px;
    padding: 4px 8px;
  }

  .clear-btn:hover {
    color: #fff;
  }

  .tabs {
    display: flex;
    border-bottom: 1px solid #333;
  }

  .tab {
    flex: 1;
    padding: 12px;
    background: none;
    border: none;
    color: #888;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
  }

  .tab:hover {
    background: #222;
    color: #fff;
  }

  .tab.active {
    color: #00ff00;
    border-bottom: 2px solid #00ff00;
  }

  .results {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
  }

  .emoji-grid,
  .icon-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 8px;
  }

  .emoji-item,
  .icon-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 12px;
    background: #222;
    border: 1px solid #333;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .emoji-item:hover,
  .icon-item:hover {
    background: #333;
    border-color: #00ff00;
    transform: scale(1.05);
  }

  .emoji-char {
    font-size: 32px;
    margin-bottom: 4px;
  }

  .emoji-name,
  .icon-name {
    font-size: 10px;
    color: #888;
    text-align: center;
    word-break: break-word;
  }

  .icon-preview {
    width: 32px;
    height: 32px;
    margin-bottom: 4px;
  }

  .icon-preview :global(svg) {
    width: 100%;
    height: 100%;
    fill: #fff;
  }

  .no-results,
  .hint {
    text-align: center;
    color: #666;
    padding: 20px;
    font-size: 14px;
  }
</style>
