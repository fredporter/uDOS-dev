"""
Map Layer Manager - Hierarchical Grid System

Manages multi-layer map system with hierarchical cell navigation:
- Multiverse layers 100-899 (Earth/Virtual/Space)
- Hierarchical cell-based zoom (120×50 = 6,000 cells per layer)
- Sparse cell storage (only cells that exist)
- Grid tile rendering at different zoom depths
- Integration with .udos.md map tiles

Part of Alpha v1.0.0.0 - Spatial Computing Layer
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

from ..config.paths import get_user_path
from ..services.logging_manager import get_logger
from .spatial_manager import GridCoordinate

logger = get_logger("map-layers")


@dataclass
class MapLayer:
    """
    Single map layer with hierarchical cell support.

    Hierarchical Layers (Alpha v1.0.0.0):
        Earth Realm (L100-399):
            L100: World surface (333km/cell at depth 0)
            L200: Underwater/caves (sparse)
            L300: Sky/atmosphere (sparse)

        Virtual Realm (L400-699):
            L401-455: NetHack dungeon (56 levels)
            L456-699: Future game worlds

        Space Realm (L700-899):
            L600-699: Solar system (planets, moons)
            L700-799: Galactic (Milky Way, Local Group)
            L800-899: Intergalactic (future)

    Hierarchical Cell Zoom:
        Depth 0: Base layer (6,000 cells: 120 cols × 50 rows)
        Depth 1: Zoomed into one cell (6,000 sub-cells)
        Depth 2: Zoomed into sub-cell (6,000 sub-sub-cells)
        Depth N: Unlimited via sparse storage

    Cell Format: CCNN (e.g., AB15, CD20)
        Columns: AA-DT (120 columns)
        Rows: 00-49 (50 rows)
    """

    realm: str  # "EARTH", "VIRTUAL", "SPACE"
    region: str  # "NA01", "NETH", "SOL", etc.
    layer: int  # 100-899
    depth: int = 0  # Current zoom depth
    cells: Dict[str, Any] = field(default_factory=dict)  # Sparse cell storage
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def coordinate(self) -> str:
        """Get base coordinate for this layer."""
        return f"{self.realm}-{self.region}-L{self.layer}"

    @property
    def precision_meters(self) -> float:
        """
        Get precision in meters at current depth.

        Earth L100 example:
            Depth 0: ~333 km/cell (40,000km / 120 cols)
            Depth 1: ~2.77 km/cell (333km / 120)
            Depth 2: ~23 m/cell (2.77km / 120)
            Depth 3: ~0.19 m/cell (23m / 120)
            Depth 4: ~1.6 mm/cell (0.19m / 120)
        """
        base_precision_km = 333  # Default Earth L100
        if self.realm == "VIRTUAL":
            base_precision_km = 0.08  # ~80m for NetHack dungeons
        elif self.realm == "SPACE" and self.layer >= 700:
            base_precision_km = 8808  # Milky Way galaxy

        precision_m = (
            base_precision_km * 1000 / (120**self.depth)
            if self.depth > 0
            else base_precision_km * 1000
        )
        return precision_m

    def get_cell(self, cell_path: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get cell data at specific hierarchical path.

        Args:
            cell_path: Path to cell (e.g., ["AB34", "CD15"])

        Returns:
            Cell data dict or None if not found
        """
        if not cell_path:
            return {"cells": self.cells, "metadata": self.metadata}

        current = self.cells
        for cell in cell_path:
            if cell not in current:
                return None
            current = current[cell]
            if not isinstance(current, dict):
                return None

        return current

    def set_cell(self, cell_path: List[str], cell_data: Dict[str, Any]):
        """
        Set cell data at specific hierarchical path.
        Creates intermediate cells if needed (sparse storage).

        Args:
            cell_path: Path to cell (e.g., ["AB34", "CD15", "AA20"])
            cell_data: Data to store at this cell
        """
        if not cell_path:
            self.cells.update(cell_data)
            return

        current = self.cells
        for i, cell in enumerate(cell_path[:-1]):
            if cell not in current:
                current[cell] = {}
            current = current[cell]

        # Set final cell
        final_cell = cell_path[-1]
        current[final_cell] = cell_data
        logger.info(f"[LOCAL] Set cell {'-'.join(cell_path)} in {self.coordinate}")


