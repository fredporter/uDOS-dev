"""
Waypoint Handler - Commands for waypoint navigation.

Handles WAYPOINT, WP commands for creating, listing, and
navigating to waypoints across universe layers.

Part of uDOS Alpha v1.0.0.53+
"""

from typing import Dict, List, Optional, Any

from dev.goblin.core.commands.base_handler import BaseCommandHandler
from dev.goblin.core.services.logging_manager import get_logger
from dev.goblin.core.services.waypoint_manager import (
    get_waypoint_manager,
    WaypointType,
    WaypointVisibility,
)

logger = get_logger("command-waypoint")


class WaypointHandler(BaseCommandHandler):
    """
    Handles waypoint navigation commands.

    Commands:
        WAYPOINT LIST         - List nearby waypoints
        WAYPOINT HERE         - Show waypoints at current tile
        WAYPOINT GOTO <id>    - Navigate to waypoint
        WAYPOINT NEW <name>   - Create waypoint
        WAYPOINT SHOW <id>    - Show waypoint details
        WAYPOINT SEARCH <q>   - Search waypoints
        WP <alias>            - Shortcut for WAYPOINT
    """

    def __init__(self, **kwargs):
        """Initialize waypoint handler."""
        super().__init__(**kwargs)
        self._waypoint_manager = None

    @property
    def waypoint_manager(self):
        """Lazy-load waypoint manager."""
        if self._waypoint_manager is None:
            self._waypoint_manager = get_waypoint_manager()
        return self._waypoint_manager

    def handle(self, command: str, params: str, grid=None, parser=None) -> Dict:
        """
        Route waypoint commands.

        Args:
            command: Command name (WAYPOINT, WP)
            params: Command parameters
            grid: Display grid
            parser: Command parser

        Returns:
            Result dict with content or error
        """
        logger.info(f"[LOCAL] Waypoint command: {command} {params}")

        # Parse subcommand
        parts = params.strip().split(None, 1)
        subcommand = parts[0].upper() if parts else ""
        sub_params = parts[1] if len(parts) > 1 else ""

        # Route subcommands
        if subcommand == "LIST" or subcommand == "L":
            return self._handle_list(sub_params)
        elif subcommand == "HERE" or subcommand == "H":
            return self._handle_here(sub_params)
        elif subcommand == "GOTO" or subcommand == "G" or subcommand == "GO":
            return self._handle_goto(sub_params)
        elif subcommand == "NEW" or subcommand == "N" or subcommand == "CREATE":
            return self._handle_new(sub_params)
        elif subcommand == "SHOW" or subcommand == "S":
            return self._handle_show(sub_params)
        elif subcommand == "SEARCH":
            return self._handle_search(sub_params)
        elif subcommand == "STATS":
            return self._handle_stats()
        elif subcommand == "CONNECTIONS" or subcommand == "CONN":
            return self._handle_connections(sub_params)
        elif subcommand == "LAYERS":
            return self._handle_layers()
        elif subcommand == "HELP" or subcommand == "?":
            return self._handle_help()
        elif params.strip():
            # Default: search
            return self._handle_search(params)
        else:
            return self._handle_help()

    def _handle_list(self, params: str) -> Dict:
        """
        List waypoints with optional filters.

        Usage: WAYPOINT LIST [--layer=N] [--type=TYPE] [--tag=TAG]
        """
        layer = None
        wp_type = None
        tag = None
        limit = 30

        parts = params.split("--")
        for part in parts[1:]:
            if part.startswith("layer="):
                try:
                    layer = int(part[6:].strip())
                except ValueError:
                    pass
            elif part.startswith("type="):
                try:
                    wp_type = WaypointType(part[5:].strip())
                except ValueError:
                    pass
            elif part.startswith("tag="):
                tag = part[4:].strip()
            elif part.startswith("limit="):
                try:
                    limit = int(part[6:].strip())
                except ValueError:
                    pass

        # Get waypoints
        waypoints = self.waypoint_manager.search(
            layer=layer, waypoint_type=wp_type, tags=[tag] if tag else None, limit=limit
        )

        lines = ["📍 Waypoints"]
        if layer is not None:
            lines[
                0
            ] += f" (Layer {layer}: {self.waypoint_manager.get_layer_name(layer)})"
        lines.append("─" * 50)

        # Group by layer
        by_layer = {}
        for wp in waypoints:
            if wp.layer not in by_layer:
                by_layer[wp.layer] = []
            by_layer[wp.layer].append(wp)

        for layer_num in sorted(by_layer.keys()):
            layer_name = self.waypoint_manager.get_layer_name(layer_num)
            lines.append(f"\n[L{layer_num:03d}] {layer_name}")

            for wp in by_layer[layer_num]:
                type_icon = self._type_icon(wp.waypoint_type)
                verified = "✓" if wp.verified else ""
                lines.append(f"  {type_icon} {wp.name} @ {wp.tile} {verified}")

        if not waypoints:
            lines.append("No waypoints found.")

        lines.append("")
        lines.append("─" * 50)
        lines.append("Use WAYPOINT SHOW <id> for details")

        return {"content": "\n".join(lines), "type": "waypoint_list"}

    def _handle_here(self, params: str) -> Dict:
        """
        Show waypoints at current location.

        Usage: WAYPOINT HERE
        """
        layer, tile = self._get_current_location()

        if not tile:
            return {"error": "Current location unknown. Use MAP to navigate first."}

        waypoints = self.waypoint_manager.get_at_tile(layer, tile)

        lines = [f"📍 Waypoints at L{layer}:{tile}"]
        lines.append("─" * 50)

        if waypoints:
            for wp in waypoints:
                type_icon = self._type_icon(wp.waypoint_type)
                lines.append(f"{type_icon} {wp.name}")
                lines.append(f"   Type: {wp.waypoint_type.value}")

                if wp.connections:
                    lines.append(f"   Connections: {len(wp.connections)}")
                    for conn in wp.connections[:3]:
                        layer_name = self.waypoint_manager.get_layer_name(
                            conn.target_layer
                        )
                        lines.append(
                            f"     → L{conn.target_layer}:{conn.target_tile} ({layer_name})"
                        )

                if wp.description:
                    lines.append(f"   {wp.description[:60]}")

                lines.append(f"   [{wp.waypoint_id}]")
                lines.append("")
        else:
            lines.append("No waypoints at this location.")
            lines.append("")
            lines.append("Create one with: WAYPOINT NEW <name>")

        return {"content": "\n".join(lines), "type": "waypoint_here"}

    def _handle_goto(self, params: str) -> Dict:
        """
        Navigate to a waypoint.

        Usage: WAYPOINT GOTO <waypoint_id_or_name>
        """
        target = params.strip()
        if not target:
            return {"error": "Usage: WAYPOINT GOTO <waypoint_id_or_name>"}

        # Find waypoint
        wp = self.waypoint_manager.get(target)

        if not wp:
            # Try search
            results = self.waypoint_manager.search(query=target, limit=1)
            if results:
                wp = results[0]

        if not wp:
            return {"error": f"Waypoint not found: {target}"}

        # Check if we can reach it
        current_layer, current_tile = self._get_current_location()

        # Check for connection from current location
        connections = self.waypoint_manager.get_connections_from(
            current_layer, current_tile
        )

        direct_connection = None
        for conn_wp, conn in connections:
            if conn.target_layer == wp.layer and conn.target_tile == wp.tile:
                direct_connection = (conn_wp, conn)
                break

        lines = [f"🚀 Navigate to: {wp.name}"]
        lines.append("─" * 50)
        lines.append(f"Target: L{wp.layer}:{wp.tile}")
        lines.append(f"Layer: {self.waypoint_manager.get_layer_name(wp.layer)}")

        if direct_connection:
            conn_wp, conn = direct_connection
            lines.append("")
            lines.append(f"✅ Direct connection available via: {conn_wp.name}")
            lines.append("")
            lines.append("Execute navigation? (This would update current position)")
            # In a real implementation, this would trigger the navigation
        else:
            lines.append("")
            lines.append("⚠️ No direct connection from current location.")
            lines.append("You may need to find an intermediate waypoint.")

        if wp.description:
            lines.append("")
            lines.append(f"Description: {wp.description}")

        return {
            "content": "\n".join(lines),
            "type": "waypoint_goto",
            "target_layer": wp.layer,
            "target_tile": wp.tile,
            "waypoint_id": wp.waypoint_id,
        }

    def _handle_new(self, params: str) -> Dict:
        """
        Create a new waypoint.

        Usage: WAYPOINT NEW <name> [--type=TYPE] [--desc=...] [--tags=...]
        """
        if not params.strip():
            return {
                "error": "Usage: WAYPOINT NEW <name> [--type=poi] [--desc=...] [--tags=...]"
            }

        parts = params.split("--")
        name = parts[0].strip()

        if not name:
            return {"error": "Waypoint name is required"}

        # Get current location as default
        layer, tile = self._get_current_location()

        wp_type = WaypointType.POI
        description = ""
        tags = []

        for part in parts[1:]:
            if part.startswith("type="):
                try:
                    wp_type = WaypointType(part[5:].strip())
                except ValueError:
                    return {
                        "error": f"Invalid type. Valid: {', '.join(t.value for t in WaypointType)}"
                    }
            elif part.startswith("desc="):
                description = part[5:].strip()
            elif part.startswith("tags="):
                tags = [t.strip() for t in part[5:].split(",")]
            elif part.startswith("layer="):
                try:
                    layer = int(part[6:].strip())
                except ValueError:
                    pass
            elif part.startswith("tile="):
                tile = part[5:].strip()

        if not tile:
            return {
                "error": "No current location and no tile specified. Use --tile=XX00"
            }

        author_id = self._get_current_user_id()

        try:
            wp = self.waypoint_manager.create(
                name=name,
                waypoint_type=wp_type,
                layer=layer,
                tile=tile,
                description=description,
                author_id=author_id,
                tags=tags,
            )

            return {
                "content": f"✅ Created waypoint: {name}\n\nID: {wp.waypoint_id}\nLocation: L{layer}:{tile}\nType: {wp_type.value}",
                "type": "waypoint_new",
                "waypoint_id": wp.waypoint_id,
            }

        except Exception as e:
            logger.error(f"[LOCAL] Waypoint create error: {e}")
            return {"error": str(e)}

    def _handle_show(self, params: str) -> Dict:
        """
        Show waypoint details.

        Usage: WAYPOINT SHOW <id>
        """
        wp_id = params.strip()
        if not wp_id:
            return {"error": "Usage: WAYPOINT SHOW <waypoint_id>"}

        wp = self.waypoint_manager.get(wp_id)

        if not wp:
            # Try search
            results = self.waypoint_manager.search(query=wp_id, limit=1)
            if results:
                wp = results[0]

        if not wp:
            return {"error": f"Waypoint not found: {wp_id}"}

        type_icon = self._type_icon(wp.waypoint_type)
        verified = "✅ Verified" if wp.verified else "❓ Unverified"

        lines = [f"{type_icon} {wp.name}"]
        lines.append("─" * 50)
        lines.append(f"ID: {wp.waypoint_id}")
        lines.append(f"Type: {wp.waypoint_type.value}")
        lines.append(f"Location: L{wp.layer}:{wp.tile}")
        lines.append(f"Layer: {self.waypoint_manager.get_layer_name(wp.layer)}")
        lines.append(f"Status: {verified}")
        lines.append(f"Visibility: {wp.visibility.value}")

        if wp.description:
            lines.append("")
            lines.append(f"Description: {wp.description}")

        if wp.tags:
            lines.append(f"Tags: {', '.join(wp.tags)}")

        if wp.connections:
            lines.append("")
            lines.append(f"Connections ({len(wp.connections)}):")
            for conn in wp.connections:
                layer_name = self.waypoint_manager.get_layer_name(conn.target_layer)
                direction = "↔" if conn.bidirectional else "→"
                lines.append(
                    f"  {direction} L{conn.target_layer}:{conn.target_tile} ({layer_name})"
                )
                if conn.requirements:
                    lines.append(f"      Requires: {', '.join(conn.requirements)}")

        if wp.real_world:
            lines.append("")
            lines.append("Real-world location:")
            if wp.real_world.get("address"):
                lines.append(f"  Address: {wp.real_world['address']}")
            if wp.real_world.get("lat") and wp.real_world.get("lon"):
                lines.append(
                    f"  Coords: {wp.real_world['lat']}, {wp.real_world['lon']}"
                )

        if wp.created:
            lines.append("")
            lines.append(f"Created: {wp.created[:10]}")

        return {"content": "\n".join(lines), "type": "waypoint_show"}

    def _handle_search(self, params: str) -> Dict:
        """
        Search waypoints.

        Usage: WAYPOINT SEARCH <query>
        """
        query = params.strip()
        if not query:
            return {"error": "Usage: WAYPOINT SEARCH <query>"}

        results = self.waypoint_manager.search(query=query, limit=20)

        lines = [f"🔍 Search: '{query}' ({len(results)} results)"]
        lines.append("─" * 50)

        for wp in results:
            type_icon = self._type_icon(wp.waypoint_type)
            layer_name = self.waypoint_manager.get_layer_name(wp.layer)
            lines.append(f"{type_icon} {wp.name}")
            lines.append(f"   L{wp.layer}:{wp.tile} ({layer_name})")
            lines.append(f"   [{wp.waypoint_id}]")

        if not results:
            lines.append("No matching waypoints found.")

        return {"content": "\n".join(lines), "type": "waypoint_search"}

    def _handle_connections(self, params: str) -> Dict:
        """
        Show available connections from current/specified location.

        Usage: WAYPOINT CONNECTIONS [layer:tile]
        """
        if params.strip():
            # Parse layer:tile
            try:
                if ":" in params:
                    layer_str, tile = params.strip().split(":", 1)
                    layer = int(layer_str.lstrip("L"))
                else:
                    layer, tile = self._get_current_location()
            except:
                return {"error": "Invalid format. Use: WAYPOINT CONNECTIONS L300:BD14"}
        else:
            layer, tile = self._get_current_location()

        if not tile:
            return {"error": "No location specified and current location unknown."}

        connections = self.waypoint_manager.get_connections_from(layer, tile)

        lines = [f"🔗 Connections from L{layer}:{tile}"]
        lines.append("─" * 50)

        if connections:
            for wp, conn in connections:
                type_icon = self._type_icon(wp.waypoint_type)
                target_layer_name = self.waypoint_manager.get_layer_name(
                    conn.target_layer
                )
                direction = "↔" if conn.bidirectional else "→"

                lines.append(f"{type_icon} {wp.name}")
                lines.append(f"   {direction} L{conn.target_layer}:{conn.target_tile}")
                lines.append(f"      ({target_layer_name})")
                if conn.requirements:
                    lines.append(f"      ⚠️ Requires: {', '.join(conn.requirements)}")
        else:
            lines.append("No connections available from this location.")

        return {"content": "\n".join(lines), "type": "waypoint_connections"}

    def _handle_layers(self) -> Dict:
        """
        Show universe layer map.

        Usage: WAYPOINT LAYERS
        """
        lines = ["🌌 Universe Layer Map"]
        lines.append("─" * 50)
        lines.append("")
        lines.append("  000-099  SYSTEM     System/meta layers")
        lines.append("  100-199  DUNGEONS   Underground challenges")
        lines.append("  200-299  UNDERGROUND Natural caves, mines")
        lines.append("  300-399  EARTH      Surface (10× zoom each)")
        lines.append("  400-499  ATMOSPHERE  Sky, clouds, aircraft")
        lines.append("  500-599  DIMENSIONS  Alternate realms")
        lines.append("  600-699  NEAR SPACE  Orbit, stations")
        lines.append("  700-799  SOLAR       Planets, moons")
        lines.append("  800-899  GALAXY      Stars, deep space")
        lines.append("")
        lines.append("─" * 50)
        lines.append("Topology: Toroidal (wraps horizontally & vertically)")
        lines.append("Grid: 60×20 tiles per layer (AA10-CH29)")
        lines.append("")
        lines.append("Vertical travel via waypoints (stairs, portals)")
        lines.append("Horizontal travel via walking or teleports")

        return {"content": "\n".join(lines), "type": "waypoint_layers"}

    def _handle_stats(self) -> Dict:
        """
        Show waypoint statistics.

        Usage: WAYPOINT STATS
        """
        stats = self.waypoint_manager.stats()

        lines = ["📊 Waypoint Statistics"]
        lines.append("─" * 50)
        lines.append(f"Total Waypoints: {stats.get('total_waypoints', 0)}")
        lines.append(f"Unique Tiles: {stats.get('unique_tiles', 0)}")
        lines.append(f"Unique Tags: {stats.get('unique_tags', 0)}")
        lines.append(f"Verified: {stats.get('verified_count', 0)}")
        lines.append("")
        lines.append("By Type:")
        for wp_type, count in stats.get("by_type", {}).items():
            lines.append(f"  {wp_type}: {count}")

        return {"content": "\n".join(lines), "type": "waypoint_stats"}

    def _handle_help(self) -> Dict:
        """Show help for waypoint commands."""
        help_text = """📍 WAYPOINT Commands

  WAYPOINT LIST           - List waypoints
  WAYPOINT HERE           - Show at current tile
  WAYPOINT GOTO <id>      - Navigate to waypoint
  WAYPOINT NEW <name>     - Create waypoint
  WAYPOINT SHOW <id>      - Show details
  WAYPOINT SEARCH <q>     - Search waypoints
  WAYPOINT CONNECTIONS    - Show available routes
  WAYPOINT LAYERS         - Show layer map
  WAYPOINT STATS          - Statistics

Creating waypoints:
  WAYPOINT NEW Cave Entrance --type=cave_entrance
  WAYPOINT NEW Launch Site --type=launch_pad --tags=space

Waypoint types:
  stairs_down   - Descend to lower layer
  stairs_up     - Ascend to upper layer
  portal        - Instant vertical teleport
  elevator      - Multi-layer access
  cave_entrance - Surface to underground
  launch_pad    - Surface to space
  poi           - Point of interest
  landmark      - Navigation landmark

Shortcut: WP = WAYPOINT"""

        return {"content": help_text, "type": "waypoint_help"}

    # Helper methods

    def _get_current_user_id(self) -> str:
        """Get current user ID from session."""
        if self.user_manager:
            return getattr(self.user_manager, "user_id", "anonymous")
        return "anonymous"

    def _get_current_location(self) -> tuple:
        """Get current layer and tile from navigation state."""
        # Default to Earth surface layer 300
        # TODO: Get from actual navigation state
        return (300, None)

    def _type_icon(self, wp_type: WaypointType) -> str:
        """Get icon for waypoint type."""
        icons = {
            WaypointType.STAIRS_DOWN: "⬇️",
            WaypointType.STAIRS_UP: "⬆️",
            WaypointType.PORTAL: "🌀",
            WaypointType.ELEVATOR: "🛗",
            WaypointType.CAVE_ENTRANCE: "🕳️",
            WaypointType.LAUNCH_PAD: "🚀",
            WaypointType.POI: "📍",
            WaypointType.LANDMARK: "🏛️",
        }
        return icons.get(wp_type, "📍")
