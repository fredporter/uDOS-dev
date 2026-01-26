"""
uDOS Viewport Manager
Handles screen size detection and 24x24 pixel cell grid system (v1.2.26)
"""

import os
import shutil
import json
from typing import Tuple, Dict, Any, Optional, List
from pathlib import Path


class ViewportManager:
    """Manages viewport calculations and screen size tier detection"""

    # Screen size reference table (14 tiers)
    SCREEN_SIZES = [
        {
            "tier": 0,
            "label": "Watch",
            "description": "Wearable display",
            "width_cells": 13,
            "height_cells": 13,
            "aspect": "1:1",
        },
        {
            "tier": 1,
            "label": "Mini Phone",
            "description": "Small smartphone",
            "width_cells": 20,
            "height_cells": 11,
            "aspect": "16:9",
        },
        {
            "tier": 2,
            "label": "Phone",
            "description": "Standard smartphone",
            "width_cells": 23,
            "height_cells": 11,
            "aspect": "19:9",
        },
        {
            "tier": 3,
            "label": "Big Phone",
            "description": "Large smartphone",
            "width_cells": 27,
            "height_cells": 12,
            "aspect": "20:9",
        },
        {
            "tier": 4,
            "label": "Compact Tab",
            "description": "Small tablet",
            "width_cells": 38,
            "height_cells": 25,
            "aspect": "3:2",
        },
        {
            "tier": 5,
            "label": "Wide Tab",
            "description": "Full-size tablet",
            "width_cells": 48,
            "height_cells": 36,
            "aspect": "4:3",
        },
        {
            "tier": 6,
            "label": "Small Notebook",
            "description": "Compact laptop",
            "width_cells": 64,
            "height_cells": 40,
            "aspect": "16:10",
        },
        {
            "tier": 7,
            "label": "Notebook",
            "description": "Standard laptop",
            "width_cells": 80,
            "height_cells": 45,
            "aspect": "16:9",
        },
        {
            "tier": 8,
            "label": "HD Display",
            "description": "Desktop monitor",
            "width_cells": 120,
            "height_cells": 68,
            "aspect": "16:9",
        },
        {
            "tier": 9,
            "label": "Wide Display",
            "description": "WQHD monitor",
            "width_cells": 160,
            "height_cells": 90,
            "aspect": "16:9",
        },
        {
            "tier": 10,
            "label": "Ultra Display",
            "description": "Ultrawide screen",
            "width_cells": 215,
            "height_cells": 92,
            "aspect": "21:9",
        },
        {
            "tier": 11,
            "label": "4K Screen",
            "description": "UHD display",
            "width_cells": 240,
            "height_cells": 135,
            "aspect": "16:9",
        },
        {
            "tier": 12,
            "label": "5K Screen",
            "description": "Retina display",
            "width_cells": 320,
            "height_cells": 180,
            "aspect": "16:9",
        },
        {
            "tier": 13,
            "label": "8K Wall",
            "description": "Large LED panel",
            "width_cells": 480,
            "height_cells": 270,
            "aspect": "16:9",
        },
        {
            "tier": 14,
            "label": "Cinema Scope",
            "description": "Projection stage",
            "width_cells": 360,
            "height_cells": 150,
            "aspect": "2.39:1",
        },
    ]

    CELL_SIZE = 24  # Each cell = 24x24 pixels (upgraded from 16x16 in v1.2.26)

    def __init__(self, settings_file: str = None):
        from dev.goblin.core.utils.paths import PATHS

        if settings_file is None:
            settings_file = str(PATHS.CORE_DATA / "viewport.json")
        self.settings_file = Path(settings_file)
        self.viewport_info = self.load_viewport_settings()

    def load_viewport_settings(self) -> Dict[str, Any]:
        """Load viewport settings from file or detect current"""
        # Always detect current terminal size (don't trust cache)
        current_size = self.get_terminal_size()

        if self.settings_file.exists():
            try:
                with open(self.settings_file) as f:
                    cached = json.load(f)
                    # Verify cached size matches current terminal
                    cached_chars = cached.get("terminal_chars", {})
                    if (
                        cached_chars.get("width") == current_size[0]
                        and cached_chars.get("height") == current_size[1]
                    ):
                        # Cache is valid, use it
                        return cached
            except Exception:
                pass

        # Cache miss or stale - auto-detect current size
        return self.detect_viewport()

    def save_viewport_settings(self) -> None:
        """Save current viewport settings to file"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, "w") as f:
                json.dump(self.viewport_info, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save viewport settings: {e}")

    def get_terminal_size(self) -> Tuple[int, int]:
        """Get current terminal size in characters"""
        try:
            size = shutil.get_terminal_size()
            return size.columns, size.lines
        except Exception:
            # Fallback to environment variables or default
            cols = int(os.getenv("COLUMNS", 80))
            lines = int(os.getenv("LINES", 24))
            return cols, lines

    def chars_to_cells(self, char_width: int, char_height: int) -> Tuple[int, int]:
        """Convert terminal character dimensions to grid cells.

        In uDOS, viewport is measured in CHARACTERS.
        Each terminal character = 1 grid unit (1:1 mapping).
        Grid cells are the displayable character positions.
        """
        # Direct 1:1 mapping - each terminal character is one grid cell
        cell_width = char_width  # 1 char = 1 grid cell horizontally
        cell_height = char_height  # 1 char = 1 grid cell vertically
        return cell_width, cell_height

    def cells_to_pixels(self, cell_width: int, cell_height: int) -> Tuple[int, int]:
        """Convert cell dimensions to pixel dimensions"""
        return cell_width * self.CELL_SIZE, cell_height * self.CELL_SIZE

    def find_nearest_screen_tier(
        self, width_cells: int, height_cells: int
    ) -> Dict[str, Any]:
        """Find the nearest screen size tier for given cell dimensions"""
        best_match = self.SCREEN_SIZES[7]  # Default to Notebook
        min_distance = float("inf")

        for screen in self.SCREEN_SIZES:
            # Calculate Euclidean distance in cell space
            distance = (
                (width_cells - screen["width_cells"]) ** 2
                + (height_cells - screen["height_cells"]) ** 2
            ) ** 0.5

            if distance < min_distance:
                min_distance = distance
                best_match = screen

        return {
            **best_match,
            "actual_width_cells": width_cells,
            "actual_height_cells": height_cells,
            "width_pixels": width_cells * self.CELL_SIZE,
            "height_pixels": height_cells * self.CELL_SIZE,
            "distance": min_distance,
        }

    def detect_viewport(self) -> Dict[str, Any]:
        """Auto-detect current viewport and find nearest screen tier"""
        char_width, char_height = self.get_terminal_size()
        cell_width, cell_height = self.chars_to_cells(char_width, char_height)

        screen_tier = self.find_nearest_screen_tier(cell_width, cell_height)

        viewport_info = {
            "detection_method": "auto",
            "terminal_chars": {"width": char_width, "height": char_height},
            "calculated_cells": {"width": cell_width, "height": cell_height},
            "screen_tier": screen_tier,
            "orientation": "horizontal" if char_width > char_height else "vertical",
            "last_updated": "auto-detect",
        }

        return viewport_info

    def set_custom_viewport(
        self, width_cells: int, height_cells: int
    ) -> Dict[str, Any]:
        """Set custom viewport dimensions"""
        screen_tier = self.find_nearest_screen_tier(width_cells, height_cells)

        self.viewport_info = {
            "detection_method": "manual",
            "terminal_chars": {"width": "custom", "height": "custom"},
            "calculated_cells": {"width": width_cells, "height": height_cells},
            "screen_tier": screen_tier,
            "last_updated": "manual_override",
        }

        self.save_viewport_settings()
        return self.viewport_info

    def get_viewport_info(self) -> Dict[str, Any]:
        """Get current viewport information"""
        return self.viewport_info

    @property
    def current_width(self) -> int:
        """Get current viewport width in cells"""
        return self.viewport_info["calculated_cells"]["width"]

    @property
    def current_height(self) -> int:
        """Get current viewport height in cells"""
        return self.viewport_info["calculated_cells"]["height"]

    @property
    def current_tier(self) -> int:
        """Get current screen tier"""
        return self.viewport_info["screen_tier"]["tier"]

    @property
    def current_label(self) -> str:
        """Get current screen tier label"""
        return self.viewport_info["screen_tier"]["label"]

    def get_nearest_tier(self, width_cells: int, height_cells: int) -> Tuple[int, str]:
        """Get nearest tier for given dimensions (convenience method)"""
        screen_tier = self.find_nearest_screen_tier(width_cells, height_cells)
        return screen_tier["tier"], screen_tier["label"]

    def get_screen_tier_list(self) -> List[Dict[str, Any]]:
        """Get list of all available screen tiers"""
        return self.SCREEN_SIZES.copy()

    def get_viewport_summary(self) -> str:
        """Get human-readable viewport summary"""
        info = self.viewport_info
        tier = info["screen_tier"]

        summary = f"""
