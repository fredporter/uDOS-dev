# Handy STT - Code Container

**Container ID:** `handy`  
**License:** MIT  
**Type:** Speech-to-Text Engine

## Overview

Handy is a free, open source, and extensible speech-to-text application that works completely offline. It uses Whisper or Parakeet models to transcribe speech on-device without cloud dependencies.

## Features

- 🆓 Free and open source (MIT)
- 🔒 Completely private - voice never leaves your device
- ⚡ Fast transcription with multiple model options
- 🎯 Voice Activity Detection (Silero VAD)
- 🌍 Automatic language detection (Parakeet V3)
- 🖥️ Cross-platform: macOS, Windows, Linux

## Models

### Whisper Models (GPU Accelerated)

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| Small | 487MB | Fastest | Good |
| Medium | 492MB | Fast | Better |
| Turbo | 1.6GB | Medium | Great |
| Large | 1.1GB | Slower | Best |

### Parakeet Models (CPU Optimized)

| Model | Size | Features |
|-------|------|----------|
| V2 | 473MB | Fast, reliable |
| V3 | 478MB | Auto language detection |

**Parakeet V3** is recommended for uDOS - runs well on CPU with automatic language detection.

## uDOS Integration

### TUI Commands

```
VOICE LISTEN                    # Start listening (push-to-talk)
VOICE LISTEN -t 30              # Listen for 30 seconds max
VOICE LISTEN > message.txt      # Save transcription to file
VOICE TRANSCRIBE recording.wav  # Transcribe audio file
VOICE MODEL parakeet-v3         # Set STT model
VOICE DOWNLOAD whisper-small    # Download model
```

### uPY Script Usage

```python
# voice-note.upy
SET note VOICE LISTEN
FILE WRITE "notes/$(DATE).txt" "$(note)"
VOICE SAY "Note saved"
```

### Combined TTS/STT Workflow

```python
# voice-assistant.upy
VOICE SAY "How can I help you?"
SET input VOICE LISTEN
# Process input...
VOICE SAY "I heard: $(input)"
```

## Installation (Wizard Server)

```bash
# Clone via Wizard library
WIZARD CLONE handy

# Download Parakeet V3 model (recommended for CPU)
python wizard/tools/voice_setup.py --download-model parakeet-v3

# Or download Whisper for GPU systems
python wizard/tools/voice_setup.py --download-model whisper-small
```

## Model Download URLs

If behind a proxy, manually download models:

**Whisper:**
- Small: `https://blob.handy.computer/ggml-small.bin`
- Medium: `https://blob.handy.computer/whisper-medium-q4_1.bin`
- Turbo: `https://blob.handy.computer/ggml-large-v3-turbo.bin`
- Large: `https://blob.handy.computer/ggml-large-v3-q5_0.bin`

**Parakeet:**
- V2: `https://blob.handy.computer/parakeet-v2-int8.tar.gz`
- V3: `https://blob.handy.computer/parakeet-v3-int8.tar.gz`

## System Requirements

### For Whisper Models
- **macOS:** M series Mac or Intel
- **Windows:** Intel, AMD, or NVIDIA GPU
- **Linux:** Intel, AMD, or NVIDIA GPU (Ubuntu 22.04, 24.04)

### For Parakeet Models (Recommended)
- **CPU:** Intel Skylake (6th gen) or equivalent AMD
- **Performance:** ~5x real-time on mid-range hardware
- **No GPU required**

## Architecture

Handy is built with:
- **Frontend:** React + TypeScript + Tailwind CSS
- **Backend:** Rust (Tauri)
- **Inference:** whisper-rs, transcription-rs (ONNX)
- **Audio:** cpal (cross-platform audio I/O)
- **VAD:** vad-rs (Silero Voice Activity Detection)

## File Structure

```
wizard/library/handy/
├── container.json      # Container manifest
├── README.md           # This file
├── repo/               # Cloned Handy source (gitignored)
└── models/             # Downloaded STT models (gitignored)
    ├── ggml-small.bin
    └── parakeet-tdt-0.6b-v3-int8/
```

## Related

- [Piper TTS](../piper/) - Text-to-speech companion
- [Handy CLI](https://github.com/cjpais/handy-cli) - Original Python CLI
- [Voice Service](../../services/voice_service.py) - uDOS voice integration

---

*Part of the uDOS Wizard Library - Offline-first speech recognition*
