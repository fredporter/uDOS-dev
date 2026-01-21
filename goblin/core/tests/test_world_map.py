#!/usr/bin/env python3
"""
Test real-world map parsing with world-map.udos.md
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dev.goblin.core.runtime.markdown import UDOSMarkdownParser


def test_world_map():
    """Test parsing the actual world map file."""
    print("\n" + "=" * 60)
    print("🌍 TESTING WORLD MAP PARSING")
    print("=" * 60)

    map_file = project_root / "memory" / "maps" / "world-map.udos.md"

    if not map_file.exists():
        print(f"❌ Map file not found: {map_file}")
        return False

    print(f"\n📖 Reading: {map_file}")

    with open(map_file, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"   Size: {len(content)} bytes")

    # Parse
    print("\n🔄 Parsing...")
    parser = UDOSMarkdownParser()
    doc = parser.parse(content)

    print(f"\n✅ Parse successful!")
    print(f"\n📊 Document Structure:")
    print(f"   Title: {doc.title}")
    print(f"   Type: {doc.metadata.get('type')}")
    print(f"   Format: {doc.metadata.get('format')}")
    print(f"   Constraint: {doc.metadata.get('constraint')}")
    print(f"   Map Tiles: {len(doc.map_tiles)}")
    print(f"   uPY Scripts: {len(doc.upy_scripts)}")
    print(f"   State Blocks: {len(doc.state_blocks)}")
    print(f"   Markdown Lines: {len(doc.markdown_content.split(chr(10)))}")

    print(f"\n🗺️  Map Tiles:")
    for i, tile in enumerate(doc.map_tiles, 1):
        lines = tile["ascii"].split("\n")
        width = max(len(line) for line in lines) if lines else 0
        height = len(lines)

        print(f"   {i}. {tile['name']} ({tile['tile_code']})")
        print(f"      Zone: {tile['zone']}")
        print(f"      Size: {width}x{height} chars")
        if width > 120:
            print(f"      ⚠️  WIDTH EXCEEDS 120: {width}")
        if height > 40:
            print(f"      ⚠️  HEIGHT EXCEEDS 40: {height}")

    # Test serialization roundtrip
    print(f"\n🔄 Testing roundtrip serialization...")
    serialized = doc.to_markdown()
    doc2 = parser.parse(serialized)

    if len(doc2.map_tiles) == len(doc.map_tiles):
        print(f"   ✅ Roundtrip successful ({len(doc2.map_tiles)} tiles)")
    else:
        print(f"   ❌ Roundtrip failed: {len(doc.map_tiles)} → {len(doc2.map_tiles)}")
        return False

    print("\n" + "=" * 60)
    print("✅ WORLD MAP TEST PASSED")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = test_world_map()
    sys.exit(0 if success else 1)
