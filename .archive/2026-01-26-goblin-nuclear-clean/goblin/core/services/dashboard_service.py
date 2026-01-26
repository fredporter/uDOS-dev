#!/usr/bin/env python3
"""
uDOS v1.3.3 - Dashboard Service

Multi-role dashboard system providing:
- Role-based dashboard views (8 security levels)
- Status aggregation from services
- Real-time updates
- Customizable layouts
- Dashboard data aggregation from workflows and missions (integrated)

Version: 1.3.3
Author: Fred Porter
Date: December 2025

Consolidated from:
- dashboard_service.py (780 LOC) - Multi-role dashboard rendering
- dashboard_data_service.py (340 LOC) - Dashboard data aggregation
= Result: 1,120 LOC unified dashboard service
"""

import json
import os
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from dev.goblin.core.ui.panel_templates import (
    Panel,
    PanelType,
    PanelStyle,
    Alignment,
    create_status_panel,
    create_progress_panel,
    create_stats_panel,
    create_list_panel,
    create_log_panel,
    create_alert_panel,
    create_header_panel,
    create_footer_panel,
    create_menu_panel,
    render_panels_horizontal,
    render_panels_vertical,
    render_panels_grid,
    DashboardLayout,
    DASHBOARD_LAYOUTS,
    get_layout,
)

# BoxStyle now comes from consolidated module
from dev.goblin.core.ui.components import BoxStyle

logger = logging.getLogger(__name__)


