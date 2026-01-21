"""
Test User Secrets Manager

Validates encrypted user secrets storage, privacy tiers, and sharing.
Alpha v1.0.0.24+
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from dev.goblin.core.security.user_secrets import (
    UserSecretsManager,
    StorageMode,
    PrivacyTier,
    SensitiveCategory,
    SecretField,
    get_user_secrets,
    store_user_secret,
    get_user_secret,
    CRYPTO_AVAILABLE,
)


class TestUserSecretsBasics:
    """Test basic UserSecrets operations."""

    @pytest.fixture
    def temp_secrets_dir(self, tmp_path):
        """Create temporary directory for secrets."""
        return tmp_path / "secrets"

    @pytest.fixture
    def manager(self, temp_secrets_dir):
        """Create a manager with temp storage."""
        return UserSecretsManager(
            user_id="test_user_123",
            mode=StorageMode.CRYPT,
            base_path=temp_secrets_dir,
        )

    def test_store_and_retrieve_secret(self, manager):
        """Test basic secret storage and retrieval."""
        manager.set("test_key", "test_value")

        result = manager.get("test_key")
        assert result == "test_value"

    def test_auto_category_detection(self, manager):
        """Test automatic category detection from field names."""
        manager.set("email", "user@example.com")
        manager.set("current_location", "NY, USA")
        manager.set("password", "secret123")
        manager.set("barter_points", 100)
        manager.set("user_theme", "dark")
        manager.set("random_data", "value")  # Generic name -> general

        fields = manager.list_fields()

        assert fields["email"]["category"] == "pii"
        assert fields["current_location"]["category"] == "location"
        assert fields["password"]["category"] == "creds"
        assert fields["barter_points"]["category"] == "financial"
        assert fields["user_theme"]["category"] == "prefs"
        assert fields["random_data"]["category"] == "general"

    def test_auto_privacy_from_category(self, manager):
        """Test automatic privacy tier based on category."""
        manager.set("email", "user@example.com")  # PII -> PRIVATE
        manager.set("user_theme", "dark")  # PREFS -> SHARED

        fields = manager.list_fields()

        assert fields["email"]["privacy"] == "private"
        assert fields["user_theme"]["privacy"] == "shared"

    def test_explicit_privacy_override(self, manager):
        """Test explicit privacy tier override."""
        manager.set(
            "public_email",
            "public@example.com",
            category=SensitiveCategory.PII,
            privacy=PrivacyTier.PUBLIC,
        )

        fields = manager.list_fields()
        assert fields["public_email"]["privacy"] == "public"

    def test_delete_secret(self, manager):
        """Test secret deletion."""
        manager.set("temp_key", "temp_value")
        assert manager.get("temp_key") == "temp_value"

        manager.delete("temp_key")
        assert manager.get("temp_key") is None


class TestEncryption:
    """Test encryption functionality."""

    @pytest.fixture
    def crypt_manager(self, tmp_path):
        """Create CRYPT mode manager."""
        return UserSecretsManager(
            user_id="crypt_user",
            mode=StorageMode.CRYPT,
            base_path=tmp_path / "secrets",
        )

    @pytest.fixture
    def tomb_manager(self, tmp_path):
        """Create TOMB mode manager."""
        return UserSecretsManager(
            user_id="tomb_user",
            mode=StorageMode.TOMB,
            base_path=tmp_path / "secrets",
        )

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Requires cryptography")
    def test_crypt_mode_encrypts_private(self, crypt_manager):
        """Test that CRYPT mode encrypts PRIVATE tier data."""
        secret_value = "super_secret_password"
        crypt_manager.set("password", secret_value)

        # Check raw storage
        fields = crypt_manager.list_fields()
        assert fields["password"]["encrypted"] is True

        # Can still retrieve decrypted
        assert crypt_manager.get("password") == secret_value

    def test_tomb_mode_no_encryption(self, tomb_manager):
        """Test that TOMB mode stores without encryption."""
        tomb_manager.set("password", "plaintext_password")

        fields = tomb_manager.list_fields()
        assert fields["password"]["encrypted"] is False

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Requires cryptography")
    def test_encryption_on_disk(self, crypt_manager, tmp_path):
        """Test that encrypted values are not readable on disk."""
        secret_value = "my_secret_123!"
        crypt_manager.set("secret_key", secret_value, privacy=PrivacyTier.PRIVATE)

        # Read raw file
        secrets_dir = tmp_path / "secrets"
        files = list(secrets_dir.rglob("secrets_crypt.json"))
        assert len(files) == 1

        raw_data = files[0].read_text()

        # Plaintext should NOT appear in file
        assert secret_value not in raw_data


class TestPrivacyTiers:
    """Test privacy tier access control."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create manager with test data."""
        mgr = UserSecretsManager(
            user_id="privacy_test_user",
            mode=StorageMode.CRYPT,
            base_path=tmp_path / "secrets",
        )

        mgr.set("public_field", "public_value", privacy=PrivacyTier.PUBLIC)
        mgr.set("shared_field", "shared_value", privacy=PrivacyTier.SHARED)
        mgr.set("private_field", "private_value", privacy=PrivacyTier.PRIVATE)
        mgr.set("system_field", "system_value", privacy=PrivacyTier.SYSTEM)

        return mgr

    def test_owner_access_all(self, manager):
        """Test owner can access all tiers."""
        assert manager.get("public_field", accessor="owner") == "public_value"
        assert manager.get("shared_field", accessor="owner") == "shared_value"
        assert manager.get("private_field", accessor="owner") == "private_value"
        assert manager.get("system_field", accessor="owner") == "system_value"

    def test_low_role_denied_private(self, manager):
        """Test low role cannot access PRIVATE tier."""
        # Role 2 (TOMB) can access PUBLIC (requires role 2+)
        result = manager.get("public_field", accessor="guest", accessor_role=2)
        assert result == "public_value"

        # Role 1 (GHOST) cannot access PUBLIC (requires role 2+)
        result = manager.get("public_field", accessor="ghost", accessor_role=1)
        assert result is None

        # Role 2 cannot access PRIVATE (requires role 5+)
        result = manager.get("private_field", accessor="guest", accessor_role=2)
        assert result is None

    def test_system_requires_wizard(self, manager):
        """Test SYSTEM tier requires WIZARD role (10)."""
        # Role 5 (KNIGHT) cannot access SYSTEM
        result = manager.get("system_field", accessor="knight", accessor_role=5)
        assert result is None

        # Role 10 (WIZARD) can access SYSTEM
        result = manager.get("system_field", accessor="wizard", accessor_role=10)
        assert result == "system_value"


