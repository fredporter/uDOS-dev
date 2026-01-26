#!/usr/bin/env python3
"""
Enhanced Runtime Block Tests - Form, If, Nav

Tests the enhanced form/if/nav block executors with real examples.

Usage:
    python test_enhanced_blocks.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dev.goblin.services.runtime_executor import RuntimeExecutor


def test_form_block():
    """Test enhanced form block parsing"""
    print("\n" + "=" * 80)
    print("TEST: Form Block Parsing")
    print("=" * 80)
    
    form_content = """
name: text Your Name
email: email Email Address
age: number Your Age
bio: textarea Tell us about yourself
subscribe: checkbox Subscribe to newsletter
"""
    
    executor = RuntimeExecutor(config={
        "max_state_size_bytes": 1024 * 1024,
        "execution_timeout_ms": 5000
    })
    result = executor.execute_block("form", form_content.strip(), None)
    
    print(f"Status: {result['status']}")
    print(f"Fields parsed: {len(result.get('fields', []))}")
    
    for field in result.get('fields', []):
        print(f"  - {field['name']}: {field['type']} ({field['label']})")
    
    expected_fields = 5
    if len(result.get('fields', [])) == expected_fields:
        print(f"✅ Form parsing test passed ({expected_fields} fields)")
        return True
    else:
        print(f"❌ Expected {expected_fields} fields, got {len(result.get('fields', []))}")
        return False


def test_if_block_comparisons():
    """Test if block conditional evaluation"""
    print("\n" + "=" * 80)
    print("TEST: If Block Conditionals")
    print("=" * 80)
    
    executor = RuntimeExecutor(config={
        "max_state_size_bytes": 1024 * 1024,
        "execution_timeout_ms": 5000
    })
    
    # Set up state
    executor.set_state({
        "$health": 75,
        "$level": 5,
        "$has_key": True,
        "$name": "Hero"
    })
    
    test_cases = [
        ("$health > 50", True),
        ("$health < 100", True),
        ("$level == 5", True),
        ("$level != 3", True),
        ("$has_key == True", True),
        ("$health >= 75", True),
        ("$level <= 10", True),
        ("$health > 80", False),
        ("$level == 3", False),
    ]
    
    passed = 0
    failed = 0
    
    for condition, expected in test_cases:
        result = executor.execute_block("if", condition, None)
        actual = result.get("condition")
        
        if actual == expected:
            print(f"  ✅ {condition} = {actual}")
            passed += 1
        else:
            print(f"  ❌ {condition} = {actual} (expected: {expected})")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ If block conditionals test passed")
        return True
    else:
        print("❌ Some conditionals failed")
        return False


def test_if_block_logical_operators():
    """Test if block with and/or operators"""
    print("\n" + "=" * 80)
    print("TEST: If Block Logical Operators")
    print("=" * 80)
    
    executor = RuntimeExecutor(config={
        "max_state_size_bytes": 1024 * 1024,
        "execution_timeout_ms": 5000
    })
    executor.set_state({
        "$health": 75,
        "$level": 5,
        "$has_key": True
    })
    
    test_cases = [
        ("$health > 50 and $level >= 5", True),
        ("$health > 80 or $level >= 5", True),
        ("$health > 80 and $level >= 5", False),
        ("$health < 50 or $level < 3", False),
        ("$has_key == True and $level > 3", True),
    ]
    
    passed = 0
    failed = 0
    
    for condition, expected in test_cases:
        result = executor.execute_block("if", condition, None)
        actual = result.get("condition")
        
        if actual == expected:
            print(f"  ✅ {condition} = {actual}")
            passed += 1
        else:
            print(f"  ❌ {condition} = {actual} (expected: {expected})")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ Logical operators test passed")
        return True
    else:
        print("❌ Some logical tests failed")
        return False


def test_nav_block():
    """Test nav block choice parsing"""
    print("\n" + "=" * 80)
    print("TEST: Nav Block Choice Parsing")
    print("=" * 80)
    
    nav_content = """
Start Quest -> quest_start
Visit Shop -> shop
Talk to Elder -> elder_conversation
Rest at Inn
Check Inventory -> inventory
"""
    
    executor = RuntimeExecutor(config={
        "max_state_size_bytes": 1024 * 1024,
        "execution_timeout_ms": 5000
    })
    result = executor.execute_block("nav", nav_content.strip(), None)
    
    print(f"Status: {result['status']}")
    print(f"Choices parsed: {len(result.get('choices', []))}")
    
    for choice in result.get('choices', []):
        print(f"  - {choice['label']} -> {choice['target']}")
    
    expected_choices = 5
    if len(result.get('choices', [])) == expected_choices:
        print(f"✅ Nav parsing test passed ({expected_choices} choices)")
        return True
    else:
        print(f"❌ Expected {expected_choices} choices, got {len(result.get('choices', []))}")
        return False


def test_set_block_fix():
    """Test that set block parser bug is fixed"""
    print("\n" + "=" * 80)
    print("TEST: Set Block Parser Fix")
    print("=" * 80)
    
    set_content = """
set $coins = 150
set $name = "Alice"
set $level = 5
"""
    
    executor = RuntimeExecutor(config={
        "max_state_size_bytes": 1024 * 1024,
        "execution_timeout_ms": 5000
    })
    result = executor.execute_block("set", set_content.strip(), None)
    
    state = executor.get_state()
    
    print(f"Status: {result['status']}")
    print(f"State after set commands:")
    
    test_cases = [
        ("$coins", 150, int),
        ("$name", "Alice", str),
        ("$level", 5, int),
    ]
    
    passed = 0
    failed = 0
    
    for var, expected_value, expected_type in test_cases:
        actual_value = state.get(var)
        print(f"  {var} = {actual_value} ({type(actual_value).__name__})")
        
        if actual_value == expected_value and isinstance(actual_value, expected_type):
            print(f"    ✅ Correct value and type")
            passed += 1
        else:
            print(f"    ❌ Expected {expected_value} ({expected_type.__name__})")
            failed += 1
    
    if failed == 0:
        print("✅ Set block parser fix verified")
        return True
    else:
        print("❌ Set block parser still has issues")
        return False


def run_all_tests():
    """Run all enhanced block tests"""
    print("\n" + "=" * 80)
    print("🧪 ENHANCED RUNTIME BLOCK TESTS")
    print("=" * 80)
    
    tests = [
        ("Form Block", test_form_block),
        ("If Conditionals", test_if_block_comparisons),
        ("If Logical Operators", test_if_block_logical_operators),
        ("Nav Block", test_nav_block),
        ("Set Block Fix", test_set_block_fix),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 80)
    if failed == 0:
        print(f"✅ ALL ENHANCED BLOCK TESTS PASSED ({passed}/{passed})")
    else:
        print(f"⚠️  TESTS COMPLETED: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
