#!/usr/bin/env python3
"""
uDOS v1.0.0.49 - Pure Fractal 60×20 Grid-Based Map System

Multi-layer mapping system with teletext mosaic rendering, supporting
the full 000-899 Universe Layer Architecture and MeshCore device overlays.

Grid Specifications (v1.0.0.49):
- Layer: 60×20 tiles (1,200 tiles per layer)
- Tile: 24×24 pixels (576 data points)
- Block: 2×3 pixels (64 patterns, ASCII-mappable)
- Coordinates: AA10-CH29 (always 4 characters)

Universe Layer Architecture:
- 000-099: System (reserved)
- 100-199: Dungeons (tutorial/learning - start here)
- 200-299: Underground (caves, mines, infrastructure)
- 300-399: Earth Surface (★ real world distributed map)
- 400-499: Atmosphere (sky, aerial, drones)
- 500-599: Dimensions (virtual overlay realities)
- 600-699: Near Space (orbits, Moon, stations)
- 700-799: Solar System (planets, asteroids)
- 800-899: Galaxy (deep space, stars, frontiers)

Earth Zoom Levels (300-399, 10× per level):
- L300: ~668 km/tile (world map)
- L310: ~67 km/tile (regional)
- L320: ~6.7 km/tile (local)
- L330: ~668 m/tile (neighborhood)
- L340: ~67 m/tile (block)
- L350: ~6.7 m/tile (building)

Coordinate System:
- Column encoding: AA-CH (60 columns)
- Row encoding: 10-29 (20 rows, always 2 digits)
- Single tile: [COL][ROW] = "AA10" to "CH29"
- Cascading: L300:AA10-BB11-CA21 (layer + tile chain)

Version: 1.0.0.49
Author: Fred Porter
Date: January 2026
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from pathlib import Path
import json

# Import grid constants from canonical source
from dev.goblin.core.constants.grid import (
    LAYER_COLUMNS,
    LAYER_ROWS,
    LAYER_TILES,
    TILE_WIDTH,
    TILE_HEIGHT,
    ROW_OFFSET,
    TELETEXT_BLOCKS,
    ASCII_BLOCKS,
    EARTH_ZOOM_FACTOR,
    # Coordinate functions
    column_to_code,
    code_to_column,
    tile_to_coord,
    coord_to_tile,
    row_to_display,
    display_to_row,
    # Universe architecture
    Realm,
    REALM_INFO,
    EarthZoom,
    earth_tile_size_km,
)


# =============================================================================
# Layer System (Based on Universe Architecture)
# =============================================================================


class LayerRange(Enum):
    """
    Layer range definitions mapped to Universe Realms.

    Each realm spans 100 layer numbers with 10 zoom levels within.
    """

    SYSTEM = (0, 99, "System/Reserved", None)
    DUNGEONS = (100, 199, "Dungeons/Tutorial", None)  # Virtual - start here
    UNDERGROUND = (200, 299, "Underground/Caves", 0.01)  # ~10m at zoom 0
    EARTH = (300, 399, "Earth Surface", 668.0)  # ~668km at L300
    ATMOSPHERE = (400, 499, "Atmosphere/Sky", 668.0)  # ~668km at L400
    DIMENSIONS = (500, 599, "Dimensions/Virtual", None)  # Virtual overlay
    NEAR_SPACE = (600, 699, "Near Space/Orbits", None)  # Space
    SOLAR_SYSTEM = (700, 799, "Solar System", None)  # Planets
    GALAXY = (800, 899, "Galaxy/Deep Space", None)  # Stars

    @property
    def start(self) -> int:
        return self.value[0]

    @property
    def end(self) -> int:
        return self.value[1]

    @property
    def description(self) -> str:
        return self.value[2]

    @property
    def resolution_km(self) -> Optional[float]:
        return self.value[3]

    @classmethod
    def from_layer(cls, layer: int) -> "LayerRange":
        """Get layer range for a layer number."""
        for lr in cls:
            if lr.start <= layer <= lr.end:
                return lr
        raise ValueError(f"Layer {layer} not in valid range 0-899")


# Network sub-layers (600-699)
class NetworkSubLayer(Enum):
    """Network layer sub-divisions."""

    MESH_DEVICES = 600  # MeshCore device positions
    MESH_SIGNALS = 610  # Signal strength heatmaps
    MESH_ROUTES = 620  # Active route paths
    MESH_TOPOLOGY = 630  # Network topology view
    WEB_SERVICES = 650  # Local web services
    CLOUD_SYNC = 660  # Cloud sync status


# =============================================================================
# Grid Cell Data Structures
# =============================================================================


@dataclass
class TerrainCell:
    """Geographic terrain data for a cell."""

    terrain_type: str = "unknown"  # ocean, land, mountain, desert, forest, urban
    elevation: float = 0.0  # meters
    climate: str = "temperate"  # tropical, arid, temperate, cold, polar
    feature: Optional[str] = None  # river, lake, coastline, etc.
    label: Optional[str] = None  # City name, region name, etc.


@dataclass
class NetworkCell:
    """Network layer data for a cell."""

    device_id: Optional[str] = None
    device_type: str = "unknown"  # node, gateway, sensor, repeater, end_device
    signal_strength: int = 0  # 0-100%
    status: str = "offline"  # online, offline, connecting, error
    routes: List[str] = field(default_factory=list)  # Connected tile codes
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomCell:
    """Custom layer data for a cell."""

    symbol: str = ""
    label: str = ""
    color: str = "white"
    tags: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MapCell:
    """Complete map cell with all layers."""

    tile_code: str  # New format: "AA10" or cascading "L300:AA10-BB11"
    grid_col: int  # 0-59
    grid_row: int  # 0-19
    base_layer: int = 300  # Default to Earth Surface
    terrain: Optional[TerrainCell] = None
    network: Optional[NetworkCell] = None
    custom: Optional[CustomCell] = None

    @property
    def display_char(self) -> str:
        """Get primary display character based on priority."""
        # Network markers take priority
        if self.network and self.network.device_id:
            return DEVICE_SYMBOLS.get(self.network.device_type, "?")

        # Custom symbols next
        if self.custom and self.custom.symbol:
            return self.custom.symbol

        # Terrain fallback
        if self.terrain:
            return TERRAIN_CHARS.get(self.terrain.terrain_type, "·")

        return "·"

    @property
    def coord(self) -> str:
        """Get coordinate in new format."""
        return tile_to_coord(self.grid_col, self.grid_row)


# =============================================================================
# Display Symbol Sets
# =============================================================================

# Terrain characters (ASCII-compatible)
TERRAIN_CHARS = {
    "ocean": "~",
    "water": "≈",
    "land": "·",
    "mountain": "▲",
    "desert": "░",
    "forest": "▓",
    "urban": "█",
    "coastal": "▒",
    "snow": "░",
    "unknown": "?",
}

# Device type symbols
DEVICE_SYMBOLS = {
    "node": "⊚",  # Primary node/hub
    "gateway": "⊕",  # Gateway/router
    "sensor": "⊗",  # Sensor/monitor
    "repeater": "⊙",  # Repeater/relay
    "end_device": "⊘",  # End device/client
    "unknown": "?",
}

# Status indicators
STATUS_SYMBOLS = {
    "online": "●",
    "offline": "○",
    "connecting": "◐",
    "error": "◑",
}

# Signal strength display
SIGNAL_CHARS = {
    100: "█",  # Full block
    75: "▓",  # Dark shade
    50: "▒",  # Medium shade
    25: "░",  # Light shade
    0: " ",  # Empty
}

# Teletext mosaic characters (2×3 blocks)
TELETEXT_MOSAIC = [
    " ",
    "🬀",
    "🬁",
    "🬂",
    "🬃",
    "🬄",
    "🬅",
    "🬆",
    "🬇",
    "🬈",
    "🬉",
    "🬊",
    "🬋",
    "🬌",
    "🬍",
    "🬎",
    "🬏",
    "🬐",
    "🬑",
    "🬒",
    "🬓",
    "▌",
    "🬔",
    "🬕",
    "🬖",
    "🬗",
    "🬘",
    "🬙",
    "🬚",
    "🬛",
    "🬜",
    "🬝",
    "🬞",
    "🬟",
    "🬠",
    "🬡",
    "🬢",
    "🬣",
    "🬤",
    "🬥",
    "🬦",
    "🬧",
    "▐",
    "🬨",
    "🬩",
    "🬪",
    "🬫",
    "🬬",
    "🬭",
    "🬮",
    "🬯",
    "🬰",
    "🬱",
    "🬲",
    "🬳",
    "🬴",
    "🬵",
    "🬶",
    "🬷",
    "🬸",
    "🬹",
    "🬺",
    "🬻",
    "█",
]


# =============================================================================
# Map Viewport & Grid
# =============================================================================


@dataclass
class MapViewport:
    """Viewport configuration for map display."""

    width: int = 60  # Viewport width in tiles (full layer width)
    height: int = 20  # Viewport height in tiles (full layer height)
    center_col: int = 30  # Center column (0-59)
    center_row: int = 10  # Center row (0-19)
    layer: int = 300  # Current layer (default: Earth Surface)
    show_network: bool = True  # Show network overlay
    show_labels: bool = True  # Show city/feature labels
    ascii_mode: bool = False  # ASCII-only mode

    @property
    def visible_range(self) -> Tuple[range, range]:
        """Get visible column and row ranges."""
        half_w = self.width // 2
        half_h = self.height // 2

        col_start = max(0, self.center_col - half_w)
        col_end = min(LAYER_COLUMNS, self.center_col + half_w)
        row_start = max(0, self.center_row - half_h)
        row_end = min(LAYER_ROWS, self.center_row + half_h)

        return range(col_start, col_end), range(row_start, row_end)

    @property
    def center_coord(self) -> str:
        """Get center coordinate in new format."""
        return tile_to_coord(self.center_col, self.center_row)

    @property
    def realm(self) -> Realm:
        """Get the realm for current layer."""
        return Realm.from_layer(self.layer)


class MapGrid:
    """
    24×24 Grid-Based Map Renderer.

    Manages viewport, cell data, layer compositing, and rendering
    for the uDOS mapping system.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize map grid.

        Args:
            project_root: Project root directory for data loading
        """
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.viewport = MapViewport()
        self.cells: Dict[str, MapCell] = {}  # Cache: tile_code -> MapCell
        self.layers: Dict[int, Dict] = {}  # Layer data cache
        self.markers: List[Dict] = []  # User-placed markers

        # Load city data for labels
        self._cities: Optional[List[Dict]] = None

    @property
    def cities(self) -> List[Dict]:
        """Lazy-load cities data."""
        if self._cities is None:
            self._cities = self._load_cities()
        return self._cities

    def _load_cities(self) -> List[Dict]:
        """Load cities from cities.json."""
        cities_file = self.project_root / "core" / "data" / "geography" / "cities.json"
        if not cities_file.exists():
            # Try extension assets location
            cities_file = (
                self.project_root / "extensions" / "assets" / "data" / "cities.json"
            )

        if cities_file.exists():
            try:
                with open(cities_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("cities", []) if isinstance(data, dict) else data
            except Exception:
                pass
        return []

    # =========================================================================
    # Tile Code Utilities
    # =========================================================================

    def column_to_code(self, col: int) -> str:
        """Convert column number (0-479) to two-letter code (AA-SL)."""
        if not 0 <= col < 480:
            raise ValueError(f"Column {col} out of range 0-479")
        first = chr(65 + (col // 26))  # A-S
        second = chr(65 + (col % 26))  # A-Z
        return f"{first}{second}"

    def code_to_column(self, code: str) -> int:
        """Convert two-letter code (AA-SL) to column number."""
        if len(code) != 2:
            raise ValueError(f"Invalid column code: {code}")
        code = code.upper()
        first = ord(code[0]) - 65
        second = ord(code[1]) - 65
        return first * 26 + second

    def make_tile_code(self, col: int, row: int, layer: int = 100) -> str:
        """Create tile code from column, row, layer."""
        col_code = self.column_to_code(col)
        return f"{col_code}{row}-{layer}"

    def parse_tile_code(self, tile_code: str) -> Dict:
        """Parse tile code into components."""
        # Format: [COL][ROW]-[LAYER] e.g., "QB185-100"
        parts = tile_code.split("-")
        grid_part = parts[0]
        layer = int(parts[1]) if len(parts) > 1 else 100

        col_code = grid_part[:2]
        row = int(grid_part[2:])
        col = self.code_to_column(col_code)

        return {
            "tile_code": tile_code,
            "column_code": col_code,
            "column": col,
            "row": row,
            "layer": layer,
            "grid_cell": grid_part,
        }

    # =========================================================================
    # Viewport Navigation
    # =========================================================================

    def set_center(self, col: int = None, row: int = None, tile_code: str = None):
        """
        Set viewport center position.

        Args:
            col: Column number (0-479)
            row: Row number (0-269)
            tile_code: Alternatively, provide tile code
        """
        if tile_code:
            parsed = self.parse_tile_code(tile_code)
            col = parsed["column"]
            row = parsed["row"]

        if col is not None:
            self.viewport.center_col = max(0, min(479, col))
        if row is not None:
            self.viewport.center_row = max(0, min(269, row))

    def pan(self, dx: int = 0, dy: int = 0):
        """Pan viewport by delta cells."""
        self.set_center(
            col=self.viewport.center_col + dx, row=self.viewport.center_row + dy
        )

    def zoom(self, layer: int):
        """Change to different layer (zoom level)."""
        if 100 <= layer <= 899:
            self.viewport.layer = layer

    def goto_city(self, city_name: str) -> bool:
        """
        Center viewport on a city.

        Args:
            city_name: City name to search for

        Returns:
            True if city found
        """
        city_name_lower = city_name.lower()
        for city in self.cities:
            if city.get("name", "").lower() == city_name_lower:
                # Convert lat/lon to grid position
                lat = city.get("lat", 0)
                lon = city.get("lon", 0)
                col, row = self.latlong_to_grid(lat, lon)
                self.set_center(col=col, row=row)
                return True
        return False

    # =========================================================================
    # Coordinate Conversion
    # =========================================================================

    def latlong_to_grid(self, lat: float, lon: float) -> Tuple[int, int]:
        """
        Convert latitude/longitude to grid column/row.

        Grid covers:
        - Longitude: -180° to +180° (480 columns)
        - Latitude: -67.5° to +67.5° (270 rows)
        """
        # Longitude to column (0-479)
        col = int((lon + 180) / 360 * 480)
        col = max(0, min(479, col))

        # Latitude to row (0-269), inverted (north = low row numbers)
        row = int((67.5 - lat) / 135 * 270)
        row = max(0, min(269, row))

        return col, row

    def grid_to_latlong(self, col: int, row: int) -> Tuple[float, float]:
        """Convert grid column/row to latitude/longitude (cell center)."""
        lon = (col / 480) * 360 - 180 + (360 / 480 / 2)
        lat = 67.5 - (row / 270) * 135 - (135 / 270 / 2)
        return lat, lon

    # =========================================================================
    # Cell Data Management
    # =========================================================================

    def get_cell(self, col: int, row: int, layer: int = None) -> MapCell:
        """
        Get or create map cell.

        Args:
            col: Column number
            row: Row number
            layer: Layer number (default: viewport layer)

        Returns:
            MapCell instance
        """
        layer = layer or self.viewport.layer
        tile_code = self.make_tile_code(col, row, layer)

        if tile_code not in self.cells:
            self.cells[tile_code] = MapCell(
                tile_code=tile_code, grid_col=col, grid_row=row, base_layer=layer
            )
            # Load terrain from layer data
            self._populate_terrain(self.cells[tile_code])

        return self.cells[tile_code]

    def _populate_terrain(self, cell: MapCell):
        """Populate terrain data for a cell."""
        # Try to load from terrain.json
        terrain_file = (
            self.project_root / "core" / "data" / "geography" / "terrain.json"
        )
        if terrain_file.exists():
            try:
                with open(terrain_file, "r") as f:
                    terrain_data = json.load(f)
                    grid_cell = f"{self.column_to_code(cell.grid_col)}{cell.grid_row}"
                    if grid_cell in terrain_data:
                        t_data = terrain_data[grid_cell]
                        cell.terrain = TerrainCell(
                            terrain_type=t_data.get("type", "land"),
                            elevation=t_data.get("elevation", 0),
                            climate=t_data.get("climate", "temperate"),
                            feature=t_data.get("feature"),
                            label=t_data.get("label"),
                        )
                        return
            except Exception:
                pass

        # Default terrain based on simple ocean/land estimate
        # Rough approximation: row < 30 or row > 240 = likely ocean
        cell.terrain = TerrainCell(terrain_type="land")

    def set_network_device(
        self,
        col: int,
        row: int,
        device_id: str,
        device_type: str = "node",
        signal: int = 100,
        status: str = "online",
        **metadata,
    ):
        """
        Place a network device marker on the map.

        Args:
            col: Column position
            row: Row position
            device_id: Device identifier
            device_type: node, gateway, sensor, repeater, end_device
            signal: Signal strength 0-100
            status: online, offline, connecting, error
            **metadata: Additional device metadata
        """
        # Network devices go on layer 600
        cell = self.get_cell(col, row, 600)
        cell.network = NetworkCell(
            device_id=device_id,
            device_type=device_type,
            signal_strength=signal,
            status=status,
            metadata=metadata,
        )

    def add_marker(
        self,
        col: int,
        row: int,
        label: str = "",
        symbol: str = "◆",
        color: str = "yellow",
    ):
        """Add a custom marker to the map."""
        self.markers.append(
            {"col": col, "row": row, "label": label, "symbol": symbol, "color": color}
        )

    # =========================================================================
    # Rendering
    # =========================================================================

    def render(self, include_frame: bool = True) -> str:
        """
        Render the current viewport as text.

        Args:
            include_frame: Add border and status bar

        Returns:
            Rendered map as string
        """
        lines = []
        col_range, row_range = self.viewport.visible_range

        # Frame top
        if include_frame:
            lines.append(self._render_top_frame(col_range))

        # Render each row
        for row in row_range:
            line_chars = []
            for col in col_range:
                cell = self.get_cell(col, row)
                char = self._get_display_char(cell, col, row)
                line_chars.append(char)

            row_str = "".join(line_chars)
            if include_frame:
                row_str = f"│{row_str}│"
            lines.append(row_str)

        # Frame bottom
        if include_frame:
            lines.append(self._render_bottom_frame(col_range))
            lines.append(self._render_status_bar())

        return "\n".join(lines)

    def _render_top_frame(self, col_range: range) -> str:
        """Render top frame with column markers."""
        width = len(col_range)

        # Column scale (every 5 columns)
        scale = ""
        for i, col in enumerate(col_range):
            if i % 5 == 0:
                col_code = self.column_to_code(col)[:2]
                scale += col_code[:1]
            else:
                scale += " "

        return f"┌{'─' * width}┐"

    def _render_bottom_frame(self, col_range: range) -> str:
        """Render bottom frame."""
        width = len(col_range)
        return f"└{'─' * width}┘"

    def _render_status_bar(self) -> str:
        """Render status bar with position info."""
        center_code = self.make_tile_code(
            self.viewport.center_col, self.viewport.center_row, self.viewport.layer
        )
        lat, lon = self.grid_to_latlong(
            self.viewport.center_col, self.viewport.center_row
        )
        layer_range = LayerRange.from_layer(self.viewport.layer)

        return f" Center: {center_code} | {lat:.2f}°, {lon:.2f}° | Layer: {layer_range.description}"

    def _get_display_char(self, cell: MapCell, col: int, row: int) -> str:
        """Get display character for a cell with priority handling."""
        # Check for custom markers first
        for marker in self.markers:
            if marker["col"] == col and marker["row"] == row:
                return marker["symbol"]

        # Check for network device (if overlay enabled)
        if self.viewport.show_network and cell.network and cell.network.device_id:
            return DEVICE_SYMBOLS.get(cell.network.device_type, "?")

        # Check for city label
        if self.viewport.show_labels:
            for city in self.cities:
                city_lat = city.get("lat", 0)
                city_lon = city.get("lon", 0)
                city_col, city_row = self.latlong_to_grid(city_lat, city_lon)
                if city_col == col and city_row == row:
                    return "●"  # City marker

        # Terrain fallback
        if cell.terrain:
            return TERRAIN_CHARS.get(cell.terrain.terrain_type, "·")

        return "·"

    # =========================================================================
    # Search & Query
    # =========================================================================

    def search_city(self, query: str) -> List[Dict]:
        """Search for cities by name."""
        query_lower = query.lower()
        results = []
        for city in self.cities:
            name = city.get("name", "")
            if query_lower in name.lower():
                col, row = self.latlong_to_grid(city.get("lat", 0), city.get("lon", 0))
                results.append(
                    {
                        "name": name,
                        "country": city.get("country", ""),
                        "tile_code": self.make_tile_code(col, row, 100),
                        "lat": city.get("lat"),
                        "lon": city.get("lon"),
                        "col": col,
                        "row": row,
                    }
                )
        return results

    def get_visible_cities(self) -> List[Dict]:
        """Get cities visible in current viewport."""
        col_range, row_range = self.viewport.visible_range
        visible = []

        for city in self.cities:
            col, row = self.latlong_to_grid(city.get("lat", 0), city.get("lon", 0))
            if col in col_range and row in row_range:
                visible.append(
                    {
                        "name": city.get("name"),
                        "tile_code": self.make_tile_code(col, row, 100),
                        "col": col,
                        "row": row,
                    }
                )

        return visible

    def get_visible_devices(self) -> List[Dict]:
        """Get MeshCore devices visible in current viewport."""
        col_range, row_range = self.viewport.visible_range
        devices = []

        for tile_code, cell in self.cells.items():
            if cell.network and cell.network.device_id:
                if cell.grid_col in col_range and cell.grid_row in row_range:
                    devices.append(
                        {
                            "device_id": cell.network.device_id,
                            "type": cell.network.device_type,
                            "status": cell.network.status,
                            "signal": cell.network.signal_strength,
                            "tile_code": tile_code,
                            "col": cell.grid_col,
                            "row": cell.grid_row,
                        }
                    )

        return devices

    # =========================================================================
    # Layer Management
    # =========================================================================

    def load_layer(self, layer: int) -> bool:
        """
        Load layer data from disk.

        Args:
            layer: Layer number (100-899)

        Returns:
            True if layer loaded successfully
        """
        layer_file = (
            self.project_root
            / "core"
            / "data"
            / "geography"
            / f"map_layer_{layer}.json"
        )

        if layer_file.exists():
            try:
                with open(layer_file, "r") as f:
                    self.layers[layer] = json.load(f)
                return True
            except Exception:
                pass

        # Create empty layer structure
        self.layers[layer] = {
            "layer": layer,
            "range": LayerRange.from_layer(layer).name,
            "cells": {},
        }
        return False

    def save_layer(self, layer: int) -> bool:
        """Save layer data to disk."""
        if layer not in self.layers:
            return False

        layer_file = (
            self.project_root
            / "core"
            / "data"
            / "geography"
            / f"map_layer_{layer}.json"
        )

        try:
            with open(layer_file, "w") as f:
                json.dump(self.layers[layer], f, indent=2)
            return True
        except Exception:
            return False

    def get_layer_info(self, layer: int = None) -> Dict:
        """Get information about a layer."""
        layer = layer or self.viewport.layer
        lr = LayerRange.from_layer(layer)

        return {
            "layer": layer,
            "range": lr.name,
            "description": lr.description,
            "resolution_km": lr.resolution_km,
            "start": lr.start,
            "end": lr.end,
            "loaded": layer in self.layers,
        }


# =============================================================================
# Factory Function
# =============================================================================

_map_grid_instance: Optional[MapGrid] = None


def get_map_grid() -> MapGrid:
    """Get singleton MapGrid instance."""
    global _map_grid_instance
    if _map_grid_instance is None:
        _map_grid_instance = MapGrid()
    return _map_grid_instance


# =============================================================================
# CLI Test
# =============================================================================

if __name__ == "__main__":
    # Test the map grid
    grid = MapGrid()

    # Center on London area (approximate)
    grid.set_center(col=240, row=95)  # ~0° lon, ~52° lat

    # Add a test device
    grid.set_network_device(240, 95, "TEST-001", device_type="gateway", signal=85)

    # Render the map
    print(grid.render())

    # Show visible cities
    print("\nVisible cities:")
    for city in grid.get_visible_cities():
        print(f"  {city['name']} at {city['tile_code']}")
