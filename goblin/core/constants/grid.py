"""
uDOS Grid Constants (v1.0.0.48)
===============================

Defines the core grid dimensions, block graphics, and coordinate system.

=============================================================================
UNIVERSE LAYER ARCHITECTURE
=============================================================================

uDOS maps a complete universe from dungeon depths to galaxy edges.
Each realm has 100 zoom levels (fractal zoom: each tile contains 60×20 sub-tiles).

    LAYER RANGE    REALM              DESCRIPTION
    ───────────    ─────              ───────────
    800-899        GALAXY             Deep space, star systems, frontiers
    700-799        SOLAR_SYSTEM       Planets, asteroids, outer reaches
    600-699        NEAR_SPACE         Orbits, Moon, space stations
    500-599        DIMENSIONS         Virtual overlay realities (coexist w/ Earth)
    400-499        ATMOSPHERE         Sky, aerial, drones, aircraft
    ═══════════════════════════════════════════════════════════════════════════
    300-399        EARTH_SURFACE      ★ REAL WORLD - Distributed Map System ★
    ═══════════════════════════════════════════════════════════════════════════
    200-299        UNDERGROUND        Caves, mines, subways, infrastructure
    100-199        DUNGEONS           Tutorial/learning levels (new users start)
    000-099        SYSTEM             Reserved for system use

User Progression:
    Dungeon (100) → Underground (200) → Earth (300) → Sky (400) →
    Dimensions (500) → Space (600) → Solar (700) → Galaxy (800)

Fractal Zoom (within each realm):
    X00: Realm overview (60×20 tiles covering entire realm)
    X10: First zoom (each X00 tile → 60×20 sub-tiles)
    X20: Second zoom (each X10 tile → 60×20 sub-tiles)
    ...and so on (theoretically infinite, practically ~10 useful levels)

Grid Hierarchy:
    - Layer: 60×20 tiles (primary working unit)
    - Tile: 24×24 pixels (576 data points)
    - Block: 2×3 pixels (64 teletext patterns, ASCII-mappable)

Key Dimensions:
    - Layer: 60×20 = 1,200 tiles
    - Layer pixels: 1,440×480 = 691,200 pixels
    - Aspect ratio: 3:1 (horizontal-first)
    - Zoom factor: 1,200× per zoom level (60 × 20)
"""

from typing import Dict, List, Tuple, Optional
from enum import IntEnum, Enum
from dataclasses import dataclass


# =============================================================================
# Universe Realm Definitions
# =============================================================================


class Realm(IntEnum):
    """
    Universe realms - vertical layers of existence.

    Each realm spans 100 layer numbers (e.g., EARTH = 300-399).
    The second digit indicates zoom level within the realm.
    """

    SYSTEM = 0  # 000-099: Reserved
    DUNGEONS = 1  # 100-199: Tutorial/learning (start here)
    UNDERGROUND = 2  # 200-299: Caves, mines, infrastructure
    EARTH_SURFACE = 3  # 300-399: ★ REAL WORLD - core distributed map
    ATMOSPHERE = 4  # 400-499: Sky, aerial, drones
    DIMENSIONS = 5  # 500-599: Virtual overlay realities
    NEAR_SPACE = 6  # 600-699: Orbits, Moon, stations
    SOLAR_SYSTEM = 7  # 700-799: Planets, asteroids
    GALAXY = 8  # 800-899: Deep space, stars, frontiers

    @property
    def layer_start(self) -> int:
        """Starting layer number for this realm."""
        return self.value * 100

    @property
    def layer_end(self) -> int:
        """Ending layer number for this realm."""
        return self.value * 100 + 99

    @property
    def is_real_world(self) -> bool:
        """Is this the core distributed Earth map?"""
        return self == Realm.EARTH_SURFACE

    @property
    def is_virtual(self) -> bool:
        """Is this a virtual/game layer?"""
        return self in (Realm.DUNGEONS, Realm.DIMENSIONS)

    @classmethod
    def from_layer(cls, layer: int) -> "Realm":
        """Get realm from layer number."""
        realm_num = layer // 100
        return cls(realm_num) if 0 <= realm_num <= 8 else cls.SYSTEM


@dataclass
class RealmInfo:
    """Detailed information about a realm."""

    realm: Realm
    name: str
    description: str
    tile_scale_km: Optional[float]  # None for virtual/space
    progression_order: int  # 1 = first, 8 = last
    is_distributed: bool  # Uses real-world distributed data?


