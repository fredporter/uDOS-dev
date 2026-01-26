"""
Spatial Manager - Location & Proximity Verification

Manages spatial conditions for uPY v0.2:
- User proximity detection (NFC, Bluetooth ranges)
- NFC ring verification
- GPS location verification (encrypted)
- Grid coordinate mapping (alphanum to lat/long)
- Object placement (real/virtual locations)
- Crypt/unlock operations (location-based)

Part of Alpha v1.0.0.0 - Spatial Computing Layer
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone
from dataclasses import dataclass, field

from ..config.paths import get_user_path
from ..services.logging_manager import get_logger

logger = get_logger("spatial-manager")


@dataclass
class GridCoordinate:
    """
    Hierarchical cell-based grid coordinate.

    Format: [REALM]-[REGION]-L[LAYER]-[CELL1]-[CELL2]-[CELL3]...
    Example: EARTH-OC-L100-AB34-CD15-AA20

    Grid: 120 columns × 50 rows = 6,000 cells per layer
    - Columns: AA-DT (120 columns)
    - Rows: 00-49 (50 rows)
    - Cell Format: CCNN (e.g., AB15, CD20)

    Hierarchical depth via cell nesting:
    - Depth 0: L100 (entire layer, 6,000 cells)
    - Depth 1: L100-AB34 (one cell zoomed, 6,000 sub-cells)
    - Depth 2: L100-AB34-CD15 (6,000 sub-sub-cells)
    - Depth N: Unlimited via sparse storage

    Zoom factor: ~120× per depth level
    Example: 333km → 2.77km → 23m → 0.19m → 1.6mm
    """

    realm: str  # e.g., "EARTH", "VIRTUAL", "SPACE"
    region: str  # e.g., "NA01", "NETH", "SOL"
    layer: int  # 100-899 (multiverse layer number)
    cells: List[str] = field(
        default_factory=list
    )  # Hierarchical cell path ["AB34", "CD15", "AA20"]

    @property
    def code(self) -> str:
        """Get full hierarchical coordinate code."""
        base = f"{self.realm}-{self.region}-L{self.layer}"
        if self.cells:
            return f"{base}-{'-'.join(self.cells)}"
        return base

    @property
    def depth(self) -> int:
        """Get current zoom depth (number of nested cells)."""
        return len(self.cells)

    def parse_cell(self, cell: str) -> Tuple[str, int]:
        """
        Parse cell format CCNN into (column, row).

        Args:
            cell: Cell code like "AB15" or "CD20"

        Returns:
            Tuple of (column_code, row_number)

        Example:
            parse_cell("AB15") -> ("AB", 15)
        """
        if len(cell) != 4:
            raise ValueError(f"Invalid cell format: {cell} (must be CCNN, e.g., AB15)")

        column = cell[:2].upper()
        row = int(cell[2:])

        # Validate column range (AA-DT = 120 columns)
        if not ("AA" <= column <= "DT"):
            raise ValueError(f"Column {column} out of range (AA-DT)")

        # Validate row range (00-49 = 50 rows)
        if not (0 <= row <= 49):
            raise ValueError(f"Row {row} out of range (00-49)")

        return (column, row)

    def zoom_into(self, cell: str) -> "GridCoordinate":
        """
        Zoom into a specific cell, creating deeper coordinate.

        Args:
            cell: Cell to zoom into (e.g., "AB34")

        Returns:
            New GridCoordinate with cell appended

        Example:
            coord = GridCoordinate("EARTH", "OC", 100, ["AB34"])
            zoomed = coord.zoom_into("CD15")  # EARTH-OC-L100-AB34-CD15
        """
        # Validate cell format
        self.parse_cell(cell)

        new_cells = self.cells + [cell.upper()]
        return GridCoordinate(
            realm=self.realm, region=self.region, layer=self.layer, cells=new_cells
        )

    def zoom_out(self) -> Optional["GridCoordinate"]:
        """
        Zoom out one level by removing last cell.

        Returns:
            New GridCoordinate with last cell removed, or None if already at base layer

        Example:
            coord = GridCoordinate("EARTH", "OC", 100, ["AB34", "CD15"])
            zoomed_out = coord.zoom_out()  # EARTH-OC-L100-AB34
        """
        if not self.cells:
            return None  # Already at base layer

        new_cells = self.cells[:-1]
        return GridCoordinate(
            realm=self.realm, region=self.region, layer=self.layer, cells=new_cells
        )

    def distance_to(self, other: "GridCoordinate") -> float:
        """
        Calculate approximate distance between hierarchical coords.
        Must be at same depth level for accurate comparison.

        Returns:
            Distance in meters (approximate)
        """
        if self.layer != other.layer:
            raise ValueError("Cannot compare coordinates at different layers")

        if self.depth != other.depth:
            raise ValueError(
                f"Cannot compare coordinates at different depths ({self.depth} vs {other.depth})"
            )

        # Calculate precision at current depth
        # Base precision at depth 0 varies by realm/layer
        # Earth L100 depth 0: ~333km per cell (40,000km / 120 cols)
        # Each zoom level divides by ~120
        base_precision_km = 333  # Default Earth L100
        precision_m = (
            base_precision_km * 1000 / (120**self.depth)
            if self.depth > 0
            else base_precision_km * 1000
        )

        # Compare last cell in hierarchy
        if self.cells and other.cells:
            self_col, self_row = self.parse_cell(self.cells[-1])
            other_col, other_row = self.parse_cell(other.cells[-1])

            # Convert column codes to numbers (AA=0, AB=1, ..., DT=119)
            self_col_num = (ord(self_col[0]) - ord("A")) * 26 + (
                ord(self_col[1]) - ord("A")
            )
            other_col_num = (ord(other_col[0]) - ord("A")) * 26 + (
                ord(other_col[1]) - ord("A")
            )

            col_diff = abs(self_col_num - other_col_num)
            row_diff = abs(self_row - other_row)

            grid_distance = (col_diff**2 + row_diff**2) ** 0.5
            return grid_distance * precision_m

        return 0.0  # Same base coordinate


@dataclass
class SpatialCondition:
    """Condition for spatial verification."""

    type: str  # 'proximity', 'nfc', 'location', 'grid', 'unlock'
    parameters: Dict[str, Any]
    verified: bool = False
    verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpatialObject:
    """Object placed in real or virtual location."""

    id: str
    type: str  # 'data', 'unlock', 'item', 'beacon'
    location: GridCoordinate
    virtual: bool  # True=virtual location, False=real-world
    content: Dict[str, Any]
    access_conditions: List[SpatialCondition] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SpatialManager:
    """Manage spatial conditions and location verification."""

    def __init__(self, config=None):
        """Initialize spatial manager."""
        self.config = config
        self.spatial_file = get_user_path("data") / "spatial.json"
        self.objects_file = get_user_path("data") / "spatial_objects.json"

        # Grid coordinate cache
        self.current_grid: Optional[GridCoordinate] = None
        self.verified_locations: Dict[str, SpatialCondition] = {}

        # Transport availability
        self.transports = {
            "nfc": False,  # NFC ring/reader available
            "bluetooth": False,  # Bluetooth adapter available
            "gps": False,  # GPS module available (encrypted)
            "meshcore": False,  # MeshCore P2P active
        }

        self._load_state()
        self._detect_transports()

    def _load_state(self):
        """Load spatial state from disk."""
        if self.spatial_file.exists():
            try:
                with open(self.spatial_file, "r") as f:
                    data = json.load(f)

                    # Restore current grid (hierarchical format)
                    if "current_grid" in data:
                        g = data["current_grid"]
                        self.current_grid = GridCoordinate(
                            realm=g.get("realm", "EARTH"),
                            region=g.get("region", "NA01"),
                            layer=g["layer"],
                            cells=g.get("cells", []),
                        )

                    # Restore transports
                    if "transports" in data:
                        self.transports.update(data["transports"])

            except Exception as e:
                logger.error(f"Failed to load spatial state: {e}")

    def _save_state(self):
        """Save spatial state to disk."""
        self.spatial_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "current_grid": (
                {
                    "realm": self.current_grid.realm,
                    "region": self.current_grid.region,
                    "layer": self.current_grid.layer,
                    "cells": self.current_grid.cells,
                }
                if self.current_grid
                else None
            ),
            "transports": self.transports,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        with open(self.spatial_file, "w") as f:
            json.dump(data, f, indent=2)

    def _detect_transports(self):
        """Detect available transport methods."""
        # Stub implementation - actual detection would check hardware
        # NFC: Check for NFC reader device
        # Bluetooth: Check for BT adapter
        # GPS: Check for GPS module
        # MeshCore: Check if service is running

        logger.info("[LOCAL] Detecting available transports...")
        # Default to MeshCore available in offline mode
        self.transports["meshcore"] = True

    # ==================== Grid Coordinate System ====================

    def parse_grid_code(self, code: str) -> GridCoordinate:
        """
        Parse grid code string into GridCoordinate.

        Format: [REALM]-[REGION]-L[LAYER][-CELL1][-CELL2]...
        Examples:
            - "EARTH-NA01-L100" (Earth, North America 01, layer 100)
            - "EARTH-NA01-L100-AB34" (with cell AB34)
            - "EARTH-NA01-L100-AB34-CD15" (nested cells)
        """
        parts = code.split("-")

        if len(parts) < 3:
            raise ValueError(f"Invalid grid code: {code} (need REALM-REGION-L###)")

        realm = parts[0]
        region = parts[1]
        layer_str = parts[2]

        # Parse L[layer]
        if not layer_str.startswith("L"):
            raise ValueError(f"Invalid layer format: {layer_str} (must be L###)")

        try:
            layer = int(layer_str[1:])
        except ValueError:
            raise ValueError(f"Invalid layer number: {layer_str}")

        # Extract cells (remaining parts)
        cells = parts[3:] if len(parts) > 3 else []

        return GridCoordinate(realm=realm, region=region, layer=layer, cells=cells)

    def grid_to_latlong(self, grid: GridCoordinate) -> Tuple[float, float]:
        """
        Convert grid coordinate to approximate lat/long.

        Note: Requires region-specific origin and scale data.
        This is a simplified implementation.
        """
        # Load region data if available
        if grid.region:
            region_data = self._load_region_data(grid.region)
            origin_lat = region_data.get("origin_lat", 0.0)
            origin_lon = region_data.get("origin_lon", 0.0)
        else:
            origin_lat, origin_lon = 0.0, 0.0

        # Calculate offset based on grid
        precision_meters = 3 * (10 ** (9 - grid.layer))

        # Rough conversion: 1 degree ≈ 111km
        meters_per_degree = 111000

        col_offset = ord(grid.column[0]) - ord("A")
        row_offset = grid.row

        lat = origin_lat + (row_offset * precision_meters / meters_per_degree)
        lon = origin_lon + (col_offset * precision_meters / meters_per_degree)

        return lat, lon

    def latlong_to_grid(
        self, lat: float, lon: float, layer: int = 9, region: str = None
    ) -> GridCoordinate:
        """Convert lat/long to grid coordinate at specified layer."""
        if region:
            region_data = self._load_region_data(region)
            origin_lat = region_data.get("origin_lat", 0.0)
            origin_lon = region_data.get("origin_lon", 0.0)
        else:
            origin_lat, origin_lon = 0.0, 0.0

        precision_meters = 3 * (10 ** (9 - layer))
        meters_per_degree = 111000

        # Calculate grid offsets
        row = int((lat - origin_lat) * meters_per_degree / precision_meters)
        col_offset = int((lon - origin_lon) * meters_per_degree / precision_meters)

        # Convert offset to column code (AA-ZZ)
        col_a = (col_offset // 26) + ord("A")
        col_b = (col_offset % 26) + ord("A")
        column = chr(col_a) + chr(col_b)

        return GridCoordinate(layer=layer, column=column, row=row, region=region)

    def _load_region_data(self, region: str) -> Dict[str, Any]:
        """Load region origin and scale data."""
        # Stub - would load from knowledge/maps/regions.json
        return {"origin_lat": 0.0, "origin_lon": 0.0, "scale": 1.0}

    def set_current_grid(self, grid: GridCoordinate):
        """Set current user grid position."""
        self.current_grid = grid
        self._save_state()
        logger.info(f"[LOCAL] Current grid: {grid.code}")

    def get_current_grid(self) -> Optional[GridCoordinate]:
        """Get current grid position."""
        return self.current_grid

    # ==================== Proximity Detection ====================

    def check_proximity(
        self, transport: str, target_id: str, max_distance: float = None
    ) -> SpatialCondition:
        """
        Check proximity to target using specified transport.

        Args:
            transport: 'nfc', 'bluetooth', 'meshcore'
            target_id: Device/beacon identifier
            max_distance: Maximum distance in meters (None = transport default)
        """
        if not self.transports.get(transport):
            return SpatialCondition(
                type="proximity",
                parameters={"transport": transport, "target": target_id},
                verified=False,
                metadata={"error": f"{transport} not available"},
            )

        # Default ranges by transport
        ranges = {
            "nfc": 0.1,  # 10cm
            "bluetooth": 10.0,  # 10m
            "meshcore": 100.0,  # 100m
        }

        max_dist = max_distance or ranges.get(transport, 10.0)

        # Stub: Actual implementation would query transport layer
        # For now, simulate based on transport availability
        distance = self._detect_distance(transport, target_id)
        verified = distance is not None and distance <= max_dist

        condition = SpatialCondition(
            type="proximity",
            parameters={
                "transport": transport,
                "target": target_id,
                "max_distance": max_dist,
            },
            verified=verified,
            verified_at=datetime.now(timezone.utc) if verified else None,
            metadata={"distance": distance},
        )

        if verified:
            logger.info(
                f"[{transport.upper()}] Proximity verified: {target_id} at {distance:.2f}m"
            )

        return condition

    def _detect_distance(self, transport: str, target_id: str) -> Optional[float]:
        """Detect distance to target via transport (stub)."""
        # Actual implementation would query:
        # - NFC: Reader status
        # - Bluetooth: RSSI to distance calculation
        # - MeshCore: Network hop count or reported GPS distance
        return None

    # ==================== NFC Ring Verification ====================

    def verify_nfc_ring(self, ring_id: str, challenge: str = None) -> SpatialCondition:
        """
        Verify NFC ring identity and optionally respond to challenge.

        Args:
            ring_id: Expected ring identifier
            challenge: Optional challenge string for authentication
        """
        if not self.transports["nfc"]:
            return SpatialCondition(
                type="nfc",
                parameters={"ring_id": ring_id},
                verified=False,
                metadata={"error": "NFC not available"},
            )

        # Stub: Actual implementation would:
        # 1. Read NFC tag
        # 2. Verify tag ID matches ring_id
        # 3. If challenge provided, perform challenge-response

        # For now, simulate success if NFC available
        verified = True  # Stub
        response = (
            hashlib.sha256(f"{ring_id}{challenge}".encode()).hexdigest()[:16]
            if challenge
            else None
        )

        condition = SpatialCondition(
            type="nfc",
            parameters={"ring_id": ring_id, "challenge": challenge},
            verified=verified,
            verified_at=datetime.now(timezone.utc) if verified else None,
            metadata={"response": response} if response else {},
        )

        if verified:
            logger.info(f"[NFC] Ring verified: {ring_id}")

        return condition

    # ==================== Location Verification ====================

    def verify_location(
        self, grid: GridCoordinate, tolerance_meters: float = 10.0
    ) -> SpatialCondition:
        """
        Verify user is at specified grid location.

        Args:
            grid: Target grid coordinate
            tolerance_meters: Acceptable distance tolerance
        """
        if not self.current_grid:
            return SpatialCondition(
                type="location",
                parameters={"grid": grid.code, "tolerance": tolerance_meters},
                verified=False,
                metadata={"error": "Current location unknown"},
            )

        try:
            distance = self.current_grid.distance_to(grid)
            verified = distance <= tolerance_meters

            condition = SpatialCondition(
                type="location",
                parameters={"grid": grid.code, "tolerance": tolerance_meters},
                verified=verified,
                verified_at=datetime.now(timezone.utc) if verified else None,
                metadata={"current_grid": self.current_grid.code, "distance": distance},
            )

            if verified:
                logger.info(
                    f"[LOCAL] Location verified: {grid.code} (distance: {distance:.1f}m)"
                )

            return condition

        except ValueError as e:
            return SpatialCondition(
                type="location",
                parameters={"grid": grid.code},
                verified=False,
                metadata={"error": str(e)},
            )

    # ==================== Object Placement ====================

    def place_object(self, obj: SpatialObject) -> bool:
        """Place object at spatial location."""
        self.objects_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing objects
        objects = []
        if self.objects_file.exists():
            with open(self.objects_file, "r") as f:
                objects = json.load(f)

        # Add new object
        obj_data = {
            "id": obj.id,
            "type": obj.type,
            "location": obj.location.code,
            "virtual": obj.virtual,
            "content": obj.content,
            "access_conditions": [
                {"type": c.type, "parameters": c.parameters}
                for c in obj.access_conditions
            ],
            "created_at": obj.created_at.isoformat(),
        }

        objects.append(obj_data)

        with open(self.objects_file, "w") as f:
            json.dump(objects, f, indent=2)

        logger.info(
            f"[LOCAL] Object placed: {obj.id} at {obj.location.code} ({'virtual' if obj.virtual else 'real'})"
        )
        return True

    def find_objects_at(
        self, grid: GridCoordinate, radius_meters: float = 10.0
    ) -> List[SpatialObject]:
        """Find objects within radius of grid coordinate."""
        if not self.objects_file.exists():
            return []

        with open(self.objects_file, "r") as f:
            objects_data = json.load(f)

        nearby = []
        for obj_data in objects_data:
            obj_grid = self.parse_grid_code(obj_data["location"])

            try:
                distance = grid.distance_to(obj_grid)
                if distance <= radius_meters:
                    # Reconstruct object
                    obj = SpatialObject(
                        id=obj_data["id"],
                        type=obj_data["type"],
                        location=obj_grid,
                        virtual=obj_data["virtual"],
                        content=obj_data["content"],
                        created_at=datetime.fromisoformat(obj_data["created_at"]),
                    )
                    nearby.append(obj)
            except ValueError:
                continue

        return nearby

    # ==================== Crypt/Unlock Operations ====================

    def location_unlock(
        self, encrypted_data: bytes, grid: GridCoordinate, tolerance: float = 10.0
    ) -> Optional[bytes]:
        """
        Decrypt data only if at correct location.

        Args:
            encrypted_data: Encrypted bytes
            grid: Required grid location for decryption
            tolerance: Distance tolerance in meters
        """
        condition = self.verify_location(grid, tolerance)

        if not condition.verified:
            logger.warning(f"[LOCAL] Location unlock failed: not at {grid.code}")
            return None

        # Stub: Actual implementation would use location-derived key
        # For now, just return data (assumes already decrypted)
        logger.info(f"[LOCAL] Location unlock successful: {grid.code}")
        return encrypted_data

    def proximity_unlock(
        self, encrypted_data: bytes, transport: str, target_id: str
    ) -> Optional[bytes]:
        """
        Decrypt data only if in proximity to target.

        Args:
            encrypted_data: Encrypted bytes
            transport: Transport method ('nfc', 'bluetooth', 'meshcore')
            target_id: Target device/beacon ID
        """
        condition = self.check_proximity(transport, target_id)

        if not condition.verified:
            logger.warning(
                f"[{transport.upper()}] Proximity unlock failed: {target_id} not in range"
            )
            return None

        logger.info(f"[{transport.upper()}] Proximity unlock successful: {target_id}")
        return encrypted_data

    # ==================== Condition Evaluation ====================

    def evaluate_conditions(self, conditions: List[SpatialCondition]) -> bool:
        """
        Evaluate list of spatial conditions (AND logic).

        Returns True only if all conditions verify.
        """
        if not conditions:
            return True

        for condition in conditions:
            if condition.type == "proximity":
                result = self.check_proximity(
                    condition.parameters["transport"],
                    condition.parameters["target"],
                    condition.parameters.get("max_distance"),
                )
            elif condition.type == "nfc":
                result = self.verify_nfc_ring(
                    condition.parameters["ring_id"],
                    condition.parameters.get("challenge"),
                )
            elif condition.type == "location":
                grid = self.parse_grid_code(condition.parameters["grid"])
                result = self.verify_location(
                    grid, condition.parameters.get("tolerance", 10.0)
                )
            else:
                logger.warning(f"Unknown condition type: {condition.type}")
                return False

            if not result.verified:
                return False

        return True
