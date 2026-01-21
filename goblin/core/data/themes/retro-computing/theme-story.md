# Retro Computing - DOS/Apple II Era Theme

## Theme Overview

**Retro Computing** transports you to the golden age of personal computers—DOS command prompts, Apple II beige, floppy disks that made satisfying clicking sounds, and error messages that somehow felt like conversations.

### Theme Identity

- **Era**: 1980s-1990s, golden age of personal computing
- **Aesthetic**: MS-DOS green screens, Apple II simplicity, beige and tan colors, monospace fonts
- **Tone**: Technical but hopeful, matter-of-fact, slightly anxious, helpful without fussiness
- **Emoji Set**: 💾 🖥️ ⌨️ 🔌 📠 🎮 ▓ █ ⚙️ 🔊
- **Core Philosophy**: Computers were tools that talked back to you, honestly

---

## System Variable Mappings

How uDOS core concepts transform into Retro Computing vocabulary:

| System Variable | Retro Computing Equivalent | Emoji | Context |
|-----------------|---------------------------|-------|---------|
| Sandbox | Boot Environment | 🖥️ | Your isolated computing session |
| Plugin | Device Driver | 🔌 | Hardware/software extensions |
| Command | Command Line Instruction | ⌨️ | Direct typed command |
| Syntax Error | SYSTEM FAULT | ❌ | Critical program failure |
| Runtime Error | GENERAL PROTECTION FAULT | 💥 | System crashed during execution |
| Warning | DISK SPACE WARNING | ⚠️ | Important system notice |
| Success | PROCESS COMPLETED SUCCESSFULLY | ✅ | Program ran without error |
| Status Update | STATUS REPORT | 📊 | System condition report |
| Progress | FILES PROCESSED | 📈 | Progress through operation |
| Debug Mode | DEBUG MODE ACTIVE | 🖥️ | Running in developer mode |
| Cache | MEMORY BANK | 💾 | Data cached in RAM |
| Log File | ACTIVITY LOG | 📄 | Record of operations |
| Process Queue | QUEUE BUFFER | 📋 | Tasks awaiting processing |
| Memory Usage | RAM USAGE | 💾 | Memory consumption (640K...) |
| File System | DIRECTORY STRUCTURE | 📁 | File organization on disk |
| Network | MODEM CONNECTION | 📠 | Network/dial-up communication |
| Security Check | COPY PROTECTION CHECK | 🔒 | License verification |
| Backup | BACKUP DISK | 💾 | Creating backup on floppies |
| Update | INSTALL PATCH | 🔄 | Installing updates |
| Initialization | SYSTEM BOOT | 🔌 | Cold boot startup |
| Shutdown | SHUTDOWN SEQUENCE | ⏻️ | Graceful shutdown |
| Timeout | TIMEOUT ERROR | ⏱️ | Operation exceeded time limit |
| Overflow | BUFFER OVERFLOW | 💥 | Capacity exceeded |
| Permission Denied | ACCESS DENIED | 🚫 | No permission for operation |
| File Not Found | FILE NOT FOUND | 🤷 | File doesn't exist |
| Connection Error | MODEM NOT RESPONDING | 📠 | Network connection failed |
| Configuration | CONFIG.SYS | ⚙️ | System configuration |
| Loop Execution | ENDLESS LOOP | 🔄 | Infinite loop detected |
| Data Validation | CHECKSUM VERIFICATION | ✓ | Data integrity check |
| Optimization | DEFRAGMENTATION | ⚡ | Performance optimization |
| Disaster Recovery | RECOVERY DISK BOOT | 💾 | System recovery from disaster |

---

## Message Templates

### Error Messages (❌ SYSTEM FAULT)

**When**: Critical program failure
**Prefix**: ❌ (the error indicator)
**Verb**: SYSTEM FAULT (DOS error message style)

**Template**: `❌ SYSTEM FAULT - {error_details}`

**Examples**:
```
❌ SYSTEM FAULT - Illegal instruction at memory address 0x4A2B
❌ SYSTEM FAULT - Disk read error on drive C:
❌ SYSTEM FAULT - Segmentation violation in kernel module
❌ SYSTEM FAULT - Runtime error at line 4082 in MAIN.BAS
```