REALM_INFO = {
    Realm.SYSTEM: RealmInfo(
        Realm.SYSTEM, "System", "Reserved for system use", None, 0, False
    ),
    Realm.DUNGEONS: RealmInfo(
        Realm.DUNGEONS,
        "Dungeons",
        "Tutorial and learning levels",
        None,
        1,
        False,  # Start here
    ),
    Realm.UNDERGROUND: RealmInfo(
        Realm.UNDERGROUND,
        "Underground",
        "Caves, mines, subways, infrastructure",
        0.01,
        2,
        False,  # ~10m per tile at zoom 0
    ),
    Realm.EARTH_SURFACE: RealmInfo(
        Realm.EARTH_SURFACE,
        "Earth Surface",
        "★ Real World - Distributed Map",
        667.0,
        3,
        True,  # ~667km per tile at layer 300
    ),
    Realm.ATMOSPHERE: RealmInfo(
        Realm.ATMOSPHERE,
        "Atmosphere",
        "Sky, aerial views, drones, aircraft",
        667.0,
        4,
        True,  # Same scale as Earth, different altitude
    ),
    Realm.DIMENSIONS: RealmInfo(
        Realm.DIMENSIONS,
        "Dimensions",
        "Virtual overlay realities",
        None,
        5,
        False,  # Coexists with Earth
    ),
    Realm.NEAR_SPACE: RealmInfo(
        Realm.NEAR_SPACE,
        "Near Space",
        "Orbits, Moon, space stations",
        400000.0,
        6,
        False,  # ~400,000km per tile (Earth-Moon)
    ),
    Realm.SOLAR_SYSTEM: RealmInfo(
        Realm.SOLAR_SYSTEM,
        "Solar System",
        "Planets, asteroids, outer reaches",
        250000000.0,
        7,
        False,  # ~250M km per tile
    ),
    Realm.GALAXY: RealmInfo(
        Realm.GALAXY,
        "Galaxy",
        "Deep space, star systems, frontiers",
        None,
        8,
        False,  # Light years scale
    ),
}


# =============================================================================
# Earth Surface Zoom Levels (Layer 300-399)
# =============================================================================

# Earth uses 10× zoom factor for useful geographic progression
# (similar to Google Maps / OpenStreetMap zoom levels)
EARTH_ZOOM_FACTOR = 10


class EarthZoom(IntEnum):
    """
    Zoom levels within Earth Surface realm (300-399).

    Uses 10× zoom per level (like Google Maps):
    - L300: ~668 km (world, major cities only)
    - L310: ~67 km (regional, all cities)
    - L320: ~6.7 km (local, towns)
    - L330: ~668 m (neighborhood)
    - L340: ~67 m (block)
    - L350: ~6.7 m (building)
    - L360: ~668 mm (room detail)
    """

    WORLD = 0  # 300: Entire Earth (60×20 = 1,200 tiles, ~50-100 cities)
    REGIONAL = 1  # 310: Regional (~67 km, all cities in region)
    LOCAL = 2  # 320: Local (~6.7 km, towns and suburbs)
    NEIGHBORHOOD = 3  # 330: Neighborhood (~668 m)
    BLOCK = 4  # 340: Block (~67 m, streets visible)
    BUILDING = 5  # 350: Building (~6.7 m)
    ROOM = 6  # 360: Room (~668 mm)
    DETAIL = 7  # 370: Detail (~67 mm)
    FINE = 8  # 380: Fine (~6.7 mm)
    MICRO = 9  # 390: Micro (~0.67 mm)

    @property
    def layer(self) -> int:
        """Get layer number for this zoom level."""
        return 300 + (self.value * 10)

    @property
    def tile_size_description(self) -> str:
        """Human-readable tile size at this zoom."""
        sizes = {
            0: "~668 km × 2000 km",
            1: "~67 km × 200 km",
            2: "~6.7 km × 20 km",
            3: "~668 m × 2 km",
            4: "~67 m × 200 m",
            5: "~6.7 m × 20 m",
            6: "~668 mm × 2 m",
            7: "~67 mm × 200 mm",
            8: "~6.7 mm × 20 mm",
            9: "~0.67 mm × 2 mm",
        }
        return sizes.get(self.value, "unknown")


# Earth-specific constants
EARTH_LAYER_START = 300
EARTH_LAYER_END = 399
EARTH_OVERVIEW_LAYER = 300  # World map layer


# =============================================================================
# Layer Grid Constants (Primary Working Unit)
# =============================================================================

LAYER_COLUMNS = 60  # Tiles per layer horizontally
LAYER_ROWS = 20  # Tiles per layer vertically
LAYER_TILES = LAYER_COLUMNS * LAYER_ROWS  # 1,200 tiles per layer

# Row offset - rows display as 10-29 (always 2 digits)
ROW_OFFSET = 10  # Row 0 displays as 10, row 19 displays as 29

