---
title: Menu System
version: 2.0.0
author: uDOS
created: 2026-01-06
tags: [menu, navigation, ui, template]
description: Interactive menu system with navigation and state management
permissions:
  execute: true
  save_state: true
variables:
  current_menu: main
  running: true
  inventory:
    water_bottle: 3
    first_aid_kit: 1
    flashlight: 1
---

# Menu System Template

A reusable menu navigation pattern with submenus and state tracking.

---

## Initialize

Set up the menu state.

```upy
# Initialize menu state
current_menu = "main"
running = True

# Inventory (could be loaded from state)
inventory = {
    "water_bottle": 3,
    "first_aid_kit": 1,
    "flashlight": 1
}
```

---

## Main Loop

Route to the correct menu based on state.

```upy
LABEL LOOP

IF NOT running:
    END

IF current_menu == "main":
    GOTO MENU_MAIN
ELIF current_menu == "inventory":
    GOTO MENU_INVENTORY
ELIF current_menu == "settings":
    GOTO MENU_SETTINGS
```

---

## Main Menu

The primary navigation hub.

```upy
LABEL MENU_MAIN

PRINT ""
PRINT "=========================================="
PRINT "  Main Menu"
PRINT "=========================================="
PRINT ""

CHOICE "Select an option:"
    OPTION "View Inventory" -> GOTO_INVENTORY
    OPTION "Settings" -> GOTO_SETTINGS
    OPTION "Exit" -> EXIT
END
```

---

## Inventory Menu

Display and manage inventory items.

```upy
LABEL MENU_INVENTORY

PRINT ""
PRINT "=========================================="
PRINT "  Inventory"
PRINT "=========================================="
PRINT ""

# Display inventory
FOR item, count IN inventory.items():
    name = item.replace("_", " ").title()
    PRINT "• " + name + " x" + str(count)

PRINT ""

CHOICE "What would you like to do?"
    OPTION "Back to Main Menu" -> GOTO_MAIN
    OPTION "Exit" -> EXIT
END
```

---

## Settings Menu

Configure application options.

```upy
LABEL MENU_SETTINGS

PRINT ""
PRINT "=========================================="
PRINT "  Settings"
PRINT "=========================================="
PRINT ""

# Display current settings
PRINT "Current settings:"
PRINT "• Theme: " + STATE.GET("theme", "default")
PRINT "• Location: " + STATE.GET("location", "Unknown")
PRINT "• Sound: " + ("On" IF STATE.GET("sound", True) ELSE "Off")
PRINT ""

CHOICE "What would you like to do?"
    OPTION "Toggle Sound" -> TOGGLE_SOUND
    OPTION "Back to Main Menu" -> GOTO_MAIN
    OPTION "Exit" -> EXIT
END
```

---

## Navigation Handlers

Handle menu transitions.

```upy
LABEL GOTO_MAIN
current_menu = "main"
GOTO LOOP

LABEL GOTO_INVENTORY
current_menu = "inventory"
GOTO LOOP

LABEL GOTO_SETTINGS
current_menu = "settings"
GOTO LOOP

LABEL TOGGLE_SOUND
current_sound = STATE.GET("sound", True)
STATE.SET("sound", NOT current_sound)
PRINT "Sound " + ("enabled" IF NOT current_sound ELSE "disabled")
GOTO MENU_SETTINGS
```

---

## Exit Handler

Clean application exit.

```upy
LABEL EXIT

running = False
PRINT ""
PRINT "Goodbye!"

END
```

---

## Notes

This template demonstrates:

- **Menu State Machine**: Track current menu in a variable
- **Navigation Pattern**: Central loop routes to correct menu
- **State Integration**: Read/write persistent state
- **Inventory System**: Dictionary-based item tracking
- **Choice Branching**: User-driven navigation

### Customization Ideas

1. Add more menu levels (nested submenus)
2. Add keyboard shortcuts (1, 2, 3 for options)
3. Add breadcrumb trail display
4. Add confirmation dialogs for destructive actions
5. Add menu animations or transitions
