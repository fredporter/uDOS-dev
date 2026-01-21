---
title: Spatial Computing & Location-Aware Scripts
type: documentation
version: 1.0.0
date: 2026-01-04
author: uDOS Core Team
---

# 🗺️ Spatial Computing in uDOS

**Alpha v1.0.0.0** introduces spatial computing capabilities that enable location-aware scripts with conditional logic, proximity detection, and real-world object placement.

---

## Overview

uDOS spatial computing combines:

1. **Hierarchical Grid System** - L0-L9 layers (3km → 3m precision)
2. **Location Verification** - GPS, grid coordinates, proximity detection
3. **Conditional Logic** - uPY v0.2 with if/then spatial conditions
4. **Transport Integration** - NFC, Bluetooth, MeshCore P2P
5. **Object Placement** - Virtual items at real/virtual locations
6. **Map Layers** - ASCII map tiles at multiple zoom levels
7. **.udos.md Integration** - Human + machine readable spatial documents

---

## Grid Coordinate System

### Layer Hierarchy

| Layer | Precision | Use Case | Example |
|-------|-----------|----------|---------|
| L0 | 3000km | World | Continents |
| L1 | 1000km | Continent | Countries |
| L2 | 300km | Country | States/provinces |
| L3 | 100km | Region | Cities |
| L4 | 30km | City | Districts |
| L5 | 10km | District | Neighborhoods |
| L6 | 3km | Neighborhood | Blocks |
| L7 | 1km | Block | Building groups |
| L8 | 300m | Building group | Individual buildings |
| L9 | 3m | Building | Rooms/objects |

### Grid Code Format

**Structure:** `[Region]-L[Layer][Column][Row]`

**Examples:**
- `NA01-L3AA10` - North America, Layer 3 (city), grid AA10
- `EU01-L9BC45` - Europe, Layer 9 (building), grid BC45
- `L0AA00` - World layer, grid AA00 (no region)

**Components:**
- **Region:** Map tile region code (NA01, EU01, AS01, etc.)
- **Layer:** 0-9 (lower = less precise, higher = more precise)
- **Column:** AA-ZZ (676 possible columns)
- **Row:** 00-99 (100 rows per column)

### Lat/Long Translation

Grid coordinates can translate to lat/long:

```python
# Grid → Lat/Long
grid = GridCoordinate(layer=9, column="BC", row=45, region="NA01")
lat, lon = spatial_manager.grid_to_latlong(grid)

# Lat/Long → Grid
grid = spatial_manager.latlong_to_grid(37.7749, -122.4194, layer=9, region="NA01")
```

**3-Meter Accuracy at L9:**
- L9 grids are 3m × 3m squares
- Sufficient for room-level positioning
- Comparable to GPS accuracy in open areas
- Better than GPS in urban canyons (when using MeshCore)

---

## Transport Methods

### NFC (Near Field Communication)

**Range:** 10cm (physical contact)

**Use Cases:**
- Physical verification ("you are here")
- NFC ring authentication
- Secure key exchange
- Object activation/unlocking

**Example:**
```python
if NFC.verify("RING-001-ALPHA"):
    OUTPUT("✅ Physical presence verified")
```

### Bluetooth

**Range:** 10 meters (adjustable)

**Use Cases:**
- Near-field unlocking
- Device pairing
- Proximity detection
- Indoor positioning

**Example:**
```python
if PROXIMITY.bluetooth("DEVICE-42", max_meters=5.0):
    OUTPUT("🔓 Device in Bluetooth range")
```

### MeshCore P2P

**Range:** 100 meters (multi-hop unlimited)

**Use Cases:**
- Off-grid networking
- Device mesh presence
- Location sharing without GPS
- P2P data transfer

**Example:**
```python
if PROXIMITY.mesh("NODE-123", max_meters=100.0):
    OUTPUT("📡 In mesh network range")
```

### Encrypted GPS

**Range:** Global

**Use Cases:**
- Location verification
- Grid positioning
- Outdoor navigation
- Geofencing

**Privacy:** GPS data is encrypted before transmission, never sent unencrypted over public networks.

---

## uPY v0.2 Spatial APIs

### LOCATION API