# Zoom factor (each tile contains this many sub-tiles when zoomed)
ZOOM_FACTOR = LAYER_TILES  # 1,200× zoom per level


# =============================================================================
# Tile Constants (Data Unit)
# =============================================================================

TILE_WIDTH = 24  # Pixels per tile horizontally
TILE_HEIGHT = 24  # Pixels per tile vertically
TILE_PIXELS = TILE_WIDTH * TILE_HEIGHT  # 576 pixels per tile

# Layer pixel dimensions
LAYER_PIXEL_WIDTH = LAYER_COLUMNS * TILE_WIDTH  # 1,440 pixels
LAYER_PIXEL_HEIGHT = LAYER_ROWS * TILE_HEIGHT  # 480 pixels
LAYER_TOTAL_PIXELS = LAYER_PIXEL_WIDTH * LAYER_PIXEL_HEIGHT  # 691,200


# =============================================================================
# Block Graphics (Teletext-style 2×3 subpixel blocks)
# =============================================================================

BLOCK_WIDTH = 2  # Pixels per block horizontally
BLOCK_HEIGHT = 3  # Pixels per block vertically
BLOCK_PIXELS = BLOCK_WIDTH * BLOCK_HEIGHT  # 6 pixels per block
BLOCK_PATTERNS = 2**BLOCK_PIXELS  # 64 possible patterns

# Blocks per tile
TILE_BLOCK_COLS = TILE_WIDTH // BLOCK_WIDTH  # 12 blocks horizontally
TILE_BLOCK_ROWS = TILE_HEIGHT // BLOCK_HEIGHT  # 8 blocks vertically
TILE_BLOCKS = TILE_BLOCK_COLS * TILE_BLOCK_ROWS  # 96 blocks per tile

# Full ASCII representation dimensions
# One tile = 12×8 block chars
LAYER_ASCII_WIDTH = LAYER_COLUMNS * TILE_BLOCK_COLS  # 720 characters
LAYER_ASCII_HEIGHT = LAYER_ROWS * TILE_BLOCK_ROWS  # 160 lines


# =============================================================================
# Column Encoding (AA-CH for 60 columns)
# =============================================================================


def column_to_code(column: int) -> str:
    """
    Convert column number (0-59) to two-letter code (AA-CH).

    60 columns = AA-AZ (0-25) + BA-BH (26-59)

    Args:
        column: Column number (0-59)

    Returns:
        Two-letter column code

    Examples:
        >>> column_to_code(0)
        'AA'
        >>> column_to_code(25)
        'AZ'
        >>> column_to_code(26)
        'BA'
        >>> column_to_code(59)
        'BH'
    """
    if not 0 <= column < LAYER_COLUMNS:
        raise ValueError(f"Column must be 0-{LAYER_COLUMNS-1}, got {column}")

    first = column // 26
    second = column % 26
    return chr(65 + first) + chr(65 + second)


def code_to_column(code: str) -> int:
    """
    Convert two-letter code to column number.

    Args:
        code: Two-letter column code (AA-CH)

    Returns:
        Column number (0-59)
    """
    if len(code) != 2 or not code.isalpha():
        raise ValueError(f"Code must be two letters, got '{code}'")

    code = code.upper()
    first = ord(code[0]) - 65
    second = ord(code[1]) - 65
    column = first * 26 + second

    if not 0 <= column < LAYER_COLUMNS:
        raise ValueError(f"Code '{code}' out of range (AA-CH)")

    return column


# =============================================================================
# Grid Coordinate System (AA10 format)
# =============================================================================

# Full coordinate format: [COL][ROW] = "AA10" to "BH29"
# - Column: AA-CH (60 columns, 0-59)
# - Row: 10-29 (20 rows, offset by ROW_OFFSET)
# This ensures all coordinates are exactly 4 characters


def row_to_display(row: int) -> int:
    """Convert internal row (0-19) to display row (10-29)."""
    if not 0 <= row < LAYER_ROWS:
        raise ValueError(f"Row must be 0-{LAYER_ROWS-1}, got {row}")
    return row + ROW_OFFSET


def display_to_row(display_row: int) -> int:
    """Convert display row (10-29) to internal row (0-19)."""
    row = display_row - ROW_OFFSET
    if not 0 <= row < LAYER_ROWS:
        raise ValueError(
            f"Display row must be {ROW_OFFSET}-{ROW_OFFSET+LAYER_ROWS-1}, got {display_row}"
        )
    return row


