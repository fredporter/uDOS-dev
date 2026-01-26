#!/usr/bin/env python3
"""
Test Runtime API Endpoints

Tests all /api/v0/runtime/* endpoints:
- POST /parse - Parse markdown blocks
- POST /execute - Execute single block
- POST /execute-all - Execute all blocks
- GET /state - Get runtime state
- POST /state - Update runtime state
- DELETE /state - Clear runtime state

Usage:
    python test_runtime_api.py
"""

import requests
import json
import sys
from pathlib import Path

# Server config
BASE_URL = "http://127.0.0.1:8767"
API_BASE = f"{BASE_URL}/api/v0/runtime"

# Test markdown content
TEST_MARKDOWN = """# Test Runtime

This is a test document with runtime blocks.

```state
$name = "Fred"
$age = 30
$coins = 100
$has_key = false
```

```set
set $coins = 150
inc $age
toggle $has_key
```

```panel
title: User Profile
content: Name: $name, Age: $age, Coins: $coins, Key: $has_key
```
"""


def test_parse():
    """Test POST /api/v0/runtime/parse"""
    print("\n" + "=" * 80)
    print("TEST: Parse Markdown")
    print("=" * 80)
    
    response = requests.post(
        f"{API_BASE}/parse",
        json={"markdown": TEST_MARKDOWN},
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Parsed {len(data['blocks'])} blocks")
        print(f"   Variables: {data['variables']}")
        print(f"   Block types: {[b['type'] for b in data['blocks']]}")
        return data
    else:
        print(f"❌ Parse failed: {response.text}")
        return None


def test_execute_block():
    """Test POST /api/v0/runtime/execute"""
    print("\n" + "=" * 80)
    print("TEST: Execute Single Block")
    print("=" * 80)
    
    # Execute a state block
    block_content = '$health = 100\n$level = 1'
    
    response = requests.post(
        f"{API_BASE}/execute",
        json={
            "block_type": "state",
            "content": block_content,
            "line": 1
        },
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Block executed - status: {data['status']}")
        print(f"   State: {data['state']}")
        return data
    else:
        print(f"❌ Execute failed: {response.text}")
        return None


def test_execute_all():
    """Test POST /api/v0/runtime/execute-all"""
    print("\n" + "=" * 80)
    print("TEST: Execute All Blocks")
    print("=" * 80)
    
    response = requests.post(
        f"{API_BASE}/execute-all",
        json={
            "markdown": TEST_MARKDOWN,
            "reset_state": True
        },
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Executed {data['blocks_executed']} blocks")
        print(f"   Failed: {data['blocks_failed']}")
        print(f"   Final state: {data['final_state']}")
        
        # Show panel output
        for i, result in enumerate(data['results'], 1):
            if result['output']:
                print(f"\n   Block {i} output:")
                print(f"   {json.dumps(result['output'], indent=2)}")
        
        return data
    else:
        print(f"❌ Execute-all failed: {response.text}")
        return None


def test_get_state():
    """Test GET /api/v0/runtime/state"""
    print("\n" + "=" * 80)
    print("TEST: Get Runtime State")
    print("=" * 80)
    
    response = requests.get(f"{API_BASE}/state", timeout=5)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ State retrieved - {data['variable_count']} variables")
        print(f"   State: {data['state']}")
        return data
    else:
        print(f"❌ Get state failed: {response.text}")
        return None


def test_update_state():
    """Test POST /api/v0/runtime/state"""
    print("\n" + "=" * 80)
    print("TEST: Update Runtime State")
    print("=" * 80)
    
    response = requests.post(
        f"{API_BASE}/state",
        json={
            "variables": {
                "test_var": "hello",
                "test_num": 42
            }
        },
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ State updated - {data['variable_count']} variables")
        print(f"   State: {data['state']}")
        return data
    else:
        print(f"❌ Update state failed: {response.text}")
        return None


def test_clear_state():
    """Test DELETE /api/v0/runtime/state"""
    print("\n" + "=" * 80)
    print("TEST: Clear Runtime State")
    print("=" * 80)
    
    response = requests.delete(f"{API_BASE}/state", timeout=5)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ State cleared - {data['variable_count']} variables remaining")
        return data
    else:
        print(f"❌ Clear state failed: {response.text}")
        return None


def check_server():
    """Check if Goblin server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server healthy - {data.get('server')} v{data.get('version')}")
            return True
    except requests.exceptions.RequestException:
        pass
    
    print(f"❌ Server not reachable at {BASE_URL}")
    print("   Start server with: dev/goblin/launch-goblin-dev.sh")
    return False


def run_all_tests():
    """Run all runtime API tests"""
    print("\n" + "=" * 80)
    print("🧪 RUNTIME API TESTS - Move 2")
    print("=" * 80)
    
    # Check server
    if not check_server():
        return False
    
    try:
        # Test parse
        parse_result = test_parse()
        if not parse_result:
            return False
        
        # Test execute single block
        exec_result = test_execute_block()
        if not exec_result:
            return False
        
        # Test get state (should have $health and $level from previous test)
        state_result = test_get_state()
        
        # Test clear state
        clear_result = test_clear_state()
        
        # Test execute all blocks
        exec_all_result = test_execute_all()
        if not exec_all_result:
            return False
        
        # Test get state (should have vars from execute-all)
        final_state = test_get_state()
        
        # Test update state
        update_result = test_update_state()
        
        # Final state check
        test_get_state()
        
        print("\n" + "=" * 80)
        print("✅ ALL RUNTIME API TESTS PASSED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Tests failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
