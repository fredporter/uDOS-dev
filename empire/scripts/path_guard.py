"""Path guard helpers to enforce inbox-only file access for Empire scripts."""

from pathlib import Path
from typing import Union

# Processing root: memory/inbox (resolved relative to repo root)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
INBOX_ROOT = (PROJECT_ROOT / "memory" / "inbox").resolve()


def resolve_inbox_path(relative_path: Union[str, Path]) -> Path:
    """Resolve a path under memory/inbox, raising if it escapes the inbox tree.

    Args:
        relative_path: Relative path inside the inbox (e.g., "processed/output.csv").

    Returns:
        Absolute Path guaranteed to be within memory/inbox.
    """
    candidate = (INBOX_ROOT / relative_path).resolve()

    # Python <3.9 compatibility for is_relative_to
    try:
        within = candidate.is_relative_to(INBOX_ROOT)  # type: ignore[attr-defined]
    except AttributeError:
        within = str(candidate).startswith(str(INBOX_ROOT))

    if not within:
        raise ValueError(f"Path {candidate} is outside inbox root {INBOX_ROOT}")

    return candidate
