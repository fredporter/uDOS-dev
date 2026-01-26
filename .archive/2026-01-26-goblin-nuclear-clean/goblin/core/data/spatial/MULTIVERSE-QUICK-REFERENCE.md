# uDOS Multiverse Quick Reference

**100.7 Billion Tiles Across 800 Layers**

---

## Layer Ranges

| Range | Realm | Tiles | Examples |
|-------|-------|-------|----------|
| **100-399** | Earth | 38.88M | Cities, districts, buildings |
| **400-599** | Virtual | 25.92M | Dungeons, fantasy worlds |
| **600-899** | Interstellar | 38.88M | Planets, galaxies, deep space |

---

## Coordinate Format

```
[REALM]-[REGION]-L[LAYER][COLUMN][ROW]

EARTH-NA01-L100AA10      # World layer, North America
EARTH-OC-AU-SYD-L301CD45 # Sydney building
VIRTUAL-NETH-L401BC45    # NetHack dungeon level 1
SPACE-SOL-L605AB20       # Mars surface
SPACE-MW-L710CD30        # Orion Arm sector
```

---

## Key Layers

### Earth
- **L100:** World base (83km precision)
- **L200-299:** Cities (300m precision)
- **L300-399:** Districts (3m precision)

### Virtual
- **L401-450:** NetHack Dungeon (50 levels)
- **L451:** Gnomish Mines
- **L452:** Sokoban puzzles
- **L453:** Quest dungeon
- **L454:** Elemental Planes
- **L455:** Astral Plane (ascension)
- **L460-499:** Fantasy realms (Middle-earth, Narnia, etc.)
- **L500-599:** User-created worlds

### Interstellar
- **L600:** Solar system overview
- **L601-610:** Inner planets (Mercury, Venus, Earth, Mars)
- **L631-660:** Outer planets (Jupiter, Saturn, Uranus, Neptune)
- **L700:** Milky Way overview
- **L710:** Orion Arm (Sol's location)
- **L751:** Andromeda Galaxy
- **L800-899:** Deep space, galaxy clusters

---

## Navigation Commands

```
LOCATE [coordinate]              # Jump to location
ZOOM IN EARTH-NA01-L100 → L200  # Zoom to detail layer
DESCEND VIRTUAL-NETH-L401       # Go down dungeon level
WARP SPACE-SOL-L603 → L751      # Interstellar travel
MAP [layer]                      # Show layer map
```

---

## Grid System

- **480 columns** × **270 rows** = **129,600 cells/layer**
- **Column codes:** AA-RZ (480 columns)
- **Row codes:** 00-270 (271 rows)
- **Total capacity:** 800 layers × 129,600 = **103.68M tiles**

---

## Data Files

- `core/data/locations.json` - Earth layers
- `core/data/spatial/locations.json` - Detailed Earth
- `core/data/spatial/planets.json` - Solar system
- `core/data/spatial/galaxies.json` - Milky Way/Local Group
- `core/data/virtual/nethack_levels.json` - NetHack dungeon

---

## NetHack Integration

**Tutorial:** `memory/adventures/nethack-tutorial.udos.md`  
**Layers:** 400-455 (56 dungeon levels)  
**Plugin:** Install via Wizard Server v1.0.3.0+  
**Source:** https://github.com/NetHack/NetHack

---

**Complete System:** 103.68M addressable tiles, offline-playable, .udos.md format  
**Distribution:** QR/Audio relay via Wizard Server mesh

---

*Alpha v1.0.0.0*
