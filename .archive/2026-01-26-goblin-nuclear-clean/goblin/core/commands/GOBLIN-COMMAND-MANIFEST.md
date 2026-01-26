# Goblin Command Manifest

## Complete Handler Inventory (v1.0.0.65+)

**Last Updated:** 2026-01-26  
**Status:** Alpha v1.0.0.65  
**Purpose:** Comprehensive inventory of remaining Goblin handlers after removal of overlapping Wizard/Core commands

---

## Executive Summary

Goblin now contains **80 active handlers** spanning:

- **Core Gameplay:** 18 handlers (workflows, missions, tasks, resources, checkpoints)
- **User Interface:** 13 handlers (display, panels, themes, TUI, input devices)
- **Data & Knowledge:** 15 handlers (memory tiers, guides, archives, overlays, waypoints)
- **Creativity & Content:** 12 handlers (make, story, music, sprites, diagrams)
- **System & Integration:** 13 handlers (file operations, time, device management, email)
- **Network & Cloud:** 8 handlers (mesh, QR, audio, voice, network, cloud)
- **Utilities:** 5 handlers (environment, variables, colors, logging, icons)

**Removed (Wizard/Core-only):**

- ❌ TREE (moved to Wizard `MEMORY TREE`)
- ❌ MAP (Core runtime only)
- ❌ PANEL (Core runtime only)
- ❌ HELP (Core runtime only)
- ❌ REPAIR (Core runtime only)
- ❌ SHAKEDOWN (Core runtime only)
- ❌ TIDY, CLEAN, BACKUP (Core maintenance)
- ❌ DEV MODE (Wizard Server only)

---

## Detailed Handler Inventory

### Core Gameplay & Workflows (18)

| Handler                | Command(s)                        | Purpose                      | Status    |
| ---------------------- | --------------------------------- | ---------------------------- | --------- |
| `mission_handler.py`   | MISSION                           | Mission creation/management  | ✅ Active |
| `workflow_handler.py`  | WORKFLOW, RUN                     | Workflow automation          | ✅ Active |
| `schedule_handler.py`  | SCHEDULE                          | Task scheduling system       | ✅ Active |
| `checklist_handler.py` | CHECKLIST                         | Checklist management         | ✅ Active |
| `calendar_handler.py`  | CAL, CALENDAR, TASK               | Calendar & task integration  | ✅ Active |
| `barter_commands.py`   | BARTER, OFFER, REQUEST, TRADE, XP | Trading & XP system          | ✅ Active |
| `resource_handler.py`  | RESOURCE                          | Resource/provider management | ✅ Active |
| `session_handler.py`   | SESSION, HISTORY, RESTORE         | Session management           | ✅ Active |
| `story_handler.py`     | STORY                             | Interactive story system     | ✅ Active |
| `scenario_handler.py`  | SCENARIO                          | Scenario management          | ✅ Active |
| `sandbox_handler.py`   | SANDBOX                           | Sandboxed execution          | ✅ Active |
| `feedback_handler.py`  | FEEDBACK, REPORT                  | User feedback collection     | ✅ Active |
| `bookmark_handler.py`  | BOOKMARK                          | Content bookmarking          | ✅ Active |
| `icon_handler.py`      | ICON                              | Icon/symbol management       | ✅ Active |
| `debug_handler.py`     | DEBUG                             | Debug mode & logging         | ✅ Active |
| `asset_handler.py`     | ASSETS                            | Game asset management        | ✅ Active |
| `xp_handler.py`        | XP                                | Experience points            | ✅ Active |
| `editor_handler.py`    | EDITOR                            | Text editor interface        | ✅ Active |

### User Interface (13)

