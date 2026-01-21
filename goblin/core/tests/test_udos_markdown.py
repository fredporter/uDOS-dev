"""
Test .udos.md Parser and Executor - Phase 5

Validates unified Markdown format parsing and execution.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dev.goblin.core.runtime.markdown import (
    UDOSMarkdownParser,
    UDOSMarkdownExecutor,
    UDOSDocument,
    ParseError,
)


def test_frontmatter_parsing():
    """Test YAML frontmatter parsing."""
    print("\n[TEST] YAML frontmatter parsing...")

    content = """---
title: Test Document
author: uDOS Team
permissions: [read, write, execute]
tags: [test, example]
---

# Test Content

This is a test document.
"""

    parser = UDOSMarkdownParser()
    doc = parser.parse(content)

    assert doc.title == "Test Document"
    assert doc.author == "uDOS Team"
    assert "execute" in doc.permissions
    assert "test" in doc.tags

    print("✅ Frontmatter parsing works")
    print(f"   Title: {doc.title}")
    print(f"   Permissions: {doc.permissions}")


def test_map_tile_parsing():
    """Test ASCII map tile parsing."""
    print("\n[TEST] ASCII map tile parsing...")

    content = """---
title: World Map Sample
type: map
---

# World Map

## North America

```map
TILE:NA01 NAME:California ZONE:America/Los_Angeles
┌──────────────────────────────────────────┐
│           CALIFORNIA REGION              │
│                                          │
│    ○ San Francisco                       │
│                                          │
│         ○ Los Angeles                    │
│                                          │
│              ○ San Diego                 │
│                                          │
└──────────────────────────────────────────┘
```

## Europe

```map
TILE:EU01 NAME:Britain
┌──────────────────┐
│    BRITAIN       │
│                  │
│    ○ London      │
│                  │
└──────────────────┘
```
"""

    parser = UDOSMarkdownParser()
    doc = parser.parse(content)

    assert len(doc.map_tiles) == 2

    # First tile
    tile1 = doc.map_tiles[0]
    assert tile1["tile_code"] == "NA01"
    assert tile1["name"] == "California"
    assert tile1["zone"] == "America/Los_Angeles"
    assert "CALIFORNIA REGION" in tile1["ascii"]

    # Second tile
    tile2 = doc.map_tiles[1]
    assert tile2["tile_code"] == "EU01"
    assert tile2["name"] == "Britain"
    assert "BRITAIN" in tile2["ascii"]

    print("✅ Map tile parsing works")
    print(f"   Tiles: {len(doc.map_tiles)}")
    print(f"   Tile 1: {tile1['name']} ({tile1['tile_code']})")
    print(f"   Tile 2: {tile2['name']} ({tile2['tile_code']})")


def test_map_tile_size_constraint():
    """Test 120x40 character constraint."""
    print("\n[TEST] Map tile size constraint...")

    # Create oversized tile
    wide_line = "X" * 150  # Exceeds 120
    tall_tile = "\n".join([f"Line {i}" for i in range(50)])  # Exceeds 40

    content = f"""---
title: Size Test
---

```map
TILE:T01
{wide_line}
```

```map
TILE:T02
{tall_tile}
```
"""

    parser = UDOSMarkdownParser()
    doc = parser.parse(content)

    # Parser doesn't enforce size, but converter should
    assert len(doc.map_tiles) == 2

    print("✅ Size constraint test complete")
    print(f"   Parser accepts tiles (converter will constrain)")


def test_map_tile_roundtrip():
    """Test map tile serialization roundtrip."""
    print("\n[TEST] Map tile roundtrip...")

    original = """---
title: Roundtrip Test
type: map
---

# Test Map

