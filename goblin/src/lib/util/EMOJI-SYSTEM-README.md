# Emoji System Documentation

## Overview

The uCode pixel editor now includes a comprehensive emoji system with:

- **GitHub :emoji: shortcode compatibility** (e.g., `:smile:`, `:heart:`, `:fire:`)
- **Mono/Color toggling** - matched pairs between monochrome and color versions
- **Smart sizing** - size hints for proper visual balance
- **1px minimum borders** - consistent spacing around all emojis
- **Category organization** - grouped by type for easy browsing

## Files

### `/src/lib/util/emojiMetadata.ts`

Central emoji metadata with:

- `EMOJI_CORE[]` - 140+ matched emoji pairs with GitHub shortcodes
- Size hints for optimal rendering (0.5-2.0 scale)
- Category classifications
- Helper functions for lookups

### `/src/lib/util/characterDatasets.ts`

Character set definitions:

- `EMOJI_COLOR_FULL` - Color emoji set (NotoColorEmoji.ttf)
- `EMOJI_MONO_FULL` - Monochrome emoji set (EmojiIconFont.ttf)
- Both sets have identical codes for 1:1 toggling
- Extended `CharacterSet` interface with new fields:
  - `githubShortcodes` - Maps codes to GitHub :emoji: format
  - `sizeHints` - Per-emoji scale adjustments
  - `renderPadding` - Minimum border space (1px default)
  - `pairedSet` - ID of corresponding mono/color set

## Matched Emoji Pairs

All 140+ emojis in `EMOJI_CORE` are available in **both** mono and color versions:

### Categories

1. **Faces** - Smiling, affection, neutral, negative (18 emojis)
2. **Gestures & Hands** - Thumbs, fists, pointing, etc. (16 emojis)
3. **Hearts** - Various heart symbols (7 emojis)
4. **Stars & Sparkles** - Stars, sparkles, dizzy (4 emojis)
5. **Weather** - Sun, clouds, moon, snow (7 emojis)
6. **Symbols - Basic** - Checkmarks, math, warnings (13 emojis)
7. **Symbols - Arrows** - Directional arrows (8 emojis)
8. **Media Controls** - Play, pause, volume (11 emojis)
9. **Objects - Tech** - Computers, phones, files (16 emojis)
10. **Objects - Tools** - Wrench, hammer, gear (5 emojis)
11. **Misc** - Games, music, camera, etc. (10 emojis)

## GitHub Shortcode Examples

```typescript
// Get shortcode from emoji code
getGithubShortcode(0x1f600); // → "grinning"
getGithubShortcode(0x2764); // → "heart"
getGithubShortcode(0x1f525); // → "fire"

// Get emoji code from shortcode
getEmojiFromShortcode("smile"); // → 0x1f604
getEmojiFromShortcode("thumbsup"); // → 0x1f44d
getEmojiFromShortcode("+1"); // → 0x1f44d (alias)
```

## Size Hints

Some emojis have size adjustments for better visual balance:

```typescript
getSizeHint(0x2764); // ❤ Heart = 0.9 (slightly smaller)
getSizeHint(0x2795); // ➕ Plus = 0.8 (smaller for crispness)
getSizeHint(0x25b6); // ▶ Play = 0.8 (smaller triangle)
getSizeHint(0x1f600); // 😀 Face = 1.0 (default)
```

## Rendering Guidelines

### 1px Minimum Border

All emojis maintain at least 1px free space around them:

- Tile grid: `gap-px` between cells
- Character library: `p-px` padding inside buttons
- Pixel editor: Proper canvas margins

### Center Alignment

Emojis are centered using flexbox:

```svelte
<div class="w-full h-full flex items-center justify-center">
  <div class="text-lg leading-none" style="font-family: {fontFamily}">
    {char.char}
  </div>
</div>
```

### Independent Sizing

Each emoji sizes itself naturally - they don't need to relate to each other in size, allowing for better visual hierarchy.

## Toggling Mono/Color

Both `EMOJI_COLOR_FULL` and `EMOJI_MONO_FULL` contain the same core emoji codes, enabling seamless toggling:

```typescript
EMOJI_COLOR_FULL.pairedSet === "emoji-mono";
EMOJI_MONO_FULL.pairedSet === "emoji-color";
```