**Flavor Subtext**: "ABORT, RETRY, FAIL?" (the original choice) or "System has halted."

---

### Success Messages (✅ PROCESS COMPLETED SUCCESSFULLY)

**When**: Program completes without errors
**Prefix**: ✅ (success indicator)
**Verb**: PROCESS COMPLETED SUCCESSFULLY (old-school confirmation)

**Template**: `✅ PROCESS COMPLETED SUCCESSFULLY - {result}`

**Examples**:
```
✅ PROCESS COMPLETED SUCCESSFULLY - File copy of 2048 bytes
✅ PROCESS COMPLETED SUCCESSFULLY - Installation complete. Restart system.
✅ PROCESS COMPLETED SUCCESSFULLY - Disk scan completed, 0 errors found
✅ PROCESS COMPLETED SUCCESSFULLY - Modem handshake successful at 14400 baud
```

**Flavor Subtext**: "All systems nominal." or "Press any key to continue..."

---

### Warning Messages (⚠️ DISK SPACE WARNING)

**When**: Something needs attention
**Prefix**: ⚠️ (alert)
**Verb**: DISK SPACE WARNING (system notice)

**Template**: `⚠️ DISK SPACE WARNING - {alert}`

**Examples**:
```
⚠️ DISK SPACE WARNING - Less than 1 MB remaining on drive C:
⚠️ DISK SPACE WARNING - Memory low; close unnecessary programs
⚠️ DISK SPACE WARNING - Extended memory corruption detected
⚠️ DISK SPACE WARNING - Unstable modem connection; packets lost
```

**Flavor Subtext**: "Please free up disk space before continuing." or "Running low on resources."

---

### Status Messages (📊 STATUS REPORT)

**When**: Reporting system status
**Prefix**: 📊 (data representation)
**Verb**: STATUS REPORT (standard system check)

**Template**: `📊 STATUS REPORT - {status}`

**Examples**:
```
📊 STATUS REPORT - All peripherals online and responsive
📊 STATUS REPORT - 640K base memory available, 4096K extended
📊 STATUS REPORT - Disk I/O subsystem functioning normally
📊 STATUS REPORT - Parallel port ready for printing
```

**Flavor Subtext**: "System status normal." or "Ready for next instruction."

---

## Style Guide

### Punctuation & Tone

- **Hyphens as separators**: Like DOS error messages (FAULT - description)
- **All caps for emphasis**: SYSTEM, FAULT, WARNING—nothing whispered
- **Periods at end**: "System has halted." (finality)
- **No emojis in command prompts**: But used in flavor text
- **Brevity is virtue**: DOS didn't waste bytes

### Emoji Usage

Hardware and state representation:
- 💾 Storage, memory, floppy disks, saving data
- 🖥️ The computer itself, the system, the monitor
- ⌨️ User input, keyboard commands
- 🔌 Power, connections, peripherals
- 📠 Modem, network, communications
- 🎮 Fun features, games, entertainment
- ▓ and █ Actual block characters for progress bars
- ⚙️ Configuration, system settings, options

### Formatting Examples

**Good Retro Computing flavor**:
```
C:\> DIR *.TXT
📄 DOCUMENTS.TXT        1024  1992-04-15
📄 LETTERS.TXT          2048  1992-04-16
📄 NOTES.TXT            512   1992-04-17

3 File(s)       3584 bytes
2457600 bytes free

✅ PROCESS COMPLETED SUCCESSFULLY - Directory listing complete
Press any key to continue...

C:\> _
```

**Avoid**:
- Lowercase (DOS screams)
- Modern UI metaphors
- Cutesy language
- Breaking the hardware focus

---

## Flavor Text Scenarios

### Boot Sequence

```
🖥️ ▓▓▓▓▓▓▓▓ SYSTEM BOOT

Award BIOS v4.51PG 08/01/92
Copyright (c) 1992 Award Software Inc.

Checking system memory... 640K OK
Extended memory test... 4096K OK

System initialization complete.
Welcome to RetroCompute OS.
```

**Context**: Startup sequence with vintage BIOS aesthetic.

---

### Shutdown Sequence

