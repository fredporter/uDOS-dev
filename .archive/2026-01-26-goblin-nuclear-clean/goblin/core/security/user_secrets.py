"""
uDOS Security - User Secrets Manager
Alpha v1.0.0.24+

Secure storage for sensitive user data with privacy tiers.

This module extends KeyStore to handle user-specific sensitive information
like personal details, location, passwords, and configurable settings.

Storage Modes:
- TOMB: Archive/static data - unencrypted but access-logged
- CRYPT: Encrypted vault - all data encrypted, conditional access

Privacy Tiers:
- PUBLIC: Visible to anyone (display name, avatar)
- SHARED: Visible to approved users/devices
- PRIVATE: Owner only, encrypted
- SYSTEM: System use only, never exposed

Sensitive Field Categories:
- PII: Personal Identifiable Information (email, DOB, address)
- LOCATION: Current/home location data
- CREDENTIALS: Passwords, tokens, auth data
- FINANCIAL: Barter points, transaction history
- HEALTH: HP, wellness tracking data

Integration:
- Uses KeyStore for encrypted storage
- Uses Role system for access control
- Uses SharingService for conditional sharing
- TinyCore compatible (file-based, no root required)
"""

import json
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

from dev.goblin.core.security.key_store import (
    KeyStore,
    KeyRealm,
    CRYPTO_AVAILABLE,
)
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("user-secrets")


# =============================================================================
# Enums and Constants
# =============================================================================


class StorageMode(Enum):
    """Storage mode for user data."""

    TOMB = "tomb"  # Archive mode - unencrypted, access-logged, static
    CRYPT = "crypt"  # Vault mode - encrypted, conditional access, dynamic


class PrivacyTier(Enum):
    """Privacy tier for user data fields."""

    PUBLIC = "public"  # Visible to anyone
    SHARED = "shared"  # Visible to approved users/devices
    PRIVATE = "private"  # Owner only, encrypted
    SYSTEM = "system"  # System use only, never exposed


class SensitiveCategory(Enum):
    """Categories of sensitive data."""

    PII = "pii"  # Personal Identifiable Information
    LOCATION = "location"  # Location data
    CREDENTIALS = "creds"  # Passwords, tokens
    FINANCIAL = "financial"  # Barter points, transactions
    HEALTH = "health"  # HP, wellness data
    PREFERENCES = "prefs"  # User preferences (less sensitive)
    GENERAL = "general"  # General settings


# Default privacy levels for categories
DEFAULT_PRIVACY = {
    SensitiveCategory.PII: PrivacyTier.PRIVATE,
    SensitiveCategory.LOCATION: PrivacyTier.PRIVATE,
    SensitiveCategory.CREDENTIALS: PrivacyTier.PRIVATE,
    SensitiveCategory.FINANCIAL: PrivacyTier.PRIVATE,
    SensitiveCategory.HEALTH: PrivacyTier.PRIVATE,
    SensitiveCategory.PREFERENCES: PrivacyTier.SHARED,
    SensitiveCategory.GENERAL: PrivacyTier.PUBLIC,
}


