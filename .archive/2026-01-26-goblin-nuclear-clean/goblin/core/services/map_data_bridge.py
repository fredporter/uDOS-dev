"""
uDOS Map Data Bridge
Provides world map data from core to Tauri/web interfaces

Version: 1.2.30
Date: 2025-12-27
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class MapDataBridge:
    """
    Bridge service for map data between core and UI layers.
    Provides world map data, TILE locations, and navigation support.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize map data bridge."""
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        self.project_root = project_root
        self.core_data_path = project_root / "core" / "data"

        # Load grid system
        try:
            from dev.goblin.core.services.uDOS_grid import Grid

            self.grid = Grid()
        except ImportError:
            logger.warning("Grid system not available")
            self.grid = None

        # Major cities with TILE codes
        self.major_cities = {
            "AA340": {
                "name": "Sydney",
                "country": "Australia",
                "population": 5300000,
                "layer": 100,
            },
            "JF57": {
                "name": "London",
                "country": "United Kingdom",
                "population": 9000000,
                "layer": 100,
            },
            "QR68": {
                "name": "Tokyo",
                "country": "Japan",
                "population": 14000000,
                "layer": 100,
            },
            "KL82": {
                "name": "New York",
                "country": "United States",
                "population": 8300000,
                "layer": 100,
            },
            "JC52": {
                "name": "Paris",
                "country": "France",
                "population": 2200000,
                "layer": 100,
            },
            "MN45": {
                "name": "Beijing",
                "country": "China",
                "population": 21500000,
                "layer": 100,
            },
            "HG39": {
                "name": "Moscow",
                "country": "Russia",
                "population": 12500000,
                "layer": 100,
            },
            "FH61": {
                "name": "Berlin",
                "country": "Germany",
                "population": 3600000,
                "layer": 100,
            },
            "CB28": {
                "name": "Los Angeles",
                "country": "United States",
                "population": 4000000,
                "layer": 100,
            },
            "PK73": {
                "name": "Shanghai",
                "country": "China",
                "population": 27000000,
                "layer": 100,
            },
        }

        # Layer definitions
        self.layers = {
            100: {
                "name": "World",
                "cell_size": "~83 km",
                "use": "Continental navigation",
            },
            200: {
                "name": "Region",
                "cell_size": "~2.78 km",
                "use": "Regional planning",
            },
            300: {"name": "City", "cell_size": "~93 m", "use": "Urban navigation"},
            400: {"name": "Block", "cell_size": "~3 m", "use": "Building layout"},
            500: {"name": "Room", "cell_size": "~10 cm", "use": "Interior mapping"},
            600: {
                "name": "Cloud",
                "cell_size": "Virtual",
                "use": "Cloud computing layer",
            },
            700: {
                "name": "Satellite",
                "cell_size": "Virtual",
                "use": "Orbital perspective",
            },
            800: {"name": "Space", "cell_size": "Virtual", "use": "Solar system"},
            850: {"name": "Galaxy", "cell_size": "Virtual", "use": "Galactic scale"},
        }

    # =========================================================================
    # WORLD MAP DATA
    # =========================================================================

    def get_world_map_data(self) -> Dict[str, Any]:
        """
        Get complete world map data for visualization.

        Returns:
            Dict with cities, layers, grid info
        """
        return {
            "cities": self.major_cities,
            "layers": self.layers,
            "grid": {
                "columns": 480,  # AA to RL
                "rows": 270,
                "total_cells": 129600,
                "column_range": "AA-RL",
                "row_range": "0-269",
            },
            "default_location": "AA340",
            "default_layer": 100,
        }

    def get_cities(self, layer: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get list of cities, optionally filtered by layer.

        Args:
            layer: Optional layer filter (100-850)

        Returns:
            List of city data dicts
        """
        cities = []
        for tile_code, city_data in self.major_cities.items():
            if layer is None or city_data["layer"] == layer:
                cities.append(
                    {
                        "tile": tile_code,
                        "name": city_data["name"],
                        "country": city_data["country"],
                        "population": city_data["population"],
                        "layer": city_data["layer"],
                    }
                )
        return cities

    def get_city_by_tile(self, tile_code: str) -> Optional[Dict[str, Any]]:
        """
        Get city data by TILE code.

        Args:
            tile_code: TILE code (e.g., "AA340")

        Returns:
            City data dict or None
        """
        city_data = self.major_cities.get(tile_code)
        if city_data:
            return {"tile": tile_code, **city_data}
        return None

    def get_city_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get city data by name.

        Args:
            name: City name

        Returns:
            City data dict or None
        """
        for tile_code, city_data in self.major_cities.items():
            if city_data["name"].lower() == name.lower():
                return {"tile": tile_code, **city_data}
        return None

    # =========================================================================
    # TILE SYSTEM
    # =========================================================================

    def validate_tile_code(self, tile_code: str) -> bool:
        """
        Validate TILE code format.

        Args:
            tile_code: TILE code to validate (e.g., "AA340" or "AA340-100")

        Returns:
            True if valid format
        """
        import re

        # Pattern: [A-Z]{2}\d{1,3}(-\d{3})?
        pattern = r"^[A-Z]{2}\d{1,3}(-\d{3})?$"
        return bool(re.match(pattern, tile_code))

    def parse_tile_code(self, tile_code: str) -> Optional[Dict[str, Any]]:
        """
        Parse TILE code into components.

        Args:
            tile_code: TILE code (e.g., "AA340-100")

        Returns:
            Dict with column, row, layer or None if invalid
        """
        if not self.validate_tile_code(tile_code):
            return None

        parts = tile_code.split("-")
        base = parts[0]
        layer = int(parts[1]) if len(parts) > 1 else None

        # Extract column (2 letters) and row (digits)
        column = base[:2]
        row = int(base[2:])

        return {
            "tile": tile_code,
            "column": column,
            "row": row,
            "layer": layer,
            "column_numeric": self._column_to_number(column),
        }

    def _column_to_number(self, column: str) -> int:
        """Convert 2-letter column code to numeric value (AA=0, AB=1, etc.)."""
        if len(column) != 2:
            return -1

        first = ord(column[0]) - ord("A")
        second = ord(column[1]) - ord("A")
        return first * 26 + second

    def _number_to_column(self, num: int) -> str:
        """Convert numeric value to 2-letter column code (0=AA, 1=AB, etc.)."""
        if num < 0 or num >= 480:
            return "??"

        first = num // 26
        second = num % 26
        return chr(ord("A") + first) + chr(ord("A") + second)

    # =========================================================================
    # LAYER SYSTEM
    # =========================================================================

    def get_layers(self) -> Dict[int, Dict[str, str]]:
        """Get all layer definitions."""
        return self.layers

    def get_layer_info(self, layer: int) -> Optional[Dict[str, str]]:
        """Get info for specific layer."""
        return self.layers.get(layer)

    def zoom_in(self, tile_code: str) -> Optional[str]:
        """
        Zoom in one layer (increase layer number for physical Earth).

        Args:
            tile_code: Current TILE code

        Returns:
            New TILE code or None if cannot zoom in
        """
        parsed = self.parse_tile_code(tile_code)
        if not parsed:
            return None

        current_layer = parsed["layer"] or 100

        # Earth layers: 100 -> 200 -> 300 -> 400 -> 500
        if current_layer < 500:
            next_layer = current_layer + 100
            return f"{parsed['column']}{parsed['row']}-{next_layer}"

        return None

    def zoom_out(self, tile_code: str) -> Optional[str]:
        """
        Zoom out one layer (decrease layer number for physical Earth).

        Args:
            tile_code: Current TILE code

        Returns:
            New TILE code or None if cannot zoom out
        """
        parsed = self.parse_tile_code(tile_code)
        if not parsed:
            return None

        current_layer = parsed["layer"] or 100

        # Earth layers: 500 -> 400 -> 300 -> 200 -> 100
        if current_layer > 100:
            prev_layer = current_layer - 100
            return f"{parsed['column']}{parsed['row']}-{prev_layer}"

        return None

    # =========================================================================
    # NAVIGATION
    # =========================================================================

    def get_adjacent_tiles(self, tile_code: str) -> Dict[str, Optional[str]]:
        """
        Get adjacent TILE codes in 4 directions.

        Args:
            tile_code: Center TILE code

        Returns:
            Dict with north, south, east, west TILE codes
        """
        parsed = self.parse_tile_code(tile_code)
        if not parsed:
            return {"north": None, "south": None, "east": None, "west": None}

        col_num = parsed["column_numeric"]
        row = parsed["row"]
        layer_suffix = f"-{parsed['layer']}" if parsed["layer"] else ""

        # Calculate adjacent tiles
        north = f"{parsed['column']}{row + 1}{layer_suffix}" if row < 269 else None
        south = f"{parsed['column']}{row - 1}{layer_suffix}" if row > 0 else None
        east = (
            f"{self._number_to_column(col_num + 1)}{row}{layer_suffix}"
            if col_num < 479
            else None
        )
        west = (
            f"{self._number_to_column(col_num - 1)}{row}{layer_suffix}"
            if col_num > 0
            else None
        )

        return {"north": north, "south": south, "east": east, "west": west}

    def calculate_distance(self, tile1: str, tile2: str) -> Optional[int]:
        """
        Calculate grid distance between two TILE codes (Manhattan distance).

        Args:
            tile1: First TILE code
            tile2: Second TILE code

        Returns:
            Grid distance or None if invalid
        """
        parsed1 = self.parse_tile_code(tile1)
        parsed2 = self.parse_tile_code(tile2)

        if not parsed1 or not parsed2:
            return None

        col_dist = abs(parsed1["column_numeric"] - parsed2["column_numeric"])
        row_dist = abs(parsed1["row"] - parsed2["row"])

        return col_dist + row_dist


# Singleton instance
_map_data_bridge: Optional[MapDataBridge] = None


def get_map_data_bridge(project_root: Optional[Path] = None) -> MapDataBridge:
    """Get singleton MapDataBridge instance."""
    global _map_data_bridge
    if _map_data_bridge is None:
        _map_data_bridge = MapDataBridge(project_root)
    return _map_data_bridge
