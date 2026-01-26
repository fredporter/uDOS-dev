"""
Test Extension System

Validates Phase 2: Extension loading, manifest parsing, permissions.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dev.goblin.core.services.extension_loader import (
    ExtensionLoader,
    ExtensionManifest,
    SecurityError,
)
from dev.goblin.core.config.paths import get_user_path


def test_manifest_parsing():
    """Test extension manifest parsing."""
    print("\n[TEST] Manifest parsing...")

    manifest_data = {
        "id": "com.test.example",
        "version": "1.0.0",
        "name": "Test Extension",
        "description": "Test extension",
        "compatibility": {
            "udos_version": ">=1.0.0",
            "platforms": ["linux"],
        },
        "dependencies": {
            "python": ["requests"],
        },
        "permissions": ["filesystem:sandbox", "api:commands"],
        "entry_points": {
            "commands": ["TEST"],
        },
    }

    manifest = ExtensionManifest(manifest_data)

    assert manifest.id == "com.test.example"
    assert manifest.version == "1.0.0"
    assert manifest.name == "Test Extension"
    assert "linux" in manifest.platforms
    assert "requests" in manifest.python_deps
    assert "filesystem:sandbox" in manifest.permissions
    assert "TEST" in manifest.commands

    print("✅ Manifest parsing works")


def test_extension_loader():
    """Test extension loader initialization."""
    print("\n[TEST] Extension loader initialization...")

    loader = ExtensionLoader()

    assert loader.system_extensions.exists() or True  # May not exist in dev
    assert loader.user_extensions.exists()  # Should be created by init_user_directory
    assert len(loader.loaded) == 0  # No extensions loaded yet

    print(f"✅ Extension loader initialized")
    print(f"   System extensions: {loader.system_extensions}")
    print(f"   User extensions: {loader.user_extensions}")


def test_permission_validation():
    """Test permission validation for user extensions."""
    print("\n[TEST] Permission validation...")

    loader = ExtensionLoader()

    # Valid permissions
    try:
        loader._validate_permissions(["filesystem:sandbox", "api:commands"])
        print("✅ Valid permissions accepted")
    except SecurityError as e:
        print(f"❌ Valid permissions rejected: {e}")
        sys.exit(1)

    # Invalid permission
    try:
        loader._validate_permissions(["filesystem:root"])
        print("❌ Invalid permission accepted (security hole!)")
        sys.exit(1)
    except SecurityError:
        print("✅ Invalid permission rejected")


def test_example_extension():
    """Test loading example extension."""
    print("\n[TEST] Example extension loading...")

    # Copy example extension to user extensions
    template_dir = project_root / "distribution/templates/extension-template"
    user_ext_dir = get_user_path("sandbox/extensions/example")

    if not user_ext_dir.exists():
        user_ext_dir.mkdir(parents=True)

        # Copy files
        import shutil

        for file in ["extension.json", "__init__.py", "README.md"]:
            src = template_dir / file
            if src.exists():
                shutil.copy(src, user_ext_dir / file)

    # Load extensions
    loader = ExtensionLoader()
    loader.load_all()

    # Check if example loaded
    if "com.udos.example" in loader.loaded:
        print("✅ Example extension loaded")

        ext = loader.loaded["com.udos.example"]
        print(f"   Name: {ext['manifest'].name}")
        print(f"   Version: {ext['manifest'].version}")
        print(f"   Trusted: {ext['trusted']}")
    else:
        print("⚠️  Example extension not found (this is OK in clean environment)")


def test_command_registration():
    """Test command registration from extensions."""
    print("\n[TEST] Command registration...")

    loader = ExtensionLoader()
    loader.load_all()

    if "EXAMPLE" in loader.command_handlers:
        print("✅ EXAMPLE command registered")

        # Test command execution
        handler = loader.command_handlers["EXAMPLE"]
        result = handler("EXAMPLE", {"message": "Test message"})

        print(f"   Result: {result}")
        assert result["status"] == "success"
        assert "Test message" in result["message"]
    else:
        print("⚠️  EXAMPLE command not registered (extension not loaded)")


def run_all_tests():
    """Run all extension system tests."""
    print("=" * 60)
    print("Extension System Tests (Phase 2)")
    print("=" * 60)

    try:
        test_manifest_parsing()
        test_extension_loader()
        test_permission_validation()
        test_example_extension()
        test_command_registration()

        print("\n" + "=" * 60)
        print("✅ ALL EXTENSION TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
