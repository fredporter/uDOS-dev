# uDOS Multiverse Layer System (100-899)

**Alpha v1.0.0.0 - Complete Spatial Universe Definition**

Based on retro teletext/CEEFAX page numbering (100-899), uDOS provides a **finite but immense** multiverse with Earth, virtual dimensions, and interstellar space.

---

## 🌍 Layer Architecture Overview

| Range | Realm | Purpose | Depth Model |
|-------|-------|---------|-------------|
| **100-399** | Earth | Physical world, cities, districts | Hierarchical cells |
| **400-599** | Virtual | Dungeons, game worlds, fantasy realms | Hierarchical cells |
| **600-899** | Interstellar | Solar system, galaxies, deep space | Hierarchical cells |

**Hierarchical System:** Each layer uses 120×50 grid (6,000 cells). Sub-layers created by appending cell coordinates.  
**Example:** `L100-AB15-CD20` = Layer 100, zoom into cell AB15, then zoom into CD20 within that cell.  
**Total Capacity:** Effectively infinite via cell nesting (6,000^depth cells per branch)

---

## 📐 Hierarchical Cell-Based Grid System

Each layer uses a manageable grid that can nest infinitely:
- **Dimensions:** 120 columns × 50 rows = **6,000 cells**
- **Column Codes:** AA-DT (120 columns)
- **Row Codes:** 00-49 (50 rows)
- **Cell Format:** CCNN (2 letters + 2 digits, e.g., AB15, CD20)
- **Cell Precision:** 24×24 pixels at display scale

**Hierarchical Coordinate Format:** `[Realm]-[Region]-L[Layer]-[Cell1]-[Cell2]-[Cell3]...`

Each additional cell = zoom into previous cell, creating unlimited depth.

**Examples:**
- `EARTH-NA01-L100` - North America base layer (6,000 cells)
- `EARTH-NA01-L100-AB15` - Zoom into cell AB15 (6,000 sub-cells within AB15)
- `EARTH-NA01-L100-AB15-CD20` - Zoom into CD20 within AB15 (6,000 sub-cells)
- `EARTH-NA01-L100-AB15-CD20-AA10` - Building level, 3 layers deep
- `VIRTUAL-NETH-L401-BC45` - NetHack dungeon L1, room BC45
- `SPACE-SOL-L605-AB20-CD30` - Mars surface, region AB20, detail CD30

---

## 🌎 EARTH REALM (Layers 100-399)

### Layer 100: World Base Layer
- **Coverage:** Complete Earth surface
- **Grid:** 120×50 = 6,000 cells
- **Precision:** ~333km per cell (40,000km / 120 columns)
- **Purpose:** Continental navigation, timezone detection
- **Data:** `core/data/spatial/locations.json`

**Zoom Example (Sydney):**
```
L100                     → World (333km/cell) - 6,000 cells
L100-AB34                → Australia region (2.77km/cell) - 6,000 cells
L100-AB34-CD15           → Sydney metro (23m/cell) - 6,000 cells
L100-AB34-CD15-AA20      → Sydney CBD building (0.2m/cell) - 6,000 cells
L100-AB34-CD15-AA20-BC10 → Room detail (1.6mm/cell) - 6,000 cells
```

### Hierarchical Navigation

**Depth Levels:**
- **Depth 0:** `L100` - World layer (333km precision)
- **Depth 1:** `L100-AB34` - Continental/country (2.77km precision)
- **Depth 2:** `L100-AB34-CD15` - City/metro (23m precision)
- **Depth 3:** `L100-AB34-CD15-AA20` - Building/room (0.2m precision)
- **Depth 4+:** Unlimited nesting for microscopic detail if needed

**Benefits:**
- Only create detail where needed (sparse data structure)
- Consistent 6,000-cell grid at every level
- Zoom factor: ~120× per level
- Natural map tile size (120×50 = exactly 120 cols × 40-50 rows for ASCII)

### Additional Earth Layers

**Layers 101-199:** Reserved for alternate Earth views
- L101: Historical maps (ancient civilizations)
- L102: Climate zones and weather patterns
- L103: Geological features and fault lines

**Layers 200-299:** Underground/Special Earth Layers
- L200: Subway/metro systems (global)
- L201: Cave systems and underground structures
- L202: Bunker networks and shelters

**Layers 300-399:** Ocean/Underwater
- L300: Ocean surface and mari or VIRTUAL-NETH-L4[LEVEL]-[CELL]

