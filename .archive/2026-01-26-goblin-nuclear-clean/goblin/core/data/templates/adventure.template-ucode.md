---
title: Survival Quest
version: 2.0.0
author: uDOS
created: 2026-01-06
tags: [adventure, survival, interactive, game]
description: An interactive survival adventure with choices, dice rolls, and character progression
permissions:
  execute: true
  save_state: true
variables:
  SPRITE_NAME: Survivor
  SPRITE_HP: 100
  SPRITE_HP_MAX: 100
  SPRITE_LEVEL: 1
  SPRITE_XP: 0
  SPRITE_LOCATION: AA340
---

# Survival Quest

An interactive text adventure where you must survive the wilderness and find your way home.

---

## Character Setup

Initialize your character with starting stats.

```upy
# Character variables
SET SPRITE_NAME = "Survivor"
SET SPRITE_HP = 100
SET SPRITE_HP_MAX = 100
SET SPRITE_LEVEL = 1
SET SPRITE_XP = 0
SET SPRITE_LOCATION = "AA340"

# Award starting XP
XP + 10
```

---

## Story Introduction

```upy
PRINT "=========================================="
PRINT "  Survival Quest"
PRINT "=========================================="
PRINT ""
PRINT "You are " + SPRITE_NAME + ", stranded in the wilderness."
PRINT "Your goal: Survive and find your way home."
PRINT ""
```

---

## The Crossroads

You stand at the edge of a dense forest. Three paths lie before you.

```upy
LABEL START

PRINT "You stand at the edge of a dense forest."
PRINT ""

CHOICE "Which path will you take?"
  OPTION "Follow the river" -> RIVER
  OPTION "Climb the hill" -> HILL
  OPTION "Build a fire" -> FIRE
END
```

---

## Path: The River

Following the river could lead to civilization... or danger.

```upy
LABEL RIVER

PRINT "You follow the river downstream..."
PRINT "The water rushes past smooth stones."
PRINT ""

# Skill check
roll = ROLL 1d20

IF roll >= 15 THEN
  PRINT "You found a clean water source!"
  PRINT "Your survival skills impress even yourself."
  XP + 50
ELSE
  PRINT "You slip on wet rocks!"
  PRINT "The fall hurts, but you push on."
  HP - 10
END

GOTO START
```

---

## Path: The Hill

The high ground offers a vantage point, but the climb is treacherous.

```upy
LABEL HILL

PRINT "You climb the steep hill..."
PRINT "Each step brings you closer to the summit."
PRINT ""

# Skill check
roll = ROLL 1d20

IF roll >= 12 THEN
  PRINT "You reach the summit!"
  PRINT "The view reveals a village in the distance."
  XP + 40
ELSE
  PRINT "The climb was too difficult."
  PRINT "You slide back down, exhausted."
  HP - 15
END

GOTO START
```

---

## Path: The Signal Fire

A fire could attract rescuers... or predators.

```upy
LABEL FIRE

PRINT "You gather dry wood and kindling..."
PRINT "The smoke begins to rise into the sky."
PRINT ""

# Skill check
roll = ROLL 1d20

IF roll >= 14 THEN
  PRINT "Rescue team spotted your signal!"
  PRINT "A helicopter appears on the horizon."
  GOTO RESCUED
ELSE
  PRINT "The fire is too small..."
  PRINT "You'll need to try something else."
  GOTO START
END
```

---

## Ending: Rescued!

Congratulations! You've been saved.

```upy
LABEL RESCUED

PRINT ""
PRINT "=========================================="
PRINT "  YOU WERE RESCUED!"
PRINT "=========================================="
PRINT ""
PRINT "Final Stats:"
PRINT "  HP: " + SPRITE_HP + "/" + SPRITE_HP_MAX
PRINT "  XP: " + SPRITE_XP
PRINT "  Level: " + SPRITE_LEVEL
PRINT ""

XP + 100
FLAG adventure_complete = true

END
```

---

## Game Over: Death

If HP reaches zero, the adventure ends.

```upy
LABEL GAME_OVER

IF SPRITE_HP <= 0 THEN
  PRINT ""
  PRINT "=========================================="
  PRINT "  GAME OVER"
  PRINT "=========================================="
  PRINT ""
  PRINT "The wilderness claimed another victim..."
  PRINT "Try again?"
  END
END
```

---

## Notes

This adventure template demonstrates:

- **Variables**: Character stats (HP, XP, Level)
- **Labels**: Named sections for branching
- **Choices**: Player-driven decisions
- **Dice Rolls**: Random outcomes with `ROLL 1d20`
- **Conditionals**: `IF/THEN/ELSE` for logic
- **State**: Flags for tracking progress

### Customization Ideas

1. Add more paths and locations
2. Create an inventory system
3. Add NPCs with dialogue
4. Include combat encounters
5. Add day/night cycle effects
