<script lang="ts">
  import { onMount } from "svelte";
  import TileGrid from "$lib/components/TileGrid.svelte";
  import LayerPanel from "$lib/components/LayerPanel.svelte";
  import CharacterPalette from "$lib/components/CharacterPalette.svelte";
  import TileLinker from "$lib/components/TileLinker.svelte";
  import CoreMapBrowser from "$lib/components/CoreMapBrowser.svelte";
  import MapLayerBrowser from "$lib/components/MapLayerBrowser.svelte";
  import type { Layer, Tile, MapDocument, TileLink } from "$lib/types/layer";
  import { createMapDocument, createEmptyTile } from "$lib/types/layer";
  import {
    addLayer,
    removeLayer,
    duplicateLayer,
    updateLayer,
    moveLayer,
    setTile,
    addTileLink,
    removeTileLink,
  } from "$lib/util/layerManager";
  import {
    saveMapDocument,
    loadMapDocument,
    exportMapAsText,
    exportMapAsMarkdown,
    DEFAULT_PATHS,
    generateFilename,
  } from "$lib/util/layerPersistence";
  import { getStateForMode, updateModeState } from "$lib/stores/modeState";
  import { getStyleState } from "$lib/services/styleManager";
  import { UButton, moveLogger } from "$lib";
  import { toastStore } from "$lib/stores/toastStore";

  // Default map dimensions
  const DEFAULT_WIDTH = 60;
  const DEFAULT_HEIGHT = 20;

  // State
  let document = $state<MapDocument>(
    createMapDocument("Untitled Map", DEFAULT_WIDTH, DEFAULT_HEIGHT)
  );
  let selectedChar = $state("█");
  let selectedCode = $state(0x2588);
  let fgColor = $state("#ffffff");
  let bgColor = $state("#000000");
  let tool = $state<"draw" | "erase" | "fill" | "select" | "link">("draw");
  let showGrid = $state(true);
  let showLinks = $state(true);
  let zoom = $state(1.0);
  let sidebarOpen = $state(true);
  let sidebarTab = $state<"layers" | "palette">("palette");
  let mapLayerPickerOpen = $state(true);
  let darkMode = $state(false);
  let showLinker = $state(false);
  let linkerTile = $state<{ tile: Tile; row: number; col: number } | null>(
    null
  );
  let loading = $state(false);
  let lastSavedPath = $state<string | null>(null);

  // Get active layer
  const activeLayer = $derived.by(() => {
    return (
      document.layers.find((l) => l.id === document.activeLayerId) ||
      document.layers[0]
    );
  });

  // Dark mode is handled globally by layout/styleManager

  // Tool handlers
  const handleTileChange = (row: number, col: number, tile: Tile) => {
    if (!activeLayer || activeLayer.locked) return;

    const updatedLayer = setTile(activeLayer, row, col, tile);
    document = updateLayer(document, activeLayer.id, updatedLayer);
  };

  const handleTileClick = (row: number, col: number, tile: Tile) => {
    if (tool === "link") {
      linkerTile = { tile, row, col };
      showLinker = true;
    }
  };

  const handleCharacterSelect = (char: string, code: number) => {
    selectedChar = char;
    selectedCode = code;
    tool = "draw";
  };

  // Layer management
  const handleAddLayer = () => {
    const name = prompt("Layer name:", `Layer ${document.layers.length + 1}`);
    if (name) {
      document = addLayer(document, name);
    }
  };

  const handleRemoveLayer = (layerId: string) => {
    if (document.layers.length === 1) {
      toastStore.warning("Cannot delete the last layer");
      return;
    }
    if (confirm("Delete this layer?")) {
      document = removeLayer(document, layerId);
    }
  };

  const handleDuplicateLayer = (layerId: string) => {
    document = duplicateLayer(document, layerId);
  };

  const handleSelectLayer = (layerId: string) => {
    document.activeLayerId = layerId;
  };

  const handleMoveLayer = (layerId: string, direction: "up" | "down") => {
    document = moveLayer(document, layerId, direction);
  };

  const handleToggleVisibility = (layerId: string) => {
    const layer = document.layers.find((l) => l.id === layerId);
    if (layer) {
      document = updateLayer(document, layerId, { visible: !layer.visible });
    }
  };

  const handleToggleLock = (layerId: string) => {
    const layer = document.layers.find((l) => l.id === layerId);
    if (layer) {
      document = updateLayer(document, layerId, { locked: !layer.locked });
    }
  };

  const handleRenameLayer = (layerId: string, newName: string) => {
    document = updateLayer(document, layerId, { name: newName });
  };

  const handleUpdateOpacity = (layerId: string, opacity: number) => {
    document = updateLayer(document, layerId, { opacity });
  };

  // Import handler for core maps
  const handleImportCoreMap = (layer: Layer) => {
    // Add the imported layer to the document
    document = {
      ...document,
      layers: [...document.layers, layer],
      activeLayerId: layer.id,
    };

    // Switch to layers tab to see the new layer
    sidebarTab = "layers";

    console.log(`[Layer Editor] Imported core map layer: ${layer.name}`);
  };

  // Load core map layer from file picker
  const handleLoadMapLayer = async (filename: string, metadata: any) => {
    try {
      // For now, just log - would integrate with actual map loading
      console.log(`[Layer Editor] Loading map layer: ${filename}`, metadata);
      toastStore.success(`Loaded: ${metadata.layer_name}`);
    } catch (error) {
      toastStore.error(`Failed to load map layer: ${error}`);
    }
  };

  // Tile linking
  const handleSaveLink = (link: TileLink | null) => {
    if (!linkerTile || !activeLayer) return;

    const { row, col } = linkerTile;

    if (link) {
      const updatedLayer = addTileLink(activeLayer, row, col, link);
      document = updateLayer(document, activeLayer.id, updatedLayer);
    } else {
      const updatedLayer = removeTileLink(activeLayer, row, col);
      document = updateLayer(document, activeLayer.id, updatedLayer);
    }

    showLinker = false;
    linkerTile = null;
  };

  // File operations
  const handleSave = async () => {
    try {
      loading = true;
      const path =
        lastSavedPath ||
        `${DEFAULT_PATHS.sandbox}${generateFilename(document.name)}`;
      await saveMapDocument(document, path);
      lastSavedPath = path;
      toastStore.success(`Map saved to ${path}`);
    } catch (error) {
      toastStore.error(`Failed to save: ${error}`);
    } finally {
      loading = false;
    }
  };

  const handleSaveAs = async () => {
    const filename = prompt("Filename:", generateFilename(document.name));
    if (!filename) return;

    const location = confirm("Save to sandbox? (Cancel for core maps)");
    const basePath = location ? DEFAULT_PATHS.sandbox : DEFAULT_PATHS.core;
    const path = `${basePath}${filename}`;

    try {
      loading = true;
      await saveMapDocument(document, path);
      lastSavedPath = path;
      toastStore.success(`Map saved to ${path}`);
    } catch (error) {
      toastStore.error(`Failed to save: ${error}`);
    } finally {
      loading = false;
    }
  };

  const handleLoad = async () => {
    const path = prompt("Path to map file (relative to memory/):");
    if (!path) return;

    try {
      loading = true;
      document = await loadMapDocument(
        `/Users/fredbook/Code/uDOS/memory/${path}`
      );
      lastSavedPath = `/Users/fredbook/Code/uDOS/memory/${path}`;
      toastStore.success("Map loaded successfully");
    } catch (error) {
      toastStore.error(`Failed to load: ${error}`);
    } finally {
      loading = false;
    }
  };

  const handleExportText = () => {
    const text = exportMapAsText(document);
    navigator.clipboard.writeText(text);
    toastStore.success("Map exported as text to clipboard");
  };

  const handleExportMarkdown = () => {
    const md = exportMapAsMarkdown(document);
    navigator.clipboard.writeText(md);
    toastStore.success("Map exported as Markdown to clipboard");
  };

  const handleNew = () => {
    if (confirm("Create new map? Unsaved changes will be lost.")) {
      const name = prompt("Map name:", "New Map");
      if (name) {
        document = createMapDocument(name, DEFAULT_WIDTH, DEFAULT_HEIGHT);
        lastSavedPath = null;
      }
    }
  };

  // Keyboard shortcuts
  const handleKeydown = (e: KeyboardEvent) => {
    // Cmd/Ctrl + S: Save
    if ((e.metaKey || e.ctrlKey) && e.key === "s") {
      e.preventDefault();
      handleSave();
    }
    // Cmd/Ctrl + N: New
    if ((e.metaKey || e.ctrlKey) && e.key === "n") {
      e.preventDefault();
      handleNew();
    }
    // D: Draw tool
    if (e.key === "d" && !e.metaKey && !e.ctrlKey) {
      tool = "draw";
    }
    // E: Erase tool
    if (e.key === "e" && !e.metaKey && !e.ctrlKey) {
      tool = "erase";
    }
    // L: Link tool
    if (e.key === "l" && !e.metaKey && !e.ctrlKey) {
      tool = "link";
    }
    // G: Toggle grid
    if (e.key === "g" && !e.metaKey && !e.ctrlKey) {
      showGrid = !showGrid;
    }
  };

  onMount(() => {
    // Load state
    const state = getStateForMode("layer-editor");
    darkMode = state.darkMode ?? getStyleState().darkMode;
    sidebarOpen = state.sidebarOpen !== undefined ? state.sidebarOpen : true;

    // Dark mode applied globally by layout/styleManager
    // Listen for events
    const setupListeners = async () => {
      const { listen } = await import("@tauri-apps/api/event");

      const unlistenSidebar = await listen("toggle-sidebar", (event: any) => {
        sidebarOpen = event.payload.open;
        updateModeState("layer-editor", { sidebarOpen: event.payload.open });
      });

      const unlistenDark = await listen("toggle-dark-mode", async () => {
        darkMode = !darkMode;
        updateModeState("layer-editor", { darkMode });
      });

      return () => {
        unlistenSidebar();
        unlistenDark();
      };
    };

    setupListeners();
  });
