# .udos.md Map Tile Format Specification

**Version:** 1.0.0  
**Author:** uDOS Core Team  
**Date:** 2026-01-04

---

## Overview

The `.udos.md` format supports ASCII map grid tiles for visualizing geographic data, world maps, timezones, and system diagrams. Map tiles are rendered as monospace ASCII art with strict size constraints.

## Format Specification

### Constraint

**Maximum Size:** 120 columns × 40 rows

This constraint ensures:
- Consistent rendering across terminal sizes
- Manageable file sizes
- Clean tiling for large maps

### Syntax

```markdown
```map
TILE:code NAME:name ZONE:timezone
[ASCII art content]
\```
```

### Metadata Line (Optional)

The first line after `\```map` can contain space-separated metadata in `KEY:value` format:

| Key | Description | Example |
|-----|-------------|---------|
| `TILE` | Unique tile identifier | `TILE:NA01` |
| `NAME` | Human-readable tile name | `NAME:California` |
| `ZONE` | Timezone identifier | `ZONE:America/Los_Angeles` |
| `LAT` | Latitude coordinate | `LAT:34.0522` |
| `LON` | Longitude coordinate | `LON:-118.2437` |
| `ELEV` | Elevation (meters) | `ELEV:71` |

**Example:**
```map
TILE:NA01 NAME:California ZONE:America/Los_Angeles LAT:36.7783 LON:-119.4179
```

If no metadata is present, the ASCII art starts immediately after `\```map`.

---

## ASCII Art Guidelines

### Character Set

Use standard ASCII + box-drawing characters:

**Box Drawing:**
```
┌ ─ ┐   ╔ ═ ╗   ╭───╮
│   │   ║   ║   │   │
└ ─ ┘   ╚ ═ ╝   ╰───╯
```

**Geographic Symbols:**
```
○ City/Town
• Point of Interest
▲ Mountain
~ Water
═ Road/Highway
│ River
```

### Best Practices

1. **Use borders** for clear tile boundaries
2. **Label key features** within the art
3. **Align text** for readability
4. **Space consistently** to maintain grid alignment
5. **Test rendering** at 120-column width

---

## Complete Example

```markdown
---
title: North America Map
type: map
tiles: 4
format: ascii
constraint: 120x40
version: 1.0.0
---

# North America

## Western United States

```map
TILE:NA01 NAME:California ZONE:America/Los_Angeles
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           CALIFORNIA                                                                       │
│                                                                                                                            │
│                                                                                                                            │
│                    ○ San Francisco                                                                                         │
│                      (Bay Area)                                                                                            │
│                                                                                                                            │
│                                                                                                                            │
│                                                                                                                            │
│                            ○ San Jose                                                                                      │
│                                                                                                                            │
│                                                                                                                            │
│                                                                                                                            │
│                                    ○ Fresno                                                                                │
│                                                                                                                            │
│                                                                                                                            │
│                                                                                                                            │
│                      ○ Los Angeles                                                                                         │
│                        (Metro Area)                                                                                        │
│                                                                                                                            │
│                                                                                                                            │
│                                                                                                                            │
│                                  ○ San Diego                                                                               │
│                                                                                                                            │
│                                                                                                                            │
│  Timezone: PST/PDT (UTC-8/-7)                                                                                              │
│  Population: 39.5M                                                                                                         │
│  Capital: Sacramento                                                                                                       │
│                                                                                                                            │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
\```

## Eastern United States

```map
TILE:NA02 NAME:NewYork ZONE:America/New_York
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                            NEW YORK                                                                        │
│                                                                                                                            │
│                                                                                                                            │
│                        ○ Buffalo                                                                                           │
│                                                                                                                            │
│                                                                                                                            │
│                                                                                                                            │
│                             ○ Rochester                                                                                    │
│                                                                                                                            │
│                                                                                                                            │
│                                      ○ Syracuse                                                                            │
│                                                                                                                            │
│                                                                                                                            │
│                                                                                                                            │
│                                            ○ Albany                                                                        │
│                                              (Capital)                                                                     │
│                                                                                                                            │
│                                                                                                                            │
│                                                            ○ New York City                                                 │
│                                                              (Metro Area)                                                  │
│                                                                                                                            │
│                                                                                                                            │
│                                                                                                                            │
│  Timezone: EST/EDT (UTC-5/-4)                                                                                              │
│  Population: 19.4M                                                                                                         │
│  Capital: Albany                                                                                                           │
│                                                                                                                            │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
\```
```

