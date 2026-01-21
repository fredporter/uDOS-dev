"""
FeedHandler - Command handler for FEED system

Handles FEED commands in the TUI:
- FEED [TICKER|SCROLL|PANEL] - Start display mode
- FEED ADD <content> - Add item to feed
- FEED ALERT <content> - Add alert
- FEED PAUSE/RESUME - Control playback
- FEED STOP - Stop display
- FEED SPEED <speed> - Set speed
- FEED STATUS - Show status
- FEED EXPORT [json|rss] - Export feed
"""

from typing import Dict, Any, Optional, List, Tuple
from dev.goblin.core.commands.base_handler import BaseCommandHandler


class FeedHandler(BaseCommandHandler):
    """
    Handler for FEED commands.

    The FEED system provides real-time data feeds displayed as
    ticker (single-line scroll) or scroll (typed page) output.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._feed_manager = None
        self._display_callback = None

    @property
    def feed_manager(self):
        """Lazy load feed manager"""
        if self._feed_manager is None:
            from dev.goblin.core.services.feed import get_feed_manager

            self._feed_manager = get_feed_manager()
        return self._feed_manager

    def set_display_callback(self, callback) -> None:
        """Set callback for display updates (used by TUI)"""
        self._display_callback = callback

    def handle(
        self, command: str, params: str, grid=None, parser=None
    ) -> Dict[str, Any]:
        """Route FEED commands"""
        command = command.upper()
        params = params.strip() if params else ""

        # Parse subcommand
        parts = params.split(None, 1)
        subcommand = parts[0].upper() if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        handlers = {
            "": self._show_feed,
            "TICKER": self._start_ticker,
            "SCROLL": self._start_scroll,
            "PANEL": self._show_panel,
            "ADD": self._add_item,
            "ALERT": self._add_alert,
            "LOG": self._add_log,
            "PAUSE": self._pause,
            "RESUME": self._resume,
            "STOP": self._stop,
            "SPEED": self._set_speed,
            "STATUS": self._show_status,
            "SOURCES": self._show_sources,
            "ENABLE": self._enable_source,
            "DISABLE": self._disable_source,
            "FILTER": self._set_filter,
            "CLEAR": self._clear_filter,
            "EXPORT": self._export,
            "HELP": self._show_help,
        }

        handler = handlers.get(subcommand, self._unknown_command)
        return handler(args)

    def set_display_callback(self, callback) -> None:
        """Set callback for display updates (used by TUI)"""
        self._display_callback = callback

    def _show_feed(self, args: str) -> Dict[str, Any]:
        """Show current feed items"""
        items = self.feed_manager.get_items(limit=20)

        if not items:
            return {
                "success": True,
                "output": "📰 Feed is empty. Add items with FEED ADD <content>",
                "type": "feed",
            }

        lines = ["📰 FEED - Current Items", ""]
        for item in items:
            lines.append(f"  {item.ticker_text}")

        lines.append("")
        lines.append(f"  {len(items)} items | FEED TICKER to start display")

        return {
            "success": True,
            "output": "\n".join(lines),
            "type": "feed",
            "items": [item.to_dict() for item in items],
        }

    def _start_ticker(self, args: str) -> Dict[str, Any]:
        """Start ticker display mode"""
        speed = args.lower() if args else "medium"

        # Get the feed text
        text = self.feed_manager.get_feed_text(limit=15)

        if not text:
            return {"success": False, "error": "Feed is empty. Add items first."}

        # Start ticker with callback if available
        self.feed_manager.start_ticker(callback=self._display_callback, speed=speed)

        return {
            "success": True,
            "output": f"▶ Ticker started (speed: {speed})",
            "type": "feed_ticker",
            "mode": "ticker",
            "speed": speed,
            "text": text,
        }

    def _start_scroll(self, args: str) -> Dict[str, Any]:
        """Start scroll display mode"""
        speed = args.lower() if args else "medium"

        lines = self.feed_manager.get_feed_lines(limit=30)

        if not lines:
            return {"success": False, "error": "Feed is empty. Add items first."}

        self.feed_manager.start_scroll(
            callback=self._display_callback, speed=speed, loop=True
        )

        return {
            "success": True,
            "output": f"📜 Scroll started (speed: {speed})",
            "type": "feed_scroll",
            "mode": "scroll",
            "speed": speed,
            "lines": lines,
        }

    def _show_panel(self, args: str) -> Dict[str, Any]:
        """Show panel display"""
        items = self.feed_manager.get_items(limit=5)

        if not items:
            return {"success": False, "error": "Feed is empty"}

        panel_lines = self.feed_manager.renderer.render_panel(items, panel_height=7)

        return {
            "success": True,
            "output": "\n".join(panel_lines),
            "type": "feed_panel",
            "items": [item.to_dict() for item in items],
        }

    def _add_item(self, args: str) -> Dict[str, Any]:
        """Add custom item to feed"""
        if not args:
            return {"success": False, "error": "Usage: FEED ADD <content>"}

        item = self.feed_manager.add_item(args)

        return {
            "success": True,
            "output": f"✓ Added to feed: {item.ticker_text}",
            "item": item.to_dict(),
        }

    def _add_alert(self, args: str) -> Dict[str, Any]:
        """Add alert to feed"""
        if not args:
            return {"success": False, "error": "Usage: FEED ALERT <message>"}

        item = self.feed_manager.alert(args)

        return {
            "success": True,
            "output": f"⚠ Alert added: {args}",
            "item": item.to_dict(),
        }

    def _add_log(self, args: str) -> Dict[str, Any]:
        """Add log entry to feed"""
        if not args:
            return {"success": False, "error": "Usage: FEED LOG <message>"}

        # Parse optional level
        parts = args.split(None, 1)
        if len(parts) > 1 and parts[0].upper() in ["ERROR", "WARN", "INFO", "DEBUG"]:
            level = parts[0].upper()
            message = parts[1]
        else:
            level = "INFO"
            message = args

        item = self.feed_manager.log(message, level)

        return {
            "success": True,
            "output": f"📋 Log added: [{level}] {message}",
            "item": item.to_dict(),
        }

    def _pause(self, args: str) -> Dict[str, Any]:
        """Pause display"""
        self.feed_manager.pause_display()
        return {"success": True, "output": "⏸ Feed paused"}

    def _resume(self, args: str) -> Dict[str, Any]:
        """Resume display"""
        self.feed_manager.resume_display()
        return {"success": True, "output": "▶ Feed resumed"}

    def _stop(self, args: str) -> Dict[str, Any]:
        """Stop display"""
        self.feed_manager.stop_display()
        return {"success": True, "output": "⏹ Feed stopped"}

    def _set_speed(self, args: str) -> Dict[str, Any]:
        """Set display speed"""
        if not args:
            return {
                "success": False,
                "error": "Usage: FEED SPEED <very_slow|slow|medium|fast|very_fast>",
            }

        if self.feed_manager.set_speed(args):
            return {"success": True, "output": f"⚡ Speed set to: {args}"}
        else:
            return {
                "success": False,
                "error": f"Unknown speed: {args}. Use: very_slow, slow, medium, fast, very_fast",
            }

    def _show_status(self, args: str) -> Dict[str, Any]:
        """Show feed system status"""
        status = self.feed_manager.get_status()

        lines = ["📊 FEED Status", ""]

        # Polling
        poll_state = "Running" if status["polling"] else "Stopped"
        lines.append(f"  Polling: {poll_state} (every {status['poll_interval']}s)")

        # Renderer
        renderer = status["renderer"]
        lines.append(f"  Display: {renderer['mode']} | Speed: {renderer['speed']:.3f}s")
        lines.append(f"  Running: {renderer['running']} | Paused: {renderer['paused']}")

        # Compiler stats
        compiler = status["compiler"]
        lines.append(
            f"  Items: {compiler['active_items']} active, {compiler['history_items']} history"
        )

        # Sources
        lines.append("")
        lines.append("  Sources:")
        for name, source in status["sources"].items():
            state = "✓" if source["enabled"] else "✗"
            lines.append(f"    {state} {name} ({source['poll_interval']}s)")

        return {"success": True, "output": "\n".join(lines), "status": status}

    def _show_sources(self, args: str) -> Dict[str, Any]:
        """Show registered sources"""
        sources = self.feed_manager.sources

        lines = ["📡 Feed Sources", ""]
        for name, source in sources.items():
            state = "enabled" if source.enabled else "disabled"
            lines.append(f"  • {name} [{state}] - poll: {source.poll_interval}s")

        return {"success": True, "output": "\n".join(lines)}

    def _enable_source(self, args: str) -> Dict[str, Any]:
        """Enable a source"""
        if not args:
            return {"success": False, "error": "Usage: FEED ENABLE <source>"}

        if self.feed_manager.enable_source(args):
            return {"success": True, "output": f"✓ Source enabled: {args}"}
        else:
            return {"success": False, "error": f"Unknown source: {args}"}

    def _disable_source(self, args: str) -> Dict[str, Any]:
        """Disable a source"""
        if not args:
            return {"success": False, "error": "Usage: FEED DISABLE <source>"}

        if self.feed_manager.disable_source(args):
            return {"success": True, "output": f"✗ Source disabled: {args}"}
        else:
            return {"success": False, "error": f"Unknown source: {args}"}

    def _set_filter(self, args: str) -> Dict[str, Any]:
        """Set feed filter"""
        if not args:
            return {
                "success": False,
                "error": "Usage: FEED FILTER <type|priority> <value>",
            }

        parts = args.split()
        if len(parts) < 2:
            return {
                "success": False,
                "error": "Usage: FEED FILTER type alert,log | FEED FILTER priority 2",
            }

        filter_type = parts[0].lower()
        filter_value = parts[1]

        if filter_type == "type":
            types = filter_value.split(",")
            self.feed_manager.filter_by_type(types)
            return {
                "success": True,
                "output": f"🔍 Filtering by types: {', '.join(types)}",
            }
        elif filter_type == "priority":
            try:
                priority = int(filter_value)
                self.feed_manager.filter_by_priority(priority)
                return {
                    "success": True,
                    "output": f"🔍 Filtering by priority ≤ {priority}",
                }
            except ValueError:
                return {"success": False, "error": "Priority must be a number 1-5"}
        else:
            return {"success": False, "error": f"Unknown filter type: {filter_type}"}

    def _clear_filter(self, args: str) -> Dict[str, Any]:
        """Clear all filters"""
        self.feed_manager.clear_filters()
        return {"success": True, "output": "🔍 Filters cleared"}

    def _export(self, args: str) -> Dict[str, Any]:
        """Export feed in various formats"""
        format_type = args.lower() if args else "json"

        if format_type == "json":
            output = self.feed_manager.get_feed_json()
            return {"success": True, "output": output, "format": "json"}
        elif format_type == "rss":
            output = self.feed_manager.get_feed_rss()
            return {"success": True, "output": output, "format": "rss"}
        elif format_type == "text":
            output = self.feed_manager.get_feed_text()
            return {"success": True, "output": output, "format": "text"}
        else:
            return {
                "success": False,
                "error": f"Unknown format: {format_type}. Use: json, rss, text",
            }

    def _show_help(self, args: str) -> Dict[str, Any]:
        """Show help for FEED commands"""
        help_text = """📰 FEED Command Help

