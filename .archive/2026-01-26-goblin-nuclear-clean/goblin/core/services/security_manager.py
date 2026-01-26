"""
Security Manager

Handles credential storage, NFC authentication, and keychain integration.
Uses OS keychain when available, falls back to encrypted files.
"""

from pathlib import Path
import os
import json
import hashlib
from typing import Optional, Dict, Any

# Try to import keyring, use fallback if not available
try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    import bcrypt

    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

from ..config.paths import get_credentials_path


class SecurityManager:
    """
    Manages credentials, NFC authentication, and keychain integration.

    Uses OS keychain when available:
    - macOS: Keychain Services
    - Linux: libsecret/gnome-keyring
    - Windows: Credential Manager
    - TinyCore: Encrypted file fallback
    """

    KEYRING_SERVICE = "com.udos.alpha"

    def __init__(self):
        self.creds_dir = get_credentials_path()
        self.encrypted_store = self.creds_dir / "keys.enc"
        self.nfc_pubkey_file = self.creds_dir / "nfc_pubkey"

        # Ensure credentials directory exists with correct permissions
        self.creds_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    def store_credential(self, key: str, value: str) -> bool:
        """
        Store credential securely.

        Tries OS keychain first, falls back to encrypted file.

        Args:
            key: Credential identifier (e.g., 'gmail_app_password')
            value: Credential value

        Returns:
            True if stored successfully
        """
        # Try OS keychain first
        if KEYRING_AVAILABLE:
            try:
                keyring.set_password(self.KEYRING_SERVICE, key, value)
                return True
            except Exception as e:
                print(f"[WARN] Keyring storage failed: {e}, using encrypted file")

        # Fallback: encrypted file
        return self._store_encrypted(key, value)

    def get_credential(self, key: str) -> Optional[str]:
        """
        Retrieve credential.

        Tries OS keychain first, falls back to encrypted file.

        Args:
            key: Credential identifier

        Returns:
            Credential value or None if not found
        """
        # Try OS keychain first
        if KEYRING_AVAILABLE:
            try:
                value = keyring.get_password(self.KEYRING_SERVICE, key)
                if value is not None:
                    return value
            except Exception:
                pass

        # Fallback: encrypted file
        return self._load_encrypted(key)

    def delete_credential(self, key: str) -> bool:
        """
        Delete credential.

        Args:
            key: Credential identifier

        Returns:
            True if deleted successfully from any store
        """
        deleted = False

        # Try OS keychain
        if KEYRING_AVAILABLE:
            try:
                keyring.delete_password(self.KEYRING_SERVICE, key)
                deleted = True  # Keychain deletion succeeded
            except Exception:
                pass

        # Also remove from encrypted file
        if self._delete_encrypted(key):
            deleted = True

        return deleted

    def _store_encrypted(self, key: str, value: str) -> bool:
        """
        Store credential in encrypted file (fallback).

        WARNING: This is a basic implementation. In production,
        use proper encryption with a master password or device key.
        """
        try:
            # Load existing credentials
            creds = self._load_encrypted_store()

            # Add/update credential
            creds[key] = self._simple_encrypt(value)

            # Save
            self.encrypted_store.write_text(json.dumps(creds))
            os.chmod(self.encrypted_store, 0o600)

            return True
        except Exception as e:
            print(f"[ERROR] Failed to store credential: {e}")
            return False

    def _load_encrypted(self, key: str) -> Optional[str]:
        """Load credential from encrypted file."""
        try:
            creds = self._load_encrypted_store()
            encrypted_value = creds.get(key)

            if encrypted_value:
                return self._simple_decrypt(encrypted_value)

            return None
        except Exception:
            return None

    def _delete_encrypted(self, key: str) -> bool:
        """Delete credential from encrypted file."""
        try:
            creds = self._load_encrypted_store()

            if key in creds:
                del creds[key]
                self.encrypted_store.write_text(json.dumps(creds))
                return True

            return False
        except Exception:
            return False

    def _load_encrypted_store(self) -> Dict[str, str]:
        """Load encrypted credential store."""
        if self.encrypted_store.exists():
            try:
                return json.loads(self.encrypted_store.read_text())
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

    def _simple_encrypt(self, value: str) -> str:
        """
        Simple obfuscation (NOT SECURE - placeholder).

        TODO: Replace with proper encryption:
        - Use cryptography.fernet with device-specific key
        - Or prompt for master password
        - Or use hardware key (NFC ring)
        """
        # Base64 encoding as placeholder
        import base64

        return base64.b64encode(value.encode()).decode()

    def _simple_decrypt(self, encrypted: str) -> str:
        """Simple deobfuscation (matches _simple_encrypt)."""
        import base64

        return base64.b64decode(encrypted.encode()).decode()

    # NFC Ring Authentication

    def register_nfc_ring(self, pubkey: bytes) -> bool:
        """
        Register NFC ring public key.

        Args:
            pubkey: NFC ring public key (raw bytes)

        Returns:
            True if registered successfully
        """
        try:
            self.nfc_pubkey_file.write_bytes(pubkey)
            os.chmod(self.nfc_pubkey_file, 0o600)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to register NFC ring: {e}")
            return False

    def has_nfc_ring(self) -> bool:
        """Check if NFC ring is registered."""
        return self.nfc_pubkey_file.exists()

    def challenge_nfc_ring(self, challenge: bytes) -> Optional[bytes]:
        """
        Challenge/response authentication with NFC ring.

        Args:
            challenge: Random challenge bytes

        Returns:
            Signature from NFC ring, or None if failed

        TODO: Implement actual NFC device communication
        """
        if not self.has_nfc_ring():
            return None

        # TODO: Implement NFC device communication
        # 1. Send challenge to NFC device via /dev/nfc0
        # 2. Receive signed response
        # 3. Verify signature with stored public key

        print("[WARN] NFC authentication not yet implemented")
        return None

    # Password Hashing (for optional password auth)

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.

        Args:
            password: Plaintext password

        Returns:
            Hashed password string
        """
        if not BCRYPT_AVAILABLE:
            # Fallback to sha256 (not recommended)
            return hashlib.sha256(password.encode()).hexdigest()

        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.

        Args:
            password: Plaintext password
            hashed: Hashed password from storage

        Returns:
            True if password matches
        """
        if not BCRYPT_AVAILABLE:
            # Fallback comparison
            return hashlib.sha256(password.encode()).hexdigest() == hashed

        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception:
            return False


# Singleton instance
_security_manager = None


def get_security_manager() -> SecurityManager:
    """Get singleton SecurityManager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager
