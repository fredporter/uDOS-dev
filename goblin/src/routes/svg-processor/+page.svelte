<script lang="ts">
  import { onMount } from "svelte";
  import SVGCanvas from "$lib/components/SVGCanvas.svelte";
  import EmojiPicker from "$lib/components/EmojiPicker.svelte";
  import { UButton, moveLogger } from "$lib";
  import { toastStore } from "$lib/stores/toastStore";
  import {
    parseSVGMetadata,
    rasterizeSVG,
    svgToPixelGrid,
    remapSVGColors,
    optimizeSVG,
    pixelGridToSVG,
    isValidSVG,
  } from "$lib/util/svgParser";
  import {
    pixelGridToAscii,
    asciiToPixelGrid,
    layerToAscii,
    asciiToLayer,
    pixelGridToTeletext,
    teletextToPixelGrid,
    wrapInCodeBlock,
    extractFromMarkdown,
  } from "$lib/util/formatConverters";
  import {
    quantizeToUdosPalette,
    UDOS_PALETTE,
  } from "$lib/util/colorQuantizer";
  import {
    iconLibrary,
    loadCustomIcon,
    exportIconLibrary,
    importIconLibrary,
    type EmojiData,
    type IconData,
  } from "$lib/util/emojiLibrary";
  import {
    nounProjectAPI,
    loadNounProjectConfig,
    saveNounProjectConfig,
  } from "$lib/util/nounProjectAPI";
  import { open, save } from "@tauri-apps/plugin-dialog";
  import { invoke } from "@tauri-apps/api/core";

  // State
  let svgContent = $state("");
  let svgMetadata = $state<any>(null);
  let activePanel = $state<"viewer" | "converter" | "library" | "settings">(
    "viewer"
  );
  let activeTool = $state<"view" | "color-remap" | "optimize" | "pixel-grid">(
    "view"
  );
  let pixelGrid = $state<(number | null)[][]>([]);
  let asciiArt = $state("");
  let canvasRef = $state<any>(null);

  // Conversion states
  let conversionInput = $state("");
  let conversionOutput = $state("");
  let conversionType = $state<
    "ascii-to-svg" | "svg-to-ascii" | "teletext-to-svg" | "svg-to-teletext"
  >("ascii-to-svg");

  // Noun Project
  let nounProjectQuery = $state("");
  let nounProjectResults = $state<any[]>([]);
  let nounProjectKey = $state("");
  let nounProjectSecret = $state("");

  /**
   * Load SVG file
   */
  async function loadSVGFile() {
    try {
      const selected = await open({
        filters: [{ name: "SVG", extensions: ["svg"] }],
      });

      if (selected && typeof selected === "string") {
        const content = await invoke<string>("read_file", { path: selected });
        if (isValidSVG(content)) {
          svgContent = content;
          svgMetadata = parseSVGMetadata(content);
        } else {
          toastStore.error("Invalid SVG file");
        }
      }
    } catch (error) {
      console.error("Failed to load SVG:", error);
      alert(`Error: ${error}`);
    }
  }

  /**
   * Save SVG file
   */
  async function saveSVGFile() {
    if (!svgContent) {
      toastStore.warning("No SVG to save");
      return;
    }

    try {
      const selected = await save({
        filters: [{ name: "SVG", extensions: ["svg"] }],
      });

      if (selected) {
        await invoke("write_file", { path: selected, contents: svgContent });
        toastStore.success("SVG saved successfully");
      }
    } catch (error) {
      console.error("Failed to save SVG:", error);
      alert(`Error: ${error}`);
    }
  }

  /**
   * Apply color remapping
   */
  async function applyColorRemap() {
    if (!svgContent) return;
    svgContent = remapSVGColors(svgContent);
    toastStore.success("Colors remapped to uDOS palette");
  }

  /**
   * Optimize SVG
   */
  function applySVGOptimize() {
    if (!svgContent) return;
    svgContent = optimizeSVG(svgContent);
    toastStore.success("SVG optimized");
  }

  /**
   * Convert to pixel grid
   */
  async function convertToPixelGrid() {
    if (!svgContent) return;
    try {
      pixelGrid = await svgToPixelGrid(svgContent, 24, 24);
      asciiArt = pixelGridToAscii(pixelGrid);
      activeTool = "pixel-grid";
    } catch (error) {
      console.error("Failed to convert:", error);
      alert(`Error: ${error}`);
    }
  }

  /**
   * Convert pixel grid back to SVG
   */
  function pixelGridToSVGConvert() {
    if (pixelGrid.length === 0) return;
    svgContent = pixelGridToSVG(pixelGrid, UDOS_PALETTE, 1);
    alert("Converted to SVG");
  }

  /**
   * Format conversion
   */
  function performConversion() {
    if (!conversionInput.trim()) {
      alert("Enter input content");
      return;
    }

    try {
      switch (conversionType) {
        case "ascii-to-svg":
          const asciiGrid = asciiToPixelGrid(conversionInput, 24, 24);
          conversionOutput = pixelGridToSVG(asciiGrid, UDOS_PALETTE, 1);
          break;

        case "svg-to-ascii":
          if (isValidSVG(conversionInput)) {
            svgToPixelGrid(conversionInput, 24, 24).then((grid) => {
              conversionOutput = pixelGridToAscii(grid);
            });
          } else {
            alert("Invalid SVG");
          }
          break;

        case "teletext-to-svg":
          const teletextGrid = teletextToPixelGrid(conversionInput, 24, 24);
          conversionOutput = pixelGridToSVG(teletextGrid, UDOS_PALETTE, 1);
          break;

        case "svg-to-teletext":
          if (isValidSVG(conversionInput)) {
            svgToPixelGrid(conversionInput, 24, 24).then((grid) => {
              conversionOutput = pixelGridToTeletext(grid);
            });
          } else {
            alert("Invalid SVG");
          }
          break;
      }
    } catch (error) {
      console.error("Conversion error:", error);
      alert(`Conversion failed: ${error}`);
    }
  }

  /**
   * Copy conversion output
   */
  function copyOutput() {
    navigator.clipboard.writeText(conversionOutput);
    alert("Copied to clipboard");
  }

  /**
   * Wrap output in markdown code block
   */
  function wrapOutputInMarkdown() {
    const type = conversionType.includes("ascii") ? "ascii" : "teletext";
    conversionOutput = wrapInCodeBlock(conversionOutput, type);
  }

  /**
   * Load custom icon
   */
  async function loadCustomIconFile() {
    try {
      const selected = await open({
        filters: [{ name: "SVG", extensions: ["svg"] }],
      });

      if (selected && typeof selected === "string") {
        const name = prompt("Icon name:");
        if (name) {
          await loadCustomIcon(selected, name);
          alert("Icon added to library");
        }
      }
    } catch (error) {
      console.error("Failed to load icon:", error);
      alert(`Error: ${error}`);
    }
  }

  /**
   * Export icon library
   */
  async function exportLibrary() {
    try {
      const selected = await save({
        defaultPath: "../memory/data/state/icon-library.json",
        filters: [{ name: "JSON", extensions: ["json"] }],
      });

      if (selected) {
        await exportIconLibrary(selected);
        alert("Library exported");
      }
    } catch (error) {
      console.error("Failed to export:", error);
      alert(`Error: ${error}`);
    }
  }

  /**
   * Import icon library
   */
  async function importLibrary() {
    try {
      const selected = await open({
        filters: [{ name: "JSON", extensions: ["json"] }],
      });

      if (selected && typeof selected === "string") {
        await importIconLibrary(selected);
        alert("Library imported");
      }
    } catch (error) {
      console.error("Failed to import:", error);
      alert(`Error: ${error}`);
    }
  }

  /**
   * Import color emoji library
   */
  async function importColorEmojiLibrary() {
    try {
      const path = "../memory/data/state/emoji-color-library.json";
      await importIconLibrary(path);
      alert("Color Emoji Library imported (30 icons)");
    } catch (error) {
      console.error("Failed to import color emoji:", error);
      alert(`Error: ${error}`);
    }
  }

  /**
   * Import mono emoji library
   */
  async function importMonoEmojiLibrary() {
    try {
      const path = "../memory/data/state/emoji-mono-library.json";
      await importIconLibrary(path);
      alert("Mono Emoji Library imported (35 icons)");
    } catch (error) {
      console.error("Failed to import mono emoji:", error);
      alert(`Error: ${error}`);
    }
  }

  /**
   * Search Noun Project
   */
  async function searchNounProject() {
    if (!nounProjectAPI.isConfigured()) {
      alert("Configure Noun Project API in Settings");
      return;
    }

    if (!nounProjectQuery.trim()) {
      alert("Enter search query");
      return;
    }

    try {
      nounProjectResults = await nounProjectAPI.search(nounProjectQuery);
    } catch (error) {
      console.error("Search failed:", error);
      alert(`Search failed: ${error}`);
    }
  }

  /**
   * Download from Noun Project
   */
  async function downloadNounIcon(iconId: number) {
    try {
      const url = await nounProjectAPI.downloadIcon(iconId);
      const svg = await nounProjectAPI.fetchSVG(url);
      svgContent = svg;
      activePanel = "viewer";
      alert("Icon loaded");
    } catch (error) {
      console.error("Download failed:", error);
      alert(`Download failed: ${error}`);
    }
  }

  /**
   * Save Noun Project config
   */
  async function saveNounConfig() {
    if (!nounProjectKey || !nounProjectSecret) {
      alert("Enter API key and secret");
      return;
    }

    try {
      await saveNounProjectConfig(nounProjectKey, nounProjectSecret);
      alert("Configuration saved");
    } catch (error) {
      console.error("Failed to save config:", error);
      alert(`Error: ${error}`);
    }
  }

  /**
   * Handle emoji/icon selection
   */
  function handleEmojiSelect(item: EmojiData | IconData) {
    if ("svg" in item && item.svg) {
      // Icon with SVG
      svgContent = item.svg;
      activePanel = "viewer";
    } else if ("unicode" in item) {
      // Emoji - need to render as text
      alert(`Selected emoji: ${item.unicode}`);
    }
  }

  // Load config on mount
  onMount(async () => {
    await loadNounProjectConfig();
  });
