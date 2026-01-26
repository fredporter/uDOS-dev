"""
uDOS Grid Utilities
===================
Grid coordinate conversion and TILE code management for the universal grid system.

Grid Specifications (v1.0.0.49 - Pure Fractal 60×20 System):
- Layer grid: 60 columns × 20 rows (1,200 tiles per layer)
- Tile: 24×24 pixels (576 data points per tile)
- Column encoding: AA-CH (60 columns, 0-59)
- Row encoding: 10-29 (20 rows, offset by ROW_OFFSET=10)
- Coordinate format: [COL][ROW] = 4 characters (e.g., "AA10", "CH29")

Cascading Coordinates:
- Format: L[LAYER]:[TILE]-[SUBTILE]-[SUBSUBTILE]...
- Example: L300:BD14-CG15-BT21
- Each level is a 60×20 subdivision of the parent tile
- Provides ~50m precision at 3 levels

Universe Layer Architecture:
- 000-099: System (reserved)
- 100-199: Dungeons (tutorial/learning)
- 200-299: Underground (caves, mines)
- 300-399: Earth Surface (★ real world distributed map)
- 400-499: Atmosphere (sky, aerial)
- 500-599: Dimensions (virtual overlays)
- 600-699: Near Space (orbits, Moon)
- 700-799: Solar System (planets)
- 800-899: Galaxy (deep space)

Version: 1.0.0.49
"""

import math
from typing import Tuple, Optional, List, Dict, Any


# Import from canonical source
from dev.goblin.core.constants.grid import (
    LAYER_COLUMNS,
    LAYER_ROWS,
    LAYER_TILES,
    ROW_OFFSET,
    EARTH_CIRCUMFERENCE_KM,
    EARTH_MERIDIAN_KM,
    EARTH_ZOOM_FACTOR,
    # Coordinate functions
    column_to_code,
    code_to_column,
    row_to_display,
    display_to_row,
    tile_to_coord,
    coord_to_tile,
    # Cascading coordinate functions
    parse_cascading_coord,
    build_cascading_coord,
    cascading_to_latlong,
    latlong_to_cascading,
    cascading_to_center_latlong,
    # Realm info
    Realm,
    REALM_INFO,
)


# =============================================================================
# Legacy Format Support
# =============================================================================

# Old format: "AA0-100" (col+row-layer)
# New format: "L300:AA10" (layer:col+row)


def legacy_to_cascading(legacy_code: str) -> str:
    """
    Convert legacy TILE format to cascading format.

    Old format: "AA0-100" or "CH27-300"
    New format: "L300:AA10" or "L300:CH27"

    Args:
        legacy_code: Legacy tile code (e.g., "AA0-100")

    Returns:
        Cascading coordinate (e.g., "L100:AA10")
    """
    parts = legacy_code.split("-")
    if len(parts) < 2:
        raise ValueError(f"Invalid legacy code: {legacy_code}")

    grid_cell = parts[0]
    layer = int(parts[1])

    # Parse old grid cell (col_code + row_without_offset)
    if len(grid_cell) < 3:
        raise ValueError(f"Invalid grid cell: {grid_cell}")

    col_code = grid_cell[:2].upper()
    old_row = int(grid_cell[2:])

    # Convert to new row with offset
    new_row = old_row + ROW_OFFSET

    return f"L{layer}:{col_code}{new_row}"


def cascading_to_legacy(cascading_code: str) -> str:
    """
    Convert cascading format back to legacy format (single level only).

    New format: "L300:AA10"
    Old format: "AA0-300"

    Args:
        cascading_code: Cascading coordinate (e.g., "L300:AA10")

    Returns:
        Legacy tile code (e.g., "AA0-300")
    """
    layer, tiles = parse_cascading_coord(cascading_code)

    if len(tiles) != 1:
        raise ValueError(
            f"Can only convert single-level cascading coords, got {len(tiles)} levels"
        )

    col, row = tiles[0]
    col_code = column_to_code(col)
    old_row = row  # Row is already internal (0-19), no offset in legacy

    return f"{col_code}{old_row}-{layer}"


# =============================================================================
# Grid Navigation
# =============================================================================


