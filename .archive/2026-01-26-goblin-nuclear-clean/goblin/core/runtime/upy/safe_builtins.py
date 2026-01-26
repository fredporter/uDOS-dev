"""
Safe Built-in Functions for uPY v0.2

Provides limited set of built-in functions for sandboxed execution.
"""

from typing import Dict, Any
import math


def safe_print(*args, **kwargs) -> None:
    """Safe print function (outputs to script context)."""
    # In actual implementation, this would log to script output buffer
    print(*args, **kwargs)


def safe_len(obj) -> int:
    """Safe len() function."""
    return len(obj)


def safe_range(*args) -> range:
    """Safe range() function."""
    return range(*args)


def safe_str(obj) -> str:
    """Safe str() conversion."""
    return str(obj)


def safe_int(obj) -> int:
    """Safe int() conversion."""
    return int(obj)


def safe_float(obj) -> float:
    """Safe float() conversion."""
    return float(obj)


def safe_bool(obj) -> bool:
    """Safe bool() conversion."""
    return bool(obj)


def safe_list(obj=None) -> list:
    """Safe list() creation."""
    if obj is None:
        return []
    return list(obj)


def safe_dict(obj=None, **kwargs) -> dict:
    """Safe dict() creation."""
    if obj is None:
        return dict(**kwargs)
    return dict(obj, **kwargs)


def safe_set(obj=None) -> set:
    """Safe set() creation."""
    if obj is None:
        return set()
    return set(obj)


def safe_tuple(obj=None) -> tuple:
    """Safe tuple() creation."""
    if obj is None:
        return ()
    return tuple(obj)


def safe_min(*args, **kwargs):
    """Safe min() function."""
    return min(*args, **kwargs)


def safe_max(*args, **kwargs):
    """Safe max() function."""
    return max(*args, **kwargs)


def safe_sum(iterable, start=0):
    """Safe sum() function."""
    return sum(iterable, start)


def safe_sorted(iterable, **kwargs):
    """Safe sorted() function."""
    return sorted(iterable, **kwargs)


def safe_reversed(iterable):
    """Safe reversed() function."""
    return reversed(iterable)


def safe_enumerate(iterable, start=0):
    """Safe enumerate() function."""
    return enumerate(iterable, start)


def safe_zip(*iterables):
    """Safe zip() function."""
    return zip(*iterables)


def safe_map(func, *iterables):
    """Safe map() function."""
    return map(func, *iterables)


def safe_filter(func, iterable):
    """Safe filter() function."""
    return filter(func, iterable)


def safe_any(iterable) -> bool:
    """Safe any() function."""
    return any(iterable)


def safe_all(iterable) -> bool:
    """Safe all() function."""
    return all(iterable)


def safe_abs(x):
    """Safe abs() function."""
    return abs(x)


def safe_round(x, ndigits=None):
    """Safe round() function."""
    return round(x, ndigits)


def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    """
    Safe __import__ that only allows whitelisted modules.

    Args:
        name: Module name
        globals, locals, fromlist, level: Standard import parameters

    Returns:
        Imported module

    Raises:
        ImportError: If module not in whitelist
    """
    allowed = {
        "json",
        "math",
        "datetime",
        "time",
        "re",
        "random",
        "string",
        "itertools",
        "collections",
        "functools",
        "operator",
    }

    base_module = name.split(".")[0]

    if base_module not in allowed:
        raise ImportError(f"Module '{name}' not allowed in uPY sandbox")

    return __import__(name, globals, locals, fromlist, level)


def get_safe_builtins() -> Dict[str, Any]:
    """
    Get dictionary of safe built-in functions for uPY execution.

    Returns:
        Dictionary of safe built-ins
    """
    return {
        # Type constructors
        "str": safe_str,
        "int": safe_int,
        "float": safe_float,
        "bool": safe_bool,
        "list": safe_list,
        "dict": safe_dict,
        "set": safe_set,
        "tuple": safe_tuple,
        # I/O
        "print": safe_print,
        # Sequence operations
        "len": safe_len,
        "range": safe_range,
        "min": safe_min,
        "max": safe_max,
        "sum": safe_sum,
        "sorted": safe_sorted,
        "reversed": safe_reversed,
        "enumerate": safe_enumerate,
        "zip": safe_zip,
        "map": safe_map,
        "filter": safe_filter,
        # Logic
        "any": safe_any,
        "all": safe_all,
        # Math
        "abs": safe_abs,
        "round": safe_round,
        # Import (restricted)
        "__import__": safe_import,
        # Constants
        "True": True,
        "False": False,
        "None": None,
        # Exceptions (for catching)
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "KeyError": KeyError,
        "IndexError": IndexError,
        "AttributeError": AttributeError,
        "ZeroDivisionError": ZeroDivisionError,
    }


def get_safe_modules() -> Dict[str, Any]:
    """
    Get dictionary of safe modules for import.

    Returns:
        Dictionary of safe modules
    """
    import json
    import math
    import datetime
    import time
    import re
    import random
    import string
    import itertools
    import collections
    import functools
    import operator

    return {
        "json": json,
        "math": math,
        "datetime": datetime,
        "time": time,
        "re": re,
        "random": random,
        "string": string,
        "itertools": itertools,
        "collections": collections,
        "functools": functools,
        "operator": operator,
    }


