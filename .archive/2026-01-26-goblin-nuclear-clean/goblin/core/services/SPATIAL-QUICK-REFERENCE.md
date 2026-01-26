# Spatial Computing Quick Reference

**uDOS Alpha v1.0.0.0 - Spatial Layer**

---

## Grid Coordinate Format

```
[Region]-L[Layer][Column][Row]

Examples:
NA01-L9AA10  →  North America, Layer 9, grid AA10
EU01-L3BC45  →  Europe, Layer 3, grid BC45
L0AA00       →  World layer (no region)
```

## Layers

| L# | Precision | Use Case |
|----|-----------|----------|
| L0 | 3000km | World |
| L3 | 100km | City |
| L6 | 3km | Neighborhood |
| L9 | 3m | Building/Room |

---

## Transport Ranges

| Method | Range | Code |
|--------|-------|------|
| NFC | 10cm | `PROXIMITY.nfc(target)` |
| Bluetooth | 10m | `PROXIMITY.bluetooth(target, 10.0)` |
| MeshCore | 100m | `PROXIMITY.mesh(target, 100.0)` |

---

## Common Patterns

### Location Check
```python
if LOCATION.verify("NA01-L9AA10", tolerance=10.0):
    OUTPUT("At location!")
```

### Proximity Check
```python
if PROXIMITY.bluetooth("DEVICE-42", max_meters=5.0):
    OUTPUT("Device in range!")
```

### NFC Verification
```python
if NFC.verify("RING-001"):
    OUTPUT("Ring verified!")
```

### Multi-Factor
```python
loc = LOCATION.verify("NA01-L9AA10", tolerance=5.0)
nfc = NFC.verify("RING-001")
prox = PROXIMITY.bluetooth("DEVICE-42", 5.0)

if loc and nfc and prox:
    OUTPUT("All conditions met!")
```

### Place Object
```python
OBJECT.place(
    id="treasure-001",
    type="unlock",
    grid_code="NA01-L9BC45",
    virtual=True,
    content={"key": "SECRET"},
    conditions=[
        {"type": "location", "parameters": {"grid": "NA01-L9BC45", "tolerance": 5.0}}
    ]
)
```

### Find Objects
```python
nearby = OBJECT.find(radius=50.0)
for obj in nearby:
    OUTPUT(f"{obj['id']} at {obj['location']}")
```

### Location-Based Unlock
```python
if UNLOCK.at_location(data, "NA01-L9BC45", tolerance=10.0):
    OUTPUT("Unlocked at location!")
```

---

## .udos.md Template

```markdown
---
title: Spatial Script
type: spatial
requires_location: true
requires_nfc: false
---

# Description

```upy
# Set location
LOCATION.set("NA01-L9AA10")

# Conditional logic
if LOCATION.verify("NA01-L9AA10", tolerance=10.0):
    OUTPUT("At target location!")
\```

```map
TILE:NA01-L9AA10 NAME:Location ZONE:America/Los_Angeles
[ASCII map 120x40]
\```

```state
{
  "current_location": null,
  "objects_found": []
}
\```
```

---

## Files

- **Implementation:** `core/services/spatial_manager.py`
- **Map Layers:** `core/services/map_layer_manager.py`
- **APIs:** `core/runtime/upy/safe_builtins.py`
- **Docs:** `core/runtime/markdown/SPATIAL-COMPUTING.md`
- **Examples:** `memory/examples/spatial-computing.udos.md`

---

## Tests

```bash
# Run spatial tests
python core/tests/test_spatial_computing.py

# Example script
udos memory/examples/spatial-computing.udos.md --execute
```

---

**Privacy:** All offline, encrypted GPS, no cloud  
**Security:** Multi-factor spatial authentication  
**Format:** Everything in .udos.md (human + machine readable)