| Handler                    | Command(s)                | Purpose                  | Status    |
| -------------------------- | ------------------------- | ------------------------ | --------- |
| `display_handler.py`       | BLANK, SPLASH, DASH, etc. | Display & rendering      | ✅ Active |
| `dashboard_handler.py`     | DASHBOARD, VIEWPORT       | Status dashboard         | ✅ Active |
| `theme_handler.py`         | THEME                     | Theme management         | ✅ Active |
| `tui_handler.py`           | TUI                       | TUI mode control         | ✅ Active |
| `keypad_demo_handler.py`   | KEYPAD                    | Universal input system   | ✅ Active |
| `mouse_handler.py`         | MOUSE                     | Mouse input handling     | ✅ Active |
| `selector_handler.py`      | SELECTOR                  | Selection framework      | ✅ Active |
| `configuration_handler.py` | CONFIG                    | System configuration     | ✅ Active |
| `setup_handler.py`         | WIZARD, SETUP             | Setup wizard             | ✅ Active |
| `splash_handler.py`        | SPLASH                    | Splash screen control    | ✅ Active |
| `typo_handler.py`          | TYPO                      | Typography system        | ✅ Active |
| `output_handler.py`        | OUTPUT, SERVER, WEB, POKE | Output/extension routing | ✅ Active |
| `environment_handler.py`   | ENV                       | Environment variables    | ✅ Active |

### Data & Knowledge (15)

| Handler                     | Command(s)                | Purpose                 | Status    |
| --------------------------- | ------------------------- | ----------------------- | --------- |
| `memory_commands.py`        | MEMORY, BANK              | 4-Tier memory system    | ✅ Active |
| `memory_unified_handler.py` | MEMORY (unified ops)      | Memory tier operations  | ✅ Active |
| `private_commands.py`       | PRIVATE                   | Tier 1 encryption       | ✅ Active |
| `shared_commands.py`        | SHARED                    | Tier 2 sharing          | ✅ Active |
| `community_commands.py`     | COMMUNITY                 | Tier 3 groups           | ✅ Active |
| `guide_handler.py`          | GUIDE, KNOWLEDGE, DOCS    | Knowledge base          | ✅ Active |
| `guide_ai_handler.py`       | GUIDE AI                  | AI knowledge bank       | ✅ Active |
| `archive_handler.py`        | ARCHIVE                   | Content archiving       | ✅ Active |
| `inbox_handler.py`          | INBOX                     | Inbox processing        | ✅ Active |
| `overlay_handler.py`        | OVERLAY                   | Overlay rendering       | ✅ Active |
| `waypoint_handler.py`       | WAYPOINT, WP              | Navigation waypoints    | ✅ Active |
| `location_handler.py`       | LOCATION, LOC, SKY, STARS | Location/privacy system | ✅ Active |
| `tile_handler.py`           | TILE, LOCATE              | Tile & mapping system   | ✅ Active |
| `geography_handler.py`      | GEO                       | 24×24 grid map system   | ✅ Active |
| `feed_handler.py`           | FEED                      | Real-time data feeds    | ✅ Active |

### Creativity & Content (12)

| Handler                | Command(s)             | Purpose                                | Status    |
| ---------------------- | ---------------------- | -------------------------------------- | --------- |
| `make_handler.py`      | MAKE                   | Unified generation system              | ✅ Active |
| `ok_handler.py`        | OK                     | Assistant generation (OK/DIAGRAM/DRAW) | ✅ Active |
| `sprite_handler.py`    | SPRITE, ITEM           | Sprite & inventory system              | ✅ Active |
| `object_handler.py`    | OBJECT                 | Game object management                 | ✅ Active |
| `draw_handler.py`      | DRAW                   | 24×24 tile editor                      | ✅ Active |
| `music_handler.py`     | MUSIC, PLAY, GROOVEBOX | Music production                       | ✅ Active |
| `voice_handler.py`     | VOICE, SAY, LISTEN     | TTS & STT (Piper/Handy)                | ✅ Active |
| `bundle_handler.py`    | BUNDLE                 | Content packaging (drip delivery)      | ✅ Active |
| `capture_handler.py`   | CAPTURE                | Web content capture                    | ✅ Active |
| `wellbeing_handler.py` | WELLBEING, RUOK        | Mood/energy tracking                   | ✅ Active |
| `prompt_handler.py`    | PROMPT                 | Admin prompt management                | ✅ Active |
| `scenario_handler.py`  | SCENARIO               | Interactive scenarios                  | ✅ Active |

