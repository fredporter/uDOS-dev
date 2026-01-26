"""
uDOS Unified Menu Service (v1.2.30)

Shared menu system logic for CLI, TUI, and GUI interfaces.

Consolidates functionality from:
- dev/examples/input_system/menu_system_example.py (Python menu)
- app/src/components/menu.js (Desktop app menus)

Provides:
- Menu item definitions with actions and shortcuts
- Multi-level menu hierarchy
- Keyboard shortcut mapping
- Menu state management
- Cross-platform menu structure

Author: uDOS Development Team
Version: 1.2.30
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class MenuItemType(Enum):
    """Menu item types"""

    ACTION = "action"  # Executes action
    SUBMENU = "submenu"  # Opens submenu
    SEPARATOR = "separator"  # Visual separator
    TOGGLE = "toggle"  # Toggleable option


@dataclass
class MenuItem:
    """
    Menu item definition.

    Attributes:
        id: Unique identifier for the item
        label: Display label
        item_type: Type of menu item
        action: Action to execute (callable or string command)
        submenu: List of submenu items
        shortcut: Keyboard shortcut (e.g., "⌘N" or "Ctrl+N")
        icon: Icon string (emoji or icon name)
        enabled: Whether item is enabled
        checked: For toggle items, current state
        metadata: Additional data
    """

    id: str
    label: str
    item_type: MenuItemType = MenuItemType.ACTION
    action: Optional[Any] = None
    submenu: Optional[List["MenuItem"]] = None
    shortcut: str = ""
    icon: str = ""
    enabled: bool = True
    checked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def separator() -> "MenuItem":
        """Create separator item"""
        return MenuItem(id="_sep", label="", item_type=MenuItemType.SEPARATOR)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        result = {
            "id": self.id,
            "label": self.label,
            "type": self.item_type.value,
            "shortcut": self.shortcut,
            "icon": self.icon,
            "enabled": self.enabled,
            "checked": self.checked,
        }
        if self.submenu:
            result["submenu"] = [item.to_dict() for item in self.submenu]
        return result


@dataclass
class MenuDefinition:
    """
    Menu bar definition.

    Attributes:
        id: Menu identifier
        label: Display label for menu
        items: List of menu items
    """

    id: str
    label: str
    items: List[MenuItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "label": self.label,
            "items": [item.to_dict() for item in self.items],
        }


class MenuService:
    """
    Unified menu service for all interfaces.

    Provides:
    - Standard menu definitions (File, Edit, View, Tools, Help)
    - Keyboard shortcut registration
    - Action dispatch
    - Menu state management
    """

    def __init__(self, action_handler: Callable[[str, Dict], Any] = None):
        """
        Initialize menu service.

        Args:
            action_handler: Callback for menu actions (action_id, metadata) -> result
        """
        self.action_handler = action_handler
        self.menus: Dict[str, MenuDefinition] = {}
        self.shortcuts: Dict[str, str] = {}  # shortcut -> action_id
        self.active_menu: Optional[str] = None
        self.menu_stack: List[List[MenuItem]] = []

        # Build default menus
        self._build_default_menus()

    def _build_default_menus(self):
        """Build default uDOS menu structure"""

        # Apple/System menu
        self.menus["apple"] = MenuDefinition(
            id="apple",
            label="",
            items=[
                MenuItem(id="about", label="About uDOS", icon="ℹ️"),
                MenuItem.separator(),
                MenuItem(
                    id="preferences",
                    label="Preferences...",
                    shortcut="⌘,",
                    enabled=False,
                ),
            ],
        )

        # File menu
        self.menus["file"] = MenuDefinition(
            id="file",
            label="File",
            items=[
                MenuItem(id="new", label="New", shortcut="⌘N", icon="📄"),
                MenuItem(id="open", label="Open...", shortcut="⌘O", icon="📂"),
                MenuItem(id="close", label="Close", shortcut="⌘W", enabled=False),
                MenuItem.separator(),
                MenuItem(id="save", label="Save", shortcut="⌘S", icon="💾"),
                MenuItem(id="save-as", label="Save As...", shortcut="⌘⇧S"),
                MenuItem.separator(),
                MenuItem(id="export", label="Export...", icon="📤"),
                MenuItem.separator(),
                MenuItem(id="quit", label="Quit", shortcut="⌘Q"),
            ],
        )

        # Edit menu
        self.menus["edit"] = MenuDefinition(
            id="edit",
            label="Edit",
            items=[
                MenuItem(id="undo", label="Undo", shortcut="⌘Z", icon="↩️"),
                MenuItem(id="redo", label="Redo", shortcut="⌘⇧Z", icon="↪️"),
                MenuItem.separator(),
                MenuItem(id="cut", label="Cut", shortcut="⌘X", icon="✂️"),
                MenuItem(id="copy", label="Copy", shortcut="⌘C", icon="📋"),
                MenuItem(id="paste", label="Paste", shortcut="⌘V", icon="📥"),
                MenuItem.separator(),
                MenuItem(id="select-all", label="Select All", shortcut="⌘A"),
                MenuItem(id="find", label="Find...", shortcut="⌘F", icon="🔍"),
            ],
        )

        # View menu
        self.menus["view"] = MenuDefinition(
            id="view",
            label="View",
            items=[
                MenuItem(id="terminal", label="Terminal Mode", icon="⌨️"),
                MenuItem(id="teletext", label="Teletext Mode", icon="📺"),
                MenuItem(id="dashboard", label="Dashboard Mode", icon="📊"),
                MenuItem.separator(),
                MenuItem(id="files", label="File Browser", shortcut="⌘1", icon="📁"),
                MenuItem(
                    id="knowledge", label="Knowledge Library", shortcut="⌘2", icon="📚"
                ),
                MenuItem.separator(),
                MenuItem(id="system-info", label="System Info", icon="ℹ️"),
                MenuItem(id="extensions", label="Extensions", icon="🧩"),
            ],
        )

        # Tools menu
        self.menus["tools"] = MenuDefinition(
            id="tools",
            label="Tools",
            items=[
                MenuItem(id="character-editor", label="Character Editor", icon="🎨"),
                MenuItem(id="grid-editor", label="Grid Editor", icon="🗺️"),
                MenuItem(id="sprite-editor", label="Sprite Editor", icon="👾"),
                MenuItem.separator(),
                MenuItem(
                    id="run-script", label="Run Script...", shortcut="⌘R", icon="▶️"
                ),
                MenuItem(
                    id="debug-panel", label="Debug Panel", shortcut="⌘D", icon="🐛"
                ),
                MenuItem.separator(),
                MenuItem(id="clean", label="Clean Workspace", icon="🧹"),
                MenuItem(id="backup", label="Backup...", icon="💾"),
            ],
        )

        # Help menu
        self.menus["help"] = MenuDefinition(
            id="help",
            label="Help",
            items=[
                MenuItem(id="help", label="uDOS Help", shortcut="⌘?", icon="❓"),
                MenuItem(id="keyboard", label="Keyboard Shortcuts", icon="⌨️"),
                MenuItem(id="wiki", label="Online Wiki", icon="🌐"),
                MenuItem.separator(),
                MenuItem(id="about", label="About uDOS", icon="ℹ️"),
            ],
        )

        # Build shortcut map
        self._build_shortcut_map()

    def _build_shortcut_map(self):
        """Build shortcut -> action_id mapping"""
        self.shortcuts.clear()

        for menu in self.menus.values():
            for item in menu.items:
                if item.shortcut and item.id:
                    self.shortcuts[item.shortcut] = item.id
                if item.submenu:
                    self._add_submenu_shortcuts(item.submenu)

    def _add_submenu_shortcuts(self, items: List[MenuItem]):
        """Recursively add submenu shortcuts"""
        for item in items:
            if item.shortcut and item.id:
                self.shortcuts[item.shortcut] = item.id
            if item.submenu:
                self._add_submenu_shortcuts(item.submenu)

    # ─── Menu Access ────────────────────────────────────────────────

    def get_menu(self, menu_id: str) -> Optional[MenuDefinition]:
        """Get menu by ID"""
        return self.menus.get(menu_id)

    def get_menu_bar(self) -> List[MenuDefinition]:
        """Get all menus in order"""
        order = ["apple", "file", "edit", "view", "tools", "help"]
        return [self.menus[m] for m in order if m in self.menus]

    def get_menu_item(self, menu_id: str, item_id: str) -> Optional[MenuItem]:
        """Find menu item by ID"""
        menu = self.menus.get(menu_id)
        if not menu:
            return None

        def find_item(items: List[MenuItem], target_id: str) -> Optional[MenuItem]:
            for item in items:
                if item.id == target_id:
                    return item
                if item.submenu:
                    found = find_item(item.submenu, target_id)
                    if found:
                        return found
            return None

        return find_item(menu.items, item_id)

    # ─── Menu Modification ──────────────────────────────────────────

    def add_menu(self, menu: MenuDefinition, position: int = None):
        """Add custom menu"""
        self.menus[menu.id] = menu
        self._build_shortcut_map()

    def add_menu_item(self, menu_id: str, item: MenuItem, position: int = None):
        """Add item to menu"""
        menu = self.menus.get(menu_id)
        if not menu:
            return False

        if position is not None:
            menu.items.insert(position, item)
        else:
            menu.items.append(item)

        if item.shortcut:
            self.shortcuts[item.shortcut] = item.id

        return True

    def remove_menu_item(self, menu_id: str, item_id: str) -> bool:
        """Remove item from menu"""
        menu = self.menus.get(menu_id)
        if not menu:
            return False

        menu.items = [i for i in menu.items if i.id != item_id]
        return True

    def set_item_enabled(self, menu_id: str, item_id: str, enabled: bool):
        """Enable/disable menu item"""
        item = self.get_menu_item(menu_id, item_id)
        if item:
            item.enabled = enabled

    def set_item_checked(self, menu_id: str, item_id: str, checked: bool):
        """Set toggle item state"""
        item = self.get_menu_item(menu_id, item_id)
        if item:
            item.checked = checked

    # ─── Action Dispatch ────────────────────────────────────────────

    def execute_action(self, action_id: str, metadata: Dict = None) -> Any:
        """
        Execute menu action.

        Args:
            action_id: Action identifier
            metadata: Additional context

        Returns:
            Result from action handler
        """
        if self.action_handler:
            return self.action_handler(action_id, metadata or {})
        return None

    def handle_shortcut(self, shortcut: str) -> bool:
        """
        Handle keyboard shortcut.

        Args:
            shortcut: Shortcut string (e.g., "⌘N")

        Returns:
            True if shortcut was handled
        """
        action_id = self.shortcuts.get(shortcut)
        if action_id:
            self.execute_action(action_id, {"source": "shortcut"})
            return True
        return False

    # ─── Menu Navigation ────────────────────────────────────────────

    def open_menu(self, menu_id: str) -> bool:
        """Open menu dropdown"""
        if menu_id in self.menus:
            self.active_menu = menu_id
            self.menu_stack = [self.menus[menu_id].items]
            return True
        return False

    def close_menu(self):
        """Close active menu"""
        self.active_menu = None
        self.menu_stack = []

    def navigate_into(self, item: MenuItem) -> bool:
        """Navigate into submenu"""
        if item.submenu:
            self.menu_stack.append(item.submenu)
            return True
        return False

    def navigate_back(self) -> bool:
        """Navigate back from submenu"""
        if len(self.menu_stack) > 1:
            self.menu_stack.pop()
            return True
        return False

    def get_current_items(self) -> List[MenuItem]:
        """Get items at current menu level"""
        if self.menu_stack:
            return self.menu_stack[-1]
        return []

    # ─── Serialization ──────────────────────────────────────────────

    def to_dict(self) -> Dict:
        """Export menu structure as dictionary"""
        return {
            "menus": {k: v.to_dict() for k, v in self.menus.items()},
            "shortcuts": self.shortcuts,
            "active_menu": self.active_menu,
        }

    def get_menu_html(self, menu_id: str) -> str:
        """
        Generate HTML for menu dropdown.

        For Tauri/web interfaces.
        """
        menu = self.menus.get(menu_id)
        if not menu:
            return ""

        html_parts = []
        for item in menu.items:
            if item.item_type == MenuItemType.SEPARATOR:
                html_parts.append('<div class="menu-separator"></div>')
            else:
                disabled = " disabled" if not item.enabled else ""
                checked = " checked" if item.checked else ""
                shortcut = (
                    f'<span class="shortcut">{item.shortcut}</span>'
                    if item.shortcut
                    else ""
                )

                html_parts.append(
                    f'<div class="menu-item{disabled}{checked}" data-action="{item.id}">'
                    f"{item.label} {shortcut}</div>"
                )

        return "\n".join(html_parts)

    def get_cli_menu(self, menu_id: str) -> str:
        """
        Generate CLI text for menu.

        For terminal interfaces.
        """
        menu = self.menus.get(menu_id)
        if not menu:
            return ""

        lines = [f"┌─ {menu.label} ─┐"]

        for i, item in enumerate(menu.items):
            if item.item_type == MenuItemType.SEPARATOR:
                lines.append("├────────────┤")
            else:
                prefix = "  " if item.enabled else "░░"
                shortcut = f"  [{item.shortcut}]" if item.shortcut else ""
                lines.append(f"│{prefix}{item.label}{shortcut}│")

        lines.append("└────────────┘")
        return "\n".join(lines)


# ─── Convenience Functions ──────────────────────────────────────────

_service_instance: MenuService = None


def get_menu_service(action_handler: Callable = None) -> MenuService:
    """Get singleton menu service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = MenuService(action_handler)
    return _service_instance


# ─── Test ───────────────────────────────────────────────────────────

if __name__ == "__main__":

    def handle_action(action_id: str, metadata: Dict):
        print(f"Action: {action_id}, metadata: {metadata}")

    service = MenuService(handle_action)

    print("Menu Bar:")
    for menu in service.get_menu_bar():
        print(f"  {menu.id}: {menu.label} ({len(menu.items)} items)")

    print("\nFile Menu (CLI):")
    print(service.get_cli_menu("file"))

    print("\nShortcuts:")
    for shortcut, action in list(service.shortcuts.items())[:5]:
        print(f"  {shortcut} -> {action}")

    print("\nTest shortcut:")
    service.handle_shortcut("⌘N")
