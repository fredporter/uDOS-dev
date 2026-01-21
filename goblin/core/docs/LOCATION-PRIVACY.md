# uDOS Location Privacy System (v1.0.0.56+)

## Overview

uDOS implements a **privacy-first location system** that:
- Masks all location data in logs by default
- Requires explicit user consent for location-tagged publications
- Supports celestial navigation (star sighting) as a GPS-free alternative
- Aligns Solar System layer with your actual sky view

---

## Privacy Levels

| Level | Description | Log Format | Use Case |
|-------|-------------|------------|----------|
| `none` | No location stored | `[LOCATION REDACTED]` | Maximum privacy |
| `hashed` | Only user can decode | `loc:a7f3b2c1d8e9` | Retrievable by owner |
| `regional` | 11km precision (DEFAULT) | `L300:BD14-a7f3` | General area visible |
| `full` | 3.1m precision | `L300:BD14:AA10:BB15:CC20` | Opt-in only |

### Log Masking Example

```
Full address:    L300:BD14:AA10:BB15:CC20
Masked (logs):   L300:BD14-a7f3
```

The regional tile (BD14 = ~668km area) is visible, but precision coordinates are hashed.

---

## Commands

```
LOCATION                    Show status
LOCATION SET <tile>         Set location manually (most private)
LOCATION SET <lat> <lon>    Set from coordinates
LOCATION PRIVACY <level>    Change privacy level
LOCATION SKY                Show visible celestial bodies
LOCATION STARS              Navigation stars currently visible
LOCATION NAVIGATE           Star-based navigation guide
LOCATION ALIGN              Solar System layer aligned to your sky
LOCATION CONSENT            Show publication consent prompt
LOCATION CLEAR              Clear location data
```

### Shortcuts

```
SKY                         Same as LOCATION SKY
STARS                       Same as LOCATION STARS
```

---

## Celestial Navigation

Navigate without GPS using the stars:

### Finding North (Northern Hemisphere)
1. Locate the Big Dipper (Ursa Major)
2. Draw a line through the two "pointer" stars
3. Follow 5× that distance to find Polaris
4. Polaris marks true north

### Finding Latitude
- Measure Polaris altitude above horizon
- Polaris altitude ≈ your latitude
- Example: Polaris at 45° = ~45°N latitude

### uDOS Integration
```
LOCATION SET L300:BD14      Set approximate location
LOCATION SKY                See what's in your sky
LOCATION NAVIGATE           Get navigation guidance
```

---

## Solar System Alignment

The Solar System layer (L600-699) aligns with your Earth location:

```
┌─────────────────────────────────────────┐
│  Your Earth tile: L300:BD14-a7f3        │
│  Solar layer: L600                       │
│                                          │
│  WHAT'S IN YOUR SKY:                     │
│  ⭐ Polaris     N      45.0°  mag: 2.0   │
│  ☀️ Sun        SW     32.5°  mag:-26.7  │
│  🌙 Moon       SE     48.2°  mag:-12.0  │
│  🪐 Venus      W      25.0°  mag:-4.0   │
└─────────────────────────────────────────┘
```

This enables:
- Looking up "stars in my sky" from your location
- Identifying celestial bodies for navigation
- Understanding the night sky without internet

---

## Location Sources

| Source | Privacy | Description |
|--------|---------|-------------|
| `manual` | ★★★★★ | User enters tile address directly |
| `star_sight` | ★★★★☆ | Calculated from star observations |
| `compass` | ★★★☆☆ | Compass + landmark reference |
| `network` | ★★☆☆☆ | WiFi/cell tower inference |
| `gps` | ★☆☆☆☆ | GPS hardware (most accurate, least private) |

---

## Publication Consent

uDOS **ALWAYS** prompts before publishing location-tagged content:

```
📍 LOCATION CONSENT

Action: publish
Current location: L300:BD14-a7f3

Privacy options:
  ● Full location (3.1m precision)
      ⚠️ Exact location will be visible
  ○ Regional only (11km precision)
      ⚠️ General area will be visible
  ○ Hashed (only you can decode)
      ⚠️ Location hidden but retrievable by you
  ○ No location
      ⚠️ Content will have no location tag

uDOS ALWAYS asks before publishing location data.
```

---

## Transport Policy

Location data follows strict transport rules:

| Transport | Location Data Allowed |
|-----------|----------------------|
| MeshCore (private) | ✅ Encrypted only |
| Bluetooth Private | ✅ Paired devices |
| NFC | ✅ Physical contact |
| QR Relay | ✅ Visual transfer |
| Bluetooth Public | ❌ NEVER |
| Internet | ❌ NEVER from device mesh |
| Wizard Server | ⚠️ Calculate only, no storage |

---

## Implementation Files

- [location_service.py](../services/location_service.py) - Core service
- [location_handler.py](../commands/location_handler.py) - CLI commands
- [logging_manager.py](../services/logging_manager.py) - LocationMaskingFilter
- [tile_hierarchy.py](../services/tile_hierarchy.py) - Grid coordinate system

---

*Last Updated: 2026-01-06*
*Version: Alpha v1.0.0.56*
