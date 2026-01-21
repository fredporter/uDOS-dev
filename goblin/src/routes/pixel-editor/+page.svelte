<script lang="ts">
  import { onMount } from "svelte";
  import PixelGrid from "$lib/components/PixelGrid.svelte";
  import CharacterLibrary from "$lib/components/CharacterLibrary.svelte";
  import ColorPalette from "$lib/components/ColorPalette.svelte";
  import {
    loadFont,
    type CharacterData,
    type LoadFontResult,
  } from "$lib/util/fontLoader";
  import { exportFont } from "$lib/util/fontExporter";
  import { getAsciiMapping } from "$lib/util/characterDatasets";
  import {
    FONT_COLLECTIONS,
    getDefaultFontCollection,
    getFontCollection,
    type FontCollection,
  } from "$lib/util/fontCollections";
  import * as svg from "$lib/components/svg";
  import { getStateForMode, updateModeState } from "$lib/stores/modeState";
  import { loadIconLibraryToEditor } from "$lib/util/emojiLibrary";
  import { UButton, moveLogger } from "$lib";

  // Default settings for reset
  const DEFAULT_COLLECTION_INDEX = 2; // Teletext50
  const DEFAULT_GRID_SIZE = 24;
  const DEFAULT_ASCII_CODE = 65; // 'A'
  const DEFAULT_FONT_NAME = "CustomFont";

  // Track the selected collection by index for reliable dropdown sync
  let selectedCollectionIndex = $state(DEFAULT_COLLECTION_INDEX);
  let selectedCollection = $derived(
    FONT_COLLECTIONS[selectedCollectionIndex] ||
      FONT_COLLECTIONS[DEFAULT_COLLECTION_INDEX]
  );
  let characters = $state<CharacterData[]>([]);
  let currentCharacter = $state<CharacterData | null>(null);
  let pixelData = $state<boolean[][] | (number | null)[][]>(
    Array(DEFAULT_GRID_SIZE)
      .fill(null)
      .map(() => Array(DEFAULT_GRID_SIZE).fill(false))
  );
  let selectedColor = $state("#000000");
  let asciiCode = $state(DEFAULT_ASCII_CODE); // Default to 'A'
  let loading = $state(false);
  let fontName = $state(DEFAULT_FONT_NAME);
  let showColorPalette = $state(false);
  let sidebarOpen = $state(true);
  let gridSize = $state(DEFAULT_GRID_SIZE); // Default: 24x24 monosorts square
  let loadedFontName = $state<string | null>(null);
  let sidebarTab = $state<"library" | "export">("library");
  let darkMode = $state(false);
  let copyNotification = $state<string | null>(null);

  // Computed font-family with emoji fallback
  let fontFamily = $derived.by(() => {
    if (!loadedFontName) return "monospace";

    // For emoji/color fonts, add system emoji fallbacks
    if (selectedCollection.type === "color") {
      return `'${loadedFontName}', 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', 'Segoe UI Symbol', sans-serif`;
    }

    return `'${loadedFontName}', monospace`;
  });

  const gridSizes = [
    { size: 24, label: "24×24" },
    { size: 48, label: "48×48" },
  ];

  $effect(() => {
    showColorPalette = selectedCollection.type === "color";
  });

  // Dark mode is applied globally via styleManager/layout
  import { getStyleState } from "$lib/services/styleManager";
  $effect(() => {
    darkMode = getStyleState().darkMode;
  });

  // Function to log current state for debugging (captured by debug panel)
  const logPixelEditorState = () => {
    console.group("🎨 Pixel Editor State");
    console.log("Dark Mode:", darkMode);
    console.log("Characters Loaded:", characters.length);
    console.log("Current Font:", loadedFontName);
    console.log("Collection:", selectedCollection.name);
    console.log("Grid Size:", gridSize + "x" + gridSize);
    console.log("Sidebar Open:", sidebarOpen);
    console.log(
      "Current Character:",
      currentCharacter
        ? `${currentCharacter.char} (U+${currentCharacter.code.toString(16)})`
        : "None"
    );
    console.log("Character Set Type:", selectedCollection.characterSet.type);
    console.log(
      "Available Codes:",
      selectedCollection.characterSet.codes?.length ?? "n/a"
    );
    console.log(
      "HTML Classes:",
      document.documentElement.className || "(none)"
    );
    console.groupEnd();
  };

  const toggleSidebar = () => {
    sidebarOpen = !sidebarOpen;
  };

  const handleCollectionChange = async (e: Event) => {
    const target = e.target as HTMLSelectElement;
    const index = parseInt(target.value);
    selectedCollectionIndex = index;
    await loadFontData();
  };

  const handleGridSizeChange = async (e: Event) => {
    const target = e.target as HTMLSelectElement;
    gridSize = parseInt(target.value);
    await loadFontData();
  };

  const loadFontData = async () => {
    loading = true;
    try {
      console.log(
        `[PixelEditor] Loading font: ${selectedCollection.name}, type: ${selectedCollection.type}, path: ${selectedCollection.path}`
      );

      console.log(
        "[PixelEditor] Character set codes:",
        selectedCollection.characterSet.codes
      );
      console.log(
        "[PixelEditor] Character set codes length:",
        selectedCollection.characterSet.codes?.length
      );

      // For emoji collections, let's see if the codes are being used correctly
      if (selectedCollection.characterSet.type === "emoji") {
        console.log("[PixelEditor] EMOJI COLLECTION DETECTED!");
        console.log(
          "[PixelEditor] First 5 emoji codes:",
          selectedCollection.characterSet.codes.slice(0, 5)
        );
        console.log(
          "[PixelEditor] These should be emoji unicode code points like 128516 (😄)"
        );
      }

      // Load font with selected dataset codes (explicit copy to avoid reactive proxy issues)
      // Use noMargin for block graphics that should fill entire grid
      const codes = Array.isArray(selectedCollection.characterSet.codes)
        ? [...selectedCollection.characterSet.codes]
        : undefined;

      if (
        selectedCollection.characterSet.type === "emoji" &&
        (!codes || codes.length === 0)
      ) {
        throw new Error(
          `Emoji collection ${selectedCollection.id} has no character codes; refusing to load`
        );
      }
      const result = await loadFont(
        selectedCollection.path,
        gridSize,
        codes,
        selectedCollection.characterSet.noMargin || false
      );
      characters = result.characters;
      console.log(`[PixelEditor] Loaded ${characters.length} characters`);
      console.log(`[PixelEditor] Font name from loader: ${result.fontName}`);
      console.log(
        `[PixelEditor] Codes (copy) length used: ${codes ? codes.length : 0}`
      );

      // Add ASCII mappings from dataset
      characters = characters.map((char) => ({
        ...char,
        asciiMapping: getAsciiMapping(
          char.code,
          selectedCollection.characterSet
        ),
      }));

      loadedFontName = result.fontName;
      if (characters.length > 0) {
        selectCharacter(characters[0]);
      }
    } catch (error) {
      console.error("Error loading font:", error);
      copyNotification = "❌ Failed to load font - Check console";
      setTimeout(() => (copyNotification = null), 3000);
    } finally {
      loading = false;
    }
  };

  const selectCharacter = (char: CharacterData) => {
    currentCharacter = char;
    pixelData = char.pixels;
    asciiCode = char.code;
    // Update grid size if character has different size
    if (char.width !== gridSize) {
      gridSize = char.width;
    }
  };

  const handlePixelChange = (data: boolean[][] | (number | null)[][]) => {
    pixelData = data;
    if (currentCharacter) {
      currentCharacter.pixels = data;
    }
  };

  const handleColorChange = (color: string) => {
    selectedColor = color;
  };

  const saveCharacter = () => {
    if (!currentCharacter) return;

    // Update the character in the library
    const index = characters.findIndex(
      (c) => c.code === currentCharacter!.code
    );
    moveLogger.success("Save Character", `ASCII ${asciiCode}`);
    copyNotification = `✅ Character '${String.fromCharCode(asciiCode)}' (ASCII ${asciiCode}) saved!`;
    setTimeout(() => (copyNotification = null), 2000);
  };

  const handleExport = async () => {
    try {
      loading = true;
      await exportFont(characters, fontName);
      copyNotification = `✅ Font exported as ${fontName}.ttf - Grid: ${gridSize}×${gridSize}`;
      setTimeout(() => (copyNotification = null), 3000);
    } catch (error) {
      console.error("Export error:", error);
      copyNotification = "❌ Failed to export font";
      setTimeout(() => (copyNotification = null), 3000);
    } finally {
      loading = false;
    }
  };

  const newCharacter = () => {
    const newChar: CharacterData = {
      code: asciiCode,
      char: String.fromCharCode(asciiCode),
      pixels: Array(gridSize)
        .fill(null)
        .map(() => Array(gridSize).fill(false)),
      width: gridSize,
      height: gridSize,
    };
    characters = [...characters, newChar];
    selectCharacter(newChar);
    moveLogger.action(
      "New Character",
      `ASCII ${asciiCode}, ${gridSize}x${gridSize}`
    );
  };

  const clearGrid = () => {
    pixelData = Array(gridSize)
      .fill(null)
      .map(() => Array(gridSize).fill(false));
    moveLogger.action("Clear Grid", `${gridSize}x${gridSize}`);
  };

  const invertGrid = () => {
    pixelData = pixelData.map((row) => row.map((pixel) => !pixel));
    moveLogger.action("Invert Grid");
  };

  const resetDisplay = async () => {
    // Reset to default values
    selectedCollectionIndex = DEFAULT_COLLECTION_INDEX;
    gridSize = DEFAULT_GRID_SIZE;
    asciiCode = DEFAULT_ASCII_CODE;
    fontName = DEFAULT_FONT_NAME;
    selectedColor = "#000000";
    sidebarTab = "library";
    sidebarOpen = true;

    // Reset pixel grid to blank
    pixelData = Array(DEFAULT_GRID_SIZE)
      .fill(null)
      .map(() => Array(DEFAULT_GRID_SIZE).fill(false));

    // Clear current character selection
    currentCharacter = null;

    // Reload font data with defaults
    await loadFontData();
  };

  // Debug: quickly switch to emoji collections
  const switchToCollection = async (id: string) => {
    const idx = FONT_COLLECTIONS.findIndex((fc) => fc.id === id);
    if (idx >= 0) {
      selectedCollectionIndex = idx;
      await loadFontData();
    } else {
      console.warn(`[PixelEditor] Collection not found: ${id}`);
    }
  };

  onMount(() => {
    console.log("[PixelEditor] Starting mount...");

    // Load dark mode from state
    const pixelEditorState = getStateForMode("pixel-editor");
    darkMode = pixelEditorState.darkMode || false;
    sidebarOpen =
      pixelEditorState.sidebarOpen !== undefined
        ? pixelEditorState.sidebarOpen
        : true;

    // Apply dark mode explicitly
    console.log("[PixelEditor] Initializing dark mode:", darkMode);
    document.documentElement.classList.remove("light", "dark");
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.add("light");
    }
    console.log(
      "[PixelEditor] HTML classes:",
      document.documentElement.className
    );

    // Load fonts asynchronously - don't block
    console.log("[PixelEditor] Starting font load...");
    loadFontData()
      .then(() => {
        console.log("[PixelEditor] Fonts loaded successfully");
      })
      .catch((error) => {
        console.error("[PixelEditor] Font load failed:", error);
        copyNotification =
          "❌ Font loading failed - see browser console (Cmd+Option+I)";
        setTimeout(() => (copyNotification = null), 5000);
      });

    // Listen for toggle-sidebar event from bottom bar
    const setupListeners = async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");

        const unlistenSidebar = await listen("toggle-sidebar", (event: any) => {
          sidebarOpen = event.payload.open;
          updateModeState("pixel-editor", { sidebarOpen: event.payload.open });
        });

        const unlistenReset = await listen("reset-mode-display", async () => {
          await resetDisplay();
        });

        const unlistenDarkMode = await listen(
          "toggle-dark-mode",
          (event: any) => {
            darkMode = event.payload.enabled;
            // Layout/styleManager applies dark mode globally
            updateModeState("pixel-editor", { darkMode });
          }
        );

        return [unlistenSidebar, unlistenReset, unlistenDarkMode];
      } catch (error) {
        console.error("[PixelEditor] Failed to setup event listeners:", error);
        return [];
      }
    };

    let unlisteners: (() => void)[] = [];
    setupListeners().then((fns) => (unlisteners = fns));

    return () => {
      unlisteners.forEach((fn) => fn());
    };
  });
