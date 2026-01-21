<script lang="ts">
  /**
   * MapLayerBrowser - File picker style panel for selecting map layers
   *
   * Shows available map layers from /core/data/maps/layers with file-browser style
   * Let's you view layer metadata, see how layers link together, and load layers
   */

  import { onMount } from "svelte";
  import { invoke } from "@tauri-apps/api/core";

  interface LayerFile {
    name: string;
    path: string;
    size: number;
    modified: string;
  }

  interface MapLayer {
    layer_id: number;
    layer_name: string;
    layer_type: string;
    description: string;
    resolution: string;
    grid_size: {
      columns: number;
      rows: number;
      total_cells: number;
    };
    [key: string]: any;
  }

  interface Props {
    onLoadLayer?: (filename: string, metadata: MapLayer) => void;
  }

  let { onLoadLayer }: Props = $props();

  let layers = $state<LayerFile[]>([]);
  let selectedFile = $state<string | null>(null);
  let selectedMetadata = $state<MapLayer | null>(null);
  let loading = $state(false);
  let linkedLayers = $state<string[]>([]);

  // Path is relative to project root, resolved by backend
  const CORE_MAPS_PATH = "core/data/maps/layers";

  onMount(async () => {
    await loadLayers();
  });

  async function loadLayers() {
    loading = true;
    try {
      const files = await invoke<string[]>("list_directory", {
        path: CORE_MAPS_PATH,
      });

      // Filter JSON files and load metadata for each
      const jsonFiles = files.filter((f) => f.endsWith(".json"));
      const layerFiles: LayerFile[] = [];

      for (const file of jsonFiles) {
        try {
          const contents = await invoke<string>("read_file", {
            path: `${CORE_MAPS_PATH}/${file}`,
          });
          const data = JSON.parse(contents);

          layerFiles.push({
            name: file,
            path: `${CORE_MAPS_PATH}/${file}`,
            size: contents.length,
            modified: new Date().toISOString(),
          });
        } catch (e) {
          console.warn(`Failed to load ${file}:`, e);
        }
      }

      layers = layerFiles;
    } catch (error) {
      console.error("Failed to load layers:", error);
    } finally {
      loading = false;
    }
  }

  async function selectLayer(filename: string) {
    selectedFile = filename;

    try {
      const contents = await invoke<string>("read_file", {
        path: `${CORE_MAPS_PATH}/${filename}`,
      });
      selectedMetadata = JSON.parse(contents);

      // Check for linked layers (simple heuristic)
      if (selectedMetadata) {
        linkedLayers = getLinkedLayers(selectedMetadata);
      }
    } catch (error) {
      console.error("Failed to load layer metadata:", error);
      selectedMetadata = null;
      linkedLayers = [];
    }
  }

  function getLinkedLayers(layer: MapLayer): string[] {
    // Map layer relationships
    const relationships: Record<string, string[]> = {
      "surface.json": ["cloud.json", "underground.json"],
      "cloud.json": ["surface.json", "satellite.json"],
      "satellite.json": ["cloud.json"],
      "underground.json": ["surface.json"],
    };

    const filename = selectedFile || "";
    return relationships[filename] || [];
  }

  function handleLoadLayer() {
    if (selectedFile && selectedMetadata) {
      onLoadLayer?.(selectedFile, selectedMetadata);
    }
  }
</script>

<div
  class="map-layer-browser h-full flex flex-col bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
>
  <!-- Header -->
  <div class="p-3 border-b border-gray-200 dark:border-gray-700">
    <h3 class="text-xs font-semibold uppercase tracking-wider mb-1">
      Map Layers
    </h3>
    <p class="text-xs text-gray-600 dark:text-gray-400">
      {layers.length} available
    </p>
  </div>

  <!-- File list -->
  <div class="flex-1 overflow-y-auto p-2">
    {#if loading}
      <div class="text-center py-8 text-sm text-gray-500">
        Loading layers...
      </div>
    {:else if layers.length === 0}
      <div class="text-center py-8 text-sm text-gray-500">No layers found</div>
    {:else}
      <div class="space-y-1">
        {#each layers as layer}
          <button
            onclick={() => selectLayer(layer.name)}
            class="w-full text-left p-2 text-xs font-mono rounded transition-colors"
            class:bg-cyan-100={selectedFile === layer.name}
            class:dark:bg-cyan-900={selectedFile === layer.name}
            class:text-cyan-900={selectedFile === layer.name}
            class:dark:text-cyan-100={selectedFile === layer.name}
            class:hover:bg-gray-100={selectedFile !== layer.name}
            class:dark:hover:bg-gray-800={selectedFile !== layer.name}
          >
            📄 {layer.name}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Details panel -->
  {#if selectedMetadata}
    <div
      class="border-t border-gray-200 dark:border-gray-700 p-3 space-y-3 max-h-96 overflow-y-auto"
    >
      <!-- Layer info -->
      <div>
        <h4 class="text-xs font-semibold mb-1">
          Layer: {selectedMetadata.layer_name}
        </h4>
        <dl class="space-y-0.5 text-xs">
          <div class="flex justify-between">
            <dt class="text-gray-600 dark:text-gray-400">Type:</dt>
            <dd class="font-mono">{selectedMetadata.layer_type}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-600 dark:text-gray-400">Resolution:</dt>
            <dd class="font-mono">{selectedMetadata.resolution}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-600 dark:text-gray-400">Grid:</dt>
            <dd class="font-mono">
              {selectedMetadata.grid_size.columns}×{selectedMetadata.grid_size
                .rows}
            </dd>
          </div>
        </dl>
      </div>

      <!-- Description -->
      {#if selectedMetadata.description}
        <div>
          <h5 class="text-xs font-semibold mb-1">Description</h5>
          <p class="text-xs text-gray-600 dark:text-gray-400 leading-snug">
            {selectedMetadata.description}
          </p>
        </div>
      {/if}

      <!-- Linked layers -->
      {#if linkedLayers.length > 0}
        <div>
          <h5 class="text-xs font-semibold mb-1">Related Layers</h5>
          <div class="flex flex-wrap gap-1">
            {#each linkedLayers as linked}
              <span
                class="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-xs"
              >
                {linked}
              </span>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Load button -->
      <button
        onclick={handleLoadLayer}
        class="w-full px-3 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded text-xs font-semibold transition-colors"
      >
        Load Layer
      </button>
    </div>
  {/if}
</div>