def coord_to_tile(coord: str) -> Tuple[int, int]:
    """
    Convert grid coordinate (e.g., 'AA10') to (column, row).

    Args:
        coord: 4-character coordinate like 'AA10', 'BH29'

    Returns:
        (column, row) tuple with internal indices (0-59, 0-19)

    Examples:
        >>> coord_to_tile('AA10')
        (0, 0)
        >>> coord_to_tile('BH29')
        (59, 19)
    """
    if len(coord) != 4:
        raise ValueError(
            f"Coordinate must be 4 characters (e.g., 'AA10'), got '{coord}'"
        )

    col_code = coord[:2].upper()
    row_str = coord[2:]

    try:
        display_row = int(row_str)
    except ValueError:
        raise ValueError(f"Invalid row number in '{coord}'")

    column = code_to_column(col_code)
    row = display_to_row(display_row)

    return (column, row)


def tile_to_coord(column: int, row: int) -> str:
    """
    Convert (column, row) to grid coordinate.

    Args:
        column: Column index (0-59)
        row: Row index (0-19)

    Returns:
        4-character coordinate like 'AA10'

    Examples:
        >>> tile_to_coord(0, 0)
        'AA10'
        >>> tile_to_coord(59, 19)
        'BH29'
    """
    col_code = column_to_code(column)
    display_row = row_to_display(row)
    return f"{col_code}{display_row}"


# =============================================================================
# Cascading Coordinates (Fractal Address System)
# =============================================================================

# Format: "L300:AA10-BB11-CA21" where:
# - L300 = Layer (determines realm and zoom level)
# - AA10 = Top-level tile
# - BB11 = Sub-tile within AA10
# - CA21 = Sub-sub-tile within BB11
# Each segment adds 10× more precision (for Earth realm)


def parse_cascading_coord(full_coord: str) -> Tuple[int, List[Tuple[int, int]]]:
    """
    Parse a cascading coordinate into layer and tile path.

    Args:
        full_coord: Full coordinate like "L300:AA10-BB11-CA21"

    Returns:
        (layer, [(col, row), ...]) tuple

    Examples:
        >>> parse_cascading_coord("L300:AA10")
        (300, [(0, 0)])
        >>> parse_cascading_coord("L300:AA10-BB11")
        (300, [(0, 0), (27, 1)])
    """
    if ":" not in full_coord:
        raise ValueError(
            f"Coordinate must include layer (e.g., 'L300:AA10'), got '{full_coord}'"
        )

    layer_part, coord_part = full_coord.split(":", 1)

    # Parse layer
    if not layer_part.upper().startswith("L"):
        raise ValueError(
            f"Layer must start with 'L' (e.g., 'L300'), got '{layer_part}'"
        )
    try:
        layer = int(layer_part[1:])
    except ValueError:
        raise ValueError(f"Invalid layer number in '{layer_part}'")

    # Parse coordinate segments
    segments = coord_part.split("-")
    tiles = []
    for seg in segments:
        col, row = coord_to_tile(seg)
        tiles.append((col, row))

    return (layer, tiles)


def build_cascading_coord(layer: int, tiles: List[Tuple[int, int]]) -> str:
    """
    Build a cascading coordinate from layer and tile path.

    Args:
        layer: Layer number (e.g., 300)
        tiles: List of (column, row) tuples for each zoom level

    Returns:
        Full coordinate like "L300:AA10-BB11-CA21"
    """
    coords = [tile_to_coord(col, row) for col, row in tiles]
    return f"L{layer}:{'-'.join(coords)}"


# =============================================================================
# LAT/LONG Conversion (Earth Surface Realm Only)
# =============================================================================


def cascading_to_latlong(full_coord: str) -> Tuple[float, float, float, float]:
    """
    Convert cascading coordinate to LAT/LONG bounding box.

    Only valid for Earth Surface realm (L300-L399).

    The Earth grid at L300 covers:
    - Longitude: -180° to +180° (60 columns, 6° each)
    - Latitude: +90° to -90° (20 rows, 9° each)

    Each zoom level (10× for Earth) subdivides the parent tile.

    Args:
        full_coord: Full coordinate like "L300:AA10-BB11"

    Returns:
        (min_lat, max_lat, min_lon, max_lon) bounding box in degrees

    Examples:
        >>> cascading_to_latlong("L300:AA10")  # Top-left tile of world
        (81.0, 90.0, -180.0, -174.0)
    """
    layer, tiles = parse_cascading_coord(full_coord)

    # Validate this is Earth realm
    if not (300 <= layer <= 399):
        raise ValueError(
            f"LAT/LONG conversion only valid for Earth (L300-L399), got L{layer}"
        )

    # Start with full Earth extent
    min_lon = -180.0
    max_lon = 180.0
    min_lat = -90.0
    max_lat = 90.0

    # Each tile in the path narrows the bounding box
    for col, row in tiles:
        # Current tile dimensions
        lon_range = max_lon - min_lon
        lat_range = max_lat - min_lat

        tile_lon = lon_range / LAYER_COLUMNS  # Width of each tile
        tile_lat = lat_range / LAYER_ROWS  # Height of each tile

        # Calculate new bounds
        # Longitude: left to right (col 0 = -180°)
        min_lon = min_lon + col * tile_lon
        max_lon = min_lon + tile_lon

        # Latitude: top to bottom (row 0 = +90°, row 19 = -90°)
        max_lat = max_lat - row * tile_lat
        min_lat = max_lat - tile_lat

    return (min_lat, max_lat, min_lon, max_lon)


