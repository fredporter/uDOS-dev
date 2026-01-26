#!/usr/bin/env python3
"""
Runtime Executor Tests - Move 2

Tests markdown runtime block parsing and execution:
- state blocks (variable declaration)
- set blocks (variable mutation)
- form blocks (input fields)
- if/else blocks (conditionals)
- nav blocks (navigation)
- panel blocks (UI panels)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from dev.goblin.services.runtime_executor import RuntimeExecutor


def test_parse_blocks():
    """Test parsing runtime blocks from markdown"""
    print("=" * 80)
    print("TEST: Parse Runtime Blocks")
    print("=" * 80)
    
    markdown = """
# Test Document

Some regular markdown content.

```state
$name = "Fred"
$age = 30
$coins = 100
```

More content here.

```set
set $coins 200
inc $age 1
```

```panel
title: User Info
content: Hello, $name! You are $age years old.
```
"""
    
    config = {"max_state_size_bytes": 1048576, "execution_timeout_ms": 5000}
    executor = RuntimeExecutor(config)
    
    result = executor.parse_markdown(markdown)
    
    print(f"\n📊 Parse Results:")
    print(f"   Blocks found: {result['ast']['total_blocks']}")
    print(f"   Block types:  {', '.join(result['ast']['block_types'])}")
    print(f"   Variables:    {len(result['variables'])}")
    print()
    
    for i, block in enumerate(result['blocks'], 1):
        print(f"   Block {i}: {block['type']} (line {block['line']})")
    
    print()
    assert result['ast']['total_blocks'] == 3, "Should find 3 blocks"
    assert 'state' in result['ast']['block_types'], "Should find state block"
    assert 'set' in result['ast']['block_types'], "Should find set block"
    assert 'panel' in result['ast']['block_types'], "Should find panel block"
    print("✅ Parse test passed")
    print()


def test_state_execution():
    """Test state block execution"""
    print("=" * 80)
    print("TEST: State Block Execution")
    print("=" * 80)
    
    config = {"max_state_size_bytes": 1048576, "execution_timeout_ms": 5000}
    executor = RuntimeExecutor(config)
    
    state_block = """
$name = "Fred"
$age = 30
$coins = 100
$has_key = true
$items = null
"""
    
    result = executor.execute_block("state", state_block)
    
    print(f"\n📊 Execution Results:")
    print(f"   Status: {result['status']}")
    print(f"   State variables: {len(result['state'])}")
    print()
    
    for var, value in result['state'].items():
        print(f"   {var} = {value} ({type(value).__name__})")
    
    print()
    assert result['status'] == 'executed', "Should execute successfully"
    assert result['state']['$name'] == "Fred", "Should set $name"
    assert result['state']['$age'] == 30, "Should set $age as int"
    assert result['state']['$coins'] == 100, "Should set $coins"
    assert result['state']['$has_key'] is True, "Should set $has_key as boolean"
    print("✅ State execution test passed")
    print()


def test_set_mutations():
    """Test set block mutations"""
    print("=" * 80)
    print("TEST: Set Block Mutations")
    print("=" * 80)
    
    config = {"max_state_size_bytes": 1048576, "execution_timeout_ms": 5000}
    executor = RuntimeExecutor(config)
    
    # Initialize state
    executor.set_state({'$coins': 100, '$has_key': False})
    print(f"\n📊 Initial State:")
    print(f"   $coins = {executor.get_state()['$coins']}")
    print(f"   $has_key = {executor.get_state()['$has_key']}")
    print()
    
    set_block = """
set $coins 200
inc $coins 50
dec $coins 25
toggle $has_key
"""
    
    result = executor.execute_block("set", set_block)
    
    print(f"📊 After Mutations:")
    print(f"   Status: {result['status']}")
    print(f"   $coins = {result['state']['$coins']} (expected: 225)")
    print(f"   $has_key = {result['state']['$has_key']} (expected: True)")
    print()
    
    assert result['state']['$coins'] == 225, "Should mutate $coins correctly"
    assert result['state']['$has_key'] is True, "Should toggle $has_key"
    print("✅ Set mutations test passed")
    print()


def test_panel_interpolation():
    """Test panel block variable interpolation"""
    print("=" * 80)
    print("TEST: Panel Variable Interpolation")
    print("=" * 80)
    
    config = {"max_state_size_bytes": 1048576, "execution_timeout_ms": 5000}
    executor = RuntimeExecutor(config)
    
    # Set state
    executor.set_state({
        '$name': 'Fred',
        '$age': 30,
        '$coins': 100
    })
    
    panel_block = """
title: User Stats
content: Hello, $name! You are $age years old and have $coins coins.
"""
    
    result = executor.execute_block("panel", panel_block)
    
    print(f"\n📊 Panel Output:")
    print(f"   Status: {result['status']}")
    print(f"   Output:\n{result['output']}")
    print()
    
    assert '$name' not in result['output'], "Variables should be interpolated"
    assert 'Fred' in result['output'], "Should contain interpolated name"
    assert '30' in result['output'], "Should contain interpolated age"
    assert '100' in result['output'], "Should contain interpolated coins"
    print("✅ Panel interpolation test passed")
    print()


def test_full_workflow():
    """Test complete runtime workflow"""
    print("=" * 80)
    print("TEST: Full Runtime Workflow")
    print("=" * 80)
    
    markdown = """
# Character Setup

```state
$player_name = "Hero"
$health = 100
$level = 1
```

## Actions

```set
inc $health 20
inc $level 1
```

## Status

```panel
title: Character Status
content: $player_name (Level $level) - Health: $health HP
```
"""
    
    config = {"max_state_size_bytes": 1048576, "execution_timeout_ms": 5000}
    executor = RuntimeExecutor(config)
    
    # Parse
    parsed = executor.parse_markdown(markdown)
    print(f"\n📥 Parsed {parsed['ast']['total_blocks']} blocks")
    
    # Execute each block in sequence
    for i, block in enumerate(parsed['blocks'], 1):
        print(f"\n⚙️  Executing block {i}/{len(parsed['blocks'])}: {block['type']}")
        result = executor.execute_block(block['type'], block['content'])
        
        if result['status'] == 'executed':
            print(f"   ✅ Success")
            if result.get('output'):
                print(f"   Output: {result['output'][:100]}...")
        else:
            print(f"   ❌ Failed: {result.get('message', 'Unknown error')}")
    
    # Check final state
    final_state = executor.get_state()
    print(f"\n📊 Final State:")
    for var, value in final_state.items():
        print(f"   {var} = {value}")
    
    print()
    assert final_state['$health'] == 120, "Health should be 120"
    assert final_state['$level'] == 2, "Level should be 2"
    print("✅ Full workflow test passed")
    print()


def run_all_tests():
    """Run all runtime executor tests"""
    print("\n🧪 RUNTIME EXECUTOR TESTS - Move 2\n")
    
    try:
        test_parse_blocks()
        test_state_execution()
        test_set_mutations()
        test_panel_interpolation()
        test_full_workflow()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
