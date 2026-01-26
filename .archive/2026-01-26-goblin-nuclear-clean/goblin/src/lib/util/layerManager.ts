/**
 * Layer Management Utilities
 *
 * Functions for manipulating layers, tiles, and map documents
 */

import type { Layer, Tile, MapDocument, TileLink } from "$lib/types/layer";
import { createLayer, createEmptyTile } from "$lib/types/layer";

/**
 * Add a new layer to a map
 */
export function addLayer(
  doc: MapDocument,
  name: string,
  insertAtIndex?: number
): MapDocument {
  const newLayer = createLayer(
    `layer-${Date.now()}`,
    name,
    doc.defaultWidth,
    doc.defaultHeight
  );

  // Set z-index based on position
  const maxZIndex = Math.max(...doc.layers.map((l) => l.zIndex), 0);
  newLayer.zIndex = maxZIndex + 1;

  const layers =
    insertAtIndex !== undefined
      ? [
          ...doc.layers.slice(0, insertAtIndex),
          newLayer,
          ...doc.layers.slice(insertAtIndex),
        ]
      : [...doc.layers, newLayer];

  return {
    ...doc,
    layers,
    activeLayerId: newLayer.id,
    metadata: {
      ...doc.metadata,
      modified: new Date().toISOString(),
    },
  };
}

/**
 * Remove a layer from a map
 */
export function removeLayer(doc: MapDocument, layerId: string): MapDocument {
  const layers = doc.layers.filter((l) => l.id !== layerId);

  // If no layers left, create a default one
  if (layers.length === 0) {
    const defaultLayer = createLayer(
      "layer-1",
      "Base Layer",
      doc.defaultWidth,
      doc.defaultHeight
    );
    layers.push(defaultLayer);
  }

  // If active layer was removed, select first layer
  const activeLayerId =
    doc.activeLayerId === layerId ? layers[0].id : doc.activeLayerId;

  return {
    ...doc,
    layers,
    activeLayerId,
    metadata: {
      ...doc.metadata,
      modified: new Date().toISOString(),
    },
  };
}

/**
 * Reorder layers
 */
export function moveLayer(
  doc: MapDocument,
  layerId: string,
  direction: "up" | "down"
): MapDocument {
  const index = doc.layers.findIndex((l) => l.id === layerId);
  if (index === -1) return doc;

  const newIndex = direction === "up" ? index - 1 : index + 1;
  if (newIndex < 0 || newIndex >= doc.layers.length) return doc;

  const layers = [...doc.layers];
  const [removed] = layers.splice(index, 1);
  layers.splice(newIndex, 0, removed);

  // Update z-indices
  layers.forEach((layer, i) => {
    layer.zIndex = i;
  });

  return {
    ...doc,
    layers,
    metadata: {
      ...doc.metadata,
      modified: new Date().toISOString(),
    },
  };
}

/**
 * Duplicate a layer
 */
export function duplicateLayer(doc: MapDocument, layerId: string): MapDocument {
  const layer = doc.layers.find((l) => l.id === layerId);
  if (!layer) return doc;

  const newLayer: Layer = {
    ...layer,
    id: `layer-${Date.now()}`,
    name: `${layer.name} (Copy)`,
    tiles: layer.tiles.map((row) => row.map((tile) => ({ ...tile }))),
    zIndex: Math.max(...doc.layers.map((l) => l.zIndex), 0) + 1,
    metadata: {
      ...layer.metadata,
      created: new Date().toISOString(),
      modified: new Date().toISOString(),
    },
  };

  return {
    ...doc,
    layers: [...doc.layers, newLayer],
    activeLayerId: newLayer.id,
    metadata: {
      ...doc.metadata,
      modified: new Date().toISOString(),
    },
  };
}

/**
 * Update layer properties
 */
export function updateLayer(
  doc: MapDocument,
  layerId: string,
  updates: Partial<Layer>
): MapDocument {
  const layers = doc.layers.map((layer) =>
    layer.id === layerId
      ? {
          ...layer,
          ...updates,
          metadata: {
            ...layer.metadata,
            modified: new Date().toISOString(),
          },
        }
      : layer
  );

  return {
    ...doc,
    layers,
    metadata: {
      ...doc.metadata,
      modified: new Date().toISOString(),
    },
  };
}