class TestSharing:
    """Test sharing functionality."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create manager with shareable data."""
        mgr = UserSecretsManager(
            user_id="sharing_test_user",
            mode=StorageMode.CRYPT,
            base_path=tmp_path / "secrets",
        )

        mgr.set("shareable_data", "shared_content", privacy=PrivacyTier.SHARED)
        mgr.set("private_data", "private_content", privacy=PrivacyTier.PRIVATE)

        return mgr

    def test_share_with_user(self, manager):
        """Test sharing data with another user."""
        result = manager.share("shareable_data", "friend_user_123")
        assert result is True

        # Check shared_with list
        fields = manager.list_fields()
        assert fields["shareable_data"]["shared_with"] == 1

    def test_cannot_share_private(self, manager):
        """Test cannot share PRIVATE tier data."""
        result = manager.share("private_data", "friend_user_123")
        assert result is False

    def test_shared_user_can_access(self, manager):
        """Test shared user can access SHARED tier data."""
        manager.share("shareable_data", "friend_user_123")

        # Friend can access (SHARED requires role 4 / CRYPT)
        result = manager.get(
            "shareable_data", accessor="friend_user_123", accessor_role=4
        )
        assert result == "shared_content"

        # Non-shared user cannot
        result = manager.get("shareable_data", accessor="stranger", accessor_role=4)
        assert result is None

    def test_unshare(self, manager):
        """Test revoking share access."""
        manager.share("shareable_data", "friend_user_123")

        # Friend can access (SHARED requires role 4 / CRYPT)
        assert (
            manager.get("shareable_data", accessor="friend_user_123", accessor_role=4)
            is not None
        )

        # Revoke
        manager.unshare("shareable_data", "friend_user_123")

        # Friend cannot access anymore
        assert (
            manager.get("shareable_data", accessor="friend_user_123", accessor_role=4)
            is None
        )