# Minimum role required to access each tier
# Role hierarchy: GHOST(1) < TOMB(2) < DRONE(3) < CRYPT(4) < KNIGHT(5) < IMP(6) < SORCERER(8) < WIZARD(10)
TIER_ROLE_REQUIREMENTS = {
    PrivacyTier.PUBLIC: 2,  # TOMB (2) - static files/packages, or DRONE (3) with automation
    PrivacyTier.SHARED: 4,  # CRYPT (4) - approved users with encryption access
    PrivacyTier.PRIVATE: 5,  # KNIGHT (5) - device owner only
    PrivacyTier.SYSTEM: 10,  # WIZARD (10) only
}


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class SecretField:
    """A single secret field with metadata."""

    name: str
    value: Any  # Will be encrypted if PRIVATE
    category: SensitiveCategory
    privacy: PrivacyTier

    # Metadata
    created: str = ""
    modified: str = ""
    accessed: str = ""
    access_count: int = 0

    # Sharing
    shared_with: List[str] = field(default_factory=list)  # User/device IDs
    share_expires: Optional[str] = None

    # Encryption state
    is_encrypted: bool = False

    def __post_init__(self):
        now = datetime.now().isoformat()
        if not self.created:
            self.created = now
        if not self.modified:
            self.modified = now

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "value": self.value,
            "category": self.category.value,
            "privacy": self.privacy.value,
            "created": self.created,
            "modified": self.modified,
            "accessed": self.accessed,
            "access_count": self.access_count,
            "shared_with": self.shared_with,
            "share_expires": self.share_expires,
            "is_encrypted": self.is_encrypted,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SecretField":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            value=data["value"],
            category=SensitiveCategory(data["category"]),
            privacy=PrivacyTier(data["privacy"]),
            created=data.get("created", ""),
            modified=data.get("modified", ""),
            accessed=data.get("accessed", ""),
            access_count=data.get("access_count", 0),
            shared_with=data.get("shared_with", []),
            share_expires=data.get("share_expires"),
            is_encrypted=data.get("is_encrypted", False),
        )


# =============================================================================
# User Secrets Manager
# =============================================================================