Display Modes:
  FEED              Show current feed items
  FEED TICKER [speed]   Start ticker (single line scroll)
  FEED SCROLL [speed]   Start scroll (page with typed effect)
  FEED PANEL        Show panel with rotating items

Content:
  FEED ADD <text>   Add custom item to feed
  FEED ALERT <msg>  Add high-priority alert
  FEED LOG <msg>    Add log entry

Control:
  FEED PAUSE        Pause display
  FEED RESUME       Resume display
  FEED STOP         Stop display
  FEED SPEED <spd>  Set speed (very_slow|slow|medium|fast|very_fast)

Sources:
  FEED SOURCES      List registered sources
  FEED ENABLE <src> Enable a source
  FEED DISABLE <src> Disable a source

Filtering:
  FEED FILTER type alert,log   Filter by type
  FEED FILTER priority 2       Filter by priority
  FEED CLEAR                   Clear filters

Export:
  FEED EXPORT json  Export as JSON
  FEED EXPORT rss   Export as RSS XML
  FEED EXPORT text  Export as plain text

Status:
  FEED STATUS       Show feed system status"""

        return {"success": True, "output": help_text}

    def _unknown_command(self, args: str) -> Dict[str, Any]:
        """Handle unknown subcommand"""
        return {
            "success": False,
            "error": f"Unknown FEED command. Type FEED HELP for available commands.",
        }