</script>

<svelte:head>
  <title>SVG Processor - Markdown</title>
</svelte:head>

<div class="svg-processor">
  <!-- Header -->
  <header class="header">
    <h1>SVG Processor</h1>
    <div class="header-actions">
      <button onclick={loadSVGFile}>📂 Open</button>
      <button onclick={saveSVGFile} disabled={!svgContent}>💾 Save</button>
    </div>
  </header>

  <!-- Main Content -->
  <div class="main-content">
    <!-- Sidebar -->
    <aside class="sidebar">
      <nav class="panel-nav">
        <button
          class="nav-btn"
          class:active={activePanel === "viewer"}
          onclick={() => (activePanel = "viewer")}
        >
          👁️ Viewer
        </button>
        <button
          class="nav-btn"
          class:active={activePanel === "converter"}
          onclick={() => (activePanel = "converter")}
        >
          🔄 Converter
        </button>
        <button
          class="nav-btn"
          class:active={activePanel === "library"}
          onclick={() => (activePanel = "library")}
        >
          📚 Library
        </button>
        <button
          class="nav-btn"
          class:active={activePanel === "settings"}
          onclick={() => (activePanel = "settings")}
        >
          ⚙️ Settings
        </button>
      </nav>

      <!-- Tool Panel -->
      {#if activePanel === "viewer"}
        <div class="tool-panel">
          <h3>Tools</h3>
          <button
            class="tool-btn"
            class:active={activeTool === "view"}
            onclick={() => (activeTool = "view")}
          >
            View
          </button>
          <button
            class="tool-btn"
            class:active={activeTool === "color-remap"}
            onclick={applyColorRemap}
            disabled={!svgContent}
          >
            Remap Colors
          </button>
          <button
            class="tool-btn"
            class:active={activeTool === "optimize"}
            onclick={applySVGOptimize}
            disabled={!svgContent}
          >
            Optimize
          </button>
          <button
            class="tool-btn"
            class:active={activeTool === "pixel-grid"}
            onclick={convertToPixelGrid}
            disabled={!svgContent}
          >
            To Pixel Grid
          </button>

          {#if pixelGrid.length > 0}
            <hr />
            <h3>Pixel Grid</h3>
            <button onclick={pixelGridToSVGConvert}>Convert to SVG</button>
            <div class="ascii-preview">
              <pre>{asciiArt}</pre>
            </div>
          {/if}

          {#if svgMetadata}
            <hr />
            <h3>Metadata</h3>
            <div class="metadata">
              <p>
                <strong>Size:</strong>
                {svgMetadata.width}×{svgMetadata.height}
              </p>
              {#if svgMetadata.title}
                <p><strong>Title:</strong> {svgMetadata.title}</p>
              {/if}
            </div>
          {/if}
        </div>
      {/if}
    </aside>

    <!-- Content Area -->
    <main class="content-area">
      {#if activePanel === "viewer"}
        <div class="viewer-panel">
          {#if svgContent}
            <SVGCanvas
              bind:this={canvasRef}
              bind:svg={svgContent}
              width={600}
              height={600}
            />
          {:else}
            <div class="empty-state">
              <p>No SVG loaded</p>
              <button onclick={loadSVGFile}>📂 Open SVG File</button>
            </div>
          {/if}
        </div>
      {:else if activePanel === "converter"}
        <div class="converter-panel">
          <h2>Format Converter</h2>

          <div class="conversion-selector">
            <label>
              Conversion Type:
              <select bind:value={conversionType}>
                <option value="ascii-to-svg">ASCII → SVG</option>
                <option value="svg-to-ascii">SVG → ASCII</option>
                <option value="teletext-to-svg">Teletext → SVG</option>
                <option value="svg-to-teletext">SVG → Teletext</option>
              </select>
            </label>
          </div>

          <div class="conversion-io">
            <div class="input-section">
              <h3>Input</h3>
              <textarea
                bind:value={conversionInput}
                placeholder="Paste content here..."
                rows="15"
              ></textarea>
            </div>

            <div class="convert-actions">
              <button onclick={performConversion}>🔄 Convert</button>
            </div>

            <div class="output-section">
              <h3>Output</h3>
              <textarea
                bind:value={conversionOutput}
                placeholder="Output will appear here..."
                rows="15"
                readonly
              ></textarea>
              <div class="output-actions">
                <button onclick={copyOutput} disabled={!conversionOutput}
                  >📋 Copy</button
                >
                <button
                  onclick={wrapOutputInMarkdown}
                  disabled={!conversionOutput}>📝 Wrap in MD</button
                >
              </div>
            </div>
          </div>
        </div>
      {:else if activePanel === "library"}
        <div class="library-panel">
          <h2>Icon & Emoji Library</h2>

          <div class="library-actions">
            <button onclick={loadCustomIconFile}>➕ Add Custom Icon</button>
            <button onclick={exportLibrary}>💾 Export Library</button>
            <button onclick={importLibrary}>📂 Import Library</button>
            <a href="/pixel-editor" class="library-link-btn">
              🎨 Open Pixel Editor
            </a>
          </div>

          <hr />

          <h3>Preset Emoji Libraries</h3>
          <div class="library-actions">
            <button onclick={importColorEmojiLibrary}>
              🎨 Import Color Emoji (30)
            </button>
            <button onclick={importMonoEmojiLibrary}>
              ⚫ Import Mono Emoji (35)
            </button>
          </div>
          <p class="library-note">
            Color: Noto Color Emoji | Mono: Noto Emoji (monochrome)
          </p>

          <hr />

          <EmojiPicker onSelect={handleEmojiSelect} />

          <hr />

          <h3>Noun Project Search</h3>
          <div class="noun-search">
            <input
              type="text"
              bind:value={nounProjectQuery}
              placeholder="Search icons..."
            />
            <button onclick={searchNounProject}>🔍 Search</button>
          </div>

          {#if nounProjectResults.length > 0}
            <div class="noun-results">
              {#each nounProjectResults as result}
                <div class="noun-item">
                  <img src={result.thumbnail_url} alt={result.term} />
                  <p>{result.term}</p>
                  <button onclick={() => downloadNounIcon(result.id)}
                    >Download</button
                  >
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {:else if activePanel === "settings"}
        <div class="settings-panel">
          <h2>Settings</h2>

          <section class="settings-section">
            <h3>Noun Project API</h3>
            <p>
              Get API credentials from <a
                href="https://thenounproject.com/developers/"
                target="_blank">The Noun Project</a
              >
            </p>

            <label>
              API Key:
              <input
                type="text"
                bind:value={nounProjectKey}
                placeholder="Enter API key"
              />
            </label>

            <label>
              API Secret:
              <input
                type="password"
                bind:value={nounProjectSecret}
                placeholder="Enter API secret"
              />
            </label>

            <button onclick={saveNounConfig}>💾 Save Configuration</button>
          </section>

          <section class="settings-section">
            <h3>uDOS Color Palette</h3>
            <p>All imported graphics are mapped to the 32-color uDOS palette</p>
            <div class="palette-preview">
              {#each UDOS_PALETTE as color, i}
                <div
                  class="palette-swatch"
                  style="background-color: {color}"
                  title="Color {i}: {color}"
                ></div>
              {/each}
            </div>
          </section>
        </div>
      {/if}
    </main>
  </div>
</div>

<style>
  .svg-processor {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--color-udos-bg);
    color: var(--color-udos-text);
    font-family: var(--font-family-mono);
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: #1a1a1a;
    border-bottom: 1px solid #333;
  }

  .header h1 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--color-udos-cyan);
  }

  .header-actions {
    display: flex;
    gap: 8px;
  }

  .header-actions button {
    padding: 6px 12px;
    background: #222;
    border: 1px solid #444;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    font-size: 13px;
  }

  .header-actions button:hover:not(:disabled) {
    background: #333;
    border-color: var(--color-udos-cyan);
  }

  .header-actions button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .main-content {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .sidebar {
    width: 250px;
    background: #1a1a1a;
    border-right: 1px solid #333;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
  }

  .panel-nav {
    display: flex;
    flex-direction: column;
    padding: 12px;
    gap: 6px;
  }

  .nav-btn {
    padding: 10px;
    background: #222;
    border: 1px solid #333;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    text-align: left;
    font-size: 14px;
    transition: all 0.2s;
  }

  .nav-btn:hover {
    background: #2a2a2a;
    border-color: var(--color-udos-cyan);
  }

  .nav-btn.active {
    background: var(--color-udos-cyan);
    color: #000;
    font-weight: 600;
  }

  .tool-panel {
    padding: 12px;
  }

  .tool-panel h3 {
    margin: 12px 0 8px;
    font-size: 12px;
    text-transform: uppercase;
    color: #888;
  }

  .tool-btn {
    display: block;
    width: 100%;
    padding: 8px;
    margin-bottom: 6px;
    background: #222;
    border: 1px solid #333;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    font-size: 13px;
  }

  .tool-btn:hover:not(:disabled) {
    background: #2a2a2a;
  }

  .tool-btn.active {
    border-color: var(--color-udos-cyan);
    color: var(--color-udos-cyan);
  }

  .tool-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .ascii-preview {
    margin-top: 12px;
    padding: 8px;
    background: #000;
    border: 1px solid #333;
    border-radius: 4px;
    overflow-x: auto;
  }

  .ascii-preview pre {
    margin: 0;
    font-size: 10px;
    line-height: 1;
    color: var(--color-udos-cyan);
  }

  .metadata {
    font-size: 12px;
    color: #ccc;
  }

  .metadata p {
    margin: 6px 0;
  }

  .content-area {
    flex: 1;
    overflow: auto;
    padding: 20px;
  }

  .viewer-panel {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
  }

  .empty-state {
    text-align: center;
    color: #666;
  }

  .empty-state p {
    margin-bottom: 16px;
    font-size: 16px;
  }

  .converter-panel,
  .library-panel,
  .settings-panel {
    max-width: 1000px;
  }

  .converter-panel h2,
  .library-panel h2,
  .settings-panel h2 {
    margin: 0 0 20px;
    color: var(--color-udos-cyan);
  }

  .conversion-selector {
    margin-bottom: 20px;
  }

  .conversion-selector label {
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 14px;
  }

  .conversion-selector select {
    padding: 8px;
    background: #222;
    border: 1px solid #444;
    border-radius: 4px;
    color: #fff;
    font-size: 14px;
  }

  .conversion-io {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 20px;
  }

  .input-section,
  .output-section {
    display: flex;
    flex-direction: column;
  }

  .input-section h3,
  .output-section h3 {
    margin: 0 0 12px;
    font-size: 14px;
    color: var(--color-udos-cyan);
  }

  textarea {
    flex: 1;
    padding: 12px;
    background: #000;
    border: 1px solid #444;
    border-radius: 4px;
    color: #fff;
    font-family: var(--font-family-mono);
    font-size: 13px;
    resize: vertical;
  }

  textarea:focus {
    outline: none;
    border-color: var(--color-udos-cyan);
  }

  .convert-actions {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .convert-actions button {
    padding: 12px 20px;
    background: var(--color-udos-cyan);
    border: none;
    border-radius: 4px;
    color: #000;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
  }

  .convert-actions button:hover {
    background: var(--color-udos-deep-water);
  }

  .output-actions {
    display: flex;
    gap: 8px;
    margin-top: 12px;
  }

  .output-actions button {
    padding: 8px 16px;
    background: #222;
    border: 1px solid #444;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    font-size: 13px;
  }

  .output-actions button:hover:not(:disabled) {
    background: #333;
    border-color: var(--color-udos-cyan);
  }

  .output-actions button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .library-actions {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }

  .library-actions button,
  .library-actions a {
    padding: 8px 16px;
    background: #222;
    border: 1px solid #444;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    font-size: 13px;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
  }

  .library-actions button:hover,
  .library-actions a:hover {
    background: #333;
    border-color: var(--color-udos-cyan);
  }

  .noun-search {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
  }

  .noun-search input {
    flex: 1;
    padding: 8px 12px;
    background: #222;
    border: 1px solid #444;
    border-radius: 4px;
    color: #fff;
    font-size: 14px;
  }

  .noun-search button {
    padding: 8px 16px;
    background: var(--color-udos-cyan);
    border: none;
    border-radius: 4px;
    color: #000;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
  }

  .noun-results {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
    margin-top: 20px;
  }

  .noun-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px;
    background: #222;
    border: 1px solid #333;
    border-radius: 4px;
  }

  .noun-item img {
    width: 64px;
    height: 64px;
    margin-bottom: 8px;
  }

  .noun-item p {
    margin: 0 0 8px;
    font-size: 12px;
    text-align: center;
  }

  .noun-item button {
    padding: 4px 12px;
    background: var(--color-udos-cyan);
    border: none;
    border-radius: 4px;
    color: #000;
    cursor: pointer;
    font-size: 12px;
  }

  .library-note {
    margin: 8px 0 0;
    font-size: 12px;
    color: #888;
    font-style: italic;
  }

  .settings-section {
    margin-bottom: 32px;
  }

  .settings-section h3 {
    margin: 0 0 12px;
    font-size: 16px;
    color: var(--color-udos-cyan);
  }

  .settings-section p {
    margin: 0 0 16px;
    color: #ccc;
    font-size: 14px;
  }

  .settings-section label {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 16px;
    font-size: 14px;
  }

  .settings-section input {
    padding: 8px 12px;
    background: #222;
    border: 1px solid #444;
    border-radius: 4px;
    color: #fff;
    font-size: 14px;
  }

  .settings-section button {
    padding: 10px 20px;
    background: var(--color-udos-cyan);
    border: none;
    border-radius: 4px;
    color: #000;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
  }

  .palette-preview {
    display: grid;
    grid-template-columns: repeat(16, 1fr);
    gap: 4px;
    margin-top: 12px;
  }

  .palette-swatch {
    width: 100%;
    padding-top: 100%;
    border-radius: 4px;
    border: 1px solid #333;
    cursor: pointer;
  }

  .palette-swatch:hover {
    transform: scale(1.2);
    z-index: 10;
    border-color: #fff;
  }

  hr {
    margin: 20px 0;
    border: none;
    border-top: 1px solid #333;
  }

  a {
    color: var(--color-udos-cyan);
    text-decoration: none;
  }

  a:hover {
    text-decoration: underline;
  }
</style>