class UserSecretsManager:
    """
    Manages encrypted user secrets and sensitive data.

    Two operating modes:
    - TOMB: Static archive with access logging (unencrypted)
    - CRYPT: Dynamic vault with encryption (default)

    Uses KeyStore for encryption keys and secure storage.
    """

    # Standard PII field names
    STANDARD_PII_FIELDS = {
        "email",
        "date_of_birth",
        "phone",
        "address",
        "real_name",
        "government_id",
        "ssn",
    }

    # Standard location fields
    STANDARD_LOCATION_FIELDS = {
        "current_location",
        "home_location",
        "last_known_location",
        "location_history",
        "gps_coords",
        "tile_code",
    }

    # Standard credential fields
    STANDARD_CREDENTIAL_FIELDS = {
        "password",
        "pin",
        "recovery_key",
        "auth_token",
        "api_key",
        "private_key",
        "encryption_key",
    }

    def __init__(
        self,
        user_id: str,
        mode: StorageMode = StorageMode.CRYPT,
        base_path: Optional[Path] = None,
    ):
        """
        Initialize UserSecretsManager.

        Args:
            user_id: Unique user identifier
            mode: TOMB (archive) or CRYPT (encrypted vault)
            base_path: Base path for secrets storage
        """
        self.user_id = user_id
        self.mode = mode

        # Storage paths
        if base_path is None:
            base_path = Path.home() / ".udos" / "secrets"

        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

        # User-specific paths
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        self.user_dir = self.base_path / user_hash
        self.user_dir.mkdir(parents=True, exist_ok=True)

        self.secrets_file = self.user_dir / f"secrets_{mode.value}.json"
        self.audit_file = self.user_dir / "access_audit.log"

        # KeyStore for encryption (only in CRYPT mode)
        self._key_store = None
        if mode == StorageMode.CRYPT:
            self._key_store = KeyStore(realm=KeyRealm.LOCAL_ONLY)

        # Load secrets
        self._secrets: Dict[str, SecretField] = {}
        self._load_secrets()

        logger.info(
            f"[LOCAL] UserSecrets initialized for {user_id[:8]}... in {mode.value} mode"
        )

    def _load_secrets(self):
        """Load secrets from storage."""
        if not self.secrets_file.exists():
            return

        try:
            data = json.loads(self.secrets_file.read_text())
            for field_data in data.get("fields", []):
                field = SecretField.from_dict(field_data)
                self._secrets[field.name] = field
        except Exception as e:
            logger.error(f"[ERROR] Failed to load secrets: {e}")

    def _save_secrets(self):
        """Save secrets to storage."""
        data = {
            "version": "1.0.0.24",
            "user_id_hash": hashlib.sha256(self.user_id.encode()).hexdigest()[:16],
            "mode": self.mode.value,
            "updated": datetime.now().isoformat(),
            "fields": [f.to_dict() for f in self._secrets.values()],
        }

        # Restricted permissions
        import os

        old_umask = os.umask(0o077)
        try:
            self.secrets_file.write_text(json.dumps(data, indent=2))
        finally:
            os.umask(old_umask)

    def _audit_access(self, action: str, field_name: str, accessor: str = "owner"):
        """Log access to audit file."""
        timestamp = datetime.now().isoformat()
        entry = f"{timestamp}|{action}|{field_name}|{accessor}|{self.mode.value}\n"

        with open(self.audit_file, "a") as f:
            f.write(entry)

    def _encrypt_value(self, value: Any) -> str:
        """Encrypt a value using KeyStore."""
        if not self._key_store:
            return json.dumps(value)

        # Get or create encryption key for this user
        key_name = f"user_secret_key_{self.user_id[:8]}"

        if not self._key_store.get_key(key_name):
            # Generate and store a random key
            random_key = secrets.token_hex(32)
            self._key_store.store_key(
                name=key_name,
                value=random_key,
                realm=KeyRealm.LOCAL_ONLY,
                description="User secrets encryption key",
            )

        # Encrypt using Fernet via KeyStore's internal encryption
        plaintext = json.dumps(value)
        return self._key_store._encrypt(plaintext)

    def _decrypt_value(self, encrypted: str) -> Any:
        """Decrypt a value using KeyStore."""
        if not self._key_store:
            return json.loads(encrypted)

        decrypted = self._key_store._decrypt(encrypted)
        if decrypted is None:
            return None
        return json.loads(decrypted)

    def _determine_category(self, name: str) -> SensitiveCategory:
        """Auto-determine category based on field name."""
        name_lower = name.lower()

        if (
            name_lower in self.STANDARD_PII_FIELDS
            or "email" in name_lower
            or "birth" in name_lower
        ):
            return SensitiveCategory.PII
        elif (
            name_lower in self.STANDARD_LOCATION_FIELDS
            or "location" in name_lower
            or "coord" in name_lower
        ):
            return SensitiveCategory.LOCATION
        elif (
            name_lower in self.STANDARD_CREDENTIAL_FIELDS
            or "password" in name_lower
            or "token" in name_lower
        ):
            return SensitiveCategory.CREDENTIALS
        elif "barter" in name_lower or "point" in name_lower or "balance" in name_lower:
            return SensitiveCategory.FINANCIAL
        elif "health" in name_lower or "hp" in name_lower or "wellness" in name_lower:
            return SensitiveCategory.HEALTH
        elif (
            "theme" in name_lower
            or "preference" in name_lower
            or "setting" in name_lower
        ):
            return SensitiveCategory.PREFERENCES
        else:
            return SensitiveCategory.GENERAL

    # =========================================================================
    # Public API
    # =========================================================================

    def set(
        self,
        name: str,
        value: Any,
        category: Optional[SensitiveCategory] = None,
        privacy: Optional[PrivacyTier] = None,
    ) -> bool:
        """
        Store a secret value.

        Args:
            name: Field name
            value: Value to store (will be encrypted if PRIVATE in CRYPT mode)
            category: Data category (auto-detected if None)
            privacy: Privacy tier (uses category default if None)

        Returns:
            True if stored successfully
        """
        # Auto-detect category if not provided
        if category is None:
            category = self._determine_category(name)

        # Use default privacy for category if not provided
        if privacy is None:
            privacy = DEFAULT_PRIVACY.get(category, PrivacyTier.PRIVATE)

        # Encrypt if CRYPT mode and PRIVATE tier
        stored_value = value
        is_encrypted = False

        if self.mode == StorageMode.CRYPT and privacy == PrivacyTier.PRIVATE:
            stored_value = self._encrypt_value(value)
            is_encrypted = True

        # Create or update field
        now = datetime.now().isoformat()

        if name in self._secrets:
            field = self._secrets[name]
            field.value = stored_value
            field.modified = now
            field.is_encrypted = is_encrypted
            if category:
                field.category = category
            if privacy:
                field.privacy = privacy
        else:
            field = SecretField(
                name=name,
                value=stored_value,
                category=category,
                privacy=privacy,
                is_encrypted=is_encrypted,
            )
            self._secrets[name] = field

        self._save_secrets()
        self._audit_access("SET", name)

        logger.debug(
            f"[LOCAL] Secret '{name}' stored ({category.value}, {privacy.value})"
        )
        return True

    def get(
        self,
        name: str,
        accessor: str = "owner",
        accessor_role: int = 10,  # Default WIZARD
    ) -> Optional[Any]:
        """
        Retrieve a secret value.

        Args:
            name: Field name
            accessor: ID of accessor (for audit)
            accessor_role: Role level of accessor (for access control)

        Returns:
            Decrypted value or None if not found/unauthorized
        """
        if name not in self._secrets:
            return None

        field = self._secrets[name]

        # Check role authorization
        required_role = TIER_ROLE_REQUIREMENTS.get(field.privacy, 10)
        if accessor_role < required_role and accessor != "owner":
            self._audit_access("DENIED", name, accessor)
            logger.warning(
                f"[LOCAL] Access denied to '{name}' for role {accessor_role}"
            )
            return None

        # Check if accessor is in shared_with list for SHARED tier
        if field.privacy == PrivacyTier.SHARED:
            if accessor != "owner" and accessor not in field.shared_with:
                self._audit_access("DENIED", name, accessor)
                return None

        # Decrypt if needed
        value = field.value
        if field.is_encrypted:
            value = self._decrypt_value(field.value)

        # Update access metadata
        field.accessed = datetime.now().isoformat()
        field.access_count += 1
        self._save_secrets()

        self._audit_access("GET", name, accessor)
        return value

    def delete(self, name: str) -> bool:
        """Delete a secret field."""
        if name not in self._secrets:
            return False

        del self._secrets[name]
        self._save_secrets()
        self._audit_access("DELETE", name)

        return True

    def share(
        self,
        name: str,
        with_user: str,
        expires: Optional[datetime] = None,
    ) -> bool:
        """
        Share a secret with another user/device.

        Only works for SHARED privacy tier fields.

        Args:
            name: Field name
            with_user: User/device ID to share with
            expires: Optional expiration datetime
        """
        if name not in self._secrets:
            return False

        field = self._secrets[name]

        # Only allow sharing for SHARED tier
        if field.privacy != PrivacyTier.SHARED:
            logger.warning(
                f"[LOCAL] Cannot share '{name}' - privacy tier is {field.privacy.value}"
            )
            return False

        if with_user not in field.shared_with:
            field.shared_with.append(with_user)

        if expires:
            field.share_expires = expires.isoformat()

        self._save_secrets()
        self._audit_access("SHARE", name, with_user)

        return True

    def unshare(self, name: str, with_user: str) -> bool:
        """Revoke sharing for a field."""
        if name not in self._secrets:
            return False

        field = self._secrets[name]

        if with_user in field.shared_with:
            field.shared_with.remove(with_user)
            self._save_secrets()
            self._audit_access("UNSHARE", name, with_user)
            return True

        return False

    def set_privacy(self, name: str, privacy: PrivacyTier) -> bool:
        """
        Change privacy tier of a field.

        May trigger encryption/decryption based on new tier.
        """
        if name not in self._secrets:
            return False

        field = self._secrets[name]
        old_privacy = field.privacy

        # Get current decrypted value
        current_value = self.get(name)

        # Update privacy
        field.privacy = privacy

        # Re-encrypt if needed
        if self.mode == StorageMode.CRYPT:
            if privacy == PrivacyTier.PRIVATE and not field.is_encrypted:
                field.value = self._encrypt_value(current_value)
                field.is_encrypted = True
            elif privacy != PrivacyTier.PRIVATE and field.is_encrypted:
                field.value = current_value
                field.is_encrypted = False

        field.modified = datetime.now().isoformat()
        self._save_secrets()

        self._audit_access(f"PRIVACY_CHANGE:{old_privacy.value}->{privacy.value}", name)
        return True

    def list_fields(
        self,
        category: Optional[SensitiveCategory] = None,
        privacy: Optional[PrivacyTier] = None,
        include_values: bool = False,
    ) -> Dict[str, Dict]:
        """
        List all fields with optional filtering.

        Args:
            category: Filter by category
            privacy: Filter by privacy tier
            include_values: Include (masked) values
        """
        result = {}

        for name, field in self._secrets.items():
            if category and field.category != category:
                continue
            if privacy and field.privacy != privacy:
                continue

            info = {
                "category": field.category.value,
                "privacy": field.privacy.value,
                "encrypted": field.is_encrypted,
                "created": field.created,
                "modified": field.modified,
                "access_count": field.access_count,
                "shared_with": len(field.shared_with),
            }

            if include_values:
                value = self.get(name)
                if isinstance(value, str) and len(value) > 4:
                    info["value_hint"] = "****" + value[-4:]
                else:
                    info["value_hint"] = "****"

            result[name] = info

        return result

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries."""
        if not self.audit_file.exists():
            return []

        entries = []
        lines = self.audit_file.read_text().strip().split("\n")

        for line in lines[-limit:]:
            parts = line.split("|")
            if len(parts) >= 5:
                entries.append(
                    {
                        "timestamp": parts[0],
                        "action": parts[1],
                        "field": parts[2],
                        "accessor": parts[3],
                        "mode": parts[4],
                    }
                )

        return entries

    def convert_mode(self, new_mode: StorageMode) -> bool:
        """
        Convert between TOMB and CRYPT modes.

        TOMB → CRYPT: Encrypts all PRIVATE fields
        CRYPT → TOMB: Decrypts all fields (loses encryption)
        """
        if new_mode == self.mode:
            return True

        logger.info(f"[LOCAL] Converting from {self.mode.value} to {new_mode.value}")

        # Get all decrypted values
        decrypted_values = {}
        for name in self._secrets:
            decrypted_values[name] = self.get(name)

        # Change mode
        old_mode = self.mode
        self.mode = new_mode

        # Update KeyStore reference
        if new_mode == StorageMode.CRYPT:
            self._key_store = KeyStore(realm=KeyRealm.LOCAL_ONLY)
        else:
            self._key_store = None

        # Update secrets file path
        self.secrets_file = self.user_dir / f"secrets_{new_mode.value}.json"

        # Re-store all values (will encrypt/decrypt as appropriate)
        for name, field in list(self._secrets.items()):
            self.set(
                name=name,
                value=decrypted_values[name],
                category=field.category,
                privacy=field.privacy,
            )

        self._audit_access(f"MODE_CONVERT:{old_mode.value}->{new_mode.value}", "*")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get secrets manager status."""
        categories = {}
        privacies = {}

        for field in self._secrets.values():
            cat = field.category.value
            priv = field.privacy.value
            categories[cat] = categories.get(cat, 0) + 1
            privacies[priv] = privacies.get(priv, 0) + 1

        return {
            "user_id_hash": hashlib.sha256(self.user_id.encode()).hexdigest()[:16],
            "mode": self.mode.value,
            "total_fields": len(self._secrets),
            "by_category": categories,
            "by_privacy": privacies,
            "crypto_available": CRYPTO_AVAILABLE,
            "has_keystore": self._key_store is not None,
        }


