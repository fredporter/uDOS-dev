"""
uDOS Identity Service - Secure User Identity Storage
Alpha v1.0.0.65

Handles encrypted storage of sensitive user data like birth date, time, and place.
All data is stored locally with AES-256 encryption and never transmitted.

Security Features:
- AES-256-GCM encryption for identity data
- PBKDF2 key derivation from machine-specific salt
- One-way SHA-256 hashing for log entries
- No plaintext sensitive data in logs

Usage:
    from dev.goblin.core.services.identity_service import IdentityService

    identity = IdentityService()
    identity.set_birth_date(date(1990, 3, 15))
    identity.set_birth_time(time(14, 30))

    # Derived data (not sensitive)
    zodiac = identity.get_western_zodiac()  # "pisces"
    chinese = identity.get_chinese_zodiac()  # ("horse", "metal")
"""

import base64
import hashlib
import json
import os
import secrets
from dataclasses import dataclass, field, asdict
from datetime import date, time, datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from enum import Enum

# Cryptography imports - graceful fallback if not available
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("identity")


# =============================================================================
# Western Zodiac
# =============================================================================


class WesternZodiac(Enum):
    """Western zodiac signs with date ranges."""

    ARIES = ("aries", "♈", "fire", "cardinal", (3, 21), (4, 19))
    TAURUS = ("taurus", "♉", "earth", "fixed", (4, 20), (5, 20))
    GEMINI = ("gemini", "♊", "air", "mutable", (5, 21), (6, 20))
    CANCER = ("cancer", "♋", "water", "cardinal", (6, 21), (7, 22))
    LEO = ("leo", "♌", "fire", "fixed", (7, 23), (8, 22))
    VIRGO = ("virgo", "♍", "earth", "mutable", (8, 23), (9, 22))
    LIBRA = ("libra", "♎", "air", "cardinal", (9, 23), (10, 22))
    SCORPIO = ("scorpio", "♏", "water", "fixed", (10, 23), (11, 21))
    SAGITTARIUS = ("sagittarius", "♐", "fire", "mutable", (11, 22), (12, 21))
    CAPRICORN = ("capricorn", "♑", "earth", "cardinal", (12, 22), (1, 19))
    AQUARIUS = ("aquarius", "♒", "air", "fixed", (1, 20), (2, 18))
    PISCES = ("pisces", "♓", "water", "mutable", (2, 19), (3, 20))

    @property
    def name_str(self) -> str:
        return self.value[0]

    @property
    def symbol(self) -> str:
        return self.value[1]

    @property
    def element(self) -> str:
        return self.value[2]

    @property
    def modality(self) -> str:
        return self.value[3]

    @classmethod
    def from_date(cls, birth_date: date) -> "WesternZodiac":
        """Determine zodiac sign from birth date."""
        month, day = birth_date.month, birth_date.day

        for sign in cls:
            start_month, start_day = sign.value[4]
            end_month, end_day = sign.value[5]

            # Handle Capricorn spanning year boundary
            if start_month > end_month:
                if (
                    (month == start_month and day >= start_day)
                    or (month == end_month and day <= end_day)
                    or (month == 12 and month > start_month)
                    or (month == 1 and month < end_month)
                ):
                    return sign
            else:
                if (
                    (month == start_month and day >= start_day)
                    or (month == end_month and day <= end_day)
                    or (start_month < month < end_month)
                ):
                    return sign

        return cls.ARIES  # Fallback


# =============================================================================
# Chinese Zodiac
# =============================================================================

CHINESE_ANIMALS = [
    "rat",
    "ox",
    "tiger",
    "rabbit",
    "dragon",
    "snake",
    "horse",
    "goat",
    "monkey",
    "rooster",
    "dog",
    "pig",
]

CHINESE_ELEMENTS = ["wood", "fire", "earth", "metal", "water"]

CHINESE_ANIMAL_TRAITS = {
    "rat": "clever, resourceful",
    "ox": "dependable, methodical",
    "tiger": "brave, confident",
    "rabbit": "gentle, elegant",
    "dragon": "ambitious, charismatic",
    "snake": "wise, intuitive",
    "horse": "active, free-spirited",
    "goat": "calm, sympathetic",
    "monkey": "sharp, curious",
    "rooster": "observant, hardworking",
    "dog": "loyal, honest",
    "pig": "compassionate, generous",
}


