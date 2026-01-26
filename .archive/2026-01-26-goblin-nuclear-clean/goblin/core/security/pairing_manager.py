"""
Mobile Console Pairing Manager v1.0.0
Manages secure pairing of mobile devices as read-only consoles.

Architecture:
  - Mobile devices pair via QR code or NFC
  - Pairing creates a session with restricted capabilities
  - Mobile console role has read-only access
  - All communication via private transports only

Security:
  - Time-limited pairing codes
  - Challenge-response verification
  - Session tokens with expiry
  - No sensitive data on mobile
"""

import json
import secrets
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Storage path for pairing data
PAIRING_DATA_PATH = Path(__file__).parent.parent.parent / "memory" / "pairing"


class PairingState(Enum):
    """Pairing session states."""

    PENDING = "pending"  # Code generated, waiting for scan
    VERIFYING = "verifying"  # Challenge sent, awaiting response
    PAIRED = "paired"  # Successfully paired
    EXPIRED = "expired"  # Pairing code expired
    REVOKED = "revoked"  # Manually revoked


@dataclass
class PairingCode:
    """Represents a pairing code for mobile console."""

    code: str  # 6-digit numeric code
    secret: str  # Shared secret for verification
    created_at: str  # ISO timestamp
    expires_at: str  # ISO timestamp
    device_name: str  # Optional device name
    state: str  # PairingState value

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PairingCode":
        return cls(**data)


@dataclass
class PairedDevice:
    """Represents a paired mobile console."""

    device_id: str  # Unique device identifier
    device_name: str  # User-friendly name
    paired_at: str  # ISO timestamp
    last_seen: str  # ISO timestamp
    session_token: str  # Current session token
    token_expires: str  # Token expiry timestamp
    role: str  # Always "mobile_console"
    capabilities: List[str]  # Allowed capabilities

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PairedDevice":
        return cls(**data)