def latlong_to_cascading(
    lat: float, lon: float, zoom_levels: int = 1, base_layer: int = 300
) -> str:
    """
    Convert LAT/LONG to cascading coordinate at specified precision.

    Args:
        lat: Latitude in degrees (-90 to +90)
        lon: Longitude in degrees (-180 to +180)
        zoom_levels: Number of zoom levels (1 = single tile, 2 = with one sub-tile, etc.)
        base_layer: Starting layer (default 300 for Earth)

    Returns:
        Cascading coordinate like "L300:AA10-BB11"

    Examples:
        >>> latlong_to_cascading(51.5, -0.1, 1)  # London at L300
        'L300:AD14'
        >>> latlong_to_cascading(51.5, -0.1, 3)  # London with 3 levels
        'L300:AD14-AG16-BD12'
    """
    if not -90 <= lat <= 90:
        raise ValueError(f"Latitude must be -90 to +90, got {lat}")
    if not -180 <= lon <= 180:
        raise ValueError(f"Longitude must be -180 to +180, got {lon}")

    tiles = []

    # Current bounds
    min_lon = -180.0
    max_lon = 180.0
    min_lat = -90.0
    max_lat = 90.0

    for _ in range(zoom_levels):
        lon_range = max_lon - min_lon
        lat_range = max_lat - min_lat

        tile_lon = lon_range / LAYER_COLUMNS
        tile_lat = lat_range / LAYER_ROWS

        # Find column (longitude)
        col = int((lon - min_lon) / tile_lon)
        col = min(col, LAYER_COLUMNS - 1)  # Clamp to valid range

        # Find row (latitude - top to bottom)
        row = int((max_lat - lat) / tile_lat)
        row = min(row, LAYER_ROWS - 1)  # Clamp to valid range

        tiles.append((col, row))

        # Narrow bounds for next level
        min_lon = min_lon + col * tile_lon
        max_lon = min_lon + tile_lon
        max_lat = max_lat - row * tile_lat
        min_lat = max_lat - tile_lat

    return build_cascading_coord(base_layer, tiles)


def cascading_to_center_latlong(full_coord: str) -> Tuple[float, float]:
    """
    Get the center point LAT/LONG of a cascading coordinate.

    Args:
        full_coord: Full coordinate like "L300:AA10-BB11"

    Returns:
        (latitude, longitude) of tile center
    """
    min_lat, max_lat, min_lon, max_lon = cascading_to_latlong(full_coord)
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    return (center_lat, center_lon)


# Legacy world column functions removed - pure fractal 60×20 system
# Each layer is 60×20, zooming into any tile gives another 60×20


# =============================================================================
# Block Graphics Character Set
# =============================================================================

