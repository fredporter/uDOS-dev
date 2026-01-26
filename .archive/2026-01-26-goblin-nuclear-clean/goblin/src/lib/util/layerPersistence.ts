/**
 * Layer Persistence - Save and load layer files
 *
 * Handles reading/writing layer JSON files to memory/sandbox and distributed layers
 */

import type { Layer, MapDocument } from "$lib/types/layer";
import { invoke } from "@tauri-apps/api/core";

/**
 * Save map document to file
 */
export async function saveMapDocument(
  doc: MapDocument,
  path: string,
): Promise<void> {
  const json = JSON.stringify(doc, null, 2);

  try {
    await invoke("write_file", {
      path,
      contents: json,
    });
  } catch (error) {
    console.error("Failed to save map document:", error);
    throw new Error(`Failed to save map: ${error}`);
  }
}

/**
 * Load map document from file
 */
export async function loadMapDocument(path: string): Promise<MapDocument> {
  try {
    const contents = await invoke<string>("read_file", { path });
    return JSON.parse(contents);
  } catch (error) {
    console.error("Failed to load map document:", error);
    throw new Error(`Failed to load map: ${error}`);
  }
}

/**
 * Save individual layer to file
 */
export async function saveLayer(layer: Layer, path: string): Promise<void> {
  const json = JSON.stringify(layer, null, 2);

  try {
    await invoke("write_file", {
      path,
      contents: json,
    });
  } catch (error) {
    console.error("Failed to save layer:", error);
    throw new Error(`Failed to save layer: ${error}`);
  }
}

/**
 * Load individual layer from file
 */
export async function loadLayer(path: string): Promise<Layer> {
  try {
    const contents = await invoke<string>("read_file", { path });
    return JSON.parse(contents);
  } catch (error) {
    console.error("Failed to load layer:", error);
    throw new Error(`Failed to load layer: ${error}`);
  }
}

/**
 * List available map files in a directory
 */
export async function listMapFiles(directory: string): Promise<string[]> {
  try {
    const entries = await invoke<string[]>("list_directory", {
      path: directory,
    });
    return entries.filter((file) => file.endsWith(".json"));
  } catch (error) {
    console.error("Failed to list map files:", error);
    return [];
  }
}

/**
 * Export map as plain text ASCII art
 */
export function exportMapAsText(doc: MapDocument): string {
  // Find the first visible layer or the active layer
  const layer =
    doc.layers.find((l) => l.visible && l.id === doc.activeLayerId) ||
    doc.layers.find((l) => l.visible) ||
    doc.layers[0];

  if (!layer) return "";

  const lines: string[] = [];

  // Add header
  lines.push(`# ${doc.name}`);
  if (doc.description) {
    lines.push(`# ${doc.description}`);
  }
  lines.push(`# ${layer.width}×${layer.height} • Layer: ${layer.name}`);
  lines.push("");

  // Add each row
  layer.tiles.forEach((row) => {
    const line = row.map((tile) => tile.char).join("");
    lines.push(line);
  });

  return lines.join("\n");
}

/**
 * Export map with metadata as Markdown
 */
export function exportMapAsMarkdown(doc: MapDocument): string {
  const lines: string[] = [];

  // Front matter
  lines.push("---");
  lines.push(`title: ${doc.name}`);
  if (doc.description) {
    lines.push(`description: ${doc.description}`);
  }
  lines.push(`version: ${doc.version}`);
  lines.push(`created: ${doc.metadata?.created || "unknown"}`);
  lines.push(`modified: ${doc.metadata?.modified || "unknown"}`);
  lines.push("---");
  lines.push("");

  // Title
  lines.push(`# ${doc.name}`);
  lines.push("");
  if (doc.description) {
    lines.push(doc.description);
    lines.push("");
  }

  // Layers section
  lines.push("## Layers");
  lines.push("");
  doc.layers.forEach((layer, i) => {
    lines.push(`### ${i + 1}. ${layer.name}`);
    if (layer.description) {
      lines.push(layer.description);
    }
    lines.push("");
    lines.push("```");
    layer.tiles.forEach((row) => {
      const line = row.map((tile) => tile.char).join("");
      lines.push(line);
    });
    lines.push("```");
    lines.push("");
  });

  return lines.join("\n");
}

/**
 * Get default save paths (relative to project root, resolved by backend)
 */
export const DEFAULT_PATHS = {
  sandbox: "memory/sandbox/",
  core: "memory/knowledge/maps/",
  drafts: "memory/drafts/",
};

/**
 * Generate filename from map name
 */
export function generateFilename(
  mapName: string,
  extension: string = "json",
): string {
  const sanitized = mapName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  const timestamp = new Date().toISOString().split("T")[0];
  return `${timestamp}-${sanitized}.${extension}`;
}
