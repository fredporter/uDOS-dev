"""
Voice Command Handler
Alpha v1.0.3.0+

TUI integration for voice libraries (Piper TTS, Handy STT).

Commands:
- VOICE SAY <text> - Speak text using Piper TTS
- VOICE LISTEN [-t seconds] - Listen and transcribe using Handy STT
- VOICE TRANSCRIBE <file.wav> - Transcribe audio file
- VOICE MODEL <name> - Set TTS or STT model
- VOICE MODELS - List available models
- VOICE DOWNLOAD <model> - Download a voice model
- VOICE STATUS - Show voice engine status
- VOICE HELP - Show help
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import subprocess
import tempfile

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("command-voice")


class VoiceHandler:
    """
    Handler for VOICE commands.

    Integrates Piper TTS and Handy STT with uDOS TUI for voice interaction.
    """

    def __init__(self):
        self.piper_available = False
        self.handy_available = False
        self.tts_model = None
        self.stt_model = None
        self.library_path = Path("library/wizard")
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if voice libraries are available"""
        # Check Piper TTS
        piper_path = self.library_path / "piper"
        if piper_path.exists() and (piper_path / "container.json").exists():
            self.piper_available = True
            logger.info("[LOCAL] Piper TTS container available")
        else:
            logger.info("[LOCAL] Piper TTS not installed")

        # Check Handy STT
        handy_path = self.library_path / "handy"
        if handy_path.exists() and (handy_path / "container.json").exists():
            self.handy_available = True
            logger.info("[LOCAL] Handy STT container available")
        else:
            logger.info("[LOCAL] Handy STT not installed")

        # Load default models if configured
        self._load_default_models()

    def _load_default_models(self):
        """Load default voice models from config"""
        try:
            config_path = Path("core/config/voice.json")
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                    self.tts_model = config.get(
                        "default_tts_model", "en_US-lessac-medium"
                    )
                    self.stt_model = config.get("default_stt_model", "parakeet-v3")
            else:
                # Sensible defaults
                self.tts_model = "en_US-lessac-medium"
                self.stt_model = "parakeet-v3"
        except Exception as e:
            logger.warning(f"[LOCAL] Could not load voice config: {e}")
            self.tts_model = "en_US-lessac-medium"
            self.stt_model = "parakeet-v3"

    def handle(self, command: str, params: List[str], grid, parser) -> Optional[str]:
        """
        Route VOICE commands to appropriate handlers.

        Args:
            command: Command name (VOICE)
            params: Command parameters
            grid: Grid instance for display
            parser: Parser instance

        Returns:
            Success/error message or None
        """
        if not params:
            return self._show_help()

        subcommand = params[0].upper()
        args = params[1:] if len(params) > 1 else []

        handlers = {
            "SAY": self._handle_say,
            "SPEAK": self._handle_say,
            "LISTEN": self._handle_listen,
            "RECORD": self._handle_listen,
            "TRANSCRIBE": self._handle_transcribe,
            "MODEL": self._handle_model,
            "MODELS": self._handle_list_models,
            "VOICES": self._handle_list_models,
            "DOWNLOAD": self._handle_download,
            "STATUS": self._handle_status,
            "HELP": lambda a, g: self._show_help(),
        }

        if subcommand in handlers:
            return handlers[subcommand](args, grid)
        else:
            # Treat as text to speak: VOICE Hello world
            text = " ".join(params)
            return self._handle_say([text], grid)

    # ========================================
    # Text-to-Speech (Piper)
    # ========================================

    def _handle_say(self, args: List[str], grid) -> str:
        """
        Speak text using Piper TTS.

        Usage:
            VOICE SAY Hello world
            VOICE SAY -f message.txt
            VOICE SAY -v en_GB-alba-medium "Hello"
        """
        if not self.piper_available:
            return self._piper_not_installed()

        if not args:
            return "❌ No text to speak\n   Usage: VOICE SAY <text>"

        # Parse options
        voice = self.tts_model
        text = None
        file_input = False

        i = 0
        while i < len(args):
            if args[i] == "-v" and i + 1 < len(args):
                voice = args[i + 1]
                i += 2
            elif args[i] == "-f" and i + 1 < len(args):
                file_input = True
                filepath = Path(args[i + 1])
                if not filepath.exists():
                    return f"❌ File not found: {filepath}"
                text = filepath.read_text()
                i += 2
            else:
                # Rest is text
                text = " ".join(args[i:])
                break

        if not text:
            return "❌ No text to speak"

        # Check if model is available
        model_path = self._get_tts_model_path(voice)
        if not model_path:
            return f"❌ TTS model not found: {voice}\n   Run: VOICE DOWNLOAD {voice}"

        logger.info(f"[LOCAL] TTS: Speaking {len(text)} chars with {voice}")

        # Generate speech (placeholder - actual implementation requires piper binary)
        try:
            result = self._synthesize_speech(text, voice)
            return f"🔊 Speaking: \"{text[:50]}{'...' if len(text) > 50 else ''}\"\n   Voice: {voice}"
        except Exception as e:
            logger.error(f"[LOCAL] TTS error: {e}")
            return f"❌ TTS error: {e}"

    def _synthesize_speech(self, text: str, voice: str) -> bool:
        """
        Synthesize speech using Piper.

        Returns True if successful, raises exception on error.
        """
        # TODO: Implement actual Piper synthesis
        # This requires:
        # 1. Piper binary (piper or piper.exe)
        # 2. Voice model (.onnx + .onnx.json)
        # 3. Audio output (direct playback or file)

        # For now, log the request
        logger.info(f"[LOCAL] Would synthesize: {text[:100]}")

        # Check for piper binary
        piper_bin = self._find_piper_binary()
        if piper_bin:
            # Real synthesis would go here
            # subprocess.run([piper_bin, "--model", model_path, "--output-raw", ...])
            pass

        return True

    def _find_piper_binary(self) -> Optional[Path]:
        """Find Piper binary in expected locations"""
        search_paths = [
            self.library_path / "piper" / "repo" / "piper",
            self.library_path / "piper" / "piper",
            Path("/opt/udos/bin/piper"),
            Path("~/.udos/bin/piper").expanduser(),
        ]

        for path in search_paths:
            if path.exists():
                return path

        return None

    def _get_tts_model_path(self, voice: str) -> Optional[Path]:
        """Get path to TTS voice model"""
        models_dir = self.library_path / "piper" / "models"
        if not models_dir.exists():
            return None

        # Check for .onnx file
        model_file = models_dir / f"{voice}.onnx"
        if model_file.exists():
            return model_file

        # Check subdirectory
        model_dir = models_dir / voice
        if model_dir.exists():
            for f in model_dir.glob("*.onnx"):
                return f

        return None

    # ========================================
    # Speech-to-Text (Handy/Whisper)
    # ========================================

    def _handle_listen(self, args: List[str], grid) -> str:
        """
        Listen and transcribe using Handy STT.

        Usage:
            VOICE LISTEN              # Listen until silence
            VOICE LISTEN -t 30        # Listen for 30 seconds
            VOICE LISTEN > file.txt   # Save to file
        """
        if not self.handy_available:
            return self._handy_not_installed()

        # Parse options
        timeout = 10  # Default 10 seconds
        output_file = None

        i = 0
        while i < len(args):
            if args[i] == "-t" and i + 1 < len(args):
                try:
                    timeout = int(args[i + 1])
                except ValueError:
                    return f"❌ Invalid timeout: {args[i + 1]}"
                i += 2
            elif args[i] == ">" and i + 1 < len(args):
                output_file = Path(args[i + 1])
                i += 2
            else:
                i += 1

        logger.info(f"[LOCAL] STT: Listening for {timeout}s with {self.stt_model}")

        try:
            # Start listening (placeholder)
            grid.show_status("🎤 Listening...")
            transcription = self._record_and_transcribe(timeout)

            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(transcription)
                return f"🎤 Transcription saved to: {output_file}\n   \"{transcription[:100]}{'...' if len(transcription) > 100 else ''}\""
            else:
                return f'🎤 Heard: "{transcription}"'
        except Exception as e:
            logger.error(f"[LOCAL] STT error: {e}")
            return f"❌ STT error: {e}"

    def _record_and_transcribe(self, timeout: int) -> str:
        """
        Record audio and transcribe using Whisper/Parakeet.

        Returns transcription text.
        """
        # TODO: Implement actual recording and transcription
        # This requires:
        # 1. Audio recording (pyaudio, sounddevice, or similar)
        # 2. Whisper/Parakeet model
        # 3. VAD for silence detection

        logger.info(f"[LOCAL] Would record for {timeout}s and transcribe")

        # Placeholder response
        return "[Transcription would appear here - STT engine not fully integrated]"

    def _handle_transcribe(self, args: List[str], grid) -> str:
        """
        Transcribe an audio file.

        Usage:
            VOICE TRANSCRIBE recording.wav
            VOICE TRANSCRIBE meeting.mp3 > transcript.txt
        """
        if not self.handy_available:
            return self._handy_not_installed()

        if not args:
            return "❌ No audio file specified\n   Usage: VOICE TRANSCRIBE <file.wav>"

        audio_file = Path(args[0])
        if not audio_file.exists():
            return f"❌ File not found: {audio_file}"

        # Check for output redirect
        output_file = None
        if len(args) >= 3 and args[1] == ">":
            output_file = Path(args[2])

        logger.info(f"[LOCAL] STT: Transcribing {audio_file}")

        try:
            transcription = self._transcribe_file(audio_file)

            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(transcription)
                return f"📝 Transcription saved to: {output_file}"
            else:
                return f"📝 Transcription:\n{transcription}"
        except Exception as e:
            logger.error(f"[LOCAL] Transcription error: {e}")
            return f"❌ Transcription error: {e}"

    def _transcribe_file(self, audio_file: Path) -> str:
        """Transcribe an audio file"""
        # TODO: Implement actual transcription
        logger.info(f"[LOCAL] Would transcribe: {audio_file}")
        return f"[Transcription of {audio_file.name} would appear here]"

    # ========================================
    # Model Management
    # ========================================

    def _handle_model(self, args: List[str], grid) -> str:
        """
        Set TTS or STT model.

        Usage:
            VOICE MODEL en_US-lessac-medium      # Set TTS model
            VOICE MODEL --tts en_US-amy-low      # Explicit TTS
            VOICE MODEL --stt parakeet-v3        # Set STT model
        """
        if not args:
            return f"📊 Current Models:\n   TTS: {self.tts_model}\n   STT: {self.stt_model}"

        model_type = None
        model_name = None

        if args[0] == "--tts" and len(args) > 1:
            model_type = "tts"
            model_name = args[1]
        elif args[0] == "--stt" and len(args) > 1:
            model_type = "stt"
            model_name = args[1]
        else:
            # Auto-detect based on model name pattern
            model_name = args[0]
            if model_name.startswith(
                (
                    "en_",
                    "de_",
                    "fr_",
                    "es_",
                    "it_",
                    "pt_",
                    "pl_",
                    "nl_",
                    "ru_",
                    "zh_",
                    "ja_",
                )
            ):
                model_type = "tts"  # Piper voice pattern
            elif model_name.startswith(("whisper", "parakeet", "ggml")):
                model_type = "stt"  # Handy model pattern
            else:
                return f"❌ Unknown model: {model_name}\n   Specify --tts or --stt"

        if model_type == "tts":
            self.tts_model = model_name
            return f"✅ TTS model set to: {model_name}"
        else:
            self.stt_model = model_name
            return f"✅ STT model set to: {model_name}"

    def _handle_list_models(self, args: List[str], grid) -> str:
        """List available voice models"""
        lines = ["📦 Voice Models:", ""]

        # TTS Models (Piper)
        lines.append("🔊 TTS (Piper):")
        tts_models = self._list_tts_models()
        if tts_models:
            for model in tts_models:
                marker = "→" if model == self.tts_model else " "
                lines.append(f"   {marker} {model}")
        else:
            lines.append("   No models installed")
            lines.append("   Run: VOICE DOWNLOAD en_US-lessac-medium")

        lines.append("")

        # STT Models (Handy)
        lines.append("🎤 STT (Handy/Whisper):")
        stt_models = self._list_stt_models()
        if stt_models:
            for model in stt_models:
                marker = "→" if model == self.stt_model else " "
                lines.append(f"   {marker} {model}")
        else:
            lines.append("   No models installed")
            lines.append("   Run: VOICE DOWNLOAD parakeet-v3")

        lines.append("")
        lines.append("Available for download:")
        lines.append("   TTS: en_US-lessac-medium, en_GB-alba-medium")
        lines.append("   STT: parakeet-v3, whisper-small, whisper-large")

        return "\n".join(lines)

    def _list_tts_models(self) -> List[str]:
        """List installed TTS models"""
        models = []
        models_dir = self.library_path / "piper" / "models"

        if models_dir.exists():
            for item in models_dir.iterdir():
                if item.suffix == ".onnx":
                    models.append(item.stem)
                elif item.is_dir():
                    models.append(item.name)

        return sorted(models)

    def _list_stt_models(self) -> List[str]:
        """List installed STT models"""
        models = []
        models_dir = self.library_path / "handy" / "models"

        if models_dir.exists():
            for item in models_dir.iterdir():
                if item.suffix == ".bin":
                    # Whisper models
                    name = item.stem
                    if name.startswith("ggml-"):
                        name = name.replace("ggml-", "whisper-")
                    models.append(name)
                elif item.is_dir() and "parakeet" in item.name:
                    # Parakeet models
                    models.append(
                        item.name.replace("-int8", "").replace(
                            "parakeet-tdt-0.6b-", "parakeet-"
                        )
                    )

        return sorted(models)

    def _handle_download(self, args: List[str], grid) -> str:
        """
        Download a voice model.

        Usage:
            VOICE DOWNLOAD en_US-lessac-medium   # TTS model
            VOICE DOWNLOAD parakeet-v3           # STT model
            VOICE DOWNLOAD whisper-small         # STT model
        """
        if not args:
            return "❌ No model specified\n   Usage: VOICE DOWNLOAD <model-name>"

        model_name = args[0]

        # Determine model type and URL
        model_info = self._get_model_download_info(model_name)
        if not model_info:
            return f"❌ Unknown model: {model_name}\n   Run: VOICE MODELS for available models"

        logger.info(f"[WIZ] Downloading model: {model_name}")

        # Download would happen here (requires Wizard Server for web access)
        return f"⬇️  Model download requested: {model_name}\n   This requires Wizard Server for web access\n   URL: {model_info.get('url', 'N/A')}"

    def _get_model_download_info(self, model_name: str) -> Optional[Dict]:
        """Get download info for a model"""
        # TTS models (Piper)
        tts_models = {
            "en_US-lessac-medium": {
                "type": "tts",
                "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
                "size": "60MB",
            },
            "en_GB-alba-medium": {
                "type": "tts",
                "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx",
                "size": "60MB",
            },
        }

        # STT models (Handy)
        stt_models = {
            "parakeet-v3": {
                "type": "stt",
                "url": "https://blob.handy.computer/parakeet-v3-int8.tar.gz",
                "size": "478MB",
            },
            "parakeet-v2": {
                "type": "stt",
                "url": "https://blob.handy.computer/parakeet-v2-int8.tar.gz",
                "size": "473MB",
            },
            "whisper-small": {
                "type": "stt",
                "url": "https://blob.handy.computer/ggml-small.bin",
                "size": "487MB",
            },
            "whisper-medium": {
                "type": "stt",
                "url": "https://blob.handy.computer/whisper-medium-q4_1.bin",
                "size": "492MB",
            },
            "whisper-large": {
                "type": "stt",
                "url": "https://blob.handy.computer/ggml-large-v3-q5_0.bin",
                "size": "1100MB",
            },
        }

        return tts_models.get(model_name) or stt_models.get(model_name)

    # ========================================
    # Status & Help
    # ========================================

    def _handle_status(self, args: List[str], grid) -> str:
        """Show voice engine status"""
        lines = ["🎤 Voice System Status", ""]

        # Piper TTS
        if self.piper_available:
            piper_bin = self._find_piper_binary()
            lines.append(f"✅ Piper TTS: Available")
            lines.append(f"   Binary: {'Found' if piper_bin else 'Not found'}")
            lines.append(f"   Model: {self.tts_model}")
            tts_models = self._list_tts_models()
            lines.append(f"   Installed: {len(tts_models)} model(s)")
        else:
            lines.append("❌ Piper TTS: Not installed")
            lines.append("   Run: WIZARD CLONE piper")

        lines.append("")

        # Handy STT
        if self.handy_available:
            lines.append(f"✅ Handy STT: Available")
            lines.append(f"   Model: {self.stt_model}")
            stt_models = self._list_stt_models()
            lines.append(f"   Installed: {len(stt_models)} model(s)")
        else:
            lines.append("❌ Handy STT: Not installed")
            lines.append("   Run: WIZARD CLONE handy")

        return "\n".join(lines)

    def _show_help(self) -> str:
        """Show VOICE command help"""
        return """🎤 Voice Commands (Piper TTS + Handy STT)

Text-to-Speech:
  VOICE SAY <text>              Speak text aloud
  VOICE SAY -f <file.txt>       Read and speak file
  VOICE SAY -v <voice> <text>   Use specific voice

Speech-to-Text:
  VOICE LISTEN                  Listen and transcribe
  VOICE LISTEN -t <seconds>     Listen with timeout
  VOICE LISTEN > <file.txt>     Save transcription to file
  VOICE TRANSCRIBE <file.wav>   Transcribe audio file

Model Management:
  VOICE MODEL <name>            Set TTS/STT model
  VOICE MODELS                  List available models
  VOICE DOWNLOAD <model>        Download a model

Status:
  VOICE STATUS                  Show engine status
  VOICE HELP                    Show this help

Examples:
  VOICE SAY Hello world
  VOICE SAY -v en_GB-alba-medium "Good morning"
  VOICE LISTEN -t 30
  VOICE MODEL parakeet-v3
  VOICE DOWNLOAD whisper-small"""

    def _piper_not_installed(self) -> str:
        """Error message when Piper is not installed"""
        return """❌ Piper TTS not installed

To install (Wizard Server required):
  WIZARD CLONE piper
  VOICE DOWNLOAD en_US-lessac-medium

Documentation: wizard/library/piper/README.md"""

    def _handy_not_installed(self) -> str:
        """Error message when Handy is not installed"""
        return """❌ Handy STT not installed

To install (Wizard Server required):
  WIZARD CLONE handy
  VOICE DOWNLOAD parakeet-v3

Documentation: wizard/library/handy/README.md"""
