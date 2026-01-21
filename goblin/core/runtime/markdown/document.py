"""
UDOS Document Model

Represents parsed .udos.md document structure.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class UDOSDocument:
    """
    Parsed .udos.md document.

    Structure:
        ---
        title: Document Title
        author: Author Name
        permissions: [read, write, execute]
        ---

        # Markdown Content

        Regular markdown text here.

        ```upy
        # Embedded uPY script
        FILE.NEW(name="output.txt")
        ```

        ```state
        {
            "counter": 0,
            "last_run": "2026-01-04"
        }
        ```
    """

    # Metadata (from YAML frontmatter)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Content sections
    markdown_content: str = ""

    # Embedded scripts
    upy_scripts: List[Dict[str, Any]] = field(default_factory=list)

    # State blocks
    state_blocks: List[Dict[str, Any]] = field(default_factory=list)

    # Map tiles (ASCII grid representations)
    map_tiles: List[Dict[str, Any]] = field(default_factory=list)

    # Raw content
    raw_content: str = ""

    @property
    def title(self) -> Optional[str]:
        """Get document title from metadata."""
        return self.metadata.get("title")

    @property
    def author(self) -> Optional[str]:
        """Get document author from metadata."""
        return self.metadata.get("author")

    @property
    def permissions(self) -> List[str]:
        """Get document permissions from metadata."""
        return self.metadata.get("permissions", [])

    @property
    def tags(self) -> List[str]:
        """Get document tags from metadata."""
        return self.metadata.get("tags", [])

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get value from state blocks.

        Args:
            key: State key
            default: Default value if not found

        Returns:
            State value or default
        """
        for state_block in self.state_blocks:
            if key in state_block.get("data", {}):
                return state_block["data"][key]
        return default

    def set_state(self, key: str, value: Any) -> None:
        """
        Set value in first state block (or create new one).

        Args:
            key: State key
            value: State value
        """
        if not self.state_blocks:
            self.state_blocks.append({"line": -1, "data": {}})

        self.state_blocks[0]["data"][key] = value

    def to_markdown(self) -> str:
        """
        Serialize document back to .udos.md format.

        Returns:
            Markdown string with frontmatter, content, scripts, and state
        """
        lines = []

        # YAML frontmatter
        if self.metadata:
            import yaml

            lines.append("---")
            lines.append(yaml.dump(self.metadata, default_flow_style=False).strip())
            lines.append("---")
            lines.append("")

        # Markdown content
        lines.append(self.markdown_content.strip())

        # uPY scripts
        for script in self.upy_scripts:
            lines.append("")
            lines.append("```upy")
            lines.append(script.get("code", "").strip())
            lines.append("```")

        # State blocks
        for state in self.state_blocks:
            lines.append("")
            lines.append("```state")
            import json

            lines.append(json.dumps(state.get("data", {}), indent=2))
            lines.append("```")

        # Map tiles
        for tile in self.map_tiles:
            lines.append("")
            lines.append(f"```map")

            # Add metadata line if present
            metadata = tile.get("metadata", {})
            if (
                metadata
                or tile.get("tile_code")
                or tile.get("name")
                or tile.get("zone")
            ):
                meta_parts = []
                if tile.get("tile_code"):
                    meta_parts.append(f"TILE:{tile['tile_code']}")
                if tile.get("name"):
                    meta_parts.append(f"NAME:{tile['name']}")
                if tile.get("zone"):
                    meta_parts.append(f"ZONE:{tile['zone']}")
                # Add any additional metadata
                for k, v in metadata.items():
                    if k not in ["tile", "name", "zone"]:
                        meta_parts.append(f"{k.upper()}:{v}")
                if meta_parts:
                    lines.append(" ".join(meta_parts))

            lines.append(tile.get("ascii", "").strip())
            lines.append("```")

        return "\n".join(lines)
