"""
Waypoint Manager Service

Manages waypoints - named locations that connect tiles across layers.
Waypoints are the primary mechanism for vertical traversal between
universe layers (e.g., from Earth surface to dungeons or space).

Part of uDOS Alpha v1.0.0.53+
"""

import json
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("waypoint-manager")


class WaypointType(Enum):
    """Types of waypoints."""

    STAIRS_DOWN = "stairs_down"  # Descend to lower layer
    STAIRS_UP = "stairs_up"  # Ascend to upper layer
    PORTAL = "portal"  # Instant vertical teleport
    ELEVATOR = "elevator"  # Multi-layer access
    CAVE_ENTRANCE = "cave_entrance"  # Surface to underground
    LAUNCH_PAD = "launch_pad"  # Surface to space
    POI = "poi"  # Point of interest (informational)
    LANDMARK = "landmark"  # Navigation landmark


class WaypointVisibility(Enum):
    """Visibility levels for waypoints."""

    PUBLIC = "public"  # Visible to all
    DISCOVERED = "discovered"  # Only visible after discovery
    HIDDEN = "hidden"  # Must be revealed by knowledge
    SYSTEM = "system"  # System-generated waypoints


@dataclass
class WaypointConnection:
    """A connection from a waypoint to another location."""

    target_layer: int  # Destination layer
    target_tile: str  # Destination tile coordinate
    target_waypoint_id: str = ""  # Optional: specific waypoint at destination
    bidirectional: bool = True  # Can travel both ways
    requirements: List[str] = field(default_factory=list)  # Tags required to use


@dataclass
class Waypoint:
    """A named location that enables navigation."""

    waypoint_id: str
    name: str
    waypoint_type: WaypointType
    layer: int  # Layer number (000-899)
    tile: str  # Tile coordinate (e.g., "BD14")
    description: str = ""
    visibility: WaypointVisibility = WaypointVisibility.PUBLIC

    # Connections to other locations
    connections: List[WaypointConnection] = field(default_factory=list)

    # Real-world linking (like PokéStops)
    real_world: Dict = field(default_factory=dict)  # {lat, lon, place_id, address}

    # Metadata
    created: str = ""
    updated: str = ""
    author_id: str = ""
    verified: bool = False

    # Tags for searchability
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "waypoint_id": self.waypoint_id,
            "name": self.name,
            "type": self.waypoint_type.value,
            "layer": self.layer,
            "tile": self.tile,
            "description": self.description,
            "visibility": self.visibility.value,
            "connections": [
                {
                    "target_layer": c.target_layer,
                    "target_tile": c.target_tile,
                    "target_waypoint_id": c.target_waypoint_id,
                    "bidirectional": c.bidirectional,
                    "requirements": c.requirements,
                }
                for c in self.connections
            ],
            "real_world": self.real_world,
            "created": self.created,
            "updated": self.updated,
            "author_id": self.author_id,
            "verified": self.verified,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Waypoint":
        """Create from dictionary."""
        connections = [
            WaypointConnection(
                target_layer=c.get("target_layer", 0),
                target_tile=c.get("target_tile", ""),
                target_waypoint_id=c.get("target_waypoint_id", ""),
                bidirectional=c.get("bidirectional", True),
                requirements=c.get("requirements", []),
            )
            for c in data.get("connections", [])
        ]

        return cls(
            waypoint_id=data.get("waypoint_id", ""),
            name=data.get("name", ""),
            waypoint_type=WaypointType(data.get("type", "poi")),
            layer=data.get("layer", 300),
            tile=data.get("tile", ""),
            description=data.get("description", ""),
            visibility=WaypointVisibility(data.get("visibility", "public")),
            connections=connections,
            real_world=data.get("real_world", {}),
            created=data.get("created", ""),
            updated=data.get("updated", ""),
            author_id=data.get("author_id", ""),
            verified=data.get("verified", False),
            tags=data.get("tags", []),
        )


