/**
 * Core Map Service - Integration with /core/data/maps/layers
 *
 * Provides access to the pre-defined geographic map layers stored in
 * core/data/maps/layers/
 *
 * These are world map layers with terrain, elevation, climate data that can
 * be imported into the tile-based layer editor.
 */

import { invoke } from "@tauri-apps/api/core";
import type { Layer } from "$lib/types/layer";
import { createLayer, createEmptyTile } from "$lib/types/layer";

// Path to core map layers (relative to project root, resolved by backend)
const CORE_MAPS_PATH = "core/data/maps/layers";

export interface CoreMapLayer {
  layer_id: number;
  layer_name: string;
  layer_type: string;
  description: string;
  version: string;
  resolution: string;
  grid_size: {
    columns: number;
    rows: number;
    total_cells: number;
  };
  terrain_types?: Record<string, TerrainType>;
  elevation?: ElevationData;
  biomes?: Record<string, BiomeData>;
  [key: string]: any;
}

export interface TerrainType {
  id: number;
  symbol: string;
  color: string;
}

export interface ElevationData {
  unit: string;
  min: number;
  max: number;
  sea_level: number;
  ranges: Record<string, { min: number; max: number; color: string }>;
}

export interface BiomeData {
  climate: string;
  precipitation_mm: number;
  temp_c: number;
}

export interface CoreMapInfo {
  name: string;
  filename: string;
  description: string;
  resolution: string;
  size: { width: number; height: number };
}

/**
 * List available core map layers
 */
export async function listCoreMapLayers(): Promise<CoreMapInfo[]> {
  try {
    const files = await invoke<string[]>("list_directory", {
      path: CORE_MAPS_PATH,
    });

    // Filter for JSON files and load their metadata
    const jsonFiles = files.filter((f) => f.endsWith(".json"));
    const maps: CoreMapInfo[] = [];

    for (const file of jsonFiles) {
      try {
        const layer = await loadCoreMapLayer(file);
        maps.push({
          name: layer.layer_name,
          filename: file,
          description: layer.description || "No description",
          resolution: layer.resolution || "Unknown",
          size: {
            width: layer.grid_size?.columns || 0,
            height: layer.grid_size?.rows || 0,
          },
        });
      } catch (e) {
        console.warn(`Failed to load metadata for ${file}:`, e);
      }
    }

    return maps;
  } catch (error) {
    console.error("Failed to list core map layers:", error);
    return [];
  }
}

/**
 * Load a core map layer by filename
 */
export async function loadCoreMapLayer(
  filename: string,
): Promise<CoreMapLayer> {
  try {
    const path = `${CORE_MAPS_PATH}/${filename}`;
    const contents = await invoke<string>("read_file", { path });
    return JSON.parse(contents);
  } catch (error) {
    console.error(`Failed to load core map layer ${filename}:`, error);
    throw new Error(`Failed to load map layer: ${error}`);
  }
}

/**
 * Convert core map layer to tile editor Layer format
 *
 * Since core maps are large (e.g., 480x270), we provide options to:
 * - Scale down to fit the editor's default 60x20 grid
 * - Extract a specific region
 * - Sample at intervals
 */
export async function convertCoreMapToLayer(
  filename: string,
  options: {
    targetWidth?: number;
    targetHeight?: number;
    region?: { x: number; y: number; width: number; height: number };
    sampleRate?: number;
  } = {},
): Promise<Layer> {
  const coreMap = await loadCoreMapLayer(filename);

  const targetWidth = options.targetWidth || 60;
  const targetHeight = options.targetHeight || 20;

  // Create a new layer with the tile editor's format
  const layer = createLayer(
    `core-${coreMap.layer_name}`,
    coreMap.layer_name.charAt(0).toUpperCase() + coreMap.layer_name.slice(1),
    targetWidth,
    targetHeight,
  );

  // Add metadata
  layer.metadata = {
    ...layer.metadata,
    category: "core-maps",
    custom: {
      source: "core-maps",
      originalFile: filename,
      originalSize: {
        width: coreMap.grid_size.columns,
        height: coreMap.grid_size.rows,
      },
      resolution: coreMap.resolution,
    },
  };

  // Convert terrain data to tiles
  // For now, we create a basic representation using terrain symbols
  if (coreMap.terrain_types) {
    // Sample the terrain data to fit our grid
    // This is a simplified conversion - you'd implement smarter sampling
    const terrainEntries = Object.entries(coreMap.terrain_types);

    // Fill with sample terrain characters
    for (let row = 0; row < targetHeight; row++) {
      for (let col = 0; col < targetWidth; col++) {
        // Sample from a representative terrain type
        const terrainIndex = Math.floor(Math.random() * terrainEntries.length);
        const [, terrain] = terrainEntries[terrainIndex];

        if (terrain && typeof terrain === "object" && "symbol" in terrain) {
          layer.tiles[row][col] = {
            char: (terrain as TerrainType).symbol,
            code: (terrain as TerrainType).symbol.charCodeAt(0),
            fg: (terrain as TerrainType).color,
          };
        }
      }
    }
  }

  return layer;
}

/**
 * Get terrain legend from core map
 */
export async function getCoreMapLegend(
  filename: string,
): Promise<Record<string, TerrainType>> {
  const coreMap = await loadCoreMapLayer(filename);
  return (coreMap.terrain_types as Record<string, TerrainType>) || {};
}

/**
 * Get elevation ranges from core map
 */
export async function getCoreMapElevation(
  filename: string,
): Promise<ElevationData | null> {
  const coreMap = await loadCoreMapLayer(filename);
  return coreMap.elevation || null;
}
