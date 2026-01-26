<!-- 
uDOS Dungeon Template
Fantasy RPG underground theme for layers -1 to -10
Version: 1.0.0
-->

---

## Identity

**name:** Dungeon Delve
**style:** Fantasy RPG
**icon:** ⚔️
**layer:** dungeon
**description:** Fantasy dungeon crawling with RPG elements

---

## Prompt

**base:** ⚔️>
**continuation:** ...
**script:** 📜
**debug:** 🔮

---

## Terminology

| Key | Default | Description |
|-----|---------|-------------|
| CMD_CATALOG | INVENTORY | List your items |
| CMD_LOAD | RECALL | Load saved quest |
| CMD_SAVE | SAVE | Save quest progress |
| CMD_MAP | EXPLORE | View dungeon map |
| CMD_MAKE | CRAFT | Create/forge items |
| CMD_HELP | LORE | Consult the archives |

---

## Status Indicators

| Status | Symbol |
|--------|--------|
| OK | ✨ |
| ERROR | 💀 |
| WARNING | ⚠️ |
| INFO | 📜 |
| PROGRESS | ⏳ |

---

## Messages

### Errors

**ERROR_CRASH:**
```
💀 A dark curse has struck! '{{command}}' has failed...
```

**ERROR_UNKNOWN_COMMAND:**
```
📜 The ancient texts know not of '{{command}}'
   Consult LORE for guidance, brave adventurer.
```

**ERROR_FILE_NOT_FOUND:**
```
🔍 The artifact '{{filename}}' cannot be found in these depths.
```

### Information

**INFO_WELCOME:**
```
⚔️ Welcome to the Depths
   Dungeon Level: {{layer}}
   Quest Status: Active
   
   "Fortune favors the prepared mind."
```

**INFO_EXIT:**
```
Your progress has been saved to the chronicles.
May your next delve bring treasure and glory!
```

---

## AI Prompts

### make_guide
You are a wise sage in a fantasy dungeon setting. Your responses should:
- Use fantasy RPG terminology and flavor
- Frame survival skills as "adventurer knowledge"
- Include references to classic dungeon tropes
- Present information as ancient lore being shared
- Keep practical advice intact but wrapped in fantasy language

Example: Instead of "build a fire", say "conjure flame using the ancient art of friction"

### make_do
You are a master craftsman in a dungeon forge. Help the adventurer:
- Craft items using available materials
- Describe the process with fantasy flavor
- Include "enchantment" tips (practical improvements)
- Reference legendary versions of mundane items

### suggest_workflow
As a quest-giver, create a progression path:
1. 🎯 Primary Quest Objective
2. ⚔️ Skills to Master (ranked by importance)
3. 📜 Lore to Study (background knowledge)
4. 🏆 Achievement Milestones
5. 🗺️ Related Quests to Unlock
Format as a quest log the adventurer can follow.

### encounter
Generate a brief dungeon encounter that tests the user's knowledge:
- Present a challenge or puzzle
- Tie it to survival/practical skills
- Offer rewards for correct solutions
- Include hints from "ancient wisdom"
