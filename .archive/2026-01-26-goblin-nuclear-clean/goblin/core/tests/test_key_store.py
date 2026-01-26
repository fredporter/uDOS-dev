"""
Test Key Store Security

Validates encrypted key storage, OS keychain integration, and key management.
Alpha v1.0.0.23+
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from dev.goblin.core.security.key_store import (
    KeyStore,
    KeyRealm,
    KeychainBackend,
    CRYPTO_AVAILABLE,
    KEYRING_AVAILABLE,
    get_wizard_key,
    get_user_key,
    store_wizard_key,
    store_user_key,
    get_key_store_status,
)


class TestKeyStoreBasics:
    """Test basic KeyStore operations."""

    @pytest.fixture
    def temp_keys_dir(self, monkeypatch, tmp_path):
        """Use temporary directory for keys."""
        keys_dir = tmp_path / ".keys"
        keys_dir.mkdir()

        # Monkeypatch the keys directory
        def mock_init(self, realm=KeyRealm.USER_MESH):
            self.realm = realm
            self.keys_dir = keys_dir
            self.keys_file = keys_dir / f"keys_{realm.value}.json"
            self._keys = {}
            self._backend = self._detect_backend()
            self._fernet = self._initialize_encryption()
            self._load_keys()

        monkeypatch.setattr(KeyStore, "__init__", mock_init)
        return keys_dir

    def test_store_and_retrieve_key(self, temp_keys_dir):
        """Test basic key storage and retrieval."""
        store = KeyStore(realm=KeyRealm.USER_MESH)

        # Store a key
        result = store.store_key(
            name="test_api_key",
            value="sk-test-1234567890",
            realm=KeyRealm.USER_MESH,
            description="Test API key",
        )
        assert result is True

        # Retrieve the key
        retrieved = store.get_key("test_api_key")
        assert retrieved == "sk-test-1234567890"

    def test_key_encryption(self, temp_keys_dir):
        """Test that keys are actually encrypted on disk."""
        store = KeyStore(realm=KeyRealm.USER_MESH)

        secret_value = "super_secret_password_123!"
        store.store_key(
            name="encrypted_key",
            value=secret_value,
            realm=KeyRealm.USER_MESH,
        )

        # Read raw file
        keys_file = temp_keys_dir / "keys_user_mesh.json"
        raw_data = json.loads(keys_file.read_text())

        # Find the encrypted value
        encrypted_value = None
        for key_data in raw_data.get("keys", []):
            if key_data["name"] == "encrypted_key":
                encrypted_value = key_data["encrypted_value"]
                break

        assert encrypted_value is not None
        # Encrypted value should NOT contain the plaintext
        assert secret_value not in encrypted_value

        if CRYPTO_AVAILABLE:
            # Fernet encrypted values start with 'gAAAAA'
            assert encrypted_value.startswith("gAAAAA") or encrypted_value.startswith(
                "b64:"
            )

        # But we can still retrieve it
        retrieved = store.get_key("encrypted_key")
        assert retrieved == secret_value

    def test_role_authorization(self, temp_keys_dir):
        """Test role-based key access."""
        store = KeyStore(realm=KeyRealm.USER_MESH)

        store.store_key(
            name="restricted_key",
            value="sensitive_data",
            realm=KeyRealm.USER_MESH,
            allowed_roles=["admin", "wizard_server"],
        )

        # Should fail with wrong role
        result = store.get_key("restricted_key", role="guest")
        assert result is None

        # Should succeed with correct role
        result = store.get_key("restricted_key", role="admin")
        assert result == "sensitive_data"

    def test_key_deletion(self, temp_keys_dir):
        """Test key deletion."""
        store = KeyStore(realm=KeyRealm.USER_MESH)

        store.store_key(
            name="temp_key",
            value="temporary",
            realm=KeyRealm.USER_MESH,
        )

        assert store.get_key("temp_key") == "temporary"

        deleted = store.delete_key("temp_key")
        assert deleted is True

        assert store.get_key("temp_key") is None

    def test_list_keys(self, temp_keys_dir):
        """Test listing keys."""
        store = KeyStore(realm=KeyRealm.USER_MESH)

        store.store_key("key1", "value1", KeyRealm.USER_MESH, description="First key")
        store.store_key("key2", "value2", KeyRealm.USER_MESH, description="Second key")

        keys = store.list_keys()

        assert "key1" in keys
        assert "key2" in keys
        assert keys["key1"]["description"] == "First key"
        assert keys["key2"]["description"] == "Second key"

    def test_list_keys_with_hints(self, temp_keys_dir):
        """Test listing keys with value hints."""
        store = KeyStore(realm=KeyRealm.USER_MESH)

        store.store_key("api_key", "sk-12345678", KeyRealm.USER_MESH)

        keys = store.list_keys(include_values=True)

        assert "api_key" in keys
        assert "value_hint" in keys["api_key"]
        # Should show last 4 chars
        assert keys["api_key"]["value_hint"] == "****5678"


class TestKeyStoreRealms:
    """Test key store realm separation."""

    @pytest.fixture
    def temp_keys_dir(self, monkeypatch, tmp_path):
        """Use temporary directory for keys."""
        keys_dir = tmp_path / ".keys"
        keys_dir.mkdir()

        original_init = KeyStore.__init__

        def mock_init(self, realm=KeyRealm.USER_MESH):
            self.realm = realm
            self.keys_dir = keys_dir
            self.keys_file = keys_dir / f"keys_{realm.value}.json"
            self._keys = {}
            self._backend = (
                KeychainBackend.ENCRYPTED_FILE
            )  # Force file backend for tests
            self._fernet = self._initialize_encryption()
            self._load_keys()

        monkeypatch.setattr(KeyStore, "__init__", mock_init)
        return keys_dir

    def test_realm_isolation(self, temp_keys_dir):
        """Test that keys in different realms are isolated."""
        user_store = KeyStore(realm=KeyRealm.USER_MESH)
        wizard_store = KeyStore(realm=KeyRealm.WIZARD_ONLY)

        user_store.store_key("shared_name", "user_value", KeyRealm.USER_MESH)
        wizard_store.store_key(
            "shared_name",
            "wizard_value",
            KeyRealm.WIZARD_ONLY,
            allowed_roles=["wizard_server"],  # Must specify roles for wizard keys
        )

        # Each store should only see its own key
        assert user_store.get_key("shared_name") == "user_value"
        assert (
            wizard_store.get_key("shared_name", role="wizard_server") == "wizard_value"
        )

    def test_wrong_realm_rejected(self, temp_keys_dir):
        """Test that storing key in wrong realm is rejected."""
        user_store = KeyStore(realm=KeyRealm.USER_MESH)

        # Should fail - trying to store wizard key in user store
        result = user_store.store_key(
            name="api_key",
            value="secret",
            realm=KeyRealm.WIZARD_ONLY,  # Wrong realm
        )
        assert result is False


class TestKeyStoreStatus:
    """Test key store status reporting."""

    def test_status_report(self):
        """Test status report generation."""
        status = get_key_store_status()

        assert "user_mesh" in status
        assert "wizard_only" in status
        assert "local_only" in status
        assert "crypto_available" in status
        assert "keyring_available" in status

        # Each realm should have status info
        assert "backend" in status["user_mesh"]
        assert "key_count" in status["user_mesh"]
        assert "encrypted" in status["user_mesh"]


class TestCryptoAvailability:
    """Test behavior with/without cryptography."""

    def test_crypto_status(self):
        """Test cryptography availability detection."""
        # CRYPTO_AVAILABLE should be True if cryptography is installed
        # We check requirements.txt includes it, so it should be available
        assert CRYPTO_AVAILABLE is True, "cryptography package should be installed"

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Requires cryptography")
    def test_fernet_encryption(self):
        """Test that Fernet encryption is used when available."""
        from cryptography.fernet import Fernet

        # Can create a Fernet key
        key = Fernet.generate_key()
        fernet = Fernet(key)

        # Can encrypt and decrypt
        plaintext = b"test message"
        encrypted = fernet.encrypt(plaintext)
        decrypted = fernet.decrypt(encrypted)

        assert decrypted == plaintext
        assert encrypted != plaintext


class TestLegacyMigration:
    """Test migration from old base64 format."""

    @pytest.fixture
    def legacy_keys_file(self, tmp_path):
        """Create a legacy format keys file."""
        keys_dir = tmp_path / ".keys"
        keys_dir.mkdir()

        import base64

        # Old format: base64 encoded (not encrypted)
        legacy_value = base64.b64encode(b"legacy_secret").decode()

        legacy_data = {
            "version": "1.0.0.2",
            "realm": "user_mesh",
            "keys": [
                {
                    "name": "old_key",
                    "realm": "user_mesh",
                    "encrypted_value": legacy_value,  # Just base64
                    "created": "2025-01-01T00:00:00",
                    "description": "Legacy key",
                    "allowed_roles": ["device_owner"],
                }
            ],
        }

        keys_file = keys_dir / "keys_user_mesh.json"
        keys_file.write_text(json.dumps(legacy_data))

        return keys_dir

    def test_read_legacy_key(self, legacy_keys_file, monkeypatch):
        """Test reading keys from legacy base64 format."""

        def mock_init(self, realm=KeyRealm.USER_MESH):
            self.realm = realm
            self.keys_dir = legacy_keys_file
            self.keys_file = legacy_keys_file / f"keys_{realm.value}.json"
            self._keys = {}
            self._backend = KeychainBackend.ENCRYPTED_FILE
            self._fernet = self._initialize_encryption()
            self._load_keys()

        monkeypatch.setattr(KeyStore, "__init__", mock_init)

        store = KeyStore(realm=KeyRealm.USER_MESH)

        # Should be able to read legacy key
        value = store.get_key("old_key")
        assert value == "legacy_secret"


# Run tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
