"""
Desktop Icon Handler for uDOS
Manages desktop icons with Noun Project integration.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from dev.goblin.core.commands.base_handler import BaseCommandHandler
from dev.goblin.core.services.noun_project_service import get_noun_project_service
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("icon-handler")


class IconHandler(BaseCommandHandler):
    """
    Handles ICON commands for desktop icon management.

    Commands:
        ICON SEARCH <query>          - Search Noun Project icons
        ICON DOWNLOAD <id>           - Download icon by ID
        ICON ADD <id> <name> <action> - Add icon to desktop
        ICON LIST                    - List all desktop icons
        ICON CACHE                   - Show cache statistics
        ICON CLEAR                   - Clear icon cache
    """

    def __init__(self):
        super().__init__()
        self.service = get_noun_project_service()
        self.desktop_config_path = Path("memory/udos.md")

    def handle(self, command: str, params: List[str], grid, parser) -> str:
        """Handle ICON commands."""
        if not params:
            return self._show_help()

        subcommand = params[0].upper()

        if subcommand == "SEARCH":
            return self._search_icons(params[1:])
        elif subcommand == "DOWNLOAD":
            return self._download_icon(params[1:])
        elif subcommand == "ADD":
            return self._add_icon(params[1:])
        elif subcommand == "LIST":
            return self._list_icons()
        elif subcommand == "CACHE":
            return self._show_cache_stats()
        elif subcommand == "CLEAR":
            return self._clear_cache(params[1:])
        else:
            return f"❌ Unknown ICON command: {subcommand}\n\n{self._show_help()}"

    def _show_help(self) -> str:
        """Show ICON command help."""
        return """
📱 ICON Commands:

  ICON SEARCH <query>          Search Noun Project for icons
  ICON DOWNLOAD <id>           Download icon by Noun Project ID
  ICON ADD <id> <name> <action> Add icon to desktop
  ICON LIST                    List all desktop icons
  ICON CACHE                   Show cache statistics
  ICON CLEAR [days]            Clear cache (older than N days)

Examples:
  ICON SEARCH document
  ICON DOWNLOAD 12345
  ICON ADD 12345 "Notes" "OPEN memory/notes/"
  ICON CACHE
  ICON CLEAR 30
"""

    def _search_icons(self, params: List[str]) -> str:
        """Search for icons."""
        if not params:
            return "❌ Usage: ICON SEARCH <query>"

        query = " ".join(params)
        logger.info(f"[LOCAL] Searching icons: {query}")

        results = self.service.search_icons(query, limit=10)

        if not results:
            return f"❌ No icons found for '{query}' or API error"

        output = [f"\n🔍 Found {len(results)} icons for '{query}':\n"]

        for i, icon in enumerate(results, 1):
            output.append(f"{i}. ID: {icon['id']}")
            output.append(f"   Term: {icon['term']}")
            output.append(f"   By: {icon.get('uploader', {}).get('name', 'Unknown')}")

            # Check if already cached
            cached = self.service.get_cached_icon(icon["id"])
            if cached:
                output.append(f"   ✅ Cached: {cached}")

            output.append("")

        output.append("💡 Use ICON DOWNLOAD <id> to download an icon")

        return "\n".join(output)

    def _download_icon(self, params: List[str]) -> str:
        """Download icon by ID."""
        if not params:
            return "❌ Usage: ICON DOWNLOAD <id>"

        try:
            icon_id = int(params[0])
        except ValueError:
            return f"❌ Invalid icon ID: {params[0]}"

        logger.info(f"[LOCAL] Downloading icon: {icon_id}")

        path = self.service.download_icon(icon_id, format="svg")

        if path:
            return f"✅ Downloaded icon {icon_id}\n   Path: {path}\n\n💡 Use ICON ADD to add to desktop"
        else:
            return f"❌ Failed to download icon {icon_id}"

    def _add_icon(self, params: List[str]) -> str:
        """Add icon to desktop configuration."""
        if len(params) < 3:
            return "❌ Usage: ICON ADD <id> <name> <action> [params]"

        try:
            icon_id = int(params[0])
        except ValueError:
            return f"❌ Invalid icon ID: {params[0]}"

        name = params[1].strip("\"'")
        action = params[2].strip("\"'")
        action_params = " ".join(params[3:]).strip("\"'") if len(params) > 3 else ""

        # Check if icon is cached
        cached = self.service.get_cached_icon(icon_id)
        if not cached:
            # Try to download it
            cached = self.service.download_icon(icon_id, format="svg")
            if not cached:
                return f"❌ Icon {icon_id} not found. Try ICON SEARCH first."

        # Add to desktop config
        icon_entry = f"- 🖼️ {name} | {action} | {action_params} | noun:{icon_id}\n"

        try:
            # Read existing config
            if not self.desktop_config_path.exists():
                self.desktop_config_path.write_text("# uDOS Desktop\n\n")

            content = self.desktop_config_path.read_text()

            # Find desktop icons section or create it
            if "## Desktop Icons" not in content:
                content += "\n## Desktop Icons\n\n"

            # Add icon entry
            content += icon_entry

            self.desktop_config_path.write_text(content)

            logger.info(f"[LOCAL] Added icon {icon_id} to desktop: {name}")
            return f"✅ Added icon to desktop\n   Name: {name}\n   Action: {action}\n   Icon ID: {icon_id}"

        except Exception as e:
            logger.error(f"[LOCAL] Failed to add icon: {e}")
            return f"❌ Failed to add icon: {e}"

    def _list_icons(self) -> str:
        """List all desktop icons."""
        if not self.desktop_config_path.exists():
            return "❌ No desktop configuration found at memory/udos.md"

        try:
            content = self.desktop_config_path.read_text()
            lines = content.split("\n")

            icons = []
            in_icons_section = False

            for line in lines:
                if line.strip() == "## Desktop Icons":
                    in_icons_section = True
                    continue
                elif line.startswith("##") and in_icons_section:
                    break
                elif in_icons_section and line.strip().startswith("-"):
                    icons.append(line.strip())

            if not icons:
                return "ℹ️ No desktop icons configured"

            output = ["\n📱 Desktop Icons:\n"]
            for i, icon_line in enumerate(icons, 1):
                output.append(f"{i}. {icon_line}")

            return "\n".join(output)

        except Exception as e:
            logger.error(f"[LOCAL] Failed to list icons: {e}")
            return f"❌ Failed to list icons: {e}"

    def _show_cache_stats(self) -> str:
        """Show cache statistics."""
        stats = self.service.get_cache_stats()

        return f"""
📊 Icon Cache Statistics:

  Cached Icons: {stats['cached_icons']}
  Cached Searches: {stats['cached_searches']}
  Total Size: {stats['total_size_mb']} MB
  Cache Directory: {stats['cache_dir']}
"""

    def _clear_cache(self, params: List[str]) -> str:
        """Clear icon cache."""
        older_than_days = None

        if params:
            try:
                older_than_days = int(params[0])
            except ValueError:
                return f"❌ Invalid number of days: {params[0]}"

        try:
            self.service.clear_cache(older_than_days)

            if older_than_days:
                return f"✅ Cleared cache (older than {older_than_days} days)"
            else:
                return "✅ Cache cleared"

        except Exception as e:
            logger.error(f"[LOCAL] Failed to clear cache: {e}")
            return f"❌ Failed to clear cache: {e}"


def create_handler():
    """Factory function for handler creation."""
    return IconHandler()
