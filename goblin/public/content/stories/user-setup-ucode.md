---
title: uDOS User Setup Wizard
version: 1.0.0
description: |
  Interactive setup wizard for uDOS first-time users.
  This story collects essential configuration and preferences.
author: uDOS Team
tags: [setup, onboarding, wizard]
---

# Welcome to uDOS

Let's set up your workspace and preferences. This will only take a few minutes.

```story
{
  "name": "username",
  "label": "What's your name?",
  "type": "text",
  "required": true,
  "placeholder": "Enter your name"
}
```

## Workspace Location

Where would you like to store your workspace files?

```story
{
  "name": "workspace_path",
  "label": "Workspace location",
  "type": "text",
  "required": true,
  "placeholder": "/home/user/workspace"
}
```

## Theme Preference

How do you like your interface?

```story
{
  "name": "theme",
  "label": "Preferred theme",
  "type": "select",
  "required": true,
  "options": ["light", "dark", "auto"]
}
```

## Features

Which features would you like enabled?

```story
{
  "name": "enable_offline",
  "label": "Offline mode",
  "type": "checkbox"
}
```

```story
{
  "name": "enable_mesh",
  "label": "Device mesh networking",
  "type": "checkbox"
}
```

```story
{
  "name": "enable_sync",
  "label": "Cloud sync (optional)",
  "type": "checkbox"
}
```

## Contact

How can we reach you for updates?

```story
{
  "name": "email",
  "label": "Email address",
  "type": "email",
  "required": false,
  "placeholder": "your@email.com"
}
```

## Additional Notes

Any other preferences or notes?

```story
{
  "name": "notes",
  "label": "Additional notes",
  "type": "textarea",
  "placeholder": "Tell us anything else about your setup..."
}
```

---

## Variables & Functions

```javascript
const getUserSummary = (answers) => {
  return `Setup for ${answers.username} at ${answers.workspace_path} (${answers.theme} theme)`;
};
```
