"""
Test TCZ Builder

Creates test TCZ packages to verify the build system.
"""

import sys
from pathlib import Path

# Add parent directories to path
workspace = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace))

from dev.goblin.core.packaging.tcz_builder import TCZBuilder, PackageSpec, create_core_spec
from dev.goblin.core.version import get_version_string


def test_minimal_package():
    """Test building a minimal package"""
    print("=" * 60)
    print("TEST: Minimal Package")
    print("=" * 60)

    output = workspace / "distribution" / "test"
    builder = TCZBuilder(workspace, output)

    spec = PackageSpec(
        name="test-minimal",
        version="1.0.0",
        description="Minimal test package",
        source_dirs=[],
        executables={},
        dependencies=[],
    )

    try:
        tcz_file = builder.build_package(spec)
        print(f"\n✅ Built: {tcz_file}")
        print(f"   Size: {tcz_file.stat().st_size / 1024:.1f} KB")

        # Check metadata files
        metadata_files = [
            tcz_file.with_suffix(".tcz.md5.txt"),
            tcz_file.with_suffix(".tcz.info"),
            tcz_file.with_suffix(".tcz.list"),
        ]

        for mf in metadata_files:
            if mf.exists():
                print(f"   ✓ {mf.name}")
            else:
                print(f"   ✗ {mf.name} (missing)")

        return True

    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_core_package():
    """Test building udos-core package"""
    print("\n" + "=" * 60)
    print("TEST: udos-core Package")
    print("=" * 60)

    output = workspace / "distribution" / "test"
    builder = TCZBuilder(workspace, output)

    try:
        version = get_version_string("core")
        spec = create_core_spec(version)

        # Simplify for testing - just core essentials
        spec.source_dirs = [
            Path("core/services"),
            Path("core/commands"),
        ]
        spec.docs = [Path("README.md")]

        tcz_file = builder.build_package(spec)
        print(f"\n✅ Built: {tcz_file}")
        print(f"   Size: {tcz_file.stat().st_size / (1024*1024):.1f} MB")

        # Check metadata files
        dep_file = Path(str(tcz_file) + ".dep")
        if dep_file.exists():
            with open(dep_file) as f:
                deps = f.read().strip().split("\n")
            print(f"   Dependencies: {len(deps)}")
            for dep in deps:
                print(f"     - {dep}")

        return True

    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_dependencies():
    """Check required tools"""
    print("=" * 60)
    print("DEPENDENCY CHECK")
    print("=" * 60)

    import subprocess

    tools = {"mksquashfs": "--help", "unsquashfs": "--help", "md5sum": "--version"}
    results = {}

    for tool, arg in tools.items():
        try:
            result = subprocess.run([tool, arg], capture_output=True, timeout=2)
            # mksquashfs and unsquashfs return 1 for --help, which is normal
            results[tool] = result.returncode in [0, 1]
        except FileNotFoundError:
            results[tool] = False
        except Exception:
            results[tool] = False

    for tool, available in results.items():
        status = "✓" if available else "✗"
        print(f"{status} {tool}")

    all_available = all(results.values())

    if not all_available:
        print("\n⚠️  Missing dependencies!")
        print("Install with: brew install squashfs")

    return all_available


if __name__ == "__main__":
    print("uDOS TCZ Builder Test Suite\n")

    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Cannot proceed without required tools")
        sys.exit(1)

    # Run tests
    results = []

    results.append(("Minimal Package", test_minimal_package()))
    results.append(("Core Package", test_core_package()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(1)