---

## Tile Grid System

For large maps, use a grid-based tile code system:

### Tile Codes

Format: `[Column][Row]` where:
- Column: A-Z (west to east)
- Row: 01-99 (north to south)

**Example Grid:**
```
A01  B01  C01  D01
A02  B02  C02  D02
A03  B03  C03  D03
```

### Neighboring Tiles

Document adjacent tiles in metadata:

```map
TILE:B02 NAME:Central NORTH:B01 SOUTH:B03 EAST:C02 WEST:A02
```

---

## Converting Existing Maps

Use the converter tool to transform Map.json files:

```bash
python -m core.runtime.markdown.map_converter input.json output.udos.md
```

### Converter Features

- **Automatic chunking** for maps exceeding 120×40
- **Metadata extraction** from JSON
- **Size enforcement** with truncation warnings
- **Tile grid generation** for large maps

### Input Formats Supported

**Tiled Maps:**
```json
{
  "name": "World Map",
  "tiles": {
    "NA01": {
      "ascii": "...",
      "name": "California",
      "timezone": "America/Los_Angeles"
    }
  }
}
```

**Grid Maps:**
```json
{
  "name": "World Map",
  "grid": [
    ["X", "X", ...],
    ["X", "X", ...],
    ...
  ]
}
```

**Region Maps:**
```json
{
  "name": "World Map",
  "regions": {
    "north_america": {
      "map": "...",
      "timezone": "..."
    }
  }
}
```

---

## Integration with uPY Scripts

Map tiles can be accessed and manipulated via uPY scripts in the same document:

```markdown
```upy
# Get all map tiles
tiles = DOCUMENT.get_map_tiles()

# Find specific tile
ca_tile = DOCUMENT.find_tile("NA01")

# Get tile metadata
zone = ca_tile["zone"]
name = ca_tile["name"]

# Render tile
COMMAND("RENDER", tile=ca_tile["tile_code"])
\```
```

---

## Rendering

### TUI Display

Map tiles render in the uDOS TUI using the monospace viewport:

```
┌─ [TILE: NA01] California ────────────────────────────────┐
│                                                           │
│              CALIFORNIA                                   │
│                                                           │
│    ○ San Francisco                                        │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Export Formats

- **PNG**: Render as monospace image
- **SVG**: Vector rendering for scalability
- **HTML**: Interactive web display
- **Terminal**: Direct ANSI output

---

## Use Cases

### World Maps
Break continents/countries into tiles for navigation and reference.

### Timezone Visualization
Display timezone boundaries with current local times.

### System Diagrams
Visualize network topologies, device meshes, or architecture.

### Game Maps
Procedurally generated or hand-crafted dungeon/world maps.

### Data Visualization
ASCII charts, graphs, and heatmaps with geographic context.

---

## Validation

The parser validates:
- ✅ Tile codes are unique within document
- ✅ Metadata format is valid (KEY:value)
- ✅ ASCII content is present
- ⚠️ Size constraints (warning only, enforced by converter)

---

## Future Enhancements

**v1.1.0:**
- Interactive tile linking (click to navigate)
- Zoom levels (multiple resolutions)
- Overlay support (weather, data layers)

**v1.2.0:**
- Dynamic tile generation from data
- Real-time updates (live sensor data)
- Collaborative multi-user editing

---

## Reference

- **YAML Frontmatter**: Document metadata
- **uPY Scripts**: `\```upy` blocks
- **State Blocks**: `\```state` JSON data
- **Map Tiles**: `\```map` ASCII art

See: [`core/runtime/markdown/`](.) for implementation details.

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-01-04  
**Spec Status:** Stable ✅
