"""
Test Path Migration - Phase 3

Validates that core services use FHS-compliant path helpers.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dev.goblin.core.services.state_manager import StateManager
from dev.goblin.core.services.device_manager import DeviceManager
from dev.goblin.core.services.log_compression import LogCompressor
from dev.goblin.core.udos_core import UserVars
from dev.goblin.core.config.paths import get_user_path


def test_state_manager_paths():
    """Test StateManager uses FHS paths."""
    print("\n[TEST] StateManager path migration...")

    sm = StateManager()

    # Should use ~/.udos/memory/ instead of memory/
    assert str(sm.state_file).startswith(str(get_user_path("")))
    assert "memory/bank/user/user-state.json" in str(sm.state_file)
    assert not str(sm.state_file).startswith("memory/")  # Not relative

    print(f"✅ StateManager uses FHS paths: {sm.state_file}")


def test_device_manager_paths():
    """Test DeviceManager uses FHS paths."""
    print("\n[TEST] DeviceManager path migration...")

    dm = DeviceManager()

    assert str(dm.device_file).startswith(str(get_user_path("")))
    assert "memory/bank/system/device.json" in str(dm.device_file)
    assert not str(dm.device_file).startswith("memory/")

    print(f"✅ DeviceManager uses FHS paths: {dm.device_file}")


def test_user_vars_paths():
    """Test UserVars uses FHS paths."""
    print("\n[TEST] UserVars path migration...")

    uv = UserVars()

    assert str(uv.var_file).startswith(str(get_user_path("")))
    assert "memory/bank/user/variables.json" in str(uv.var_file)
    assert not str(uv.var_file).startswith("memory/")

    print(f"✅ UserVars uses FHS paths: {uv.var_file}")


def test_log_compressor_paths():
    """Test LogCompressor uses FHS paths."""
    print("\n[TEST] LogCompressor path migration...")

    lc = LogCompressor()

    assert str(lc.log_dir).startswith(str(get_user_path("")))
    assert "memory/logs" in str(lc.log_dir)
    assert not str(lc.log_dir).startswith("memory/")

    print(f"✅ LogCompressor uses FHS paths: {lc.log_dir}")


def test_path_consistency():
    """Test all services use consistent paths."""
    print("\n[TEST] Path consistency across services...")

    sm = StateManager()
    dm = DeviceManager()
    uv = UserVars()
    lc = LogCompressor()

    base_path = get_user_path("")

    # All should share same base path
    paths = [
        sm.state_file.parent.parent.parent,
        dm.device_file.parent.parent.parent,
        uv.var_file.parent.parent.parent,
        lc.log_dir.parent,
    ]

    for path in paths:
        assert str(path).startswith(str(base_path))

    print(f"✅ All services use consistent base path: {base_path}")


def test_development_vs_production():
    """Test paths work in both dev and production modes."""
    print("\n[TEST] Development vs production mode...")

    base = get_user_path("")

    # In development, should use ~/.udos/memory/
    # In production, should use same ~/.udos/memory/
    # (Project root doesn't matter for user paths)

    assert ".udos" in str(base)
    assert "memory" in str(base)

    print(f"✅ Paths configured for: {base}")

    # Check if we're in dev mode (memory/ directory exists in project)
    project_memory = project_root / "memory"
    if project_memory.exists():
        print("   📦 Development mode: project memory/ directory exists")

    # User directory always in ~/.udos/
    home_udos = Path.home() / ".udos"
    if home_udos.exists():
        print(f"   🏠 User directory: {home_udos}")


def run_all_tests():
    """Run all path migration tests."""
    print("=" * 60)
    print("Path Migration Tests (Phase 3)")
    print("=" * 60)

    try:
        test_state_manager_paths()
        test_device_manager_paths()
        test_user_vars_paths()
        test_log_compressor_paths()
        test_path_consistency()
        test_development_vs_production()

        print("\n" + "=" * 60)
        print("✅ ALL PATH MIGRATION TESTS PASSED")
        print("=" * 60)
        print("\n📍 Summary:")
        print(f"   - StateManager: ~/.udos/memory/bank/user/user-state.json")
        print(f"   - DeviceManager: ~/.udos/memory/bank/system/device.json")
        print(f"   - UserVars: ~/.udos/memory/bank/user/variables.json")
        print(f"   - LogCompressor: ~/.udos/memory/logs/")
        print(f"\n✨ All services now use FHS-compliant paths!")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
