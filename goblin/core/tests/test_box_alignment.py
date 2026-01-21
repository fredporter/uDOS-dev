#!/usr/bin/env python3
"""Test box drawing alignment with fixed code"""

from dev.goblin.core.utils.column_formatter import ColumnFormatter, ColumnConfig

# Test with 60-char viewport (like the reported issue)
# The formatter should be initialized with width that accounts for viewport correctly

# Simulate viewport of 60 chars
formatter = ColumnFormatter(ColumnConfig(width=56))  # 60 - 4 for margins

top = formatter.box_top()
sep = formatter.box_separator()
line = formatter.box_line("Test Content", align="center")
bottom = formatter.box_bottom()

print(f"Top length:    {len(top)} chars")
print(f"Sep length:    {len(sep)} chars")
print(f"Line length:   {len(line)} chars")
print(f"Bottom length: {len(bottom)} chars")

# All should be the same length
lengths = {len(top), len(sep), len(line), len(bottom)}
if len(lengths) == 1:
    print(f"\n✓ All lines are {list(lengths)[0]} characters wide (CORRECT)")
else:
    print(f"\n✗ Lines have different widths: {lengths} (INCORRECT)")

# Visual check
print("\n" + top)
print(line)
print(sep)
print(line)
print(bottom)
