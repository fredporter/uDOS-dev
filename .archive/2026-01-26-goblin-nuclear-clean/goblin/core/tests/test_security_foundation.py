"""
Test Security Foundation

Validates user directory structure, permissions, and security manager.
"""

import sys
import os
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dev.goblin.core.config import init_user_directory, get_user_path, get_config_path
from dev.goblin.core.services.security_manager import get_security_manager


def test_user_directory_structure():
    """Test user directory initialization."""
    print("Testing user directory structure...")

    # Initialize
    init_user_directory()

    # Check directories exist
    udos_home = Path.home() / ".udos"

    required_dirs = [
        "config",
        "memory",
        "memory/sandbox",
        "memory/sandbox/scripts",
        "memory/logs",
        ".credentials",
    ]

    for dir_path in required_dirs:
        full_path = udos_home / dir_path
        assert full_path.exists(), f"Missing directory: {dir_path}"
        print(f"  ✓ {dir_path} exists")

    # Check permissions
    config_dir = udos_home / "config"
    config_mode = oct(os.stat(config_dir).st_mode)[-3:]
    assert config_mode == "700", f"Config dir permissions incorrect: {config_mode}"
    print(f"  ✓ Config permissions correct (700)")

    creds_dir = udos_home / ".credentials"
    creds_mode = oct(os.stat(creds_dir).st_mode)[-3:]
    assert creds_mode == "700", f"Credentials dir permissions incorrect: {creds_mode}"
    print(f"  ✓ Credentials permissions correct (700)")

    print("✅ User directory structure validated\n")


def test_path_helpers():
    """Test path helper functions."""
    print("Testing path helpers...")

    # User paths
    logs_path = get_user_path("logs")
    assert logs_path.exists()
    assert "memory/logs" in str(logs_path)
    print(f"  ✓ User path: {logs_path}")

    # Config paths
    config_path = get_config_path("user.json")
    assert config_path.exists()
    assert "config" in str(config_path)
    print(f"  ✓ Config path: {config_path}")

    print("✅ Path helpers validated\n")


def test_security_manager():
    """Test security manager credential storage."""
    print("Testing security manager...")

    security = get_security_manager()

    # Store credential
    test_key = "test_credential"
    test_value = "secret_value_12345"

    success = security.store_credential(test_key, test_value)
    assert success, "Failed to store credential"
    print(f"  ✓ Credential stored")

    # Retrieve credential
    retrieved = security.get_credential(test_key)
    assert retrieved == test_value, f"Retrieved value doesn't match: {retrieved}"
    print(f"  ✓ Credential retrieved correctly")

    # Delete credential
    deleted = security.delete_credential(test_key)
    assert deleted, "Failed to delete credential"
    print(f"  ✓ Credential deleted")

    # Verify deleted
    after_delete = security.get_credential(test_key)
    assert after_delete is None, "Credential still exists after deletion"
    print(f"  ✓ Credential properly removed")

    print("✅ Security manager validated\n")


def test_password_hashing():
    """Test password hashing."""
    print("Testing password hashing...")

    security = get_security_manager()

    password = "test_password_123"
    hashed = security.hash_password(password)

    assert len(hashed) > 20, "Hash too short"
    print(f"  ✓ Password hashed")

    # Verify correct password
    valid = security.verify_password(password, hashed)
    assert valid, "Password verification failed"
    print(f"  ✓ Correct password verified")

    # Verify wrong password
    invalid = security.verify_password("wrong_password", hashed)
    assert not invalid, "Wrong password validated"
    print(f"  ✓ Wrong password rejected")

    print("✅ Password hashing validated\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SECURITY FOUNDATION TEST SUITE")
    print("=" * 60)
    print()

    try:
        test_user_directory_structure()
        test_path_helpers()
        test_security_manager()
        test_password_hashing()

        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("User directory: ~/.udos/")
        print("Config: ~/.udos/config/")
        print("Workspace: ~/.udos/memory/")
        print("Credentials: ~/.udos/.credentials/")

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        import traceback

        traceback.print_exc()
        sys.exit(1)
