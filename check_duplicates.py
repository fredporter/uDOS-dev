#!/usr/bin/env python3
"""Check for duplicate function definitions across uDOS services."""

import os
from collections import Counter


def find_duplicates_in_file(filepath):
    """Find duplicate function definitions in a Python file."""
    dups = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            funcs = []
            for i, line in enumerate(f, 1):
                if line.startswith('def '):
                    name = line.split('(')[0].replace('def ', '').strip()
                    funcs.append((name, i))
            counts = Counter(n for n, _ in funcs)
            for name, count in counts.items():
                if count > 1:
                    lines = [l for n, l in funcs if n == name]
                    dups.append((name, lines))
    except Exception:
        pass
    return dups


def check_unused_imports(filepath):
    """Check for potentially unused imports (basic check)."""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()

        imports = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                if ' import ' in stripped:
                    # from X import Y, Z
                    parts = stripped.split(' import ')[1]
                    for part in parts.split(','):
                        name = part.strip().split(' as ')[-1].strip()
                        if name and name != '*':
                            imports.append((name, i))
                elif stripped.startswith('import '):
                    # import X
                    for part in stripped.replace('import ', '').split(','):
                        name = part.strip().split(' as ')[-1].strip()
                        if name:
                            imports.append((name, i))
    except Exception:
        pass
    return issues


def check_long_functions(filepath, max_lines=100):
    """Find functions that are too long."""
    long_funcs = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        func_starts = []
        for i, line in enumerate(lines):
            if line.startswith('def ') or line.startswith('async def '):
                name = line.split('(')[0].replace('def ', '').replace('async ', '').strip()
                func_starts.append((name, i))

        for j, (name, start) in enumerate(func_starts):
            if j + 1 < len(func_starts):
                end = func_starts[j + 1][1]
            else:
                end = len(lines)
            length = end - start
            if length > max_lines:
                long_funcs.append((name, start + 1, length))
    except Exception:
        pass
    return long_funcs


def main():
    dirs = ['core', 'wizard', 'services', 'commands', 'extensions', 'tui', 'mcp']

    print("=" * 60)
    print("DUPLICATE FUNCTION DEFINITIONS")
    print("=" * 60)
    dup_count = 0
    for d in dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            if '.archive' in root or '.venv' in root or '__pycache__' in root:
                continue
            for f in files:
                if f.endswith('.py'):
                    path = os.path.join(root, f)
                    dups = find_duplicates_in_file(path)
                    if dups:
                        print(f'\n{path}:')
                        for name, lines in dups:
                            print(f'  {name}: lines {lines}')
                            dup_count += 1

    if dup_count == 0:
        print("\nNo duplicates found!")
    else:
        print(f"\nTotal: {dup_count} duplicate function(s)")

    print("\n" + "=" * 60)
    print("VERY LONG FUNCTIONS (>100 lines)")
    print("=" * 60)
    long_count = 0
    for d in dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            if '.archive' in root or '.venv' in root or '__pycache__' in root:
                continue
            for f in files:
                if f.endswith('.py'):
                    path = os.path.join(root, f)
                    long_funcs = check_long_functions(path)
                    if long_funcs:
                        print(f'\n{path}:')
                        for name, line, length in long_funcs:
                            print(f'  {name} (line {line}): {length} lines')
                            long_count += 1

    if long_count == 0:
        print("\nNo very long functions found!")
    else:
        print(f"\nTotal: {long_count} long function(s)")


if __name__ == '__main__':
    main()

    # Additional checks
    print("\n" + "=" * 60)
    print("BARE EXCEPT CLAUSES (bad practice)")
    print("=" * 60)

    dirs = ['core', 'wizard', 'services', 'commands', 'extensions', 'tui', 'mcp']
    bare_excepts = []
    for d in dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            if '.archive' in root or '.venv' in root or '__pycache__' in root:
                continue
            for f in files:
                if f.endswith('.py'):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                            for i, line in enumerate(fp, 1):
                                stripped = line.strip()
                                if stripped == 'except:' or stripped.startswith('except :'):
                                    bare_excepts.append((path, i))
                    except Exception:
                        pass

    if bare_excepts:
        for path, line in bare_excepts[:15]:
            print(f'  {path}:{line}')
        if len(bare_excepts) > 15:
            print(f'  ... and {len(bare_excepts) - 15} more')
        print(f"\nTotal: {len(bare_excepts)} bare except(s)")
    else:
        print("\nNo bare except clauses found!")

    print("\n" + "=" * 60)
    print("TODO / FIXME COUNTS")
    print("=" * 60)

    todo_count = 0
    fixme_count = 0
    for d in dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            if '.archive' in root or '.venv' in root or '__pycache__' in root:
                continue
            for f in files:
                if f.endswith('.py'):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read()
                            todo_count += content.count('TODO')
                            fixme_count += content.count('FIXME')
                    except Exception:
                        pass

    print(f"TODO comments: {todo_count}")
    print(f"FIXME comments: {fixme_count}")