```python
# Get current location
location = LOCATION.get()
# Returns: {'grid': 'NA01-L9AA10', 'layer': 9, 'column': 'AA', 'row': 10, 'region': 'NA01'}

# Set current location
LOCATION.set("NA01-L9BC45")

# Verify at location (with tolerance)
if LOCATION.verify("NA01-L9BC45", tolerance=10.0):
    OUTPUT("✅ At required location")

# Get distance to target
distance = LOCATION.distance_to("NA01-L9BC50")
OUTPUT(f"Distance: {distance:.1f} meters")
```

### PROXIMITY API

```python
# Check proximity via transport
if PROXIMITY.check("bluetooth", "DEVICE-42", max_distance=10.0):
    OUTPUT("In range")

# Convenience methods
PROXIMITY.nfc("TARGET")          # 10cm range
PROXIMITY.bluetooth("TARGET", 10.0)  # 10m range
PROXIMITY.mesh("TARGET", 100.0)      # 100m range
```

### NFC API

```python
# Check if NFC available
if NFC.available():
    # Verify ring identity
    if NFC.verify("RING-001-ALPHA"):
        OUTPUT("✅ Ring verified")
    
    # Challenge-response authentication
    if NFC.verify("RING-001-ALPHA", challenge="auth-2026"):
        OUTPUT("🔐 Full authentication")
```

### OBJECT API

```python
# Place object at location
OBJECT.place(
    id="treasure-001",
    type="unlock",
    grid_code="NA01-L9BC45",
    virtual=True,  # or False for real-world object
    content={"message": "Found it!", "points": 100},
    conditions=[
        {"type": "location", "parameters": {"grid": "NA01-L9BC45", "tolerance": 5.0}},
        {"type": "nfc", "parameters": {"ring_id": "RING-001-ALPHA"}}
    ]
)

# Find objects near location
nearby = OBJECT.find(grid_code="NA01-L9BC45", radius=50.0)
for obj in nearby:
    OUTPUT(f"Found: {obj['id']} at {obj['location']}")
```

### UNLOCK API

```python
# Location-based decryption
if UNLOCK.at_location(encrypted_data, "NA01-L9BC45", tolerance=10.0):
    OUTPUT("🔓 Data unlocked at correct location")

# Proximity-based decryption
if UNLOCK.near_device(encrypted_data, "bluetooth", "DEVICE-42"):
    OUTPUT("🔓 Data unlocked near device")
```

---

## Conditional Logic

uPY v0.2 supports standard Python conditionals for spatial logic:

### Single Condition

```python
if LOCATION.verify("NA01-L9AA10", tolerance=5.0):
    OUTPUT("✅ Access granted")
else:
    OUTPUT("❌ Wrong location")
```

### Multiple Conditions (AND)

```python
location_ok = LOCATION.verify("NA01-L9AA10", tolerance=5.0)
nfc_ok = NFC.verify("RING-001-ALPHA")
proximity_ok = PROXIMITY.bluetooth("DEVICE-42", 5.0)

if location_ok and nfc_ok and proximity_ok:
    OUTPUT("🎉 All conditions met - full access")
else:
    OUTPUT("❌ Not all conditions satisfied")
```

### Multiple Conditions (OR)

```python
# Grant access via any method
if NFC.verify("RING-001-ALPHA"):
    OUTPUT("✅ NFC access")
elif PROXIMITY.bluetooth("DEVICE-42", 5.0):
    OUTPUT("✅ Bluetooth access")
elif LOCATION.verify("NA01-L9AA10", tolerance=10.0):
    OUTPUT("✅ Location access")
else:
    OUTPUT("❌ No access method succeeded")
```

### Nested Conditions

```python
if LOCATION.verify("NA01-L9AA10", tolerance=10.0):
    # At correct location
    if NFC.available():
        # NFC is available - use it
        if NFC.verify("RING-001-ALPHA"):
            OUTPUT("🔐 Maximum security access")
        else:
            OUTPUT("⚠️ At location but NFC failed")
    else:
        # NFC not available - use proximity
        if PROXIMITY.bluetooth("DEVICE-42", 10.0):
            OUTPUT("🔓 Location + Bluetooth access")
        else:
            OUTPUT("⏸️ At location, waiting for device")
else:
    OUTPUT("❌ Not at required location")
```

---

## Use Cases