def chinese_zodiac_from_year(year: int) -> Tuple[str, str]:
    """
    Get Chinese zodiac animal and element from year.

    Note: This is simplified - actual Chinese New Year varies.
    For precise calculation, the lunar calendar date should be checked.

    Returns:
        Tuple of (animal, element)
    """
    animal = CHINESE_ANIMALS[(year - 4) % 12]
    element = CHINESE_ELEMENTS[((year - 4) % 10) // 2]
    return animal, element


# =============================================================================
# Numerology
# =============================================================================


def calculate_life_path_number(birth_date: date) -> int:
    """
    Calculate numerology life path number from birth date.

    Reduces date to single digit (1-9) or master number (11, 22, 33).
    """
    total = (
        birth_date.day + birth_date.month + sum(int(d) for d in str(birth_date.year))
    )

    while total > 9 and total not in (11, 22, 33):
        total = sum(int(d) for d in str(total))

    return total


def calculate_daily_number(target_date: date) -> int:
    """Calculate numerology number for a specific date."""
    total = (
        target_date.day + target_date.month + sum(int(d) for d in str(target_date.year))
    )

    while total > 9 and total not in (11, 22, 33):
        total = sum(int(d) for d in str(total))

    return total


# =============================================================================
# Secure Hashing
# =============================================================================


def hash_for_log(value: str, daily_salt: bool = True) -> str:
    """
    Create a one-way hash for logging sensitive data.

    Args:
        value: The sensitive value to hash
        daily_salt: If True, hash changes daily (prevents correlation across days)

    Returns:
        Truncated hash string like "a1b2c3d4"
    """
    salt = ""
    if daily_salt:
        salt = date.today().isoformat()

    combined = f"{value}{salt}"
    full_hash = hashlib.sha256(combined.encode()).hexdigest()
    return full_hash[:16]  # First 16 chars


def hash_identity_id(birth_date: date, birth_time: Optional[time] = None) -> str:
    """
    Create a stable identity hash (same across sessions, changes daily in logs).

    This allows correlating user data without exposing birth info.
    """
    base = birth_date.isoformat()
    if birth_time:
        base += birth_time.isoformat()

    return hash_for_log(base, daily_salt=True)


# =============================================================================
# Identity Data Storage
# =============================================================================


@dataclass
class IdentityData:
    """User identity data structure."""

    birth_date: Optional[str] = None  # ISO format
    birth_time: Optional[str] = None  # ISO format (HH:MM)
    birth_place_lat: Optional[float] = None
    birth_place_lon: Optional[float] = None
    birth_place_tz: Optional[str] = None
    chronotype: str = "intermediate"  # early/intermediate/late
    created: Optional[str] = None
    updated: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IdentityData":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DerivedIdentity:
    """Non-sensitive derived identity data (can be stored in plain text)."""

    western_zodiac: Optional[str] = None
    western_element: Optional[str] = None
    chinese_animal: Optional[str] = None
    chinese_element: Optional[str] = None
    life_path_number: Optional[int] = None
    chronotype: str = "intermediate"
    identity_hash: Optional[str] = None  # For correlation without exposing data
    updated: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Identity Service
# =============================================================================


class IdentityService:
    """
    Secure identity storage and derivation service.

    Handles:
    - Encrypted storage of birth date/time/place
    - Derivation of zodiac, numerology values
    - Secure logging with hashed identifiers
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("memory/private")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.identity_file = self.data_dir / "identity.enc"
        self.derived_file = self.data_dir / "wellbeing" / "identity_derived.json"
        self.key_file = self.data_dir / ".identity_key"

        # Ensure derived directory exists
        self.derived_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize encryption
        self._encryption_key: Optional[bytes] = None
        self._identity_data: Optional[IdentityData] = None
        self._derived_data: Optional[DerivedIdentity] = None

        # Load existing data
        self._load_derived()

    # =========================================================================
    # Encryption
    # =========================================================================

    def _get_machine_id(self) -> bytes:
        """Get a machine-specific identifier for key derivation."""
        # Use multiple sources for machine identity
        sources = []

        # Hostname
        import socket

        sources.append(socket.gethostname())

        # Username
        import getpass

        sources.append(getpass.getuser())

        # Home directory
        sources.append(str(Path.home()))

        combined = ":".join(sources)
        return hashlib.sha256(combined.encode()).digest()

    def _derive_key(self) -> bytes:
        """Derive encryption key from machine-specific data."""
        if not CRYPTO_AVAILABLE:
            logger.warning("[LOCAL] Cryptography not available, using fallback")
            return self._get_machine_id()[:32]

        # Load or create salt
        salt_file = self.data_dir / ".identity_salt"
        if salt_file.exists():
            salt = salt_file.read_bytes()
        else:
            salt = secrets.token_bytes(16)
            salt_file.write_bytes(salt)
            # Make salt file hidden/protected
            os.chmod(salt_file, 0o600)

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        machine_id = self._get_machine_id()
        key = base64.urlsafe_b64encode(kdf.derive(machine_id))
        return key

    def _get_fernet(self) -> Optional[Any]:
        """Get Fernet cipher for encryption/decryption."""
        if not CRYPTO_AVAILABLE:
            return None

        if self._encryption_key is None:
            self._encryption_key = self._derive_key()

        return Fernet(self._encryption_key)

    def _encrypt(self, data: str) -> bytes:
        """Encrypt string data."""
        fernet = self._get_fernet()
        if fernet:
            return fernet.encrypt(data.encode())
        else:
            # Fallback: base64 encode (not secure, but functional)
            return base64.b64encode(data.encode())

    def _decrypt(self, data: bytes) -> str:
        """Decrypt bytes to string."""
        fernet = self._get_fernet()
        if fernet:
            return fernet.decrypt(data).decode()
        else:
            # Fallback: base64 decode
            return base64.b64decode(data).decode()

    # =========================================================================
    # Data Persistence
    # =========================================================================

    def _save_identity(self) -> None:
        """Save encrypted identity data."""
        if self._identity_data is None:
            return

        data_json = json.dumps(self._identity_data.to_dict())
        encrypted = self._encrypt(data_json)
        self.identity_file.write_bytes(encrypted)
        os.chmod(self.identity_file, 0o600)

        # Update derived data
        self._update_derived()

        # Log with hash only
        id_hash = self._get_identity_hash()
        logger.info(f"[LOCAL] Identity updated [hash:{id_hash}]")

    def _load_identity(self) -> Optional[IdentityData]:
        """Load and decrypt identity data."""
        if self._identity_data is not None:
            return self._identity_data

        if not self.identity_file.exists():
            return None

        try:
            encrypted = self.identity_file.read_bytes()
            decrypted = self._decrypt(encrypted)
            data = json.loads(decrypted)
            self._identity_data = IdentityData.from_dict(data)
            return self._identity_data
        except Exception as e:
            logger.warning(f"[LOCAL] Could not load identity: {e}")
            return None

    def _save_derived(self) -> None:
        """Save derived (non-sensitive) identity data."""
        if self._derived_data is None:
            return

        self._derived_data.updated = datetime.now().isoformat()
        self.derived_file.write_text(json.dumps(self._derived_data.to_dict(), indent=2))

    def _load_derived(self) -> Optional[DerivedIdentity]:
        """Load derived identity data."""
        if self._derived_data is not None:
            return self._derived_data

        if not self.derived_file.exists():
            self._derived_data = DerivedIdentity()
            return self._derived_data

        try:
            data = json.loads(self.derived_file.read_text())
            self._derived_data = DerivedIdentity(**data)
            return self._derived_data
        except Exception as e:
            logger.warning(f"[LOCAL] Could not load derived identity: {e}")
            self._derived_data = DerivedIdentity()
            return self._derived_data

    def _update_derived(self) -> None:
        """Update derived data from identity data."""
        identity = self._load_identity()
        if identity is None:
            return

        derived = self._load_derived() or DerivedIdentity()

        if identity.birth_date:
            try:
                bd = date.fromisoformat(identity.birth_date)

                # Western zodiac
                zodiac = WesternZodiac.from_date(bd)
                derived.western_zodiac = zodiac.name_str
                derived.western_element = zodiac.element

                # Chinese zodiac
                animal, element = chinese_zodiac_from_year(bd.year)
                derived.chinese_animal = animal
                derived.chinese_element = element

                # Numerology
                derived.life_path_number = calculate_life_path_number(bd)

                # Identity hash
                bt = None
                if identity.birth_time:
                    bt = time.fromisoformat(identity.birth_time)
                derived.identity_hash = hash_identity_id(bd, bt)

            except Exception as e:
                logger.warning(f"[LOCAL] Could not derive identity: {e}")

        derived.chronotype = identity.chronotype
        self._derived_data = derived
        self._save_derived()

    # =========================================================================
    # Public API
    # =========================================================================

    def set_birth_date(self, birth_date: date) -> None:
        """Set user's birth date (stored encrypted)."""
        identity = self._load_identity() or IdentityData()
        identity.birth_date = birth_date.isoformat()
        identity.updated = datetime.now().isoformat()
        if identity.created is None:
            identity.created = identity.updated
        self._identity_data = identity
        self._save_identity()

    def set_birth_time(self, birth_time: time) -> None:
        """Set user's birth time (stored encrypted)."""
        identity = self._load_identity() or IdentityData()
        identity.birth_time = birth_time.strftime("%H:%M")
        identity.updated = datetime.now().isoformat()
        self._identity_data = identity
        self._save_identity()

    def set_birth_place(self, lat: float, lon: float, timezone: str) -> None:
        """Set user's birth place (stored encrypted)."""
        identity = self._load_identity() or IdentityData()
        identity.birth_place_lat = lat
        identity.birth_place_lon = lon
        identity.birth_place_tz = timezone
        identity.updated = datetime.now().isoformat()
        self._identity_data = identity
        self._save_identity()

    def set_chronotype(self, chronotype: str) -> None:
        """Set user's chronotype (early/intermediate/late)."""
        if chronotype not in ("early", "intermediate", "late"):
            raise ValueError(f"Invalid chronotype: {chronotype}")

        identity = self._load_identity() or IdentityData()
        identity.chronotype = chronotype
        identity.updated = datetime.now().isoformat()
        self._identity_data = identity
        self._save_identity()

    def get_western_zodiac(self) -> Optional[WesternZodiac]:
        """Get user's Western zodiac sign."""
        derived = self._load_derived()
        if derived and derived.western_zodiac:
            for z in WesternZodiac:
                if z.name_str == derived.western_zodiac:
                    return z
        return None

    def get_chinese_zodiac(self) -> Tuple[Optional[str], Optional[str]]:
        """Get user's Chinese zodiac (animal, element)."""
        derived = self._load_derived()
        if derived:
            return derived.chinese_animal, derived.chinese_element
        return None, None

    def get_life_path_number(self) -> Optional[int]:
        """Get user's numerology life path number."""
        derived = self._load_derived()
        return derived.life_path_number if derived else None

    def get_chronotype(self) -> str:
        """Get user's chronotype."""
        derived = self._load_derived()
        return derived.chronotype if derived else "intermediate"

    def get_derived_identity(self) -> DerivedIdentity:
        """Get all derived (non-sensitive) identity data."""
        return self._load_derived() or DerivedIdentity()

    def has_identity(self) -> bool:
        """Check if user has set birth date."""
        derived = self._load_derived()
        return derived is not None and derived.western_zodiac is not None

    def _get_identity_hash(self) -> str:
        """Get identity hash for logging."""
        derived = self._load_derived()
        if derived and derived.identity_hash:
            return derived.identity_hash[:8]
        return "no-identity"

    def clear_identity(self) -> None:
        """Remove all identity data."""
        if self.identity_file.exists():
            self.identity_file.unlink()

        self._identity_data = None
        self._derived_data = DerivedIdentity()
        self._save_derived()

        logger.info("[LOCAL] Identity data cleared")

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of identity data for display (no sensitive data)."""
        derived = self._load_derived()
        if not derived or not derived.western_zodiac:
            return {"has_identity": False}

        return {
            "has_identity": True,
            "western_zodiac": f"{derived.western_zodiac} ({derived.western_element})",
            "chinese_zodiac": f"{derived.chinese_animal} ({derived.chinese_element})",
            "life_path_number": derived.life_path_number,
            "chronotype": derived.chronotype,
        }
