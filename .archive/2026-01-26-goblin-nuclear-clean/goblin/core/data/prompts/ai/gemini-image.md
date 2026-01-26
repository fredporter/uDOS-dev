---
id: gemini-image
provider: gemini
model: gemini-2.0-flash
version: 1.0.0
created: 2026-01-06
author: uDOS Dev Mode
tags: [ai, image, generation, graphics, svg, teletext]
---

# Gemini Image Generation Prompts

## Overview

Gemini AI prompts for generating visual content in uDOS. Supports multiple
output formats including SVG, teletext graphics, ASCII art, and nano-banana style.

## Available Styles

| Style | Description | Use Case |
|-------|-------------|----------|
| Technical-Kinetic | MCM geometry, B&W, mechanical | Technical docs, diagrams |
| Nano-Banana | Playful minimalism, geometric | Icons, UI elements |
| Teletext | WST mosaic, 8-color | System UI, retro graphics |
| ASCII/PETSCII | C64 block characters | TUI, terminal art |

---

## Technical-Kinetic (Default SVG)

### Description

Mid-century modern geometry merged with kinetic art elements.
Strict black and white only - no gradients, no grays.

### Palette

- Black: `#000000` - Primary strokes and fills
- White: `#FFFFFF` - Background and negative space

### Pattern Library

| Pattern | Use | Example |
|---------|-----|---------|
| Hatching | Shading, depth | `45° parallel lines, 2px spacing` |
| Cross-hatch | Dense shading | `45° + 135° overlay` |
| Stipple | Gradients, fog | `Random dots, density varies` |
| Wavy lines | Flow, movement | `Sine wave paths` |
| Dashed | Technical, structure | `4px dash, 2px gap` |

### Geometry Elements

- Circles and arcs
- Straight lines and rays
- Triangles and polygons
- Precise tangent points
- Geometric intersections

### Kinetic Elements

- Gears and cogs (mechanical)
- Conduits and pipes (flow)
- Levers and pivots (motion)
- Trajectories and paths
- Dynamic balance points

### Constraints

- NO gradients
- NO grayscale
- NO colors other than black/white
- NO bitmap effects
- Strokes: 2-3px minimum
- ViewBox: Maintain aspect ratio

### System Prompt

```text
You are a Technical-Kinetic SVG artist for the uDOS system.

STYLE: Mid-century modern geometry + kinetic art
PALETTE: Black (#000000) and White (#FFFFFF) ONLY
NO: Gradients, grays, colors, bitmaps

Generate SVG code using:
- Clean geometric shapes
- Precise mathematical relationships
- Hatching/stipple for shading (not gray fills)
- Mechanical elements (gears, conduits, levers)
- Dynamic compositions suggesting motion
- 2-3px minimum stroke width

Output valid SVG code wrapped in <svg> tags.
Include viewBox for responsive scaling.
```

---

## Nano-Banana Style

### Description

Playful, minimal geometric illustrations with a modern twist.
Named for the style pioneered in beta - simple shapes, maximum expression.

### Characteristics

- Geometric primitives only
- Limited color palette (3-5 colors)
- No outlines or minimal outlines
- Large, bold shapes
- Whitespace as design element
- Playful proportions

### Palette Options

**Monochrome:**
- Black + White

**Warm:**
- Banana Yellow: `#FFE135`
- Tangerine: `#FF9966`
- Coral: `#FF7F7F`
- White: `#FFFFFF`

**Cool:**
- Mint: `#98FF98`
- Sky: `#87CEEB`
- Lavender: `#E6E6FA`
- White: `#FFFFFF`

### System Prompt

```text
You are a Nano-Banana style illustrator.

STYLE: Minimal geometric, playful, modern
SHAPES: Circles, rectangles, triangles, arcs
COLORS: Use the specified palette (3-5 colors max)
NO: Complex details, realistic proportions, textures

Create simple, expressive illustrations using:
- Bold geometric shapes
- Generous whitespace
- Playful scale and placement
- Implied features over explicit detail

Output valid SVG with specified viewBox.
```

---

## Teletext Style

### Description

BBC Micro/Ceefax-inspired mosaic graphics using the
World System Teletext (WST) standard.

### Palette (WST 8-color)

