"""
JSON Viewer/Editor - TUI Mode

Enhanced terminal-based JSON browser and editor with tree navigation,
syntax highlighting, validation, and schema support.

Part of uDOS v1.2.31 - Editor Suite

Features:
- Tree view with expand/collapse
- Syntax highlighting by type
- Inline editing with validation
- JSON Schema validation
- Auto-backup before save
- Diff view for changes
- Search within JSON
- Path tracking (e.g., data.users[0].name)
- Undo/Redo support
- Copy value/path to clipboard

Keyboard Controls:
  Navigation: 8=↑  2=↓  4=←collapse  6=→expand
  Edit:       Enter=edit value  Del=delete key
  Expand:     Space=toggle  A=expand all  C=collapse all
  Search:     /=search  N=next match
  Undo/Redo:  7=undo  9=redo
  File:       Ctrl+S=save
  Exit:       Q or Esc
"""

import json
import copy
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from dev.goblin.core.ui.components.box_drawing import render_section, render_separator, BoxStyle


class JSONType(Enum):
    """JSON value types with display properties."""

    OBJECT = ("📦", "\033[33m")  # Yellow
    ARRAY = ("📋", "\033[35m")  # Magenta
    STRING = ("📝", "\033[32m")  # Green
    NUMBER = ("🔢", "\033[36m")  # Cyan
    BOOLEAN = ("✓", "\033[34m")  # Blue
    NULL = ("∅", "\033[90m")  # Gray

    @property
    def icon(self) -> str:
        return self.value[0]

    @property
    def color(self) -> str:
        return self.value[1]


@dataclass
class JSONTreeNode:
    """Node in the JSON tree structure."""

    key: str
    value: Any
    parent: Optional["JSONTreeNode"] = None
    children: List["JSONTreeNode"] = field(default_factory=list)
    expanded: bool = False
    depth: int = 0

    def __post_init__(self):
        """Build children from value."""
        if isinstance(self.value, dict):
            for k, v in self.value.items():
                child = JSONTreeNode(key=k, value=v, parent=self, depth=self.depth + 1)
                self.children.append(child)
        elif isinstance(self.value, list):
            for i, v in enumerate(self.value):
                child = JSONTreeNode(
                    key=f"[{i}]", value=v, parent=self, depth=self.depth + 1
                )
                self.children.append(child)

    @property
    def json_type(self) -> JSONType:
        """Get JSON type of value."""
        if isinstance(self.value, dict):
            return JSONType.OBJECT
        elif isinstance(self.value, list):
            return JSONType.ARRAY
        elif isinstance(self.value, str):
            return JSONType.STRING
        elif isinstance(self.value, bool):
            return JSONType.BOOLEAN
        elif isinstance(self.value, (int, float)):
            return JSONType.NUMBER
        elif self.value is None:
            return JSONType.NULL
        else:
            return JSONType.STRING

    @property
    def is_container(self) -> bool:
        """Check if node is a container (object or array)."""
        return isinstance(self.value, (dict, list))

    def get_path(self) -> str:
        """Get full JSON path to this node."""
        if self.parent is None:
            return self.key

        parent_path = self.parent.get_path()
        if self.key.startswith("["):
            return f"{parent_path}{self.key}"
        else:
            return f"{parent_path}.{self.key}" if parent_path else self.key

    def get_display_value(self, max_len: int = 50) -> str:
        """Get formatted display value."""
        if isinstance(self.value, dict):
            return f"{{ {len(self.value)} keys }}"
        elif isinstance(self.value, list):
            return f"[ {len(self.value)} items ]"
        elif isinstance(self.value, str):
            if len(self.value) > max_len:
                return f'"{self.value[:max_len-3]}..."'
            return f'"{self.value}"'
        elif isinstance(self.value, bool):
            return "true" if self.value else "false"
        elif self.value is None:
            return "null"
        else:
            return str(self.value)

    def toggle_expand(self):
        """Toggle expansion state."""
        if self.is_container:
            self.expanded = not self.expanded

    def expand_all(self):
        """Expand this node and all children."""
        if self.is_container:
            self.expanded = True
            for child in self.children:
                child.expand_all()

    def collapse_all(self):
        """Collapse this node and all children."""
        if self.is_container:
            self.expanded = False
            for child in self.children:
                child.collapse_all()


@dataclass
class EditorState:
    """State for undo/redo."""

    data: Dict
    cursor_path: str
    timestamp: str