```
⏻️ SHUTDOWN SEQUENCE INITIATED
Closing open files... done
Flushing disk cache... done
Saving system state... done

Please wait... Do not power off.
It is now safe to turn off your computer.
```

**Context**: Graceful shutdown with safety warning.

---

### Empty Result

```
C:\> DIR *.BAK
No matching files found.

Returning to command prompt...
C:\>_
```

**Context**: Query returns nothing—DOS-style response.

---

### Long Operation with Progress

```
⏳ COPYING FILES...
▓▓▓▓▓░░░░░░░░░░░░░░░░ 22%

Source: A:\
Destination: C:\DATA
15 files remaining...
```

**Context**: Progress bar in authentic block characters.

---

### Completion & Command Prompt

```
✅ PROCESS COMPLETED SUCCESSFULLY
2048 bytes copied in 3.2 seconds
Transfer rate: 640K/sec

C:\> _
```

**Context**: Back to command prompt, ready for next instruction.

---

## Example Interactions

### File Creation

**User Command**: `NEWFILE /data/records.txt`

**System Response**:
```
[Internal: File created]

✅ PROCESS COMPLETED SUCCESSFULLY - File created

C:\DATA> _
```

---

### Access Denied

**User Command**: `DELETE /system/bios.rom`

**System Response**:
```
❌ SYSTEM FAULT - Access Denied
This file is write-protected.

ABORT, RETRY, FAIL? _
```

---

### Backup Operation

**User Command**: `BACKUP --full`

**System Response**:
```
💾 BACKUP UTILITY v1.0
Backing up all files...

⏳ Initializing drive A:
Insert backup disk 1 of 3...
Waiting for disk...

[When ready]
▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░ 35%

1247 files copied...
```

---

### System Information

**User Command**: `DEBUG --verbose`

**System Response**:
```
📊 STATUS REPORT - SYSTEM DIAGNOSTIC

CPU: 80286-12MHz
RAM: 640K base + 4096K extended
HDD: 40MB (C:)
Floppy: 3.5" 1.44MB (A:)
Video: VGA 640x480

All systems operational.
Ready for next command.

C:\> _
```

---

## Tips for Retro Computing Enthusiasts

- **Respect the hardware**: These systems pushed their limits
- **Embrace constraints**: 640K should be enough for anybody
- **Save your work**: Always back up to floppy disks
- **Read the manual**: RTFM (ask for more information)
- **Keep error messages close**: They tell you what went wrong

---

## Theme Integration Points

Retro Computing activates at:

1. **Startup** → Boot sequence and system check
2. **Command Success** → PROCESS COMPLETED SUCCESSFULLY
3. **Command Failure** → SYSTEM FAULT errors
4. **Warnings** → DISK SPACE WARNING notices
5. **Status Queries** → STATUS REPORT readout
6. **File Operations** → Directory listings
7. **Long Operations** → Progress bars with ▓░ blocks
8. **Shutdown** → Safety sequence

### Display Pipeline

Retro Computing messages appear AFTER:
- ✅ Core execution complete
- ✅ Operations logged
- ✅ Error checking finished

Themes stay in display layer; core debugging remains clear.

---

## Extending Retro Computing

### New System Concepts

To add a feature:

1. What's the technical operation?
2. What's the DOS/Apple II equivalent?
3. Choose appropriate emoji
4. Add to variables.json
5. Create example messages
6. Document the pattern

### Community Contributions

Retro Computing welcomes:
- Apple II variant (cleaner aesthetics)
- Commodore 64 theme
- ZX Spectrum variant
- Expanded vintage error messages
- Additional BIOS/boot sequences
- Period-appropriate ASCII art

---

## Design Philosophy

**Retro Computing** proves that constraints breed character. By honoring the genuine limitations of 1980s-90s computers:

🖥️ **Honesty** - Error messages that actually explain what went wrong  
💾 **Permanence** - Saving and backups matter, always  
⌨️ **Control** - The user is in command via typed instructions  
🔌 **Hardware** - Respect the actual machines and their capabilities  
📊 **Clarity** - Status reports that leave no ambiguity  

The old ways work. The simple ways endure.

---

*Last Updated: 2026-01-14*  
*Part of Theme Architecture Redesign (Alpha v1.0.2.0)*  
*"Have you tried turning it off and on again?"*