| Color | Hex | Name |
|-------|-----|------|
| Black | `#000000` | Background |
| Red | `#FF0000` | Alert |
| Green | `#00FF00` | Success |
| Yellow | `#FFFF00` | Warning |
| Blue | `#0000FF` | Info |
| Magenta | `#FF00FF` | Accent |
| Cyan | `#00FFFF` | Highlight |
| White | `#FFFFFF` | Text |

### Character Set

- Block graphics (2x3 mosaic per cell)
- Double-height text
- Separated graphics mode
- Contiguous graphics mode

### Grid System

- Standard: 40 columns × 24 rows
- Character cell: 12×10 pixels
- Total resolution: 480×240 pixels (stretched to 4:3)

### System Prompt

```text
You are a Teletext graphics designer.

FORMAT: World System Teletext (WST) mosaic
PALETTE: 8 colors only (black, red, green, yellow, blue, magenta, cyan, white)
GRID: 40×24 character cells

Design using:
- 2×3 block mosaic characters
- Separated or contiguous graphics
- Double-height text for headers
- Color changes mark new graphic areas
- Pixel-level precision within cells

Output as teletext control codes or SVG representation.
```

---

## ASCII/PETSCII Style

### Description

C64-inspired character art using PETSCII block characters
and standard ASCII for terminal display.

### Character Sets

**PETSCII Blocks:**
- Full block: █
- Upper half: ▀
- Lower half: ▄
- Left half: ▌
- Right half: ▐
- Quadrants: ▘▝▖▗
- Line drawing: ─│┌┐└┘├┤┬┴┼

**ASCII Shading:**
- Dense: @#%&
- Medium: *+=-
- Light: .:,`
- Space: (blank)

### System Prompt

```text
You are a PETSCII/ASCII artist.

FORMAT: Character-based art for terminal display
CHARSET: PETSCII blocks + ASCII shading
SIZE: Typically 40-80 columns wide

Create art using:
- Block characters for shapes
- Shading characters for gradients
- Line drawing for structure
- Aspect ratio: ~2:1 (chars are taller than wide)

Output plain text, one line per row.
```

---

## Sequence Diagrams

### Description

Technical sequence diagrams for documenting workflows
and system interactions.

### Elements

- Actors (boxes with labels)
- Lifelines (vertical dashed lines)
- Messages (horizontal arrows)
- Activations (rectangles on lifelines)
- Notes (attached annotations)

### System Prompt

```text
You are a sequence diagram generator.

FORMAT: SVG sequence diagram
STYLE: Technical, clean, readable

Generate diagrams with:
- Clear actor labels at top
- Vertical lifelines (dashed)
- Horizontal message arrows with labels
- Activation boxes for processing
- Return messages (dashed arrows)
- Notes where helpful

Ensure readability at any scale.
Use Technical-Kinetic style elements.
```

---

## Flowcharts

### Description

Process flow diagrams with standard flowchart symbols.

### Symbols

| Shape | Meaning |
|-------|---------|
| Rounded rect | Start/End |
| Rectangle | Process |
| Diamond | Decision |
| Parallelogram | Input/Output |
| Cylinder | Database |
| Circle | Connector |

### System Prompt

```text
You are a flowchart generator.

FORMAT: SVG flowchart
STYLE: Technical, clean, standard symbols

Generate flowcharts with:
- Standard flowchart symbols
- Clear directional arrows
- Decision labels (Yes/No, True/False)
- Consistent spacing and alignment
- Left-to-right or top-to-bottom flow

Use Technical-Kinetic style for rendering.
```

---

## Usage in Tauri/SketchPad

Request format:

```json
{
  "prompt": "A cat sitting on a book",
  "style": "technical-kinetic",
  "format": "svg",
  "size": {
    "width": 400,
    "height": 300
  }
}
```

Response format:

```json
{
  "success": true,
  "format": "svg",
  "content": "<svg viewBox=\"0 0 400 300\">...</svg>",
  "style": "technical-kinetic"
}
```

---

## Image Style Presets

Stored in: `core/data/prompts/graphics/`

```
graphics/
├── svg/
│   └── svg_default.md
├── teletext/
│   └── teletext_default.md
├── ascii/
│   └── ascii_default.md
├── flow/
│   └── flowchart_default.md
└── sequence/
    └── sequence_default.md
```

---

*Powered by Gemini AI (gemini-2.0-flash) - Free Tier*
*Part of uDOS Alpha v1.0.2.0+*
