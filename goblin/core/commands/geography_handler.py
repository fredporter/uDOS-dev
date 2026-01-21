#!/usr/bin/env python3
"""
uDOS v1.3.1 - Geography Command Handler

Unified geography and mapping commands using the new MapGrid system.
Provides enhanced map navigation, viewport control, layer management,
and MeshCore device overlay integration.

Commands:
  MAP VIEW [width] [height]    - Show ASCII map view
  MAP PAN <direction>          - Pan viewport (N/S/E/W or numpad)
  MAP ZOOM <layer>             - Change to different layer
  MAP GOTO <tile|city>         - Jump to location
  MAP SEARCH <query>           - Search for cities/features
  MAP MARKER <action> [args]   - Manage custom markers
  MAP LAYER [number]           - Show/set current layer
  MAP DEVICES                  - Show MeshCore devices on map
  MAP STATUS                   - Current viewport status
  MAP EXPORT [format]          - Export map view

Layer Ranges:
  100-199: World/continent level (~83km/cell)
  200-299: Region/country level (~2.7km/cell)
  300-399: City/district level (~93m/cell)
  400-499: Block/street level (~3m/cell)
  500-599: Building/room level (~10cm/cell)
  600-699: Network layer (MeshCore devices)
  700-799: Custom layer (user overlays)
  800-899: Meta layer (annotations)

Version: 1.3.1
Author: Fred Porter
Date: December 2025
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from dev.goblin.core.commands.base_handler import BaseCommandHandler


class GeographyHandler(BaseCommandHandler):
    """
    Geography and mapping command handler.

    Integrates with MapGrid for viewport management and MeshCore
    for network device overlays.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._map_grid = None
        self._meshcore_service = None

    @property
    def map_grid(self):
        """Lazy-load MapGrid instance."""
        if self._map_grid is None:
            from dev.goblin.core.ui.map_grid import get_map_grid

            self._map_grid = get_map_grid()
        return self._map_grid

    @property
    def meshcore_service(self):
        """Lazy-load MeshCore service for device overlays."""
        if self._meshcore_service is None:
            try:
                from extensions.transport.meshcore import (
                    get_mesh_service as get_meshcore_service,
                )

                self._meshcore_service = get_meshcore_service()
            except ImportError:
                self._meshcore_service = None
        return self._meshcore_service

    def handle(self, command: str, params: str, grid=None, parser=None) -> str:
        """
        Route MAP subcommands to handlers.

        Args:
            command: Command name (MAP)
            params: Command parameters
            grid: Grid instance (for compatibility)
            parser: Parser instance (for compatibility)

        Returns:
            Command result message
        """
        if not params:
            return self._handle_status([])

        parts = params.strip().split(maxsplit=1)
        subcommand = parts[0].upper()
        sub_params = parts[1] if len(parts) > 1 else ""

        handlers = {
            "VIEW": self._handle_view,
            "PAN": self._handle_pan,
            "ZOOM": self._handle_zoom,
            "GOTO": self._handle_goto,
            "SEARCH": self._handle_search,
            "MARKER": self._handle_marker,
            "LAYER": self._handle_layer,
            "LAYERS": self._handle_layers,
            "DEVICES": self._handle_devices,
            "STATUS": self._handle_status,
            "EXPORT": self._handle_export,
            "CITIES": self._handle_cities,
            "INFO": self._handle_info,
        }

        handler = handlers.get(subcommand)
        if handler:
            return handler(sub_params.split() if sub_params else [])
        else:
            return self._handle_view(parts)  # Default to view

    # =========================================================================
    # View Commands
    # =========================================================================

    def _handle_view(self, params: List[str]) -> str:
        """
        Show ASCII map view of current viewport.

        Usage: MAP VIEW [width] [height]
        """
        width = 24
        height = 24

        # Parse optional dimensions
        if len(params) >= 1 and params[0].isdigit():
            width = int(params[0])
        if len(params) >= 2 and params[1].isdigit():
            height = int(params[1])

        # Update viewport size
        self.map_grid.viewport.width = min(max(10, width), 80)
        self.map_grid.viewport.height = min(max(10, height), 40)

        # Render map
        map_output = self.map_grid.render(include_frame=True)

        # Add visible cities legend
        visible_cities = self.map_grid.get_visible_cities()[:5]  # Top 5
        if visible_cities:
            map_output += "\n\n● Cities: " + ", ".join(
                c["name"] for c in visible_cities
            )

        # Add visible devices if network overlay enabled
        if self.map_grid.viewport.show_network:
            devices = self.map_grid.get_visible_devices()
            if devices:
                map_output += f"\n⊚ Devices: {len(devices)} visible"

        return map_output

    def _handle_status(self, params: List[str]) -> str:
        """
        Show current map viewport status.

        Usage: MAP STATUS
        """
        vp = self.map_grid.viewport
        layer_info = self.map_grid.get_layer_info()

        center_tile = self.map_grid.make_tile_code(
            vp.center_col, vp.center_row, vp.layer
        )
        lat, lon = self.map_grid.grid_to_latlong(vp.center_col, vp.center_row)

        result = f"""🗺️  Map Status
{'='*50}
Center: {center_tile}
Coordinates: {lat:.4f}°, {lon:.4f}°
Grid Position: Column {vp.center_col}, Row {vp.center_row}

Layer: {vp.layer} ({layer_info['description']})
Resolution: {layer_info['resolution_km'] or 'Virtual'} km/cell
Layer Range: {layer_info['start']}-{layer_info['end']}

Viewport: {vp.width}×{vp.height} cells
Network Overlay: {'ON' if vp.show_network else 'OFF'}
Labels: {'ON' if vp.show_labels else 'OFF'}
"""

        # Add visible items count
        visible_cities = self.map_grid.get_visible_cities()
        visible_devices = self.map_grid.get_visible_devices()

        result += f"""
Visible Cities: {len(visible_cities)}
Visible Devices: {len(visible_devices)}
Markers: {len(self.map_grid.markers)}

Commands:
  MAP PAN <N/S/E/W>    - Move viewport
  MAP ZOOM <layer>     - Change layer (100-899)
  MAP GOTO <city>      - Jump to city
  MAP SEARCH <query>   - Find locations
"""
        return result

    # =========================================================================
    # Navigation Commands
    # =========================================================================

    def _handle_pan(self, params: List[str]) -> str:
        """
        Pan viewport in a direction.

        Usage: MAP PAN <direction>
        Directions: N/NORTH, S/SOUTH, E/EAST, W/WEST
                    NE, NW, SE, SW
                    Or numpad: 8=N, 2=S, 4=W, 6=E, 7=NW, 9=NE, 1=SW, 3=SE
        """
        if not params:
            return "Usage: MAP PAN <direction> (N/S/E/W, NE/NW/SE/SW, or numpad 1-9)"

        direction = params[0].upper()
        step = 5  # Default pan step

        if len(params) > 1 and params[1].isdigit():
            step = int(params[1])

        # Direction mapping
        dx, dy = 0, 0
        directions = {
            "N": (0, -step),
            "NORTH": (0, -step),
            "8": (0, -step),
            "S": (0, step),
            "SOUTH": (0, step),
            "2": (0, step),
            "E": (step, 0),
            "EAST": (step, 0),
            "6": (step, 0),
            "W": (-step, 0),
            "WEST": (-step, 0),
            "4": (-step, 0),
            "NE": (step, -step),
            "9": (step, -step),
            "NW": (-step, -step),
            "7": (-step, -step),
            "SE": (step, step),
            "3": (step, step),
            "SW": (-step, step),
            "1": (-step, step),
        }

        if direction in directions:
            dx, dy = directions[direction]
            self.map_grid.pan(dx, dy)
            return self._handle_view([])
        else:
            return f"Unknown direction: {direction}. Use N/S/E/W, NE/NW/SE/SW, or numpad 1-9."

    def _handle_zoom(self, params: List[str]) -> str:
        """
        Change to a different map layer (zoom level).

        Usage: MAP ZOOM <layer>
        Layers: 100 (world), 200 (region), 300 (city), 400 (block), 500 (building)
                600 (network), 700 (custom), 800 (meta)
        """
        if not params:
            return """Usage: MAP ZOOM <layer>

Layer Ranges:
  100-199: World level (~83km/cell)
  200-299: Region level (~2.7km/cell)
  300-399: City level (~93m/cell)
  400-499: Block level (~3m/cell)
  500-599: Building level (~10cm/cell)
  600-699: Network layer (MeshCore)
  700-799: Custom layer
  800-899: Meta layer

Example: MAP ZOOM 300"""

        try:
            layer = int(params[0])
            if 100 <= layer <= 899:
                self.map_grid.zoom(layer)
                return self._handle_status([])
            else:
                return "Layer must be between 100 and 899."
        except ValueError:
            return "Invalid layer number. Use a value between 100 and 899."

    def _handle_goto(self, params: List[str]) -> str:
        """
        Jump viewport to a location.

        Usage: MAP GOTO <city_name> | MAP GOTO <tile_code>
        """
        if not params:
            return "Usage: MAP GOTO <city_name> or MAP GOTO <tile_code>"

        target = " ".join(params)

        # Try as tile code first (e.g., QB185-100)
        if "-" in target and any(c.isdigit() for c in target):
            try:
                parsed = self.map_grid.parse_tile_code(target.upper())
                self.map_grid.set_center(col=parsed["column"], row=parsed["row"])
                self.map_grid.viewport.layer = parsed["layer"]
                return self._handle_view([])
            except (ValueError, KeyError):
                pass

        # Try as city name
        if self.map_grid.goto_city(target):
            return self._handle_view([])

        # Search for matches
        results = self.map_grid.search_city(target)
        if results:
            suggestions = "\n".join(
                f"  • {r['name']}, {r['country']} ({r['tile_code']})"
                for r in results[:5]
            )
            return f"City not found: {target}\n\nDid you mean:\n{suggestions}"

        return f"Location not found: {target}"

    def _handle_search(self, params: List[str]) -> str:
        """
        Search for cities and features.

        Usage: MAP SEARCH <query>
        """
        if not params:
            return "Usage: MAP SEARCH <query>"

        query = " ".join(params)
        results = self.map_grid.search_city(query)

        if not results:
            return f"No results found for: {query}"

        output = f"🔍 Search Results for '{query}' ({len(results)} found):\n"
        output += "=" * 50 + "\n"

        for r in results[:10]:  # Show top 10
            output += f"  {r['name']}, {r['country']}\n"
            output += f"    TILE: {r['tile_code']} | {r['lat']:.2f}°, {r['lon']:.2f}°\n"

        if len(results) > 10:
            output += f"\n  ... and {len(results) - 10} more results"

        output += "\n\nUse MAP GOTO <city> to jump to a location."
        return output

    # =========================================================================
    # Layer Management
    # =========================================================================

    def _handle_layer(self, params: List[str]) -> str:
        """
        Show or change current layer.

        Usage: MAP LAYER [number]
        """
        if params and params[0].isdigit():
            return self._handle_zoom(params)

        return self._handle_layers(params)

    def _handle_layers(self, params: List[str]) -> str:
        """
        Show all available layers.

        Usage: MAP LAYERS
        """
        from dev.goblin.core.ui.map_grid import LayerRange

        current = self.map_grid.viewport.layer

        output = f"""🗺️  Map Layers
{'='*50}
Current Layer: {current}

Geographic Layers:
  100-199: World/Continent    (~83km/cell)    {'◄' if 100 <= current <= 199 else ''}
  200-299: Region/Country     (~2.7km/cell)   {'◄' if 200 <= current <= 299 else ''}
  300-399: City/District      (~93m/cell)     {'◄' if 300 <= current <= 399 else ''}
  400-499: Block/Street       (~3m/cell)      {'◄' if 400 <= current <= 499 else ''}
  500-599: Building/Room      (~10cm/cell)    {'◄' if 500 <= current <= 599 else ''}

Virtual Layers:
  600-699: Network/MeshCore   (device overlay) {'◄' if 600 <= current <= 699 else ''}
  700-799: Custom/User        (user overlays)  {'◄' if 700 <= current <= 799 else ''}
  800-899: Meta/Annotations   (bookmarks, etc) {'◄' if 800 <= current <= 899 else ''}

Use MAP ZOOM <layer> to change layers.
"""
        return output

    # =========================================================================
    # Device Overlay Commands
    # =========================================================================

    def _handle_devices(self, params: List[str]) -> str:
        """
        Show MeshCore devices on current map view.

        Usage: MAP DEVICES [TOGGLE|ON|OFF]
        """
        if params:
            action = params[0].upper()
            if action == "TOGGLE":
                self.map_grid.viewport.show_network = (
                    not self.map_grid.viewport.show_network
                )
            elif action == "ON":
                self.map_grid.viewport.show_network = True
            elif action == "OFF":
                self.map_grid.viewport.show_network = False

        # Get visible devices
        devices = self.map_grid.get_visible_devices()

        output = f"""⊚ MeshCore Device Overlay
{'='*50}
Overlay Status: {'ENABLED' if self.map_grid.viewport.show_network else 'DISABLED'}
Visible Devices: {len(devices)}
"""

        if devices:
            output += "\nDevices in View:\n"
            for d in devices:
                status_icon = {
                    "online": "●",
                    "offline": "○",
                    "connecting": "◐",
                    "error": "◑",
                }.get(d["status"], "?")
                output += f"  {status_icon} {d['device_id']} ({d['type']}) - {d['tile_code']}\n"
                output += f"    Signal: {d['signal']}% | Status: {d['status']}\n"
        else:
            output += "\nNo devices in current viewport."
            output += "\n\nTo add test device: Use MESH SCAN to discover devices."

        output += f"\n\nCommands:\n  MAP DEVICES TOGGLE - Toggle overlay\n  MAP DEVICES ON/OFF - Enable/disable"
        return output

    # =========================================================================
    # Marker Commands
    # =========================================================================

    def _handle_marker(self, params: List[str]) -> str:
        """
        Manage custom map markers.

        Usage: MAP MARKER ADD <tile_code> [label]
               MAP MARKER REMOVE <tile_code>
               MAP MARKER LIST
               MAP MARKER CLEAR
        """
        if not params:
            return """Usage: MAP MARKER <action> [args]

Actions:
  ADD <tile_code> [label]  - Add marker at location
  REMOVE <tile_code>       - Remove marker
  LIST                     - Show all markers
  CLEAR                    - Remove all markers

Example: MAP MARKER ADD QB185-100 "Home Base" """

        action = params[0].upper()

        if action == "LIST":
            if not self.map_grid.markers:
                return "No markers set. Use MAP MARKER ADD <tile> [label]"

            output = f"📍 Map Markers ({len(self.map_grid.markers)}):\n"
            for m in self.map_grid.markers:
                tile = self.map_grid.make_tile_code(m["col"], m["row"], 100)
                output += f"  {m['symbol']} {tile} - {m.get('label', 'Unlabeled')}\n"
            return output

        elif action == "CLEAR":
            count = len(self.map_grid.markers)
            self.map_grid.markers.clear()
            return f"Cleared {count} markers."

        elif action == "ADD" and len(params) > 1:
            try:
                parsed = self.map_grid.parse_tile_code(params[1].upper())
                label = " ".join(params[2:]) if len(params) > 2 else ""
                self.map_grid.add_marker(
                    parsed["column"], parsed["row"], label=label, symbol="◆"
                )
                return f"Added marker at {params[1].upper()}" + (
                    f": {label}" if label else ""
                )
            except (ValueError, KeyError):
                return f"Invalid tile code: {params[1]}"

        elif action == "REMOVE" and len(params) > 1:
            try:
                parsed = self.map_grid.parse_tile_code(params[1].upper())
                col, row = parsed["column"], parsed["row"]
                original_count = len(self.map_grid.markers)
                self.map_grid.markers = [
                    m
                    for m in self.map_grid.markers
                    if not (m["col"] == col and m["row"] == row)
                ]
                if len(self.map_grid.markers) < original_count:
                    return f"Removed marker at {params[1].upper()}"
                else:
                    return f"No marker found at {params[1].upper()}"
            except (ValueError, KeyError):
                return f"Invalid tile code: {params[1]}"

        return "Unknown marker action. Use ADD, REMOVE, LIST, or CLEAR."

    # =========================================================================
    # Information Commands
    # =========================================================================

    def _handle_cities(self, params: List[str]) -> str:
        """
        List visible cities or search by region.

        Usage: MAP CITIES [region]
        """
        visible = self.map_grid.get_visible_cities()

        if not visible:
            return "No cities visible in current viewport. Try MAP PAN or MAP ZOOM."

        output = f"🏙️ Cities in View ({len(visible)}):\n"
        output += "=" * 40 + "\n"

        for city in visible:
            output += f"  ● {city['name']} ({city['tile_code']})\n"

        return output

    def _handle_info(self, params: List[str]) -> str:
        """
        Get information about a specific tile/cell.

        Usage: MAP INFO <tile_code>
        """
        if not params:
            # Show info for center tile
            tile_code = self.map_grid.make_tile_code(
                self.map_grid.viewport.center_col,
                self.map_grid.viewport.center_row,
                self.map_grid.viewport.layer,
            )
        else:
            tile_code = params[0].upper()

        try:
            parsed = self.map_grid.parse_tile_code(tile_code)
            lat, lon = self.map_grid.grid_to_latlong(parsed["column"], parsed["row"])
            layer_info = self.map_grid.get_layer_info(parsed["layer"])

            output = f"""📍 Tile Information: {tile_code}
{'='*50}
Grid Cell: {parsed['grid_cell']}
Column: {parsed['column_code']} ({parsed['column']})
Row: {parsed['row']}
Layer: {parsed['layer']} ({layer_info['description']})

Coordinates: {lat:.4f}°, {lon:.4f}°
Resolution: {layer_info['resolution_km'] or 'Virtual'} km/cell

"""
            # Check for cities at this location
            for city in self.map_grid.cities:
                city_col, city_row = self.map_grid.latlong_to_grid(
                    city.get("lat", 0), city.get("lon", 0)
                )
                if city_col == parsed["column"] and city_row == parsed["row"]:
                    output += f"City: {city.get('name')}, {city.get('country')}\n"
                    break

            return output

        except (ValueError, KeyError) as e:
            return f"Invalid tile code: {tile_code}"

    def _handle_export(self, params: List[str]) -> str:
        """
        Export current map view.

        Usage: MAP EXPORT [format]
        Formats: ASCII (default), JSON, HTML
        """
        fmt = params[0].upper() if params else "ASCII"

        if fmt == "ASCII":
            return self.map_grid.render(include_frame=True)

        elif fmt == "JSON":
            col_range, row_range = self.map_grid.viewport.visible_range
            data = {
                "viewport": {
                    "center_col": self.map_grid.viewport.center_col,
                    "center_row": self.map_grid.viewport.center_row,
                    "width": self.map_grid.viewport.width,
                    "height": self.map_grid.viewport.height,
                    "layer": self.map_grid.viewport.layer,
                },
                "visible_cities": self.map_grid.get_visible_cities(),
                "visible_devices": self.map_grid.get_visible_devices(),
                "markers": self.map_grid.markers,
            }
            return json.dumps(data, indent=2)

        elif fmt == "HTML":
            return "HTML export not yet implemented. Use ASCII or JSON."

        return f"Unknown format: {fmt}. Use ASCII, JSON, or HTML."


# =============================================================================
# Handler Factory
# =============================================================================


def get_geography_handler(**kwargs) -> GeographyHandler:
    """Create geography handler instance."""
    return GeographyHandler(**kwargs)