def get_spatial_builtins(spatial_manager) -> Dict[str, Any]:
    """
    Get spatial computing built-ins for location-aware scripts.

    Provides:
    - LOCATION: Current grid position
    - PROXIMITY: Check proximity to target
    - NFC: Verify NFC ring
    - VERIFY: Verify location condition
    - UNLOCK: Location/proximity-based decryption
    - PLACE: Place object at location
    - FIND: Find objects near location

    Args:
        spatial_manager: SpatialManager instance

    Returns:
        Dictionary of spatial built-ins
    """

    class LocationAPI:
        """Location information and verification."""

        @staticmethod
        def get():
            """Get current grid location."""
            grid = spatial_manager.get_current_grid()
            if not grid:
                return None
            return {
                "grid": grid.code,
                "layer": grid.layer,
                "column": grid.column,
                "row": grid.row,
                "region": grid.region,
            }

        @staticmethod
        def set(grid_code: str):
            """Set current grid location."""
            grid = spatial_manager.parse_grid_code(grid_code)
            spatial_manager.set_current_grid(grid)
            return True

        @staticmethod
        def verify(grid_code: str, tolerance: float = 10.0) -> bool:
            """Verify user is at specified location."""
            grid = spatial_manager.parse_grid_code(grid_code)
            condition = spatial_manager.verify_location(grid, tolerance)
            return condition.verified

        @staticmethod
        def distance_to(grid_code: str) -> float:
            """Get distance to target grid in meters."""
            current = spatial_manager.get_current_grid()
            if not current:
                return -1.0
            target = spatial_manager.parse_grid_code(grid_code)
            try:
                return current.distance_to(target)
            except ValueError:
                return -1.0

    class ProximityAPI:
        """Proximity detection via transports."""

        @staticmethod
        def check(transport: str, target_id: str, max_distance: float = None) -> bool:
            """Check if target is in proximity range."""
            condition = spatial_manager.check_proximity(
                transport, target_id, max_distance
            )
            return condition.verified

        @staticmethod
        def nfc(target_id: str) -> bool:
            """Check NFC proximity (10cm range)."""
            return ProximityAPI.check("nfc", target_id, 0.1)

        @staticmethod
        def bluetooth(target_id: str, max_meters: float = 10.0) -> bool:
            """Check Bluetooth proximity."""
            return ProximityAPI.check("bluetooth", target_id, max_meters)

        @staticmethod
        def mesh(target_id: str, max_meters: float = 100.0) -> bool:
            """Check MeshCore P2P proximity."""
            return ProximityAPI.check("meshcore", target_id, max_meters)

    class NFCAPI:
        """NFC ring verification."""

        @staticmethod
        def verify(ring_id: str, challenge: str = None) -> bool:
            """Verify NFC ring identity."""
            condition = spatial_manager.verify_nfc_ring(ring_id, challenge)
            return condition.verified

        @staticmethod
        def available() -> bool:
            """Check if NFC is available."""
            return spatial_manager.transports["nfc"]

    class UnlockAPI:
        """Location/proximity-based unlocking."""

        @staticmethod
        def at_location(data, grid_code: str, tolerance: float = 10.0):
            """Unlock data if at specified location."""
            grid = spatial_manager.parse_grid_code(grid_code)
            result = spatial_manager.location_unlock(data, grid, tolerance)
            return result is not None

        @staticmethod
        def near_device(data, transport: str, target_id: str):
            """Unlock data if near target device."""
            result = spatial_manager.proximity_unlock(data, transport, target_id)
            return result is not None

    class ObjectAPI:
        """Spatial object placement and discovery."""

        @staticmethod
        def place(
            id: str,
            type: str,
            grid_code: str,
            content: dict,
            virtual: bool = False,
            conditions: list = None,
        ):
            """Place object at location."""
            from ..services.spatial_manager import SpatialObject, SpatialCondition

            grid = spatial_manager.parse_grid_code(grid_code)

            # Parse conditions if provided
            access_conditions = []
            if conditions:
                for cond in conditions:
                    access_conditions.append(
                        SpatialCondition(
                            type=cond["type"], parameters=cond["parameters"]
                        )
                    )

            obj = SpatialObject(
                id=id,
                type=type,
                location=grid,
                virtual=virtual,
                content=content,
                access_conditions=access_conditions,
            )

            return spatial_manager.place_object(obj)

        @staticmethod
        def find(grid_code: str = None, radius: float = 10.0) -> list:
            """Find objects near location."""
            if grid_code:
                grid = spatial_manager.parse_grid_code(grid_code)
            else:
                grid = spatial_manager.get_current_grid()
                if not grid:
                    return []

            objects = spatial_manager.find_objects_at(grid, radius)
            return [
                {
                    "id": obj.id,
                    "type": obj.type,
                    "location": obj.location.code,
                    "virtual": obj.virtual,
                    "content": obj.content,
                }
                for obj in objects
            ]

    return {
        "LOCATION": LocationAPI,
        "PROXIMITY": ProximityAPI,
        "NFC": NFCAPI,
        "UNLOCK": UnlockAPI,
        "OBJECT": ObjectAPI,
    }
