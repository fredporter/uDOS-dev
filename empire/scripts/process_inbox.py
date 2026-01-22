"""Process files from memory/inbox with strict inbox-only path enforcement."""

import argparse
import shutil
from pathlib import Path
from typing import List

from .path_guard import resolve_inbox_path, INBOX_ROOT


def find_files(pattern: str) -> List[Path]:
    """Find files in memory/inbox matching glob pattern."""
    return sorted(resolve_inbox_path(".").glob(pattern))


def process_file(path: Path, output_dir: Path) -> None:
    """Stub processor: copies file to processed/ while preserving name.

    Replace this with real processing logic (CSV parse, enrichment, etc.).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / path.name
    shutil.copy2(path, target)


def main() -> None:
    parser = argparse.ArgumentParser(description="Process inbox files (memory/inbox)")
    parser.add_argument(
        "--pattern", default="*", help="Glob pattern relative to inbox root"
    )
    parser.add_argument(
        "--output-subdir",
        default="processed",
        help="Subdirectory under inbox for outputs",
    )
    args = parser.parse_args()

    files = find_files(args.pattern)
    if not files:
        print("No files matched in memory/inbox")
        return

    output_dir = resolve_inbox_path(args.output_subdir)
    for path in files:
        process_file(path, output_dir)
        print(f"Processed {path.name} -> {output_dir}")


if __name__ == "__main__":
    main()