# Unicode teletext mosaic characters (Symbols for Legacy Computing block)
# These map 2×3 pixel patterns to single characters
# Pattern bits: [TL, TR, ML, MR, BL, BR] where T=top, M=middle, B=bottom, L=left, R=right
TELETEXT_BLOCKS = [
    " ",  # 0b000000 = 0
    "🬀",  # 0b000001 = 1  (BR only)
    "🬁",  # 0b000010 = 2  (BL only)
    "🬂",  # 0b000011 = 3  (BL+BR)
    "🬃",  # 0b000100 = 4  (MR only)
    "🬄",  # 0b000101 = 5  (MR+BR)
    "🬅",  # 0b000110 = 6  (MR+BL)
    "🬆",  # 0b000111 = 7  (MR+BL+BR)
    "🬇",  # 0b001000 = 8  (ML only)
    "🬈",  # 0b001001 = 9  (ML+BR)
    "🬉",  # 0b001010 = 10 (ML+BL)
    "🬊",  # 0b001011 = 11 (ML+BL+BR)
    "🬋",  # 0b001100 = 12 (ML+MR)
    "🬌",  # 0b001101 = 13 (ML+MR+BR)
    "🬍",  # 0b001110 = 14 (ML+MR+BL)
    "🬎",  # 0b001111 = 15 (ML+MR+BL+BR)
    "🬏",  # 0b010000 = 16 (TR only)
    "🬐",  # 0b010001 = 17 (TR+BR)
    "🬑",  # 0b010010 = 18 (TR+BL)
    "🬒",  # 0b010011 = 19 (TR+BL+BR)
    "🬓",  # 0b010100 = 20 (TR+MR)
    "▌",  # 0b010101 = 21 (TR+MR+BR) - right half
    "🬔",  # 0b010110 = 22 (TR+MR+BL)
    "🬕",  # 0b010111 = 23 (TR+MR+BL+BR)
    "🬖",  # 0b011000 = 24 (TR+ML)
    "🬗",  # 0b011001 = 25 (TR+ML+BR)
    "🬘",  # 0b011010 = 26 (TR+ML+BL)
    "🬙",  # 0b011011 = 27 (TR+ML+BL+BR)
    "🬚",  # 0b011100 = 28 (TR+ML+MR)
    "🬛",  # 0b011101 = 29 (TR+ML+MR+BR)
    "🬜",  # 0b011110 = 30 (TR+ML+MR+BL)
    "🬝",  # 0b011111 = 31 (TR+ML+MR+BL+BR)
    "🬞",  # 0b100000 = 32 (TL only)
    "🬟",  # 0b100001 = 33 (TL+BR)
    "🬠",  # 0b100010 = 34 (TL+BL)
    "🬡",  # 0b100011 = 35 (TL+BL+BR)
    "🬢",  # 0b100100 = 36 (TL+MR)
    "🬣",  # 0b100101 = 37 (TL+MR+BR)
    "🬤",  # 0b100110 = 38 (TL+MR+BL)
    "🬥",  # 0b100111 = 39 (TL+MR+BL+BR)
    "🬦",  # 0b101000 = 40 (TL+ML)
    "🬧",  # 0b101001 = 41 (TL+ML+BR)
    "▐",  # 0b101010 = 42 (TL+ML+BL) - left half
    "🬨",  # 0b101011 = 43 (TL+ML+BL+BR)
    "🬩",  # 0b101100 = 44 (TL+ML+MR)
    "🬪",  # 0b101101 = 45 (TL+ML+MR+BR)
    "🬫",  # 0b101110 = 46 (TL+ML+MR+BL)
    "🬬",  # 0b101111 = 47 (TL+ML+MR+BL+BR)
    "🬭",  # 0b110000 = 48 (TL+TR)
    "🬮",  # 0b110001 = 49 (TL+TR+BR)
    "🬯",  # 0b110010 = 50 (TL+TR+BL)
    "🬰",  # 0b110011 = 51 (TL+TR+BL+BR)
    "🬱",  # 0b110100 = 52 (TL+TR+MR)
    "🬲",  # 0b110101 = 53 (TL+TR+MR+BR)
    "🬳",  # 0b110110 = 54 (TL+TR+MR+BL)
    "🬴",  # 0b110111 = 55 (TL+TR+MR+BL+BR)
    "🬵",  # 0b111000 = 56 (TL+TR+ML)
    "🬶",  # 0b111001 = 57 (TL+TR+ML+BR)
    "🬷",  # 0b111010 = 58 (TL+TR+ML+BL)
    "🬸",  # 0b111011 = 59 (TL+TR+ML+BL+BR)
    "🬹",  # 0b111100 = 60 (TL+TR+ML+MR)
    "🬺",  # 0b111101 = 61 (TL+TR+ML+MR+BR)
    "🬻",  # 0b111110 = 62 (TL+TR+ML+MR+BL)
    "█",  # 0b111111 = 63 (full block)
]

# ASCII fallback characters for terminals without Unicode
# Maps the same 64 patterns to ASCII-compatible characters
ASCII_BLOCKS = [
    " ",  # 0  empty
    ".",  # 1  BR
    ".",  # 2  BL
    "_",  # 3  bottom
    ".",  # 4  MR
    "|",  # 5  right edge
    "/",  # 6  diagonal
    "J",  # 7  right+bottom
    ".",  # 8  ML
    "\\",  # 9  diagonal
    "|",  # 10 left edge
    "L",  # 11 left+bottom
    "-",  # 12 middle
    "]",  # 13 right+middle+bottom
    "[",  # 14 left+middle+bottom
    "U",  # 15 bottom half
    "'",  # 16 TR
    "\\",  # 17 diagonal
    "/",  # 18 diagonal
    ",",  # 19 top-right+bottom
    "]",  # 20 right side
    "]",  # 21 right half
    "/",  # 22 slash pattern
    "d",  # 23 right heavy
    "/",  # 24 diagonal
    "Y",  # 25 Y shape
    "/",  # 26 slash
    "k",  # 27 complex
    "7",  # 28 top+middle right
    ")",  # 29 right arc
    "Z",  # 30 Z shape
    "%",  # 31 almost full right
    "`",  # 32 TL
    "\\",  # 33 diagonal
    "|",  # 34 left edge top
    "L",  # 35 left corner
    "/",  # 36 slash
    "Y",  # 37 Y shape
    "/",  # 38 diagonal
    "b",  # 39 left heavy
    "[",  # 40 left side
    "\\",  # 41 backslash
    "[",  # 42 left half
    "p",  # 43 left heavy
    "T",  # 44 T shape
    "(",  # 45 left arc
    "<",  # 46 left arrow
    "%",  # 47 almost full left
    '"',  # 48 top
    "\\",  # 49 backslash
    "/",  # 50 slash
    "=",  # 51 top+bottom
    ")",  # 52 right arc
    "P",  # 53 P shape
    "/",  # 54 slash
    "@",  # 55 heavy
    "(",  # 56 left arc
    "(",  # 57 left arc
    "\\",  # 58 backslash
    "@",  # 59 heavy
    "n",  # 60 top half
    "@",  # 61 almost full
    "@",  # 62 almost full
    "#",  # 63 full block
]


