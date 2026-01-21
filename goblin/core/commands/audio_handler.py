"""
Audio Transport Command Handler
Alpha v1.1.0.3+

Handles audio-based data transfer using FSK modulation and Imperial sounds.
"""

from pathlib import Path
from typing import Optional, List
import wave
import struct

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("command-audio")


class AudioHandler:
    """
    Handler for audio transport commands.

    Commands:
    - AUDIO SEND <file> [output.wav] - Encode file to FSK audio
    - AUDIO RECEIVE <audio.wav> [output_file] - Decode FSK audio to file
    - AUDIO SAY <text> [output.wav] - Encode text to FSK audio
    - AUDIO PLAY <pattern> - Play Imperial sound pattern
    - AUDIO GROOVE <mml> [output.wav] - Render MML pattern to audio
    - AUDIO BOOT - Play boot sequence
    - AUDIO TEST - Run audio system test
    """

    def __init__(self):
        self.codec = None
        self.sounds = None
        self.groovebox = None
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if audio libraries are available"""
        try:
            from extensions.transport.audio import (
                AudioCodec,
                ImperialSounds,
                ImperialGroovebox,
            )

            self.codec = AudioCodec()
            self.sounds = ImperialSounds()
            self.groovebox = ImperialGroovebox()
            logger.info("[AUD] Audio transport libraries loaded")
        except ImportError as e:
            logger.warning(f"[AUD] Audio libraries not available: {e}")
            self.codec = None
            self.sounds = None
            self.groovebox = None

    def handle(self, command: str, params: List[str], grid, parser) -> Optional[str]:
        """
        Route AUDIO commands to appropriate handlers.

        Args:
            command: Command name (AUDIO)
            params: Command parameters [SEND|RECEIVE|SAY|PLAY|GROOVE|BOOT|TEST, ...]
            grid: Grid instance
            parser: Parser instance

        Returns:
            Success/error message or None
        """
        if not params:
            return self._show_help()

        subcommand = params[0].upper()

        if subcommand == "SEND":
            return self._handle_send(params[1:])
        elif subcommand == "RECEIVE":
            return self._handle_receive(params[1:])
        elif subcommand == "SAY":
            return self._handle_say(params[1:])
        elif subcommand == "PLAY":
            return self._handle_play(params[1:])
        elif subcommand == "GROOVE":
            return self._handle_groove(params[1:])
        elif subcommand == "BOOT":
            return self._handle_boot()
        elif subcommand == "TEST":
            return self._handle_test()
        elif subcommand == "TRANSMIT":
            return self._handle_transmit(params[1:])
        elif subcommand == "LISTEN":
            return self._handle_listen(params[1:])
        elif subcommand == "DEVICES":
            return self._handle_devices()
        elif subcommand == "HELP":
            return self._show_help()
        else:
            return f"❌ Unknown AUDIO command: {subcommand}\nUse 'AUDIO HELP' for usage"

    def _handle_send(self, params: List[str]) -> str:
        """
        Encode file to FSK audio.

        Usage: AUDIO SEND <file> [output.wav]
        """
        if not self.codec:
            return "❌ Audio codec not available"

        if not params:
            return "❌ Usage: AUDIO SEND <file> [output.wav]"

        # Get file path
        file_path = Path(params[0])

        # Resolve relative to memory/sandbox if not absolute
        if not file_path.is_absolute():
            file_path = Path.home() / ".udos" / "memory" / "sandbox" / file_path

        if not file_path.exists():
            return f"❌ File not found: {file_path}"

        # Get output file
        if len(params) > 1:
            output_file = Path(params[1])
        else:
            output_dir = Path.home() / ".udos" / "memory" / ".tmp" / "audio-send"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{file_path.stem}_fsk.wav"

        try:
            # Read file
            logger.info(f"[AUD-ENC] Reading file: {file_path}")
            file_data = file_path.read_bytes()

            # Encode to FSK audio
            audio_data = self.codec.encode(file_data)

            # Get config from encoder
            config = self.codec.encoder.config

            # Calculate duration
            duration_sec = len(audio_data) / config.sample_rate

            # Save WAV
            output_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_wav(audio_data, output_file)

            logger.info(
                f"[AUD-ENC] Created FSK audio: {output_file} ({duration_sec:.2f}s)"
            )

            return (
                f"✅ Encoded {file_path.name} ({len(file_data)} bytes) to FSK audio\n"
                f"📁 Saved to: {output_file}\n"
                f"🎵 Duration: {duration_sec:.2f} seconds\n"
                f"📡 Baud: {config.bit_rate} bps\n"
                f"🔊 Frequencies: {config.mark_freq}Hz (mark) / {config.space_freq}Hz (space)\n\n"
                f"💡 Play this audio near another uDOS device running 'AUDIO RECEIVE'"
            )

        except Exception as e:
            logger.error(f"[AUD-ENC] Failed to encode file: {e}", exc_info=True)
            return f"❌ Failed to encode file: {e}"

    def _handle_receive(self, params: List[str]) -> str:
        """
        Decode FSK audio to file.

        Usage: AUDIO RECEIVE <audio.wav> [output_file]
        """
        if not self.codec:
            return "❌ Audio codec not available"

        if not params:
            return "❌ Usage: AUDIO RECEIVE <audio.wav> [output_file]"

        # Get audio file path
        audio_path = Path(params[0])
        if not audio_path.is_absolute():
            audio_path = Path.home() / ".udos" / "memory" / audio_path

        if not audio_path.exists():
            return f"❌ Audio file not found: {audio_path}"

        # Get output file
        if len(params) > 1:
            output_file = Path(params[1])
        else:
            output_file = (
                Path.home()
                / ".udos"
                / "memory"
                / "sandbox"
                / f"received_{audio_path.stem}.dat"
            )

        try:
            # Read WAV file
            logger.info(f"[AUD-DEC] Reading audio: {audio_path}")
            audio_data = self._read_wav(audio_path)

            # Decode FSK
            decoded_data = self.codec.decode(audio_data)

            if not decoded_data:
                return (
                    f"❌ Failed to decode FSK audio\n"
                    f"Possible issues:\n"
                    f"  - Audio quality too low\n"
                    f"  - Wrong encoding format\n"
                    f"  - CRC checksum failed"
                )

            # Save decoded file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(decoded_data)

            logger.info(f"[AUD-DEC] Saved {len(decoded_data)} bytes to {output_file}")

            return (
                f"✅ Successfully decoded FSK audio\n"
                f"📁 File: {output_file.name} ({len(decoded_data)} bytes)\n"
                f"💾 Saved to: {output_file}\n"
                f"🎵 Source: {audio_path.name}"
            )

        except Exception as e:
            logger.error(f"[AUD-DEC] Failed to decode audio: {e}", exc_info=True)
            return f"❌ Failed to decode audio: {e}"

    def _handle_say(self, params: List[str]) -> str:
        """
        Encode text to FSK audio.

        Usage: AUDIO SAY <text> [output.wav]
        """
        if not self.codec:
            return "❌ Audio codec not available"

        if not params:
            return "❌ Usage: AUDIO SAY <text> [output.wav]"

        # Get text and optional output file
        if len(params) > 1 and params[-1].endswith(".wav"):
            text = " ".join(params[:-1])
            output_file = Path(params[-1])
        else:
            text = " ".join(params)
            output_dir = Path.home() / ".udos" / "memory" / ".tmp" / "audio-say"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "message_fsk.wav"

        try:
            # Encode text to bytes
            text_bytes = text.encode("utf-8")

            # Encode to FSK audio
            audio_data = self.codec.encode(text_bytes)
            config = self.codec.encoder.config
            duration_sec = len(audio_data) / config.sample_rate

            # Save WAV
            output_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_wav(audio_data, output_file)

            logger.info(f"[AUD] Encoded text ({len(text)} chars) to FSK audio")

            return (
                f"✅ Encoded message to FSK audio\n"
                f"📝 Text: {text[:50]}{'...' if len(text) > 50 else ''}\n"
                f"📁 Saved to: {output_file}\n"
                f"🎵 Duration: {duration_sec:.2f} seconds\n\n"
                f"💡 Play this audio near another uDOS device to receive"
            )

        except Exception as e:
            logger.error(f"[AUD] Failed to encode text: {e}", exc_info=True)
            return f"❌ Failed to encode text: {e}"

    def _handle_play(self, params: List[str]) -> str:
        """
        Play Imperial sound pattern.

        Usage: AUDIO PLAY <pattern>
        Patterns: BOOT, BREATH, HANDSHAKE, DATA, SUCCESS, ERROR, DISCONNECT
        """
        if not self.groovebox:
            return "❌ Groovebox not available"

        if not params:
            return (
                "❌ Usage: AUDIO PLAY <pattern>\n"
                "Patterns: BOOT, BREATH, HANDSHAKE, DATA, SUCCESS, ERROR, DISCONNECT"
            )

        pattern_name = params[0].upper()

        # Map pattern names to groovebox methods
        pattern_map = {
            "BOOT": ("boot_sequence", "🚀 Imperial Boot Sequence"),
            "BREATH": ("vader_breath", "😤 Vader Breathing"),
            "HANDSHAKE": ("handshake", "🤝 Handshake Signal"),
            "DATA": ("data_stream", "📊 Data Transfer"),
            "SUCCESS": ("success", "✅ Success Fanfare"),
            "ERROR": ("error", "❌ Error Alert"),
            "DISCONNECT": ("disconnect", "🔌 Disconnect"),
        }

        if pattern_name not in pattern_map:
            available = ", ".join(pattern_map.keys())
            return f"❌ Unknown pattern: {pattern_name}\nAvailable: {available}"

        method_name, description = pattern_map[pattern_name]

        try:
            # Get audio from groovebox
            method = getattr(self.groovebox, method_name)
            audio_data = method()

            # Save to temp file
            output_dir = Path.home() / ".udos" / "memory" / ".tmp" / "audio-play"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"imperial_{pattern_name.lower()}.wav"

            self._save_wav(audio_data, output_file)

            duration_sec = len(audio_data) / 44100  # Default sample rate

            logger.info(f"[AUD] Generated Imperial pattern: {pattern_name}")

            return (
                f"🎵 {description}\n"
                f"📁 Saved to: {output_file}\n"
                f"🎵 Duration: {duration_sec:.2f} seconds\n\n"
                f"💡 Use system audio player to play the WAV file"
            )

        except Exception as e:
            logger.error(f"[AUD] Failed to play pattern: {e}", exc_info=True)
            return f"❌ Failed to play pattern: {e}"

    def _handle_groove(self, params: List[str]) -> str:
        """
        Render MML pattern to audio.

        Usage: AUDIO GROOVE <mml_pattern> [output.wav]
        Example: AUDIO GROOVE "t120 l8 o4 c d e f g a b o5 c"
        """
        if not self.groovebox:
            return "❌ Groovebox not available"

        if not params:
            return (
                "❌ Usage: AUDIO GROOVE <mml_pattern> [output.wav]\n"
                'Example: AUDIO GROOVE "t120 l8 o4 c d e f g a b o5 c"'
            )

        # Get MML and optional output file
        if len(params) > 1 and params[-1].endswith(".wav"):
            mml = " ".join(params[:-1])
            output_file = Path(params[-1])
        else:
            mml = " ".join(params)
            output_dir = Path.home() / ".udos" / "memory" / ".tmp" / "audio-groove"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "groove_output.wav"

        try:
            from extensions.transport.audio import SoundBank

            # Parse and render MML
            audio_data = self.groovebox.render_mml(mml, SoundBank.FM_LEAD)

            # Save WAV
            output_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_wav(audio_data, output_file)

            duration_sec = len(audio_data) / 44100

            logger.info(f"[AUD] Rendered MML pattern ({len(mml)} chars)")

            return (
                f"✅ Rendered MML pattern\n"
                f"🎵 MML: {mml[:50]}{'...' if len(mml) > 50 else ''}\n"
                f"📁 Saved to: {output_file}\n"
                f"🎵 Duration: {duration_sec:.2f} seconds"
            )

        except Exception as e:
            logger.error(f"[AUD] Failed to render MML: {e}", exc_info=True)
            return f"❌ Failed to render MML: {e}"

    def _handle_boot(self) -> str:
        """
        Play boot sequence.

        Usage: AUDIO BOOT
        """
        return self._handle_play(["BOOT"])

    def _handle_test(self) -> str:
        """
        Run audio system test.

        Usage: AUDIO TEST
        """
        results = []
        results.append("🔊 Audio System Test\n")

        # Check codec
        if self.codec:
            config = self.codec.encoder.config
            results.append(
                f"✅ FSK Codec: Ready\n"
                f"   - Sample Rate: {config.sample_rate} Hz\n"
                f"   - Baud Rate: {config.bit_rate} bps\n"
                f"   - Mark Freq: {config.mark_freq} Hz\n"
                f"   - Space Freq: {config.space_freq} Hz"
            )
        else:
            results.append("❌ FSK Codec: Not available")

        # Check sounds
        if self.sounds:
            results.append("\n✅ Imperial Sounds: Ready")
            results.append(f"   - Boot Sequence: Available")
            results.append(f"   - Vader Breathing: Available")
        else:
            results.append("\n❌ Imperial Sounds: Not available")

        # Check groovebox
        if self.groovebox:
            results.append("\n✅ Imperial Groovebox: Ready")
            results.append(f"   - Sound Banks: 6 available")
            results.append(f"   - Patterns: 10 predefined")
        else:
            results.append("\n❌ Imperial Groovebox: Not available")

        # Run quick round-trip test
        if self.codec:
            try:
                test_data = b"uDOS Audio Test"
                encoded = self.codec.encode(test_data)
                decoded = self.codec.decode(encoded)

                if decoded == test_data:
                    results.append("\n✅ FSK Round-trip: PASSED")
                else:
                    results.append("\n❌ FSK Round-trip: FAILED (data mismatch)")
            except Exception as e:
                results.append(f"\n❌ FSK Round-trip: FAILED ({e})")

        # Check real-time I/O
        try:
            from extensions.transport.audio import AudioTransmitter, AudioReceiver

            tx = AudioTransmitter()
            rx = AudioReceiver()

            if tx.is_available() and rx.is_available():
                results.append("\n✅ Real-time Audio I/O: Ready (pyaudio)")

                # List devices
                output_devs = tx.get_devices()
                input_devs = rx.get_devices()
                results.append(f"   - Output devices: {len(output_devs)}")
                results.append(f"   - Input devices: {len(input_devs)}")
            else:
                results.append("\n⚠️ Real-time Audio I/O: pyaudio not installed")
                results.append("   Install: pip install pyaudio")
                results.append("   macOS: brew install portaudio")
        except ImportError:
            results.append("\n⚠️ Real-time Audio I/O: Not available")

        return "\n".join(results)

    def _handle_transmit(self, params: List[str]) -> str:
        """
        Transmit data through speaker in real-time.

        Usage: AUDIO TRANSMIT <file|text>
        """
        try:
            from extensions.transport.audio import AudioTransmitter
        except ImportError:
            return "❌ Audio transmitter not available"

        tx = AudioTransmitter()
        if not tx.is_available():
            return (
                "❌ pyaudio not installed\n"
                "Install: pip install pyaudio\n"
                "macOS: brew install portaudio"
            )

        if not params:
            return "❌ Usage: AUDIO TRANSMIT <file|text>"

        # Check if it's a file or text
        input_str = " ".join(params)
        file_path = Path(input_str)

        if not file_path.is_absolute():
            potential_file = Path.home() / ".udos" / "memory" / "sandbox" / input_str
            if potential_file.exists():
                file_path = potential_file

        if file_path.exists() and file_path.is_file():
            # Transmit file
            data = file_path.read_bytes()
            data_type = f"file ({file_path.name})"
        else:
            # Transmit as text
            data = input_str.encode("utf-8")
            data_type = "text message"

        logger.info(f"[AUD] Transmitting {data_type}: {len(data)} bytes")

        # Show progress in real-time
        progress_msg = [""]

        def progress_cb(pct, state):
            progress_msg[0] = f"Progress: {pct}%"

        success = tx.transmit_data(data, progress_cb)

        if success:
            return (
                f"✅ Transmitted {data_type}\n"
                f"📊 Size: {len(data)} bytes\n"
                f"🔊 Output: Speaker\n\n"
                f"💡 Receiver should run: AUDIO LISTEN"
            )
        else:
            return f"❌ Transmission failed"

    def _handle_listen(self, params: List[str]) -> str:
        """
        Listen for FSK signal through microphone.

        Usage: AUDIO LISTEN [timeout_seconds] [output_file]
        """
        try:
            from extensions.transport.audio import AudioReceiver
        except ImportError:
            return "❌ Audio receiver not available"

        rx = AudioReceiver()
        if not rx.is_available():
            return (
                "❌ pyaudio not installed\n"
                "Install: pip install pyaudio\n"
                "macOS: brew install portaudio"
            )

        # Parse parameters
        timeout = 30.0
        output_file = None

        for param in params:
            if param.replace(".", "").isdigit():
                timeout = float(param)
            elif "." in param or "/" in param:
                output_file = Path(param)

        if output_file and not output_file.is_absolute():
            output_file = Path.home() / ".udos" / "memory" / "sandbox" / output_file

        logger.info(f"[AUD] Listening for FSK signal (timeout: {timeout}s)")

        # Status updates
        status_msg = ["Waiting for signal..."]

        def status_cb(state, msg):
            status_msg[0] = msg

        # Listen and decode
        decoded = rx.listen_and_decode(
            timeout_seconds=timeout, status_callback=status_cb
        )

        if decoded:
            # Save if output file specified
            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(decoded)
                save_msg = f"💾 Saved to: {output_file}"
            else:
                save_msg = ""

            # Try to decode as text
            try:
                text = decoded.decode("utf-8")
                content_msg = (
                    f"📝 Content: {text[:100]}{'...' if len(text) > 100 else ''}"
                )
            except:
                content_msg = f"📊 Binary data: {len(decoded)} bytes"

            return (
                f"✅ Received FSK transmission\n"
                f"📊 Size: {len(decoded)} bytes\n"
                f"{content_msg}\n"
                f"{save_msg}"
            ).strip()
        else:
            return (
                f"⏱️ No signal received (timeout: {timeout}s)\n"
                f"Status: {status_msg[0]}\n\n"
                f"💡 Make sure transmitter is running: AUDIO TRANSMIT <data>"
            )

    def _handle_devices(self) -> str:
        """
        List available audio devices.

        Usage: AUDIO DEVICES
        """
        try:
            from extensions.transport.audio import AudioTransmitter, AudioReceiver
        except ImportError:
            return "❌ Audio I/O not available"

        tx = AudioTransmitter()
        rx = AudioReceiver()

        if not tx.is_available():
            return (
                "❌ pyaudio not installed\n"
                "Install: pip install pyaudio\n"
                "macOS: brew install portaudio"
            )

        results = ["🔊 Audio Devices\n"]

        # Output devices
        results.append("OUTPUT (Speakers):")
        output_devs = tx.get_devices()
        if output_devs:
            for dev in output_devs:
                results.append(f"  [{dev['index']}] {dev['name']}")
        else:
            results.append("  (none found)")

        # Input devices
        results.append("\nINPUT (Microphones):")
        input_devs = rx.get_devices()
        if input_devs:
            for dev in input_devs:
                results.append(f"  [{dev['index']}] {dev['name']}")
        else:
            results.append("  (none found)")

        return "\n".join(results)

    def _save_wav(self, audio_data: List[float], output_path: Path):
        """Save audio data to WAV file"""
        sample_rate = 44100

        with wave.open(str(output_path), "w") as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)

            # Convert float samples to 16-bit integers
            samples = [int(s * 32767) for s in audio_data]
            frames = struct.pack(f"<{len(samples)}h", *samples)
            wav.writeframes(frames)

    def _read_wav(self, audio_path: Path) -> List[float]:
        """Read WAV file to audio data"""
        with wave.open(str(audio_path), "r") as wav:
            n_frames = wav.getnframes()
            frames = wav.readframes(n_frames)

            # Convert to float samples
            samples = struct.unpack(f"<{n_frames}h", frames)
            return [s / 32767 for s in samples]

    def _show_help(self) -> str:
        """Show AUDIO command help"""
        return """
