<!-- 
uDOS Upside Down Template
Stranger Things-inspired subterranean horror theme
Layers -11 to -100: The deep unknown
Version: 1.0.0
-->

---

## Identity

**name:** The Upside Down
**style:** Subterranean Horror
**icon:** 🔻
**layer:** upside_down
**description:** Dark mirror world beneath reality - proceed with caution

---

## Prompt

**base:** 🔻>
**continuation:** ···
**script:** ⚡
**debug:** 👁️

---

## Terminology

| Key | Default | Description |
|-----|---------|-------------|
| CMD_CATALOG | SCAN | Detect nearby anomalies |
| CMD_LOAD | BREACH | Access stored data |
| CMD_SAVE | ANCHOR | Save reality checkpoint |
| CMD_MAP | SENSE | Perceive surroundings |
| CMD_MAKE | SURVIVE | Create from nothing |
| CMD_HELP | PROTOCOL | Emergency procedures |

---

## Status Indicators

| Status | Symbol |
|--------|--------|
| OK | 💡 |
| ERROR | 🩸 |
| WARNING | ⚡ |
| INFO | 👁️ |
| PROGRESS | ⏳ |

---

## Messages

### Errors

**ERROR_CRASH:**
```
🩸 Reality destabilized. '{{command}}' consumed by the void.
   Attempting to restore anchor point...
```

**ERROR_UNKNOWN_COMMAND:**
```
👁️ '{{command}}' has no meaning here.
   The rules are different. Consult PROTOCOL.
```

**ERROR_FILE_NOT_FOUND:**
```
💀 '{{filename}}' exists only in echoes now.
   The Upside Down does not forget. It transforms.
```

### Information

**INFO_WELCOME:**
```
🔻 BREACH DETECTED - UPSIDE DOWN LAYER {{layer}}
   ⚠️  HOSTILE ENVIRONMENT
   ⚠️  Reality Stability: {{stability}}%
   ⚠️  Communication range: LIMITED
   
   Remember: Light is your anchor. Sound attracts attention.
```

**INFO_EXIT:**
```
Closing breach to Layer {{layer}}.
Anchor points preserved.

You made it back. This time.
```

**INFO_LAYER_DESCENT:**
```
⚡ DESCENDING DEEPER...
   Layer {{from}} → Layer {{to}}
   Warning: Signal degradation detected.
   Warning: Hostile presence increasing.
```

---

## AI Prompts

### make_guide
You are a survivor documenting knowledge from the Upside Down. Your responses:
- Frame everything through survival horror lens
- Emphasize dangers and precautions FIRST
- Use tense, urgent language
- Include "field notes" style observations
- Reference that things work DIFFERENTLY here
- Always include an escape/safety note

The Upside Down inverts normal rules. Water flows up. Fire attracts predators.
Sound travels too far. Light is precious but draws attention.

### make_do
You are helping someone survive in hostile territory with minimal resources:
- Improvisation is critical
- Everything has trade-offs (noise, light, scent)
- Include warnings about what attracts attention
- Suggest backup plans
- Time is always limited

### suggest_workflow
Create a survival protocol for the given situation:
1. 🚨 IMMEDIATE THREATS - What can kill you NOW
2. 🛡️ DEFENSIVE MEASURES - First priorities
3. 📡 SIGNAL/ESCAPE - How to get help or get out
4. ⚡ RESOURCE MANAGEMENT - What you have, what you need
5. 👁️ ENVIRONMENTAL HAZARDS - What to watch for
Format as an emergency checklist.

### encounter
Generate a tense survival moment in the Upside Down:
- Something is wrong
- The user must make a quick decision
- Their knowledge determines survival
- Include sensory details (cold, damp, spores)
- Add a time pressure element

### reality_check
Generate a "something is different here" observation:
- A normal survival fact that's inverted
- Why the Upside Down version matters
- How to adapt traditional knowledge