🖥️  Viewport: {tier['label']} (Tier {tier['tier']})
📐 Dimensions: {tier['actual_width_cells']}×{tier['actual_height_cells']} cells
📏 Pixels: {tier['width_pixels']}×{tier['height_pixels']}px
📺 Aspect: {tier['aspect']} - {tier['description']}
🔍 Detection: {info['detection_method']}
"""

        if info["detection_method"] == "auto":
            summary += f"🖼️  Terminal: {info['terminal_chars']['width']}×{info['terminal_chars']['height']} chars\n"

        if tier.get("distance", 0) > 0:
            summary += f"📊 Match Distance: {tier['distance']:.1f} cells\n"

        return summary.strip()

    def refresh_viewport(self) -> Dict[str, Any]:
        """Refresh viewport detection (for REBOOT command)"""
        if self.viewport_info.get("detection_method") == "auto":
            # Re-detect automatically
            self.viewport_info = self.detect_viewport()
            self.save_viewport_settings()

        return self.viewport_info

    def get_size_comparison_chart(self) -> str:
        """Generate visual size comparison chart"""
        current_tier = self.viewport_info["screen_tier"]["tier"]

        chart = "📏 Screen Size Comparison (relative width):\n\n"

        for screen in self.SCREEN_SIZES:
            # Calculate relative bar length (max 40 chars)
            max_width = max(s["width_cells"] for s in self.SCREEN_SIZES)
            bar_length = int((screen["width_cells"] / max_width) * 40)
            bar = "█" * bar_length

            # Mark current tier
            marker = "👉 " if screen["tier"] == current_tier else "   "

            chart += f"{marker}{screen['label']:15s}: {bar}\n"

        return chart