/**
 * Set tile at position
 */
export function setTile(
  layer: Layer,
  row: number,
  col: number,
  tile: Tile
): Layer {
  if (row < 0 || row >= layer.height || col < 0 || col >= layer.width) {
    return layer;
  }

  const tiles = layer.tiles.map((r, i) =>
    i === row ? r.map((t, j) => (j === col ? tile : t)) : r
  );

  return {
    ...layer,
    tiles,
    metadata: {
      ...layer.metadata,
      modified: new Date().toISOString(),
    },
  };
}

/**
 * Fill area with tile
 */
export function fillArea(
  layer: Layer,
  startRow: number,
  startCol: number,
  endRow: number,
  endCol: number,
  tile: Tile
): Layer {
  const tiles = layer.tiles.map((row, i) =>
    row.map((t, j) => {
      if (i >= startRow && i <= endRow && j >= startCol && j <= endCol) {
        return { ...tile };
      }
      return t;
    })
  );

  return {
    ...layer,
    tiles,
    metadata: {
      ...layer.metadata,
      modified: new Date().toISOString(),
    },
  };
}

/**
 * Clear area (set to empty tiles)
 */
export function clearArea(
  layer: Layer,
  startRow: number,
  startCol: number,
  endRow: number,
  endCol: number
): Layer {
  return fillArea(layer, startRow, startCol, endRow, endCol, createEmptyTile());
}

/**
 * Add link to tile
 */
export function addTileLink(
  layer: Layer,
  row: number,
  col: number,
  link: TileLink
): Layer {
  if (row < 0 || row >= layer.height || col < 0 || col >= layer.width) {
    return layer;
  }

  const tile = { ...layer.tiles[row][col], link };
  return setTile(layer, row, col, tile);
}

/**
 * Remove link from tile
 */
export function removeTileLink(layer: Layer, row: number, col: number): Layer {
  if (row < 0 || row >= layer.height || col < 0 || col >= layer.width) {
    return layer;
  }

  const tile = { ...layer.tiles[row][col] };
  delete tile.link;
  return setTile(layer, row, col, tile);
}

/**
 * Get all tiles with links in a layer
 */
export function getLinkedTiles(layer: Layer): Array<{
  row: number;
  col: number;
  tile: Tile;
}> {
  const linked: Array<{ row: number; col: number; tile: Tile }> = [];

  layer.tiles.forEach((row, i) => {
    row.forEach((tile, j) => {
      if (tile.link) {
        linked.push({ row: i, col: j, tile });
      }
    });
  });

  return linked;
}

/**
 * Merge layers into a single composite layer
 */
export function mergeLayers(layers: Layer[]): Layer {
  if (layers.length === 0) {
    return createLayer("merged", "Merged Layer");
  }

  if (layers.length === 1) {
    return layers[0];
  }

  // Sort by z-index (bottom to top)
  const sortedLayers = [...layers]
    .filter((l) => l.visible)
    .sort((a, b) => a.zIndex - b.zIndex);

  const width = sortedLayers[0].width;
  const height = sortedLayers[0].height;

  const merged = createLayer("merged", "Merged Layer", width, height);

  // Composite tiles from bottom to top
  sortedLayers.forEach((layer) => {
    layer.tiles.forEach((row, i) => {
      row.forEach((tile, j) => {
        // Only composite if tile is not empty (space character)
        if (tile.char !== " " && tile.code !== 0x0020) {
          merged.tiles[i][j] = { ...tile };
        }
      });
    });
  });

  return merged;
}

/**
 * Export layer as JSON
 */
export function exportLayerAsJSON(layer: Layer): string {
  return JSON.stringify(layer, null, 2);
}

/**
 * Export map document as JSON
 */
export function exportMapAsJSON(doc: MapDocument): string {
  return JSON.stringify(doc, null, 2);
}

/**
 * Import layer from JSON
 */
export function importLayerFromJSON(json: string): Layer {
  return JSON.parse(json);
}

/**
 * Import map document from JSON
 */
export function importMapFromJSON(json: string): MapDocument {
  return JSON.parse(json);
}
