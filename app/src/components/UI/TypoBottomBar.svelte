<script lang="ts">
  import { onMount } from "svelte";
  import { writable } from "svelte/store";
  import { getCurrentWindow } from "@tauri-apps/api/window";

  // Tailwind font and size classes as in Typo
  const fontFamilies = [
    "font-sans",
    "font-humanist",
    "font-serif",
    "font-old-style",
    "font-mono",
  ];
  const fontLabels = ["Sans", "Humanist", "Serif", "OldStyle", "Mono"];

  // Map font classes to actual font-family values
  const fontFamilyValues = [
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif", // Sans
    "Seravek, 'Gill Sans Nova', Ubuntu, Calibri, 'DejaVu Sans', source-sans-pro, sans-serif", // Humanist
    "'Iowan Old Style', 'Palatino Linotype', 'URW Palladio L', P052, serif", // Serif
    "'Crimson Text', 'Garamond', 'EB Garamond', 'Times New Roman', serif", // Old Style
    "'IBM Plex Mono', 'Menlo', 'Monaco', 'Consolas', monospace", // Mono
  ];

  const fontFamilyIdx = writable(0);
  let currentFontIdx = 0;

  const fontSizes = [
    "prose-sm",
    "prose-base",
    "prose-lg",
    "prose-xl",
    "prose-2xl",
  ];
  const fontSizeValues = [14, 16, 18, 20, 24]; // px values
  const fontSizeIdx = writable(1); // default prose-base
  let currentSizeIdx = 1;

  export let isDark: boolean = true;
  export let onDarkModeToggle: () => void = () => {};
  export let viewMode: boolean = false;
  export let onToggleView: () => void = () => {};

  let isFullscreen = false;

  async function toggleFullscreen() {
    try {
      const window = getCurrentWindow();
      isFullscreen = !isFullscreen;
      await window.setFullscreen(isFullscreen);
    } catch (err) {
      console.error("Fullscreen error:", err);
    }
  }

  // Track fullscreen state on mount
  onMount(async () => {
    updateRootFont();
    try {
      const window = getCurrentWindow();
      isFullscreen = await window.isFullscreen();
    } catch (err) {
      console.error("Could not get fullscreen state:", err);
    }
  });

  // Subscribe to store changes to keep local vars in sync
  fontFamilyIdx.subscribe((i) => {
    currentFontIdx = i;
    updateRootFont();
  });

  fontSizeIdx.subscribe((i) => {
    currentSizeIdx = i;
    updateRootFont();
  });

  function cycleFont() {
    fontFamilyIdx.update((i) => (i + 1) % fontFamilies.length);
  }
  function incSize() {
    fontSizeIdx.update((i) => Math.min(fontSizes.length - 1, i + 1));
  }
  function decSize() {
    fontSizeIdx.update((i) => Math.max(0, i - 1));
  }
  function resetSize() {
    fontFamilyIdx.set(0); // Reset to Sans
    fontSizeIdx.set(1); // Reset to base size
  }
  function updateRootFont() {
    if (typeof window === "undefined") return;

    // Remove all font and size classes from html and app-wrapper
    document.documentElement.classList.remove(...fontFamilies, ...fontSizes);
    const appWrapper = document.getElementById("app-wrapper");
    if (appWrapper) {
      appWrapper.classList.remove(...fontFamilies, ...fontSizes);
      appWrapper.classList.add(
        fontFamilies[currentFontIdx],
        fontSizes[currentSizeIdx],
      );
    }
    document.documentElement.classList.add(
      fontFamilies[currentFontIdx],
      fontSizes[currentSizeIdx],
    );

    // Set CSS variables for components that use them (like TypoEditor)
    document.documentElement.style.setProperty(
      "--typo-font-family",
      fontFamilyValues[currentFontIdx],
    );
    document.documentElement.style.setProperty(
      "--typo-font-size",
      `${fontSizeValues[currentSizeIdx]}px`,
    );
  }
</script>

