---
title: uCode Format
author: uMarkdown Team
date: 2026-01-20
category: formats
---

# uCode Format

Build executable markdown documents with runtime blocks.

## What is uCode?

uCode format (`-ucode.md`) combines markdown with executable code blocks that can maintain state, handle user input, and create interactive experiences.

## Runtime Blocks

### State Block

Initialize variables:

\`\`\`state
$player = { "name": "Hero", "level": 1 }
$gold = 100
\`\`\`

### Form Block

Collect user input:

\`\`\`form
name: text
age: number
agreed: toggle
\`\`\`

### Navigation Block

Create interactive choices:

\`\`\`nav
choice: "Option 1"
goto: section_1
choice: "Option 2"
goto: section_2
\`\`\`

## Use Cases

- Interactive fiction and games
- Educational tutorials
- Configuration wizards
- Decision trees
- Dynamic documentation

## Learn More

Check the full [uCode documentation](#) for advanced features.
