#!/usr/bin/env python3
"""
uDOS v1.3.1 - Map Tile Library & Editor Integration

Provides map-specific tile editing and a library of terrain/feature tiles
for the 24×24 grid mapping system.

Components:
- MapTileLibrary: Pre-built terrain and feature tiles
- MapTileEditor: Map-specific tile editing wrapper
- MapDataManager: Geography data caching and management

Tile Categories:
- terrain: ocean, land, mountain, desert, forest, urban, coastal, snow
- features: river, lake, road, bridge, building, park, landmark
- markers: city, capital, port, airport, station, poi
- network: node, gateway, sensor, repeater, device

File Format:
- JSON tiles stored in core/data/geography/tiles/
- Custom user tiles in memory/drafts/tiles/map/

Version: 1.3.1
Author: Fred Porter
Date: December 2025
"""

import json
import copy
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache


# =============================================================================
# Tile Data Structures
# =============================================================================

@dataclass
class MapTile:
    """Single map tile (24×24 or smaller pattern)."""
    id: str
    name: str
    category: str               # terrain, feature, marker, network
    size: Tuple[int, int]       # (width, height) - usually (24, 24) or (1, 1)
    data: List[List[str]]       # Character grid
    colors: Optional[Dict] = None  # Optional color data
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.colors is None:
            self.colors = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'size': list(self.size),
            'data': self.data,
            'colors': self.colors,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MapTile':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            category=data['category'],
            size=tuple(data['size']),
            data=data['data'],
            colors=data.get('colors'),
            metadata=data.get('metadata', {})
        )
    
    def render(self) -> str:
        """Render tile as string."""
        return '\n'.join(''.join(row) for row in self.data)


# =============================================================================
# Built-in Tile Patterns (1x1 cells)
# =============================================================================

# Single-character terrain patterns
TERRAIN_PATTERNS = {
    'ocean': {
        'char': '~',
        'variants': ['~', '≈', '∼'],
        'color': 'blue'
    },
    'water': {
        'char': '≈',
        'variants': ['≈', '~', '∽'],
        'color': 'cyan'
    },
    'land': {
        'char': '·',
        'variants': ['·', '.', '∘'],
        'color': 'green'
    },
    'mountain': {
        'char': '▲',
        'variants': ['▲', '△', '∧'],
        'color': 'white'
    },
    'desert': {
        'char': '░',
        'variants': ['░', '▒', '∷'],
        'color': 'yellow'
    },
    'forest': {
        'char': '▓',
        'variants': ['▓', '▒', '♣'],
        'color': 'green'
    },
    'urban': {
        'char': '█',
        'variants': ['█', '▓', '▇'],
        'color': 'white'
    },
    'coastal': {
        'char': '▒',
        'variants': ['▒', '░', '≈'],
        'color': 'cyan'
    },
    'snow': {
        'char': '░',
        'variants': ['░', '·', '∘'],
        'color': 'white'
    },
    'grassland': {
        'char': '·',
        'variants': ['·', ',', '\''],
        'color': 'green'
    },
}

# Marker symbols
MARKER_PATTERNS = {
    'city': {'char': '●', 'color': 'white'},
    'capital': {'char': '★', 'color': 'yellow'},
    'port': {'char': '⚓', 'color': 'blue'},
    'airport': {'char': '✈', 'color': 'white'},
    'station': {'char': '⊞', 'color': 'white'},
    'poi': {'char': '◆', 'color': 'yellow'},
    'landmark': {'char': '◎', 'color': 'magenta'},
    'user': {'char': '▲', 'color': 'red'},
}

# Network device symbols
NETWORK_PATTERNS = {
    'node': {'char': '⊚', 'color': 'green'},
    'gateway': {'char': '⊕', 'color': 'blue'},
    'sensor': {'char': '⊗', 'color': 'cyan'},
    'repeater': {'char': '⊙', 'color': 'yellow'},
    'end_device': {'char': '⊘', 'color': 'white'},
}

# Feature symbols
FEATURE_PATTERNS = {
    'river': {'char': '≈', 'color': 'blue'},
    'lake': {'char': '○', 'color': 'blue'},
    'road': {'char': '═', 'color': 'white'},
    'bridge': {'char': '╬', 'color': 'white'},
    'building': {'char': '■', 'color': 'white'},
    'park': {'char': '♣', 'color': 'green'},
}


