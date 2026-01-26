<script lang="ts">
  /**
   * CoreMapBrowser - Browse and import maps from /core/data/maps/layers
   */

  import { onMount } from "svelte";
  import {
    listCoreMapLayers,
    convertCoreMapToLayer,
    getCoreMapLegend,
    type CoreMapInfo,
    type TerrainType,
  } from "$lib/services/coreMapService";
  import type { Layer } from "$lib/types/layer";

  interface Props {
    onImport?: (layer: Layer) => void;
  }

  let { onImport }: Props = $props();

  let maps = $state<CoreMapInfo[]>([]);
  let selectedMap = $state<CoreMapInfo | null>(null);
  let legend = $state<Record<string, TerrainType>>({});
  let loading = $state(false);
  let importing = $state(false);

  // Import options
  let targetWidth = $state(60);
  let targetHeight = $state(20);

  onMount(async () => {
    await loadMaps();
  });

  async function loadMaps() {
    loading = true;
    try {
      maps = await listCoreMapLayers();
    } catch (e) {
      console.error("Failed to load core maps:", e);
    } finally {
      loading = false;
    }
  }

  async function selectMap(map: CoreMapInfo) {
    selectedMap = map;

    // Load legend for preview
    try {
      legend = await getCoreMapLegend(map.filename);
    } catch (e) {
      console.error("Failed to load legend:", e);
      legend = {};
    }
  }

  async function importMap() {
    if (!selectedMap) return;

    importing = true;
    try {
      const layer = await convertCoreMapToLayer(selectedMap.filename, {
        targetWidth,
        targetHeight,
      });

      onImport?.(layer);
    } catch (e) {
      console.error("Failed to import map:", e);
      alert(`Failed to import map: ${e}`);
    } finally {
      importing = false;
    }
  }
</script>

<div
  class="core-map-browser h-full flex flex-col bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
>
  <div class="p-4 border-b border-gray-300 dark:border-gray-700">
    <h3 class="text-sm font-semibold mb-2">Core Map Layers</h3>
    <p class="text-xs text-gray-600 dark:text-gray-400">
      Geographic data from <code>/core/data/maps/layers</code>
    </p>
  </div>

  <div class="flex-1 overflow-y-auto p-4">
    {#if loading}
      <div class="text-center py-8 text-gray-500">Loading map layers...</div>
    {:else if maps.length === 0}
      <div class="text-center py-8 text-gray-500">No core maps found</div>
    {:else}
      <div class="space-y-2">
        {#each maps as map}
          <button
            onclick={() => selectMap(map)}
            class="w-full text-left p-3 rounded border transition-colors"
            class:border-cyan-500={selectedMap?.filename === map.filename}
            class:bg-cyan-50={selectedMap?.filename === map.filename}
            class:dark:bg-cyan-950={selectedMap?.filename === map.filename}
            class:border-gray-300={selectedMap?.filename !== map.filename}
            class:dark:border-gray-700={selectedMap?.filename !== map.filename}
            class:hover:bg-gray-50={selectedMap?.filename !== map.filename}
            class:dark:hover:bg-gray-800={selectedMap?.filename !==
              map.filename}
          >
            <div class="font-medium text-sm">{map.name}</div>
            <div class="text-xs text-gray-600 dark:text-gray-400 mt-1">
              {map.description}
            </div>
            <div class="text-xs text-gray-500 mt-1">
              {map.size.width}×{map.size.height} • {map.resolution}
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </div>

  {#if selectedMap}
    <div class="border-t border-gray-300 dark:border-gray-700 p-4">
      <h4 class="text-xs font-semibold mb-2">Import Options</h4>

      <div class="space-y-2 mb-3">
        <label class="block text-xs">
          <span class="text-gray-600 dark:text-gray-400">Target Width:</span>
          <input
            type="number"
            bind:value={targetWidth}
            min="10"
            max="200"
            class="w-full mt-1 px-2 py-1 text-xs border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800"
          />
        </label>
        <label class="block text-xs">
          <span class="text-gray-600 dark:text-gray-400">Target Height:</span>
          <input
            type="number"
            bind:value={targetHeight}
            min="10"
            max="100"
            class="w-full mt-1 px-2 py-1 text-xs border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800"
          />
        </label>
      </div>

      {#if Object.keys(legend).length > 0}
        <div class="mb-3">
          <h5 class="text-xs font-semibold mb-1">Terrain Legend:</h5>
          <div class="grid grid-cols-2 gap-1 text-xs">
            {#each Object.entries(legend) as [name, terrain]}
              <div class="flex items-center gap-1">
                <span
                  class="w-4 h-4 flex items-center justify-center font-mono text-xs"
                  style="color: {terrain.color}"
                >
                  {terrain.symbol}
                </span>
                <span class="text-gray-600 dark:text-gray-400">{name}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <button
        onclick={importMap}
        disabled={importing}
        class="w-full px-4 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:bg-gray-400 text-white rounded text-sm font-medium transition-colors"
      >
        {importing ? "Importing..." : "Import as New Layer"}
      </button>

      <p class="text-xs text-gray-500 mt-2 text-center">
        Original: {selectedMap.size.width}×{selectedMap.size.height} → Target: {targetWidth}×{targetHeight}
      </p>
    </div>
  {/if}
</div>

<style>
  code {
    font-family: var(--font-family-mono);
    font-size: 0.9em;
    padding: 0.1em 0.3em;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 3px;
  }

  :global(.dark) code {
    background: rgba(255, 255, 255, 0.05);
  }
</style>
