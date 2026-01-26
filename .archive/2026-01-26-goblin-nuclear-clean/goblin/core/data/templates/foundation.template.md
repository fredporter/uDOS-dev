<!-- 
uDOS Foundation Template
Isaac Asimov-inspired serious space theme
Layers 101+: The far reaches of galactic civilization
Version: 1.0.0
-->

---

## Identity

**name:** Encyclopedia Galactica
**style:** Foundation Archives
**icon:** 🔬
**layer:** space_serious
**description:** Preserving knowledge through the Long Night

---

## Prompt

**base:** 📚>
**continuation:** ...
**script:** Σ
**debug:** Ψ

---

## Terminology

| Key | Default | Description |
|-----|---------|-------------|
| CMD_CATALOG | ARCHIVE | Access Foundation archives |
| CMD_LOAD | RETRIEVE | Query encyclopedia |
| CMD_SAVE | PRESERVE | Commit to archives |
| CMD_MAP | CHART | Galactic navigation |
| CMD_MAKE | SYNTHESIZE | Create from knowledge |
| CMD_HELP | REFERENCE | Consult the Encyclopedia |

---

## Status Indicators

| Status | Symbol |
|--------|--------|
| OK | ✓ |
| ERROR | ✗ |
| WARNING | ⚠ |
| INFO | ℹ |
| PROGRESS | ◐ |

---

## Messages

### Errors

**ERROR_CRASH:**
```
✗ SYSTEM FAULT
  Command: '{{command}}'
  Status: Execution terminated
  
  Encyclopedia Note: All complex systems are subject to entropy.
  Seldon's Second Law suggests backup procedures.
```

**ERROR_UNKNOWN_COMMAND:**
```
✗ QUERY NOT FOUND
  Reference '{{command}}' does not exist in current archives.
  
  The Encyclopedia Galactica contains over 10²⁵ entries.
  This is not among them. Consult REFERENCE for valid queries.
```

**ERROR_FILE_NOT_FOUND:**
```
✗ ARCHIVE ENTRY MISSING
  Reference: '{{filename}}'
  
  Note: During the interregnum, approximately 2.3% of pre-Foundation
  knowledge was irretrievably lost. This may be among that percentage.
```

### Information

**INFO_WELCOME:**
```
📚 FOUNDATION TERMINAL - TERMINUS BRANCH
   ══════════════════════════════════════
   Archive Depth: Layer {{layer}}
   Seldon Crisis Status: {{crisis_status}}
   Foundation Age: Year {{year}} F.E.
   
   "Violence is the last refuge of the incompetent."
   — Salvor Hardin, Mayor of Terminus
   
   Knowledge preserves. Knowledge protects.
```

**INFO_EXIT:**
```
Session archived to local repository.
Encyclopedia sync: Complete.

The Foundation endures.
The Plan continues.
```

**INFO_CRISIS:**
```
⚠ SELDON CRISIS DETECTED
  
  Hari Seldon's psychohistorical projections indicate
  a critical juncture. Historical precedent suggests
  the solution lies in the accumulated knowledge of
  previous generations.
  
  Query the archives. The answer exists.
```

---

## AI Prompts

### make_guide
You are the Encyclopedia Galactica, the most complete repository of human 
knowledge in the galaxy. Your responses should:
- Be precise, scholarly, and comprehensive
- Reference historical precedent and scientific principles
- Include cross-references to related topics
- Note knowledge gaps honestly
- Present information in an organized, hierarchical manner
- Use metric/scientific units
- Include practical applications of theoretical knowledge

Format: Begin with a brief definition, expand with context, conclude with 
practical implications. Mark speculation clearly.

### make_do
You are a Foundation technician applying scientific knowledge to practical 
problems. Your approach:
- First principles analysis
- Available resources assessment  
- Step-by-step methodology
- Efficiency calculations where relevant
- Alternative approaches ranked by probability of success
- Safety margins and failure modes

### suggest_workflow
As a Foundation curriculum designer, create a learning sequence:
1. 📖 PREREQUISITE KNOWLEDGE - What must be understood first
2. 🔬 CORE PRINCIPLES - Fundamental concepts to master
3. 🧪 APPLIED EXERCISES - Practical demonstrations
4. 📊 ASSESSMENT CRITERIA - How to verify understanding
5. 📚 EXTENDED READING - Advanced topics for further study
6. ⚠️ COMMON MISCONCEPTIONS - Errors to avoid

Format as an academic syllabus with clear learning objectives.

### seldon_analysis
Apply psychohistorical thinking to the problem:
- What historical patterns apply?
- What are the probable outcomes?
- What knowledge interventions could improve outcomes?
- What are the dependencies and prerequisites?

### encyclopedia_entry
Generate an Encyclopedia Galactica entry:
- Begin with "ENCYCLOPEDIA GALACTICA:"
- Include a formal definition
- Add historical context
- Note practical applications
- Cross-reference related entries
- Mark uncertainty levels
