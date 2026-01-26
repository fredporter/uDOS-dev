"""
Template System for uDOS
Replaces the deprecated theme system with user-editable markdown templates.

Version: 1.0.1
Created: 2026-01-06
Updated: 2026-01-07 - Added LayerTheme mapping for dimensional templates

Layer Theme Mapping:
- Surface (0): Default Earth themes
- Dungeon (-1 to -10): Fantasy RPG underground
- Upside Down (-11 to -100): Stranger Things "The Upside Down"
- Space Humor (1 to 100): Hitchhiker's Guide style
- Space Serious (101+): Foundation/serious sci-fi
"""

import re
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("system-template")


class LayerTheme(Enum):
    """
    Map layer theme categories for dimensional templates.

    Layer ID ranges map to themed content:
    - Negative = underground/subterranean
    - Zero = surface/Earth
    - Positive = sky/space
    """

    SURFACE = "surface"  # Earth, default (layer 0)
    DUNGEON = "dungeon"  # Fantasy RPG underground (-1 to -10)
    UPSIDE_DOWN = "upside_down"  # Stranger Things subterranean (-11 to -100)
    SPACE_HUMOR = "space_humor"  # Hitchhiker's Guide style (1 to 100)
    SPACE_SERIOUS = "space_serious"  # Foundation, serious sci-fi (101+)


# Layer ID to theme mapping ranges
LAYER_THEME_RANGES: Dict[LayerTheme, Tuple[int, int]] = {
    LayerTheme.SURFACE: (0, 0),
    LayerTheme.DUNGEON: (-10, -1),
    LayerTheme.UPSIDE_DOWN: (-100, -11),
    LayerTheme.SPACE_HUMOR: (1, 100),
    LayerTheme.SPACE_SERIOUS: (101, 10000),
}


def layer_to_theme(layer_id: int) -> LayerTheme:
    """Map a layer ID to its theme category."""
    for theme, (min_id, max_id) in LAYER_THEME_RANGES.items():
        if min_id <= layer_id <= max_id:
            return theme

    # Default based on sign for out-of-range values
    if layer_id < 0:
        return LayerTheme.UPSIDE_DOWN
    elif layer_id > 0:
        return LayerTheme.SPACE_SERIOUS
    return LayerTheme.SURFACE


@dataclass
class TemplateData:
    """Parsed template data."""

    # Identity
    name: str = "Default System"
    style: str = "Standard uDOS"
    icon: str = "💻"
    description: str = "Clean, straightforward uDOS system responses"

    # Layer theme (for dimensional templates)
    layer_theme: Optional[LayerTheme] = None

    # Prompts
    prompt_base: str = ">"
    prompt_continuation: str = "..."
    prompt_script: str = "#"
    prompt_debug: str = "?"

    # Terminology (command aliases)
    terminology: Dict[str, str] = field(default_factory=dict)

    # Messages (error, info, success patterns)
    messages: Dict[str, str] = field(default_factory=dict)

    # Status indicators
    status_indicators: Dict[str, str] = field(default_factory=dict)

    # Log tags
    log_tags: Dict[str, str] = field(default_factory=dict)

    # AI prompts (for themed generation)
    ai_prompts: Dict[str, str] = field(default_factory=dict)


