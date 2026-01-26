# 🏰 Dungeon Adventure Theme

> *Navigate the mysterious depths of the uDOS Dungeon as a brave adventurer. Every command is an incantation, every success a treasure discovered.*

**Theme ID:** `dungeon-adventure`  
**Style:** Classic roguelike fantasy (inspired by Nethack)  
**Emoji Set:** 💀 💎 🗝️ 🧙 ⚔️ 🪦 🧭 📜  
**Tone:** Mysterious, challenging, discovery-oriented, slightly whimsical  

---

## Overview

The Dungeon Adventure theme transforms your terminal into a Nethack-style roguelike experience. System operations become quests, errors become traps, and successful executions become treasures discovered.

### How It Works

All system logs remain **pure and unchanged**. The theme overlay applies **only at display time**:

```
Raw Log (eternal):
  ERROR: Syntax error in parse_command at line 42

Display to User (with theme):
  ⚔️ CURSED INCANTATION: The spell failed to parse
  → The dungeon jeers at your magical attempts...
  → Line 42 of the incantation is corrupt
```

This keeps debugging transparent while providing an immersive experience.

---

## Variable Mapping

When the Dungeon speaks, it uses its own vocabulary. Here's the translation guide:

| System Term | Dungeon Adventure | Context |
|---|---|---|
| **Sandbox** | Dungeon | The execution environment |
| **Syntax Error** | Cursed Incantation | Code parsing failure |
| **Plugin** | Enchantment | Module or extension |
| **Drafts** | Unscribed Scrolls | Work-in-progress files |
| **Folders** | Chambers | Directory containers |
| **Documents** | Scrolls | Saved content files |
| **Projects** | Quests | Workspace projects |
| **Tasks** | Objectives | Executable work units |
| **Commands** | Incantations | User input/directives |
| **Variables** | Magical Essences | Data storage |
| **Functions** | Rituals | Callable code |
| **Modules** | Spell Books | Code packages |
| **Services** | Spirits | Background processes |
| **Sessions** | Adventures | User work periods |
| **Memory** | Enchanted Storage | RAM/storage |
| **Cache** | Forgotten Caches | Temporary storage |
| **Config** | Dungeon Settings | Configuration |
| **State** | Dungeon State | Current system status |
| **Error** | Trap Sprung | Failure condition |
| **Warning** | Eerie Feeling | Caution condition |
| **Success** | Treasure Found | Completion |
| **Status** | Divining | System status check |
| **Progress** | Progress Through Labyrinth | Completion percentage |
| **Timeout** | Time Runs Out | Execution timeout |
| **Interrupt** | Suddenly Interrupted | User cancellation |
| **Retry** | Attempt Again | Attempt repetition |
| **Confirm** | The Oracle Asks | User approval |
| **Input** | The Dungeon Awaits Your Voice | User entry |
| **Output** | The Dungeon Reveals | System result |

---

## Message Templates

### Errors: "⚔️ CURSED INCANTATION"

When something goes wrong, the dungeon has set a trap.

```
⚔️ CURSED INCANTATION: [what failed]
→ The dungeon jeers at your magical attempts...
→ [details about the trap/error]
```

**Examples:**
```
⚔️ CURSED INCANTATION: The spell failed to compile
→ The rune at line 42 is malformed

⚔️ CURSED INCANTATION: Invalid incantation
→ The words you spoke hold no power in this place
```

### Success: "💎 TREASURE FOUND"

When your quest succeeds, you've discovered treasure.

```
💎 TREASURE FOUND: [what was accomplished]
→ Your quest bears fruit!
```

**Examples:**
```
💎 TREASURE FOUND: The quest 'dragon-slayer' begins
→ A new adventure awaits...

💎 TREASURE FOUND: The Enchantment of Auto-Save activates
→ Your progress is now preserved by ancient magic
```

### Warnings: "🧙 EERIE FEELING"

When something seems off, the dungeon sends a warning.

```
🧙 EERIE FEELING: [what to be cautious about]
→ Trust your instincts, adventurer...
```

