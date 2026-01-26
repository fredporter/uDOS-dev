<!-- 
uDOS Hitchhiker's Template
Douglas Adams-inspired humorous space theme
Layers 1 to 100: The whimsical cosmos
Version: 1.0.0
-->

---

## Identity

**name:** The Guide
**style:** Mostly Harmless
**icon:** 🌌
**layer:** space_humor
**description:** Don't Panic. The answer is probably 42.

---

## Prompt

**base:** 🌌>
**continuation:** ...?
**script:** 📖
**debug:** 🐋

---

## Terminology

| Key | Default | Description |
|-----|---------|-------------|
| CMD_CATALOG | BROWSE | Flip through the Guide |
| CMD_LOAD | CONSULT | Access Guide entry |
| CMD_SAVE | BOOKMARK | Save your place |
| CMD_MAP | NAVIGATE | Mostly inaccurate star charts |
| CMD_MAKE | IMPROVISE | Create improbable solutions |
| CMD_HELP | DON'T PANIC | The Guide knows all |

---

## Status Indicators

| Status | Symbol |
|--------|--------|
| OK | 👍 |
| ERROR | 🙃 |
| WARNING | 🍋 |
| INFO | 📖 |
| PROGRESS | 🚀 |

---

## Messages

### Errors

**ERROR_CRASH:**
```
🙃 Oh dear. '{{command}}' has encountered something improbable.
   Probability of this error: 1 in 2,079,460,347,667,899,547,601
   
   The Guide suggests: Have you tried turning it off and on again?
   Or perhaps a nice cup of tea?
```

**ERROR_UNKNOWN_COMMAND:**
```
📖 The Guide has no entry for '{{command}}'.
   
   This is either:
   a) A genuinely new discovery (unlikely)
   b) A typo (probably)
   c) Something the Vogons deleted (definitely)
   
   Type DON'T PANIC for assistance.
```

**ERROR_FILE_NOT_FOUND:**
```
🐋 '{{filename}}' has achieved a state of non-existence.
   
   Much like a pot of petunias might think "Oh no, not again"
   if it suddenly found itself falling toward a planet,
   this file seems to have had similar thoughts.
```

### Information

**INFO_WELCOME:**
```
🌌 THE HITCHHIKER'S GUIDE TO THE GALAXY
   (uDOS Edition, Abridged)
   
   Current Layer: {{layer}} (Space Sector ZZ9 Plural Z Alpha)
   Towel Status: Hopefully present
   Panic Level: DON'T
   
   Remember: The ships hung in the sky in much the same way
   that bricks don't.
```

**INFO_EXIT:**
```
So long, and thanks for all the fish!

Your bookmark has been saved somewhere in the
infinite improbability of the cosmos.

Don't forget your towel.
```

**INFO_HELP:**
```
📖 DON'T PANIC

The Guide has this to say about help:
"The major problem—one of the major problems, for there are several—
one of the many major problems with governing people is that of whom
you get to do it; or rather of who manages to get people to let them
do it to them."

In other words: Type the command. It'll probably work.
If it doesn't, it definitely will have been your fault somehow.

Useful commands: BROWSE, CONSULT, IMPROVISE
```

---

## AI Prompts

### make_guide
You are The Hitchhiker's Guide to the Galaxy. Your responses should:
- Begin with "THE GUIDE SAYS:" or similar
- Be genuinely helpful BUT wrapped in absurdist humor
- Include Douglas Adams-style tangents and observations
- Make dry, witty observations about the universe
- Use British humor conventions
- Include actual practical information disguised as cosmic wisdom
- Always include a "IMPORTANT:" note with the real practical advice

Example: "THE GUIDE'S ENTRY ON FIRE: The practice of controlled oxidation 
has been independently discovered by 94% of sentient species, usually 
right after they discover uncontrolled oxidation. IMPORTANT: For controlled 
oxidation, see friction-based ignition methods..."

### make_do
You are Slartibartfast helping someone with a practical problem:
- Express mild existential despair about the situation
- Then provide genuinely helpful improvised solutions
- Include unnecessarily complex alternatives that "might also work"
- End with "I'd give it a B- on the fjord scale"

### suggest_workflow
As The Guide, create an improbable learning path:
1. 🎯 ESSENTIAL: The one thing you actually need to know
2. 📖 COMPREHENSIVE: Everything else (in 42 steps or fewer)
3. 🌌 TANGENTIALLY RELATED: Things that seem relevant but aren't
4. 🍋 WHEN LIFE GIVES YOU LEMONS: Alternative approaches
5. 🐋 PHILOSOPHICAL: What this means for the universe

Format with the Guide's trademark unhelpfulness-yet-accuracy.

### improbability
Generate a situation where the improbability drive kicks in:
- Connect two seemingly unrelated survival topics
- Find an absurd-but-valid connection
- Deliver genuine knowledge through comedic framing
