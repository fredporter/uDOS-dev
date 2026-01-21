# Songscribe - Code Container

**Container ID:** `songscribe`  
**License:** MIT  
**Type:** Audio-to-Sheet-Music Engine

## Overview

Songscribe is the fastest way to turn any song into sheet music. Using machine learning algorithms for instrument separation and audio-to-MIDI conversion, it provides an incredible starting point for transcribing every part of a song in minutes.

## Features

- 🎵 **Audio Upload** - File upload or YouTube URL
- 🎸 **Instrument Separation** - ML-powered stem isolation (Moseca/Demucs)
- 🎹 **Audio-to-MIDI** - Neural network conversion (Spotify Basic Pitch)
- 🥁 **Drum Transcription** - Specialized drum detection (ADTOF)
- 📜 **Sheet Music Generation** - Automatic score creation
- 🎛️ **MIDI Editor** - Customize transcription parameters
- 📄 **PDF Export** - Print-ready sheet music

## Presets

| Preset | Stems | Use Case |
|--------|-------|----------|
| **Solo** | 1 instrument | Single instrument pieces |
| **Duet** | Vocals, No Vocals | Singer + accompaniment |
| **Small Band** | Vocals, Drums, Bass, Other | Rock/pop bands |
| **Full Band** | Vocals, Drums, Bass, Guitar, Piano, Other | Complex arrangements |

## Groovebox Integration

Songscribe works seamlessly with the uDOS Groovebox extension:

```
┌─────────────────────────────────────────────────────────────┐
│                    SONGSCRIBE WORKFLOW                       │
│                                                              │
│   Audio File / YouTube URL                                   │
│           ↓                                                  │
│   Instrument Separation (Moseca)                             │
│           ↓                                                  │
│   Audio-to-MIDI (Basic Pitch)                                │
│           ↓                                                  │
│   MIDI File (.mid)                                           │
│           ↓                                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              GROOVEBOX INTEGRATION                   │   │
│   │                                                      │   │
│   │   MIDI → MML Conversion                              │   │
│   │   Edit in Groovebox Pattern Editor                   │   │
│   │   Add 808 drum patterns                              │   │
│   │   Export to uDOS audio system                        │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## TUI Commands

```bash
# Transcribe audio file
MUSIC TRANSCRIBE song.mp3

# Transcribe from YouTube
MUSIC TRANSCRIBE "https://youtube.com/watch?v=..."

# Separate stems only
MUSIC SEPARATE song.mp3 --preset full_band

# Export stems
MUSIC STEMS song.mp3

# Generate score from MIDI
MUSIC SCORE melody.mid

# Import transcribed MIDI to Groovebox
MUSIC IMPORT transcription.mid
```

## uPY Script Examples

```python
# transcribe-song.upy
# Full transcription workflow

SET song "memory/music/mysong.mp3"
MUSIC TRANSCRIBE "$(song)" --preset small_band

# Get the separated stems
MUSIC STEMS "$(song)"

# Import bass line to Groovebox for editing
MUSIC IMPORT "$(song).stems/bass.mid" AS bass_pattern

# Add 808 drums
MUSIC 808 boom_bap

# Play together
MUSIC PLAY bass_pattern
```

## Backend Dependencies

The Songscribe backend uses these key Python libraries:

### Moseca (Instrument Separation)
- Based on Demucs from Facebook AI Research
- High-quality source separation
- Multiple stem configurations

### Basic Pitch (Audio-to-MIDI)
- Spotify's neural network for pitch detection
- Polyphonic note detection
- Confidence-based note extraction

### ADTOF (Drum Transcription)
- Specialized for drum kit transcription
- Kick, snare, hi-hat, tom detection
- Timing and velocity extraction

## Installation (Wizard Server)

```bash
# Clone via Wizard library
WIZARD CLONE songscribe

# Install Python backend dependencies
pip install moseca basic-pitch adtof

# Install Node.js frontend
cd wizard/library/songscribe/repo
npm install
npm run build
```

## System Requirements

- **CPU:** Modern multi-core processor
- **Memory:** 8GB+ RAM (ML models are memory-intensive)
- **GPU:** Optional CUDA support for faster processing
- **Storage:** ~2GB for ML models
- **Python:** 3.9+
- **Node.js:** 18+ (for frontend)

## File Structure

```
wizard/library/songscribe/
├── container.json      # Container manifest
├── README.md           # This file
├── repo/               # Cloned songscribe source (gitignored)
│   ├── app/            # Next.js app
│   ├── components/     # React components
│   └── utils/          # Utilities
└── models/             # Downloaded ML models (gitignored)
    ├── demucs/         # Instrument separation
    ├── basic-pitch/    # Audio-to-MIDI
    └── adtof/          # Drum transcription
```

## Related

- [Groovebox Extension](../../../extensions/groovebox/) - MML music production
- [Music Handler](../../../core/commands/music_handler.py) - TUI music commands
- [Audio Transport](../../../extensions/transport/audio/) - Audio data transfer

## Credits

- **Moseca** - Fabio Grasso (instrument separation)
- **Basic Pitch** - Spotify (audio-to-MIDI)
- **ADTOF** - M. Zehren (drum transcription)
- **Songscribe** - Gabe Serna

---

*Part of the uDOS Wizard Library - AI-powered music transcription*
