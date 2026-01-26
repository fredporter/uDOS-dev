---
title: User Setup
version: 2.0.0
author: uDOS
created: 2026-01-06
tags: [setup, profile, configuration, system]
description: User profile configuration and first-run setup wizard
permissions:
  execute: true
  save_state: true
  file_access: true
---

# User Setup Script

First-run configuration wizard that creates and populates the user profile.

---

## Header

Display the setup banner.

```upy
PRINT "============================================================"
PRINT "  uDOS USER SETUP - v2.0.0"
PRINT "============================================================"
PRINT ""
```

---

## Check Existing Profile

Check if user.json exists and create from template if missing.

```upy
# Check if user.json exists
file_exists = FILE.EXISTS("memory/user.json")

IF NOT file_exists:
    PRINT "Creating user.json from template..."
    FILE.COPY("core/data/templates/user.template.json", "memory/user.json")
    needs_setup = True
ELSE:
    needs_setup = False

# Load the profile
user_profile = FILE.LOAD_JSON("memory/user.json")
updated = False
```

---

## Name Configuration

Get or set the user's name (required field).

```upy
# Get current name
user_name = user_profile.get("USER_PROFILE", {}).get("NAME", "")

IF user_name == "":
    PRINT ""
    PRINT "Let's set up your profile."
    PRINT ""
    user_name = INPUT "Enter your name:"
    
    IF user_name == "":
        PRINT "Name is required!"
        user_name = INPUT "Enter your name:"
    
    user_profile["USER_PROFILE"]["NAME"] = user_name
    updated = True

PRINT "✅ Name: " + user_name
```

---

## Timezone Configuration

Set the user's timezone (optional, defaults to UTC).

```upy
# Get current timezone
timezone = user_profile.get("USER_PROFILE", {}).get("TIMEZONE", "")

IF timezone == "":
    PRINT ""
    PRINT "Common timezones: UTC, Australia/Sydney, America/New_York, Europe/London"
    tz_input = INPUT "Enter timezone (press ENTER for UTC):"
    
    IF tz_input == "":
        timezone = "UTC"
    ELSE:
        timezone = tz_input
    
    user_profile["USER_PROFILE"]["TIMEZONE"] = timezone
    updated = True

PRINT "✅ Timezone: " + timezone
```

---

## Location Configuration

Set the user's general location (optional for privacy).

```upy
# Get current location
location = user_profile.get("USER_PROFILE", {}).get("LOCATION", "")

IF location == "":
    PRINT ""
    PRINT "Location helps with weather and local knowledge."
    PRINT "(This is optional - leave blank for privacy)"
    loc_input = INPUT "Enter location (city/region):"
    
    IF loc_input == "":
        location = "Not specified"
    ELSE:
        location = loc_input
    
    user_profile["USER_PROFILE"]["LOCATION"] = location
    updated = True

PRINT "✅ Location: " + location
```

---

## Preferred Mode

Set the user's preferred interface mode.

```upy
# Get current mode preference
mode = user_profile.get("USER_PROFILE", {}).get("PREFERRED_MODE", "")

IF mode == "" OR needs_setup:
    PRINT ""
    PRINT "Interface modes:"
    PRINT "  STANDARD  - Normal terminal experience"
    PRINT "  MINIMAL   - Reduced output, faster"
    PRINT "  VERBOSE   - Detailed feedback"
    PRINT ""
    
    CHOICE "Select preferred mode:"
        OPTION "Standard" -> SET_STANDARD
        OPTION "Minimal" -> SET_MINIMAL
        OPTION "Verbose" -> SET_VERBOSE
    END

LABEL SET_STANDARD
mode = "STANDARD"
GOTO MODE_DONE

LABEL SET_MINIMAL
mode = "MINIMAL"
GOTO MODE_DONE

LABEL SET_VERBOSE
mode = "VERBOSE"
GOTO MODE_DONE

LABEL MODE_DONE
user_profile["USER_PROFILE"]["PREFERRED_MODE"] = mode
updated = True
PRINT "✅ Mode: " + mode
```

---

## Save Profile

Save the updated profile if changes were made.

```upy
IF updated:
    FILE.SAVE_JSON(user_profile, "memory/user.json")
    PRINT ""
    PRINT "✅ Profile saved to memory/user.json"
```

---

## Setup Complete

Display completion message and summary.

```upy
PRINT ""
PRINT "============================================================"
PRINT "  Setup Complete!"
PRINT "============================================================"
PRINT ""
PRINT "Your profile:"
PRINT "  Name:     " + user_name
PRINT "  Timezone: " + timezone
PRINT "  Location: " + location
PRINT "  Mode:     " + mode
PRINT ""
PRINT "You can update these settings anytime with:"
PRINT "  CONFIG USER"
PRINT ""

# Award XP for completing setup
IF needs_setup:
    XP + 25
    PRINT "🎉 +25 XP for completing setup!"

END
```

---

## Notes

This script demonstrates:

- **File Operations**: Check, copy, load, save JSON files
- **Optional Inputs**: Default values for skipped fields
- **Profile Schema**: Standard user.template.json structure
- **Privacy Consideration**: Location is optional
- **First-run Detection**: Different behavior for new vs existing users

### Profile Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| NAME | Yes | - | User's display name |
| TIMEZONE | No | UTC | Local timezone |
| LOCATION | No | Not specified | General location |
| PREFERRED_MODE | No | STANDARD | Interface mode |

### Related Commands

- `CONFIG USER` - Edit profile settings
- `CONFIG SHOW` - Display current config
- `CONFIG RESET` - Reset to defaults