**Future**: Add UI toggle button to switch between paired sets while maintaining current emoji selection.

## Creating New Emoji Sets

### Themed Subsets

Create focused collections for specific use cases:

```typescript
export const EMOJI_DEVELOPER: CharacterSet = {
  name: "Developer Emojis",
  description: "Tech-focused emoji set for coding",
  type: "emoji",
  renderPadding: 1,
  codes: [
    0x1f4bb, // 💻 Laptop
    0x1f4be, // 💾 Floppy disk
    0x1f511, // 🔑 Key
    0x1f512, // 🔒 Lock
    0x1f525, // 🔥 Fire
    0x1f41b, // 🐛 Bug
    0x2699, // ⚙ Gear
    0x1f527, // 🔧 Wrench
    // ... more dev-related emojis
  ],
  githubShortcodes: {
    0x1f4bb: "computer",
    0x1f4be: "floppy_disk",
    0x1f511: "key",
    // ... mappings
  },
};
```

### Category Filters

Use the helper functions to create category-based sets:

```typescript
import { getEmojisByCategory } from "$lib/util/emojiMetadata";

// Get all heart emojis
const heartEmojis = getEmojisByCategory("hearts");

// Get all gesture emojis
const gestureEmojis = getEmojisByCategory("gestures");
```

## Future Enhancements

### Planned Features

1. **Visual Toggle Button** - UI control to switch mono/color
2. **Search by Shortcode** - Type `:heart:` to find emojis
3. **Recent Emojis** - Track frequently used emojis
4. **Custom Size Overrides** - Per-project emoji scaling
5. **Emoji Picker** - Modal with category tabs
6. **ASCII Fallbacks** - Text-only representation
7. **Skin Tone Support** - Modifier sequences
8. **Composite Emojis** - ZWJ sequences (e.g., family emojis)

### Extensibility

The system is designed for easy extension:

- Add new categories to `EmojiCategory` type
- Extend `EMOJI_CORE` array with new entries
- Create themed subsets in `characterDatasets.ts`
- Add custom size hints per emoji
- Map regional emoji variations

## Technical Notes

### Font Requirements

- **Color**: `NotoColorEmoji.ttf` (Google Noto)
- **Mono**: `EmojiIconFont.ttf` (monochrome icon font)

### Rendering Pipeline

1. Load font via `fontLoader.ts`
2. Extract character at specified grid size (24×24 or 48×48)
3. Apply `renderPadding` margin (1px default)
4. For color: capture RGB values per pixel
5. For mono: black/white threshold
6. Center character within usable grid space
7. Apply `sizeHint` if specified

### Performance

- Lazy loading: Only render visible emojis
- Canvas caching: Pre-render to data URLs
- Grid virtualization: Future optimization for large sets

## Examples

### Basic Usage

```typescript
// In pixel editor
import { EMOJI_COLOR_FULL, EMOJI_MONO_FULL } from "$lib/util/characterDatasets";
import { getGithubShortcode } from "$lib/util/emojiMetadata";

// Load color emoji set
await loadFont(
  "/fonts/NotoColorEmoji.ttf",
  24,
  EMOJI_COLOR_FULL.codes,
  false,
  "color"
);

// Get shortcode for display
const shortcode = getGithubShortcode(selectedEmoji.code);
console.log(`Selected: :${shortcode}:`);
```

### Toggle Implementation

```typescript
let currentSet = $state<"color" | "mono">("color");

function toggleEmojiMode() {
  currentSet = currentSet === "color" ? "mono" : "color";
  const newCollection =
    currentSet === "color" ? EMOJI_COLOR_FULL : EMOJI_MONO_FULL;

  // Reload with same emoji codes in different style
  await loadFont(
    newCollection.path,
    gridSize,
    newCollection.codes,
    newCollection.noMargin || false,
    currentSet
  );
}
```

## References

- [GitHub Emoji Cheat Sheet](https://github.com/ikatyang/emoji-cheat-sheet)
- [Unicode Emoji List](https://unicode.org/emoji/charts/full-emoji-list.html)
- [Noto Color Emoji](https://github.com/googlefonts/noto-emoji)
