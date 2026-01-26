"""
.udos.md Parser

Parses unified Markdown format with YAML frontmatter, uPY scripts, and state blocks.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .document import UDOSDocument


class ParseError(Exception):
    """Raised when parsing .udos.md fails."""

    pass


class UDOSMarkdownParser:
    """
    Parser for .udos.md unified Markdown format.

    Extracts:
    - YAML frontmatter (metadata)
    - Markdown content
    - uPY script blocks (```upy)
    - State blocks (```state with JSON)
    """

    def __init__(self):
        """Initialize parser."""
        self.frontmatter_pattern = re.compile(
            r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL | re.MULTILINE
        )

        self.code_block_pattern = re.compile(r"```(\w+)\s*\n(.*?)\n```", re.DOTALL)

    def parse(self, content: str) -> UDOSDocument:
        """
        Parse .udos.md content.

        Args:
            content: Raw .udos.md file content

        Returns:
            UDOSDocument with parsed components

        Raises:
            ParseError: If parsing fails
        """
        doc = UDOSDocument(raw_content=content)

        # Extract frontmatter
        remaining_content = content
        frontmatter_match = self.frontmatter_pattern.match(content)

        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            doc.metadata = self._parse_frontmatter(frontmatter_text)
            remaining_content = content[frontmatter_match.end() :]

        # Extract code blocks (uPY scripts and state blocks)
        code_blocks = []
        for match in self.code_block_pattern.finditer(remaining_content):
            lang = match.group(1).lower()
            code = match.group(2)
            line_num = content[: match.start()].count("\n") + 1

            code_blocks.append(
                {
                    "lang": lang,
                    "code": code,
                    "line": line_num,
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # Remove code blocks to get pure markdown
        markdown_content = remaining_content
        for block in reversed(code_blocks):  # Reverse to maintain positions
            markdown_content = (
                markdown_content[: block["start"]] + markdown_content[block["end"] :]
            )

        doc.markdown_content = markdown_content.strip()

        # Categorize code blocks
        for block in code_blocks:
            if block["lang"] == "upy":
                doc.upy_scripts.append(
                    {
                        "code": block["code"],
                        "line": block["line"],
                    }
                )
            elif block["lang"] == "state":
                try:
                    state_data = json.loads(block["code"])
                    doc.state_blocks.append(
                        {
                            "data": state_data,
                            "line": block["line"],
                        }
                    )
                except json.JSONDecodeError as e:
                    raise ParseError(
                        f"Invalid JSON in state block at line {block['line']}: {e}"
                    )
            elif block["lang"] == "map":
                # Parse map tile metadata from first line if present (TILE:code format)
                tile_data = self._parse_map_block(block["code"], block["line"])
                doc.map_tiles.append(tile_data)

        return doc

    def _parse_map_block(self, ascii_content: str, line_num: int) -> Dict[str, Any]:
        """
        Parse map block with optional metadata.

        Format:
            TILE:AB12 NAME:Location ZONE:timezone
            [ASCII art follows]

        Args:
            ascii_content: Map block content
            line_num: Line number in source

        Returns:
            Map tile data dict
        """
        lines = ascii_content.split("\n")
        metadata = {}
        ascii_start = 0

        # Check if first line contains metadata
        if lines and ":" in lines[0] and not lines[0].strip().startswith("│"):
            # Parse metadata line
            first_line = lines[0].strip()
            for part in first_line.split():
                if ":" in part:
                    key, value = part.split(":", 1)
                    metadata[key.lower()] = value
            ascii_start = 1

        # Get ASCII content
        ascii_art = "\n".join(lines[ascii_start:]).strip()

        return {
            "ascii": ascii_art,
            "metadata": metadata,
            "tile_code": metadata.get("tile", ""),
            "name": metadata.get("name", ""),
            "zone": metadata.get("zone", ""),
            "line": line_num,
        }

    def _parse_frontmatter(self, text: str) -> Dict[str, Any]:
        """
        Parse YAML frontmatter.

        Args:
            text: YAML text

        Returns:
            Parsed metadata dict

        Raises:
            ParseError: If YAML parsing fails
        """
        if not YAML_AVAILABLE:
            # Fallback to simple key: value parsing
            return self._parse_simple_frontmatter(text)

        try:
            return yaml.safe_load(text) or {}
        except yaml.YAMLError as e:
            raise ParseError(f"Invalid YAML frontmatter: {e}")

    def _parse_simple_frontmatter(self, text: str) -> Dict[str, Any]:
        """
        Simple key: value parser (fallback if PyYAML not available).

        Args:
            text: Frontmatter text

        Returns:
            Parsed metadata dict
        """
        metadata = {}

        for line in text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Try to parse as JSON for lists/objects
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    pass

                metadata[key] = value

        return metadata

    def parse_file(self, filepath: str) -> UDOSDocument:
        """
        Parse .udos.md file.

        Args:
            filepath: Path to .udos.md file

        Returns:
            Parsed UDOSDocument

        Raises:
            ParseError: If file cannot be read or parsed
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return self.parse(content)
        except IOError as e:
            raise ParseError(f"Cannot read file {filepath}: {e}")