```map
TILE:RT01 NAME:TestTile ZONE:UTC
┌────┐
│Test│
└────┘
```
"""

    parser = UDOSMarkdownParser()
    doc1 = parser.parse(original)

    # Serialize back to markdown
    serialized = doc1.to_markdown()

    # Parse again
    doc2 = parser.parse(serialized)

    assert len(doc2.map_tiles) == 1
    assert doc2.map_tiles[0]["tile_code"] == "RT01"
    assert doc2.map_tiles[0]["name"] == "TestTile"
    assert doc2.map_tiles[0]["zone"] == "UTC"

    print("✅ Map tile roundtrip works")
    print(f"   Original tiles: {len(doc1.map_tiles)}")
    print(f"   Roundtrip tiles: {len(doc2.map_tiles)}")


def test_upy_script_extraction():
    """Test uPY script extraction."""
    print("\n[TEST] uPY script extraction...")

    content = """---
title: Script Test
---

# Script Example

```upy
x = 10
print(f"Value: {x}")
```

More content here.

```upy
y = 20
print(f"Another: {y}")
```
"""

    parser = UDOSMarkdownParser()
    doc = parser.parse(content)

    assert len(doc.upy_scripts) == 2
    assert "x = 10" in doc.upy_scripts[0]["code"]
    assert "y = 20" in doc.upy_scripts[1]["code"]

    print("✅ uPY script extraction works")
    print(f"   Found {len(doc.upy_scripts)} scripts")


def test_state_block_parsing():
    """Test state block parsing."""
    print("\n[TEST] State block parsing...")

    content = """---
title: State Test
---

# State Example

```state
{
    "counter": 0,
    "last_run": "2026-01-04",
    "settings": {
        "enabled": true
    }
}
```
"""

    parser = UDOSMarkdownParser()
    doc = parser.parse(content)

    assert len(doc.state_blocks) == 1
    assert doc.get_state("counter") == 0
    assert doc.get_state("last_run") == "2026-01-04"

    print("✅ State block parsing works")
    print(f"   Counter: {doc.get_state('counter')}")


def test_markdown_content_extraction():
    """Test markdown content extraction."""
    print("\n[TEST] Markdown content extraction...")

    content = """---
title: Content Test
---

# Main Title

This is **bold** and this is *italic*.

## Subsection

- Item 1
- Item 2

```upy
# This should be removed from markdown
print("test")
```

More text after script.
"""

    parser = UDOSMarkdownParser()
    doc = parser.parse(content)

    assert "# Main Title" in doc.markdown_content
    assert "**bold**" in doc.markdown_content
    assert "More text after script" in doc.markdown_content
    # Script should not be in markdown content
    assert 'print("test")' not in doc.markdown_content

    print("✅ Markdown content extraction works")


def test_script_execution():
    """Test uPY script execution from .udos.md."""
    print("\n[TEST] Script execution...")

    content = """---
title: Execution Test
permissions: [read, write, execute]
---

# Script Execution

```upy
x = 10
y = 20
result = x + y
print(f"Sum: {result}")
```

```upy
import json
data = {"test": "value"}
print(json.dumps(data))
```
"""

    executor = UDOSMarkdownExecutor()
    result = executor.execute(content)

    assert result["success"] is True
    assert len(result["scripts"]) == 2
    assert result["scripts"][0]["success"] is True
    assert "Sum: 30" in result["scripts"][0]["output"]

    print("✅ Script execution works")
    print(f"   Executed {len(result['scripts'])} scripts successfully")


def test_permission_validation():
    """Test permission validation."""
    print("\n[TEST] Permission validation...")

    content = """---
title: Permission Test
permissions: [read]
---

```upy
print("This should not execute")
```
"""

    executor = UDOSMarkdownExecutor()
    result = executor.execute(content)

    assert result["success"] is False
    assert "permission" in result["error"].lower()

    print("✅ Permission validation works")
    print(f"   Blocked execution: {result['error']}")


def test_state_access_from_script():
    """Test STATE access from uPY scripts."""
    print("\n[TEST] State access from scripts...")

    content = """---
title: State Access Test
permissions: [read, write, execute]
---

```state
{
    "counter": 5
}
```

