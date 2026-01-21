"""
QR Transport Command Handler
Alpha v1.0.1.1+

Handles QR code generation and scanning for visual data transfer.
"""

from pathlib import Path
from typing import Optional, List
import json

from dev.goblin.core.services.logging_manager import get_logger
from extensions.transport.qr import QREncoder, QRDecoder, PacketType

logger = get_logger("command-qr")


class QRHandler:
    """
    Handler for QR transport commands.

    Commands:
    - QR SEND <file> - Encode file to QR codes
    - QR RECEIVE <dir> - Scan QR codes from directory
    - QR PAIR <device_name> - Generate pairing QR code
    - QR SHOW <text> - Display text as QR code
    """

    def __init__(self):
        self.encoder = None
        self.decoder = None
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if QR libraries are available"""
        try:
            from extensions.transport.qr import QREncoder, QRDecoder

            self.encoder = QREncoder()
            self.decoder = QRDecoder()
            logger.info("[QR] QR transport libraries loaded")
        except ImportError as e:
            logger.warning(f"[QR] QR libraries not available: {e}")
            self.encoder = None
            self.decoder = None

    def handle(self, command: str, params: List[str], grid, parser) -> Optional[str]:
        """
        Route QR commands to appropriate handlers.

        Args:
            command: Command name (QR)
            params: Command parameters [SEND|RECEIVE|PAIR|SHOW, ...]
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
        elif subcommand == "PAIR":
            return self._handle_pair(params[1:])
        elif subcommand == "SHOW":
            return self._handle_show(params[1:])
        elif subcommand == "HELP":
            return self._show_help()
        else:
            return f"❌ Unknown QR command: {subcommand}\nUse 'QR HELP' for usage"

    def _handle_send(self, params: List[str]) -> str:
        """
        Encode file to QR codes.

        Usage: QR SEND <file> [output_dir]
        """
        if not self.encoder:
            return (
                "❌ QR encoder not available. Install with: pip install 'qrcode[pil]'"
            )

        if not params:
            return "❌ Usage: QR SEND <file> [output_dir]"

        # Get file path
        file_path = Path(params[0])

        # Resolve relative to memory/sandbox if not absolute
        if not file_path.is_absolute():
            file_path = Path.home() / ".udos" / "memory" / "sandbox" / file_path

        if not file_path.exists():
            return f"❌ File not found: {file_path}"

        # Get output directory
        if len(params) > 1:
            output_dir = Path(params[1])
        else:
            output_dir = Path.home() / ".udos" / "memory" / ".tmp" / "qr-send"

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Read file
            logger.info(f"[QR-ENC] Reading file: {file_path}")
            file_data = file_path.read_bytes()

            # Encode to QR packets
            packets = self.encoder.encode_data(
                file_data,
                PacketType.FILE,
                metadata={
                    "filename": file_path.name,
                    "size": len(file_data),
                    "mime_type": self._guess_mime_type(file_path),
                },
            )

            # Save QR codes
            self.encoder.save_packets_qr(packets, output_dir, prefix="qr")

            logger.info(f"[QR-ENC] Created {len(packets)} QR code(s) in {output_dir}")

            # Show first QR as ASCII
            if packets:
                ascii_qr = self.encoder.packet_to_ascii(packets[0])
                return (
                    f"✅ Encoded {file_path.name} ({len(file_data)} bytes) into {len(packets)} QR code(s)\n"
                    f"📁 Saved to: {output_dir}\n\n"
                    f"📱 QR Code 1/{len(packets)}:\n\n{ascii_qr}\n\n"
                    f"💡 Scan all {len(packets)} QR codes to receive the complete file"
                )

        except Exception as e:
            logger.error(f"[QR-ENC] Failed to encode file: {e}", exc_info=True)
            return f"❌ Failed to encode file: {e}"

    def _handle_receive(self, params: List[str]) -> str:
        """
        Decode QR codes from directory.

        Usage: QR RECEIVE <image_dir> [output_file]
        """
        if not self.decoder:
            return "❌ QR decoder not available. Install with: pip install pyzbar pillow && brew install zbar"

        if not params:
            return "❌ Usage: QR RECEIVE <image_dir> [output_file]"

        # Get image directory
        image_dir = Path(params[0])
        if not image_dir.is_absolute():
            image_dir = Path.home() / ".udos" / "memory" / image_dir

        if not image_dir.exists():
            return f"❌ Directory not found: {image_dir}"

        # Get output file
        if len(params) > 1:
            output_file = Path(params[1])
        else:
            output_file = Path.home() / ".udos" / "memory" / "sandbox" / "received_file"

        try:
            # Find QR images
            qr_images = sorted(image_dir.glob("*.png"))
            if not qr_images:
                qr_images = sorted(image_dir.glob("*.jpg"))

            if not qr_images:
                return f"❌ No QR code images found in {image_dir}"

            logger.info(f"[QR-DEC] Found {len(qr_images)} QR image(s)")

            # Decode and assemble
            assembled_data = self.decoder.decode_and_assemble(
                qr_images, verify_crc=True
            )

            if not assembled_data:
                # Check what's missing
                first_packet = self.decoder.decode_image(qr_images[0])
                if first_packet:
                    missing = self.decoder.get_missing_chunks(first_packet.packet_id)
                    return f"❌ Incomplete packet set. Missing chunks: {missing}"
                else:
                    return f"❌ Failed to decode QR codes"

            # Get metadata from first packet
            first_packet = self.decoder.decode_image(qr_images[0])
            filename = (
                first_packet.metadata.get("filename", "received_file")
                if first_packet.metadata
                else "received_file"
            )

            # Update output filename if not specified
            if len(params) <= 1:
                output_file = output_file.parent / filename

            # Save file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(assembled_data)

            logger.info(f"[QR-DEC] Saved {len(assembled_data)} bytes to {output_file}")

            return (
                f"✅ Successfully received file via QR codes\n"
                f"📁 File: {filename} ({len(assembled_data)} bytes)\n"
                f"💾 Saved to: {output_file}\n"
                f"📱 Scanned {len(qr_images)} QR code(s)"
            )

        except Exception as e:
            logger.error(f"[QR-DEC] Failed to decode QR codes: {e}", exc_info=True)
            return f"❌ Failed to decode QR codes: {e}"

    def _handle_pair(self, params: List[str]) -> str:
        """
        Generate device pairing QR code.

        Usage: QR PAIR <device_name>
        """
        if not self.encoder:
            return "❌ QR encoder not available"

        if not params:
            return "❌ Usage: QR PAIR <device_name>"

        device_name = " ".join(params)

        try:
            # Generate device ID
            import uuid

            device_id = f"device-{uuid.uuid4().hex[:8]}"

            # Create handshake packet
            from extensions.transport.qr.packet import PacketBuilder

            builder = PacketBuilder()

            packet = builder.create_handshake(
                device_id=device_id, device_name=device_name
            )

            # Show as ASCII
            ascii_qr = self.encoder.packet_to_ascii(packet)

            logger.info(
                f"[QR] Generated pairing QR for device: {device_name} (ID: {device_id})"
            )

            return (
                f"📱 Device Pairing QR Code\n\n"
                f"Device: {device_name}\n"
                f"ID: {device_id}\n\n"
                f"{ascii_qr}\n\n"
                f"💡 Scan this QR code with another uDOS device to pair"
            )

        except Exception as e:
            logger.error(f"[QR] Failed to generate pairing QR: {e}", exc_info=True)
            return f"❌ Failed to generate pairing QR: {e}"

    def _handle_show(self, params: List[str]) -> str:
        """
        Display text as QR code.

        Usage: QR SHOW <text>
        """
        if not self.encoder:
            return "❌ QR encoder not available"

        if not params:
            return "❌ Usage: QR SHOW <text>"

        text = " ".join(params)

        try:
            # Encode text
            packets = self.encoder.encode_text(text)

            if not packets:
                return "❌ Failed to encode text"

            # Show as ASCII
            ascii_qr = self.encoder.packet_to_ascii(packets[0])

            logger.info(f"[QR] Generated QR for text: {text[:50]}...")

            if len(packets) > 1:
                return (
                    f"📱 Text QR Code (1/{len(packets)})\n\n"
                    f"{ascii_qr}\n\n"
                    f"⚠️  Text too long for single QR code. Use 'QR SEND' to save all {len(packets)} QR codes."
                )
            else:
                return (
                    f"📱 Text QR Code\n\n"
                    f"{ascii_qr}\n\n"
                    f"💡 Scan this QR code to receive: {text}"
                )

        except Exception as e:
            logger.error(f"[QR] Failed to show text as QR: {e}", exc_info=True)
            return f"❌ Failed to show text as QR: {e}"

    def _guess_mime_type(self, file_path: Path) -> str:
        """Guess MIME type from file extension"""
        ext = file_path.suffix.lower()
        mime_types = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".py": "text/x-python",
            ".upy": "text/x-upy",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".pdf": "application/pdf",
        }
        return mime_types.get(ext, "application/octet-stream")

    def _show_help(self) -> str:
        """Show QR command help"""
        return """
📱 QR Transport Commands

Visual data transfer via QR codes for offline communication.

COMMANDS:
  QR SEND <file> [output_dir]
    Encode file to QR codes
    Example: QR SEND README.MD
    
  QR RECEIVE <image_dir> [output_file]
    Decode QR codes from scanned images
    Example: QR RECEIVE scanned-qr/
    
  QR PAIR <device_name>
    Generate device pairing QR code
    Example: QR PAIR "Fred's Laptop"
    
  QR SHOW <text>
    Display text as QR code
    Example: QR SHOW "Hello, uDOS!"
    
  QR HELP
    Show this help message

TRANSPORT POLICY:
  Realm: PRIVATE_SAFE
  Data: Allowed (with packet limits)
  Commands: Allowed (pairing, data transfer)
  
DEPENDENCIES:
  Encoder: pip install 'qrcode[pil]'
  Decoder: pip install pyzbar pillow && brew install zbar

NOTES:
  - Large files are split into multiple QR codes
  - Each QR code contains ~256 bytes of data
  - CRC32 validation ensures data integrity
  - All QR codes must be scanned to receive complete file
  
📚 See: extensions/transport/qr/README.md
"""
