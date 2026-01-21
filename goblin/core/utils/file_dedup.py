"""
Shared file deduplication utilities
Used by: backup_handler, sandbox_handler, maintenance_handler

Provides consistent file hashing and duplicate detection across uDOS.

Version: 1.0.0
Author: uDOS Core Team
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


def calculate_file_hash(
    filepath: Path, algorithm: str = "sha256", chunk_size: int = 65536
) -> str:
    """
    Calculate file hash using specified algorithm.

    Args:
        filepath: Path to file to hash
        algorithm: Hash algorithm ('md5', 'sha256', 'sha1')
        chunk_size: Read chunk size in bytes (default: 64KB)

    Returns:
        Hexadecimal hash string

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If algorithm not supported

    Example:
        >>> from pathlib import Path
        >>> hash_value = calculate_file_hash(Path('file.txt'), 'sha256')
        >>> print(hash_value)
        '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Get hasher for algorithm
    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(
            f"Unsupported hash algorithm: {algorithm}. Use: md5, sha1, sha256"
        )

    # Read file in chunks for memory efficiency
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def find_duplicate_files(
    directory: Path,
    exclude_hidden: bool = True,
    algorithm: str = "sha256",
    progress_callback: Optional[callable] = None,
) -> Dict[str, List[Path]]:
    """
    Find duplicate files in directory, grouped by hash.

    Args:
        directory: Directory to scan
        exclude_hidden: Skip files starting with '.' (default: True)
        algorithm: Hash algorithm to use ('md5', 'sha256', 'sha1')
        progress_callback: Optional callback function(current, total, filepath)

    Returns:
        Dict mapping hash -> list of duplicate file paths
        Only returns hashes with 2+ files (actual duplicates)

    Example:
        >>> from pathlib import Path
        >>> duplicates = find_duplicate_files(Path('memory/.archive'))
        >>> for hash_val, files in duplicates.items():
        ...     print(f"Hash {hash_val[:12]}... has {len(files)} copies")
        ...     for f in files:
        ...         print(f"  - {f}")
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    # Build hash map
    hash_to_files = defaultdict(list)

    # Collect all files
    all_files = [
        f
        for f in directory.rglob("*")
        if f.is_file() and (not exclude_hidden or not f.name.startswith("."))
    ]

    total_files = len(all_files)

    # Hash each file
    for idx, file_path in enumerate(all_files, 1):
        try:
            file_hash = calculate_file_hash(file_path, algorithm)
            hash_to_files[file_hash].append(file_path)

            if progress_callback:
                progress_callback(idx, total_files, file_path)

        except Exception as e:
            # Skip files that can't be read (permissions, I/O errors, etc.)
            continue

    # Filter to only duplicates (2+ files with same hash)
    duplicates = {
        hash_val: sorted(files, key=lambda f: str(f))  # Consistent ordering
        for hash_val, files in hash_to_files.items()
        if len(files) > 1
    }

    return duplicates


def get_duplicate_stats(duplicates: Dict[str, List[Path]]) -> Dict[str, any]:
    """
    Calculate statistics about duplicate files.

    Args:
        duplicates: Dict from find_duplicate_files()

    Returns:
        Dict with statistics:
        - duplicate_groups: Number of duplicate groups
        - duplicate_files: Total duplicate file count (excluding first in each group)
        - wasted_space: Total bytes that could be reclaimed
        - wasted_space_mb: Wasted space in MB

    Example:
        >>> duplicates = find_duplicate_files(Path('memory/.archive'))
        >>> stats = get_duplicate_stats(duplicates)
        >>> print(f"Can reclaim {stats['wasted_space_mb']:.2f} MB")
    """
    duplicate_groups = len(duplicates)
    duplicate_files = sum(len(files) - 1 for files in duplicates.values())
    wasted_space = 0

    # Calculate wasted space (all files except first in each group)
    for files in duplicates.values():
        for duplicate_file in files[1:]:  # Skip first (kept copy)
            try:
                wasted_space += duplicate_file.stat().st_size
            except Exception:
                pass  # Skip files with stat errors

    return {
        "duplicate_groups": duplicate_groups,
        "duplicate_files": duplicate_files,
        "wasted_space": wasted_space,
        "wasted_space_mb": wasted_space / (1024 * 1024),
    }


def remove_duplicates(
    duplicates: Dict[str, List[Path]], dry_run: bool = True, keep_first: bool = True
) -> Tuple[int, int, int]:
    """
    Remove duplicate files, keeping one copy of each.

    Args:
        duplicates: Dict from find_duplicate_files()
        dry_run: If True, don't actually delete (default: True)
        keep_first: If True, keep first file in each group (default: True)

    Returns:
        Tuple of (removed_count, failed_count, bytes_reclaimed)

    Example:
        >>> duplicates = find_duplicate_files(Path('memory/.archive'))
        >>> removed, failed, bytes_freed = remove_duplicates(duplicates, dry_run=False)
        >>> print(f"Removed {removed} files, reclaimed {bytes_freed / 1024 / 1024:.2f} MB")
    """
    removed_count = 0
    failed_count = 0
    bytes_reclaimed = 0

    for files in duplicates.values():
        # Determine which files to remove
        files_to_remove = files[1:] if keep_first else files[:-1]

        for duplicate_file in files_to_remove:
            try:
                file_size = duplicate_file.stat().st_size

                if not dry_run:
                    duplicate_file.unlink()

                removed_count += 1
                bytes_reclaimed += file_size

            except Exception as e:
                failed_count += 1

    return (removed_count, failed_count, bytes_reclaimed)


# Convenience aliases for backward compatibility
def calculate_md5(filepath: Path) -> str:
    """Calculate MD5 hash of file (convenience wrapper)."""
    return calculate_file_hash(filepath, "md5")


def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA-256 hash of file (convenience wrapper)."""
    return calculate_file_hash(filepath, "sha256")
