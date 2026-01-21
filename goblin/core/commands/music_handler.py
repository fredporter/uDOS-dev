"""
Music/Groovebox Command Handler
Alpha v1.0.3.0+

TUI integration for the Groovebox extension - MML-based music production.

Commands:
- MUSIC PLAY <pattern.mml|preset> - Play MML pattern or 808 preset
- MUSIC STOP - Stop playback
- MUSIC EDIT [pattern.mml] - Open pattern editor
- MUSIC EXPORT <pattern.mml> <output.mid> - Export to MIDI
- MUSIC PRESETS - List available 808 presets
- MUSIC BPM <tempo> - Set tempo (40-300)
- MUSIC LIBRARY - Browse sound library
- MUSIC HELP - Show help
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import subprocess
import platform
import threading
import struct
import wave

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("command-music")


class MusicHandler:
    """
    Handler for MUSIC/PLAY commands.

    Integrates groovebox extension with TUI for music production.
    """

    def __init__(self):
        self.groovebox = None
        self.current_tempo = 120
        self.is_playing = False
        self._playback_process = None
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if groovebox extension is available"""
        try:
            from wizard.extensions.groovebox.engine import MMLParser, Sequencer, MidiExporter
            from wizard.extensions.groovebox.instruments import Drum808

            self.parser = MMLParser()
            self.sequencer = Sequencer()
            self.exporter = MidiExporter()
            self.drum808 = Drum808()
            self.groovebox = True
            logger.info("[LOCAL] Groovebox extension loaded")
        except ImportError as e:
            logger.warning(f"[LOCAL] Groovebox not available: {e}")
            self.groovebox = None
            self.parser = None
            self.sequencer = None
            self.exporter = None
            self.drum808 = None

    def handle(self, command: str, params: List[str], grid, parser) -> Optional[str]:
        """
        Route MUSIC commands to appropriate handlers.

        Args:
            command: Command name (MUSIC, PLAY)
            params: Command parameters
            grid: Grid instance for display
            parser: Parser instance

        Returns:
            Success/error message or None
        """
        if not self.groovebox:
            return (
                "❌ Groovebox extension not installed\n   Run: PLUGIN INSTALL groovebox"
            )

        if not params:
            return self._show_help()

        subcommand = params[0].upper()

        # Route to handlers
        if subcommand == "PLAY":
            return self._handle_play(params[1:], grid)
        elif subcommand == "STOP":
            return self._handle_stop()
        elif subcommand == "EDIT":
            return self._handle_edit(params[1:], grid)
        elif subcommand == "EXPORT":
            return self._handle_export(params[1:])
        elif subcommand == "PRESETS":
            return self._handle_presets()
        elif subcommand == "BPM":
            return self._handle_bpm(params[1:])
        elif subcommand == "LIBRARY":
            return self._handle_library(grid)
        elif subcommand == "NEW":
            return self._handle_new(params[1:])
        elif subcommand == "808":
            return self._handle_808(params[1:])
        elif subcommand == "HELP":
            return self._show_help()
        else:
            # Treat as pattern name directly
            return self._handle_play(params, grid)

    def _handle_play(self, params: List[str], grid) -> str:
        """Play MML pattern or preset with actual audio output"""
        if not params:
            return "❌ Usage: MUSIC PLAY <pattern.mml|preset_name>\n   Example: MUSIC PLAY house_basic"

        target = params[0]
        pattern = None
        source_name = target

        # Check if it's an 808 preset
        presets = self.drum808.list_presets()
        if target.lower() in presets:
            pattern = self.drum808.get_preset(target.lower())
            source_name = f"808/{target.lower()}"
        else:
            # Check if it's an MML file
            target_path = Path(target)
            if not target_path.suffix:
                target_path = target_path.with_suffix(".mml")

            # Search in memory/music/ or absolute path
            search_paths = [
                target_path,
                Path.home() / ".udos" / "memory" / "music" / target_path.name,
                Path("memory/music") / target_path.name,
            ]

            mml_file = None
            for sp in search_paths:
                if sp.exists():
                    mml_file = sp
                    break

            if mml_file:
                mml_content = mml_file.read_text()
                pattern = self.parser.parse(mml_content)
                source_name = mml_file.name
            elif any(c in target for c in "cdefgabCDEFGABr"):
                # Try parsing as inline MML
                try:
                    pattern = self.parser.parse(target)
                    source_name = "inline"
                except Exception as e:
                    logger.error(f"[LOCAL] MML parse error: {e}")
                    return f"❌ Invalid MML: {e}"

        if not pattern:
            return f"❌ Pattern not found: {target}\n   Use MUSIC PRESETS to see available presets"

        # Render and play
        return self._render_and_play(pattern, source_name)

    def _render_and_play(self, pattern, source_name: str) -> str:
        """Render pattern to WAV and play it"""
        try:
            from extensions.transport.audio.groovebox import (
                ImperialGroovebox,
                Pattern,
                Note,
                SoundBank,
            )

            groovebox = ImperialGroovebox()

            # Convert MMLPattern (from groovebox/engine) to Pattern (for transport/audio)
            # if needed
            if hasattr(pattern, "bank"):
                # Already a transport/audio Pattern
                render_pattern = pattern
            else:
                # Convert MMLPattern to transport Pattern
                notes = []
                for mml_note in pattern.notes:
                    if hasattr(mml_note, "midi_note"):
                        # MMLNote from engine
                        midi_note = mml_note.midi_note
                        is_rest = midi_note == -1
                        length = 4.0 / mml_note.length  # Convert to beats
                        velocity = mml_note.velocity / 127.0
                    else:
                        # Already a Note
                        midi_note = mml_note.pitch
                        is_rest = mml_note.is_rest
                        length = mml_note.length
                        velocity = mml_note.velocity

                    notes.append(
                        Note(
                            pitch=midi_note if midi_note >= 0 else 0,
                            length=length,
                            velocity=velocity,
                            is_rest=is_rest or midi_note == -1,
                        )
                    )

                render_pattern = Pattern(
                    name=source_name, notes=notes, bank=SoundBank.IMPERIAL_808
                )

            samples = groovebox.render_pattern(render_pattern)

            # Create temp WAV file
            temp_dir = Path.home() / ".udos" / "memory" / ".tmp" / "music"
            temp_dir.mkdir(parents=True, exist_ok=True)
            wav_file = temp_dir / "playback.wav"

            self._save_wav(samples, wav_file)

            # Play audio in background
            self._play_audio_file(wav_file)

            note_count = len(pattern.notes)
            duration = len(samples) / 44100
            self.is_playing = True

            tempo = pattern.tempo if hasattr(pattern, "tempo") else self.current_tempo
            logger.info(
                f"[LOCAL] Playing: {source_name} ({note_count} notes, {duration:.1f}s)"
            )
            return f"🎵 Playing: {source_name}\n   {note_count} notes @ {tempo} BPM\n   Duration: {duration:.1f}s\n   MUSIC STOP to end"

        except ImportError:
            # Fallback: show pattern info without audio
            note_count = len(pattern.notes)
            logger.info(f"[LOCAL] Pattern loaded (no audio): {source_name}")
            return f"🎵 Loaded: {source_name}\n   {note_count} notes @ {self.current_tempo} BPM\n   💡 Audio playback requires transport/audio module"
        except Exception as e:
            logger.error(f"[LOCAL] Playback error: {e}")
            return f"❌ Playback error: {e}"

    def _save_wav(self, samples: List[float], filepath: Path):
        """Save samples to WAV file"""
        sample_rate = 44100
        max_val = 32767

        with wave.open(str(filepath), "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)

            for sample in samples:
                # Clamp and convert to 16-bit PCM
                clamped = max(min(sample * 0.7, 1.0), -1.0)
                packed = struct.pack("<h", int(clamped * max_val))
                wav.writeframes(packed)

    def _play_audio_file(self, filepath: Path):
        """Play audio file using system player"""
        # Stop any existing playback
        self._stop_playback()

        system = platform.system()

        def play_background():
            try:
                if system == "Darwin":  # macOS
                    self._playback_process = subprocess.Popen(
                        ["afplay", str(filepath)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                elif system == "Linux":
                    # Try aplay (ALSA), then paplay (PulseAudio)
                    for player in ["aplay", "paplay", "play"]:
                        try:
                            self._playback_process = subprocess.Popen(
                                [player, str(filepath)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                            break
                        except FileNotFoundError:
                            continue
                elif system == "Windows":
                    # Use PowerShell to play audio
                    self._playback_process = subprocess.Popen(
                        [
                            "powershell",
                            "-c",
                            f"(New-Object Media.SoundPlayer '{filepath}').PlaySync()",
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            except Exception as e:
                logger.error(f"[LOCAL] Audio playback failed: {e}")

        # Start playback in background thread
        thread = threading.Thread(target=play_background, daemon=True)
        thread.start()

    def _stop_playback(self):
        """Stop current playback"""
        if self._playback_process:
            try:
                self._playback_process.terminate()
                self._playback_process = None
            except Exception:
                pass

    def _handle_stop(self) -> str:
        """Stop playback"""
        if not self.is_playing and not self._playback_process:
            return "⏹ Nothing playing"

        self._stop_playback()
        self.is_playing = False
        self.sequencer.stop()
        logger.info("[LOCAL] Playback stopped")
        return "⏹ Stopped"

    def _handle_edit(self, params: List[str], grid) -> str:
        """Open pattern editor - TUI or text mode"""
        filename = params[0] if params else "untitled"
        mode = params[1].lower() if len(params) > 1 else "tui"

        # Check for TUI pattern editor
        if mode == "tui" or mode == "grid":
            return self._open_pattern_editor(filename, grid)

        # Ensure .mml extension for text mode
        if not filename.endswith(".mml"):
            filename += ".mml"

        # Create music directory if needed
        music_dir = Path("memory/music")
        music_dir.mkdir(parents=True, exist_ok=True)

        file_path = music_dir / filename

        # Load existing or create template
        if file_path.exists():
            content = file_path.read_text()
            logger.info(f"[LOCAL] Editing existing pattern: {file_path}")
        else:
            content = self._get_template_pattern()
            logger.info(f"[LOCAL] Creating new pattern: {file_path}")

        # Return editor launch instruction
        return f"""🎹 Pattern Editor: {filename}
─────────────────────────────
{content[:500]}{'...' if len(content) > 500 else ''}
─────────────────────────────
Commands:
  MUSIC PLAY {filename} - Preview
  MUSIC EXPORT {filename} out.mid - Export MIDI
  FILE EDIT {file_path} - Edit in text editor
  MUSIC EDIT {filename.replace('.mml','')} tui - Open grid editor"""

    def _open_pattern_editor(self, name: str, grid) -> str:
        """Open the TUI pattern editor"""
        try:
            from dev.goblin.core.ui.pattern_editor import (
                PatternEditor,
                PatternData,
                load_preset,
            )

            # Check if it's a preset
            presets = self.drum808.list_presets() if self.drum808 else []
            pattern = None

            if name.lower() in presets:
                # Load 808 preset as starting point
                preset = load_preset("four_on_floor")  # Default grid preset
                if preset:
                    preset.name = name
                    pattern = preset
            else:
                # Check for saved pattern
                pattern_path = Path("memory/sounds/presets") / f"{name}.json"
                if pattern_path.exists():
                    try:
                        import json

                        data = json.loads(pattern_path.read_text())
                        pattern = PatternData.from_dict(data)
                    except Exception:
                        pass

            # Create editor
            if pattern is None:
                pattern = PatternData(name=name)

            editor = PatternEditor(pattern)

            # Wire up playback callbacks
            editor.on_play = lambda p: self._handle_play([p.name], grid)
            editor.on_stop = lambda: self._handle_stop()

            # Render the grid
            lines = editor.render()
            output = "\n".join(lines)

            logger.info(f"[LOCAL] Pattern editor opened: {name}")
            return f"""{output}

💡 Interactive controls shown above
   Save: Press Ctrl+S or use MUSIC SAVE {name}
   Exit: Press Q or Esc"""

        except ImportError as e:
            logger.error(f"[LOCAL] Pattern editor not available: {e}")
            return f"❌ Pattern editor not available: {e}\n   Use MUSIC EDIT {name} text for MML editor"

    def _handle_export(self, params: List[str]) -> str:
        """Export pattern to MIDI"""
        if len(params) < 2:
            return "❌ Usage: MUSIC EXPORT <pattern.mml> <output.mid>"

        source = params[0]
        output = params[1]

        # Ensure extensions
        if not source.endswith(".mml"):
            source += ".mml"
        if not output.endswith(".mid"):
            output += ".mid"

        # Find source file
        source_path = Path("memory/music") / source
        if not source_path.exists():
            source_path = Path(source)

        if not source_path.exists():
            return f"❌ Pattern not found: {source}"

        # Parse and export
        try:
            mml_content = source_path.read_text()
            pattern = self.parser.parse(mml_content)

            self.exporter.clear()
            self.exporter.set_tempo(pattern.tempo)
            self.exporter.add_pattern(pattern)

            output_path = Path("memory/music") / output
            output_path.parent.mkdir(parents=True, exist_ok=True)

            midi_data = self.exporter.export()
            output_path.write_bytes(midi_data)

            logger.info(
                f"[LOCAL] Exported MIDI: {output_path} ({len(midi_data)} bytes)"
            )
            return f"✅ Exported: {output_path}\n   {len(pattern.notes)} notes, {len(midi_data)} bytes"

        except Exception as e:
            logger.error(f"[LOCAL] Export error: {e}")
            return f"❌ Export failed: {e}"

    def _handle_presets(self) -> str:
        """List available 808 presets"""
        presets = self.drum808.list_presets()

        lines = ["🥁 TR-808 Presets", "─" * 30]
        for name in presets:
            pattern = self.drum808.get_preset(name)
            note_count = len(pattern.notes)
            lines.append(f"  • {name:<15} ({note_count} hits)")

        lines.append("")
        lines.append("Play: MUSIC PLAY <preset_name>")

        return "\n".join(lines)

    def _handle_bpm(self, params: List[str]) -> str:
        """Set tempo"""
        if not params:
            return f"🎵 Current tempo: {self.current_tempo} BPM\n   Usage: MUSIC BPM <40-300>"

        try:
            tempo = int(params[0])
            if not 40 <= tempo <= 300:
                return "❌ BPM must be between 40 and 300"

            self.current_tempo = tempo
            self.sequencer.set_tempo(tempo)
            logger.info(f"[LOCAL] Tempo set to {tempo} BPM")
            return f"🎵 Tempo: {tempo} BPM"

        except ValueError:
            return "❌ Invalid tempo. Usage: MUSIC BPM <40-300>"

    def _handle_library(self, grid) -> str:
        """Browse sound library using SoundLibrary manager"""
        try:
            from wizard.extensions.groovebox.library import (
                get_sound_library,
                create_builtin_808_pack,
            )

            library = get_sound_library()

            # Ensure built-in pack exists
            create_builtin_808_pack(library)

            lines = ["📚 Sound Library", "═" * 40]

            # List installed packs
            packs = library.list_packs()
            if packs:
                lines.append("")
                lines.append("📦 Installed Packs:")
                for pack in packs:
                    status = "✓" if pack["valid"] else "⚠"
                    lines.append(
                        f"  {status} {pack['name']} v{pack['version']} "
                        f"({pack['instruments']} instruments)"
                    )
            else:
                lines.append("")
                lines.append("  (No packs installed)")

            # Built-in sounds
            lines.append("")
            lines.append("🥁 Built-in:")
            lines.append("  • TR-808 Drum Machine (6 presets)")

            # User samples
            user_samples = library.list_user_samples()
            if user_samples:
                lines.append("")
                lines.append(f"👤 User Samples ({len(user_samples)}):")
                for sample in user_samples[:5]:
                    lines.append(f"  • {sample['name']} ({sample['format']})")
                if len(user_samples) > 5:
                    lines.append(f"  ... and {len(user_samples) - 5} more")

            # Presets
            presets = library.list_presets()
            if presets:
                lines.append("")
                lines.append(f"💾 Saved Presets ({len(presets)}):")
                for preset in presets[:5]:
                    lines.append(f"  • {preset}")
                if len(presets) > 5:
                    lines.append(f"  ... and {len(presets) - 5} more")

            lines.append("")
            lines.append("─" * 40)
            lines.append("Commands:")
            lines.append("  MUSIC PRESETS     - List 808 presets")
            lines.append("  MUSIC EDIT <name> - Open pattern editor")

            return "\n".join(lines)

        except ImportError:
            # Fallback to simple listing
            return self._handle_library_fallback(grid)

    def _handle_library_fallback(self, grid) -> str:
        """Fallback library listing without SoundLibrary module"""
        packs_dir = Path("extensions/groovebox/packs")

        lines = ["📚 Sound Library", "─" * 30]

        if packs_dir.exists():
            packs = list(packs_dir.glob("*/manifest.json"))
            if packs:
                lines.append("Installed Packs:")
                for pack in packs:
                    manifest = json.loads(pack.read_text())
                    name = manifest.get("name", pack.parent.name)
                    sounds = manifest.get("sound_count", "?")
                    lines.append(f"  • {name} ({sounds} sounds)")
            else:
                lines.append("  (No packs installed)")
        else:
            lines.append("  (No packs installed)")

        lines.append("")
        lines.append("Built-in:")
        lines.append("  • TR-808 Drum Machine (6 presets)")
        lines.append("")
        lines.append("Install packs: PLUGIN SEARCH groovebox-packs")

        return "\n".join(lines)

    def _handle_new(self, params: List[str]) -> str:
        """Create new pattern file"""
        filename = params[0] if params else "pattern.mml"

        if not filename.endswith(".mml"):
            filename += ".mml"

        music_dir = Path("memory/music")
        music_dir.mkdir(parents=True, exist_ok=True)

        file_path = music_dir / filename

        if file_path.exists():
            return f"❌ File exists: {file_path}\n   Use MUSIC EDIT {filename} to edit"

        content = self._get_template_pattern()
        file_path.write_text(content)

        logger.info(f"[LOCAL] Created pattern: {file_path}")
        return f"✅ Created: {file_path}\n   Edit: MUSIC EDIT {filename}\n   Play: MUSIC PLAY {filename}"

    def _handle_808(self, params: List[str]) -> str:
        """Quick 808 pattern commands"""
        if not params:
            return self._handle_presets()

        preset = params[0].lower()
        return self._handle_play([preset], None)

    def _get_template_pattern(self) -> str:
        """Get template MML pattern"""
        return """; uDOS Groovebox Pattern
; MML (Music Macro Language) notation
; ===================================

; Set tempo and default length
t120 l8

; Track 1: Melody
; Notes: c d e f g a b (add + for sharp, - for flat)
; Octave: o4 (middle), > up, < down
; Length: 1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth
o4 c4 e8 g8 c+4 r4 < g2

; Track 2: Bass (lower octave)
o2 c4 c4 g4 g4

; Drums: Use channel 10 MIDI mapping
; c=kick, d=snare, f#=hi-hat, a#=clap

; Loop section: [pattern]4 repeats 4 times
[c4 r4 d4 r4]2

; Tips:
; - Use ; for comments
; - Use & for ties: c4&c8 (dotted quarter)
; - Use . for dotted notes: c4.
"""

    def _show_help(self) -> str:
        """Show help"""
        return """🎹 MUSIC Commands (Groovebox)
═══════════════════════════════════

PLAYBACK:
  MUSIC PLAY <pattern|preset>  Play pattern or 808 preset
  MUSIC STOP                   Stop playback
  MUSIC BPM <tempo>           Set tempo (40-300)

808 DRUM MACHINE:
  MUSIC PRESETS               List 808 presets
  MUSIC 808 <preset>          Quick play 808 preset

PATTERN EDITING:
  MUSIC EDIT <name>           Open TUI grid editor (16-step)
  MUSIC EDIT <name> text      Open MML text editor
  MUSIC NEW <name>            Create new MML pattern

EXPORT:
  MUSIC EXPORT <src> <dst>    Export to MIDI file

LIBRARY:
  MUSIC LIBRARY               Browse sound packs & presets

GRID EDITOR CONTROLS:
  ↑↓←→  Navigate grid       Space  Toggle step
  P     Play/Pause          S      Stop
  M     Mute track          +/-    Adjust BPM
  Q     Exit editor

MML SYNTAX:
  Notes: c d e f g a b r(rest)
  Sharps: c+ or c#  Flats: c-
  Octave: o4 (set) > (up) < (down)
  Length: l8 (default) or c4 d8 e16
  Tempo: t120
  Loop: [cde]4 (repeat 4x)
  
Example: MUSIC PLAY house_basic"""


# Standalone test
if __name__ == "__main__":
    handler = MusicHandler()
    print(handler._handle_presets())
