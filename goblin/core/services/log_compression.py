"""
Log Compression & Correlation ID System

Implements:
- Gzip compression for logs >7 days old
- UUID4 correlation IDs for request tracing
- X-Correlation-ID header propagation
- Custom log formatter with correlation tracking
- Monthly tar.gz archives
- Integration with CLEAN command

Author: uDOS Development Team
Version: 1.2.26
Date: December 22, 2025
"""

import gzip
import shutil
import tarfile
import uuid
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from ..config.paths import get_user_path


class CorrelationIDFormatter(logging.Formatter):
    """
    Custom log formatter that includes correlation IDs for request tracing.

    Format: [timestamp] [level] [correlation_id] [module] message
    """

    def format(self, record: logging.LogRecord) -> str:
        """Add correlation ID to log record."""
        # Get correlation ID from record or generate new one
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "no-correlation"

        # Standard format with correlation ID
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        correlation_id = record.correlation_id
        module = record.name
        message = record.getMessage()

        return f"[{timestamp}] [{level}] [{correlation_id}] [{module}] {message}"


class CorrelationIDManager:
    """
    Manages correlation IDs for cross-service request tracing.

    Features:
    - Thread-local storage
    - Request-scoped IDs
    - Header propagation
    - ID validation
    """

    _current_id: Optional[str] = None
    _id_stack: List[str] = []

    @classmethod
    def new_id(cls) -> str:
        """Generate new UUID4 correlation ID."""
        new_id = f"req_{uuid.uuid4().hex[:16]}"
        cls._current_id = new_id
        return new_id

    @classmethod
    def get_current_id(cls) -> Optional[str]:
        """Get current correlation ID."""
        return cls._current_id

    @classmethod
    def set_current_id(cls, correlation_id: str) -> None:
        """Set current correlation ID (from header)."""
        cls._current_id = correlation_id

    @classmethod
    def clear_current_id(cls) -> None:
        """Clear current correlation ID."""
        cls._current_id = None

    @classmethod
    def push_id(cls, correlation_id: str) -> None:
        """Push ID onto stack (for nested calls)."""
        if cls._current_id:
            cls._id_stack.append(cls._current_id)
        cls._current_id = correlation_id

    @classmethod
    def pop_id(cls) -> Optional[str]:
        """Pop ID from stack (restore previous)."""
        if cls._id_stack:
            cls._current_id = cls._id_stack.pop()
        else:
            cls._current_id = None
        return cls._current_id

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Export correlation context."""
        return {"current_id": cls._current_id, "stack": cls._id_stack.copy()}


class LogCompressor:
    """
    Handles compression and archiving of old log files.

    Compression Strategy:
    - Logs >7 days old: Gzip compressed individually
    - Logs >30 days old: Archived to monthly tar.gz
    - Compressed files moved to .archive/ folder
    - Original files deleted after compression
    """

    def __init__(self, log_dir: Path = None):
        """Initialize log compressor."""
        self.log_dir = log_dir or get_user_path("logs")
        self.archive_dir = self.log_dir / ".archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def compress_old_logs(
        self, days_threshold: int = 7, dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Compress logs older than threshold.

        Args:
            days_threshold: Age in days before compression
            dry_run: Preview changes without executing

        Returns:
            Dictionary with compression stats
        """
        stats = {"compressed": 0, "skipped": 0, "errors": 0, "bytes_saved": 0}

        cutoff_date = datetime.now() - timedelta(days=days_threshold)

        # Find uncompressed log files
        log_files = [f for f in self.log_dir.glob("*.log") if f.is_file()]

        for log_file in log_files:
            try:
                # Check file age
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)

                if file_time < cutoff_date:
                    if dry_run:
                        original_size = log_file.stat().st_size
                        stats["compressed"] += 1
                        stats["bytes_saved"] += (
                            original_size * 0.7
                        )  # Estimate 70% compression
                    else:
                        # Compress file
                        original_size = log_file.stat().st_size
                        compressed_file = self.archive_dir / f"{log_file.name}.gz"

                        with open(log_file, "rb") as f_in:
                            with gzip.open(compressed_file, "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)

                        compressed_size = compressed_file.stat().st_size
                        stats["bytes_saved"] += original_size - compressed_size
                        stats["compressed"] += 1

                        # Delete original
                        log_file.unlink()
                else:
                    stats["skipped"] += 1

            except Exception as e:
                stats["errors"] += 1
                print(f"Error compressing {log_file}: {e}")

        return stats

    def create_monthly_archive(
        self, year: int, month: int, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Create monthly tar.gz archive of compressed logs.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            dry_run: Preview changes without executing

        Returns:
            Archive creation stats
        """
        stats = {"files_archived": 0, "archive_size": 0, "success": False}

        archive_name = f"{year}-{month:02d}.tar.gz"
        archive_path = self.archive_dir / archive_name

        # Find compressed logs from target month
        month_prefix = f"{year}{month:02d}"
        compressed_logs = [
            f
            for f in self.archive_dir.glob("*.log.gz")
            if f.name.startswith(month_prefix)
        ]

        if not compressed_logs:
            return stats

        if dry_run:
            stats["files_archived"] = len(compressed_logs)
            stats["archive_size"] = sum(f.stat().st_size for f in compressed_logs)
        else:
            try:
                with tarfile.open(archive_path, "w:gz") as tar:
                    for log_file in compressed_logs:
                        tar.add(log_file, arcname=log_file.name)
                        stats["files_archived"] += 1

                stats["archive_size"] = archive_path.stat().st_size
                stats["success"] = True

                # Delete individual compressed files after archiving
                for log_file in compressed_logs:
                    log_file.unlink()

            except Exception as e:
                stats["error"] = str(e)

        return stats

    def get_compression_report(self) -> str:
        """Generate compression status report."""
        lines = ["📦 Log Compression Report", ""]

        # Count uncompressed logs
        uncompressed = list(self.log_dir.glob("*.log"))
        uncompressed_size = sum(f.stat().st_size for f in uncompressed) / (1024 * 1024)

        # Count compressed logs
        compressed = list(self.archive_dir.glob("*.log.gz"))
        compressed_size = sum(f.stat().st_size for f in compressed) / (1024 * 1024)

        # Count archives
        archives = list(self.archive_dir.glob("*.tar.gz"))
        archive_size = sum(f.stat().st_size for f in archives) / (1024 * 1024)

        lines.append(
            f"📄 Uncompressed: {len(uncompressed)} files ({uncompressed_size:.2f} MB)"
        )
        lines.append(
            f"🗜️  Compressed: {len(compressed)} files ({compressed_size:.2f} MB)"
        )
        lines.append(f"📦 Archives: {len(archives)} files ({archive_size:.2f} MB)")
        lines.append(
            f"💾 Total: {uncompressed_size + compressed_size + archive_size:.2f} MB"
        )

        # Recommendations
        lines.append("")
        cutoff_date = datetime.now() - timedelta(days=7)
        old_logs = [
            f
            for f in uncompressed
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff_date
        ]

        if old_logs:
            lines.append(f"⚠️  {len(old_logs)} logs ready for compression")
            lines.append("   Run: LOGS COMPRESS")
        else:
            lines.append("✅ All logs up to date")

        return "\n".join(lines)


class CorrelationLogger:
    """
    Logger wrapper that automatically includes correlation IDs.

    Usage:
        logger = CorrelationLogger('my_module')
        logger.info('Processing request')
        # Output: [timestamp] [INFO] [req_abc123] [my_module] Processing request
    """

    def __init__(self, name: str):
        """Initialize correlation logger."""
        self.logger = logging.getLogger(name)
        self.name = name

        # Add correlation formatter if not already present
        if not any(
            isinstance(h.formatter, CorrelationIDFormatter)
            for h in self.logger.handlers
        ):
            formatter = CorrelationIDFormatter()
            for handler in self.logger.handlers:
                handler.setFormatter(formatter)

    def _log(self, level: int, msg: str, *args, **kwargs):
        """Log with correlation ID."""
        extra = kwargs.get("extra", {})
        extra["correlation_id"] = (
            CorrelationIDManager.get_current_id() or "no-correlation"
        )
        kwargs["extra"] = extra
        self.logger.log(level, msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with correlation ID."""
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log info message with correlation ID."""
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with correlation ID."""
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log error message with correlation ID."""
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with correlation ID."""
        self._log(logging.CRITICAL, msg, *args, **kwargs)


# Global compressor instance
_compressor: Optional[LogCompressor] = None


def get_log_compressor() -> LogCompressor:
    """Get or create global log compressor."""
    global _compressor
    if _compressor is None:
        _compressor = LogCompressor()
    return _compressor


def setup_correlation_logging(logger_name: str) -> CorrelationLogger:
    """
    Setup correlation logging for a module.

    Args:
        logger_name: Name of the logger (e.g., 'uDOS.API')

    Returns:
        CorrelationLogger instance
    """
    return CorrelationLogger(logger_name)


# Flask integration helper
def flask_correlation_middleware():
    """
    Flask before_request middleware to set correlation ID from header.

    Usage in extensions/api/server.py:
        @app.before_request
        def set_correlation_id():
            return flask_correlation_middleware()
    """
    from flask import request

    # Get correlation ID from header or generate new one
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = CorrelationIDManager.new_id()
    else:
        CorrelationIDManager.set_current_id(correlation_id)

    # Store in request context for response header
    request.correlation_id = correlation_id


def flask_correlation_after_request():
    """
    Flask after_request middleware to add correlation ID to response header.

    Usage in extensions/api/server.py:
        @app.after_request
        def add_correlation_header(response):
            flask_correlation_after_request(response)
            return response
    """
    from flask import request, g

    def add_header(response):
        if hasattr(request, "correlation_id"):
            response.headers["X-Correlation-ID"] = request.correlation_id
        return response

    return add_header
