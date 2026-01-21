"""
Tile Hierarchy Service

Manages hierarchical relationships between tiles across universe layers.
Enables knowledge cascading from parent tiles to children.

Part of uDOS Alpha v1.0.0.56+

Layer Architecture (000-799):
    000-099  SYSTEM         Reserved for system operations
    100-199  DUNGEONS       Procedural/tutorial (1 zoom = 11km)
    200-299  SUBTERRANEAN   Underground (3 zoom = 3.1m) ★
    300-399  EARTH          Surface reality (3 zoom = 3.1m) ★
    400-499  DIMENSIONS     AR/Virtual overlay (3 zoom = 3.1m) ★
    500-599  ATMOSPHERE     Sky, aerial, flight (1 zoom = 11km)
    600-699  SOLAR_SYSTEM   Moon, planets, orbit (1 zoom = 11km)
    700-799  GALAXY         Stars, deep space (1 zoom = 11km)

Zoom Depth Rules:
    - SUBTERRANEAN, EARTH, DIMENSIONS: 3 levels (3.1m precision)
    - All others: 1 level (11km precision)

Address Format:
    Earth/Subterranean/Dimensions (3 levels):
        L300:BD14                    = 668 km (continent)
        L300:BD14:AA10               = 11 km (city)
        L300:BD14:AA10:BB15          = 185 m (suburb)
        L300:BD14:AA10:BB15:CC20     = 3.1 m (front door) ← MAX

    Other realms (1 level):
        L600:BD14                    = 668 km
        L600:BD14:AA10               = 11 km ← MAX

Vertical Alignment:
    Same address = same physical Earth location across precision trio:
        L200:BD14:AA10:BB15:CC20  = Underground at THIS spot
        L300:BD14:AA10:BB15:CC20  = Surface at THIS spot
        L400:BD14:AA10:BB15:CC20  = AR marker at THIS spot
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("tile-hierarchy")


# Grid constants
GRID_COLS = 60  # AA-CH (A=0, B=1, ... A=0+26=26, B=27, etc)
GRID_ROWS = 20  # 10-29 (ROW_OFFSET = 10)
ROW_OFFSET = 10
EARTH_ZOOM_FACTOR = 10  # Each layer zoom = 10x


class LayerRealm(Enum):
    """
    Universe layer realms.

    Vertical stacking (bottom to top):
        SYSTEM (000-099)      - Reserved for system ops
        DUNGEONS (100-199)    - Procedural/tutorial
        SUBTERRANEAN (200-299) - Underground (3.1m precision)
        EARTH (300-399)       - Surface reality (3.1m precision)
        DIMENSIONS (400-499)  - AR/Virtual overlay (3.1m precision)
        ATMOSPHERE (500-599)  - Sky, aerial, flight
        SOLAR_SYSTEM (600-699) - Moon, planets, orbit
        GALAXY (700-799)      - Stars, deep space
    """

    SYSTEM = "system"  # 000-099
    DUNGEONS = "dungeons"  # 100-199
    SUBTERRANEAN = "subterranean"  # 200-299 (was UNDERGROUND)
    EARTH = "earth"  # 300-399
    DIMENSIONS = "dimensions"  # 400-499 (moved from 500-599)
    ATMOSPHERE = "atmosphere"  # 500-599 (moved from 400-499)
    SOLAR_SYSTEM = "solar_system"  # 600-699 (merged NEAR_SPACE + SOLAR)
    GALAXY = "galaxy"  # 700-799 (was 800-899)


@dataclass
class TileLocation:
    """A precise location in the universe layer system."""

    layer: int  # 000-899
    col: str  # AA-CH
    row: int  # 10-29

    @property
    def coord(self) -> str:
        """Get tile coordinate string (e.g., 'BD14')."""
        return f"{self.col}{self.row}"

    @property
    def full_path(self) -> str:
        """Get full layer:tile path (e.g., 'L300:BD14')."""
        return f"L{self.layer:03d}:{self.coord}"

    @property
    def realm(self) -> LayerRealm:
        """Get the realm this tile belongs to."""
        if 0 <= self.layer < 100:
            return LayerRealm.SYSTEM
        elif 100 <= self.layer < 200:
            return LayerRealm.DUNGEONS
        elif 200 <= self.layer < 300:
            return LayerRealm.SUBTERRANEAN
        elif 300 <= self.layer < 400:
            return LayerRealm.EARTH
        elif 400 <= self.layer < 500:
            return LayerRealm.DIMENSIONS
        elif 500 <= self.layer < 600:
            return LayerRealm.ATMOSPHERE
        elif 600 <= self.layer < 700:
            return LayerRealm.SOLAR_SYSTEM
        elif 700 <= self.layer < 800:
            return LayerRealm.GALAXY
        return LayerRealm.SYSTEM

    def __str__(self) -> str:
        return self.full_path

    def __hash__(self) -> int:
        return hash(self.full_path)

    def __eq__(self, other) -> bool:
        if isinstance(other, TileLocation):
            return self.full_path == other.full_path
        return False


@dataclass
class TileHierarchyNode:
    """A node in the tile hierarchy tree."""

    location: TileLocation
    parent: Optional["TileHierarchyNode"] = None
    children: List["TileHierarchyNode"] = field(default_factory=list)

    # Knowledge attached to this tile
    document_ids: Set[str] = field(default_factory=set)

    # Metadata
    name: Optional[str] = None  # Human-readable name (e.g., "Europe", "London")
    description: Optional[str] = None


class TileHierarchy:
    """
    Manages hierarchical tile relationships across universe layers.

    Key features:
    - Parent/child tile calculation based on zoom levels
    - Knowledge cascade: parent knowledge applies to children
    - Path-based queries: L300:* for all Earth, L300:BD* for region
    - Automatic inheritance of documents
    """

    # Layer realm boundaries
    REALM_BOUNDS = {
        LayerRealm.SYSTEM: (0, 99),
        LayerRealm.DUNGEONS: (100, 199),
        LayerRealm.SUBTERRANEAN: (200, 299),
        LayerRealm.EARTH: (300, 399),
        LayerRealm.DIMENSIONS: (400, 499),
        LayerRealm.ATMOSPHERE: (500, 599),
        LayerRealm.SOLAR_SYSTEM: (600, 699),
        LayerRealm.GALAXY: (700, 799),
    }

    # Zoom depth per realm (how many nested grids)
    # 3 = front door precision (3.1m), 1 = regional precision (11km)
    REALM_ZOOM_DEPTH = {
        LayerRealm.SYSTEM: 0,
        LayerRealm.DUNGEONS: 1,
        LayerRealm.SUBTERRANEAN: 3,  # Buried things need precision!
        LayerRealm.EARTH: 3,  # Front door precision
        LayerRealm.DIMENSIONS: 3,  # AR markers need same precision as physical
        LayerRealm.ATMOSPHERE: 1,
        LayerRealm.SOLAR_SYSTEM: 1,
        LayerRealm.GALAXY: 1,
    }

    # Zoom factor per level (60 columns = 60x zoom per level)
    ZOOM_FACTOR = GRID_COLS  # 60

    def __init__(self):
        """Initialize tile hierarchy."""
        # Index of known tiles with attached documents
        self._tile_index: Dict[str, TileHierarchyNode] = {}

        # Reverse index: document_id -> tile paths
        self._doc_tiles: Dict[str, Set[str]] = {}

        logger.info("[LOCAL] TileHierarchy initialized")

    # =========================================================================
    # Parsing and Validation
    # =========================================================================

    @staticmethod
    def parse_tile(tile_str: str) -> Optional[TileLocation]:
        """
        Parse a tile string into a TileLocation.

        Accepts:
            - "L300:BD14" (full path)
            - "BD14" (coordinate only, assumes layer 300)
            - "300:BD14" (layer without L prefix)

        Returns:
            TileLocation or None if invalid
        """
        tile_str = tile_str.strip().upper()

        # Full path: L300:BD14 or 300:BD14
        match = re.match(r"^L?(\d{1,3}):([A-Z]{2})(\d{2})$", tile_str)
        if match:
            layer = int(match.group(1))
            col = match.group(2)
            row = int(match.group(3))

            if 0 <= layer <= 899 and ROW_OFFSET <= row < ROW_OFFSET + GRID_ROWS:
                return TileLocation(layer=layer, col=col, row=row)
            return None

        # Coordinate only: BD14 (default to layer 300)
        match = re.match(r"^([A-Z]{2})(\d{2})$", tile_str)
        if match:
            col = match.group(1)
            row = int(match.group(2))

            if ROW_OFFSET <= row < ROW_OFFSET + GRID_ROWS:
                return TileLocation(layer=300, col=col, row=row)
            return None

        return None

    @staticmethod
    def is_valid_tile(tile_str: str) -> bool:
        """Check if a tile string is valid."""
        return TileHierarchy.parse_tile(tile_str) is not None

    # =========================================================================
    # Hierarchy Calculations
    # =========================================================================

    def get_parent_tile(self, location: TileLocation) -> Optional[TileLocation]:
        """
        Get the parent tile (one zoom level out).

        For Earth layers (300-399):
            - L310:BD14 parent is L300:B?1? (approximately)
            - Each zoom out = 10x larger area
            - Parent covers 10x10 grid of child tiles

        Args:
            location: Current tile location (TileLocation or string path)

        Returns:
            Parent TileLocation or None if at top level
        """
        # Handle string input
        if isinstance(location, str):
            location = self.parse_tile(location)
            if not location:
                return None

        realm = location.realm
        bounds = self.REALM_BOUNDS.get(realm)

        if not bounds:
            return None

        min_layer, max_layer = bounds

        # Can't go above minimum layer in realm
        if location.layer <= min_layer:
            return None

        # Realms with 3-level zoom depth use 10-step layers
        # (SUBTERRANEAN, EARTH, DIMENSIONS)
        high_precision_realms = (
            LayerRealm.SUBTERRANEAN,
            LayerRealm.EARTH,
            LayerRealm.DIMENSIONS,
        )

        if realm in high_precision_realms:
            # Zoom layers: round down to nearest 10
            current_zoom = (location.layer // 10) * 10
            parent_layer = current_zoom - 10 if current_zoom > min_layer else None

            if parent_layer is None or parent_layer < min_layer:
                return None

            # Same coordinate at parent zoom level
            return TileLocation(layer=parent_layer, col=location.col, row=location.row)

        # For other realms, just go one layer up
        parent_layer = location.layer - 1

        # For other realms, same coordinate but different layer
        return TileLocation(layer=parent_layer, col=location.col, row=location.row)

    def get_child_tiles(
        self, location: TileLocation, direct_only: bool = True
    ) -> List[TileLocation]:
        """
        Get child tiles (one zoom level in).

        For Earth layers, each tile has ~100 child tiles (10x10 grid).

        Args:
            location: Parent tile location (TileLocation or string path)
            direct_only: Only direct children (one level) or all descendants

        Returns:
            List of child TileLocations
        """
        # Handle string input
        if isinstance(location, str):
            location = self.parse_tile(location)
            if not location:
                return []

        realm = location.realm
        bounds = self.REALM_BOUNDS.get(realm)

        if not bounds:
            return []

        min_layer, max_layer = bounds

        # Can't go below maximum layer in realm
        if location.layer >= max_layer:
            return []

        # Realms with 3-level zoom depth use 10-step layers
        high_precision_realms = (
            LayerRealm.SUBTERRANEAN,
            LayerRealm.EARTH,
            LayerRealm.DIMENSIONS,
        )

        if realm in high_precision_realms:
            current_zoom = (location.layer // 10) * 10
            child_layer = current_zoom + 10

            if child_layer > max_layer:
                return []

            # Same coordinate at next zoom level (in full impl, would be 10x10 grid)
            return [TileLocation(layer=child_layer, col=location.col, row=location.row)]

        # For other realms, just go one layer down
        child_layer = location.layer + 1
        children = []

        # For now, return the same coordinate at next layer
        children.append(
            TileLocation(layer=child_layer, col=location.col, row=location.row)
        )

        return children

    def get_ancestor_chain(self, location: TileLocation) -> List[TileLocation]:
        """
        Get all ancestor tiles up to the realm root.

        Args:
            location: Starting tile (TileLocation or string path)

        Returns:
            List from immediate parent to root (first = parent, last = root)
        """
        # Handle string input
        if isinstance(location, str):
            location = self.parse_tile(location)
            if not location:
                return []

        ancestors = []
        current = location

        while True:
            parent = self.get_parent_tile(current)
            if parent is None:
                break
            ancestors.append(parent)
            current = parent

        return ancestors

    def get_realm_root(self, location: TileLocation) -> TileLocation:
        """Get the root tile for a location's realm."""
        realm = location.realm
        bounds = self.REALM_BOUNDS.get(realm)

        if not bounds:
            return location

        min_layer, _ = bounds
        return TileLocation(layer=min_layer, col=location.col, row=location.row)

    # =========================================================================
    # Document Attachment
    # =========================================================================

    def attach_document(self, doc_id: str, tile_path: str, cascade_up: bool = False):
        """
        Attach a document to a tile.

        Args:
            doc_id: Document ID
            tile_path: Tile path (e.g., "L300:BD14")
            cascade_up: Also attach to parent tiles (for global knowledge)
        """
        location = self.parse_tile(tile_path)
        if not location:
            logger.warning(f"[LOCAL] Invalid tile path: {tile_path}")
            return

        # Create or get node
        full_path = location.full_path
        if full_path not in self._tile_index:
            self._tile_index[full_path] = TileHierarchyNode(location=location)

        node = self._tile_index[full_path]
        node.document_ids.add(doc_id)

        # Update reverse index
        if doc_id not in self._doc_tiles:
            self._doc_tiles[doc_id] = set()
        self._doc_tiles[doc_id].add(full_path)

        # Cascade up to parents if requested
        if cascade_up:
            for ancestor in self.get_ancestor_chain(location):
                ancestor_path = ancestor.full_path
                if ancestor_path not in self._tile_index:
                    self._tile_index[ancestor_path] = TileHierarchyNode(
                        location=ancestor
                    )
                self._tile_index[ancestor_path].document_ids.add(doc_id)
                self._doc_tiles[doc_id].add(ancestor_path)

    def detach_document(self, doc_id: str, tile_path: str = None):
        """
        Detach a document from tiles.

        Args:
            doc_id: Document ID
            tile_path: Specific tile (or all if None)
        """
        if tile_path:
            location = self.parse_tile(tile_path)
            if location and location.full_path in self._tile_index:
                self._tile_index[location.full_path].document_ids.discard(doc_id)
            if doc_id in self._doc_tiles:
                self._doc_tiles[doc_id].discard(
                    location.full_path if location else tile_path
                )
        else:
            # Remove from all tiles
            if doc_id in self._doc_tiles:
                for path in self._doc_tiles[doc_id]:
                    if path in self._tile_index:
                        self._tile_index[path].document_ids.discard(doc_id)
                del self._doc_tiles[doc_id]

    # =========================================================================
    # Knowledge Query (with Cascade)
    # =========================================================================

    def get_documents_at(
        self, tile_path: str, include_inherited: bool = True
    ) -> Set[str]:
        """
        Get document IDs at a tile, optionally including inherited.

        Args:
            tile_path: Tile path (e.g., "L300:BD14")
            include_inherited: Include docs from ancestor tiles

        Returns:
            Set of document IDs
        """
        location = self.parse_tile(tile_path)
        if not location:
            return set()

        result = set()

        # Direct documents
        full_path = location.full_path
        if full_path in self._tile_index:
            result.update(self._tile_index[full_path].document_ids)

        # Inherited documents (from ancestors)
        if include_inherited:
            for ancestor in self.get_ancestor_chain(location):
                ancestor_path = ancestor.full_path
                if ancestor_path in self._tile_index:
                    result.update(self._tile_index[ancestor_path].document_ids)

        return result

    def get_documents_in_realm(self, realm: LayerRealm) -> Set[str]:
        """Get all documents in a realm."""
        result = set()
        bounds = self.REALM_BOUNDS.get(realm)

        if not bounds:
            return result

        min_layer, max_layer = bounds

        for path, node in self._tile_index.items():
            if min_layer <= node.location.layer <= max_layer:
                result.update(node.document_ids)

        return result

    def query_tiles(self, pattern: str, include_inherited: bool = True) -> Set[str]:
        """
        Query documents matching a tile pattern.

        Patterns:
            - "L300:*"      - All tiles at layer 300
            - "L300:BD*"    - Tiles starting with BD at layer 300
            - "L3*:BD14"    - BD14 across all Earth layers (300-399)
            - "*:BD14"      - BD14 at any layer

        Args:
            pattern: Tile pattern with wildcards
            include_inherited: Include inherited documents

        Returns:
            Set of matching document IDs
        """
        pattern = pattern.strip().upper()
        result = set()

        # Handle patterns
        if "*" in pattern:
            # Parse pattern parts
            if ":" in pattern:
                layer_pat, coord_pat = pattern.split(":", 1)
                layer_pat = layer_pat.lstrip("L")
            else:
                layer_pat = "*"
                coord_pat = pattern

            for path, node in self._tile_index.items():
                matches = True

                # Check layer
                if layer_pat != "*":
                    if layer_pat.endswith("*"):
                        layer_prefix = layer_pat[:-1]
                        if not str(node.location.layer).startswith(layer_prefix):
                            matches = False
                    elif str(node.location.layer) != layer_pat.zfill(3):
                        matches = False

                # Check coordinate
                if matches and coord_pat != "*":
                    if coord_pat.endswith("*"):
                        coord_prefix = coord_pat[:-1]
                        if not node.location.coord.startswith(coord_prefix):
                            matches = False
                    elif node.location.coord != coord_pat:
                        matches = False

                if matches:
                    if include_inherited:
                        result.update(self.get_documents_at(path, True))
                    else:
                        result.update(node.document_ids)
        else:
            # Exact match
            result = self.get_documents_at(pattern, include_inherited)

        return result

    # =========================================================================
    # Hierarchy Information
    # =========================================================================

    def get_layer_info(self, layer: int) -> Dict[str, Any]:
        """Get information about a layer."""
        # Determine realm
        realm = None
        for r, (min_l, max_l) in self.REALM_BOUNDS.items():
            if min_l <= layer <= max_l:
                realm = r
                break

        # Calculate zoom/scale for Earth layers
        if realm == LayerRealm.EARTH:
            zoom_level = layer - 300
            tile_size_km = 600 / (10**zoom_level) if zoom_level > 0 else 600
            scale_desc = (
                f"1 tile ≈ {tile_size_km:.0f}km"
                if tile_size_km >= 1
                else f"1 tile ≈ {tile_size_km*1000:.0f}m"
            )
        else:
            zoom_level = None
            scale_desc = None

        return {
            "layer": layer,
            "realm": realm.value if realm else "unknown",
            "zoom_level": zoom_level,
            "scale": scale_desc,
            "tiles_indexed": sum(
                1 for n in self._tile_index.values() if n.location.layer == layer
            ),
            "documents": sum(
                len(n.document_ids)
                for n in self._tile_index.values()
                if n.location.layer == layer
            ),
        }

    def get_hierarchy_path(self, tile_path: str) -> List[Dict[str, Any]]:
        """
        Get the full hierarchy path for a tile.

        Returns list from root to tile, each with:
        - location: Full path
        - name: Human name (if known)
        - doc_count: Documents at this level
        - inherited_count: Docs inherited from above
        """
        location = self.parse_tile(tile_path)
        if not location:
            return []

        # Get ancestors (reversed to go root -> tile)
        ancestors = self.get_ancestor_chain(location)
        ancestors.reverse()
        ancestors.append(location)

        result = []
        inherited = set()

        for loc in ancestors:
            path = loc.full_path
            direct_docs = set()

            if path in self._tile_index:
                direct_docs = self._tile_index[path].document_ids.copy()

            result.append(
                {
                    "location": path,
                    "name": self._tile_index.get(
                        path, TileHierarchyNode(location=loc)
                    ).name,
                    "doc_count": len(
                        direct_docs - inherited
                    ),  # Only new docs at this level
                    "inherited_count": len(inherited),
                    "total_count": len(direct_docs | inherited),
                }
            )

            inherited.update(direct_docs)

        return result

    def stats(self) -> Dict[str, Any]:
        """Get hierarchy statistics."""
        realm_stats = {}
        for realm in LayerRealm:
            docs = self.get_documents_in_realm(realm)
            tiles = sum(
                1 for n in self._tile_index.values() if n.location.realm == realm
            )
            if docs or tiles:
                realm_stats[realm.value] = {
                    "tiles": tiles,
                    "documents": len(docs),
                }

        return {
            "total_tiles": len(self._tile_index),
            "total_documents": len(self._doc_tiles),
            "by_realm": realm_stats,
        }


# Singleton instance
_hierarchy: Optional[TileHierarchy] = None


def get_tile_hierarchy() -> TileHierarchy:
    """Get or create the singleton tile hierarchy."""
    global _hierarchy
    if _hierarchy is None:
        _hierarchy = TileHierarchy()
    return _hierarchy
