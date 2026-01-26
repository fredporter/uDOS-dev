"""
uDOS Maps Service
Core v1.0.0.32

Grid-first TILE code system with multi-layer support.
Provides map navigation, coordinate conversion, and layer management.

Components:
- map_engine.py: Grid engine with TILE code conversion
- map_data_manager.py: GeoJSON and layer data management

Usage:
    from dev.goblin.core.services.maps import MapEngine

    engine = MapEngine()
    tile = engine.latlong_to_tile(51.5074, -0.1278)  # London
"""

from .map_engine import MapEngine
from .map_data_manager import MapDataManager

__all__ = ["MapEngine", "MapDataManager"]
