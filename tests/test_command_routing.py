#!/usr/bin/env python3
"""
Simple test to isolate the BACKUP command routing issue
"""
import sys
import os
from pathlib import Path

# Add the uDOS directory to the path dynamically
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from core.interpreters.uDOS_parser import Parser

def main():
    print("=== uDOS Command Routing Test ===")
    
    # Test 1: Parser loading
    parser = Parser()
    print(f"✓ Parser loaded {len(parser.commands)} commands")
    
    # Test 2: Check if BACKUP is loaded
    if "BACKUP" in parser.commands:
        print("✓ BACKUP command found in parser")
        cmd_data = parser.commands["BACKUP"]
        print(f"  - Syntax: {cmd_data['SYNTAX']}")
        print(f"  - uCODE Template: {cmd_data['UCODE_TEMPLATE']}")
    else:
        print("❌ BACKUP command NOT found in parser")
        return
    
    # Test 3: Parse BACKUP command
    test_commands = [
        "BACKUP --validate",
        "EXTENSION STATUS", 
        "TILE INFO AA340"
    ]
    
    for cmd in test_commands:
        try:
            result = parser.parse(cmd)
            print(f"✓ '{cmd}' → '{result}'")
        except Exception as e:
            print(f"❌ '{cmd}' failed: {e}")

if __name__ == "__main__":
    main()