L401                  → Dungeon Level 1 (Entry) - 6,000 cells
L401-BC45             → Specific room in Level 1 - 6,000 sub-cells
L402                  → Dungeon Level 2
...
L425                  → Dungeon Level 25 (Medusa)
L425-AA10             → Medusa's chamber detail
...
L450                  → Dungeon Level 50 (Wizard of Yendor)
```

**Features:**
- 50 base dungeon levels (L401-L450)
- Each level: 120×50 = 6,000 cells (manageable dungeon size)
- Zoom into specific rooms via cell append: `L401-BC45`
- Monsters, traps, items, altars mapped to grid
- State persistence in .udos.md format

**Tile Capacity:** 50 levels × 6,000 base cells + infinite detail via cell nesting
L402: Dungeon Level 2
...
L425: Dungeon Level 25 (Medusa)
...
L450: Dungeon Level 50 (Wizard of Yendor)
```

**Features:**
- 50 procedurally generated dungeon levels
- Each level: 129,600 possible tile placements
- Monsters, traps, items, altars mapped to grid
- State persistence in .udos.md format

**Tile Capacity:** 50 levels × 129,600 tiles = **6.48M tiles**

#### Layer 451: Gnomish Mines (Levels 1-12)
```
L451-01: Mines Level 1
L451-12: Mines Level 12 (Minetown)
```

#### Layer 452: Sokoban (4 puzzle levels)
```
L452-01: Sokoban Level 1
L452-04: Sokoban Level 4 (Prize)
```

#### Layer 453: Quest Levels (Quest dungeon)
```
L453-01: Quest Home Level
L453-05: Quest Goal Level (Nemesis)
```

#### Layer 454-455: Special Planes
```
L454: Elemental Planes (Earth/Air/Fire/Water)
L455: Astral Plane 56 base levels × 6,000 cells + infinite room detailcension)
```

**NetHack Total:** ~7M tiles

### Other Virtual Worlds (Layers 460-599)

#### Layers 460-479: Fantasy Realms
- L460: Middle-earth (Tolkien)
- L461: Narnia (Lewis)
- L462: Westeros (Game of Thrones)
- L463: Discworld (Pratchett)
- L464: Forgotten Realms (D&D)

#### Layers 480-499: Sci-Fi Dimensions
- L480: Foundation Galaxy (Asimov)
- L481: Dune (Arrakis)
- L482: Hitchhiker's Guide universe

#### Layers 500-599: User-Created Worlds
- **Reserved for custom adventures**
- Choose-your-own-adventure paths
- Escape room scenarios
- Educational simulations200 base layers × 6,000 cells + infinite detail via nesting
- Survival challenges

**Virtual Realm Total:** ~25M addressable tiles

---

## 🚀 INTERSTELLAR REALM (Layers 600-899)

### Solar System (Layers 600-699)

#### Layer 600: Solar System Overview
- **Coverage:** Entire Sol system, orbital paths
- **Data:** `core/data/spatial/planets.json`
- **Precision:** 1 AU per cell (~150M km)

#### Layers 601-610: Inner Planets
```
L601: Mercury surface + orbit
L602: Venus surface + orbit
L603: Earth orbit (external view)
L604: Luna (Moon) surface
L605: Mars surface
L606: Phobos/Deimos
```

#### Layers 611-630: Asteroid Belt
```
L611-L630: 20 layers for major asteroids/dwarf planets
- Ceres
- Vesta
- Pallas
```

#### Layers 631-660: Outer Planets & Moons
```
L631: Jupiter system (Io, Europa, Ganymede, Callisto)
L632-635: Jupiter's major moons (detailed)
L641: Saturn system (Titan, Enceladus, Rhea)
L642-645: Saturn's major moons
L651: Uranus system
L661: Neptune system (Triton)
```

#### Layers 670-699: Kuiper Belt & Beyond
```
L671: Pluto/Charon system
L680-699: Kuiper Belt ob100 layers × 6,000 cells + planetary surface detail via nestingloud markers
```

**Solar System Total:** ~12.96M tiles

### Local Group Galaxies (Layers 700-799)

#### Layer 700: Milky Way Overview
- **Data:** `core/data/spatial/galaxies.json`
- **Coverage:** Entire galaxy structure
- **Precision:** 1000 light-years per cell

#### Layers 701-750: Milky Way Sectors
```
L701: Galactic Core (Sagittarius A*)
L710: Orion Arm (Sol's location)
L720: Perseus Arm
L730: Sagittarius Arm
L740: Scutum-Centaurus Arm
```

#### Layers 751-780: Nearby Galaxies
```
L751: Andromeda Galaxy (M31)
L752: Triangulum Galaxy (M33)
L761: Large Magellanic Cloud
L762: Small Magellanic Cloud
L770-780: Local Group d100 layers × 6,000 cells + galactic detail via nesting
```

**Local Group Total:** ~10.37M tiles

### Deep Space (Layers 800-899)

#### Layers 800-850: Virgo Supercluster
```
L800: Virgo Cluster overview
L810-850: Major galaxy clusters
```