class MobilePairingManager:
    """
    Manages mobile console pairing and sessions.

    Pairing Flow:
    1. Host generates pairing code (QR/display)
    2. Mobile scans code and sends challenge
    3. Host verifies challenge and issues session token
    4. Mobile uses token for subsequent requests
    """

    # Configuration
    PAIRING_CODE_EXPIRY_MINUTES = 5
    SESSION_TOKEN_EXPIRY_HOURS = 24
    MAX_PAIRED_DEVICES = 5

    # Mobile console capabilities (read-only)
    MOBILE_CAPABILITIES = ["workflow_read", "command_restricted", "file_read_sandbox"]

    # Allowed commands for mobile console
    ALLOWED_COMMANDS = [
        "VIEW",
        "LIST",
        "HELP",
        "SEARCH",
        "READ",
        "STATUS",
        "TIME",
        "GUIDE",
        "KNOWLEDGE",
    ]

    def __init__(self, logger=None):
        """Initialize pairing manager."""
        self.logger = logger
        self.data_path = PAIRING_DATA_PATH
        self.data_path.mkdir(parents=True, exist_ok=True)

        # File paths
        self.pending_file = self.data_path / "pending_pairings.json"
        self.devices_file = self.data_path / "paired_devices.json"

        # Load existing data
        self.pending_pairings: Dict[str, PairingCode] = self._load_pending()
        self.paired_devices: Dict[str, PairedDevice] = self._load_devices()

    # ═══════════════════════════════════════════════════════════════
    # Pairing Code Generation
    # ═══════════════════════════════════════════════════════════════

    def generate_pairing_code(
        self, device_name: str = "Mobile Console"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a new pairing code for mobile device.

        Args:
            device_name: Optional name for the device

        Returns:
            Tuple of (pairing_code, qr_data_dict)
        """
        # Generate 6-digit code
        code = f"{secrets.randbelow(1000000):06d}"

        # Generate shared secret
        secret = secrets.token_hex(32)

        # Calculate expiry
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.PAIRING_CODE_EXPIRY_MINUTES)

        # Create pairing record
        pairing = PairingCode(
            code=code,
            secret=secret,
            created_at=now.isoformat() + "Z",
            expires_at=expires.isoformat() + "Z",
            device_name=device_name,
            state=PairingState.PENDING.value,
        )

        # Store pending pairing
        self.pending_pairings[code] = pairing
        self._save_pending()

        # Create QR data (what mobile will scan)
        qr_data = {
            "type": "udos_pairing",
            "version": "1.0",
            "code": code,
            "secret_hash": hashlib.sha256(secret.encode()).hexdigest()[:16],
            "expires": expires.isoformat() + "Z",
            "host_id": self._get_host_id(),
        }

        if self.logger:
            self.logger.info(f"[PAIRING] Generated code {code} for '{device_name}'")

        return code, qr_data

    def get_pairing_qr_string(self, device_name: str = "Mobile Console") -> str:
        """
        Generate pairing code and return QR-encodable string.

        Returns:
            JSON string suitable for QR encoding
        """
        code, qr_data = self.generate_pairing_code(device_name)
        return json.dumps(qr_data, separators=(",", ":"))

    # ═══════════════════════════════════════════════════════════════
    # Pairing Verification
    # ═══════════════════════════════════════════════════════════════

    def verify_pairing(
        self, code: str, challenge_response: str, device_info: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], str]:
        """
        Verify a pairing attempt from mobile device.

        Args:
            code: The 6-digit pairing code
            challenge_response: Hash of (code + secret + device_id)
            device_info: Device information from mobile

        Returns:
            Tuple of (success, session_token, message)
        """
        # Check if code exists
        if code not in self.pending_pairings:
            return False, None, "Invalid pairing code"

        pairing = self.pending_pairings[code]

        # Check expiry
        expires = datetime.fromisoformat(pairing.expires_at.rstrip("Z"))
        if datetime.utcnow() > expires:
            pairing.state = PairingState.EXPIRED.value
            self._save_pending()
            return False, None, "Pairing code expired"

        # Check state
        if pairing.state != PairingState.PENDING.value:
            return False, None, f"Pairing code already {pairing.state}"

        # Verify challenge response
        device_id = device_info.get("device_id", "unknown")
        expected = hashlib.sha256(
            f"{code}{pairing.secret}{device_id}".encode()
        ).hexdigest()

        if challenge_response != expected:
            if self.logger:
                self.logger.warning(
                    f"[PAIRING] Challenge verification failed for code {code}"
                )
            return False, None, "Challenge verification failed"

        # Check device limit
        if len(self.paired_devices) >= self.MAX_PAIRED_DEVICES:
            return (
                False,
                None,
                f"Maximum paired devices ({self.MAX_PAIRED_DEVICES}) reached",
            )

        # Generate session token
        session_token = secrets.token_urlsafe(32)
        token_expires = datetime.utcnow() + timedelta(
            hours=self.SESSION_TOKEN_EXPIRY_HOURS
        )

        # Create paired device record
        now = datetime.utcnow().isoformat() + "Z"
        device = PairedDevice(
            device_id=device_id,
            device_name=device_info.get("name", pairing.device_name),
            paired_at=now,
            last_seen=now,
            session_token=session_token,
            token_expires=token_expires.isoformat() + "Z",
            role="mobile_console",
            capabilities=self.MOBILE_CAPABILITIES.copy(),
        )

        # Store paired device
        self.paired_devices[device_id] = device
        self._save_devices()

        # Update pairing state
        pairing.state = PairingState.PAIRED.value
        self._save_pending()

        if self.logger:
            self.logger.info(
                f"[PAIRING] Successfully paired device '{device.device_name}' ({device_id})"
            )

        return True, session_token, f"Paired successfully as '{device.device_name}'"

    # ═══════════════════════════════════════════════════════════════
    # Session Management
    # ═══════════════════════════════════════════════════════════════

    def validate_session(self, device_id: str, session_token: str) -> Tuple[bool, str]:
        """
        Validate a session token for a paired device.

        Args:
            device_id: Device identifier
            session_token: Session token to validate

        Returns:
            Tuple of (valid, message)
        """
        if device_id not in self.paired_devices:
            return False, "Device not paired"

        device = self.paired_devices[device_id]

        # Check token
        if device.session_token != session_token:
            return False, "Invalid session token"

        # Check expiry
        expires = datetime.fromisoformat(device.token_expires.rstrip("Z"))
        if datetime.utcnow() > expires:
            return False, "Session expired"

        # Update last seen
        device.last_seen = datetime.utcnow().isoformat() + "Z"
        self._save_devices()

        return True, "Session valid"

    def refresh_session(
        self, device_id: str, session_token: str
    ) -> Tuple[bool, Optional[str], str]:
        """
        Refresh session token for a paired device.

        Args:
            device_id: Device identifier
            session_token: Current session token

        Returns:
            Tuple of (success, new_token, message)
        """
        valid, msg = self.validate_session(device_id, session_token)
        if not valid:
            return False, None, msg

        device = self.paired_devices[device_id]

        # Generate new token
        new_token = secrets.token_urlsafe(32)
        new_expires = datetime.utcnow() + timedelta(
            hours=self.SESSION_TOKEN_EXPIRY_HOURS
        )

        device.session_token = new_token
        device.token_expires = new_expires.isoformat() + "Z"
        device.last_seen = datetime.utcnow().isoformat() + "Z"
        self._save_devices()

        return True, new_token, "Session refreshed"

    # ═══════════════════════════════════════════════════════════════
    # Command Authorization
    # ═══════════════════════════════════════════════════════════════

    def authorize_command(
        self, device_id: str, session_token: str, command: str
    ) -> Tuple[bool, str]:
        """
        Check if a mobile console can execute a command.

        Args:
            device_id: Device identifier
            session_token: Session token
            command: Command to authorize

        Returns:
            Tuple of (authorized, message)
        """
        # Validate session first
        valid, msg = self.validate_session(device_id, session_token)
        if not valid:
            return False, msg

        # Check command whitelist
        cmd_upper = command.upper().split()[0] if command else ""
        if cmd_upper not in self.ALLOWED_COMMANDS:
            return False, f"Command '{cmd_upper}' not allowed for mobile console"

        return True, "Command authorized"

    # ═══════════════════════════════════════════════════════════════
    # Device Management
    # ═══════════════════════════════════════════════════════════════

    def list_devices(self) -> List[Dict[str, Any]]:
        """
        List all paired devices.

        Returns:
            List of device info dicts
        """
        devices = []
        for device in self.paired_devices.values():
            # Check if session expired
            expires = datetime.fromisoformat(device.token_expires.rstrip("Z"))
            active = datetime.utcnow() < expires

            devices.append(
                {
                    "device_id": device.device_id,
                    "device_name": device.device_name,
                    "paired_at": device.paired_at,
                    "last_seen": device.last_seen,
                    "active": active,
                    "role": device.role,
                }
            )

        return devices

    def revoke_device(self, device_id: str) -> Tuple[bool, str]:
        """
        Revoke pairing for a device.

        Args:
            device_id: Device to revoke

        Returns:
            Tuple of (success, message)
        """
        if device_id not in self.paired_devices:
            return False, "Device not found"

        device = self.paired_devices.pop(device_id)
        self._save_devices()

        if self.logger:
            self.logger.info(
                f"[PAIRING] Revoked device '{device.device_name}' ({device_id})"
            )

        return True, f"Device '{device.device_name}' unpaired"

    def revoke_all(self) -> Tuple[int, str]:
        """
        Revoke all paired devices.

        Returns:
            Tuple of (count, message)
        """
        count = len(self.paired_devices)
        self.paired_devices.clear()
        self._save_devices()

        if self.logger:
            self.logger.info(f"[PAIRING] Revoked all {count} paired devices")

        return count, f"Revoked {count} paired devices"

    # ═══════════════════════════════════════════════════════════════
    # Persistence
    # ═══════════════════════════════════════════════════════════════

    def _load_pending(self) -> Dict[str, PairingCode]:
        """Load pending pairings from disk."""
        if not self.pending_file.exists():
            return {}

        try:
            with open(self.pending_file) as f:
                data = json.load(f)
            return {k: PairingCode.from_dict(v) for k, v in data.items()}
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_pending(self):
        """Save pending pairings to disk."""
        data = {k: v.to_dict() for k, v in self.pending_pairings.items()}
        with open(self.pending_file, "w") as f:
            json.dump(data, f, indent=2)

    def _load_devices(self) -> Dict[str, PairedDevice]:
        """Load paired devices from disk."""
        if not self.devices_file.exists():
            return {}

        try:
            with open(self.devices_file) as f:
                data = json.load(f)
            return {k: PairedDevice.from_dict(v) for k, v in data.items()}
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_devices(self):
        """Save paired devices to disk."""
        data = {k: v.to_dict() for k, v in self.paired_devices.items()}
        with open(self.devices_file, "w") as f:
            json.dump(data, f, indent=2)

    def _get_host_id(self) -> str:
        """Get unique identifier for this host."""
        # Use machine ID or generate one
        host_id_file = self.data_path / ".host_id"
        if host_id_file.exists():
            return host_id_file.read_text().strip()

        host_id = secrets.token_hex(16)
        host_id_file.write_text(host_id)
        return host_id


# Singleton instance
_pairing_manager: Optional[MobilePairingManager] = None


def get_pairing_manager(logger=None) -> MobilePairingManager:
    """Get or create the pairing manager singleton."""
    global _pairing_manager
    if _pairing_manager is None:
        _pairing_manager = MobilePairingManager(logger=logger)
    return _pairing_manager