class WaypointManager:
    """
    Manages waypoints for navigation between tiles and layers.

    Waypoints provide:
    - Named locations for navigation
    - Vertical connections between layers
    - Real-world POI linking
    - Discovery mechanics
    """

    # Layer ranges
    LAYER_SYSTEM = (0, 99)
    LAYER_DUNGEONS = (100, 199)
    LAYER_UNDERGROUND = (200, 299)
    LAYER_EARTH = (300, 399)
    LAYER_ATMOSPHERE = (400, 499)
    LAYER_DIMENSIONS = (500, 599)
    LAYER_NEAR_SPACE = (600, 699)
    LAYER_SOLAR = (700, 799)
    LAYER_GALAXY = (800, 899)

    def __init__(self, waypoints_path: Path = None):
        """
        Initialize waypoint manager.

        Args:
            waypoints_path: Where waypoints are stored
        """
        self.waypoints_path = waypoints_path or Path("memory/apps/maps/waypoints")
        self.waypoints_path.mkdir(parents=True, exist_ok=True)

        # Waypoint indexes
        self._waypoints: Dict[str, Waypoint] = {}  # id -> waypoint
        self._by_tile: Dict[str, List[str]] = {}  # "L300:BD14" -> [waypoint_ids]
        self._by_type: Dict[WaypointType, List[str]] = {}  # type -> [waypoint_ids]
        self._by_tag: Dict[str, List[str]] = {}  # tag -> [waypoint_ids]

        # Load existing waypoints
        self._load_waypoints()

        logger.info(
            f"[LOCAL] WaypointManager initialized with {len(self._waypoints)} waypoints"
        )

    def _load_waypoints(self):
        """Load waypoints from disk."""
        # Load from JSON files in waypoints directory
        for wp_file in self.waypoints_path.glob("**/*.waypoint.json"):
            try:
                data = json.loads(wp_file.read_text(encoding="utf-8"))
                waypoint = Waypoint.from_dict(data)
                self._index_waypoint(waypoint)
            except Exception as e:
                logger.warning(f"[LOCAL] Failed to load waypoint {wp_file}: {e}")

        # Load bulk waypoints from layer files
        for layer_file in self.waypoints_path.glob("layer_*.json"):
            try:
                data = json.loads(layer_file.read_text(encoding="utf-8"))
                for wp_data in data.get("waypoints", []):
                    waypoint = Waypoint.from_dict(wp_data)
                    self._index_waypoint(waypoint)
            except Exception as e:
                logger.warning(f"[LOCAL] Failed to load layer file {layer_file}: {e}")

    def _index_waypoint(self, waypoint: Waypoint):
        """Add waypoint to all indexes."""
        self._waypoints[waypoint.waypoint_id] = waypoint

        # Tile index (layer + tile)
        tile_key = f"L{waypoint.layer:03d}:{waypoint.tile}"
        if tile_key not in self._by_tile:
            self._by_tile[tile_key] = []
        self._by_tile[tile_key].append(waypoint.waypoint_id)

        # Type index
        if waypoint.waypoint_type not in self._by_type:
            self._by_type[waypoint.waypoint_type] = []
        self._by_type[waypoint.waypoint_type].append(waypoint.waypoint_id)

        # Tag index
        for tag in waypoint.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            self._by_tag[tag].append(waypoint.waypoint_id)

    def _remove_from_indexes(self, waypoint: Waypoint):
        """Remove waypoint from all indexes."""
        # Remove from main dict
        if waypoint.waypoint_id in self._waypoints:
            del self._waypoints[waypoint.waypoint_id]

        # Remove from tile index
        tile_key = f"L{waypoint.layer:03d}:{waypoint.tile}"
        if tile_key in self._by_tile:
            self._by_tile[tile_key] = [
                wid for wid in self._by_tile[tile_key] if wid != waypoint.waypoint_id
            ]

        # Remove from type index
        if waypoint.waypoint_type in self._by_type:
            self._by_type[waypoint.waypoint_type] = [
                wid
                for wid in self._by_type[waypoint.waypoint_type]
                if wid != waypoint.waypoint_id
            ]

        # Remove from tag indexes
        for tag in waypoint.tags:
            if tag in self._by_tag:
                self._by_tag[tag] = [
                    wid for wid in self._by_tag[tag] if wid != waypoint.waypoint_id
                ]

    def _generate_id(self, name: str, layer: int) -> str:
        """Generate unique waypoint ID."""
        slug = name.lower().replace(" ", "_")[:20]
        suffix = secrets.token_hex(4)
        return f"wp_{layer}_{slug}_{suffix}"

    def get(self, waypoint_id: str) -> Optional[Waypoint]:
        """Get waypoint by ID."""
        return self._waypoints.get(waypoint_id)

    def get_at_tile(self, layer: int, tile: str) -> List[Waypoint]:
        """Get all waypoints at a specific tile."""
        tile_key = f"L{layer:03d}:{tile}"
        wp_ids = self._by_tile.get(tile_key, [])
        return [self._waypoints[wid] for wid in wp_ids if wid in self._waypoints]

    def get_by_type(self, waypoint_type: WaypointType) -> List[Waypoint]:
        """Get all waypoints of a specific type."""
        wp_ids = self._by_type.get(waypoint_type, [])
        return [self._waypoints[wid] for wid in wp_ids if wid in self._waypoints]

    def get_by_tag(self, tag: str) -> List[Waypoint]:
        """Get all waypoints with a specific tag."""
        wp_ids = self._by_tag.get(tag, [])
        return [self._waypoints[wid] for wid in wp_ids if wid in self._waypoints]

    def get_connections_from(
        self, layer: int, tile: str
    ) -> List[Tuple[Waypoint, WaypointConnection]]:
        """
        Get all available connections from a tile.

        Args:
            layer: Current layer
            tile: Current tile

        Returns:
            List of (waypoint, connection) tuples
        """
        waypoints = self.get_at_tile(layer, tile)
        connections = []

        for wp in waypoints:
            for conn in wp.connections:
                connections.append((wp, conn))

        return connections

    def can_traverse(
        self, connection: WaypointConnection, user_tags: List[str] = None
    ) -> bool:
        """
        Check if a connection can be traversed.

        Args:
            connection: The connection to check
            user_tags: Tags the user has (for requirement checking)

        Returns:
            True if traversal is allowed
        """
        if not connection.requirements:
            return True

        user_tags = set(user_tags or [])
        required = set(connection.requirements)

        return required.issubset(user_tags)

    def create(
        self,
        name: str,
        waypoint_type: WaypointType,
        layer: int,
        tile: str,
        description: str = "",
        author_id: str = "",
        tags: List[str] = None,
        visibility: WaypointVisibility = WaypointVisibility.PUBLIC,
        real_world: Dict = None,
        connections: List[Dict] = None,
    ) -> Waypoint:
        """
        Create a new waypoint.

        Args:
            name: Waypoint name
            waypoint_type: Type of waypoint
            layer: Layer number (0-899)
            tile: Tile coordinate
            description: Description
            author_id: Creating user
            tags: Tags for searchability
            visibility: Visibility level
            real_world: Real-world location data
            connections: Connection definitions

        Returns:
            Created waypoint
        """
        now = datetime.now().isoformat()
        waypoint_id = self._generate_id(name, layer)

        # Build connections
        wp_connections = []
        if connections:
            for conn in connections:
                wp_connections.append(
                    WaypointConnection(
                        target_layer=conn.get("target_layer", layer),
                        target_tile=conn.get("target_tile", tile),
                        target_waypoint_id=conn.get("target_waypoint_id", ""),
                        bidirectional=conn.get("bidirectional", True),
                        requirements=conn.get("requirements", []),
                    )
                )

        waypoint = Waypoint(
            waypoint_id=waypoint_id,
            name=name,
            waypoint_type=waypoint_type,
            layer=layer,
            tile=tile,
            description=description,
            visibility=visibility,
            connections=wp_connections,
            real_world=real_world or {},
            created=now,
            updated=now,
            author_id=author_id,
            verified=False,
            tags=tags or [],
        )

        # Index
        self._index_waypoint(waypoint)

        # Save
        self._save_waypoint(waypoint)

        logger.info(f"[LOCAL] Created waypoint: {name} at L{layer}:{tile}")
        return waypoint

    def update(self, waypoint_id: str, **updates) -> Waypoint:
        """
        Update an existing waypoint.

        Args:
            waypoint_id: Waypoint ID
            **updates: Fields to update

        Returns:
            Updated waypoint
        """
        waypoint = self._waypoints.get(waypoint_id)
        if not waypoint:
            raise ValueError(f"Waypoint not found: {waypoint_id}")

        # Remove from indexes (will re-add after update)
        self._remove_from_indexes(waypoint)

        # Apply updates
        if "name" in updates:
            waypoint.name = updates["name"]
        if "description" in updates:
            waypoint.description = updates["description"]
        if "tags" in updates:
            waypoint.tags = updates["tags"]
        if "visibility" in updates:
            waypoint.visibility = WaypointVisibility(updates["visibility"])
        if "real_world" in updates:
            waypoint.real_world = updates["real_world"]
        if "verified" in updates:
            waypoint.verified = updates["verified"]
        if "connections" in updates:
            waypoint.connections = [
                WaypointConnection(**c) if isinstance(c, dict) else c
                for c in updates["connections"]
            ]

        waypoint.updated = datetime.now().isoformat()

        # Re-index
        self._index_waypoint(waypoint)

        # Save
        self._save_waypoint(waypoint)

        logger.info(f"[LOCAL] Updated waypoint: {waypoint_id}")
        return waypoint

    def delete(self, waypoint_id: str, author_id: str = None) -> bool:
        """
        Delete a waypoint.

        Args:
            waypoint_id: Waypoint ID
            author_id: Must match author or be wizard

        Returns:
            True if deleted
        """
        waypoint = self._waypoints.get(waypoint_id)
        if not waypoint:
            raise ValueError(f"Waypoint not found: {waypoint_id}")

        if author_id and waypoint.author_id != author_id:
            raise PermissionError("Only author can delete waypoint")

        # Remove from indexes
        self._remove_from_indexes(waypoint)

        # Delete file
        file_path = self.waypoints_path / f"{waypoint_id}.waypoint.json"
        if file_path.exists():
            file_path.unlink()

        logger.info(f"[LOCAL] Deleted waypoint: {waypoint_id}")
        return True

    def _save_waypoint(self, waypoint: Waypoint):
        """Save waypoint to disk."""
        file_path = self.waypoints_path / f"{waypoint.waypoint_id}.waypoint.json"
        data = waypoint.to_dict()
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def search(
        self,
        query: str = "",
        layer: int = None,
        waypoint_type: WaypointType = None,
        tags: List[str] = None,
        near_tile: str = None,
        radius: int = 5,
        verified_only: bool = False,
        limit: int = 50,
    ) -> List[Waypoint]:
        """
        Search for waypoints.

        Args:
            query: Text search in name/description
            layer: Filter by layer
            waypoint_type: Filter by type
            tags: Filter by tags (any match)
            near_tile: Filter by proximity to tile
            radius: Tile radius for proximity search
            verified_only: Only verified waypoints
            limit: Max results

        Returns:
            List of matching waypoints
        """
        results = list(self._waypoints.values())

        # Text search
        if query:
            query_lower = query.lower()
            results = [
                wp
                for wp in results
                if query_lower in wp.name.lower()
                or query_lower in wp.description.lower()
            ]

        # Layer filter
        if layer is not None:
            results = [wp for wp in results if wp.layer == layer]

        # Type filter
        if waypoint_type:
            results = [wp for wp in results if wp.waypoint_type == waypoint_type]

        # Tag filter
        if tags:
            tag_set = set(tags)
            results = [wp for wp in results if tag_set & set(wp.tags)]

        # Verified filter
        if verified_only:
            results = [wp for wp in results if wp.verified]

        # TODO: Proximity filter (requires coordinate parsing)

        # Limit
        if len(results) > limit:
            results = results[:limit]

        return results

    def get_layer_name(self, layer: int) -> str:
        """Get human-readable name for a layer."""
        if self.LAYER_SYSTEM[0] <= layer <= self.LAYER_SYSTEM[1]:
            return "System"
        elif self.LAYER_DUNGEONS[0] <= layer <= self.LAYER_DUNGEONS[1]:
            return f"Dungeon (Depth {layer - 100})"
        elif self.LAYER_UNDERGROUND[0] <= layer <= self.LAYER_UNDERGROUND[1]:
            return f"Underground (Level {layer - 200})"
        elif self.LAYER_EARTH[0] <= layer <= self.LAYER_EARTH[1]:
            zoom = layer - 300
            return f"Earth Surface (Zoom {zoom})"
        elif self.LAYER_ATMOSPHERE[0] <= layer <= self.LAYER_ATMOSPHERE[1]:
            return f"Atmosphere (Alt {layer - 400})"
        elif self.LAYER_DIMENSIONS[0] <= layer <= self.LAYER_DIMENSIONS[1]:
            return f"Dimension {layer - 500}"
        elif self.LAYER_NEAR_SPACE[0] <= layer <= self.LAYER_NEAR_SPACE[1]:
            return "Near Space / Orbit"
        elif self.LAYER_SOLAR[0] <= layer <= self.LAYER_SOLAR[1]:
            return "Solar System"
        elif self.LAYER_GALAXY[0] <= layer <= self.LAYER_GALAXY[1]:
            return "Galaxy"
        else:
            return f"Unknown Layer {layer}"

    def stats(self) -> Dict:
        """Get waypoint statistics."""
        type_counts = {}
        for wp_type in WaypointType:
            count = len(self._by_type.get(wp_type, []))
            if count > 0:
                type_counts[wp_type.value] = count

        return {
            "total_waypoints": len(self._waypoints),
            "unique_tiles": len(self._by_tile),
            "unique_tags": len(self._by_tag),
            "by_type": type_counts,
            "verified_count": sum(1 for wp in self._waypoints.values() if wp.verified),
        }


# Singleton instance
_manager: Optional[WaypointManager] = None


def get_waypoint_manager() -> WaypointManager:
    """Get or create the singleton waypoint manager."""
    global _manager
    if _manager is None:
        _manager = WaypointManager()
    return _manager