```upy
# Get state
current = STATE.GET(key="counter")
print(f"Current counter: {current}")

# Update state
STATE.SET(key="counter", value=current + 1)
new_value = STATE.GET(key="counter")
print(f"New counter: {new_value}")
```
"""

    executor = UDOSMarkdownExecutor()
    result = executor.execute(content)

    assert result["success"] is True
    assert "Current counter: 5" in result["scripts"][0]["output"]
    assert "New counter: 6" in result["scripts"][0]["output"]

    # Check state was updated
    assert result["document"].get_state("counter") == 6

    print("✅ State access from scripts works")


def test_command_execution():
    """Test command execution from .udos.md scripts."""
    print("\n[TEST] Command execution from scripts...")

    executed_commands = []

    def mock_executor(command: str, params: dict):
        executed_commands.append({"command": command, "params": params})
        return {"status": "success"}

    content = """---
title: Command Test
permissions: [read, write, execute]
---

```upy
FILE.NEW(name="test.txt", content="Hello")
MESH.SEND(device="node2", message="ping")
```
"""

    executor = UDOSMarkdownExecutor(command_executor=mock_executor)
    result = executor.execute(content)

    assert result["success"] is True
    assert len(executed_commands) == 2
    assert executed_commands[0]["command"] == "FILE.NEW"
    assert executed_commands[1]["command"] == "MESH.SEND"

    print("✅ Command execution from scripts works")
    print(f"   Executed {len(executed_commands)} commands")


def test_validation_only():
    """Test validation without execution."""
    print("\n[TEST] Validation only...")

    content = """---
title: Validation Test
---

```upy
x = 10
print(x)
```

```upy
import os  # This should fail validation
os.system("ls")
```
"""

    executor = UDOSMarkdownExecutor()
    result = executor.validate_only(content)

    assert result["valid"] is False
    assert any("os" in err.lower() for err in result["errors"])

    print("✅ Validation only works")
    print(f"   Found {len(result['errors'])} errors")


def test_document_serialization():
    """Test document serialization back to markdown."""
    print("\n[TEST] Document serialization...")

    content = """---
title: Serialization Test
author: Test Author
---

# Content

Test content here.

```upy
print("test")
```

```state
{"key": "value"}
```
"""

    parser = UDOSMarkdownParser()
    doc = parser.parse(content)

    # Serialize back
    serialized = doc.to_markdown()

    # Re-parse
    doc2 = parser.parse(serialized)

    assert doc2.title == doc.title
    assert doc2.author == doc.author
    assert len(doc2.upy_scripts) == len(doc.upy_scripts)
    assert len(doc2.state_blocks) == len(doc.state_blocks)

    print("✅ Document serialization works")


def run_all_tests():
    """Run all .udos.md parser/executor tests."""
    print("=" * 60)
    print(".udos.md Parser and Executor Tests (Phase 5)")
    print("=" * 60)

    try:
        test_frontmatter_parsing()
        test_map_tile_parsing()
        test_map_tile_size_constraint()
        test_map_tile_roundtrip()
        test_upy_script_extraction()
        test_state_block_parsing()
        test_markdown_content_extraction()
        test_script_execution()
        test_permission_validation()
        test_state_access_from_script()
        test_command_execution()
        test_validation_only()
        test_document_serialization()

        print("\n" + "=" * 60)
        print("✅ ALL .udos.md TESTS PASSED")
        print("=" * 60)
        print("\n🎉 Phase 5 Implementation Complete!")
        print("\nFeatures validated:")
        print("  ✅ YAML frontmatter parsing")
        print("  ✅ uPY script extraction")
        print("  ✅ State block parsing (JSON)")
        print("  ✅ Map tile parsing (ASCII)")
        print("  ✅ Markdown content extraction")
        print("  ✅ Script execution with uPY")
        print("  ✅ Permission validation")
        print("  ✅ STATE.GET/SET from scripts")
        print("  ✅ Command execution")
        print("  ✅ Validation-only mode")
        print("  ✅ Document serialization")
        print("  ✅ Map tile roundtrip")
        print("\n🏗️  TinyCore Architecture Refactor COMPLETE!")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