class MapLayerManager:
    """Manage hierarchical map layer system with sparse cell storage."""

    def __init__(self, config=None):
        """Initialize map layer manager."""
        self.config = config
        self.layers_dir = get_user_path("data") / "map_layers"
        self.tiles_dir = get_user_path("data") / "map_tiles"

        # Layer cache (key: realm-region-layer)
        self.layers: Dict[str, MapLayer] = {}

        # Current view state
        self.current_layer: Optional[MapLayer] = None
        self.current_coordinate: Optional[GridCoordinate] = None

        self.layers_dir.mkdir(parents=True, exist_ok=True)
        self.tiles_dir.mkdir(parents=True, exist_ok=True)

    # ==================== Layer Management ====================

    def load_layer(
        self, realm: str, region: str, layer: int, cell_path: Optional[List[str]] = None
    ) -> MapLayer:
        """
        Load layer from disk or hierarchical data files.

        Args:
            realm: Realm code ("EARTH", "VIRTUAL", "SPACE")
            region: Region code ("NA01", "NETH", "SOL")
            layer: Layer number (100-899)
            cell_path: Optional hierarchical cell path for depth loading

        Returns:
            MapLayer instance with sparse cell data

        Example:
            # Load Earth world layer
            layer = manager.load_layer("EARTH", "OC", 100)

            # Load zoomed into Sydney
            layer = manager.load_layer("EARTH", "OC", 100, ["AB34", "CD15"])
        """
        cache_key = f"{realm}-{region}-L{layer}"

        # Check cache
        if cache_key in self.layers:
            cached_layer = self.layers[cache_key]
            if cell_path:
                # Update depth if zooming
                cached_layer.depth = len(cell_path)
            return cached_layer

        # Try to load from hierarchical data files
        layer_data = self._load_hierarchical_data(realm, region, layer)

        if layer_data:
            map_layer = MapLayer(
                realm=realm,
                region=region,
                layer=layer,
                depth=len(cell_path) if cell_path else 0,
                cells=layer_data.get("cells", {}),
                metadata=layer_data.get("metadata", {}),
            )

            self.layers[cache_key] = map_layer
            logger.info(f"[LOCAL] Loaded {cache_key} from hierarchical data")
            return map_layer

        # Create new empty layer
        map_layer = MapLayer(
            realm=realm,
            region=region,
            layer=layer,
            depth=len(cell_path) if cell_path else 0,
        )

        self.layers[cache_key] = map_layer
        logger.info(f"[LOCAL] Created new layer {cache_key}")
        return map_layer

    def _load_hierarchical_data(
        self, realm: str, region: str, layer: int
    ) -> Optional[Dict[str, Any]]:
        """
        Load layer data from hierarchical JSON files.

        Checks:
            - core/data/spatial/locations-hierarchical.json (Earth)
            - core/data/virtual/nethack_levels-hierarchical.json (Virtual)
            - core/data/spatial/planets-hierarchical.json (Space 600-699)
            - core/data/spatial/galaxies-hierarchical.json (Space 700-899)
        """
        data_dir = Path(__file__).parent.parent / "data"

        # Earth realm
        if realm == "EARTH" and layer == 100:
            locations_file = data_dir / "spatial" / "locations-hierarchical.json"
            if locations_file.exists():
                with open(locations_file, "r") as f:
                    data = json.load(f)
                    # Convert locations to cell structure
                    cells = {}
                    for location in data.get("locations", []):
                        coord = location.get("coordinate", "")
                        if coord.startswith(f"EARTH-{region}-L100"):
                            # Extract cell path from coordinate
                            parts = coord.split("-")[3:]  # After EARTH-REGION-L100
                            if parts:
                                self._set_nested_cell(cells, parts, location)
                    return {"cells": cells, "metadata": data.get("grid", {})}

        # Virtual realm (NetHack)
        elif realm == "VIRTUAL" and region == "NETH" and 401 <= layer <= 455:
            nethack_file = data_dir / "virtual" / "nethack_levels-hierarchical.json"
            if nethack_file.exists():
                with open(nethack_file, "r") as f:
                    data = json.load(f)
                    # Find this specific level
                    for section in [
                        "main_dungeon",
                        "gnomish_mines",
                        "sokoban",
                        "elemental_planes",
                        "astral_plane",
                    ]:
                        if section in data:
                            levels = (
                                data[section].get("levels", [])
                                if section != "astral_plane"
                                else [data[section].get("level", {})]
                            )
                            if section == "astral_plane":
                                levels = (
                                    [data[section].get("level", {})]
                                    if "level" in data[section]
                                    else []
                                )

                            for level_data in levels:
                                if level_data.get("layer") == layer or level_data.get(
                                    "coordinate", ""
                                ).endswith(f"L{layer}"):
                                    cells = {}
                                    # Add special rooms as cells
                                    for room in level_data.get("special_rooms", []):
                                        cell = room.get("cell")
                                        if cell:
                                            cells[cell] = room
                                    return {"cells": cells, "metadata": level_data}

        # Space realm - planets
        elif realm == "SPACE" and 600 <= layer <= 639:
            planets_file = data_dir / "spatial" / "planets-hierarchical.json"
            if planets_file.exists():
                with open(planets_file, "r") as f:
                    data = json.load(f)
                    # Find planet data for this layer
                    for category in [
                        "terrestrial_planets",
                        "asteroid_belt",
                        "gas_giants",
                        "kuiper_belt",
                    ]:
                        for planet in data.get(category, []):
                            if planet.get("coordinate") == f"SPACE-{region}-L{layer}":
                                cells = {}
                                for location in planet.get("notable_locations", []):
                                    coord = location.get("coordinate", "")
                                    if coord:
                                        parts = coord.split("-")[
                                            3:
                                        ]  # After SPACE-REGION-LAYER
                                        if parts:
                                            self._set_nested_cell(
                                                cells, parts, location
                                            )
                                return {"cells": cells, "metadata": planet}

        # Space realm - galaxies
        elif realm == "SPACE" and 700 <= layer <= 799:
            galaxies_file = data_dir / "spatial" / "galaxies-hierarchical.json"
            if galaxies_file.exists():
                with open(galaxies_file, "r") as f:
                    data = json.load(f)
                    # Find galaxy data
                    if layer == 710:  # Milky Way
                        mw = data.get("milky_way", {})
                        cells = {}
                        # Add notable regions as cells
                        for region_data in mw.get("structure", {}).get(
                            "notable_regions", []
                        ):
                            coord = region_data.get("coordinate", "")
                            if coord:
                                parts = coord.split("-")[3:]
                                if parts:
                                    self._set_nested_cell(cells, parts, region_data)
                        return {"cells": cells, "metadata": mw}

        return None

    def _set_nested_cell(self, cells: Dict, path: List[str], data: Dict):
        """Helper to set nested cell data."""
        current = cells
        for cell in path[:-1]:
            if cell not in current:
                current[cell] = {}
            current = current[cell]
        current[path[-1]] = data

    def save_layer(self, layer: MapLayer):
        """Save layer to disk (sparse format)."""
        layer_file = self.layers_dir / f"{layer.coordinate}.json"

        data = {
            "realm": layer.realm,
            "region": layer.region,
            "layer": layer.layer,
            "depth": layer.depth,
            "precision_meters": layer.precision_meters,
            "cells": layer.cells,
            "metadata": layer.metadata,
        }

        with open(layer_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"[LOCAL] Saved layer {layer.coordinate}")

    # ==================== Hierarchical Navigation ====================

    def zoom_into_cell(self, cell: str) -> Optional[GridCoordinate]:
        """
        Zoom into specific cell, increasing depth.

        Args:
            cell: Cell to zoom into (e.g., "AB34")

        Returns:
            New GridCoordinate at deeper level, or None if no current view

        Example:
            # Currently at EARTH-OC-L100
            new_coord = manager.zoom_into_cell("AB34")  # → EARTH-OC-L100-AB34
        """
        if not self.current_coordinate:
            logger.warning("[LOCAL] No current coordinate to zoom from")
            return None

        try:
            zoomed = self.current_coordinate.zoom_into(cell)
            self.current_coordinate = zoomed

            # Update current layer depth
            if self.current_layer:
                self.current_layer.depth = zoomed.depth

            logger.info(f"[LOCAL] Zoomed into {cell} → {zoomed.code}")
            return zoomed

        except ValueError as e:
            logger.error(f"[LOCAL] Invalid cell {cell}: {e}")
            return None

    def zoom_out_cell(self) -> Optional[GridCoordinate]:
        """
        Zoom out one level, decreasing depth.

        Returns:
            New GridCoordinate at shallower level, or None if already at base

        Example:
            # Currently at EARTH-OC-L100-AB34-CD15
            new_coord = manager.zoom_out_cell()  # → EARTH-OC-L100-AB34
        """
        if not self.current_coordinate:
            logger.warning("[LOCAL] No current coordinate to zoom from")
            return None

        zoomed_out = self.current_coordinate.zoom_out()

        if zoomed_out:
            self.current_coordinate = zoomed_out

            # Update current layer depth
            if self.current_layer:
                self.current_layer.depth = zoomed_out.depth

            logger.info(f"[LOCAL] Zoomed out → {zoomed_out.code}")
            return zoomed_out
        else:
            logger.info("[LOCAL] Already at base layer, cannot zoom out")
            return None

    def set_view(self, coordinate: GridCoordinate):
        """
        Set current view to specific hierarchical coordinate.
        Loads appropriate layer and sets depth.

        Args:
            coordinate: GridCoordinate to view
        """
        self.current_coordinate = coordinate
        self.current_layer = self.load_layer(
            realm=coordinate.realm,
            region=coordinate.region,
            layer=coordinate.layer,
            cell_path=coordinate.cells,
        )
        logger.info(f"[LOCAL] Set view to {coordinate.code} (depth {coordinate.depth})")

    def get_cell_data(self, coordinate: GridCoordinate) -> Optional[Dict[str, Any]]:
        """
        Get data for specific hierarchical coordinate.

        Args:
            coordinate: GridCoordinate to query

        Returns:
            Cell data dict or None if not found
        """
        layer = self.load_layer(
            realm=coordinate.realm,
            region=coordinate.region,
            layer=coordinate.layer,
            cell_path=coordinate.cells,
        )

        return layer.get_cell(coordinate.cells)
        """
        Zoom in to child layer (higher precision).

        Args:
            grid: Current grid coordinate

        Returns:
            Child layer or None if at maximum zoom
        """
        if grid.layer >= 9:
            logger.warning("[LOCAL] Already at maximum zoom (L9)")
            return None

        child_layer = self.load_layer(grid.region, grid.layer + 1)

        # Update current view
        self.current_layer = child_layer
        self.current_grid = GridCoordinate(
            layer=grid.layer + 1, column=grid.column, row=grid.row, region=grid.region
        )

        logger.info(
            f"[LOCAL] Zoomed in: L{grid.layer} → L{grid.layer + 1} ({child_layer.precision_meters}m precision)"
        )
        return child_layer

    def zoom_out(self, grid: GridCoordinate) -> Optional[MapLayer]:
        """
        Zoom out to parent layer (lower precision).

        Args:
            grid: Current grid coordinate

        Returns:
            Parent layer or None if at minimum zoom
        """
        if grid.layer <= 0:
            logger.warning("[LOCAL] Already at minimum zoom (L0)")
            return None

        parent_layer = self.load_layer(grid.region, grid.layer - 1)

        # Update current view
        self.current_layer = parent_layer
        self.current_grid = GridCoordinate(
            layer=grid.layer - 1, column=grid.column, row=grid.row, region=grid.region
        )

        logger.info(
            f"[LOCAL] Zoomed out: L{grid.layer} → L{grid.layer - 1} ({parent_layer.precision_meters}m precision)"
        )
        return parent_layer

    def navigate_to(self, grid: GridCoordinate) -> MapLayer:
        """
        Navigate to specific grid coordinate.

        Args:
            grid: Target grid coordinate

        Returns:
            Layer at target grid
        """
        layer = self.load_layer(grid.region, grid.layer)

        self.current_layer = layer
        self.current_grid = grid

        logger.info(
            f"[LOCAL] Navigated to {grid.code} (L{grid.layer}, {layer.precision_meters}m precision)"
        )
        return layer

    # ==================== Tile Management ====================

    def import_udos_md_tile(self, udos_file: Path) -> bool:
        """
        Import .udos.md map tile into layer system.

        Parses .udos.md file and extracts map tiles into appropriate layers.

        Args:
            udos_file: Path to .udos.md file

        Returns:
            True if successful
        """
        from ..runtime.markdown import UDOSMarkdownParser

        logger.info(f"[LOCAL] Importing .udos.md tiles from {udos_file.name}")

        # Parse document
        with open(udos_file, "r") as f:
            content = f.read()

        parser = UDOSMarkdownParser()
        doc = parser.parse(content)

        # Extract map tiles
        imported = 0
        for tile in doc.map_tiles:
            # Parse grid from metadata
            tile_code = tile.get("tile_code", "")
            if not tile_code:
                continue

            # Determine layer from tile code or default to L9
            # Format: [Region-]L[layer][Column][Row]
            if "L" in tile_code:
                parts = tile_code.split("L")
                region = parts[0].rstrip("-") if "-" in parts[0] else "WORLD"
                layer_str = parts[1][0]
                layer_num = int(layer_str)
            else:
                # Legacy format: assume L9
                region = tile.get("region", "WORLD")
                layer_num = 9

            # Load or create layer
            layer = self.load_layer(region, layer_num)

            # Parse grid coordinates from tile code
            # Simplified: extract column and row
            col = tile.get("metadata", {}).get("column", "AA")
            row = int(tile.get("metadata", {}).get("row", 0))

            grid = GridCoordinate(layer=layer_num, column=col, row=row, region=region)

            # Add tile to layer
            tile_data = {
                "ascii": tile["ascii"],
                "name": tile.get("name", ""),
                "zone": tile.get("zone", ""),
                "metadata": tile.get("metadata", {}),
            }

            layer.add_tile(grid, tile_data)
            imported += 1

        # Save layers
        for layer in set(self.layers.values()):
            if layer.tiles:  # Only save if has tiles
                self.save_layer(layer)

        logger.info(f"[LOCAL] Imported {imported} tiles from {udos_file.name}")
        return imported > 0

    def export_layer_to_udos_md(
        self, region: str, layer: int, output_file: Path
    ) -> bool:
        """
        Export layer to .udos.md format.

        Args:
            region: Region code
            layer: Layer number
            output_file: Output .udos.md file path

        Returns:
            True if successful
        """
        map_layer = self.load_layer(region, layer)

        if not map_layer.tiles:
            logger.warning(f"[LOCAL] Layer {region}-L{layer} has no tiles to export")
            return False

        # Build .udos.md content
        lines = []

        # Frontmatter
        lines.append("---")
        lines.append(f"title: {region} Layer {layer} Map")
        lines.append("type: map")
        lines.append(f"layer: {layer}")
        lines.append(f"region: {region}")
        lines.append(f"precision: {map_layer.precision_meters}m")
        lines.append(f"tiles: {len(map_layer.tiles)}")
        lines.append("format: ascii")
        lines.append("constraint: 120x40")
        lines.append("version: 1.0.0")
        lines.append("---")
        lines.append("")

        # Description
        lines.append(f"# {region} - Layer {layer} Map")
        lines.append("")
        lines.append(
            f"**Precision:** {map_layer.precision_meters} meters per grid unit"
        )
        lines.append(f"**Tile Size:** {map_layer.tile_size_meters} meters")
        lines.append(f"**Total Tiles:** {len(map_layer.tiles)}")
        lines.append("")

        # Tiles
        for tile_key, tile_data in map_layer.tiles.items():
            name = tile_data.get("name", tile_key)
            lines.append(f"## {name}")
            lines.append("")

            lines.append("```map")

            # Metadata line
            tile_code = f"{region}-L{layer}{tile_key}"
            zone = tile_data.get("zone", "")

            meta_parts = [f"TILE:{tile_code}"]
            if name:
                meta_parts.append(f"NAME:{name}")
            if zone:
                meta_parts.append(f"ZONE:{zone}")

            lines.append(" ".join(meta_parts))
            lines.append(tile_data["ascii"])
            lines.append("```")
            lines.append("")

        # Write file
        with open(output_file, "w") as f:
            f.write("\n".join(lines))

        logger.info(f"[LOCAL] Exported {region}-L{layer} to {output_file}")
        return True

    # ==================== Rendering ====================

    def render_tile_at_grid(self, grid: GridCoordinate) -> Optional[str]:
        """
        Render ASCII map tile at grid coordinate.

        Args:
            grid: Grid coordinate

        Returns:
            ASCII art string or None if tile not found
        """
        layer = self.load_layer(grid.region, grid.layer)
        tile_data = layer.get_tile(grid)

        if not tile_data:
            logger.warning(f"[LOCAL] No tile found at {grid.code}")
            return None

        return tile_data.get("ascii", "")

    def get_layer_info(self, region: str, layer: int) -> Dict[str, Any]:
        """Get information about layer."""
        map_layer = self.load_layer(region, layer)

        return {
            "layer": map_layer.layer,
            "region": map_layer.region,
            "precision_meters": map_layer.precision_meters,
            "tile_size_meters": map_layer.tile_size_meters,
            "tile_count": len(map_layer.tiles),
            "parent_layer": map_layer.parent_layer,
            "child_layer": map_layer.child_layer,
        }