class JSONTreeViewer:
    """Enhanced JSON viewer/editor for TUI mode."""

    # ANSI codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    INVERT = "\033[7m"

    def __init__(self, config=None):
        self.config = config
        self.project_root = Path(config.project_root) if config else Path.cwd()

        # Data state
        self.current_file: Optional[str] = None
        self.original_data: Optional[Dict] = None
        self.current_data: Optional[Dict] = None
        self.root: Optional[JSONTreeNode] = None

        # Navigation state
        self.cursor: Optional[JSONTreeNode] = None
        self.scroll_offset = 0
        self.viewport_height = 20

        # Edit state
        self.undo_stack: List[EditorState] = []
        self.redo_stack: List[EditorState] = []
        self.modified = False

        # Search state
        self.search_query = ""
        self.search_matches: List[JSONTreeNode] = []
        self.search_index = 0

        # UI state
        self.message = ""
        self.editing = False
        self.edit_buffer = ""

        # Schema
        self.schema: Optional[Dict] = None

    def load_file(self, filepath: str) -> Tuple[bool, str]:
        """Load JSON file."""
        try:
            # Resolve path
            if not os.path.isabs(filepath):
                filepath = self.project_root / filepath

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.current_file = str(filepath)
            self.original_data = copy.deepcopy(data)
            self.current_data = data

            # Build tree
            filename = Path(filepath).name
            self.root = JSONTreeNode(key=filename, value=data)
            self.root.expanded = True
            self.cursor = self.root

            # Clear state
            self.undo_stack = []
            self.redo_stack = []
            self.modified = False
            self.scroll_offset = 0

            return True, f"✅ Loaded: {filepath}"

        except FileNotFoundError:
            return False, f"❌ File not found: {filepath}"
        except json.JSONDecodeError as e:
            return False, f"❌ Invalid JSON at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"❌ Error: {e}"

    def load_string(self, json_string: str, name: str = "data") -> Tuple[bool, str]:
        """Load JSON from string."""
        try:
            data = json.loads(json_string)

            self.current_file = None
            self.original_data = copy.deepcopy(data)
            self.current_data = data

            self.root = JSONTreeNode(key=name, value=data)
            self.root.expanded = True
            self.cursor = self.root

            self.undo_stack = []
            self.redo_stack = []
            self.modified = False
            self.scroll_offset = 0

            return True, "✅ JSON loaded"

        except json.JSONDecodeError as e:
            return False, f"❌ Invalid JSON: {e.msg}"
        except Exception as e:
            return False, f"❌ Error: {e}"

    def load_schema(self, schema_path: str) -> Tuple[bool, str]:
        """Load JSON Schema for validation."""
        try:
            with open(schema_path, "r") as f:
                self.schema = json.load(f)
            return True, f"✅ Schema loaded: {schema_path}"
        except Exception as e:
            return False, f"❌ Schema error: {e}"

    def _save_state(self):
        """Save current state for undo."""
        if self.current_data is None:
            return

        state = EditorState(
            data=copy.deepcopy(self.current_data),
            cursor_path=self.cursor.get_path() if self.cursor else "",
            timestamp=datetime.now().isoformat(),
        )
        self.undo_stack.append(state)
        self.redo_stack.clear()

        # Limit stack size
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)

    def undo(self) -> bool:
        """Undo last change."""
        if not self.undo_stack:
            self.message = "Nothing to undo"
            return False

        # Save current to redo
        current_state = EditorState(
            data=copy.deepcopy(self.current_data),
            cursor_path=self.cursor.get_path() if self.cursor else "",
            timestamp=datetime.now().isoformat(),
        )
        self.redo_stack.append(current_state)

        # Restore previous
        state = self.undo_stack.pop()
        self.current_data = state.data
        self._rebuild_tree()

        self.message = "Undo"
        return True

    def redo(self) -> bool:
        """Redo undone change."""
        if not self.redo_stack:
            self.message = "Nothing to redo"
            return False

        # Save current to undo
        current_state = EditorState(
            data=copy.deepcopy(self.current_data),
            cursor_path=self.cursor.get_path() if self.cursor else "",
            timestamp=datetime.now().isoformat(),
        )
        self.undo_stack.append(current_state)

        # Restore redo
        state = self.redo_stack.pop()
        self.current_data = state.data
        self._rebuild_tree()

        self.message = "Redo"
        return True

    def _rebuild_tree(self):
        """Rebuild tree from current_data."""
        if self.current_data is None:
            return

        name = Path(self.current_file).name if self.current_file else "data"
        self.root = JSONTreeNode(key=name, value=self.current_data)
        self.root.expanded = True
        self.cursor = self.root

    def _get_visible_nodes(self) -> List[JSONTreeNode]:
        """Get list of all visible nodes in order."""
        if not self.root:
            return []

        visible = []
        self._collect_visible(self.root, visible)
        return visible

    def _collect_visible(self, node: JSONTreeNode, visible: List[JSONTreeNode]):
        """Recursively collect visible nodes."""
        visible.append(node)

        if node.expanded and node.children:
            for child in node.children:
                self._collect_visible(child, visible)

    def navigate_up(self) -> bool:
        """Move cursor up."""
        if not self.root:
            return False

        visible = self._get_visible_nodes()
        try:
            idx = visible.index(self.cursor)
            if idx > 0:
                self.cursor = visible[idx - 1]
                self._ensure_cursor_visible()
                return True
        except ValueError:
            pass
        return False

    def navigate_down(self) -> bool:
        """Move cursor down."""
        if not self.root:
            return False

        visible = self._get_visible_nodes()
        try:
            idx = visible.index(self.cursor)
            if idx < len(visible) - 1:
                self.cursor = visible[idx + 1]
                self._ensure_cursor_visible()
                return True
        except ValueError:
            pass
        return False

    def _ensure_cursor_visible(self):
        """Adjust scroll to keep cursor visible."""
        if not self.cursor:
            return

        visible = self._get_visible_nodes()
        try:
            idx = visible.index(self.cursor)

            # Scroll up if cursor above viewport
            if idx < self.scroll_offset:
                self.scroll_offset = idx

            # Scroll down if cursor below viewport
            elif idx >= self.scroll_offset + self.viewport_height:
                self.scroll_offset = idx - self.viewport_height + 1
        except ValueError:
            pass

    def expand(self):
        """Expand current node."""
        if self.cursor and self.cursor.is_container:
            self.cursor.expanded = True

    def collapse(self):
        """Collapse current node or go to parent."""
        if self.cursor:
            if self.cursor.expanded and self.cursor.is_container:
                self.cursor.expanded = False
            elif self.cursor.parent:
                self.cursor = self.cursor.parent

    def toggle_expand(self):
        """Toggle expansion."""
        if self.cursor:
            self.cursor.toggle_expand()

    def expand_all(self):
        """Expand all nodes."""
        if self.root:
            self.root.expand_all()
            self.message = "Expanded all"

    def collapse_all(self):
        """Collapse all nodes."""
        if self.root:
            for child in self.root.children:
                child.collapse_all()
            self.message = "Collapsed all"

    def edit_value(self, new_value_str: str) -> Tuple[bool, str]:
        """Edit value at cursor."""
        if not self.cursor or self.cursor == self.root:
            return False, "Cannot edit root"

        if self.cursor.is_container:
            return False, "Cannot edit container (edit children)"

        try:
            self._save_state()

            # Parse new value
            new_value = self._parse_value(new_value_str)
            old_value = self.cursor.value

            # Update in tree
            self.cursor.value = new_value

            # Update in data structure
            self._update_data_at_path(self.cursor.get_path(), new_value)

            self.modified = True
            return True, f"Updated: {old_value} → {new_value}"

        except Exception as e:
            return False, f"Error: {e}"

    def _parse_value(self, value_str: str) -> Any:
        """Parse string to JSON value."""
        value_str = value_str.strip()

        # Try JSON parsing
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            pass

        # Handle quotes
        if (value_str.startswith('"') and value_str.endswith('"')) or (
            value_str.startswith("'") and value_str.endswith("'")
        ):
            return value_str[1:-1]

        # Try number
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # Boolean/null
        if value_str.lower() in ("true", "yes"):
            return True
        if value_str.lower() in ("false", "no"):
            return False
        if value_str.lower() in ("null", "none"):
            return None

        # Default string
        return value_str

    def _update_data_at_path(self, path: str, value: Any):
        """Update value at JSON path in current_data."""
        parts = self._parse_path(path)
        if not parts:
            return

        # Navigate to parent
        obj = self.current_data
        for part in parts[:-1]:
            if isinstance(part, int):
                obj = obj[part]
            else:
                obj = obj[part]

        # Set value
        last_part = parts[-1]
        if isinstance(last_part, int):
            obj[last_part] = value
        else:
            obj[last_part] = value

    def _parse_path(self, path: str) -> List[Union[str, int]]:
        """Parse JSON path to list of keys/indices."""
        parts = []
        current = ""

        # Skip root key
        if "." in path:
            path = path.split(".", 1)[1]
        else:
            return parts

        i = 0
        while i < len(path):
            c = path[i]

            if c == ".":
                if current:
                    parts.append(current)
                    current = ""
            elif c == "[":
                if current:
                    parts.append(current)
                    current = ""
                # Find closing bracket
                end = path.index("]", i)
                index = int(path[i + 1 : end])
                parts.append(index)
                i = end
            else:
                current += c

            i += 1

        if current:
            parts.append(current)

        return parts

    def search(self, query: str):
        """Search for nodes matching query."""
        self.search_query = query.lower()
        self.search_matches = []
        self.search_index = 0

        if not query or not self.root:
            return

        self._search_node(self.root)

        if self.search_matches:
            self.cursor = self.search_matches[0]
            self._expand_to_cursor()
            self._ensure_cursor_visible()
            self.message = f"Found {len(self.search_matches)} matches"
        else:
            self.message = "No matches found"

    def _search_node(self, node: JSONTreeNode):
        """Recursively search nodes."""
        # Check key
        if self.search_query in node.key.lower():
            self.search_matches.append(node)
        # Check value for leaves
        elif not node.is_container:
            if self.search_query in str(node.value).lower():
                self.search_matches.append(node)

        for child in node.children:
            self._search_node(child)

    def next_match(self):
        """Go to next search match."""
        if not self.search_matches:
            return

        self.search_index = (self.search_index + 1) % len(self.search_matches)
        self.cursor = self.search_matches[self.search_index]
        self._expand_to_cursor()
        self._ensure_cursor_visible()
        self.message = f"Match {self.search_index + 1}/{len(self.search_matches)}"

    def _expand_to_cursor(self):
        """Expand all parents to make cursor visible."""
        if not self.cursor:
            return

        node = self.cursor.parent
        while node:
            if node.is_container:
                node.expanded = True
            node = node.parent

    def save(self, filepath: str = None) -> Tuple[bool, str]:
        """Save JSON to file."""
        try:
            save_path = filepath or self.current_file
            if not save_path:
                return False, "No filename specified"

            # Resolve path
            if not os.path.isabs(save_path):
                save_path = self.project_root / save_path

            # Backup existing
            if os.path.exists(save_path):
                backup_path = f"{save_path}.backup"
                import shutil

                shutil.copy2(save_path, backup_path)

            # Validate against schema
            if self.schema:
                try:
                    import jsonschema

                    jsonschema.validate(self.current_data, self.schema)
                except jsonschema.ValidationError as e:
                    return False, f"Schema validation failed: {e.message}"
                except ImportError:
                    pass  # Skip validation if jsonschema not available

            # Write file
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self.current_data, f, indent=2, ensure_ascii=False)

            self.current_file = str(save_path)
            self.original_data = copy.deepcopy(self.current_data)
            self.modified = False

            return True, f"✅ Saved: {save_path}"

        except Exception as e:
            return False, f"❌ Error saving: {e}"

    def get_diff(self) -> List[str]:
        """Get diff between original and current."""
        if not self.original_data or not self.current_data:
            return ["No data loaded"]

        if self.original_data == self.current_data:
            return ["No changes"]

        lines = ["Changes:"]
        self._compare(self.original_data, self.current_data, lines, "")
        return lines

    def _compare(self, old: Any, new: Any, lines: List[str], path: str):
        """Recursively compare values."""
        if old == new:
            return

        if type(old) != type(new):
            lines.append(f"  {path}: {type(old).__name__} → {type(new).__name__}")
            return

        if isinstance(old, dict):
            old_keys = set(old.keys())
            new_keys = set(new.keys())

            for key in new_keys - old_keys:
                lines.append(f"  {path}.{key}: + ADDED")

            for key in old_keys - new_keys:
                lines.append(f"  {path}.{key}: - REMOVED")

            for key in old_keys & new_keys:
                new_path = f"{path}.{key}" if path else key
                self._compare(old[key], new[key], lines, new_path)

        elif isinstance(old, list):
            if len(old) != len(new):
                lines.append(f"  {path}: length {len(old)} → {len(new)}")

            for i, (o, n) in enumerate(zip(old, new)):
                self._compare(o, n, lines, f"{path}[{i}]")

        else:
            old_str = json.dumps(old)
            new_str = json.dumps(new)
            lines.append(f"  {path}: {old_str} → {new_str}")

    def render(self, width: int = 80) -> str:
        """Render viewer for terminal."""
        output = []

        # Header (standardized)
        title = f"JSON VIEWER"
        subtitle = (
            f"{Path(self.current_file).name if self.current_file else '[No file]'}"
        )
        header = render_section(
            title, subtitle=subtitle, width=width, style=BoxStyle.SINGLE, align="center"
        )
        output.extend(header.splitlines())

        if not self.root:
            output.append("  No JSON loaded. Use JSON LOAD <file>")
            return "\n".join(output)

        # Tree view
        visible = self._get_visible_nodes()
        start = self.scroll_offset
        end = min(start + self.viewport_height, len(visible))

        for node in visible[start:end]:
            line = self._render_node(node, width)
            output.append(line)

        # Scroll indicators
        if self.scroll_offset > 0:
            output.insert(3, f"  {'▲ more above':^{width-4}}")
        if end < len(visible):
            output.append(f"  {'▼ more below':^{width-4}}")

        # Status bar
        output.append(render_separator(width, style=BoxStyle.SINGLE))
        status = f"  Path: {self.cursor.get_path() if self.cursor else 'N/A'}"
        status += f" | Undo: {len(self.undo_stack)}"
        if self.search_query:
            status += (
                f" | Search: '{self.search_query}' ({len(self.search_matches)} matches)"
            )
        output.append(status[:width])

        # Message
        if self.message:
            output.append(f"  {self.message}")

        # Help
        output.append("")
        output.append("  8/2=nav | 4/6=collapse/expand | Space=toggle | Enter=edit")
        output.append("  /=search | n=next | A=expand all | C=collapse all | Q=quit")

        return "\n".join(output)

    def _render_node(self, node: JSONTreeNode, width: int) -> str:
        """Render single node line."""
        indent = "  " * node.depth

        # Cursor highlight
        cursor = "▶ " if node == self.cursor else "  "

        # Expand indicator
        if node.is_container:
            expand = "▼ " if node.expanded else "▶ "
        else:
            expand = "  "

        # Type icon and color
        jtype = node.json_type
        icon = jtype.icon
        color = jtype.color

        # Value display
        value = node.get_display_value()

        # Search highlight
        highlight = ""
        if node in self.search_matches:
            highlight = "\033[43m"  # Yellow background

        # Build line
        line = f"{cursor}{indent}{expand}{highlight}{color}{icon} {node.key}: {value}{self.RESET}"

        return line[:width]

    def handle_key(self, key: str) -> bool:
        """Handle keyboard input. Returns False to exit."""
        self.message = ""

        # Navigation
        if key == "8" or key == "up":
            self.navigate_up()
        elif key == "2" or key == "down":
            self.navigate_down()
        elif key == "4" or key == "left":
            self.collapse()
        elif key == "6" or key == "right":
            self.expand()

        # Expand/collapse
        elif key == " ":
            self.toggle_expand()
        elif key.lower() == "a":
            self.expand_all()
        elif key.lower() == "c":
            self.collapse_all()

        # Undo/Redo
        elif key == "7":
            self.undo()
        elif key == "9":
            self.redo()

        # Search
        elif key == "/" or key.lower() == "s":
            self.message = "Search: (enter query)"
            # In real implementation, would enter search mode
        elif key.lower() == "n":
            self.next_match()

        # Exit
        elif key.lower() == "q" or key == "escape":
            return False

        return True