### System & Integration (13)

| Handler                | Command(s)                         | Purpose                                   | Status    |
| ---------------------- | ---------------------------------- | ----------------------------------------- | --------- |
| `file_handler.py`      | FILE                               | File operations                           | ✅ Active |
| `assistant_handler.py` | ASSISTANT, ASSIST                  | AI assistant routing                      | ✅ Active |
| `system_handler.py`    | SYSTEM                             | System admin (STATUS, DISK, REBOOT, etc.) | ✅ Active |
| `time_handler.py`      | TIME, CLOCK, TIMER, EGG, STOPWATCH | Time/date system                          | ✅ Active |
| `json_handler.py`      | JSON                               | JSON viewer/editor                        | ✅ Active |
| `logs_handler.py`      | LOGS                               | Log management                            | ✅ Active |
| `gmail_handler.py`     | GMAIL, LOGIN, LOGOUT, EMAIL, SYNC  | Gmail integration                         | ✅ Active |
| `device_handler.py`    | DEVICE                             | Input device management                   | ✅ Active |
| `plugin_handler.py`    | PLUGIN                             | Plugin container management               | ✅ Active |
| `install_handler.py`   | INSTALL                            | TCZ package management                    | ✅ Active |
| `stack_handler.py`     | STACK                              | Capability-based installation             | ✅ Active |
| `extension_handler.py` | EXTENSION, EXT                     | Extension management                      | ✅ Active |
| `mode_handler.py`      | MODE, GHOST, TOMB, CRYPT           | Prompt mode switching                     | ✅ Active |

### Network & Cloud (8)

| Handler              | Command(s) | Purpose                         | Status    |
| -------------------- | ---------- | ------------------------------- | --------- |
| `network_handler.py` | NETWORK    | Unified network management      | ✅ Active |
| `mesh_handler.py`    | MESH       | MeshCore P2P networking         | ✅ Active |
| `qr_handler.py`      | QR         | QR code relay transport         | ✅ Active |
| `audio_handler.py`   | AUDIO      | Acoustic packet transport       | ✅ Active |
| `cloud_handler.py`   | CLOUD      | Business intelligence/cloud ops | ✅ Active |
| `pair_handler.py`    | PAIR       | Mobile console pairing          | ✅ Active |
| `loader_handler.py`  | LOADER     | Terminal loader system          | ✅ Active |
| `quota_handler.py`   | QUOTA      | API quota management            | ✅ Active |

### Utilities (5)

| Handler               | Command(s)     | Purpose                    | Status    |
| --------------------- | -------------- | -------------------------- | --------- |
| `peek_handler.py`     | PEEK           | Data collection system     | ✅ Active |
| `color_handler.py`    | COLOR, PALETTE | Color/palette management   | ✅ Active |
| `user_handler.py`     | USER           | User management            | ✅ Active |
| `variable_handler.py` | VAR, SET, GET  | Variable management        | ✅ Active |
| `profile_handler.py`  | PROFILE        | User profile configuration | ✅ Active |

### Survival & Knowledge (1)

| Handler               | Command(s) | Purpose                   | Status    |
| --------------------- | ---------- | ------------------------- | --------- |
| `survival_handler.py` | SURVIVAL   | Survival knowledge system | ✅ Active |

---

## Commands Delegated to Core/Wizard

These commands are **NOT** duplicated in Goblin; they route to guidance messages:

### Core Runtime (User input HELP, MAP, PANEL, TIDY, CLEAN, REPAIR, SHAKEDOWN)

```
elif module == "HELP":
    → _core_only_command("HELP")

elif module == "MAP":
    → _core_only_command("MAP")

elif module == "PANEL" or module == "UI":
    → _core_only_command("PANEL")

elif module == "TIDY":
    → _core_only_command("TIDY")

elif module == "CLEAN":
    → _core_only_command("CLEAN")
```

**Location:** `dev/goblin/core/uDOS_commands.py` lines 800–929