🔊 Audio Transport Commands

FSK-based data transfer and Imperial sound patterns for offline communication.

FILE ENCODING/DECODING:
  AUDIO SEND <file> [output.wav]
    Encode file to FSK audio WAV file
    Example: AUDIO SEND README.MD
    
  AUDIO RECEIVE <audio.wav> [output_file]
    Decode FSK audio WAV to file
    Example: AUDIO RECEIVE transfer.wav
    
  AUDIO SAY <text> [output.wav]
    Encode text message to FSK audio WAV
    Example: AUDIO SAY "Hello from uDOS"

REAL-TIME TRANSFER (requires pyaudio):
  AUDIO TRANSMIT <file|text>
    Transmit data through speaker in real-time
    Example: AUDIO TRANSMIT secret.txt
    Example: AUDIO TRANSMIT "Hello mesh!"
    
  AUDIO LISTEN [timeout] [output_file]
    Listen for FSK signal through microphone
    Example: AUDIO LISTEN 30 received.dat
    Example: AUDIO LISTEN (30 second default)
    
  AUDIO DEVICES
    List available audio input/output devices

IMPERIAL SOUNDS:
  AUDIO PLAY <pattern>
    Play Imperial sound pattern
    Patterns: BOOT, BREATH, HANDSHAKE, DATA, SUCCESS, ERROR, DISCONNECT
    Example: AUDIO PLAY BOOT
    
  AUDIO GROOVE <mml> [output.wav]
    Render MML (Music Macro Language) pattern
    Example: AUDIO GROOVE "t120 o4 c d e f g"
    
  AUDIO BOOT
    Shortcut for AUDIO PLAY BOOT
    
DIAGNOSTICS:
  AUDIO TEST
    Run audio system diagnostics
    
  AUDIO HELP
    Show this help message

FSK ENCODING:
  Baud Rate: 100 bps (Bell 202 compatible)
  Mark Freq: 1200 Hz (logic 1)
  Space Freq: 2200 Hz (logic 0)
  Sample Rate: 44100 Hz
  Validation: CRC-16 checksum

TRANSPORT POLICY:
  Realm: PRIVATE_SAFE
  Range: Acoustic (room-level)
  Data: Allowed (with preamble sync)
  Commands: Allowed (handshake, data transfer)

DEPENDENCIES:
  Real-time I/O requires pyaudio:
    pip install pyaudio
    macOS: brew install portaudio
    Linux: sudo apt-get install python3-pyaudio

📚 See: extensions/transport/audio/README.md
"""
