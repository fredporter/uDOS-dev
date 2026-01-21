"""
uDOS v1.3.3 - Dashboard Handler

Handles dashboard, status, and system information display:
- System status monitoring
- Dashboard creation (CLI and web)
- Viewport and palette information
- Live status monitoring
- Multi-role dashboard views (v1.3.3)
- Unified configuration via ConfigManager (v1.5.0+)
"""

import os
import sys
import json
import time
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional
from .base_handler import BaseCommandHandler
from dev.goblin.core.uDOS_main import get_config  # v1.5.0 Unified configuration

# v1.3.3 - Role-based dashboard service
try:
    from dev.goblin.core.services.dashboard_service import (
        DashboardService,
        DashboardType,
        RoleLevel,
        DashboardConfig,
        get_dashboard_service,
        init_dashboard_service,
    )

    DASHBOARD_SERVICE_AVAILABLE = True
except ImportError:
    DASHBOARD_SERVICE_AVAILABLE = False


class DashboardHandler(BaseCommandHandler):
    """Handles dashboard, status, and system information operations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _emoji_visual_len(self, text):
        """Calculate visual length of text accounting for emoji (2 chars each)."""
        import re

        # Count emojis - comprehensive pattern covering most emoji blocks
        # U+1F300-1F9FF: Emoticons, symbols, transport, pictographs
        # U+2600-27BF: Miscellaneous symbols (⚠️, ✅, etc.)
        # U+2700-27BF: Dingbats
        emoji_pattern = (
            r"[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U00002700-\U000027BF]"
        )
        emoji_count = len(re.findall(emoji_pattern, text))

        # Variation selectors don't add visual width - emoji+VS = 2 chars, 2 cols
        variation_selectors = len(re.findall(r"[\uFE00-\uFE0F]", text))

        # Visual width: string + (emoji add 1 col) - (VS take char but no visual width)
        return len(text) + emoji_count - variation_selectors

    def _center_text(self, text, width):
        """Center text in a box accounting for emoji visual width."""
        visual_len = self._emoji_visual_len(text)
        padding_total = width - visual_len
        if padding_total < 0:
            return text[:width]  # Truncate if too long
        left_pad = padding_total // 2
        right_pad = padding_total - left_pad
        return (" " * left_pad) + text + (" " * right_pad)

    def _ljust_emoji(self, text, width):
        """Left-justify text accounting for emoji visual width."""
        visual_len = self._emoji_visual_len(text)
        padding = width - visual_len
        if padding < 0:
            return text[:width]
        return text + (" " * padding)

    def _box_line(self, content, width=78):
        """Create a box line with proper padding accounting for emoji visual width."""
        # Emoji display as 2 columns but count as 1 char, so we need less padding
        visual_len = self._emoji_visual_len(content)
        padding = width - visual_len
        if padding < 0:
            # Content too long, truncate
            content = content[:width]
            padding = 0
        return "║" + content + (" " * padding) + "║\n"

    def _load_workflow_state(self):
        """Load current workflow state from memory/workflows/state/current.json."""
        try:
            state_file = PATHS.WORKFLOW_STATE
            if state_file.exists():
                with open(state_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def _get_mission_emoji(self, status):
        """Get emoji for mission status."""
        emoji_map = {
            "DRAFT": "📝",
            "ACTIVE": "⚡",
            "PAUSED": "⏸️",
            "COMPLETED": "✅",
            "FAILED": "❌",
            "ARCHIVED": "📦",
            "IDLE": "💤",
        }
        return emoji_map.get(status.upper(), "❓")

    def _format_elapsed_time(self, seconds):
        """Format elapsed time in human-readable format."""
        if not seconds or seconds == 0:
            return "00:00:00"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _build_lifecycle_bar(self, steps, current_step):
        """Build visual lifecycle progress bar."""
        # Find current step index
        try:
            current_idx = steps.index(current_step)
        except ValueError:
            current_idx = -1

        bar = ""
        for i, step in enumerate(steps):
            if i < current_idx:
                bar += "✅ "  # Completed
            elif i == current_idx:
                bar += "⚡ "  # Current
            else:
                bar += "⭕ "  # Pending

            # Add step name (abbreviated)
            bar += step[:3] + " "

        return bar.strip()

    def _build_font_demo_section(self, config):
        """
        Build font rendering demo section for selected fonts only.

        Shows 4 available font families with rendering examples:
        - chicago: Classic Macintosh System font
        - mallard: BBC Teletext rendering font
        - petme: Commodore PET/CBM font family
        - mode7: BBC Micro Mode 7 Teletext font

        User's selected font is highlighted with ✓ marker.

        Args:
            config: Configuration instance with user preferences

        Returns:
            Formatted string with font demos
        """
        output = ""

        # Get user's selected font from user.json (system_settings.ui.primary_font)
        try:
            user_font = config.get_user(
                "system_settings.ui.primary_font", "chicago"
            ).lower()
        except:
            user_font = "chicago"

        # Define the 4 core font families with rendering demos
        # Include variant names for better matching
        fonts = {
            "chicago": {
                "name": "Chicago",
                "desc": "Classic Macintosh System font",
                "demo": "ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789",
                "variants": ["chicago", "chicagoflf"],
            },
            "mallard": {
                "name": "Mallard",
                "desc": "BBC Teletext rendering font",
                "demo": "ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789",
                "variants": ["mallard", "teletext", "mode7", "blocky", "smooth"],
            },
            "petme": {
                "name": "PetMe",
                "desc": "Commodore PET/CBM font family",
                "demo": "ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789",
                "variants": ["petme", "petme64", "petme128", "petme2x", "petme2y"],
            },
            "mode7": {
                "name": "MODE7GX3",
                "desc": "BBC Micro Mode 7 Teletext font",
                "demo": "ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789",
                "variants": ["mode7gx3", "mode7"],
            },
        }

        # Render each font with demo
        for font_key, font_info in fonts.items():
            # Check if this is the user's selected font or variant
            selected = False
            for variant in font_info["variants"]:
                if variant in user_font.lower():
                    selected = True
                    break

            marker = "✓" if selected else " "

            # Font name line with selection marker
            font_line = f"  {marker} {font_info['name']} - {font_info['desc']}"
            output += self._box_line(font_line)

            # Demo text (first line - uppercase + digits)
            demo_line = f"    {font_info['demo'][:70]}"
            output += self._box_line(demo_line)

            # Demo text (second line - lowercase + symbols)
            demo_line2 = "    abcdefghijklmnopqrstuvwxyz !@#$%^&*()"
            output += self._box_line(demo_line2)

            # Add spacing between fonts (except after last one)
            if list(fonts.keys()).index(font_key) < len(fonts) - 1:
                output += self._box_line("")

        # Footer hint showing current selection
        output += self._box_line("")
        current_font_display = (
            user_font if len(user_font) < 20 else user_font[:17] + "..."
        )
        output += self._box_line(f"  Current: {current_font_display}")
        output += self._box_line(
            "  💡 Change: CONFIG SET system_settings.ui.primary_font <font>"
        )

        return output

    def _build_system_inventory_section(self):
        """
        Build system inventory section showing handler/service/knowledge counts.

        Returns:
            Formatted string with inventory metrics
        """
        output = ""

        try:
            # Count handlers
            handlers_path = Path(__file__).parent
            handler_count = len(list(handlers_path.glob("*_handler.py")))

            # Count services
            services_path = Path(__file__).parent.parent / "services"
            service_count = (
                len(list(services_path.glob("*.py"))) if services_path.exists() else 0
            )

            # Count knowledge articles
            knowledge_path = Path(__file__).parent.parent.parent / "knowledge"
            knowledge_count = (
                len(list(knowledge_path.rglob("*.md")))
                if knowledge_path.exists()
                else 0
            )

            # Count library clones (ucode + wizard)
            library_path = Path(__file__).parent.parent.parent / "library"
            library_clones = (
                len(
                    [
                        d
                        for d in (library_path / "ucode").iterdir()
                        if d.is_dir() and d.name != ".gitkeep"
                    ]
                )
                + len(
                    [
                        d
                        for d in (library_path / "wizard").iterdir()
                        if d.is_dir() and d.name != ".gitkeep"
                    ]
                )
                if library_path.exists()
                else 0
            )

            # Count wiki articles
            wiki_path = Path(__file__).parent.parent.parent / "wiki"
            wiki_count = len(list(wiki_path.rglob("*.md"))) if wiki_path.exists() else 0

            # Build output
            output += self._box_line(
                f"  Handlers: {handler_count:3d}    Services: {service_count:3d}    Wiki: {wiki_count:3d}"
            )
            output += self._box_line(
                f"  Knowledge Bank: {knowledge_count:3d} articles    Library: {library_clones:2d} clones"
            )

            # Get version info
            try:
                from dev.goblin.core.version import get_core_version, get_all_versions

                versions = get_all_versions()
                core_ver = versions.get("core", "unknown")
                api_ver = versions.get("api", "unknown")
                app_ver = versions.get("app", "unknown")
                output += self._box_line(
                    f"  Versions: Core {core_ver} | API {api_ver} | App {app_ver}"
                )
            except Exception:
                output += self._box_line("  Versions: Unable to retrieve")

        except Exception as e:
            output += self._box_line(
                f"  Inventory: Unable to calculate ({str(e)[:40]})"
            )

        return output

    def handle_status(self, params, grid, parser):
        """
        Display comprehensive system status.
        Supports --live flag for real-time monitoring.

        Args:
            params: Optional parameters including --live flag
            grid: Grid instance (unused)
            parser: Parser instance (unused)

        Returns:
            System status display
        """
        # Check for --live flag
        live_mode = params and ("--live" in params or "LIVE" in params)

        if live_mode:
            return self._status_live_mode()
        else:
            return self._status_snapshot()

    def _status_snapshot(self):
        """Display a single snapshot of system status with enhanced ASCII dashboard."""
        # Get configuration
        config = get_config()

        # Load workflow state
        workflow_state = self._load_workflow_state()

        # Build comprehensive dashboard
        status = "╔" + "═" * 78 + "╗\n"
        status += "║" + self._center_text("📊 uDOS SYSTEM DASHBOARD", 78) + "║\n"
        status += "╠" + "═" * 78 + "╣\n"

        # User & Location Information
        status += "║ " + self._ljust_emoji("👤 USER PROFILE", 77) + "║\n"
        status += "║ " + "─" * 77 + "║\n"

        username = config.username or "user"
        location = config.location or "Unknown"
        timezone = config.timezone or "UTC"

        # Get current time
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%Y-%m-%d")

        # Get planet/galaxy info from config or defaults
        # Planet/Galaxy are cosmetic user preferences (not functional workspaces)
        planet = config.get("planet", "Earth")
        galaxy = config.get("galaxy", "Milky Way")

        status += self._box_line(
            f"  Name: {username[:25].ljust(25)}  Timezone: {timezone[:28].ljust(28)}"
        )
        status += self._box_line(f"  Location: {location[:66]}")
        status += self._box_line(
            f"  Planet: {planet[:25].ljust(25)}  Galaxy: {galaxy[:28].ljust(28)}"
        )
        status += self._box_line(
            f"  Time: {current_time.ljust(18)}  Date: {current_date.ljust(28)}"
        )

        status += "╠" + "═" * 78 + "╣\n"

        # Mission & Workflow Status
        status += "║ " + self._ljust_emoji("🚀 MISSION CONTROL", 77) + "║\n"
        status += "║ " + "─" * 77 + "║\n"

        if workflow_state and workflow_state.get("current_mission"):
            mission = workflow_state["current_mission"]
            mission_status = workflow_state.get("status", "UNKNOWN")

            # Mission name and status
            mission_name = mission.get("name", "Unknown")[:40]
            status_emoji = self._get_mission_emoji(mission_status)
            status += self._box_line(
                f"  Active: {mission_name[:40].ljust(40)} {status_emoji} {mission_status}"
            )

            # Progress bar
            progress = mission.get("progress", 0)
            if isinstance(progress, str) and "/" in progress:
                # Parse "45/55" format
                try:
                    current, total = map(int, progress.split("/"))
                    percent = int((current / total) * 100) if total > 0 else 0
                except:
                    percent = 0
            else:
                percent = int(progress) if isinstance(progress, (int, float)) else 0

            # Visual progress bar
            bar_length = 30
            filled = int((percent / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            status += self._box_line(f"  Progress: [{bar}] {percent}%")

            # Mission details
            if "phase" in mission:
                phase = mission["phase"][:20]
                elapsed = mission.get("elapsed_time", 0)
                elapsed_str = self._format_elapsed_time(elapsed)
                status += self._box_line(
                    f"  Phase: {phase.ljust(20)}  Runtime: {elapsed_str}"
                )

            # Lifecycle steps
            lifecycle_steps = ["INIT", "SETUP", "EXECUTE", "MONITOR", "COMPLETE"]
            current_phase = mission.get("phase", "UNKNOWN").upper()
            lifecycle_bar = self._build_lifecycle_bar(lifecycle_steps, current_phase)
            status += self._box_line(f"  Lifecycle: {lifecycle_bar}")

            # Checkpoint info
            checkpoints_saved = workflow_state.get("checkpoints_saved", 0)
            last_checkpoint = mission.get("last_checkpoint", "None")
            status += self._box_line(
                f"  Checkpoints: {checkpoints_saved} saved  Last: {str(last_checkpoint)[:20]}"
            )

        else:
            # No active mission
            status += self._box_line("  Status: 💤 No active mission")

            # Stats
            total = workflow_state.get("missions_total", 0) if workflow_state else 0
            completed = (
                workflow_state.get("missions_completed", 0) if workflow_state else 0
            )
            failed = workflow_state.get("missions_failed", 0) if workflow_state else 0

            if total > 0:
                status += self._box_line(
                    f"  History: {completed} completed / {failed} failed / {total} total"
                )

                # Perfect streak
                streak = (
                    workflow_state.get("perfect_streak", 0) if workflow_state else 0
                )
                if streak > 0:
                    status += self._box_line(f"  🔥 Perfect streak: {streak} missions")

                # XP earned
                xp = workflow_state.get("total_xp_earned", 0) if workflow_state else 0
                if xp > 0:
                    status += self._box_line(f"  ⭐ Total XP: {xp}")
            else:
                status += self._box_line(
                    "  💡 Start a mission: ucode memory/workflows/missions/<mission>.upy"
                )

        status += "╠" + "═" * 78 + "╣\n"

        # Connection & Display Status
        status += "║ " + self._ljust_emoji("🔌 SYSTEM STATUS", 77) + "║\n"
        status += "║ " + "─" * 77 + "║\n"

        # Connection status with color-coded indicator
        if self.connection:
            mode = self.connection.get_mode()
            if "ONLINE" in mode:
                conn_icon = "🟢"
                conn_status = "ONLINE"
            else:
                conn_icon = "🔴"
                conn_status = "OFFLINE"
            status += self._box_line(f"  Connectivity: {conn_icon} {conn_status}")

        # Viewport info
        if self.viewport:
            specs = self.viewport.get_grid_specs()
            status += self._box_line(
                f"  Display: 📐 {specs['terminal_width']}×{specs['terminal_height']} chars"
            )
            status += self._box_line(f"  Device: {specs['device_type']}")

        status += "╠" + "═" * 78 + "╣\n"

        # Font Rendering Demo (v1.2.31 - User preferences)
        status += "║ " + self._ljust_emoji("🔤 FONT RENDERING", 77) + "║\n"
        status += "║ " + "─" * 77 + "║\n"
        status += self._build_font_demo_section(config)

        status += "╠" + "═" * 78 + "╣\n"

        # System Metrics (v1.2.22 - Device awareness)
        status += "║ " + self._ljust_emoji("💻 DEVICE METRICS", 77) + "║\n"
        status += "║ " + "─" * 77 + "║\n"

        try:
            from dev.goblin.core.services.device_monitor import DeviceMonitor

            device_monitor = DeviceMonitor(config)
            caps = device_monitor.get_capabilities(use_cache=True)

            # Disk usage bar
            disk_bar_len = 30
            disk_filled = int((caps.disk_usage_percent / 100) * disk_bar_len)
            disk_bar = "█" * disk_filled + "░" * (disk_bar_len - disk_filled)
            status += self._box_line(
                f"  Disk: [{disk_bar}] {caps.disk_usage_percent:.1f}%"
            )
            status += self._box_line(
                f"        {caps.disk_used_gb:.1f}GB used / {caps.disk_total_gb:.1f}GB total ({caps.disk_free_gb:.1f}GB free)"
            )

            # Memory usage bar
            if caps.ram_total_gb > 0:
                ram_bar_len = 30
                ram_filled = int((caps.ram_usage_percent / 100) * ram_bar_len)
                ram_bar = "█" * ram_filled + "░" * (ram_bar_len - ram_filled)
                status += self._box_line(
                    f"  RAM:  [{ram_bar}] {caps.ram_usage_percent:.1f}%"
                )
                status += self._box_line(
                    f"        {caps.ram_total_gb - caps.ram_available_gb:.1f}GB used / {caps.ram_total_gb:.1f}GB total ({caps.ram_available_gb:.1f}GB available)"
                )

            # CPU load
            if caps.cpu_load_1min is not None:
                load_color = (
                    "🟢"
                    if caps.cpu_load_1min < caps.cpu_cores
                    else "🟡" if caps.cpu_load_1min < caps.cpu_cores * 2 else "🔴"
                )
                status += self._box_line(
                    f"  CPU:  {load_color} {caps.cpu_cores} cores, load: {caps.cpu_load_1min:.2f} (1m) {caps.cpu_load_5min:.2f} (5m)"
                )
            else:
                status += self._box_line(f"  CPU:  {caps.cpu_cores} cores")

            # Battery (if present)
            if caps.has_battery and caps.battery_percent is not None:
                battery_bar_len = 20
                battery_filled = int((caps.battery_percent / 100) * battery_bar_len)
                battery_bar = "█" * battery_filled + "░" * (
                    battery_bar_len - battery_filled
                )
                charge_icon = "⚡" if caps.battery_charging else "🔋"
                status += self._box_line(
                    f"  Battery: {charge_icon} [{battery_bar}] {caps.battery_percent:.0f}%"
                )

            # Device class
            device_class = device_monitor.get_device_class(caps)
            suggested_preset = device_monitor.suggest_udos_preset(caps)
            status += self._box_line(
                f"  Class: {device_class.upper():<15}  Suggested preset: {suggested_preset.upper()}"
            )

        except Exception as e:
            status += self._box_line("  ⚠️  Device metrics unavailable")

        status += "╠" + "═" * 78 + "╣\n"

        # Web Extension Servers with visual status bars
        status += "║ " + self._ljust_emoji("🌐 WEB SERVERS", 77) + "║\n"
        status += "║ " + "─" * 77 + "║\n"

        # Import ServerManager if available
        try:
            from extensions.server_manager import ServerManager

            server_manager = ServerManager()

            any_running = False
            for srv_name, srv_info in server_manager.servers.items():
                if server_manager._is_process_running(srv_info.get("pid")):
                    any_running = True
                    url = srv_info.get("url", "Unknown")
                    uptime = time.time() - srv_info.get("started_at", time.time())
                    uptime_str = server_manager._format_uptime(uptime)

                    # Create status bar based on uptime
                    bar_length = 10
                    filled = min(
                        bar_length, int((uptime / 3600) * bar_length)
                    )  # 1 hour = full bar
                    bar = "█" * filled + "░" * (bar_length - filled)

                    status += self._box_line(
                        f"  ✅ {srv_name[:16].ljust(16)} {bar} {uptime_str.rjust(8)}"
                    )
                    status += self._box_line(f"     {url}")

            if not any_running:
                status += self._box_line("  ⭕ No servers running")
                status += self._box_line(
                    "     💡 Use: OUTPUT START teletext (or dashboard/typora)"
                )
        except Exception as e:
            status += self._box_line("  📡 Web servers not configured")
            status += self._box_line("     💡 Available when extensions loaded")

        status += "╠" + "═" * 78 + "╣\n"

        # System health and resources
        status += "║ " + self._ljust_emoji("🏥 SYSTEM HEALTH", 77) + "║\n"
        status += "║ " + "─" * 77 + "║\n"

        try:
            from dev.goblin.core.services.uDOS_startup import (
                check_python_version,
                check_dependencies,
            )

            py_ok = check_python_version()
            dep_result = check_dependencies()
            dep_ok = dep_result.status == "success"

            py_status = f"✅ {sys.version.split()[0]}" if py_ok else "⚠️  WARNING"
            status += self._box_line(f"  Python: {py_status}")

            dep_status = "✅ All installed" if dep_ok else "⚠️  Issues detected"
            status += self._box_line(f"  Dependencies: {dep_status}")

            # Add system resources
            try:
                import psutil

                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory().percent
                disk = psutil.disk_usage(".").percent

                cpu_emoji = "✅" if cpu < 70 else "⚠️" if cpu < 90 else "🔴"
                mem_emoji = "✅" if mem < 70 else "⚠️" if mem < 90 else "🔴"
                disk_emoji = "✅" if disk < 80 else "⚠️" if disk < 95 else "🔴"

                status += self._box_line(
                    f"  CPU: {cpu_emoji} {cpu:5.1f}%  Memory: {mem_emoji} {mem:5.1f}%  Disk: {disk_emoji} {disk:5.1f}%"
                )
            except ImportError:
                status += self._box_line(
                    "  Resources: 💡 Install psutil for monitoring"
                )
        except Exception as e:
            status += self._box_line("  Health check: Unable to verify")

        # History stats if available
        if self.history:
            undo_count = len(self.history.undo_stack)
            redo_count = len(self.history.redo_stack)
            history_str = f"History: {undo_count} undo / {redo_count} redo available"
            status += self._box_line(f"  {history_str}")

        status += "╠" + "═" * 78 + "╣\n"

        # System Inventory (v1.0.0.64+)
        status += "║ " + self._ljust_emoji("📊 SYSTEM INVENTORY", 77) + "║\n"
        status += "║ " + "─" * 77 + "║\n"
        status += self._build_system_inventory_section()
        status += "╠" + "═" * 78 + "╣\n"

        # API Quotas (if resource manager available)
        try:
            from dev.goblin.core.services.resource_manager import get_resource_manager

            rm = get_resource_manager()
            status += "║ " + self._ljust_emoji("🔑 API QUOTAS", 77) + "║\n"
            status += "║ " + "─" * 77 + "║\n"

            for provider in ["gemini", "github"]:
                quota_info = rm.check_api_quota(provider)
                if "error" not in quota_info:
                    percent = quota_info["percent"]
                    emoji = "✅" if percent < 50 else "⚠️" if percent < 80 else "🔴"
                    quota_str = f"{provider.upper()}: {emoji} {quota_info['used']}/{quota_info['limit']} ({percent}%)"
                    status += self._box_line(f"  {quota_str}")
        except Exception:
            pass  # Skip quota section if not available

        # Archive System Health (v1.1.16)
        try:
            from dev.goblin.core.utils.archive_manager import ArchiveManager

            archive_mgr = ArchiveManager()
            health = archive_mgr.get_health_metrics()

            status += "╠" + "═" * 78 + "╣\n"
            status += "║ " + self._ljust_emoji("📦 ARCHIVE SYSTEM", 77) + "║\n"
            status += "║ " + "─" * 77 + "║\n"

            # Total stats
            total_size_mb = round(health["total_size"] / (1024 * 1024), 2)
            emoji = (
                "✅" if total_size_mb < 100 else "⚠️" if total_size_mb < 500 else "🔴"
            )

            archive_stats = f"Archives: {health['total_archives']}  Files: {health['total_files']}  Size: {emoji} {total_size_mb} MB"
            status += self._box_line(f"  {archive_stats}")

            # Warnings
            if health["warnings"]:
                for warning in health["warnings"][:2]:  # Show max 2 warnings
                    warn_text = warning[:70]  # Truncate long warnings
                    status += self._box_line(f"  ⚠️  {warn_text}")
        except Exception:
            pass  # Skip archive section if not available

        status += "╚" + "═" * 78 + "╝\n"
        status += "\n💡 Tips: STATUS --live (monitoring) | RESOURCE STATUS (detailed quotas)\n"

        return status

    def _status_live_mode(self):
        """Display live-updating status (updates every 3 seconds)."""
        try:
            status = "\n🔴 LIVE STATUS MODE (Press Ctrl+C to exit)\n\n"
            status += "Refreshing every 3 seconds...\n\n"
            status += self._get_live_status_display()
            status += "\n\n💡 Press Ctrl+C to return to command prompt\n"
            status += (
                "\n⚠️  Note: Full live mode requires threading. This is a snapshot.\n"
            )

            return status

        except KeyboardInterrupt:
            return "\n\n✅ Exited live status mode\n"

    def _get_live_status_display(self):
        """Get the current status display for live mode."""
        display = "╔" + "═" * 78 + "╗\n"
        display += self._box_line(
            f" 🔮 uDOS LIVE STATUS - {datetime.now().strftime('%H:%M:%S')}"
        )
        display += "╠" + "═" * 78 + "╣\n"

        # Server status with visual indicators
        display += self._box_line(" SERVER STATUS")
        display += "║ " + "─" * 77 + "║\n"

        servers = {
            "typo": {"name": "Typo Editor", "port": 5173},
            "dashboard": {"name": "Dashboard", "port": 8888},
            "terminal": {"name": "Web Terminal", "port": 8889},
            "teletext": {"name": "Teletext Interface", "port": 9002},
            "desktop": {"name": "System Desktop", "port": 8892},
            "font-editor": {"name": "Character Editor", "port": 8891},
            "markdown": {"name": "Markdown Viewer (Typo)", "port": 5173},
        }

        try:
            from dev.goblin.core.uDOS_server import ServerManager
            from dev.goblin.core.utils.paths import PATHS

            server_manager = ServerManager()

            for srv_id, srv_config in servers.items():
                if srv_id in server_manager.servers:
                    srv_info = server_manager.servers[srv_id]
                    if server_manager._is_process_running(srv_info.get("pid")):
                        uptime = time.time() - srv_info.get("started_at", time.time())
                        uptime_str = server_manager._format_uptime(uptime)
                        port = srv_info.get("port", srv_config["port"])

                        indicator = "●"
                        line = f"  {indicator} {srv_config['name'][:20].ljust(20)} [ONLINE]  :{port}  ⏱ {uptime_str}"
                        display += self._box_line(line)
                    else:
                        line = f"  ○ {srv_config['name'][:20].ljust(20)} [OFFLINE] :{srv_config['port']}"
                        display += self._box_line(line)
                else:
                    line = f"  ○ {srv_config['name'][:20].ljust(20)} [OFFLINE] :{srv_config['port']}"
                    display += self._box_line(line)
        except Exception:
            display += self._box_line("  ⚠️  Server status unavailable")

        display += "╚" + "═" * 78 + "╝"

        return display

    def handle_dashboard(self, params, grid, parser):
        """
        Display system dashboard (alias for STATUS command).

        DASH is now an alias for STATUS, showing enhanced ASCII dashboard
        with user info, location, planet, galaxy, time, and system metrics.
        """
        return self._status_snapshot()

    def handle_viewport(self, params, grid, parser):
        """
        Display viewport visualization with educational TUI demo.

        Shows:
        - Current terminal dimensions
        - Device tier detection
        - TUI capabilities (Unicode, colors, monospace)
        - Box-drawing and column formatting demos
        - Color palette test
        """
        try:
            from dev.goblin.core.services.viewport_manager import ViewportManager
            from dev.goblin.core.utils.viewport_viz import ViewportVisualizer

            # Get viewport info
            vp = ViewportManager()
            vp_info = vp.refresh_viewport()

            # Create visualizer
            viz = ViewportVisualizer(viewport=vp)

            # Generate educational splash
            return viz.generate_educational_splash(viewport_manager=vp)

        except Exception as e:
            return f"❌ Error displaying viewport: {e}\n💡 Try: REBOOT"

    def handle_palette(self, params, grid, parser):
        """
        Display color palette with visual tests and reference.

        Shows the Polaroid color system with:
        - Color blocks visualization
        - Hex codes and tput numbers
        - Usage descriptions
        - Grayscale gradient
        """
        try:
            # Load palette data from font-system.json
            palette_path = Path("core/data/font-system.json")
            with open(palette_path, "r") as f:
                font_system = json.load(f)

            palette = font_system["font_system"]["color_palette"]
            colors = palette["colors"]

            # Build output
            output = []
            output.append("🎨 " + palette["NAME"].upper() + " COLOR PALETTE")
            output.append("=" * 60)
            output.append(f"Name: {palette['NAME']}")
            output.append(f"Version: {palette['VERSION']}")
            output.append(f"Description: {palette['DESCRIPTION']}")
            output.append("")

            # Primary colors section
            output.append("📋 PRIMARY COLORS:")
            output.append("-" * 60)
            for color_id, color_data in colors["PRIMARY"].items():
                # Color block (unicode filled block)
                ansi_code = color_data["ansi"].replace("\\033", "\033")
                reset = "\033[0m"
                block = f"{ansi_code}███{reset}"

                name = color_data["name"].ljust(20)
                tput_hex = f"(tput:{color_data['tput']}) {color_data['hex']}".ljust(20)
                usage = color_data["usage"]

                output.append(f"  {block} {name} {tput_hex} - {usage}")

            output.append("")

            # Monochrome section
            output.append("📋 MONOCHROME:")
            output.append("-" * 60)
            for color_id, color_data in colors["MONOCHROME"].items():
                ansi_code = color_data["ansi"].replace("\\033", "\033")
                reset = "\033[0m"
                block = f"{ansi_code}███{reset}"

                name = color_data["name"].ljust(20)
                tput_hex = f"(tput:{color_data['tput']}) {color_data['hex']}".ljust(20)
                usage = color_data["usage"]

                output.append(f"  {block} {name} {tput_hex} - {usage}")

            output.append("")

            # Grayscale gradient
            output.append("📋 GRAYSCALE GRADIENT:")
            output.append("-" * 60)
            gradient_line = "  "
            for color_id, color_data in colors["GRAYSCALE"].items():
                ansi_code = color_data["ansi"].replace("\\033", "\033")
                reset = "\033[0m"
                gradient_line += f"{ansi_code}████{reset}"
            output.append(gradient_line)
            output.append(
                "  Black → Darkest → Dark → Medium → Light → Lightest → White"
            )
            output.append("")

            # Visual test blocks
            output.append("🎨 COLOR COMBINATION TESTS:")
            output.append("-" * 60)
            test_line = "  "
            for color_id in ["red", "green", "yellow", "blue", "purple", "cyan"]:
                color_data = colors["PRIMARY"][color_id]
                ansi_code = color_data["ansi"].replace("\\033", "\033")
                reset = "\033[0m"
                test_line += f"{ansi_code}██{reset} "
            output.append(test_line)
            output.append("")

            output.append("=" * 60)
            output.append("💡 Use: VIEWPORT for terminal capabilities test")
            output.append("💡 Use: REBOOT to see full splash screen with color tests")
            output.append("=" * 60)

            return "\n".join(output)

        except Exception as e:
            return f"❌ Failed to load palette: {str(e)}"

    # =========================================================================
    # v1.3.3 - Multi-Role Dashboard Commands
    # =========================================================================

    def handle_dash(self, params, grid, parser):
        """
        Display role-based dashboard view.

        Usage:
            DASH                  - Main dashboard
            DASH PROFILE          - Profile dashboard
            DASH NETWORK          - Network status
            DASH KNOWLEDGE        - Knowledge browser
            DASH MISSIONS         - Mission tracking
            DASH COMMUNITY        - Community features
            DASH ADMIN            - Admin dashboard (Wizard only)
            DASH --role <level>   - Override role for testing
            DASH --compact        - Compact mode
        """
        if not DASHBOARD_SERVICE_AVAILABLE:
            # Fall back to legacy dashboard
            return self._status_snapshot()

        try:
            service = get_dashboard_service()

            # Parse parameters
            dashboard_type = DashboardType.MAIN
            role_override = None
            compact = False

            if params:
                param_str = " ".join(params).upper()

                # Check for dashboard type
                if "PROFILE" in param_str:
                    dashboard_type = DashboardType.PROFILE
                elif "NETWORK" in param_str:
                    dashboard_type = DashboardType.NETWORK
                elif "KNOWLEDGE" in param_str:
                    dashboard_type = DashboardType.KNOWLEDGE
                elif "MISSIONS" in param_str:
                    dashboard_type = DashboardType.MISSIONS
                elif "COMMUNITY" in param_str:
                    dashboard_type = DashboardType.COMMUNITY
                elif "ADMIN" in param_str:
                    dashboard_type = DashboardType.ADMIN

                # Check for role override
                if "--role" in param_str.lower() or "--ROLE" in param_str:
                    for i, p in enumerate(params):
                        if p.lower() == "--role" and i + 1 < len(params):
                            try:
                                role_val = int(params[i + 1])
                                role_override = RoleLevel(role_val)
                            except (ValueError, KeyError):
                                # Try by name
                                role_name = params[i + 1].upper()
                                for rl in RoleLevel:
                                    if rl.name == role_name:
                                        role_override = rl
                                        break

                # Check for compact mode
                if "--compact" in param_str.lower() or "--COMPACT" in param_str:
                    compact = True

            # Apply role override if specified
            if role_override:
                service.set_role(role_override)

            # Apply compact mode
            if compact:
                service.config.compact_mode = True

            # Get and render dashboard
            lines = service.get_dashboard(dashboard_type)

            # Reset compact mode
            if compact:
                service.config.compact_mode = False

            return "\n".join(lines)

        except Exception as e:
            return f"❌ Dashboard error: {e}\n💡 Falling back to legacy STATUS"

    def handle_dash_role(self, params, grid, parser):
        """
        Set or display current dashboard role.

        Usage:
            DASH ROLE             - Show current role
            DASH ROLE <level>     - Set role (0-7 or name)
            DASH ROLE LIST        - List all roles
        """
        if not DASHBOARD_SERVICE_AVAILABLE:
            return "❌ Dashboard service not available"

        try:
            service = get_dashboard_service()

            if not params:
                # Show current role
                role = service.config.role
                return f"Current role: {role.name} (Level {role.value})"

            param = params[0].upper()

            if param == "LIST":
                lines = ["Available roles:"]
                for rl in RoleLevel:
                    lines.append(f"  {rl.value}: {rl.name}")
                return "\n".join(lines)

            # Set role
            try:
                role_val = int(param)
                new_role = RoleLevel(role_val)
            except ValueError:
                # Try by name
                new_role = None
                for rl in RoleLevel:
                    if rl.name == param:
                        new_role = rl
                        break
                if not new_role:
                    return f"❌ Unknown role: {param}\n💡 Use: DASH ROLE LIST"

            service.set_role(new_role)
            return f"✅ Role set to: {new_role.name} (Level {new_role.value})"

        except Exception as e:
            return f"❌ Error: {e}"

    def handle_dash_alert(self, params, grid, parser):
        """
        Manage dashboard alerts.

        Usage:
            DASH ALERT                    - Show active alerts
            DASH ALERT ADD "message"      - Add info alert
            DASH ALERT ADD --warning "m"  - Add warning alert
            DASH ALERT ADD --error "m"    - Add error alert
            DASH ALERT CLEAR              - Clear all alerts
        """
        if not DASHBOARD_SERVICE_AVAILABLE:
            return "❌ Dashboard service not available"

        try:
            service = get_dashboard_service()

            if not params:
                # Show alerts
                alerts = service.state.alerts
                if not alerts:
                    return "No active alerts"

                lines = ["Active alerts:"]
                for i, alert in enumerate(alerts):
                    icon = {
                        "info": "ℹ️",
                        "warning": "⚠️",
                        "error": "❌",
                        "success": "✅",
                    }.get(alert.get("type", "info"), "•")
                    lines.append(f"  {icon} {alert.get('message', '')}")
                return "\n".join(lines)

            action = params[0].upper()

            if action == "CLEAR":
                service.clear_alerts()
                return "✅ Alerts cleared"

            if action == "ADD":
                # Determine alert type
                alert_type = "info"
                message_parts = []

                for p in params[1:]:
                    if p == "--warning":
                        alert_type = "warning"
                    elif p == "--error":
                        alert_type = "error"
                    elif p == "--success":
                        alert_type = "success"
                    else:
                        message_parts.append(p)

                message = " ".join(message_parts).strip("\"'")
                if not message:
                    return "❌ Please provide a message"

                service.add_alert(message, alert_type)
                return f"✅ Alert added: {message}"

            return "❌ Unknown action. Use: DASH ALERT [ADD|CLEAR]"

        except Exception as e:
            return f"❌ Error: {e}"

    def handle_dash_layout(self, params, grid, parser):
        """
        Manage dashboard layouts.

        Usage:
            DASH LAYOUT           - Show current layout
            DASH LAYOUT LIST      - List available layouts
            DASH LAYOUT <name>    - Switch to layout
        """
        if not DASHBOARD_SERVICE_AVAILABLE:
            return "❌ Dashboard service not available"

        try:
            from dev.goblin.core.ui.panel_templates import list_layouts, DASHBOARD_LAYOUTS

            service = get_dashboard_service()

            if not params:
                return f"Current layout: {service.config.layout}"

            param = params[0].upper()

            if param == "LIST":
                layouts = list_layouts()
                lines = ["Available layouts:"]
                for name in layouts:
                    layout = DASHBOARD_LAYOUTS.get(name)
                    desc = layout.description if layout else ""
                    lines.append(f"  • {name}: {desc}")
                return "\n".join(lines)

            # Set layout
            layout_name = params[0].lower()
            if layout_name in list_layouts():
                service.set_layout(layout_name)
                return f"✅ Layout set to: {layout_name}"
            else:
                return f"❌ Unknown layout: {layout_name}\n💡 Use: DASH LAYOUT LIST"

        except Exception as e:
            return f"❌ Error: {e}"