# =============================================================================
# Convenience Functions
# =============================================================================


def get_user_secrets(
    user_id: str, mode: StorageMode = StorageMode.CRYPT
) -> UserSecretsManager:
    """Get or create a UserSecretsManager for a user."""
    return UserSecretsManager(user_id=user_id, mode=mode)


def store_user_secret(
    user_id: str,
    name: str,
    value: Any,
    category: Optional[SensitiveCategory] = None,
    privacy: Optional[PrivacyTier] = None,
) -> bool:
    """Convenience function to store a user secret."""
    manager = get_user_secrets(user_id)
    return manager.set(name, value, category, privacy)


def get_user_secret(user_id: str, name: str) -> Optional[Any]:
    """Convenience function to get a user secret."""
    manager = get_user_secrets(user_id)
    return manager.get(name)


# =============================================================================
# CLI Interface
# =============================================================================


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="uDOS User Secrets Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Store a secret
  python -m core.security.user_secrets set email user@example.com --user myuser
  
  # Get a secret
  python -m core.security.user_secrets get email --user myuser
  
  # List all secrets
  python -m core.security.user_secrets list --user myuser
  
  # Convert to TOMB mode
  python -m core.security.user_secrets convert tomb --user myuser
""",
    )

    parser.add_argument("--user", "-u", required=True, help="User ID")
    parser.add_argument("--mode", "-m", choices=["crypt", "tomb"], default="crypt")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # set command
    set_parser = subparsers.add_parser("set", help="Store a secret")
    set_parser.add_argument("name", help="Field name")
    set_parser.add_argument("value", nargs="?", help="Value (prompts if not provided)")
    set_parser.add_argument(
        "--privacy", "-p", choices=["public", "shared", "private", "system"]
    )
    set_parser.add_argument(
        "--category",
        "-c",
        choices=["pii", "location", "creds", "financial", "health", "prefs", "general"],
    )

    # get command
    get_parser = subparsers.add_parser("get", help="Get a secret")
    get_parser.add_argument("name", help="Field name")

    # list command
    list_parser = subparsers.add_parser("list", help="List secrets")
    list_parser.add_argument(
        "--values", "-v", action="store_true", help="Show value hints"
    )

    # share command
    share_parser = subparsers.add_parser("share", help="Share a secret")
    share_parser.add_argument("name", help="Field name")
    share_parser.add_argument("with_user", help="User to share with")

    # convert command
    convert_parser = subparsers.add_parser("convert", help="Convert storage mode")
    convert_parser.add_argument("target_mode", choices=["crypt", "tomb"])

    # status command
    status_parser = subparsers.add_parser("status", help="Show status")

    # audit command
    audit_parser = subparsers.add_parser("audit", help="Show audit log")
    audit_parser.add_argument("--limit", "-l", type=int, default=20)

    args = parser.parse_args()

    mode = StorageMode.CRYPT if args.mode == "crypt" else StorageMode.TOMB
    manager = UserSecretsManager(user_id=args.user, mode=mode)

    if args.command == "set":
        value = args.value
        if not value:
            import getpass

            value = getpass.getpass(f"Enter value for '{args.name}': ")

        privacy = PrivacyTier(args.privacy) if args.privacy else None
        category = SensitiveCategory(args.category) if args.category else None

        manager.set(args.name, value, category, privacy)
        print(f"✅ Secret '{args.name}' stored")

    elif args.command == "get":
        value = manager.get(args.name)
        if value is not None:
            print(value)
        else:
            print(f"❌ Secret '{args.name}' not found")

    elif args.command == "list":
        fields = manager.list_fields(include_values=args.values)
        print(json.dumps(fields, indent=2))

    elif args.command == "share":
        if manager.share(args.name, args.with_user):
            print(f"✅ '{args.name}' shared with {args.with_user}")
        else:
            print(f"❌ Could not share '{args.name}'")

    elif args.command == "convert":
        target = StorageMode.CRYPT if args.target_mode == "crypt" else StorageMode.TOMB
        if manager.convert_mode(target):
            print(f"✅ Converted to {target.value} mode")
        else:
            print(f"❌ Conversion failed")

    elif args.command == "status":
        status = manager.get_status()
        print(json.dumps(status, indent=2))

    elif args.command == "audit":
        log = manager.get_audit_log(args.limit)
        for entry in log:
            print(
                f"{entry['timestamp']} | {entry['action']} | {entry['field']} | {entry['accessor']}"
            )


if __name__ == "__main__":
    main()