class TestModeConversion:
    """Test TOMB ↔ CRYPT mode conversion."""

    @pytest.fixture
    def crypt_manager(self, tmp_path):
        """Create CRYPT mode manager with data."""
        mgr = UserSecretsManager(
            user_id="convert_test_user",
            mode=StorageMode.CRYPT,
            base_path=tmp_path / "secrets",
        )

        mgr.set("email", "user@example.com")
        mgr.set("password", "secret123")
        mgr.set("theme", "dark")

        return mgr

    @pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Requires cryptography")
    def test_crypt_to_tomb(self, crypt_manager):
        """Test converting from CRYPT to TOMB."""
        # Verify encrypted
        fields = crypt_manager.list_fields()
        assert fields["password"]["encrypted"] is True

        # Convert
        crypt_manager.convert_mode(StorageMode.TOMB)

        # Verify no longer encrypted
        assert crypt_manager.mode == StorageMode.TOMB
        fields = crypt_manager.list_fields()
        assert fields["password"]["encrypted"] is False

        # Data still accessible
        assert crypt_manager.get("password") == "secret123"

    def test_tomb_to_crypt(self, tmp_path):
        """Test converting from TOMB to CRYPT."""
        # Start in TOMB mode
        mgr = UserSecretsManager(
            user_id="tomb_convert_user",
            mode=StorageMode.TOMB,
            base_path=tmp_path / "secrets",
        )

        mgr.set("password", "plaintext")
        assert mgr.list_fields()["password"]["encrypted"] is False

        # Convert to CRYPT
        mgr.convert_mode(StorageMode.CRYPT)

        # Verify encrypted
        assert mgr.mode == StorageMode.CRYPT
        if CRYPTO_AVAILABLE:
            assert mgr.list_fields()["password"]["encrypted"] is True

        # Data still accessible
        assert mgr.get("password") == "plaintext"


class TestAuditLog:
    """Test audit logging."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create manager."""
        return UserSecretsManager(
            user_id="audit_test_user",
            mode=StorageMode.CRYPT,
            base_path=tmp_path / "secrets",
        )

    def test_audit_on_set(self, manager):
        """Test SET operations are audited."""
        manager.set("test_key", "test_value")

        log = manager.get_audit_log()
        assert len(log) >= 1
        assert any(e["action"] == "SET" and e["field"] == "test_key" for e in log)

    def test_audit_on_get(self, manager):
        """Test GET operations are audited."""
        manager.set("test_key", "test_value")
        manager.get("test_key")

        log = manager.get_audit_log()
        assert any(e["action"] == "GET" and e["field"] == "test_key" for e in log)

    def test_audit_on_share(self, manager):
        """Test SHARE operations are audited."""
        manager.set("shared_key", "shared_value", privacy=PrivacyTier.SHARED)
        manager.share("shared_key", "friend_user")

        log = manager.get_audit_log()
        assert any(
            e["action"] == "SHARE" and e["accessor"] == "friend_user" for e in log
        )

    def test_audit_on_denied(self, manager):
        """Test DENIED operations are audited."""
        manager.set("private_key", "private_value", privacy=PrivacyTier.PRIVATE)
        manager.get("private_key", accessor="guest", accessor_role=1)

        log = manager.get_audit_log()
        assert any(e["action"] == "DENIED" for e in log)


class TestStatus:
    """Test status reporting."""

    def test_status_report(self, tmp_path):
        """Test status report generation."""
        mgr = UserSecretsManager(
            user_id="status_test_user",
            mode=StorageMode.CRYPT,
            base_path=tmp_path / "secrets",
        )

        mgr.set("email", "user@example.com")
        mgr.set("location", "NYC")
        mgr.set("theme", "dark")

        status = mgr.get_status()

        assert status["mode"] == "crypt"
        assert status["total_fields"] == 3
        assert "by_category" in status
        assert "by_privacy" in status


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_store_and_get_user_secret(self, tmp_path, monkeypatch):
        """Test convenience functions."""
        # Monkeypatch the base path
        import dev.goblin.core.security.user_secrets as user_secrets_module

        original_class = user_secrets_module.UserSecretsManager

        class MockManager(original_class):
            def __init__(self, user_id, mode=StorageMode.CRYPT, base_path=None):
                super().__init__(user_id, mode, tmp_path / "secrets")

        monkeypatch.setattr(user_secrets_module, "UserSecretsManager", MockManager)

        # Test convenience functions
        result = store_user_secret("test_user", "api_key", "abc123")
        assert result is True

        value = get_user_secret("test_user", "api_key")
        assert value == "abc123"


# Run tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
