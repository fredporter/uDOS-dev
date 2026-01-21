"""
Overlay Handler - Commands for managing knowledge overlays.

Handles OVERLAY commands for creating, listing, and applying
custom knowledge filters.

Part of uDOS Alpha v1.0.0.53+
"""

from typing import Dict, List, Optional, Any

from dev.goblin.core.commands.base_handler import BaseCommandHandler
from dev.goblin.core.services.logging_manager import get_logger
from dev.goblin.core.services.overlay_manager import get_overlay_manager, OverlayType

logger = get_logger("command-overlay")


class OverlayHandler(BaseCommandHandler):
    """
    Handles overlay management commands.

    Commands:
        OVERLAY LIST           - List available overlays
        OVERLAY NEW <name>     - Create new overlay
        OVERLAY EDIT <name>    - Edit overlay filters
        OVERLAY DELETE <name>  - Delete user overlay
        OVERLAY APPLY <name>   - Apply overlay (same as @name)
        OVERLAY SHOW <name>    - Show overlay details
    """

    def __init__(self, **kwargs):
        """Initialize overlay handler."""
        super().__init__(**kwargs)
        self._overlay_manager = None

    @property
    def overlay_manager(self):
        """Lazy-load overlay manager."""
        if self._overlay_manager is None:
            self._overlay_manager = get_overlay_manager()
        return self._overlay_manager

    def handle(self, command: str, params: str, grid=None, parser=None) -> Dict:
        """
        Route overlay commands.

        Args:
            command: Command name (OVERLAY)
            params: Command parameters
            grid: Display grid
            parser: Command parser

        Returns:
            Result dict with content or error
        """
        logger.info(f"[LOCAL] Overlay command: {command} {params}")

        # Parse subcommand
        parts = params.strip().split(None, 1)
        subcommand = parts[0].upper() if parts else ""
        sub_params = parts[1] if len(parts) > 1 else ""

        # Route subcommands
        if subcommand == "LIST" or subcommand == "L":
            return self._handle_list(sub_params)
        elif subcommand == "NEW" or subcommand == "N" or subcommand == "CREATE":
            return self._handle_new(sub_params)
        elif subcommand == "EDIT" or subcommand == "E":
            return self._handle_edit(sub_params)
        elif subcommand == "DELETE" or subcommand == "D" or subcommand == "REMOVE":
            return self._handle_delete(sub_params)
        elif subcommand == "APPLY" or subcommand == "A":
            return self._handle_apply(sub_params)
        elif subcommand == "SHOW" or subcommand == "S":
            return self._handle_show(sub_params)
        elif subcommand == "HELP" or subcommand == "?":
            return self._handle_help()
        elif params.strip():
            # Default: show overlay
            return self._handle_show(params)
        else:
            return self._handle_help()

    def _handle_list(self, params: str) -> Dict:
        """
        List available overlays.

        Usage: OVERLAY LIST [--user|--system|--all]
        """
        include_system = True
        user_id = self._get_current_user_id()

        if "--user" in params:
            include_system = False

        overlays = self.overlay_manager.list(
            user_id=user_id, include_system=include_system
        )

        lines = ["🎭 Available Overlays"]
        lines.append("─" * 50)

        # Group by type
        system_overlays = [o for o in overlays if o.overlay_type == OverlayType.SYSTEM]
        user_overlays = [o for o in overlays if o.overlay_type == OverlayType.USER]

        if system_overlays and include_system:
            lines.append("")
            lines.append("System Overlays:")
            for overlay in system_overlays:
                lines.append(f"  {overlay.name:15} - {overlay.description[:40]}")

        if user_overlays:
            lines.append("")
            lines.append("Your Overlays:")
            for overlay in user_overlays:
                lines.append(f"  {overlay.name:15} - {overlay.description[:40]}")

        if not overlays:
            lines.append("No overlays found.")

        lines.append("")
        lines.append("─" * 50)
        lines.append("Use OVERLAY SHOW <name> for details")
        lines.append("Use KNOWLEDGE LIST @name to apply overlay")

        return {"content": "\n".join(lines), "type": "overlay_list"}

    def _handle_new(self, params: str) -> Dict:
        """
        Create a new user overlay.

        Usage: OVERLAY NEW <name> [--desc=description] [--tags=t1,t2] [--quality=min]
        """
        if not params.strip():
            return {
                "error": "Usage: OVERLAY NEW <name> [--desc=...] [--tags=...] [--quality=...]"
            }

        # Parse parameters
        parts = params.split("--")
        name = parts[0].strip()

        if not name:
            return {"error": "Overlay name is required"}

        if name.startswith("@"):
            return {"error": "User overlay names cannot start with @"}

        description = ""
        filters = {}

        for part in parts[1:]:
            if part.startswith("desc="):
                description = part[5:].strip()
            elif part.startswith("tags="):
                filters["include_tags"] = [t.strip() for t in part[5:].split(",")]
            elif part.startswith("exclude-tags="):
                filters["exclude_tags"] = [t.strip() for t in part[13:].split(",")]
            elif part.startswith("quality="):
                try:
                    filters["min_quality"] = float(part[8:].strip())
                except ValueError:
                    pass
            elif part.startswith("category=") or part.startswith("cat="):
                cat_val = part.split("=", 1)[1].strip()
                filters["include_categories"] = [cat_val]
            elif part.startswith("verified"):
                filters["verified_only"] = True

        user_id = self._get_current_user_id()

        try:
            overlay = self.overlay_manager.create(
                name=name, user_id=user_id, description=description, filters=filters
            )

            return {
                "content": f"✅ Created overlay: {name}\n\nUse KNOWLEDGE LIST @{name} to apply it.",
                "type": "overlay_new",
            }

        except Exception as e:
            logger.error(f"[LOCAL] Overlay create error: {e}")
            return {"error": str(e)}

    def _handle_edit(self, params: str) -> Dict:
        """
        Edit an existing overlay.

        Usage: OVERLAY EDIT <name> --tags=... --quality=...
        """
        if not params.strip():
            return {"error": "Usage: OVERLAY EDIT <name> [--tags=...] [--quality=...]"}

        parts = params.split("--")
        name = parts[0].strip()

        if not name:
            return {"error": "Overlay name is required"}

        updates = {}

        for part in parts[1:]:
            if part.startswith("desc="):
                updates["description"] = part[5:].strip()
            elif part.startswith("tags="):
                if "filters" not in updates:
                    updates["filters"] = {}
                updates["filters"]["include_tags"] = [
                    t.strip() for t in part[5:].split(",")
                ]
            elif part.startswith("quality="):
                if "filters" not in updates:
                    updates["filters"] = {}
                try:
                    updates["filters"]["min_quality"] = float(part[8:].strip())
                except ValueError:
                    pass

        if not updates:
            return {"error": "No updates specified"}

        user_id = self._get_current_user_id()

        try:
            overlay = self.overlay_manager.update(name, user_id, **updates)
            return {"content": f"✅ Updated overlay: {name}", "type": "overlay_edit"}
        except Exception as e:
            logger.error(f"[LOCAL] Overlay edit error: {e}")
            return {"error": str(e)}

    def _handle_delete(self, params: str) -> Dict:
        """
        Delete a user overlay.

        Usage: OVERLAY DELETE <name>
        """
        name = params.strip()
        if not name:
            return {"error": "Usage: OVERLAY DELETE <name>"}

        user_id = self._get_current_user_id()

        try:
            self.overlay_manager.delete(name, user_id)
            return {"content": f"✅ Deleted overlay: {name}", "type": "overlay_delete"}
        except Exception as e:
            logger.error(f"[LOCAL] Overlay delete error: {e}")
            return {"error": str(e)}

    def _handle_show(self, params: str) -> Dict:
        """
        Show overlay details.

        Usage: OVERLAY SHOW <name>
        """
        name = params.strip()
        if not name:
            return {"error": "Usage: OVERLAY SHOW <name>"}

        overlay = self.overlay_manager.get(name)
        if not overlay:
            return {"error": f"Overlay not found: {name}"}

        lines = [f"🎭 Overlay: {overlay.name}"]
        lines.append("─" * 50)
        lines.append(f"Type: {overlay.overlay_type.value}")
        lines.append(f"Description: {overlay.description or '(none)'}")
        lines.append("")
        lines.append("Filters:")

        f = overlay.filters
        if f.include_tags:
            lines.append(f"  Include tags: {', '.join(f.include_tags)}")
        if f.exclude_tags:
            lines.append(f"  Exclude tags: {', '.join(f.exclude_tags)}")
        if f.include_categories:
            lines.append(f"  Include categories: {', '.join(f.include_categories)}")
        if f.exclude_categories:
            lines.append(f"  Exclude categories: {', '.join(f.exclude_categories)}")
        if f.min_quality > 0:
            lines.append(f"  Min quality: {f.min_quality}")
        if f.verified_only:
            lines.append("  Verified only: yes")
        if f.statuses != ["published"]:
            lines.append(f"  Statuses: {', '.join(f.statuses)}")

        lines.append("")
        lines.append(f"Sort: {overlay.sort_by} ({overlay.sort_order})")
        lines.append(f"Limit: {overlay.limit}")

        if overlay.created:
            lines.append(f"Created: {overlay.created[:10]}")

        lines.append("")
        lines.append("─" * 50)
        lines.append(f"Apply with: KNOWLEDGE LIST {name}")

        return {"content": "\n".join(lines), "type": "overlay_show"}

    def _handle_apply(self, params: str) -> Dict:
        """
        Apply overlay and show results (redirect to KNOWLEDGE LIST).

        Usage: OVERLAY APPLY <name>
        """
        name = params.strip()
        if not name:
            return {"error": "Usage: OVERLAY APPLY <name>"}

        # Note: Knowledge handler deprecated - overlay apply not currently functional
        # TODO: Implement overlay apply without knowledge_handler dependency
        return {
            "message": f"🎭 Overlay '{name}' marked for apply",
            "note": "Overlay apply feature under development",
            "suggestion": "Use GUIDE or GUIDE AI for knowledge access",
        }

    def _handle_help(self) -> Dict:
        """Show help for overlay commands."""
        help_text = """🎭 OVERLAY Commands

  OVERLAY LIST             - List all overlays
  OVERLAY NEW <name>       - Create overlay
  OVERLAY EDIT <name>      - Edit overlay
  OVERLAY DELETE <name>    - Delete overlay
  OVERLAY SHOW <name>      - Show overlay details
  OVERLAY APPLY <name>     - Apply overlay

Creating overlays:
  OVERLAY NEW survival --desc=Survival skills --tags=survival,wilderness
  OVERLAY NEW medical --tags=medical,first-aid --quality=5
  OVERLAY NEW verified-only --verified

System overlays (built-in):
  @all        - All published docs
  @personal   - Your documents
  @drafts     - Your drafts
  @nearby     - Location-linked
  @emergency  - Emergency docs
  @verified   - Expert-verified
  @high-quality - Quality 7+

Note: User overlays cannot start with @"""

        return {"content": help_text, "type": "overlay_help"}

    def _get_current_user_id(self) -> str:
        """Get current user ID from session."""
        if self.user_manager:
            return getattr(self.user_manager, "user_id", "anonymous")
        return "anonymous"