### 1. Location-Based Data Access

**Scenario:** Decrypt field notes only when at field site

```python
site_grid = "NA01-L9BC45"

if LOCATION.verify(site_grid, tolerance=10.0):
    # Decrypt and display field notes
    notes = UNLOCK.at_location(encrypted_notes, site_grid)
    OUTPUT(notes)
else:
    OUTPUT("Travel to site to access notes")
    distance = LOCATION.distance_to(site_grid)
    OUTPUT(f"Distance: {distance:.1f}m away")
```

### 2. Proximity-Based Device Pairing

**Scenario:** Pair with field sensor when in Bluetooth range

```python
sensor_id = "SENSOR-ENV-001"

if PROXIMITY.bluetooth(sensor_id, max_meters=5.0):
    # In range - read sensor data
    OUTPUT("📊 Sensor detected - reading data...")
    # COMMAND("MESH.PAIR", device=sensor_id)
    # data = COMMAND("MESH.READ", device=sensor_id)
else:
    OUTPUT(f"Move closer to sensor {sensor_id}")
```

### 3. NFC Ring Authentication

**Scenario:** Verify physical presence before unlocking secure data

```python
if not NFC.available():
    OUTPUT("⚠️ NFC not available on this device")
else:
    if NFC.verify("ADMIN-RING-001", challenge="daily-auth"):
        OUTPUT("🔐 Admin authenticated")
        # Grant admin access
    else:
        OUTPUT("❌ Authentication failed - tap ring")
```

### 4. Treasure Hunt / Scavenger Hunt

**Scenario:** Find virtual treasures at real-world locations

```python
treasures = [
    {"id": "T1", "grid": "NA01-L9AA10", "name": "Golden Gate"},
    {"id": "T2", "grid": "NA01-L9AB15", "name": "Alcatraz"},
    {"id": "T3", "grid": "NA01-L9AC20", "name": "Pier 39"}
]

for treasure in treasures:
    if LOCATION.verify(treasure['grid'], tolerance=10.0):
        if NFC.verify("PLAYER-RING"):
            OUTPUT(f"✨ Found: {treasure['name']}!")
            # Mark collected
        else:
            OUTPUT(f"📍 Treasure here! Tap ring to collect")
```

### 5. Geofenced Automation

**Scenario:** Trigger actions when entering/leaving area

```python
home_grid = "NA01-L9AA10"
work_grid = "NA01-L9BC45"

if LOCATION.verify(home_grid, tolerance=50.0):
    OUTPUT("🏠 At home - enabling home network")
    # COMMAND("MESH.JOIN", network="home")
    
elif LOCATION.verify(work_grid, tolerance=50.0):
    OUTPUT("🏢 At work - enabling work network")
    # COMMAND("MESH.JOIN", network="work")
    
else:
    OUTPUT("📍 Mobile mode - using public mesh")
    # COMMAND("MESH.JOIN", network="public")
```

### 6. Multi-Factor Spatial Authentication

**Scenario:** Require location + device + ring for vault access

```python
vault_grid = "NA01-L9BC45"
vault_device = "VAULT-CONTROLLER-001"
admin_ring = "ADMIN-RING-001"

# Check all three factors
location_ok = LOCATION.verify(vault_grid, tolerance=3.0)
device_ok = PROXIMITY.nfc(vault_device)  # Must be at NFC range
ring_ok = NFC.verify(admin_ring)

if location_ok and device_ok and ring_ok:
    OUTPUT("🎉 VAULT ACCESS GRANTED")
    OUTPUT("All three factors verified:")
    OUTPUT(f"  ✅ Location: {vault_grid}")
    OUTPUT(f"  ✅ Device: {vault_device}")
    OUTPUT(f"  ✅ Ring: {admin_ring}")
    
    # Unlock vault
    if UNLOCK.at_location(vault_data, vault_grid, tolerance=3.0):
        OUTPUT("🔓 Vault opened")
else:
    OUTPUT("❌ VAULT ACCESS DENIED")
    OUTPUT("Requirements:")
    OUTPUT(f"  {'✅' if location_ok else '❌'} Be at vault location")
    OUTPUT(f"  {'✅' if device_ok else '❌'} Touch NFC reader")
    OUTPUT(f"  {'✅' if ring_ok else '❌'} Present admin ring")
```

