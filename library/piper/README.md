# Piper TTS - Code Container

**Container ID:** `piper`  
**License:** GPL-3.0 (new OHF-Voice fork) / MIT (original rhasspy)  
**Type:** Text-to-Speech Engine

## Overview

Piper is a fast, local neural text-to-speech system that produces natural-sounding speech entirely offline. It's ideal for uDOS voice synthesis on user devices without cloud dependencies.

## History

- **Original:** [rhasspy/piper](https://github.com/rhasspy/piper) (MIT, archived Oct 2025)
- **Current:** [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) (GPL-3.0, active)

## Features

- ⚡ Fast synthesis (~10x real-time on Raspberry Pi 4)
- 🌍 30+ languages with multiple voices
- 🔒 Completely offline - no cloud required
- 📦 Small model sizes (16MB - 100MB per voice)
- 🎛️ Adjustable speed and speaker selection

## Voice Models

Voice models are hosted on HuggingFace:
- https://huggingface.co/rhasspy/piper-voices

### Model Quality Tiers

| Quality | Size | Speed | Use Case |
|---------|------|-------|----------|
| `x_low` | ~16MB | Fastest | Low-resource devices |
| `low` | ~20MB | Fast | Raspberry Pi |
| `medium` | ~60MB | Normal | Desktop |
| `high` | ~100MB | Slower | High quality |

## uDOS Integration

### TUI Commands

```
VOICE SAY Hello world           # Speak text
VOICE SAY -f message.txt        # Speak file contents
VOICE MODEL en_US-lessac-medium # Set voice model
VOICE VOICES                    # List available voices
VOICE DOWNLOAD en_GB-alba-medium # Download voice model
```

### uPY Script Usage

```python
# voice-demo.upy
VOICE SAY "Welcome to uDOS"
VOICE MODEL "en_US-amy-low"
VOICE SAY "System ready for voice commands"
```

## Installation (Wizard Server)

```bash
# Clone via Wizard library
WIZARD CLONE piper

# Or manual git clone
git clone https://github.com/OHF-Voice/piper1-gpl wizard/library/piper/repo

# Download default voice model
python wizard/tools/voice_setup.py --download-model en_US-lessac-medium
```

## System Requirements

- **CPU:** Any modern processor (x64 or ARM64)
- **Memory:** 256MB - 2GB depending on model
- **Storage:** ~60MB for engine + models
- **GPU:** Optional ONNX Runtime acceleration

## File Structure

```
wizard/library/piper/
├── container.json      # Container manifest
├── README.md           # This file
├── repo/               # Cloned piper source (gitignored)
└── models/             # Downloaded voice models (gitignored)
    ├── en_US-lessac-medium.onnx
    └── en_US-lessac-medium.onnx.json
```

## Related

- [Handy STT](../handy/) - Speech-to-text companion
- [Voice Service](../../services/voice_service.py) - uDOS voice integration

---

*Part of the uDOS Wizard Library - Offline-first voice synthesis*