class TemplateLoader:
    """
    Load and parse udos.template.md files.

    Replaces ThemeLoader with markdown-based templates.
    Supports layer-themed templates for dimensional content.
    """

    # Default locations to search for templates
    DEFAULT_PATHS = [
        "memory/templates/udos.template.md",  # User custom
        "core/data/templates/udos.template.md",  # System default
    ]

    # Layer-themed template paths
    LAYER_TEMPLATE_PATHS = {
        LayerTheme.SURFACE: "core/data/templates/surface.template.md",
        LayerTheme.DUNGEON: "core/data/templates/dungeon.template.md",
        LayerTheme.UPSIDE_DOWN: "core/data/templates/upside-down.template.md",
        LayerTheme.SPACE_HUMOR: "core/data/templates/hitchhikers.template.md",
        LayerTheme.SPACE_SERIOUS: "core/data/templates/foundation.template.md",
    }

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize template loader."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self._template_data: Optional[TemplateData] = None
        self._raw_content: str = ""
        self._sections: Dict[str, str] = {}

        # Layer template cache
        self._layer_templates: Dict[LayerTheme, TemplateData] = {}

    def load(self, template_path: Optional[str] = None) -> TemplateData:
        """
        Load template from file.

        Args:
            template_path: Optional specific path, otherwise searches DEFAULT_PATHS

        Returns:
            TemplateData with parsed values
        """
        path = self._find_template(template_path)

        if not path:
            logger.warning("[LOCAL] No template found, using defaults")
            self._template_data = TemplateData()
            self._apply_defaults()
            return self._template_data

        try:
            self._raw_content = path.read_text(encoding="utf-8")
            self._parse_sections()
            self._template_data = self._build_template_data()
            logger.info(f"[LOCAL] Loaded template: {path.name}")
            return self._template_data

        except Exception as e:
            logger.error(f"[ERROR] Template load failed: {e}")
            self._template_data = TemplateData()
            self._apply_defaults()
            return self._template_data

    def _find_template(self, specific_path: Optional[str]) -> Optional[Path]:
        """Find template file from paths."""
        if specific_path:
            path = Path(specific_path)
            if not path.is_absolute():
                path = self.project_root / path
            if path.exists():
                return path
            logger.warning(f"[LOCAL] Template not found: {specific_path}")

        # Search default paths
        for rel_path in self.DEFAULT_PATHS:
            path = self.project_root / rel_path
            if path.exists():
                return path

        return None

    def _parse_sections(self):
        """Parse markdown into sections by ## headers."""
        self._sections = {}
        current_section = "preamble"
        current_content = []

        for line in self._raw_content.split("\n"):
            if line.startswith("## "):
                # Save previous section
                if current_content:
                    self._sections[current_section] = "\n".join(current_content)
                # Start new section
                current_section = line[3:].strip().lower()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            self._sections[current_section] = "\n".join(current_content)

    def _build_template_data(self) -> TemplateData:
        """Build TemplateData from parsed sections."""
        data = TemplateData()

        # Parse Identity section
        if "identity" in self._sections:
            identity = self._parse_key_values(self._sections["identity"])
            data.name = identity.get("name", data.name)
            data.style = identity.get("style", data.style)
            data.icon = identity.get("icon", data.icon)
            data.description = identity.get("description", data.description)

        # Parse Prompt section
        if "prompt" in self._sections:
            prompts = self._parse_key_values(self._sections["prompt"])
            data.prompt_base = prompts.get("base", data.prompt_base)
            data.prompt_continuation = prompts.get(
                "continuation", data.prompt_continuation
            )
            data.prompt_script = prompts.get("script", data.prompt_script)
            data.prompt_debug = prompts.get("debug", data.prompt_debug)

        # Parse Terminology table
        if "terminology" in self._sections:
            data.terminology = self._parse_table(
                self._sections["terminology"], "Key", "Default"
            )

        # Parse Messages section (code blocks with names)
        if "messages" in self._sections:
            data.messages = self._parse_named_code_blocks(self._sections["messages"])

        # Parse Status Indicators table
        if "status indicators" in self._sections:
            data.status_indicators = self._parse_table(
                self._sections["status indicators"], "Status", "Symbol"
            )

        # Parse Log Tags table
        if "log tags" in self._sections:
            data.log_tags = self._parse_table(
                self._sections["log tags"], "Tag", "Context"
            )

        self._apply_defaults(data)
        return data

    def _parse_key_values(self, content: str) -> Dict[str, str]:
        """Parse **key:** value patterns."""
        result = {}
        pattern = r"\*\*(\w+):\*\*\s*(.+?)(?=\n\*\*|\n\n|$)"

        for match in re.finditer(pattern, content, re.DOTALL):
            key = match.group(1).lower()
            value = match.group(2).strip()
            result[key] = value

        return result

    def _parse_table(
        self, content: str, key_col: str, value_col: str
    ) -> Dict[str, str]:
        """Parse markdown table into dict."""
        result = {}
        lines = content.strip().split("\n")

        # Find header row
        header_idx = -1
        key_idx = -1
        value_idx = -1

        for i, line in enumerate(lines):
            if "|" in line and key_col in line:
                cols = [c.strip() for c in line.split("|")]
                try:
                    key_idx = cols.index(key_col)
                    value_idx = cols.index(value_col)
                    header_idx = i
                    break
                except ValueError:
                    continue

        if header_idx < 0:
            return result

        # Parse data rows (skip header and separator)
        for line in lines[header_idx + 2 :]:
            if "|" not in line or line.strip().startswith("|--"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) > max(key_idx, value_idx):
                key = cols[key_idx]
                value = cols[value_idx]
                if key and not key.startswith("-"):
                    result[key] = value

        return result

    def _parse_named_code_blocks(self, content: str) -> Dict[str, str]:
        """Parse **NAME:** followed by code block."""
        result = {}

        # Pattern: **NAME:** followed by ``` block
        pattern = r"\*\*(\w+):\*\*\s*```[^\n]*\n(.*?)```"

        for match in re.finditer(pattern, content, re.DOTALL):
            name = match.group(1).upper()
            value = match.group(2).strip()
            result[name] = value

        return result

    def _apply_defaults(self, data: Optional[TemplateData] = None):
        """Apply default values for missing entries."""
        if data is None:
            data = self._template_data

        # Default terminology
        default_terminology = {
            "CMD_CATALOG": "CATALOG",
            "CMD_LOAD": "LOAD",
            "CMD_SAVE": "SAVE",
            "CMD_RUN": "RUN",
            "CMD_CLS": "CLS",
            "CMD_HELP": "HELP",
            "CMD_MAP": "MAP",
            "CMD_EDIT": "EDIT",
            "CMD_EXIT": "EXIT",
            "CMD_REBOOT": "REBOOT",
            "CMD_REPAIR": "REPAIR",
        }
        for key, value in default_terminology.items():
            if key not in data.terminology:
                data.terminology[key] = value

        # Default messages
        default_messages = {
            "ERROR_CRASH": "ERROR: Command '{{command}}' failed unexpectedly",
            "ERROR_INVALID_FORMAT": "ERROR: Invalid format '{{input}}' - {{error}}",
            "ERROR_UNKNOWN_MODULE": "ERROR: Unknown module '{{module}}'",
            "ERROR_UNKNOWN_COMMAND": "ERROR: Unknown command '{{command}}'",
            "ERROR_FILE_NOT_FOUND": "ERROR: File not found '{{filename}}'",
            "ERROR_GENERIC": "ERROR: {{error}}",
            "INFO_EXIT": "Goodbye! uDOS session terminated.",
            "INFO_HELP_INTRO": "Available commands:",
            "SUCCESS_GENERIC": "Operation completed successfully",
        }
        for key, value in default_messages.items():
            if key not in data.messages:
                data.messages[key] = value

        # Default status indicators
        default_status = {
            "OK": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "INFO": "ℹ️",
            "PROGRESS": "⏳",
        }
        for key, value in default_status.items():
            if key not in data.status_indicators:
                data.status_indicators[key] = value

    def get_message(self, key: str, **kwargs) -> str:
        """
        Get a message with variable substitution.

        Args:
            key: Message key (e.g., 'ERROR_CRASH')
            **kwargs: Variables to substitute (e.g., command='FOO')

        Returns:
            Formatted message string
        """
        if not self._template_data:
            self.load()

        template = self._template_data.messages.get(key, f"[{key}]")

        # Substitute {{variable}} patterns
        for var_name, var_value in kwargs.items():
            template = template.replace(f"{{{{{var_name}}}}}", str(var_value))

        return template

    def get_terminology(self, key: str) -> str:
        """Get terminology value."""
        if not self._template_data:
            self.load()
        return self._template_data.terminology.get(key, key)

    def get_prompt(self) -> str:
        """Get the base prompt string."""
        if not self._template_data:
            self.load()
        return self._template_data.prompt_base

    def get_status_icon(self, status: str) -> str:
        """Get status indicator icon."""
        if not self._template_data:
            self.load()
        return self._template_data.status_indicators.get(status.upper(), "•")

    @property
    def data(self) -> TemplateData:
        """Get loaded template data."""
        if not self._template_data:
            self.load()
        return self._template_data

    # === Layer Theme Methods ===

    def get_for_layer(self, layer_id: int) -> TemplateData:
        """
        Get appropriate template for a map layer.

        Args:
            layer_id: Map layer ID (negative=underground, positive=sky/space)

        Returns:
            TemplateData for the layer's theme
        """
        theme = layer_to_theme(layer_id)
        return self.get_layer_template(theme)

    def get_layer_template(self, theme: LayerTheme) -> TemplateData:
        """
        Get template for a specific layer theme.

        Args:
            theme: LayerTheme enum value

        Returns:
            TemplateData for the theme (cached)
        """
        # Check cache
        if theme in self._layer_templates:
            return self._layer_templates[theme]

        # Try to load themed template
        if theme in self.LAYER_TEMPLATE_PATHS:
            path = self.project_root / self.LAYER_TEMPLATE_PATHS[theme]
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8")
                    old_content = self._raw_content
                    old_sections = self._sections

                    self._raw_content = content
                    self._parse_sections()
                    template = self._build_template_data()
                    template.layer_theme = theme

                    # Restore state
                    self._raw_content = old_content
                    self._sections = old_sections

                    # Cache and return
                    self._layer_templates[theme] = template
                    logger.info(f"[LOCAL] Loaded layer template: {theme.value}")
                    return template

                except Exception as e:
                    logger.error(f"[ERROR] Layer template load failed: {e}")

        # Fallback to default template with theme set
        if not self._template_data:
            self.load()

        # Return copy with layer theme set
        fallback = TemplateData(
            name=self._template_data.name,
            style=self._template_data.style,
            icon=self._template_data.icon,
            description=self._template_data.description,
            layer_theme=theme,
            prompt_base=self._template_data.prompt_base,
            prompt_continuation=self._template_data.prompt_continuation,
            prompt_script=self._template_data.prompt_script,
            prompt_debug=self._template_data.prompt_debug,
            terminology=dict(self._template_data.terminology),
            messages=dict(self._template_data.messages),
            status_indicators=dict(self._template_data.status_indicators),
            log_tags=dict(self._template_data.log_tags),
            ai_prompts=dict(self._template_data.ai_prompts),
        )
        self._layer_templates[theme] = fallback
        return fallback

    def list_available_themes(self) -> Dict[str, bool]:
        """List all layer themes and whether their templates exist."""
        result = {}
        for theme in LayerTheme:
            if theme in self.LAYER_TEMPLATE_PATHS:
                path = self.project_root / self.LAYER_TEMPLATE_PATHS[theme]
                result[theme.value] = path.exists()
            else:
                result[theme.value] = False
        return result

    def get_ai_prompt(self, prompt_name: str, layer_id: int = 0) -> Optional[str]:
        """
        Get AI prompt for a specific action, themed by layer.

        Args:
            prompt_name: Name of the prompt (e.g., 'make_guide', 'make_do')
            layer_id: Current map layer for theming

        Returns:
            AI system prompt string or None
        """
        template = self.get_for_layer(layer_id)
        return template.ai_prompts.get(prompt_name)


