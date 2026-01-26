"""
Logging Manager - Flat Directory Structure with Filename-Based Categorization

This module provides centralized logging with:
- Flat directory structure (memory/logs/)
- Filename-based categorization (prefix-date.log)
- Automatic log rotation (daily)
- Retention policy enforcement (auto-delete old logs)
- Structured logging (JSON format option)
- Context injection (user, session, timestamp)
- Search/filter utilities
- Location privacy masking (v1.0.0.56+)

Usage:
    from dev.goblin.core.services.logging_manager import get_logger

    logger = get_logger('system-startup')
    logger.info('uDOS starting...')
    # Creates: memory/logs/system-startup-2025-11-28.log

Version: 1.1.7
"""

import logging
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import gzip
import shutil
from dev.goblin.core.utils.paths import PATHS


class FlatFileHandler(logging.FileHandler):
    """Custom file handler with flat directory structure and daily rotation."""

    def __init__(self, category: str, log_dir: Path, date_format: str = "%Y-%m-%d"):
        """Initialize handler with category-based filename.

        Args:
            category: Log category (e.g., 'system-startup', 'ucode-execution')
            log_dir: Base log directory (memory/logs/)
            date_format: Date format for filename (default: YYYY-MM-DD)
        """
        self.category = category
        self.log_dir = Path(log_dir)
        self.date_format = date_format
        self.current_date = None

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize with current filename
        filename = self._get_current_filename()
        super().__init__(filename, mode="a", encoding="utf-8")

    def _get_current_filename(self) -> str:
        """Get current log filename based on category and date."""
        date_str = datetime.now().strftime(self.date_format)
        self.current_date = date_str
        return str(self.log_dir / f"{self.category}-{date_str}.log")

    def emit(self, record: logging.LogRecord):
        """Emit log record, rotating file if date changed."""
        # Check if date has changed (daily rotation)
        current_date = datetime.now().strftime(self.date_format)
        if current_date != self.current_date:
            # Date changed, rotate to new file
            self.close()
            self.baseFilename = self._get_current_filename()
            self.stream = self._open()

        super().emit(record)


class CategoryFormatter(logging.Formatter):
    """Formatter that adds category to log record."""

    def __init__(self, category: str, *args, **kwargs):
        """Initialize formatter with category.

        Args:
            category: Log category to inject into records
            *args: Passed to logging.Formatter
            **kwargs: Passed to logging.Formatter
        """
        super().__init__(*args, **kwargs)
        self.category = category

    def format(self, record: logging.LogRecord) -> str:
        """Add category to record before formatting."""
        record.category = self.category
        return super().format(record)


class ContextFilter(logging.Filter):
    """Filter that injects context into log records."""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """Initialize filter with context.

        Args:
            context: Context dictionary to inject
        """
        super().__init__()
        self.context = context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Inject context into record."""
        if self.context:
            record.context = self.context
        # Ensure source field exists (default to 'unknown')
        if not hasattr(record, "source"):
            record.source = self.context.get("source", "unknown")
        return True


class LocationMaskingFilter(logging.Filter):
    """
    Filter that masks location data in log messages for privacy.

    Converts full tile addresses to masked format:
        L300:BD14:AA10:BB15:CC20 → L300:BD14-####

    Part of uDOS privacy-first location policy (v1.0.0.56+).
    """

    # Regex to match full tile addresses (layer + 2+ coordinate parts)
    # Matches: L300:BD14:AA10, L300:BD14:AA10:BB15, L300:BD14:AA10:BB15:CC20
    TILE_PATTERN = re.compile(
        r"L(\d{3}):([A-Z]{2}\d{2}):([A-Z]{2}\d{2}(?::[A-Z]{2}\d{2})*)"
    )

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask location data in message."""
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = self._mask_locations(record.msg)
        return True

    def _mask_locations(self, message: str) -> str:
        """Replace full tile addresses with masked versions."""
        import hashlib

        def mask_match(match):
            layer = match.group(1)
            regional = match.group(2)
            precision = match.group(3)
            # Hash the precision part
            hash_hex = hashlib.sha256(precision.encode()).hexdigest()[:4]
            return f"L{layer}:{regional}-{hash_hex}"

        return self.TILE_PATTERN.sub(mask_match, message)