#### Layers 851-890: Observable Universe Sectors
```
L851-890: Deep space quasars, galaxy superclusters
Navigation markers for cosmic scale
```

#### Layers 891-899: Reserved for Expansion
```
L891-899: Future exopl100 layers × 6,000 cells + cosmic structure detail via nesting

---

## 📊 Total Capacity Summary

| Realm | Base Layers | Cells per Layer | Base Tiles | Hierarchical Depth |
|-------|-------------|-----------------|------------|-------------------|
| **Earth** | 100-399 (300) | 6,000 | 1.8M | Unlimited via cells |
| **Virtual** | 400-599 (200) | 6,000 | 1.2M | Unlimited via cells |
| **Interstellar** | 600-899 (300) | 6,000 | 1.8M | Unlimited via cells |
| **GRAND TOTAL** | **800 layers** | **6,000** | **4.8M base** | **∞ via nesting** |

**Hierarchical Capacity:**
- Depth 0: 800 layers × 6,000 cells = 4.8M base tiles
- Depth 1: Up to 4.8M × 6,000 = 28.8 billion (only created as needed)
- Depth 2: Up to 28.8B × 6,000 = 172.8 trillion (sparse storage)
- **Effective capacity:** Infinite via cell nesting, stored sparsely

**Storage Benefits:**
- Only store cells that exist (sparse data structure)
- World layer: ~6,000 cells (~60KB JSON)
- City zoom: +6,000 cells per city (~60KB each)
- Building detail: +6,                  # World layer (6,000 cells)
LOCATE EARTH-NA01-L100-AB34             # Zoom to Australia
LOCATE EARTH-NA01-L100-AB34-CD15        # Zoom to Sydney metro
LOCATE EARTH-NA01-L100-AB34-CD15-AA20   # Zoom to specific building
ZOOM IN AB34                            # Zoom into current cell
ZOOM OUT                                # Go back up one level
```

### Virtual Navigation
```
LOCATE VIRTUAL-NETH-L401                # Dungeon level 1 (6,000 cells)
LOCATE VIRTUAL-NETH-L401-BC45           # Specific room in level 1
DESCEND                                 # L401 → L402 (down stairs)
ASCEND                                  # L402 → L401 (up stairs)
LOCATE VIRTUAL-NETH-L425                # Medusa's level
LOCATE VIRTUAL-NETH-L425-AA10           # Zoom to Medusa's chamber
```

### Interstellar Navigation
```
LOCATE SPACE-SOL-L605                   # Mars surface (6,000 cells)
LOCATE SPACE-SOL-L605-AB20              # Mars region
LOCATE SPACE-SOL-L605-AB20-CD30         # Detailed Mars terrain
LOCATE SPACE-MW-L710                    # Orion Arm sector
WARP SPACE-MW-L751                      # Jump to Andromeda Galaxy
```

### Virtual Navigation
```
LOCATE VIRTUAL-NETH-L401AA01        # NetHack dungeon entrance
DESCEND VIRTUAL-NETH-L401 → L402    # Go down one level
LOCATE VIRTUAL-NETH-L425BC10        # Medusa's level
```

### Interstellar Navigation
```
LOCATE SPACE-SOL-L605AB20           # Mars surface
LOCATE SPACE-MW-L710CD30            # Orion Arm sector
WARP SPACE-SOL-L603 → SPACE-MW-L751 # Earth orbit → Andromeda
```

---

## 🎯 NetHack Integration Plan

### Phase 1: Core Mapping (v1.0.0.1)
- [x] Define layers 400-455 for NetHack dungeon
- [ ] Create `core/data/virtual/nethack_levels.json` with level metadata
- [ ] Map dungeon features to grid coordinates
- [ ] Implement DESCEND/ASCEND commands for level transitions

### Phase 2: Tutorial Adventure (v1.0.0.2)
- [ ] Create `memory/adventures/nethack-tutorial.udos.md`
- [ ] Choose-your-own-adventure narrative
- [ ] Map exploration with grid-based movement
- [ ] Monster encounters, treasure hunting
- [ ] State persistence (inventory, HP, level progress)

### Phase 3: Plugin System (v1.0.3.0)
- [ ] Add NetHack to Wizard Server plugin repository
- [ ] Package recipe: https://github.com/NetHack/NetHack
- [ ] TCZ builder for Tiny Core Linux compatibility
- [ ] QR relay for large plugin distribution (NetHack ~10MB)

### Phase 4: Live Play Integration (v1.1.0+)
- [ ] Real NetHack binary integration
- [ ] Terminal adapter (NetHack TTY → uDOS TUI)
- [ ] Save state mapping (.udos.md ↔ NetHack save files)
- [ ] Multiplayer via MeshCore P2P