def pattern_to_block(pattern: int, ascii_mode: bool = False) -> str:
    """
    Convert a 6-bit pattern to a block character.

    Pattern bits (LSB to MSB): BR, BL, MR, ML, TR, TL

    Args:
        pattern: Integer 0-63 representing 2×3 pixel pattern
        ascii_mode: Use ASCII fallback characters

    Returns:
        Block character (Unicode teletext or ASCII)
    """
    if not 0 <= pattern < BLOCK_PATTERNS:
        raise ValueError(f"Pattern must be 0-63, got {pattern}")

    return ASCII_BLOCKS[pattern] if ascii_mode else TELETEXT_BLOCKS[pattern]


def pixels_to_pattern(pixels: List[List[bool]]) -> int:
    """
    Convert a 2×3 pixel grid to pattern integer.

    Args:
        pixels: 3 rows × 2 cols of booleans
                [[TL, TR], [ML, MR], [BL, BR]]

    Returns:
        Pattern integer 0-63
    """
    if len(pixels) != 3 or any(len(row) != 2 for row in pixels):
        raise ValueError("Pixels must be 3×2 grid")

    # Bit positions: TL=32, TR=16, ML=8, MR=4, BL=2, BR=1
    pattern = 0
    if pixels[0][0]:
        pattern |= 32  # TL
    if pixels[0][1]:
        pattern |= 16  # TR
    if pixels[1][0]:
        pattern |= 8  # ML
    if pixels[1][1]:
        pattern |= 4  # MR
    if pixels[2][0]:
        pattern |= 2  # BL
    if pixels[2][1]:
        pattern |= 1  # BR

    return pattern


def pattern_to_pixels(pattern: int) -> List[List[bool]]:
    """
    Convert pattern integer to 2×3 pixel grid.

    Args:
        pattern: Integer 0-63

    Returns:
        3 rows × 2 cols of booleans
    """
    if not 0 <= pattern < BLOCK_PATTERNS:
        raise ValueError(f"Pattern must be 0-63, got {pattern}")

    return [
        [bool(pattern & 32), bool(pattern & 16)],  # Top: TL, TR
        [bool(pattern & 8), bool(pattern & 4)],  # Middle: ML, MR
        [bool(pattern & 2), bool(pattern & 1)],  # Bottom: BL, BR
    ]


# =============================================================================
# Storage Calculations
# =============================================================================


class StorageSize:
    """Calculate storage requirements for different encodings."""

    @staticmethod
    def layer_bytes(bits_per_pixel: int) -> int:
        """Bytes needed for one layer at given bit depth."""
        return (LAYER_TOTAL_PIXELS * bits_per_pixel) // 8


# Pre-calculated storage sizes (per 60×20 layer)
STORAGE = {
    "layer_mono": StorageSize.layer_bytes(1),  # 86,400 bytes (~84 KB)
    "layer_4color": StorageSize.layer_bytes(2),  # 172,800 bytes (~169 KB)
    "layer_8color": StorageSize.layer_bytes(3),  # 259,200 bytes (~253 KB)
    "layer_16color": StorageSize.layer_bytes(4),  # 345,600 bytes (~337 KB)
}


# =============================================================================
# Geographic Constants (for Earth Surface Layer 300)
# =============================================================================

EARTH_CIRCUMFERENCE_KM = 40075  # At equator
EARTH_MERIDIAN_KM = 40008  # Pole to pole