def get_adjacent_tiles(coord: str) -> Dict[str, str]:
    """
    Get adjacent tile coordinates (N, S, E, W, NE, NW, SE, SW).

    Args:
        coord: Tile coordinate (e.g., "AA10" or "L300:AA10")

    Returns:
        Dictionary of adjacent tiles

    Example:
        >>> get_adjacent_tiles("BE20")
        {'N': 'BE19', 'S': 'BE21', 'E': 'BF20', 'W': 'BD20', ...}
    """
    # Handle cascading format
    layer = None
    if ":" in coord:
        layer_part, tile_part = coord.split(":", 1)
        layer = int(layer_part[1:])
        # Get first tile only
        first_tile = tile_part.split("-")[0]
        col, row = coord_to_tile(first_tile)
    else:
        col, row = coord_to_tile(coord)

    adjacent = {}

    # North (row decreases)
    if row > 0:
        adj_coord = tile_to_coord(col, row - 1)
        adjacent["N"] = f"L{layer}:{adj_coord}" if layer else adj_coord

    # South (row increases)
    if row < LAYER_ROWS - 1:
        adj_coord = tile_to_coord(col, row + 1)
        adjacent["S"] = f"L{layer}:{adj_coord}" if layer else adj_coord

    # East (column increases)
    if col < LAYER_COLUMNS - 1:
        adj_coord = tile_to_coord(col + 1, row)
        adjacent["E"] = f"L{layer}:{adj_coord}" if layer else adj_coord

    # West (column decreases)
    if col > 0:
        adj_coord = tile_to_coord(col - 1, row)
        adjacent["W"] = f"L{layer}:{adj_coord}" if layer else adj_coord

    # Diagonals
    if row > 0 and col < LAYER_COLUMNS - 1:
        adj_coord = tile_to_coord(col + 1, row - 1)
        adjacent["NE"] = f"L{layer}:{adj_coord}" if layer else adj_coord

    if row > 0 and col > 0:
        adj_coord = tile_to_coord(col - 1, row - 1)
        adjacent["NW"] = f"L{layer}:{adj_coord}" if layer else adj_coord

    if row < LAYER_ROWS - 1 and col < LAYER_COLUMNS - 1:
        adj_coord = tile_to_coord(col + 1, row + 1)
        adjacent["SE"] = f"L{layer}:{adj_coord}" if layer else adj_coord

    if row < LAYER_ROWS - 1 and col > 0:
        adj_coord = tile_to_coord(col - 1, row + 1)
        adjacent["SW"] = f"L{layer}:{adj_coord}" if layer else adj_coord

    return adjacent


def get_tiles_in_range(
    start_col: int, start_row: int, end_col: int, end_row: int
) -> List[str]:
    """
    Get all tile coordinates in a rectangular range.

    Args:
        start_col: Starting column (0-59)
        start_row: Starting row (0-19)
        end_col: Ending column (inclusive)
        end_row: Ending row (inclusive)

    Returns:
        List of tile coordinates
    """
    tiles = []
    for row in range(start_row, min(end_row + 1, LAYER_ROWS)):
        for col in range(start_col, min(end_col + 1, LAYER_COLUMNS)):
            tiles.append(tile_to_coord(col, row))
    return tiles


# =============================================================================
# Distance Calculations
# =============================================================================


def calculate_distance_km(coord1: str, coord2: str) -> float:
    """
    Calculate approximate distance between two coordinates in kilometers.
    Uses Haversine formula. Only valid for Earth Surface realm (L300-L399).

    Args:
        coord1: First cascading coordinate (e.g., "L300:BD14")
        coord2: Second cascading coordinate (e.g., "L300:AR15")

    Returns:
        Distance in kilometers
    """
    lat1, lon1 = cascading_to_center_latlong(coord1)
    lat2, lon2 = cascading_to_center_latlong(coord2)

    # Haversine formula
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Earth's radius in km
    radius = 6371
    distance = radius * c

    return round(distance, 1)


def tile_distance(coord1: str, coord2: str) -> int:
    """
    Calculate Manhattan distance in tiles between two coordinates.

    Args:
        coord1: First coordinate (e.g., "AA10")
        coord2: Second coordinate (e.g., "BE20")

    Returns:
        Number of tiles (Manhattan distance)
    """
    col1, row1 = coord_to_tile(coord1)
    col2, row2 = coord_to_tile(coord2)
    return abs(col2 - col1) + abs(row2 - row1)


