#!/usr/bin/env python3
"""
Visual test for SmartPrompt completions
Run this to see how completions should work
"""

from core.input.smart_prompt import SmartPrompt

print("=" * 60)
print("SMARTPROMPT COMPLETION TEST")
print("=" * 60)
print()
print("Expected behavior:")
print("1. White block cursor blinks 3 times before prompt")
print("2. Type 'reb' and completions appear automatically below")
print("3. Press Tab to cycle through completions")
print("4. Press Enter to select/execute")
print()
print("Starting test...")
print()

sp = SmartPrompt()

# This will show blinking cursor then prompt
result = sp.ask()

print(f"\nYou entered: {result}")