# Global instance for easy access
_template_loader: Optional[TemplateLoader] = None


def get_template_loader(project_root: Optional[Path] = None) -> TemplateLoader:
    """Get or create global template loader."""
    global _template_loader
    if _template_loader is None:
        _template_loader = TemplateLoader(project_root)
        _template_loader.load()
    return _template_loader


def get_message(key: str, **kwargs) -> str:
    """Convenience function to get formatted message."""
    return get_template_loader().get_message(key, **kwargs)


def get_status_icon(status: str) -> str:
    """Convenience function to get status icon."""
    return get_template_loader().get_status_icon(status)


def get_template_for_layer(layer_id: int) -> TemplateData:
    """Get template for a specific map layer."""
    return get_template_loader().get_for_layer(layer_id)


def get_ai_prompt(prompt_name: str, layer_id: int = 0) -> Optional[str]:
    """Get AI prompt themed by layer."""
    return get_template_loader().get_ai_prompt(prompt_name, layer_id)


def list_layer_themes() -> Dict[str, bool]:
    """List available layer themes."""
    return get_template_loader().list_available_themes()


# Migration helper - maps old theme keys to new template keys
THEME_TO_TEMPLATE_MAP = {
    "ERROR_CRASH": "ERROR_CRASH",
    "ERROR_INVALID_UCODE_FORMAT": "ERROR_INVALID_FORMAT",
    "ERROR_UNKNOWN_MODULE": "ERROR_UNKNOWN_MODULE",
    "ERROR_UNKNOWN_SYSTEM_COMMAND": "ERROR_UNKNOWN_COMMAND",
    "ERROR_UNKNOWN_FILE_COMMAND": "ERROR_UNKNOWN_COMMAND",
    "ERROR_GENERIC": "ERROR_GENERIC",
    "INFO_EXIT": "INFO_EXIT",
    "INFO_HELP_INTRO": "INFO_HELP_INTRO",
    "INFO_REPAIR_RUNNING": "PROGRESS_START",
    "ACTION_SUCCESS": "SUCCESS_GENERIC",
    "ACTION_SUCCESS_REPAIR_COMPLETE": "SUCCESS_GENERIC",
}