---

## Map Layer Integration

### Hierarchical Navigation

Navigate from city level down to building level:

```python
# Start at city level
LOCATION.set("NA01-L3AA10")  # San Francisco, city level
OUTPUT(f"City level: {LOCATION.get()['grid']}")

# Zoom to neighborhood
LOCATION.set("NA01-L6AA10")  # Same coordinates, higher precision
OUTPUT(f"Neighborhood level: {LOCATION.get()['grid']}")

# Zoom to building
LOCATION.set("NA01-L9AA10")  # Room-level precision
OUTPUT(f"Building level: {LOCATION.get()['grid']}")
```

### Layer-Specific Objects

Place objects at appropriate layers:

```python
# City-level beacon
OBJECT.place(
    id="city-center",
    type="beacon",
    grid_code="NA01-L3AA10",  # City layer
    virtual=False,
    content={"name": "San Francisco City Center"}
)

# Building-level treasure
OBJECT.place(
    id="office-key",
    type="unlock",
    grid_code="NA01-L9BC45",  # Building layer
    virtual=True,
    content={"key": "ABC123"}
)
```

---

## .udos.md Spatial Documents

All spatial logic lives in human-readable `.udos.md` files:

**Structure:**
```markdown
---
title: Spatial Script
type: spatial
requires_location: true
requires_nfc: false
---

# Description

Human-readable explanation of spatial logic

## Example

```upy
# Machine-executable spatial conditions
if LOCATION.verify("NA01-L9AA10", tolerance=10.0):
    OUTPUT("At location!")
\```

```map
TILE:NA01 NAME:Location ZONE:America/Los_Angeles
[ASCII map showing location]
\```

```state
{
  "current_location": null,
  "objects_found": []
}
\```
```

**Benefits:**
- Single source of truth
- Human + machine readable
- Version control friendly
- Portable across devices
- Offline-first

---

## Privacy & Security

### GPS Encryption

- GPS coordinates encrypted before storage
- Never transmitted unencrypted over networks
- Decrypted only on local device
- User controls location sharing

### Transport Security

- **NFC:** Physical proximity required (10cm)
- **Bluetooth:** Encrypted pairing only
- **MeshCore:** E2E encrypted P2P
- **No Cloud:** All verification happens offline

### Location Data

- Stored only in user's `~/.udos/bank/system/spatial.json`
- Never leaves device without explicit user action
- Can be cleared at any time
- Opt-in for all location features

---

## Technical Architecture

```
┌─────────────────────────────────────────┐
│        uPY v0.2 Script Layer            │
│  (LOCATION, PROXIMITY, NFC, UNLOCK)     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       Spatial Manager                   │
│  - Grid coordinate system               │
│  - Transport integration                │
│  - Condition evaluation                 │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼────┐  ┌──▼─────┐
│  NFC  │  │  BT   │  │  Mesh  │
│ Ring  │  │Device │  │ Core   │
└───────┘  └───────┘  └────────┘
```

**Components:**
1. **uPY Safe Builtins** - Spatial APIs for scripts
2. **Spatial Manager** - Core spatial logic
3. **Map Layer Manager** - Hierarchical grid system
4. **Device Manager** - Transport availability
5. **.udos.md Parser** - Document integration

---

## Examples

See:
- [`memory/examples/spatial-computing.udos.md`](../examples/spatial-computing.udos.md) - Complete examples
- [`core/services/spatial_manager.py`](../../core/services/spatial_manager.py) - Implementation
- [`core/services/map_layer_manager.py`](../../core/services/map_layer_manager.py) - Map layers

---

## Future Enhancements

**v1.0.1.0+:**
- Real-time GPS integration
- Bluetooth RSSI distance calculation
- NFC ring hardware support
- Indoor positioning (Bluetooth beacons)
- AR/camera-based positioning

**v1.0.2.0+:**
- Multi-user spatial collaboration
- Shared object placement
- Real-time location sharing (opt-in)
- Spatial chat/messaging

**v1.0.3.0+:**
- Machine learning location prediction
- Automated geofencing
- Spatial analytics
- Heat maps and patterns

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-01-04  
**Status:** Specification + Implementation Complete ✅  
**uDOS Version:** Alpha v1.0.0.0