---

## 🔐 Virtual World Rules

### Privacy & Offline
- All virtual worlds playable offline
- State stored in `memory/adventures/*.udos.md`
- No cloud dependency for single-player
from typing import List, Optional

class GridCoordinate:
    realm: str              # 'EARTH', 'VIRTUAL', 'SPACE'
    region: str             # 'NA01', 'NETH', 'SOL'
    layer: int              # 100-899 (base layer)
    cells: List[str] = []   # Hierarchical cells: ['AB34', 'CD15', 'AA20']
    
    @property
    def code(self) -> str:
        """Generate full hierarchical coordinate."""
        base = f"{self.realm}-{self.region}-L{self.layer}"
        if self.cells:
            return base + "-" + "-".join(self.cells)
        return base
    
    @property
    def depth(self) -> int:
        """Get zoom depth (0 = base layer, 1+ = zoomed)."""
        return len(self.cells)
    
    def zoom_into(self, cell: str) -> 'GridCoordinate':
        """Create new coordinate zoomed into specified cell."""
        return GridCoordinate(
            realm=self.realm,
            region=self.region,
            layer=self.layer,
            cells=self.cells + [cell]
        )
    
    def zoom_out(self) -> Optional['GridCoordinate']:
        """Go back up one level."""
        if not self.cells:
            return None  # Already at base
        return GridCoordinate(
            realm=self.realm,
            region=self.region,
            layer=self.layer,
            cells=self.cells[:-1]
        )
    
    def parse_cell(cell: str) -> tuple[str, int]:
        """Parse cell code like 'AB15' into column='AB', row=15."""
        if len(cell) != 4:
            raise ValueError(f"Invalid cell format: {cell}")
        column = cell[:2]
        row = int(cell[2:])
        return column, row

---

##Hierarchical Universe:** 800 base layers × 6,000 cells = 4.8M base tiles, infinite via cell nesting  
**Real-World Precision:** 0.2 meters at depth 3 (building level), 1.6mm at depth 4  
**Virtual Depth:** 50+ NetHack dungeon levels, zoom into any room  
**Cosmic Scale:** Sol system to Virgo Supercluster coverage  
**Storage Efficiency:** Sparse hierarchical storage, ~100MB vs 1GB flat model

The uDOS multiverse uses **hierarchical cell-based layers** — zoom infinitely into any cell, store only what exists, ready for offline exploration and interstellar navigation
class GridCoordinate:
    realm: str  # 'EARTH', 'VIRTUAL', 'SPACE'
    region: str  # 'NA01', 'NETH', 'SOL'
    layer: int  # 100-899
    column: str  # AA-RZ
    row: int  # 00-270

    @property
    def code(self) -> str:
        return f"{self.realm}-{self.region}-L{self.layer}{self.column}{self.row:02d}"
```

### Map Layer Manager Extensions

Update `core/services/map_layer_manager.py`:
```python
class MapLayerManager:
    def load_layer(self, realm: str, region: str, layer: int) -> MapLayer:
        """Load layer from appropriate data source."""
        if realm == "EARTH":
            return self._load_earth_layer(layer)
        elif realm == "VIRTUAL":
            return self._load_virtual_layer(region, layer)
        elif realm == "SPACE":
            return self._load_space_layer(region, layer)
```

### Data File Structure
```
core/data/spatial/
├── locations.json          # Earth layers 100-399
├── planets.json            # Solar system layers 600-699
├── galaxies.json           # Milky Way/Local Group 700-799
└── virtual/
    ├── nethack_levels.json # Dungeon layers 400-455
    ├── fantasy_realms.json # Layers 460-479
    └── scifi_worlds.json   # Layers 480-499
```

---

## 📚 References

- **Teletext Standard:** 100-899 page numbering (CEEFAX, BBC)
- **NetHack:** https://github.com/NetHack/NetHack
- **Spatial Computing:** `core/runtime/markdown/SPATIAL-COMPUTING.md`
- **Map Tiles:** `core/runtime/markdown/parser.py` (ASCII map support)
- **Plugin System:** `dev/roadmap/WIZARD-PLUGIN-SYSTEM.md`

---

**Total Finite Universe:** 103.68 million addressable tiles across 800 layers  
**Real-World Precision:** 3 meters at Earth district layers  
**Virtual Depth:** 50+ NetHack dungeon levels, infinite custom worlds  
**Cosmic Scale:** Sol system to Virgo Supercluster coverage

The uDOS multiverse is **finite but vast**, ready for offline exploration, choose-your-own-adventure gameplay, and interstellar navigation — all in `.udos.md` format.

---

*Last Updated: 2026-01-04*  
*Alpha v1.0.0.0 - Multiverse Layer System*
