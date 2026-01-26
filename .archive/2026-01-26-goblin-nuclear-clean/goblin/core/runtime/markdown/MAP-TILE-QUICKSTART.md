# Creating 120×40 Map Tiles - Quick Guide

## Exact Dimensions

**Total:** 120 characters wide × 40 lines tall  
**Content Area:** 118 wide × 38 tall (borders use 2 chars width, 2 lines height)

## Template (Copy/Paste Ready)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Verification:**
- Top border: 1 + 118 + 1 = 120 chars
- Content lines: 38 lines
- Bottom border: 1 line
- Total: 40 lines

## Python Helper for Validation

```python
def validate_tile(ascii_art: str) -> tuple[bool, str]:
    """Validate map tile dimensions."""
    lines = ascii_art.split('\n')
    height = len(lines)
    width = max(len(line) for line in lines) if lines else 0
    
    issues = []
    if width > 120:
        issues.append(f"Width exceeds 120: {width}")
    if height > 40:
        issues.append(f"Height exceeds 40: {height}")
    
    if issues:
        return False, "; ".join(issues)
    return True, f"Valid: {width}×{height}"

# Usage
tile = """
┌────...(120 chars)...────┐
│                        │
...
└────────────────────────┘
"""

valid, msg = validate_tile(tile)
print(msg)
```

## VS Code Ruler Settings

Add to `settings.json` for visual guide:

```json
{
    "editor.rulers": [120],
    "editor.wordWrap": "off"
}
```

## Common Mistakes

### ❌ Border Too Wide (126 chars)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
(126 chars - TOO WIDE)
```

### ✅ Correct Width (120 chars)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
(120 chars - PERFECT)
```

## Quick Measurement

Count the dashes between corners:
- ❌ 124 dashes = 126 total (too wide)
- ✅ 118 dashes = 120 total (perfect)

## Bash One-Liner to Generate Template

```bash
# Top border
echo -n "┌" && printf '─%.0s' {1..118} && echo "┐"

# Content lines (38 total)
for i in {1..38}; do
    echo -n "│" && printf ' %.0s' {1..118} && echo "│"
done

# Bottom border
echo -n "└" && printf '─%.0s' {1..118} && echo "┘"
```

## Python One-Liner to Generate Template

```python
print("┌" + "─"*118 + "┐")
for _ in range(38):
    print("│" + " "*118 + "│")
print("└" + "─"*118 + "┘")
```

## Example: Correct California Tile

```map
TILE:NA01 NAME:California ZONE:America/Los_Angeles
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           CALIFORNIA                                                                   │
│                                                                                                                        │
│                                                                                                                        │
│                    ○ San Francisco                                                                                     │
│                      (Bay Area)                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                            ○ San Jose                                                                                  │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                    ○ Fresno                                                                            │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                      ○ Los Angeles                                                                                     │
│                        (Metro Area)                                                                                    │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                  ○ San Diego                                                                           │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│                                                                                                                        │
│  Timezone: PST/PDT (UTC-8/-7)                                                                                          │
│  Population: 39.5M                                                                                                     │
│  Capital: Sacramento                                                                                                   │
│                                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Dimensions:** 120 × 40 ✅

## Testing Your Tile

```bash
# Check width
cat tile.txt | wc -L
# Should output: 120

# Check height
cat tile.txt | wc -l
# Should output: 40
```

---

**Remember:** The converter tool (`map_converter.py`) will automatically enforce these constraints when converting from JSON, but for hand-crafted tiles, use this template!