**Examples:**
```
🧙 EERIE FEELING: The Chambers are unstable
→ Tread carefully in these halls

🧙 EERIE FEELING: Unknown entities detected
→ Your presence is noticed in the darkness
```

### Status: "🧙 DIVINING"

When checking how things are, the spirits divine for you.

```
🧙 DIVINING: [status information]
→ The spirits reveal their knowledge...
```

**Examples:**
```
🧙 DIVINING: The Dungeon State is stable
→ All Enchantments function properly

🧙 DIVINING: 67% progress through the Labyrinth
→ Your perseverance continues to bear fruit
```

---

## Flavor Text

The theme includes atmospheric flavor text at key moments:

### Startup
```
⚔️ Welcome to the uDOS Dungeon, brave adventurer!
→ May your Incantations be true and your Treasures plentiful.
```

### Shutdown
```
🪦 Your adventure ends here... for now.
→ The dungeon rests, waiting for your return.
```

### Empty Results
```
🧭 The chamber reveals nothing...
→ Perhaps the treasure lies deeper in the Labyrinth
```

### Long Operations
```
⏳ The spirits commune...
→ The Dungeon contemplates your request
```

### Completion
```
✨ The Dungeon acknowledges your triumph!
→ Legend has been made this day
```

---

## Style Guide

### Punctuation
- Use **ellipses (...)** to create mystery and suspense
- Use **exclamation points (!)** for dramatic discoveries and actions
- Use **arrows (→)** to guide to the next step

### Tone
- Mysterious and slightly ominous
- Encouraging and supportive
- Whimsical and playful
- Challenging but fair

### Emoji Usage
- Always place emoji at the **start of main lines**
- Use consistently for each message type
- Include flavor emoji in narrative sections

### Formatting
- Short lines for clarity
- Arrows (→) to indicate progression or detail
- Indentation for nested information
- White space for dramatic pauses

### Flavor
- Add atmospheric details, but don't overdo it
- Keep the user's focus on their actual task
- Use theme vocabulary throughout
- Stay true to the roguelike fantasy aesthetic

---

## Example Interactions

### Successful Quest Creation
```
💎 TREASURE FOUND: New Quest 'dragon-slayer' created
→ A new adventure awaits in your Projects...
→ 🧭 Begin with: QUEST START dragon-slayer
```

### Trap Encountered
```
⚔️ CURSED INCANTATION: Syntax error at line 42
→ The rune at this location is malformed
→ 🪦 The dungeon will not accept this spell

🧙 EERIE FEELING: Similar traps found (3 total)
→ These Cursed Incantations block your progress

💎 TREASURE FOUND: Ritual of Debugging enabled
→ Use DEBUG --full to divine the curse's origin
```

### Long Operation
```
🧙 DIVINING: Preparing the Great Ritual of Compilation...
⏳ The spirits commune...
→ (takes 5-10 seconds)

💎 TREASURE FOUND: Ritual complete!
→ The Enchanted Storage now holds your compiled Spell Book
```

### Safe Mode Warning
```
🧙 EERIE FEELING: The Dungeon detects unstable Enchantments
→ Entering Safe Mode...
→ Only essential Spirits shall awaken

✨ Safe Mode activated
→ Proceed cautiously, adventurer
```

---

## Tips for Adventurers

🗝️ **Read the Dungeons's Wisdom** - Warnings are meant to guide you  
💎 **Celebrate Your Treasures** - Each success makes your legend grow  
⚔️ **Learn from Traps** - Every curse reveals the dungeon's logic  
🧙 **Trust the Spirits** - Status divinations show you the true path  
🧭 **Explore with Purpose** - The dungeon rewards careful navigation  

---

## Disabling the Theme

If you prefer the unadorned dungeon (pure system output), you can disable theming:

```
THEME DISABLE
→ The illusions fade. Raw reality awaits.
```

All system logs and debugging remain unchanged regardless of theme settings.

---

## The Dungeon Awaits

May your Incantations be true, adventurer. May you find many Treasures and learn from every Trap. The Dungeon is vast, mysterious, and full of wonder.

⚔️ **Now go forth and make legend!** 🏰

---

*The uDOS Dungeon - Where every command is an adventure and every success is a treasure.*