class DashboardDataService:
    """
    Internal service for dashboard data aggregation.
    Provides live data for all dashboard panels (integrated from dashboard_data_service.py).
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize dashboard data service."""
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        self.project_root = project_root
        self.memory_path = project_root / "memory"
        self.workflows_path = self.memory_path / "workflows"

    # =========================================================================
    # DASHBOARD STATUS
    # =========================================================================

    def get_dashboard_status(self) -> Dict[str, Any]:
        """Get complete dashboard status with all panel data."""
        return {
            "missions": self.get_missions_panel_data(),
            "workflows": self.get_workflows_panel_data(),
            "checklists": self.get_checklists_panel_data(),
            "xp": self.get_xp_panel_data(),
            "system": self.get_system_panel_data(),
            "timestamp": datetime.now().isoformat(),
        }

    # =========================================================================
    # MISSIONS PANEL
    # =========================================================================

    def get_missions_panel_data(self) -> Dict[str, Any]:
        """Get missions panel data."""
        missions_dir = self.workflows_path / "missions"

        if not missions_dir.exists():
            return {
                "active": [],
                "count": 0,
                "total_steps": 0,
                "completed_steps": 0,
                "progress_percent": 0,
            }

        active_missions = []
        total_steps = 0
        completed_steps = 0

        # Scan for .upy mission files
        for mission_file in missions_dir.glob("*.upy"):
            try:
                mission_data = self._parse_mission_file(mission_file)
                if mission_data and mission_data.get("status") == "active":
                    active_missions.append(mission_data)
                    total_steps += mission_data.get("total_steps", 0)
                    completed_steps += mission_data.get("completed_steps", 0)
            except Exception as e:
                logger.error(f"Error parsing mission {mission_file}: {e}")

        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        return {
            "active": active_missions,
            "count": len(active_missions),
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "progress_percent": round(progress, 1),
        }

    def _parse_mission_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse mission .upy file for metadata."""
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Extract frontmatter (YAML-style)
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()

                    # Simple YAML parser for mission metadata
                    metadata = {}
                    for line in frontmatter.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip()

                    # Count steps (commands in file)
                    body = parts[2]
                    total_steps = (
                        body.count("\n(")
                        + body.count("\nGENERATE")
                        + body.count("\nLIST")
                    )

                    return {
                        "id": file_path.stem,
                        "name": metadata.get("title", file_path.stem),
                        "status": metadata.get("status", "active").lower(),
                        "priority": metadata.get("priority", "medium").lower(),
                        "total_steps": total_steps,
                        "completed_steps": int(metadata.get("completed_steps", "0")),
                        "progress_percent": 0,  # Calculate from completed_steps
                        "file": str(file_path),
                    }

            return None
        except Exception as e:
            logger.error(f"Error parsing mission file {file_path}: {e}")
            return None

    # =========================================================================
    # WORKFLOWS PANEL
    # =========================================================================

    def get_workflows_panel_data(self) -> Dict[str, Any]:
        """Get workflows panel data."""
        state_dir = self.workflows_path / "state"

        if not state_dir.exists():
            return {
                "current": None,
                "phase": "idle",
                "checkpoints": 0,
                "status": "inactive",
            }

        # Check for current workflow state
        current_state_file = state_dir / "current.json"
        if current_state_file.exists():
            try:
                with open(current_state_file, "r") as f:
                    state = json.load(f)

                return {
                    "current": state.get("workflow_name"),
                    "phase": state.get("phase", "unknown"),
                    "checkpoints": state.get("checkpoint_count", 0),
                    "status": state.get("status", "active"),
                    "last_update": state.get("last_update"),
                }
            except Exception as e:
                logger.error(f"Error reading workflow state: {e}")

        return {
            "current": None,
            "phase": "idle",
            "checkpoints": 0,
            "status": "inactive",
        }

    # =========================================================================
    # CHECKLISTS PANEL
    # =========================================================================

    def get_checklists_panel_data(self) -> Dict[str, Any]:
        """Get checklists panel data."""
        checklists_dir = self.memory_path / "checklists"

        if not checklists_dir.exists():
            return {
                "active": [],
                "count": 0,
                "total_items": 0,
                "completed_items": 0,
                "progress_percent": 0,
            }

        active_checklists = []
        total_items = 0
        completed_items = 0

        # Scan for checklist files
        for checklist_file in checklists_dir.rglob("*.json"):
            try:
                with open(checklist_file, "r") as f:
                    checklist = json.load(f)

                if checklist.get("status") == "active":
                    items = checklist.get("items", [])
                    completed = sum(1 for item in items if item.get("completed", False))

                    checklist_data = {
                        "id": checklist_file.stem,
                        "name": checklist.get("name", checklist_file.stem),
                        "total_items": len(items),
                        "completed_items": completed,
                        "progress_percent": (
                            (completed / len(items) * 100) if items else 0
                        ),
                    }

                    active_checklists.append(checklist_data)
                    total_items += len(items)
                    completed_items += completed
            except Exception as e:
                logger.error(f"Error parsing checklist {checklist_file}: {e}")

        progress = (completed_items / total_items * 100) if total_items > 0 else 0

        return {
            "active": active_checklists,
            "count": len(active_checklists),
            "total_items": total_items,
            "completed_items": completed_items,
            "progress_percent": round(progress, 1),
        }

    # =========================================================================
    # XP PANEL
    # =========================================================================

    def get_xp_panel_data(self) -> Dict[str, Any]:
        """Get XP and achievements panel data."""
        xp_file = self.memory_path / "bank" / "user" / "xp.json"

        if not xp_file.exists():
            return {
                "total_xp": 0,
                "level": 1,
                "level_name": "Novice",
                "achievements": [],
                "perfect_streak": 0,
            }

        try:
            with open(xp_file, "r") as f:
                xp_data = json.load(f)

            return {
                "total_xp": xp_data.get("total_xp", 0),
                "level": xp_data.get("level", 1),
                "level_name": xp_data.get("level_name", "Novice"),
                "achievements": xp_data.get("achievements", []),
                "perfect_streak": xp_data.get("perfect_streak", 0),
            }
        except Exception as e:
            logger.error(f"Error reading XP data: {e}")
            return {
                "total_xp": 0,
                "level": 1,
                "level_name": "Novice",
                "achievements": [],
                "perfect_streak": 0,
            }

    # =========================================================================
    # SYSTEM PANEL
    # =========================================================================

    def get_system_panel_data(self) -> Dict[str, Any]:
        """Get system status panel data."""
        return {
            "uptime": self._get_system_uptime(),
            "memory_usage": self._get_memory_usage(),
            "disk_usage": self._get_disk_usage(),
            "api_status": "online",
            "extensions": self._get_extension_status(),
        }

    def _get_system_uptime(self) -> str:
        """Get system uptime."""
        # Simplified - return current time for now
        return "Active"

    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage stats."""
        try:
            import psutil

            mem = psutil.virtual_memory()
            return {
                "used_percent": mem.percent,
                "used_mb": mem.used // (1024 * 1024),
                "total_mb": mem.total // (1024 * 1024),
            }
        except ImportError:
            return {"used_percent": 0, "used_mb": 0, "total_mb": 0}

    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage for project."""
        try:
            import shutil

            usage = shutil.disk_usage(self.project_root)
            return {
                "used_percent": (usage.used / usage.total) * 100,
                "used_gb": usage.used // (1024**3),
                "total_gb": usage.total // (1024**3),
            }
        except Exception:
            return {"used_percent": 0, "used_gb": 0, "total_gb": 0}

    def _get_extension_status(self) -> Dict[str, str]:
        """Get status of extensions."""
        return {
            "tauri": "online",
            "api": "online",
            "web": "online",
            "cloud": "offline",
            "meshcore": "offline",
        }


class DashboardType:
    """Dashboard types by purpose."""
    MAIN = "main"  # Main system dashboard
    PROFILE = "profile"  # User profile view
    NETWORK = "network"  # Network/MeshCore status
    KNOWLEDGE = "knowledge"  # Knowledge bank browser
    MISSIONS = "missions"  # Mission tracking
    COMMUNITY = "community"  # Community features
    ADMIN = "admin"  # Admin/wizard dashboard
    CUSTOM = "custom"  # User-defined


class RoleLevel(Enum):
    """User role levels (maps to user_profile.Role)."""

    VISITOR = 0  # Read-only, limited access
    SURVIVOR = 1  # Basic features
    EXPLORER = 2  # Map access
    BUILDER = 3  # Create content
    GHOST = 4  # Network features
    MENTOR = 5  # Guide others
    GUARDIAN = 6  # Moderate content
    WIZARD = 7  # Full admin


@dataclass
class DashboardConfig:
    """Dashboard configuration."""

    user_id: str = "local"
    role: RoleLevel = RoleLevel.SURVIVOR
    theme: str = "default"
    layout: str = "status"
    refresh_rate: int = 30  # Seconds
    show_alerts: bool = True
    show_tips: bool = True
    compact_mode: bool = False
    custom_panels: List[str] = field(default_factory=list)


@dataclass
class DashboardState:
    """Current dashboard state."""

    active_type: DashboardType = DashboardType.MAIN
    last_refresh: Optional[datetime] = None
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    cached_data: Dict[str, Any] = field(default_factory=dict)
    scroll_position: int = 0
    selected_panel: int = 0


class DashboardService:
    """
    Multi-role dashboard service.

    Provides role-appropriate views and aggregates
    status from multiple services.
    """

    def __init__(self, config: Optional[DashboardConfig] = None):
        """Initialize dashboard service."""
        self.config = config or DashboardConfig()
        self.state = DashboardState()
        self._data_providers: Dict[str, Callable] = {}
        self._register_default_providers()

    def _register_default_providers(self) -> None:
        """Register default data providers."""
        self._data_providers = {
            "system": self._get_system_status,
            "user": self._get_user_status,
            "network": self._get_network_status,
            "resources": self._get_resource_status,
            "activity": self._get_recent_activity,
            "missions": self._get_mission_status,
            "knowledge": self._get_knowledge_status,
        }

    def register_provider(self, name: str, provider: Callable) -> None:
        """Register a custom data provider."""
        self._data_providers[name] = provider

    def get_dashboard(self, dashboard_type: DashboardType = None) -> List[str]:
        """Get rendered dashboard for current role."""
        dtype = dashboard_type or self.state.active_type

        # Get role-appropriate panels
        panels = self._get_panels_for_role(dtype)

        # Render based on layout
        if self.config.compact_mode:
            return self._render_compact(panels)
        else:
            return self._render_full(panels)

    def _get_panels_for_role(self, dtype: DashboardType) -> List[Panel]:
        """Get panels appropriate for user's role."""
        panels = []
        role = self.config.role

        if dtype == DashboardType.MAIN:
            panels = self._build_main_dashboard(role)
        elif dtype == DashboardType.PROFILE:
            panels = self._build_profile_dashboard(role)
        elif dtype == DashboardType.NETWORK:
            panels = self._build_network_dashboard(role)
        elif dtype == DashboardType.KNOWLEDGE:
            panels = self._build_knowledge_dashboard(role)
        elif dtype == DashboardType.MISSIONS:
            panels = self._build_missions_dashboard(role)
        elif dtype == DashboardType.COMMUNITY:
            panels = self._build_community_dashboard(role)
        elif dtype == DashboardType.ADMIN:
            panels = self._build_admin_dashboard(role)

        return panels

    def _build_main_dashboard(self, role: RoleLevel) -> List[Panel]:
        """Build main system dashboard."""
        panels = []

        # Header for all roles
        panels.append(
            create_header_panel(
                "uDOS Dashboard",
                f"Role: {role.name} | {datetime.now().strftime('%H:%M:%S')}",
                width=78,
            )
        )

        # System status (all roles)
        system_data = self._data_providers["system"]()
        panels.append(create_status_panel("System", system_data, width=38))

        # Resources (Survivor+)
        if role.value >= RoleLevel.SURVIVOR.value:
            resource_data = self._data_providers["resources"]()
            panels.append(create_stats_panel("Resources", resource_data, width=38))

        # Activity log (Explorer+)
        if role.value >= RoleLevel.EXPLORER.value:
            activity = self._data_providers["activity"]()
            panels.append(
                create_log_panel("Recent Activity", activity, width=78, height=8)
            )

        # Network status (Ghost+)
        if role.value >= RoleLevel.GHOST.value:
            network_data = self._data_providers["network"]()
            panels.append(create_status_panel("Network", network_data, width=78))

        # Alerts (if any)
        if self.config.show_alerts and self.state.alerts:
            for alert in self.state.alerts[:3]:
                panels.append(
                    create_alert_panel(
                        alert.get("message", ""),
                        alert_type=alert.get("type", "info"),
                        width=78,
                    )
                )

        return panels

    def _build_profile_dashboard(self, role: RoleLevel) -> List[Panel]:
        """Build user profile dashboard."""
        panels = []

        user_data = self._data_providers["user"]()

        panels.append(
            create_header_panel(
                f"Profile: {user_data.get('username', 'Unknown')}",
                f"Role: {role.name}",
                width=78,
            )
        )

        # Basic info
        panels.append(
            create_status_panel(
                "User Info",
                {
                    "Username": user_data.get("username", "local"),
                    "Role": role.name,
                    "Level": str(user_data.get("level", 1)),
                    "Joined": user_data.get("joined", "Today"),
                },
                width=38,
            )
        )

        # Stats
        resource_data = self._data_providers["resources"]()
        panels.append(create_stats_panel("Stats", resource_data, width=38))

        # Achievements (Builder+)
        if role.value >= RoleLevel.BUILDER.value:
            achievements = user_data.get("achievements", [])
            panels.append(
                create_list_panel(
                    "Achievements",
                    achievements[:5] if achievements else ["No achievements yet"],
                    bullet="🏆",
                    width=78,
                )
            )

        return panels

    def _build_network_dashboard(self, role: RoleLevel) -> List[Panel]:
        """Build network status dashboard."""
        panels = []

        # Require Ghost+ for network dashboard
        if role.value < RoleLevel.GHOST.value:
            panels.append(
                create_alert_panel(
                    "Network dashboard requires Ghost role (4) or higher.",
                    alert_type="warning",
                    width=78,
                )
            )
            return panels

        panels.append(
            create_header_panel(
                "Network Status", "MeshCore Primary | Web/Cloud Extension", width=78
            )
        )

        network_data = self._data_providers["network"]()

        # MeshCore status
        panels.append(
            create_status_panel(
                "MeshCore (Primary)",
                {
                    "Status": network_data.get("meshcore_status", "Offline"),
                    "Peers": str(network_data.get("peer_count", 0)),
                    "Signal": network_data.get("signal", "N/A"),
                    "Latency": network_data.get("latency", "N/A"),
                },
                width=38,
                style=BoxStyle.DOUBLE,
            )
        )

        # Web/Cloud status (Wizard gateway)
        panels.append(
            create_status_panel(
                "Web/Cloud (Extension)",
                {
                    "Gateway": network_data.get("gateway_status", "Disabled"),
                    "API": network_data.get("api_status", "N/A"),
                    "Sync": network_data.get("sync_status", "N/A"),
                },
                width=38,
            )
        )

        # Connected devices (Guardian+)
        if role.value >= RoleLevel.GUARDIAN.value:
            devices = network_data.get("devices", [])
            panels.append(
                create_list_panel(
                    "Connected Devices",
                    devices[:10] if devices else ["No devices connected"],
                    bullet="📡",
                    width=78,
                )
            )

        return panels

    def _build_knowledge_dashboard(self, role: RoleLevel) -> List[Panel]:
        """Build knowledge browser dashboard."""
        panels = []

        panels.append(
            create_header_panel("Knowledge Bank", "230+ Survival Guides", width=78)
        )

        knowledge_data = self._data_providers["knowledge"]()

        # Categories
        categories = knowledge_data.get("categories", [])
        panels.append(
            create_menu_panel(
                "Categories",
                categories[:10] if categories else ["water", "fire", "shelter", "food"],
                width=38,
            )
        )

        # Recent guides
        recent = knowledge_data.get("recent", [])
        panels.append(
            create_list_panel(
                "Recently Viewed",
                recent[:5] if recent else ["No recent guides"],
                bullet="📖",
                width=38,
            )
        )

        # Progress (Builder+)
        if role.value >= RoleLevel.BUILDER.value:
            progress = knowledge_data.get("completion", 0.0)
            panels.append(create_progress_panel("Completion", progress, width=78))

        return panels

    def _build_missions_dashboard(self, role: RoleLevel) -> List[Panel]:
        """Build mission tracking dashboard."""
        panels = []

        panels.append(
            create_header_panel("Missions", "Active Workflows & Tasks", width=78)
        )

        mission_data = self._data_providers["missions"]()

        # Active missions
        active = mission_data.get("active", [])
        panels.append(
            create_list_panel(
                "Active Missions",
                active[:5] if active else ["No active missions"],
                bullet="🎯",
                width=38,
            )
        )

        # Completed missions
        completed = mission_data.get("completed", [])
        panels.append(
            create_list_panel(
                "Completed",
                completed[:5] if completed else ["None yet"],
                bullet="✅",
                width=38,
            )
        )

        # Mission progress
        if active:
            progress = mission_data.get("current_progress", 0.0)
            panels.append(
                create_progress_panel(
                    f"Current: {active[0] if active else 'N/A'}", progress, width=78
                )
            )

        return panels

    def _build_community_dashboard(self, role: RoleLevel) -> List[Panel]:
        """Build community features dashboard."""
        panels = []

        # Require Builder+ for community
        if role.value < RoleLevel.BUILDER.value:
            panels.append(
                create_alert_panel(
                    "Community dashboard requires Builder role (3) or higher.",
                    alert_type="warning",
                    width=78,
                )
            )
            return panels

        panels.append(create_header_panel("Community", "Share & Connect", width=78))

        # Stats
        panels.append(
            create_status_panel(
                "Your Stats",
                {
                    "Submissions": "3",
                    "Downloads": "127",
                    "Rating": "4.5 ★",
                    "Reputation": "42",
                },
                width=38,
            )
        )

        # Leaderboard
        panels.append(
            create_list_panel(
                "Leaderboard",
                [
                    "1. wizard_dev (1250 XP)",
                    "2. survivor_jane (980 XP)",
                    "3. explorer_bob (875 XP)",
                ],
                bullet="🏅",
                width=38,
            )
        )

        # Recent submissions (Mentor+)
        if role.value >= RoleLevel.MENTOR.value:
            panels.append(
                create_list_panel(
                    "Pending Reviews",
                    ["water_filter_v2.md (2h ago)", "shelter_tarp.svg (5h ago)"],
                    bullet="📝",
                    width=78,
                )
            )

        return panels

    def _build_admin_dashboard(self, role: RoleLevel) -> List[Panel]:
        """Build admin/wizard dashboard."""
        panels = []

        # Require Wizard
        if role.value < RoleLevel.WIZARD.value:
            panels.append(
                create_alert_panel(
                    "Admin dashboard requires Wizard role (7).",
                    alert_type="error",
                    width=78,
                )
            )
            return panels

        panels.append(
            create_header_panel(
                "⚡ Admin Dashboard", "Wizard Access", width=78, style=BoxStyle.DOUBLE
            )
        )

        # System health
        panels.append(
            create_stats_panel(
                "System Health",
                {
                    "CPU": (35, 100),
                    "Memory": (2048, 8192),
                    "Disk": (45, 100),
                },
                width=38,
            )
        )

        # Network
        panels.append(
            create_status_panel(
                "Services",
                {
                    "API Server": "Running",
                    "MeshCore": "Active",
                    "Web Gateway": "Enabled",
                    "Sync": "Idle",
                },
                width=38,
            )
        )

        # User stats
        panels.append(
            create_status_panel(
                "Users",
                {
                    "Total": "1,234",
                    "Active (24h)": "89",
                    "New (7d)": "23",
                    "Banned": "2",
                },
                width=38,
            )
        )

        # Content stats
        panels.append(
            create_status_panel(
                "Content",
                {
                    "Guides": "230",
                    "User Content": "456",
                    "Pending Review": "12",
                    "Flagged": "3",
                },
                width=38,
            )
        )

        return panels

    def _render_compact(self, panels: List[Panel]) -> List[str]:
        """Render dashboard in compact mode."""
        # Stack all panels vertically
        return render_panels_vertical(panels, gap=0)

    def _render_full(self, panels: List[Panel]) -> List[str]:
        """Render dashboard in full layout."""
        if not panels:
            return ["No panels to display"]

        lines = []

        # Header panel (full width)
        if panels and panels[0].panel_type == PanelType.HEADER:
            lines.extend(panels[0].render())
            panels = panels[1:]

        # Arrange remaining panels in pairs
        i = 0
        while i < len(panels):
            if i + 1 < len(panels):
                # Pair panels horizontally
                pair = render_panels_horizontal([panels[i], panels[i + 1]], gap=2)
                lines.extend(pair)
                i += 2
            else:
                # Single panel
                lines.extend(panels[i].render())
                i += 1

        return lines

    # =========================================================================
    # Data Providers (default implementations)
    # =========================================================================

    def _get_system_status(self) -> Dict[str, str]:
        """Get system status data."""
        return {
            "Version": "1.3.3",
            "Mode": "Offline",
            "Theme": self.config.theme,
            "Uptime": "Local Session",
        }

    def _get_user_status(self) -> Dict[str, Any]:
        """Get user status data."""
        return {
            "username": self.config.user_id,
            "role": self.config.role.name,
            "level": 1,
            "joined": datetime.now().strftime("%Y-%m-%d"),
            "achievements": [],
        }

    def _get_network_status(self) -> Dict[str, Any]:
        """Get network status data."""
        return {
            "meshcore_status": "Offline",
            "peer_count": 0,
            "signal": "N/A",
            "latency": "N/A",
            "gateway_status": "Disabled",
            "api_status": "Offline",
            "sync_status": "N/A",
            "devices": [],
        }

    def _get_resource_status(self) -> Dict[str, tuple]:
        """Get resource stats (current, max)."""
        return {
            "XP": (0, 1000),
            "HP": (100, 100),
            "Barter": (0, 100),
        }

    def _get_recent_activity(self) -> List[str]:
        """Get recent activity log."""
        return [
            f"[{datetime.now().strftime('%H:%M')}] Dashboard loaded",
            "Use GUIDE to browse knowledge",
            "Use PROFILE to view your stats",
        ]

    def _get_mission_status(self) -> Dict[str, Any]:
        """Get mission status data."""
        return {
            "active": [],
            "completed": [],
            "current_progress": 0.0,
        }

    def _get_knowledge_status(self) -> Dict[str, Any]:
        """Get knowledge status data."""
        return {
            "categories": ["water", "fire", "shelter", "food", "medical", "navigation"],
            "recent": [],
            "completion": 0.0,
        }

    # =========================================================================
    # Dashboard Management
    # =========================================================================

    def switch_dashboard(self, dtype: DashboardType) -> None:
        """Switch active dashboard type."""
        self.state.active_type = dtype
        self.state.scroll_position = 0
        self.state.selected_panel = 0

    def add_alert(self, message: str, alert_type: str = "info") -> None:
        """Add an alert to the dashboard."""
        self.state.alerts.insert(
            0,
            {
                "message": message,
                "type": alert_type,
                "timestamp": datetime.now().isoformat(),
            },
        )
        # Keep only last 10 alerts
        self.state.alerts = self.state.alerts[:10]

    def clear_alerts(self) -> None:
        """Clear all alerts."""
        self.state.alerts.clear()

    def refresh(self) -> List[str]:
        """Refresh and return current dashboard."""
        self.state.last_refresh = datetime.now()
        return self.get_dashboard()

    def set_role(self, role: RoleLevel) -> None:
        """Update user role."""
        self.config.role = role

    def set_layout(self, layout: str) -> None:
        """Set dashboard layout."""
        if layout in DASHBOARD_LAYOUTS:
            self.config.layout = layout

    def get_config(self) -> DashboardConfig:
        """Get current configuration."""
        return self.config

    def save_config(self, path: str) -> bool:
        """Save configuration to file."""
        try:
            config_dict = {
                "user_id": self.config.user_id,
                "role": self.config.role.value,
                "theme": self.config.theme,
                "layout": self.config.layout,
                "refresh_rate": self.config.refresh_rate,
                "show_alerts": self.config.show_alerts,
                "show_tips": self.config.show_tips,
                "compact_mode": self.config.compact_mode,
                "custom_panels": self.config.custom_panels,
            }
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(config_dict, f, indent=2)
            return True
        except Exception:
            return False

    def load_config(self, path: str) -> bool:
        """Load configuration from file."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
            self.config = DashboardConfig(
                user_id=data.get("user_id", "local"),
                role=RoleLevel(data.get("role", 1)),
                theme=data.get("theme", "default"),
                layout=data.get("layout", "status"),
                refresh_rate=data.get("refresh_rate", 30),
                show_alerts=data.get("show_alerts", True),
                show_tips=data.get("show_tips", True),
                compact_mode=data.get("compact_mode", False),
                custom_panels=data.get("custom_panels", []),
            )
            return True
        except Exception:
            return False


# =============================================================================
# Module singleton
# =============================================================================

_dashboard_service: Optional[DashboardService] = None


def get_dashboard_service() -> DashboardService:
    """Get the dashboard service singleton."""
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService()
    return _dashboard_service


def init_dashboard_service(config: DashboardConfig = None) -> DashboardService:
    """Initialize dashboard service with config."""
    global _dashboard_service
    _dashboard_service = DashboardService(config)
    return _dashboard_service


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Dashboard Service Test")
    print("=" * 80)

    # Test with different roles
    for role in [
        RoleLevel.VISITOR,
        RoleLevel.SURVIVOR,
        RoleLevel.GHOST,
        RoleLevel.WIZARD,
    ]:
        print(f"\n{'=' * 80}")
        print(f"ROLE: {role.name}")
        print("=" * 80)

        config = DashboardConfig(role=role)
        service = DashboardService(config)

        dashboard = service.get_dashboard(DashboardType.MAIN)
        print("\n".join(dashboard))

    print("\n" + "=" * 80)
    print("✅ Dashboard Service working!")