<div class="typo-bottom-bar">
  <!-- Left side: Status info -->
  <div class="typo-bar-left">
    <span class="status-text"
      >{fontLabels[currentFontIdx]} · {fontSizes[currentSizeIdx].replace(
        "prose-",
        "",
      )}</span
    >
  </div>

  <!-- Right side: Controls -->
  <div class="typo-bar-right">
    <div class="typo-bar-section size-controls">
      <button
        on:click={decSize}
        aria-label="Decrease font size"
        title="Decrease font size">A−</button
      >
      <button
        on:click={incSize}
        aria-label="Increase font size"
        title="Increase font size">A+</button
      >
      <button
        on:click={resetSize}
        aria-label="Reset font size"
        title="Reset font size"
        class="reset-btn"
      >
        ∞
      </button>
    </div>

    <div class="typo-bar-section">
      <button
        class="font-btn"
        on:click={cycleFont}
        aria-label="Toggle font family"
        title="Change font family"
      >
        Aa
      </button>
    </div>

    <div class="typo-bar-section">
      <button
        on:click={onToggleView}
        class="font-btn"
        aria-label="Toggle editor view"
        title={viewMode ? "Show editor" : "Hide editor"}
      >
        {#if viewMode}
          <span style="font-size: 1.25rem;">✎</span>
        {:else}
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
            <path
              fill-rule="evenodd"
              d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
              clip-rule="evenodd"
            />
          </svg>
        {/if}
      </button>
    </div>

    <div class="typo-bar-section">
      <button
        on:click={toggleFullscreen}
        class="font-btn"
        aria-label="Toggle fullscreen"
        title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
      >
        {#if isFullscreen}
          ⛶
        {:else}
          ⛶
        {/if}
      </button>
    </div>

    <div class="typo-bar-section">
      <button
        on:click={onDarkModeToggle}
        class="font-btn"
        aria-label="Toggle dark mode"
        title="Toggle dark mode"
      >
        {#if isDark}
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"
            ><path
              d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4.22 2.47a1 1 0 011.42 1.42l-.7.7a1 1 0 11-1.42-1.42l.7-.7zM18 9a1 1 0 100 2h-1a1 1 0 100-2h1zm-2.47 4.22a1 1 0 011.42 1.42l-.7.7a1 1 0 11-1.42-1.42l.7-.7zM10 16a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zm-4.22-2.47a1 1 0 00-1.42 1.42l.7.7a1 1 0 001.42-1.42l-.7-.7zM4 9a1 1 0 100 2H3a1 1 0 100-2h1zm2.47-4.22a1 1 0 00-1.42-1.42l-.7.7a1 1 0 001.42 1.42l.7-.7zM10 6a4 4 0 100 8 4 4 0 000-8z"
            /></svg
          >
        {:else}
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"
            ><path
              d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"
            /></svg
          >
        {/if}
      </button>
    </div>
  </div>
</div>

<style>
  .typo-bottom-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100vw;
    background: #f8fafc;
    color: #1e293b;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 1.5rem;
    z-index: 100;
    border-top: 1px solid #e2e8f0;
    transition:
      background 0.2s,
      color 0.2s,
      border-color 0.2s;
  }
  :global(html.dark) .typo-bottom-bar {
    background: #18181b;
    color: #f1f5f9;
    border-top-color: #334155;
  }

  .typo-bar-left {
    display: flex;
    align-items: center;
  }

  .status-text {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }
  :global(html.dark) .status-text {
    color: #94a3b8;
  }

  .typo-bar-right {
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }

  .typo-bar-section {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .font-btn {
    background: none;
    border: none;
    color: inherit;
    font-family: inherit;
    font-size: 1rem;
    padding: 0.375rem 0.75rem;
    border-radius: 0.375rem;
    cursor: pointer;
    opacity: 0.8;
    transition:
      background 0.2s,
      opacity 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .font-btn:hover {
    background: #e2e8f0;
    opacity: 1;
  }
  :global(html.dark) .font-btn:hover {
    background: #334155;
    opacity: 1;
  }

  .size-controls {
    display: flex;
    gap: 0.25rem;
  }

  .size-controls button {
    background: none;
    border: 1px solid #cbd5e1;
    color: inherit;
    font-size: 0.875rem;
    padding: 0.375rem 0.75rem;
    border-radius: 0.375rem;
    cursor: pointer;
    transition:
      border-color 0.2s,
      background 0.2s;
    font-weight: 600;
    line-height: 1;
    min-width: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  :global(html.dark) .size-controls button {
    border-color: #475569;
  }
  .size-controls button:hover {
    background: #e2e8f0;
    border-color: #94a3b8;
  }
  :global(html.dark) .size-controls button:hover {
    background: #334155;
    border-color: #64748b;
  }

  .size-controls button:nth-child(3) {
    background: #f0f9ff;
    border-color: #3b82f6;
    color: #0c4a6e;
    font-weight: 700;
    font-size: 1rem;
    padding: 0.375rem 0.75rem;
  }
  :global(html.dark) .size-controls button:nth-child(3) {
    background: #082f49;
    border-color: #0c4a6e;
    color: #bae6fd;
  }
  .size-controls button:nth-child(3):hover {
    background: #dbeafe;
    border-color: #60a5fa;
  }
  :global(html.dark) .size-controls button:nth-child(3):hover {
    background: #0c4a6e;
    border-color: #60a5fa;
  }
</style>