</script>

<!-- Copy notification - Use F12 for full debug panel -->
{#if copyNotification}
  <div
    class="fixed top-4 right-4 bg-green-500 text-white p-2 text-xs z-40 rounded shadow-lg"
  >
    {copyNotification}
  </div>
{/if}

<div
  class="flex flex-col h-full bg-gray-100 text-gray-900 dark:bg-gray-900 dark:text-gray-100 transition-colors duration-200"
  class:dark={darkMode}
  data-theme={darkMode ? "dark" : "light"}
>
  <!-- Main Content - Two Panel Layout -->
  <div class="flex-1 flex overflow-hidden">
    <!-- Left Sidebar (Library / Export Tabs) -->
    {#if sidebarOpen}
      <aside
        class="w-80 bg-gray-200 border-gray-300 dark:bg-gray-800 dark:border-gray-700 border-r shrink-0 flex flex-col overflow-hidden"
      >
        <!-- Tab Switcher -->
        <div
          class="flex border-gray-300 dark:border-gray-700 border-b shrink-0"
        >
          <button
            onclick={() => (sidebarTab = "library")}
            class="flex-1 px-4 py-3 text-sm font-medium transition-colors {sidebarTab ===
            'library'
              ? 'bg-white text-blue-600 dark:bg-gray-900 dark:text-blue-400 border-b-2 border-blue-500'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:bg-gray-800'}"
          >
            Character Library
          </button>
          <button
            onclick={() => (sidebarTab = "export")}
            class="flex-1 px-4 py-3 text-sm font-medium transition-colors {sidebarTab ===
            'export'
              ? 'bg-white text-purple-600 dark:bg-gray-900 dark:text-purple-400 border-b-2 border-purple-500'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:bg-gray-800'}"
          >
            Export Font
          </button>
        </div>

        <!-- Tab Content -->
        <div class="flex-1 overflow-y-auto pb-6">
          {#if sidebarTab === "library"}
            <!-- Character Library Tab -->
            <div class="p-4 space-y-4">
              <!-- Font Collection Selector -->
              <div
                class="p-3 bg-white dark:bg-gray-900 rounded border border-gray-300 dark:border-gray-700"
              >
                <label
                  for="collection-select"
                  class="block text-xs font-semibold mb-2 text-gray-700 dark:text-gray-400 uppercase tracking-wide"
                  >Font + Character Set:</label
                >
                <select
                  id="collection-select"
                  value={selectedCollectionIndex}
                  onchange={handleCollectionChange}
                  class="w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {#each FONT_COLLECTIONS as collection, i}
                    <option value={i}>
                      {collection.name} ({collection.characterSet.codes.length})
                    </option>
                  {/each}
                </select>
                <p class="text-xs text-gray-600 dark:text-gray-500 mt-2">
                  {selectedCollection.description}
                </p>
              </div>

              <!-- Grid Size Selector -->
              <div
                class="p-3 bg-white dark:bg-gray-900 rounded border border-gray-300 dark:border-gray-700"
              >
                <label
                  for="grid-size"
                  class="block text-xs font-semibold mb-2 text-gray-700 dark:text-gray-400 uppercase tracking-wide"
                  >Grid Size:</label
                >
                <select
                  id="grid-size"
                  value={gridSize}
                  onchange={handleGridSizeChange}
                  class="w-full bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {#each gridSizes as gs}
                    <option value={gs.size}>{gs.label}</option>
                  {/each}
                </select>
              </div>

              <!-- Emoji Library Import -->
              <!-- Collection Info -->
              <div
                class="p-3 bg-white dark:bg-gray-900 rounded border border-gray-300 dark:border-gray-700"
              >
                <div
                  class="block text-xs font-semibold mb-2 text-gray-700 dark:text-gray-400 uppercase tracking-wide"
                  >Current Collection:</div
                >
                <div class="text-sm text-gray-900 dark:text-gray-300">
                  <strong>{selectedCollection.name}</strong>
                  <br />
                  <span class="text-gray-700 dark:text-gray-400"
                    >{selectedCollection.description}</span
                  >
                  <br />
                  <span class="text-xs text-gray-600 dark:text-gray-500">
                    {characters.length} characters loaded
                  </span>
                </div>
              </div>

              <div class="flex items-center justify-between mb-2">
                <h3
                  class="text-sm font-semibold text-gray-900 dark:text-gray-300 uppercase tracking-wide"
                >
                  Library ({characters.length})
                </h3>
                <button
                  onclick={newCharacter}
                  class="px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-xs font-medium transition-colors"
                  title="Create new character"
                >
                  + New
                </button>
              </div>
              {#if loading}
                <div class="text-center py-8 text-gray-600 dark:text-gray-400">
                  Loading...
                </div>
              {:else}
                <CharacterLibrary
                  {characters}
                  {currentCharacter}
                  onSelect={selectCharacter}
                  {fontFamily}
                  {gridSize}
                  fontType={selectedCollection.type}
                />
              {/if}
            </div>
          {:else}
            <!-- Export Tab -->
            <div class="p-4 space-y-6">
              <!-- ASCII Code Selector -->
              <div class="p-4 bg-gray-900 rounded border border-gray-700">
                <h4
                  class="text-xs font-semibold mb-3 text-gray-400 uppercase tracking-wide"
                >
                  ASCII Mapping
                </h4>
                <div class="flex items-center gap-2 mb-3">
                  <label
                    for="ascii-input"
                    class="text-sm font-medium text-gray-300">Code:</label
                  >
                  <input
                    id="ascii-input"
                    type="number"
                    bind:value={asciiCode}
                    min="32"
                    max="126"
                    class="bg-gray-700 text-gray-100 border border-gray-600 rounded px-3 py-1 w-20 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <span
                    class="text-2xl font-mono bg-gray-700 px-3 py-1 rounded border border-gray-600"
                  >
                    {String.fromCharCode(asciiCode)}
                  </span>
                </div>
                <!-- Block Graphics Reference -->
                <div class="grid grid-cols-8 gap-1 text-xs font-mono">
                  {#each Array.from({ length: 95 }, (_, i) => i + 32) as code}
                    <button
                      onclick={() => (asciiCode = code)}
                      class="aspect-square bg-gray-800 hover:bg-gray-700 border border-gray-700 flex items-center justify-center transition-colors"
                      class:ring-2={code === asciiCode}
                      class:ring-blue-500={code === asciiCode}
                      title={`ASCII ${code}`}
                    >
                      {String.fromCharCode(code)}
                    </button>
                  {/each}
                </div>
              </div>

              <!-- Export Panel -->
              <div class="p-4 bg-gray-900 rounded border border-gray-700">
                <h4
                  class="text-xs font-semibold mb-2 text-gray-400 uppercase tracking-wide"
                >
                  Compile Monosorts Font
                </h4>
                <p class="text-xs text-gray-500 mb-4">
                  Exports TTF for use in Teledesk, Terminal, and other OS
                  systems
                </p>

                <div class="space-y-4">
                  <div>
                    <label
                      for="font-name"
                      class="block text-sm font-medium text-gray-300 mb-2"
                    >
                      Font Name:
                    </label>
                    <input
                      id="font-name"
                      type="text"
                      bind:value={fontName}
                      class="w-full bg-gray-700 text-gray-100 border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="CustomFont"
                    />
                  </div>

                  <div class="p-3 bg-gray-800 rounded border border-gray-700">
                    <div class="text-xs text-gray-400 space-y-1">
                      <div class="flex justify-between">
                        <span>Grid Size:</span>
                        <span class="font-mono text-purple-400"
                          >{gridSize}×{gridSize}</span
                        >
                      </div>
                      <div class="flex justify-between">
                        <span>Format:</span>
                        <span class="font-mono text-purple-400">TTF</span>
                      </div>
                      <div class="flex justify-between">
                        <span>Characters:</span>
                        <span class="font-mono text-purple-400"
                          >{characters.length}</span
                        >
                      </div>
                      <div class="flex justify-between">
                        <span>Type:</span>
                        <span class="font-mono text-purple-400">Monosorts</span>
                      </div>
                    </div>
                  </div>

                  <button
                    onclick={handleExport}
                    disabled={loading || characters.length === 0}
                    class="w-full px-4 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded font-medium transition-colors"
                  >
                    {loading ? "Compiling..." : "Export TTF"}
                  </button>

                  <button
                    onclick={logPixelEditorState}
                    class="w-full mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded font-medium text-sm transition-colors"
                    title="Log current state to console (visible in F12 debug panel)"
                  >
                    🐛 Debug Log
                  </button>
                </div>

                <!-- Info -->
                <div class="mt-4 text-xs text-gray-400">
                  <h5 class="font-semibold mb-2 text-gray-300">Workflow:</h5>
                  <ul class="space-y-1">
                    <li>• Draft fonts compile to Downloads</li>
                    <li>• Move to memory/sandbox/drafts</li>
                    <li>• Install from memory/user/fonts</li>
                    <li>• Use in Terminal & Teledesk grids</li>
                  </ul>
                </div>
              </div>
            </div>
          {/if}
        </div>
      </aside>
    {/if}

    <!-- Right Panel (Grid Editor + Character Library) -->
    <main class="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900">
      <!-- Toolbar -->
      <div
        class="bg-gray-200 border-gray-300 dark:bg-gray-800 dark:border-gray-700 border-b p-3 shrink-0"
      >
        <div class="flex flex-wrap gap-3 items-center justify-between">
          <div class="flex gap-2">
            <UButton
              variant="secondary"
              size="sm"
              onclick={clearGrid}

            >
              Clear
            </UButton>
            <UButton
              variant="secondary"
              size="sm"
              onclick={invertGrid}

            >
              Invert
            </UButton>
            <UButton
              variant="primary"
              size="sm"
              onclick={saveCharacter}
              disabled={!currentCharacter}
            >
              Save Character
            </UButton>
            <UButton
              variant="success"
              size="sm"
              onclick={newCharacter}

            >
              + New
            </UButton>
          </div>

          {#if currentCharacter}
            <div
              class="text-sm text-gray-700 dark:text-gray-300 flex items-center gap-4"
            >
              <div>
                Editing: <span
                  class="font-mono text-lg px-2 bg-gray-300 dark:bg-gray-700 rounded"
                >
                  {currentCharacter.char}</span
                >
                <span class="text-gray-600 dark:text-gray-500"
                  >ASCII {currentCharacter.code}</span
                >
              </div>
              <div
                class="text-xs text-gray-600 dark:text-gray-500 border-gray-400 dark:border-gray-600 border-l pl-4"
              >
                {gridSize}×{gridSize} monosorts • Click to toggle • Drag to draw
              </div>
            </div>
          {/if}
        </div>
      </div>

      <!-- Grid + Preview Area -->
      <div
        class="flex-1 flex flex-col overflow-auto bg-gray-50 dark:bg-gray-900 p-4"
      >
        <!-- Pixel Grid Editor -->
        <div class="w-full flex flex-col items-center">
          <div class="flex justify-center mb-4">
            <PixelGrid
              pixels={pixelData}
              color={selectedColor}
              onChange={handlePixelChange}
            />
          </div>

          {#if showColorPalette}
            <div class="mb-4 flex justify-center">
              <ColorPalette {selectedColor} onChange={handleColorChange} />
            </div>
          {/if}

          <!-- Preview -->
          <div
            class="bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700 p-4 rounded border"
          >
            <div
              class="text-xs text-gray-600 dark:text-gray-400 mb-3 uppercase tracking-wide text-center"
            >
              Preview - {selectedCollection.name}
            </div>
            <div class="flex gap-6 items-center justify-center">
              <div class="text-6xl" style="font-family: {fontFamily}">
                {String.fromCharCode(asciiCode)}
              </div>
              <div class="text-4xl" style="font-family: {fontFamily}">
                {String.fromCharCode(asciiCode)}
              </div>
              <div class="text-2xl" style="font-family: {fontFamily}">
                {String.fromCharCode(asciiCode)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</div>

<style>
  :global(body) {
    overflow: hidden;
  }
</style>