# =============================================================================
# Map Tile Library
# =============================================================================

class MapTileLibrary:
    """
    Library of map tiles for terrain, features, and markers.
    
    Provides both built-in 1x1 patterns and loadable 24x24 tiles.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize tile library.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        
        # Tile storage
        self._tiles: Dict[str, MapTile] = {}
        
        # Load built-in patterns as 1x1 tiles
        self._load_builtin_patterns()
        
        # Load custom tiles from disk
        self._load_custom_tiles()
    
    def _load_builtin_patterns(self):
        """Load built-in 1x1 patterns as tiles."""
        # Terrain patterns
        for name, pattern in TERRAIN_PATTERNS.items():
            tile = MapTile(
                id=f"terrain_{name}",
                name=name.title(),
                category='terrain',
                size=(1, 1),
                data=[[pattern['char']]],
                colors={'fg': pattern.get('color', 'white')},
                metadata={'variants': pattern.get('variants', [])}
            )
            self._tiles[tile.id] = tile
        
        # Marker patterns
        for name, pattern in MARKER_PATTERNS.items():
            tile = MapTile(
                id=f"marker_{name}",
                name=name.title(),
                category='marker',
                size=(1, 1),
                data=[[pattern['char']]],
                colors={'fg': pattern.get('color', 'white')}
            )
            self._tiles[tile.id] = tile
        
        # Network patterns
        for name, pattern in NETWORK_PATTERNS.items():
            tile = MapTile(
                id=f"network_{name}",
                name=name.title(),
                category='network',
                size=(1, 1),
                data=[[pattern['char']]],
                colors={'fg': pattern.get('color', 'white')}
            )
            self._tiles[tile.id] = tile
        
        # Feature patterns
        for name, pattern in FEATURE_PATTERNS.items():
            tile = MapTile(
                id=f"feature_{name}",
                name=name.title(),
                category='feature',
                size=(1, 1),
                data=[[pattern['char']]],
                colors={'fg': pattern.get('color', 'white')}
            )
            self._tiles[tile.id] = tile
    
    def _load_custom_tiles(self):
        """Load custom tiles from disk."""
        # System tiles
        system_dir = self.project_root / "core" / "data" / "geography" / "tiles"
        if system_dir.exists():
            self._load_tiles_from_dir(system_dir)
        
        # User tiles
        user_dir = self.project_root / "memory" / "drafts" / "tiles" / "map"
        if user_dir.exists():
            self._load_tiles_from_dir(user_dir)
    
    def _load_tiles_from_dir(self, directory: Path):
        """Load all tiles from a directory."""
        for file_path in directory.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'id' in data:
                        tile = MapTile.from_dict(data)
                        self._tiles[tile.id] = tile
            except Exception:
                continue
    
    def get_tile(self, tile_id: str) -> Optional[MapTile]:
        """Get tile by ID."""
        return self._tiles.get(tile_id)
    
    def get_terrain(self, terrain_type: str) -> Optional[MapTile]:
        """Get terrain tile by type."""
        return self._tiles.get(f"terrain_{terrain_type}")
    
    def get_marker(self, marker_type: str) -> Optional[MapTile]:
        """Get marker tile by type."""
        return self._tiles.get(f"marker_{marker_type}")
    
    def get_network(self, device_type: str) -> Optional[MapTile]:
        """Get network device tile by type."""
        return self._tiles.get(f"network_{device_type}")
    
    def list_tiles(self, category: str = None) -> List[MapTile]:
        """List all tiles, optionally filtered by category."""
        tiles = list(self._tiles.values())
        if category:
            tiles = [t for t in tiles if t.category == category]
        return sorted(tiles, key=lambda t: (t.category, t.name))
    
    def list_categories(self) -> List[str]:
        """List all tile categories."""
        return sorted(set(t.category for t in self._tiles.values()))
    
    def add_tile(self, tile: MapTile, save: bool = True) -> bool:
        """
        Add a tile to the library.
        
        Args:
            tile: MapTile to add
            save: Save to disk if True
            
        Returns:
            Success flag
        """
        self._tiles[tile.id] = tile
        
        if save:
            return self.save_tile(tile)
        return True
    
    def save_tile(self, tile: MapTile) -> bool:
        """Save tile to user tiles directory."""
        user_dir = self.project_root / "memory" / "drafts" / "tiles" / "map"
        user_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = user_dir / f"{tile.id}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(tile.to_dict(), f, indent=2)
            return True
        except Exception:
            return False
    
    def remove_tile(self, tile_id: str) -> bool:
        """Remove tile from library (user tiles only)."""
        if tile_id not in self._tiles:
            return False
        
        # Don't allow removing built-in tiles
        if tile_id.startswith(('terrain_', 'marker_', 'network_', 'feature_')):
            if self._tiles[tile_id].size == (1, 1):
                return False  # Built-in pattern
        
        # Remove from memory
        del self._tiles[tile_id]
        
        # Remove from disk if exists
        user_dir = self.project_root / "memory" / "drafts" / "tiles" / "map"
        file_path = user_dir / f"{tile_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        return True


# =============================================================================
# Geography Data Manager
# =============================================================================

class GeographyDataManager:
    """
    Manages geography data with caching and lazy loading.
    
    Features:
    - LRU cache for layer data
    - Lazy loading of tile data
    - Import/export functionality
    - Offline data management
    """
    
    def __init__(self, project_root: Optional[Path] = None, cache_size: int = 10):
        """
        Initialize data manager.
        
        Args:
            project_root: Project root directory
            cache_size: Maximum number of layers to cache
        """
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.data_dir = self.project_root / "core" / "data" / "geography"
        self.cache_dir = self.project_root / "memory" / "cache" / "geography"
        
        # Layer cache (LRU)
        self._layer_cache: Dict[int, Dict] = {}
        self._cache_order: List[int] = []
        self._cache_size = cache_size
        
        # Metadata cache
        self._metadata: Optional[Dict] = None
        
        # Statistics
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'layers_loaded': 0,
            'bytes_cached': 0
        }
    
    @property
    def metadata(self) -> Dict:
        """Get geography metadata (lazy loaded)."""
        if self._metadata is None:
            self._metadata = self._load_metadata()
        return self._metadata
    
    def _load_metadata(self) -> Dict:
        """Load geography metadata."""
        metadata_file = self.data_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default metadata
        return {
            'version': '1.3.1',
            'layers': list(range(100, 900, 100)),
            'last_updated': datetime.now().isoformat(),
            'tile_count': 0,
            'city_count': 0
        }
    
    def get_layer(self, layer: int, force_reload: bool = False) -> Dict:
        """
        Get layer data (cached).
        
        Args:
            layer: Layer number (100-899)
            force_reload: Force reload from disk
            
        Returns:
            Layer data dictionary
        """
        # Check cache
        if not force_reload and layer in self._layer_cache:
            self.stats['cache_hits'] += 1
            # Move to end of LRU order
            if layer in self._cache_order:
                self._cache_order.remove(layer)
            self._cache_order.append(layer)
            return self._layer_cache[layer]
        
        self.stats['cache_misses'] += 1
        
        # Load from disk
        data = self._load_layer(layer)
        
        # Add to cache
        self._add_to_cache(layer, data)
        
        return data
    
    def _load_layer(self, layer: int) -> Dict:
        """Load layer data from disk."""
        layer_file = self.data_dir / f"map_layer_{layer}.json"
        
        if layer_file.exists():
            try:
                with open(layer_file, 'r', encoding='utf-8') as f:
                    self.stats['layers_loaded'] += 1
                    return json.load(f)
            except Exception:
                pass
        
        # Check cache directory
        cache_file = self.cache_dir / f"layer_{layer}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Return empty layer
        return {
            'layer': layer,
            'cells': {},
            'metadata': {}
        }
    
    def _add_to_cache(self, layer: int, data: Dict):
        """Add layer to cache with LRU eviction."""
        # Evict if cache full
        while len(self._cache_order) >= self._cache_size:
            oldest = self._cache_order.pop(0)
            if oldest in self._layer_cache:
                del self._layer_cache[oldest]
        
        self._layer_cache[layer] = data
        self._cache_order.append(layer)
        
        # Update stats
        data_size = len(json.dumps(data))
        self.stats['bytes_cached'] += data_size
    
    def save_layer(self, layer: int, data: Dict, to_cache: bool = False) -> bool:
        """
        Save layer data.
        
        Args:
            layer: Layer number
            data: Layer data
            to_cache: Save to cache directory (vs main data)
            
        Returns:
            Success flag
        """
        if to_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            file_path = self.cache_dir / f"layer_{layer}.json"
        else:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            file_path = self.data_dir / f"map_layer_{layer}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Update cache
            self._layer_cache[layer] = data
            if layer not in self._cache_order:
                self._cache_order.append(layer)
            
            return True
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear the layer cache."""
        self._layer_cache.clear()
        self._cache_order.clear()
        self.stats['bytes_cached'] = 0
    
    def preload_layers(self, layers: List[int]):
        """Preload multiple layers into cache."""
        for layer in layers:
            self.get_layer(layer)
    
    def get_cities(self) -> List[Dict]:
        """Get cities data (cached)."""
        cities_file = self.data_dir / "cities.json"
        if cities_file.exists():
            try:
                with open(cities_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('cities', []) if isinstance(data, dict) else data
            except Exception:
                pass
        return []
    
    def get_terrain(self) -> Dict:
        """Get terrain data."""
        terrain_file = self.data_dir / "terrain.json"
        if terrain_file.exists():
            try:
                with open(terrain_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def export_region(self, center_tile: str, radius: int = 5, 
                      layers: List[int] = None) -> Dict:
        """
        Export a region of map data.
        
        Args:
            center_tile: Center tile code
            radius: Radius in cells
            layers: Layers to export (default: [100])
            
        Returns:
            Export data dictionary
        """
        layers = layers or [100]
        
        export_data = {
            'version': '1.3.1',
            'center': center_tile,
            'radius': radius,
            'layers': {},
            'exported_at': datetime.now().isoformat()
        }
        
        for layer in layers:
            layer_data = self.get_layer(layer)
            # Filter to region cells (simplified - full implementation would use grid utils)
            export_data['layers'][layer] = layer_data
        
        return export_data
    
    def import_region(self, data: Dict, merge: bool = True) -> bool:
        """
        Import map region data.
        
        Args:
            data: Import data dictionary
            merge: Merge with existing data (vs replace)
            
        Returns:
            Success flag
        """
        if 'layers' not in data:
            return False
        
        for layer_num, layer_data in data['layers'].items():
            layer = int(layer_num)
            
            if merge:
                existing = self.get_layer(layer)
                existing['cells'].update(layer_data.get('cells', {}))
                self.save_layer(layer, existing, to_cache=True)
            else:
                self.save_layer(layer, layer_data, to_cache=True)
        
        return True
    
    def get_stats(self) -> Dict:
        """Get data manager statistics."""
        return {
            **self.stats,
            'cache_size': len(self._layer_cache),
            'max_cache_size': self._cache_size
        }


# =============================================================================
# Factory Functions
# =============================================================================

_tile_library: Optional[MapTileLibrary] = None
_data_manager: Optional[GeographyDataManager] = None


def get_tile_library() -> MapTileLibrary:
    """Get singleton tile library instance."""
    global _tile_library
    if _tile_library is None:
        _tile_library = MapTileLibrary()
    return _tile_library


def get_data_manager() -> GeographyDataManager:
    """Get singleton data manager instance."""
    global _data_manager
    if _data_manager is None:
        _data_manager = GeographyDataManager()
    return _data_manager


# =============================================================================
# CLI Test
# =============================================================================

if __name__ == "__main__":
    print("Map Tile Library Test")
    print("=" * 50)
    
    library = get_tile_library()
    
    print(f"\nCategories: {library.list_categories()}")
    
    print("\nTerrain Tiles:")
    for tile in library.list_tiles('terrain'):
        print(f"  {tile.id}: {tile.data[0][0]} ({tile.name})")
    
    print("\nMarker Tiles:")
    for tile in library.list_tiles('marker'):
        print(f"  {tile.id}: {tile.data[0][0]} ({tile.name})")
    
    print("\nNetwork Tiles:")
    for tile in library.list_tiles('network'):
        print(f"  {tile.id}: {tile.data[0][0]} ({tile.name})")
    
    print("\n" + "=" * 50)
    print("Geography Data Manager Test")
    print("=" * 50)
    
    manager = get_data_manager()
    print(f"\nMetadata: {manager.metadata}")
    print(f"Stats: {manager.get_stats()}")
