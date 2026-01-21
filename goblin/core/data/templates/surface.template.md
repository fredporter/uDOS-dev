# uDOS Surface Template
#
# Default Earth-based theme for layer 0.
# Clean, practical survival and knowledge focus.
#
# Version: 1.0.0
# Layer: surface (0)

---

## Identity

**name:** Surface Operations
**style:** Survival Guide
**icon:** 🌍
**layer:** surface
**description:** Practical Earth-based survival and knowledge system

---

## Prompt

**base:** 🌍>
**continuation:** ...
**script:** #
**debug:** ?

---

## Terminology

| Key | Default | Description |
|-----|---------|-------------|
| CMD_CATALOG | CATALOG | List available resources |
| CMD_LOAD | LOAD | Load knowledge file |
| CMD_SAVE | SAVE | Save progress |
| CMD_MAP | MAP | View terrain map |
| CMD_MAKE | MAKE | Create/build something |
| CMD_HELP | HELP | Survival guide |

---

## Messages

### Errors

**ERROR_CRASH:**
```
⚠️ System malfunction: '{{command}}' failed
```

**ERROR_UNKNOWN_COMMAND:**
```
Unknown action: '{{command}}' - Type HELP for guide
```

### Information

**INFO_WELCOME:**
```
🌍 Surface Operations Ready
   Location: Earth (Layer 0)
   Status: All systems nominal
```

**INFO_EXIT:**
```
Session ended. Stay safe out there.
```

---

## AI Prompts

### make_guide
You are a practical survival guide writer. Your responses should be:
- Actionable and safety-focused
- Based on real-world survival techniques
- Clear step-by-step instructions
- Include warnings about common mistakes
- Reference the uDOS knowledge bank when relevant

Focus on Earth-based scenarios: wilderness survival, emergency preparedness, 
practical skills, and sustainable living.

### make_do
You are a resourceful assistant helping with practical tasks. Focus on:
- Using available materials creatively
- Safety first, then efficiency
- Step-by-step instructions
- Common alternatives if ideal tools aren't available

### suggest_workflow
Suggest a learning path for the given topic that includes:
1. Essential safety knowledge (priority)
2. Core skills to master
3. Practice exercises
4. Related knowledge to explore
Format as a checklist the user can follow.
