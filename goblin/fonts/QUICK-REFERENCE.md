# uFont Manager Quick Reference

**Version:** 1.0.0 | **Location:** `/dev/goblin/fonts/`

---

## 🎯 Quick Commands

```bash
# Distribute fonts to all targets
cd /Users/fredbook/Code/uDOS/dev/goblin/fonts
./distribute.sh

# Check what's in the repository
ls -R

# View font manifest
cat manifest.json | jq .

# Add new font
# 1. Copy font file to appropriate directory
# 2. Update manifest.json
# 3. Run ./distribute.sh
```

---

## 📁 Repository Structure

```
/dev/goblin/fonts/          ← Central repository (source of truth)
├── manifest.json           ← Metadata, credits, settings
├── README.md              ← Full documentation
├── QUICK-REFERENCE.md     ← This file
├── distribute.sh          ← Distribution script
├── retro/                 ← Retro computing fonts
│   ├── c64/
│   ├── teletext/
│   ├── apple/
│   └── gaming/
├── emoji/                 ← Emoji fonts
└── custom/                ← User fonts
```

---

## 📊 Available Fonts

| Font                 | Type  | Grid  | Path                                    |
| -------------------- | ----- | ----- | --------------------------------------- |
| **PetMe64**          | Mono  | 24x24 | `retro/c64/PetMe64.ttf`                 |
| **Teletext50**       | Mono  | 24x24 | `retro/teletext/Teletext50.otf`         |
| **Chicago**          | Mono  | 24x24 | `retro/apple/Chicago.ttf`               |
| **Monaco**           | Mono  | 24x24 | `retro/apple/monaco.ttf`                |
| **Press Start 2P**   | Mono  | 24x24 | `retro/gaming/PressStart2P-Regular.ttf` |
| **Noto Color Emoji** | Color | 24x24 | `emoji/NotoColorEmoji.ttf`              |
| **Noto Emoji**       | Mono  | 24x24 | `emoji/NotoEmoji-Regular.ttf`           |

---

## 🎨 Monosorts Settings

Each font in `manifest.json` has `monosorts` settings for 24x24 grid rendering:

```json
"monosorts": {
  "centering": "baseline" | "ink-center",
  "verticalOffset": 0,      // pixels
  "horizontalOffset": 0     // pixels
}
```

**Centering modes:**

- `baseline` - Align to font baseline
- `ink-center` - Center actual ink area (best for block graphics)

**Offsets:**

- Positive values move character down/right
- Negative values move character up/left
- Values in target resolution pixels (24x24)

---

## 🔄 Distribution Flow

```
1. Source: /dev/goblin/fonts/      (Central repository)
           ↓
2. Script: ./distribute.sh          (Distribution)
           ↓
3. Target: /dev/goblin/public/fonts/ (Vite dev server)
           ↓
4. Access: http://localhost:5173/fonts/ (Browser)
```

---

## 📝 Manifest Schema

```json
{
  "collections": {
    "category": {
      "subcategory": {
        "FontName": {
          "file": "path/to/font.ttf",
          "name": "Display Name",
          "type": "mono" | "color",
          "gridSize": 24,
          "author": "Author Name",
          "license": "License Type",
          "url": "https://source.url",
          "description": "Description",
          "monosorts": {
            "centering": "baseline" | "ink-center",
            "verticalOffset": 0,
            "horizontalOffset": 0
          }
        }
      }
    }
  }
}
```

---

## 🚀 Adding New Fonts

### Step 1: Copy Font File

```bash
cp /path/to/newfont.ttf /dev/goblin/fonts/category/
```

### Step 2: Update Manifest

Add entry to `manifest.json`:

```json
"NewFont": {
  "file": "category/newfont.ttf",
  "name": "New Font",
  "type": "mono",
  "gridSize": 24,
  "author": "Author",
  "license": "License",
  "description": "Description",
  "monosorts": {
    "centering": "baseline",
    "verticalOffset": 0,
    "horizontalOffset": 0
  }
}
```

### Step 3: Distribute

```bash
cd /dev/goblin/fonts && ./distribute.sh
```

### Step 4: Test

Open pixel editor: http://localhost:5173/pixel-editor

---

## 📜 License Summary

| License             | Commercial | Modified | Redistributed | Attribution |
| ------------------- | ---------- | -------- | ------------- | ----------- |
| **OFL**             | ✅         | ✅       | ✅            | ✅ Required |
| **Apache 2.0**      | ✅         | ✅       | ✅            | ✅ Required |
| **Free (Personal)** | ❌         | ❌       | ❌            | ✅ Required |

All fonts retain original credits and attribution.

---

## 🔗 Integration

### Pixel Editor

- Reads fonts from `/public/fonts/`
- Uses manifest metadata for rendering
- Monosorts grid positioning

### Future Mac App

- Will read from manifest.json
- Google Fonts API integration
- System-wide font installation

---

**Part of uDOS Alpha v1.0.2.0**  
**uFont Manager Beta**