# Convenience functions
def create_json_viewer(config=None) -> JSONTreeViewer:
    """Create new JSON viewer instance."""
    return JSONTreeViewer(config)


def get_json_viewer_help() -> str:
    """Get help text for JSON viewer."""
    return """
JSON VIEWER/EDITOR
══════════════════

Interactive JSON browser and editor with tree navigation.

COMMANDS:
  JSON VIEW <file>          View JSON file
  JSON EDIT <file>          Edit JSON file
  JSON VALIDATE <file>      Validate against schema
  JSON DIFF <file1> <file2> Compare two JSON files
  JSON PATH <file> <path>   Get value at path

KEYBOARD CONTROLS:
  Navigation: 8=↑  2=↓  4=collapse  6=expand
  Expand:     Space=toggle  A=expand all  C=collapse all
  Edit:       Enter=edit value  Del=delete key
  Search:     /=search  N=next match
  Undo/Redo:  7=undo  9=redo
  File:       S=save
  Exit:       Q or Esc

PATH SYNTAX:
  data.users[0].name        Access nested values
  config.server.port        Dot notation for objects
  items[5].id               Bracket notation for arrays

FEATURES:
  - Syntax highlighting by type
  - Schema validation (JSON Schema)
  - Diff view for changes
  - Auto-backup before save
  - Search within JSON
  - Copy value/path

FILES:
  JSON files can be anywhere in the project.
"""