### Wizard Server (TREE, DEV MODE)

```
elif module == "TREE":
    → _wizard_only_command("TREE")

elif module == "DEV":
    → _wizard_only_command("DEV")
```

**Location:** `dev/goblin/core/uDOS_commands.py` lines 800–929

### Memory Tier (MEMORY TREE subcommand)

```python
def _tree(self, args: List[str]) -> str:
    """Inform callers that TREE moved to Wizard-only service."""
    return (
        "TREE output now comes from the Wizard TUI.\n"
        "Launch wizard.server and use its TREE command."
    )
```

**Location:** `dev/goblin/core/commands/memory_commands.py` lines 350–355

---

## Handler Organization (File Structure)

```
dev/goblin/core/commands/
├── base_handler.py              # Base class for all handlers
├── system_handler.py            # System admin commands
├── file_handler.py              # File operations
├── assistant_handler.py         # AI assistant routing
│
├── WORKFLOWS & TASKS (6)
├── mission_handler.py
├── workflow_handler.py
├── schedule_handler.py
├── calendar_handler.py
├── checklist_handler.py
├── resource_handler.py
│
├── MEMORY SYSTEM (6)
├── memory_commands.py
├── memory_unified_handler.py
├── private_commands.py
├── shared_commands.py
├── community_commands.py
├── guide_handler.py
│
├── USER INTERFACE (13)
├── display_handler.py
├── dashboard_handler.py
├── theme_handler.py
├── tui_handler.py
├── configuration_handler.py
├── setup_handler.py
├── keypad_demo_handler.py
├── mouse_handler.py
├── selector_handler.py
├── splash_handler.py
├── typo_handler.py
├── output_handler.py
├── environment_handler.py
│
├── CREATIVITY & CONTENT (12)
├── make_handler.py
├── ok_handler.py
├── sprite_handler.py
├── object_handler.py
├── draw_handler.py
├── story_handler.py
├── music_handler.py
├── voice_handler.py
├── bundle_handler.py
├── capture_handler.py
├── wellbeing_handler.py
├── prompt_handler.py
│
├── NETWORK & CLOUD (8)
├── network_handler.py
├── mesh_handler.py
├── qr_handler.py
├── audio_handler.py
├── cloud_handler.py
├── pair_handler.py
├── loader_handler.py
├── quota_handler.py
│
├── UTILITIES (5)
├── peek_handler.py
├── color_handler.py
├── user_handler.py
├── variable_handler.py
├── profile_handler.py
│
└── [Other handlers...]
    └── time_handler.py, json_handler.py, logs_handler.py, etc.
```

---

## Known Overlaps & Decisions

### ✅ RESOLVED OVERLAPS (Removed from Goblin)

| Command      | Was Duplicate?    | Removed                    | Notes                                |
| ------------ | ----------------- | -------------------------- | ------------------------------------ |
| TREE         | Yes (Wizard/Core) | ✅ tree_handler.py deleted | Now routes to `MEMORY TREE`          |
| MAP          | Yes (Core)        | ✅ Routing message added   | Core runtime owns spatial operations |
| PANEL        | Yes (Core)        | ✅ Routing message added   | Core runtime owns display blocks     |
| HELP         | Yes (Core)        | ✅ Routing message added   | Core runtime provides canonical help |
| REPAIR       | Yes (Core)        | ✅ Routing message added   | Core self-healing system             |
| SHAKEDOWN    | Yes (Core)        | ✅ Routing message added   | Core system validation (47 tests)    |
| TIDY         | Yes (Core)        | ✅ Routing message added   | Core workspace cleanup               |
| CLEAN        | Yes (Core)        | ✅ Routing message added   | Core maintenance                     |
| BACKUP (old) | Yes (Core)        | ✅ Routing message added   | Core backup handler                  |
| DEV MODE     | Yes (Wizard)      | ✅ Routing message added   | Wizard Server interactive TUI        |

### ⚠️ POTENTIAL OVERLAPS (Still Present, Requires Audit)

These handlers may have overlapping functionality with Core/Wizard equivalents:

