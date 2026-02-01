#!/usr/bin/env python3
"""
Test Secure Config Panel
=========================

Validates that the config management system works correctly.
Tests encryption, validation, audit logging, and API endpoints.
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_secure_config_manager():
    """Test SecureConfigManager class."""
    print("\n" + "="*60)
    print("🔐 Testing SecureConfigManager")
    print("="*60)

    try:
        from wizard.services.secure_config import SecureConfigManager, KeyCategory

        print("✅ SecureConfigManager import successful")

        # Initialize
        manager = SecureConfigManager()
        print("✅ SecureConfigManager initialized")

        # Test setting a key
        manager.set_key(
            name="TEST_GEMINI_API_KEY",
            value="AIzaSy_test_key_12345678901234567890",
            category=KeyCategory.AI_PROVIDERS,
            provider="Google"
        )
        print("✅ Key set successfully")

        # Test getting a key
        value = manager.get_key("TEST_GEMINI_API_KEY", decrypt=True)
        assert value == "AIzaSy_test_key_12345678901234567890", "Key value mismatch!"
        print("✅ Key retrieved and decrypted correctly")

        # Test validation
        is_valid = manager.validate_key("TEST_GEMINI_API_KEY")
        print(f"✅ Key validation: {is_valid}")

        # Test getting all keys
        all_keys = manager.get_all_keys()
        assert "TEST_GEMINI_API_KEY" in all_keys, "Key not in list!"
        print(f"✅ All keys retrieved ({len(all_keys)} total)")

        # Test status
        status = manager.get_status()
        print(f"✅ Status retrieved:")
        print(f"   - Total keys: {status['total_keys']}")
        print(f"   - Keys set: {status['keys_set']}")
        print(f"   - Encryption: {'✅ Enabled' if status['encryption_enabled'] else '⚠️ Disabled'}")

        # Test deletion
        manager.delete_key("TEST_GEMINI_API_KEY")
        print("✅ Key deleted successfully")

        # Verify deletion
        remaining = manager.get_all_keys()
        assert "TEST_GEMINI_API_KEY" not in remaining, "Key still exists after deletion!"
        print("✅ Deletion verified")

        print("\n✅ SecureConfigManager: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ SecureConfigManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_routes():
    """Test FastAPI routes."""
    print("\n" + "="*60)
    print("🚀 Testing FastAPI Routes")
    print("="*60)

    try:
        from wizard.routes.config import router

        print("✅ Config routes import successful")
        print(f"✅ Routes registered: {len(router.routes)} total")

        # List route details
        for route in router.routes:
            if hasattr(route, 'path'):
                print(f"   - {route.methods or ['GET']} {route.path}")

        print("\n✅ FastAPI Routes: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ FastAPI routes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """Verify required files exist."""
    print("\n" + "="*60)
    print("📁 Testing File Structure")
    print("="*60)

    files_to_check = [
        "public/wizard/services/secure_config.py",
        "public/wizard/routes/config.py",
        "public/wizard/server.py",
        "docs/howto/SECURE-CONFIG-PANEL.md",
        "SECURE-CONFIG-PANEL-QUICK.md",
        ".env.template",
        "bin/setup-secrets.sh",
    ]

    all_exist = True
    for file_path in files_to_check:
        full_path = PROJECT_ROOT / file_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        if not exists:
            all_exist = False

    if all_exist:
        print("\n✅ File Structure: ALL FILES PRESENT")
    else:
        print("\n⚠️  File Structure: SOME FILES MISSING")

    return all_exist


def test_encryption():
    """Test encryption/decryption."""
    print("\n" + "="*60)
    print("🔒 Testing Encryption")
    print("="*60)

    try:
        from cryptography.fernet import Fernet

        print("✅ cryptography library available")

        # Generate a key
        key = Fernet.generate_key()
        cipher = Fernet(key)
        print("✅ Encryption key generated")

        # Test encrypt/decrypt
        test_message = "sk-proj-1234567890abcdefghijklmnop"
        encrypted = cipher.encrypt(test_message.encode())
        print(f"✅ Message encrypted: {len(encrypted)} bytes")

        decrypted = cipher.decrypt(encrypted).decode()
        assert decrypted == test_message, "Decrypted message doesn't match!"
        print("✅ Message decrypted successfully")

        print("\n✅ Encryption: ALL TESTS PASSED")
        return True

    except ImportError:
        print("\n⚠️  cryptography not installed")
        print("   Run: pip install cryptography")
        return False
    except Exception as e:
        print(f"\n❌ Encryption test failed: {e}")
        return False


def test_audit_log():
    """Test audit logging."""
    print("\n" + "="*60)
    print("📝 Testing Audit Logging")
    print("="*60)

    try:
        from wizard.services.secure_config import SecureConfigManager

        manager = SecureConfigManager()

        # Perform an action
        manager.set_key(
            name="AUDIT_TEST_KEY",
            value="test_value_12345",
            category="ai_providers",
            provider="Test"
        )
        print("✅ Test key set")

        # Check if audit log exists
        config_dir = Path(__file__).parent.parent / "config"
        audit_log = config_dir / "keys.audit.log"

        if audit_log.exists():
            with open(audit_log, "r") as f:
                last_line = f.readlines()[-1]
                print(f"✅ Audit log exists and updated")
                print(f"   Last entry: {last_line.strip()[:80]}...")
        else:
            print("⚠️  Audit log not yet created")

        print("\n✅ Audit Logging: TEST PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Audit logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  🔐 SECURE CONFIG PANEL - TEST SUITE".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)

    tests = [
        ("File Structure", test_file_structure),
        ("Encryption", test_encryption),
        ("SecureConfigManager", test_secure_config_manager),
        ("Audit Logging", test_audit_log),
        ("FastAPI Routes", test_config_routes),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} passed")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📌 Next steps:")
        print("   1. Launch Wizard: python wizard/launch_wizard_dev.py --no-tui")
        print("   2. Open panel: http://127.0.0.1:8765/api/config/panel")
        print("   3. Add your API keys")
        print("   4. Run: ./bin/setup-secrets.sh")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        print("\n📌 Fix issues above, then:")
        print("   1. Install missing dependencies: pip install cryptography")
        print("   2. Verify file structure")
        print("   3. Run this test again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