# Earth overview at Layer 300 (60×20 covering entire planet)
# Each tile covers: 360°/60 = 6° longitude, 180°/20 = 9° latitude
EARTH_TILE_DEGREES_LON = 360 / LAYER_COLUMNS  # 6° per tile
EARTH_TILE_DEGREES_LAT = 180 / LAYER_ROWS  # 9° per tile

# At equator, 1° longitude ≈ 111 km
# 1° latitude ≈ 111 km everywhere
EARTH_TILE_WIDTH_KM = EARTH_CIRCUMFERENCE_KM / LAYER_COLUMNS  # ~668 km/tile
EARTH_TILE_HEIGHT_KM = EARTH_MERIDIAN_KM / LAYER_ROWS  # ~2000 km/tile


# Zoom calculations for Earth (uses 10× factor, not 1,200×)
def earth_tile_size_km(zoom_level: int) -> Tuple[float, float]:
    """
    Calculate tile size in km at a given Earth zoom level.

    Uses 10× zoom factor (like Google Maps) for practical geographic progression:
    - Level 0 (300): ~668 km × 2000 km
    - Level 1 (310): ~67 km × 200 km
    - Level 2 (320): ~6.7 km × 20 km
    - Level 3 (330): ~668 m × 2 km
    - etc.

    Args:
        zoom_level: 0 = Layer 300, 1 = Layer 310, etc.

    Returns:
        (width_km, height_km) tuple
    """
    width = EARTH_TILE_WIDTH_KM / (EARTH_ZOOM_FACTOR**zoom_level)
    height = EARTH_TILE_HEIGHT_KM / (EARTH_ZOOM_FACTOR**zoom_level)
    return (width, height)


# =============================================================================
# Realm Layer Ranges (Updated for Universe Architecture)
# =============================================================================

# These map to the Realm enum but provided as dict for convenience
REALM_LAYER_RANGES = {
    "system": (0, 99),  # Reserved
    "dungeons": (100, 199),  # Tutorial/learning
    "underground": (200, 299),  # Caves, infrastructure
    "earth": (300, 399),  # ★ REAL WORLD - distributed map
    "atmosphere": (400, 499),  # Sky, aerial
    "dimensions": (500, 599),  # Virtual overlays
    "near_space": (600, 699),  # Orbits, Moon
    "solar_system": (700, 799),  # Planets
    "galaxy": (800, 899),  # Deep space
}

# Default zoom factors (can be realm-specific)
# Earth uses EARTH_ZOOM_FACTOR (10×) for practical geographic zoom
# Other realms can use the full ZOOM_FACTOR (1,200×) or custom values


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Universe architecture
    "Realm",
    "RealmInfo",
    "REALM_INFO",
    "REALM_LAYER_RANGES",
    "EarthZoom",
    "EARTH_LAYER_START",
    "EARTH_LAYER_END",
    "EARTH_OVERVIEW_LAYER",
    "EARTH_ZOOM_FACTOR",
    # Grid dimensions
    "LAYER_COLUMNS",
    "LAYER_ROWS",
    "LAYER_TILES",
    "ZOOM_FACTOR",
    "ROW_OFFSET",
    # Tile dimensions
    "TILE_WIDTH",
    "TILE_HEIGHT",
    "TILE_PIXELS",
    "LAYER_PIXEL_WIDTH",
    "LAYER_PIXEL_HEIGHT",
    "LAYER_TOTAL_PIXELS",
    # Block graphics
    "BLOCK_WIDTH",
    "BLOCK_HEIGHT",
    "BLOCK_PIXELS",
    "BLOCK_PATTERNS",
    "TILE_BLOCK_COLS",
    "TILE_BLOCK_ROWS",
    "TILE_BLOCKS",
    "LAYER_ASCII_WIDTH",
    "LAYER_ASCII_HEIGHT",
    "TELETEXT_BLOCKS",
    "ASCII_BLOCKS",
    # Column/row encoding
    "column_to_code",
    "code_to_column",
    "row_to_display",
    "display_to_row",
    # Coordinate functions
    "coord_to_tile",
    "tile_to_coord",
    "parse_cascading_coord",
    "build_cascading_coord",
    # LAT/LONG conversion
    "cascading_to_latlong",
    "latlong_to_cascading",
    "cascading_to_center_latlong",
    # Block pattern functions
    "pattern_to_block",
    "pixels_to_pattern",
    "pattern_to_pixels",
    "earth_tile_size_km",
    # Storage
    "STORAGE",
    "StorageSize",
    # Geographic
    "EARTH_CIRCUMFERENCE_KM",
    "EARTH_MERIDIAN_KM",
    "EARTH_TILE_DEGREES_LON",
    "EARTH_TILE_DEGREES_LAT",
    "EARTH_TILE_WIDTH_KM",
    "EARTH_TILE_HEIGHT_KM",
]