| Handler                | Commands              | Potential Overlap                              | Action                                               |
| ---------------------- | --------------------- | ---------------------------------------------- | ---------------------------------------------------- |
| `assistant_handler.py` | ASSISTANT, ASSIST     | AI routing (also in Wizard)                    | **Verify:** Does this duplicate Wizard's AI gateway? |
| `time_handler.py`      | TIME, CLOCK, TIMER    | Also in Core?                                  | **Audit:** Check Core runtime time handling          |
| `guide_handler.py`     | GUIDE, KNOWLEDGE      | Knowledge bank (also in Core)                  | **Verify:** Goblin-specific vs Core GUIDE            |
| `location_handler.py`  | LOCATION, SKY, STARS  | Privacy-first location system with consent     | ✅ Goblin-only feature                               |
| `tile_handler.py`      | TILE, LOCATE, WEATHER | Geographic data (cities, weather, conversions) | ✅ Complements GEOGRAPHY                             |
| `geography_handler.py` | GEO, MAP              | 24×24 MapGrid spatial system with layers       | ✅ Distinct from TILE                                |
| `feed_handler.py`      | FEED                  | Real-time ticker/scroll display for TUI        | ✅ TUI-specific, not Core                            |
| `json_handler.py`      | JSON                  | JSON viewer/editor in terminal                 | ✅ TUI tool, not duplicate                           |

---

## Audit Results (2026-01-26)

### ✅ COMPLETED: All Potential Overlaps Verified

**Status:** All flagged handlers reviewed. **No duplicate functionality found.**

**Key Findings:**

1. **Assistant Handler (Deprecated)**
   - Marked DEPRECATED as of v1.2.0
   - Clear migration path: ASSISTANT ASK → MAKE DO
   - Maintained as compatibility shim with deprecation warnings
   - ✅ No overlap with Wizard AI gateway

2. **Time Handler (Goblin-Specific)**
   - Unique features: EGG timer with large ASCII display, STOPWATCH
   - Implements termdown-inspired countdown visualization
   - TUI-interactive features not suitable for Core runtime
   - ✅ No Core equivalent found

3. **Guide Handler (Goblin-Specific)**
   - Unique: Interactive learning with user progress tracking
   - Features: GUIDE COMPLETE, GUIDE PROGRESS, GUIDE REGEN, GUIDE REVIEW
   - Core provides static knowledge; Goblin tracks user journey
   - ✅ No overlap with Core static guides

4. **Mapping Systems (Complementary)**
   - TILE: Geographic data (cities, weather, conversions, terrain)
   - GEOGRAPHY: Spatial visualization (24×24 MapGrid with 9 layer bands)
   - Both needed: Data layer + visualization layer
   - ✅ Distinct, non-overlapping purposes

5. **Feed Handler (TUI-Specific)**
   - Purpose: Real-time ticker and scroll display for terminal
   - Not data-processing feed; presentation layer only
   - ✅ Distinct from Core data feeds

6. **JSON Handler (TUI Tool)**
   - JSON viewer/editor for terminal environment
   - Development utility, not business logic
   - ✅ TUI-specific tool

---

## Summary Statistics

| Category                  | Count | Status                          |
| ------------------------- | ----- | ------------------------------- |
| **Total Handlers**        | 80    | ✅ Active                       |
| **Removed (Wizard/Core)** | 8     | ✅ Delegated                    |
| **Active Handlers**       | 80    | ✅ Running                      |
| **Overlaps Audited**      | 7     | ✅ All Verified (No Duplicates) |
| **Deprecated Handlers**   | 1     | ✅ Migration Path Active        |

---

## Audit Conclusion

**All Goblin handlers are either:**

1. Goblin-specific features (interactive TUI, progress tracking, visualization)
2. Properly deprecated with clear migration paths (Assistant)
3. Complementary to Core/Wizard (not duplicate functionality)

**No action required.** Goblin command set is clean and properly scoped.

---

_Last Updated: 2026-01-26_  
_Goblin v1.0.0.65 (Alpha)_
