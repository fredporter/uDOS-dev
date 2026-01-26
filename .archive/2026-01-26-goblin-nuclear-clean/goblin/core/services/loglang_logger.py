#!/usr/bin/env python3
"""
uDOS LogLang Logger v1.0
Compact human-readable logging using LogLang format

Format: [HH:MM:SS.mmm] LEVEL @SOURCE #CID $CATEGORY >ACTION: Message +metadata

Example:
[18:23:45.123] ERR @API #a3f2 $FILES >READ: Not found +path=wiki/test.md +code=404
[18:23:46.001] OK  @TAURI #b7e1 $FETCH >DONE: Loaded +count=69 +time=53ms

See: memory/logs/LOGLANG-SPEC.md
"""

import os
import sys
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import deque
import random
import json

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "memory" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class LogLangLogger:
    """Thread-safe logger using compact LogLang format"""

    def __init__(self, source: str = "CORE"):
        self.source = source.upper()
        self.lock = threading.Lock()

        # In-memory buffer for real-time streaming (last 1000 entries)
        self.buffer = deque(maxlen=1000)

        # Log file paths
        today = datetime.now().strftime("%Y-%m-%d")
        self.unified_log = LOG_DIR / f"unified-{today}.log"
        self.error_log = LOG_DIR / f"error-{today}.log"
        self.source_log = LOG_DIR / f"{self.source.lower()}-{today}.log"

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata as +key=value pairs"""
        if not metadata:
            return ""

        parts = []
        for key, value in metadata.items():
            if value is None:
                continue

            # Quote strings with spaces
            if isinstance(value, str) and " " in value:
                parts.append(f'+{key}="{value}"')
            else:
                parts.append(f"+{key}={value}")

        return " " + " ".join(parts) if parts else ""

    def _write_log(
        self,
        level: str,
        category: str,
        action: str,
        message: str,
        cid: Optional[str] = None,
        **metadata,
    ):
        """Write log entry to files and buffer"""
        # Generate correlation ID if not provided
        if not cid:
            cid = f"{random.randint(0, 65535):04x}"

        # Format timestamp with milliseconds
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Format metadata
        meta_str = self._format_metadata(metadata)

        # Build log line
        log_line = f"[{timestamp}] {level} @{self.source} #{cid} ${category} >{action}: {message}{meta_str}"

        # Write to files
        with self.lock:
            # Unified log (all messages)
            with open(self.unified_log, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")

            # Source-specific log
            with open(self.source_log, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")

            # Error log (errors and critical only)
            if level in ["ERR", "CRT"]:
                with open(self.error_log, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")

            # Add to buffer for real-time streaming
            self.buffer.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": level.strip(),
                    "source": self.source,
                    "correlationId": cid,
                    "category": category,
                    "action": action,
                    "message": message,
                    "metadata": metadata,
                    "raw": log_line,
                }
            )

    # Logging methods
    def ok(
        self,
        category: str,
        action: str,
        message: str,
        cid: Optional[str] = None,
        **metadata,
    ):
        """Log success"""
        self._write_log("OK ", category, action, message, cid, **metadata)

    def info(
        self,
        category: str,
        action: str,
        message: str,
        cid: Optional[str] = None,
        **metadata,
    ):
        """Log info"""
        self._write_log("INF", category, action, message, cid, **metadata)

    def warning(
        self,
        category: str,
        action: str,
        message: str,
        cid: Optional[str] = None,
        **metadata,
    ):
        """Log warning"""
        self._write_log("WRN", category, action, message, cid, **metadata)

    def error(
        self,
        category: str,
        action: str,
        message: str,
        cid: Optional[str] = None,
        **metadata,
    ):
        """Log error"""
        self._write_log("ERR", category, action, message, cid, **metadata)

    def critical(
        self,
        category: str,
        action: str,
        message: str,
        cid: Optional[str] = None,
        **metadata,
    ):
        """Log critical"""
        self._write_log("CRT", category, action, message, cid, **metadata)

    def debug(
        self,
        category: str,
        action: str,
        message: str,
        cid: Optional[str] = None,
        **metadata,
    ):
        """Log debug"""
        self._write_log("DBG", category, action, message, cid, **metadata)

    def trace(
        self,
        category: str,
        action: str,
        message: str,
        cid: Optional[str] = None,
        **metadata,
    ):
        """Log trace"""
        self._write_log("TRC", category, action, message, cid, **metadata)

    def get_recent(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs from buffer"""
        with self.lock:
            return list(self.buffer)[-count:]

    def search(
        self,
        query: Optional[str] = None,
        level: Optional[str] = None,
        category: Optional[str] = None,
        cid: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search logs in buffer"""
        results = []

        with self.lock:
            for entry in reversed(self.buffer):
                # Apply filters
                if level and entry["level"] != level:
                    continue
                if category and entry["category"] != category:
                    continue
                if cid and entry["correlationId"] != cid:
                    continue
                if query and query.lower() not in entry["raw"].lower():
                    continue

                results.append(entry)

                if len(results) >= limit:
                    break

        return results


# Global logger instances
_loggers: Dict[str, LogLangLogger] = {}
_lock = threading.Lock()


def get_logger(source: str = "CORE") -> LogLangLogger:
    """Get or create logger for source"""
    source = source.upper()
    with _lock:
        if source not in _loggers:
            _loggers[source] = LogLangLogger(source)
        return _loggers[source]


# Convenience module-level logger
log = get_logger("CORE")


if __name__ == "__main__":
    # Test the logger
    print("Testing LogLangLogger...")
    print(f"Logs will be written to: {LOG_DIR}\n")

    # Test different log levels
    log.info("INIT", "START", "Logger test started")
    log.debug("INIT", "LOAD", "Debug message", test="value", count=123)
    log.warning("CACHE", "READ", "Cache miss", key="test-key", retry=True)
    log.error("FILES", "READ", "File not found", path="/test/file.txt", code=404)
    log.ok("INIT", "DONE", "Test completed", duration="123ms")

    # Test correlation ID tracking
    cid = "test"
    log.info("FETCH", "REQ", "Starting request", cid=cid, url="http://test")
    log.info("FETCH", "RESP", "Got response", cid=cid, code=200, bytes=1234)
    log.ok("FETCH", "DONE", "Request complete", cid=cid, total="145ms")

    # Test search
    print("\nRecent logs:")
    recent = log.get_recent(5)
    for entry in recent:
        print(entry["raw"])

    # Test correlation search
    print(f"\nLogs with CID '{cid}':")
    cid_logs = log.search(cid=cid)
    for entry in cid_logs:
        print(entry["raw"])

    print(f"\n✓ Test complete. Check log files in: {LOG_DIR}")