</script>

<svelte:window onkeydown={handleKeydown} />

<div
  class="layer-editor w-screen h-screen flex flex-col bg-gray-100 dark:bg-slate-950 text-gray-900 dark:text-slate-100"
  class:dark={darkMode}
>
  <!-- Top toolbar -->
  <div
    class="flex justify-between items-center px-4 py-2 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-gray-700 gap-3"
  >
    <div class="flex items-center gap-2">
      <h2 class="text-base font-semibold">{document.name}</h2>
      {#if lastSavedPath}
        <span class="text-xs text-gray-500 dark:text-gray-400"
          >{lastSavedPath}</span
        >
      {/if}
    </div>

    <div class="flex items-center gap-2">
      <!-- File operations -->
      <button
        class="px-3 py-1.5 text-xs border rounded hover:bg-gray-100 dark:hover:bg-gray-800"
        onclick={handleNew}
        title="New Map (Cmd+N)"
      >
        📄 New
      </button>
      <button
        class="px-3 py-1.5 text-xs border rounded hover:bg-gray-100 dark:hover:bg-gray-800"
        onclick={handleLoad}
        title="Load Map"
      >
        📂 Load
      </button>
      <button
        class="px-3 py-1.5 text-xs border rounded hover:bg-gray-100 dark:hover:bg-gray-800"
        onclick={handleSave}
        title="Save (Cmd+S)"
      >
        💾 Save
      </button>

      <div class="w-px bg-gray-300 dark:bg-gray-600"></div>

      <!-- Tools -->
      <button
        class="px-3 py-1.5 text-xs border rounded"
        class:bg-cyan-500={tool === "draw"}
        class:text-white={tool === "draw"}
        class:hover:bg-gray-100={tool !== "draw"}
        class:dark:hover:bg-gray-800={tool !== "draw"}
        onclick={() => (tool = "draw")}
        title="Draw (D)"
      >
        ✏️ Draw
      </button>
      <button
        class="px-3 py-1.5 text-xs border rounded"
        class:bg-cyan-500={tool === "erase"}
        class:text-white={tool === "erase"}
        class:hover:bg-gray-100={tool !== "erase"}
        class:dark:hover:bg-gray-800={tool !== "erase"}
        onclick={() => (tool = "erase")}
        title="Erase (E)"
      >
        🧹 Erase
      </button>
      <button
        class="px-3 py-1.5 text-xs border rounded"
        class:bg-cyan-500={tool === "link"}
        class:text-white={tool === "link"}
        class:hover:bg-gray-100={tool !== "link"}
        class:dark:hover:bg-gray-800={tool !== "link"}
        onclick={() => (tool = "link")}
        title="Link Tile (L)"
      >
        🔗 Link
      </button>

      <div class="w-px bg-gray-300 dark:bg-gray-600"></div>

      <!-- View options -->
      <UButton
        size="xs"
        variant={showGrid ? "primary" : "secondary"}
        onclick={() => {
          showGrid = !showGrid;
          moveLogger.action("Toggle Grid", showGrid ? "On" : "Off");
        }}
      >
        Grid
      </UButton>
      <UButton
        size="xs"
        variant={showLinks ? "primary" : "secondary"}
        onclick={() => {
          showLinks = !showLinks;
          moveLogger.action("Toggle Links", showLinks ? "On" : "Off");
        }}
      >
        Links
      </UButton>

      <!-- Zoom -->
      <select
        bind:value={zoom}
        class="px-2 py-1.5 text-xs border rounded bg-white dark:bg-gray-800"
      >
        <option value={0.5}>50%</option>
        <option value={0.75}>75%</option>
        <option value={1.0}>100%</option>
        <option value={1.25}>125%</option>
        <option value={1.5}>150%</option>
        <option value={2.0}>200%</option>
      </select>
    </div>
  </div>

  <!-- Main layout: File picker | Canvas | Sidebar -->
  <div class="flex flex-1 overflow-hidden">
    <!-- Left: Map Layer File Picker -->
    {#if mapLayerPickerOpen}
      <div
        class="w-64 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
      >
        <MapLayerBrowser onLoadLayer={handleLoadMapLayer} />
      </div>
    {/if}

    <!-- Center: Canvas -->
    <div class="flex-1 flex flex-col">
      {#if loading}
        <div class="flex-1 flex items-center justify-center">
          <div class="text-sm text-gray-500">Loading...</div>
        </div>
      {:else if activeLayer}
        <div class="flex-1 overflow-auto">
          <TileGrid
            layer={activeLayer}
            {selectedChar}
            {selectedCode}
            {fgColor}
            {bgColor}
            {tool}
            {showGrid}
            {showLinks}
            {zoom}
            onTileChange={handleTileChange}
            onTileClick={handleTileClick}
          />
        </div>
      {:else}
        <div class="flex-1 flex items-center justify-center">
          <div class="text-center text-gray-500">No layer selected</div>
        </div>
      {/if}
    </div>

    <!-- Right: Tools Sidebar -->
    {#if sidebarOpen}
      <div
        class="w-80 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex flex-col"
      >
        <!-- Tab bar -->
        <div class="flex border-b border-gray-200 dark:border-gray-700">
          <button
            class="flex-1 px-4 py-2 text-xs font-semibold"
            class:bg-cyan-100={sidebarTab === "layers"}
            class:dark:bg-cyan-900={sidebarTab === "layers"}
            class:text-cyan-900={sidebarTab === "layers"}
            class:dark:text-cyan-100={sidebarTab === "layers"}
            class:hover:bg-gray-100={sidebarTab !== "layers"}
            class:dark:hover:bg-gray-800={sidebarTab !== "layers"}
            onclick={() => (sidebarTab = "layers")}
          >
            Layers
          </button>
          <button
            class="flex-1 px-4 py-2 text-xs font-semibold"
            class:bg-cyan-100={sidebarTab === "palette"}
            class:dark:bg-cyan-900={sidebarTab === "palette"}
            class:text-cyan-900={sidebarTab === "palette"}
            class:dark:text-cyan-100={sidebarTab === "palette"}
            class:hover:bg-gray-100={sidebarTab !== "palette"}
            class:dark:hover:bg-gray-800={sidebarTab !== "palette"}
            onclick={() => (sidebarTab = "palette")}
          >
            Palette
          </button>
        </div>

        <!-- Tab content -->
        <div class="flex-1 overflow-y-auto">
          {#if sidebarTab === "layers"}
            <LayerPanel
              {document}
              onAddLayer={handleAddLayer}
              onRemoveLayer={handleRemoveLayer}
              onDuplicateLayer={handleDuplicateLayer}
              onSelectLayer={handleSelectLayer}
              onMoveLayer={handleMoveLayer}
              onToggleVisibility={handleToggleVisibility}
              onToggleLock={handleToggleLock}
              onRenameLayer={handleRenameLayer}
              onUpdateOpacity={handleUpdateOpacity}
            />
          {:else if sidebarTab === "palette"}
            <CharacterPalette
              bind:selectedCode
              onSelect={handleCharacterSelect}
            />
          {/if}
        </div>
      </div>
    {/if}
  </div>

  <!-- Tile linker modal -->
  {#if showLinker && linkerTile}
    <TileLinker
      tile={linkerTile.tile}
      row={linkerTile.row}
      col={linkerTile.col}
      onSaveLink={handleSaveLink}
      onClose={() => {
        showLinker = false;
        linkerTile = null;
      }}
    />
  {/if}
</div>

<style>
  :global(.dark) .layer-editor {
    background-color: rgb(15, 23, 42);
    color: rgb(241, 245, 249);
  }
</style>