class SourceAdapter(logging.LoggerAdapter):
    """Logger adapter that adds source field to all log entries.

    Sources: tui, tauri, api, system
    """

    def process(self, msg, kwargs):
        """Add source to extra dict."""
        extra = kwargs.get("extra", {})
        extra["source"] = self.extra.get("source", "unknown")
        kwargs["extra"] = extra
        return msg, kwargs


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, category: str, include_context: bool = True):
        """Initialize formatter.

        Args:
            category: Log category
            include_context: Include context fields (user, session, etc.)
        """
        super().__init__()
        self.category = category
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """Format record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "category": self.category,
            "source": getattr(record, "source", "unknown"),
            "message": record.getMessage(),
        }

        # Add context if available
        if self.include_context and hasattr(record, "context"):
            log_data["context"] = record.context

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class LoggingManager:
    """Central logging manager with flat directory structure."""

    # Log retention policies (in days)
    RETENTION_POLICIES = {
        "system": 30,  # System logs: 30 days
        "ucode": 30,  # uCODE logs: 30 days
        "command": 30,  # Command logs: 30 days
        "web": 30,  # Web logs: 30 days
        "ai": 30,  # AI logs: 30 days
        "extension": 30,  # Extension logs: 30 days
        "error": 90,  # Error logs: 90 days
        "debug": 7,  # Debug logs: 7 days
        "audit": 90,  # Audit logs: 90 days
        "mission": None,  # Mission logs: never auto-delete
    }

    def __init__(self, log_dir: str = str(PATHS.MEMORY_LOGS)):
        """Initialize logging manager.

        Args:
            log_dir: Base directory for all logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.loggers: Dict[str, logging.Logger] = {}

    def get_logger(
        self,
        category: str,
        level: int = logging.INFO,
        structured: bool = False,
        context: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> logging.Logger:
        """Get or create logger for category.

        Args:
            category: Log category (e.g., 'system-startup')
            level: Logging level (DEBUG, INFO, WARN, ERROR, CRITICAL)
            structured: Use JSON structured format
            context: Additional context (user, session, etc.)
            source: Log source identifier (tui, tauri, api, system)

        Returns:
            Configured logger instance
        """
        # Create cache key including source for separate loggers per source
        cache_key = f"{category}:{source or 'default'}"

        # Return existing logger if already created
        if cache_key in self.loggers:
            return self.loggers[cache_key]

        # Create new logger
        logger = logging.Logger(category, level=level)

        # Add context filter with source
        ctx = context or {}
        if source:
            ctx["source"] = source
        context_filter = ContextFilter(ctx)
        logger.addFilter(context_filter)

        # Add location masking filter for privacy (v1.0.0.56+)
        location_filter = LocationMaskingFilter()
        logger.addFilter(location_filter)

        # Add flat file handler
        handler = FlatFileHandler(category, self.log_dir)

        # Set formatter - include source in text format
        if structured:
            formatter = StructuredFormatter(category, include_context=True)
        else:
            # Include source in log format: [timestamp] [LEVEL] [category] [source] message
            fmt = "[%(asctime)s] [%(levelname)s] [%(category)s]"
            if source:
                fmt += f" [{source}]"
            fmt += " %(message)s"
            formatter = CategoryFormatter(category, fmt, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

        # Cache logger with source-aware key
        self.loggers[cache_key] = logger

        return logger

    def enforce_retention_policy(self, dry_run: bool = False) -> Dict[str, int]:
        """Enforce log retention policies (auto-delete old logs).

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            Dictionary of deleted file counts by category
        """
        deleted_counts = {}
        now = datetime.now()

        for log_file in self.log_dir.glob("*.log"):
            # Extract category from filename (prefix before first dash)
            parts = log_file.stem.split("-")
            if len(parts) < 2:
                continue  # Skip malformed filenames

            # Get base category (first part before dash)
            base_category = parts[0]

            # Get retention days for this category
            retention_days = self.RETENTION_POLICIES.get(base_category)

            # Skip if no auto-delete policy
            if retention_days is None:
                continue

            # Extract date from filename (last 3 parts: YYYY-MM-DD)
            if len(parts) >= 4:
                try:
                    date_str = "-".join(parts[-3:])
                    log_date = datetime.strptime(date_str, "%Y-%m-%d")

                    # Check if older than retention period
                    age_days = (now - log_date).days
                    if age_days > retention_days:
                        if not dry_run:
                            log_file.unlink()
                        deleted_counts[base_category] = (
                            deleted_counts.get(base_category, 0) + 1
                        )
                except ValueError:
                    # Couldn't parse date, skip
                    continue

        return deleted_counts

    def archive_logs(self, month: Optional[str] = None) -> Optional[Path]:
        """Archive logs to compressed tarball.

        Args:
            month: Month to archive (YYYY-MM), defaults to last month

        Returns:
            Path to created archive, or None if no logs to archive
        """
        if month is None:
            # Default to last month
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            month = last_month.strftime("%Y-%m")

        # Find logs matching month
        pattern = f"*-{month}-*.log"
        log_files = list(self.log_dir.glob(pattern))

        if not log_files:
            return None

        # Create archive directory
        archive_dir = PATHS.MEMORY_LOGS / ".archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Create tar.gz archive
        archive_path = archive_dir / f"{month}.tar.gz"

        import tarfile

        with tarfile.open(archive_path, "w:gz") as tar:
            for log_file in log_files:
                tar.add(log_file, arcname=log_file.name)

        # Delete original files after archiving
        for log_file in log_files:
            log_file.unlink()

        return archive_path

    def search_logs(
        self,
        pattern: str,
        category: Optional[str] = None,
        days: int = 7,
        case_sensitive: bool = False,
    ) -> List[Dict[str, str]]:
        """Search logs for pattern.

        Args:
            pattern: Search pattern (regex supported)
            category: Limit to specific category
            days: Number of days to search (default: 7)
            case_sensitive: Case-sensitive search

        Returns:
            List of matching log entries with metadata
        """
        import re

        matches = []
        cutoff_date = datetime.now() - timedelta(days=days)

        # Build regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        # Search log files
        for log_file in self.log_dir.glob("*.log"):
            # Filter by category if specified
            if category and not log_file.stem.startswith(category):
                continue

            # Check file age
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff_date:
                continue

            # Search file contents
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            matches.append(
                                {
                                    "file": log_file.name,
                                    "line_num": line_num,
                                    "line": line.rstrip(),
                                    "category": log_file.stem.split("-")[0],
                                }
                            )
            except (IOError, UnicodeDecodeError):
                # Skip problematic files
                continue

        return matches

    def get_log_stats(self) -> Dict[str, Any]:
        """Get statistics about current logs.

        Returns:
            Dictionary with log statistics
        """
        stats = {
            "total_files": 0,
            "total_size_mb": 0,
            "by_category": {},
            "oldest_log": None,
            "newest_log": None,
        }

        oldest_time = None
        newest_time = None

        for log_file in self.log_dir.glob("*.log"):
            stats["total_files"] += 1

            # Get size
            size_bytes = log_file.stat().st_size
            stats["total_size_mb"] += size_bytes / (1024 * 1024)

            # Get category
            category = log_file.stem.split("-")[0]
            if category not in stats["by_category"]:
                stats["by_category"][category] = {"count": 0, "size_mb": 0}
            stats["by_category"][category]["count"] += 1
            stats["by_category"][category]["size_mb"] += size_bytes / (1024 * 1024)

            # Track oldest/newest
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if oldest_time is None or mtime < oldest_time:
                oldest_time = mtime
                stats["oldest_log"] = log_file.name
            if newest_time is None or mtime > newest_time:
                newest_time = mtime
                stats["newest_log"] = log_file.name

        # Round sizes
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        for cat_stats in stats["by_category"].values():
            cat_stats["size_mb"] = round(cat_stats["size_mb"], 2)

        return stats


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


# Log source constants
class LogSource:
    """Log source identifiers for unified logging."""

    TUI = "tui"  # Terminal UI
    TAURI = "tauri"  # Tauri desktop app
    API = "api"  # REST API server
    SYSTEM = "system"  # System/background processes
    WIZARD = "wizard"  # Wizard Server


def get_logging_manager() -> LoggingManager:
    """Get global logging manager instance."""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager


def get_logger(category: str, source: Optional[str] = None, **kwargs) -> logging.Logger:
    """Convenience function to get logger.

    Args:
        category: Log category (e.g., 'session-commands', 'api-server')
        source: Log source (tui, tauri, api, system, wizard)
        **kwargs: Additional arguments for get_logger()

    Returns:
        Configured logger

    Example:
        # TUI command logging
        logger = get_logger('session-commands', source=LogSource.TUI)
        logger.info('User entered: HELP')

        # API request logging
        logger = get_logger('api-requests', source=LogSource.API)
        logger.info('POST /api/execute')
    """
    manager = get_logging_manager()
    return manager.get_logger(category, source=source, **kwargs)