# =============================================================================
# Coordinate Validation
# =============================================================================


def validate_coord(coord: str) -> bool:
    """
    Validate a tile coordinate.

    Args:
        coord: Coordinate to validate (e.g., "AA10" or "L300:AA10-BB11")

    Returns:
        True if valid, False otherwise
    """
    try:
        if ":" in coord:
            parse_cascading_coord(coord)
        else:
            coord_to_tile(coord)
        return True
    except (ValueError, IndexError):
        return False


def validate_layer(layer: int) -> bool:
    """
    Validate a layer number.

    Args:
        layer: Layer number (0-899)

    Returns:
        True if valid realm exists
    """
    try:
        Realm.from_layer(layer)
        return True
    except ValueError:
        return False


def get_realm_for_layer(layer: int) -> Tuple[Realm, str]:
    """
    Get realm information for a layer number.

    Args:
        layer: Layer number (0-899)

    Returns:
        (Realm, description) tuple
    """
    realm = Realm.from_layer(layer)
    info = REALM_INFO[realm]
    return (realm, info.description)


# =============================================================================
# Coordinate Formatting
# =============================================================================


def format_coord_display(coord: str) -> str:
    """
    Format coordinate for display with realm context.

    Args:
        coord: Cascading coordinate (e.g., "L300:BD14")

    Returns:
        Formatted string with realm info
    """
    if ":" not in coord:
        return coord

    layer, tiles = parse_cascading_coord(coord)
    realm, desc = get_realm_for_layer(layer)

    tile_strs = [tile_to_coord(col, row) for col, row in tiles]
    return f"[{realm.name}] L{layer}:{'-'.join(tile_strs)}"


def coord_to_json(coord: str) -> Dict[str, Any]:
    """
    Convert coordinate to JSON-serializable dictionary.

    Args:
        coord: Cascading coordinate

    Returns:
        Dictionary with coordinate components
    """
    if ":" not in coord:
        col, row = coord_to_tile(coord)
        return {
            "type": "simple",
            "coord": coord,
            "column": col,
            "row": row,
            "column_code": column_to_code(col),
            "display_row": row_to_display(row),
        }

    layer, tiles = parse_cascading_coord(coord)
    realm = Realm.from_layer(layer)

    return {
        "type": "cascading",
        "coord": coord,
        "layer": layer,
        "realm": realm.name,
        "tiles": [
            {
                "column": col,
                "row": row,
                "coord": tile_to_coord(col, row),
            }
            for col, row in tiles
        ],
        "depth": len(tiles),
    }


# =============================================================================
# Test / Demo
# =============================================================================

if __name__ == "__main__":
    print("Grid Utilities Test (v1.0.0.49 - Pure Fractal 60×20)")
    print("=" * 60)
    print(f"Layer grid: {LAYER_COLUMNS}×{LAYER_ROWS} ({LAYER_TILES} tiles)")
    print(f"Row range: {ROW_OFFSET}-{ROW_OFFSET + LAYER_ROWS - 1} (always 2 digits)")
    print(f"Column range: AA-CH (60 columns)")
    print()

    # Test basic coordinates
    print("Basic Coordinates:")
    for col, row, desc in [
        (0, 0, "Top-left"),
        (59, 0, "Top-right"),
        (0, 19, "Bottom-left"),
        (59, 19, "Bottom-right"),
    ]:
        coord = tile_to_coord(col, row)
        print(f"  ({col}, {row}) = {coord}  [{desc}]")

    print()

    # Test London cascading coordinate
    print("London (51.5°N, 0.1°W):")
    london = latlong_to_cascading(51.5, -0.1, 3)
    print(f"  Cascading: {london}")
    center = cascading_to_center_latlong(london)
    print(f"  Center: {center[0]:.4f}°, {center[1]:.4f}°")

    print()

    # Test adjacent tiles
    print("Adjacent to BE20:")
    adjacent = get_adjacent_tiles("BE20")
    for direction, adj_coord in adjacent.items():
        print(f"  {direction}: {adj_coord}")

    print()

    # Test distance
    london_coord = latlong_to_cascading(51.5, -0.1, 1)
    paris_coord = latlong_to_cascading(48.9, 2.3, 1)
    dist = calculate_distance_km(london_coord, paris_coord)
    print(f"Distance London-Paris: {dist} km")
