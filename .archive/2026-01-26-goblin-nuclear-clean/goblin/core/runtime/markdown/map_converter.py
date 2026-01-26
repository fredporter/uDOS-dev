#!/usr/bin/env python3
"""
Map Converter Tool

Converts Map.json data into -ucode.md format with ASCII grid tiles.
Enforces 120x40 character constraint per tile.

Usage:
    python -m core.runtime.markdown.map_converter input.json output-ucode.md

Author: uDOS Core Team
Version: 1.0.0
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import textwrap


class MapConverter:
    """Convert Map.json data to -ucode.md format with ASCII tiles."""

    TILE_WIDTH = 120
    TILE_HEIGHT = 40

    def __init__(self):
        self.tiles: List[Dict[str, Any]] = []

    def convert_json_to_tiles(self, map_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert Map.json structure to tile format.

        Args:
            map_data: Map JSON data

        Returns:
            List of tile dictionaries
        """
        tiles = []

        # Handle different map data structures
        if "tiles" in map_data:
            # Already tiled
            for tile_code, tile_data in map_data["tiles"].items():
                tiles.append(self._convert_tile(tile_code, tile_data))

        elif "grid" in map_data:
            # Full grid - chunk into tiles
            grid = map_data["grid"]
            tiles = self._chunk_grid(grid, map_data.get("metadata", {}))

        elif "regions" in map_data:
            # Region-based map
            for region_name, region_data in map_data["regions"].items():
                tiles.append(self._convert_region(region_name, region_data))

        return tiles

    def _convert_tile(
        self, tile_code: str, tile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert single tile data."""
        ascii_art = tile_data.get("ascii", self._generate_placeholder(tile_code))

        # Enforce size constraints
        ascii_art = self._constrain_size(ascii_art)

        return {
            "tile_code": tile_code,
            "name": tile_data.get("name", tile_code),
            "zone": tile_data.get("timezone", tile_data.get("zone", "")),
            "metadata": {
                "lat": tile_data.get("lat"),
                "lon": tile_data.get("lon"),
                "elevation": tile_data.get("elevation"),
            },
            "ascii": ascii_art,
        }

    def _chunk_grid(
        self, grid: List[List[str]], metadata: Dict
    ) -> List[Dict[str, Any]]:
        """
        Chunk large grid into 120x40 tiles.

        Args:
            grid: 2D grid of characters
            metadata: Map metadata

        Returns:
            List of tile dicts
        """
        tiles = []

        grid_height = len(grid)
        grid_width = len(grid[0]) if grid else 0

        # Calculate tile grid dimensions
        tiles_v = (grid_height + self.TILE_HEIGHT - 1) // self.TILE_HEIGHT
        tiles_h = (grid_width + self.TILE_WIDTH - 1) // self.TILE_WIDTH

        for row in range(tiles_v):
            for col in range(tiles_h):
                tile_code = f"{chr(65 + col)}{row + 1:02d}"

                # Extract tile section
                start_row = row * self.TILE_HEIGHT
                end_row = min(start_row + self.TILE_HEIGHT, grid_height)
                start_col = col * self.TILE_WIDTH
                end_col = min(start_col + self.TILE_WIDTH, grid_width)

                tile_lines = []
                for r in range(start_row, end_row):
                    line = "".join(grid[r][start_col:end_col])
                    tile_lines.append(line)

                ascii_art = "\n".join(tile_lines)

                tiles.append(
                    {
                        "tile_code": tile_code,
                        "name": f"Tile {tile_code}",
                        "zone": metadata.get("default_zone", ""),
                        "metadata": {"row": row, "col": col},
                        "ascii": ascii_art,
                    }
                )

        return tiles

    def _convert_region(self, region_name: str, region_data: Dict) -> Dict[str, Any]:
        """Convert region to tile."""
        ascii_art = region_data.get("map", self._generate_placeholder(region_name))
        ascii_art = self._constrain_size(ascii_art)

        return {
            "tile_code": region_name[:4].upper(),
            "name": region_name,
            "zone": region_data.get("timezone", ""),
            "metadata": region_data.get("metadata", {}),
            "ascii": ascii_art,
        }

    def _constrain_size(self, ascii_art: str) -> str:
        """
        Enforce 120x40 character constraint.

        Args:
            ascii_art: ASCII art string

        Returns:
            Constrained ASCII art
        """
        lines = ascii_art.split("\n")

        # Limit height
        if len(lines) > self.TILE_HEIGHT:
            lines = lines[: self.TILE_HEIGHT]

        # Limit width and pad
        constrained_lines = []
        for line in lines:
            if len(line) > self.TILE_WIDTH:
                line = line[: self.TILE_WIDTH]
            constrained_lines.append(line)

        return "\n".join(constrained_lines)

    def _generate_placeholder(self, identifier: str) -> str:
        """Generate placeholder ASCII art for missing data."""
        border = "┌" + "─" * (self.TILE_WIDTH - 2) + "┐"
        empty = "│" + " " * (self.TILE_WIDTH - 2) + "│"
        bottom = "└" + "─" * (self.TILE_WIDTH - 2) + "┘"

        title = f"MAP TILE: {identifier}"
        title_line = "│" + title.center(self.TILE_WIDTH - 2) + "│"

        lines = [border, title_line]
        for _ in range(self.TILE_HEIGHT - 4):
            lines.append(empty)
        lines.append(bottom)

        return "\n".join(lines)

    def generate_ucode_md(self, map_name: str, tiles: List[Dict[str, Any]]) -> str:
        """
        Generate -ucode.md content from tiles.

        Args:
            map_name: Name of the map
            tiles: List of tile data

        Returns:
            Complete -ucode.md content
        """
        lines = []

        # Frontmatter
        lines.append("---")
        lines.append(f"title: {map_name}")
        lines.append("type: map")
        lines.append(f"tiles: {len(tiles)}")
        lines.append("format: ascii")
        lines.append("constraint: 120x40")
        lines.append("version: 1.0.0")
        lines.append("---")
        lines.append("")

        # Description
        lines.append(f"# {map_name}")
        lines.append("")
        lines.append(
            f"This map contains {len(tiles)} ASCII tiles rendered at 120x40 characters each."
        )
        lines.append("")

        # Tiles
        for tile in tiles:
            lines.append(f"## {tile['name']}")
            if tile.get("zone"):
                lines.append(f"**Timezone:** {tile['zone']}")
            lines.append("")

            lines.append("```map")

            # Metadata line
            meta_parts = []
            if tile.get("tile_code"):
                meta_parts.append(f"TILE:{tile['tile_code']}")
            if tile.get("name"):
                meta_parts.append(f"NAME:{tile['name']}")
            if tile.get("zone"):
                meta_parts.append(f"ZONE:{tile['zone']}")

            if meta_parts:
                lines.append(" ".join(meta_parts))

            lines.append(tile["ascii"])
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def convert_file(self, input_path: Path, output_path: Path):
        """
        Convert Map.json file to .udos.md.

        Args:
            input_path: Path to input JSON file
            output_path: Path to output .udos.md file
        """
        print(f"📖 Reading {input_path}...")
        with open(input_path, "r", encoding="utf-8") as f:
            map_data = json.load(f)

        print("🔄 Converting to tiles...")
        tiles = self.convert_json_to_tiles(map_data)

        print(f"📝 Generated {len(tiles)} tiles")

        map_name = map_data.get("name", input_path.stem)
        ucode_content = self.generate_ucode_md(map_name, tiles)

        print(f"💾 Writing {output_path}...")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ucode_content)

        print(f"✅ Conversion complete!")
        print(f"   Tiles: {len(tiles)}")
        print(f"   Output: {output_path}")


def main():
    """CLI entry point."""
    if len(sys.argv) != 3:
        print(
            "Usage: python -m core.runtime.markdown.map_converter input.json output-ucode.md"
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"❌ Error: {input_path} not found")
        sys.exit(1)

    converter = MapConverter()
    converter.convert_file(input_path, output_path)


if __name__ == "__main__":
    main()
