"""
uDOS Debug Panel Service (v1.2.30)

Multi-source live log viewer with streaming support.

Enhances core/ui/debug_panel.py with:
- Multiple log source monitoring
- WebSocket streaming support
- Correlation ID tracking
- Error context aggregation
- Cross-interface API

Author: uDOS Development Team
Version: 1.2.30
"""

import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set


class LogLevel(Enum):
    """Log severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    @property
    def priority(self) -> int:
        """Get level priority (higher = more severe)"""
        return ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].index(self.value)


@dataclass
class LogEntry:
    """
    Structured log entry.
    
    Attributes:
        timestamp: ISO timestamp
        level: Log level
        source: Log source (file/module)
        message: Log message
        correlation_id: Request correlation ID
        metadata: Additional structured data
    """
    timestamp: str
    level: LogLevel
    source: str
    message: str
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def matches_filter(
        self,
        min_level: LogLevel = None,
        sources: Set[str] = None,
        search: str = None,
        correlation_id: str = None,
    ) -> bool:
        """Check if entry matches filters"""
        if min_level and self.level.priority < min_level.priority:
            return False
        
        if sources and self.source not in sources:
            return False
        
        if search and search.lower() not in self.message.lower():
            return False
        
        if correlation_id and self.correlation_id != correlation_id:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'level': self.level.value,
            'source': self.source,
            'message': self.message,
            'correlation_id': self.correlation_id,
            'metadata': self.metadata,
        }
    
    def format_cli(self, show_source: bool = True) -> str:
        """Format for CLI display"""
        icons = {
            LogLevel.DEBUG: '🔍',
            LogLevel.INFO: 'ℹ️ ',
            LogLevel.WARNING: '⚠️ ',
            LogLevel.ERROR: '❌',
            LogLevel.CRITICAL: '🔥',
        }
        icon = icons.get(self.level, '  ')
        
        # Short timestamp
        time_str = self.timestamp[-12:-4] if len(self.timestamp) > 12 else self.timestamp[-8:]
        
        if show_source:
            source_str = f"[{self.source[:15]}]" if len(self.source) > 15 else f"[{self.source}]"
            return f"{icon} {time_str} {source_str} {self.message}"
        else:
            return f"{icon} {time_str} {self.message}"


@dataclass
class LogSource:
    """
    Log source configuration.
    
    Attributes:
        name: Source identifier
        path: Log file path
        enabled: Whether source is active
        pattern: Regex pattern for parsing
        color: Display color
    """
    name: str
    path: Path
    enabled: bool = True
    pattern: str = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+([^:]+):\s+(.+)'
    color: str = "white"
    
    # Track file position for tailing
    _last_position: int = 0
    _last_size: int = 0


class DebugPanelService:
    """
    Multi-source debug panel service.
    
    Features:
    - Monitor multiple log files simultaneously
    - Live tail with auto-scroll
    - Filter by level, source, search, correlation ID
    - Error context aggregation
    - WebSocket streaming support
    - Export filtered logs
    """
    
    # Standard log sources
    DEFAULT_SOURCES = [
        ('dev', 'dev.log', 'cyan'),
        ('error', 'error.log', 'red'),
        ('system', 'system.log', 'green'),
        ('api', 'api_server.log', 'yellow'),
        ('tui', 'tui-debug-{date}.log', 'magenta'),
        ('session', 'session-commands-{date}.log', 'blue'),
        ('terminal', 'terminal_server.log', 'white'),
    ]
    
    def __init__(self, logs_dir: Path = None):
        """
        Initialize debug panel service.
        
        Args:
            logs_dir: Logs directory (auto-detected if None)
        """
        self._init_logs_dir(logs_dir)
        
        # Sources
        self.sources: Dict[str, LogSource] = {}
        
        # Aggregated entries
        self.entries: List[LogEntry] = []
        self.max_entries = 1000
        
        # Filters
        self.min_level: LogLevel = LogLevel.DEBUG
        self.active_sources: Set[str] = set()
        self.search_term: Optional[str] = None
        self.correlation_filter: Optional[str] = None
        
        # UI state
        self.auto_scroll = True
        self.scroll_offset = 0
        self.viewport_lines = 20
        
        # Streaming callbacks
        self._subscribers: List[Callable[[LogEntry], None]] = []
        
        # Initialize default sources
        self._init_default_sources()
    
    def _init_logs_dir(self, logs_dir: Path = None):
        """Initialize logs directory"""
        if logs_dir:
            self.logs_dir = Path(logs_dir)
        else:
            try:
                from dev.goblin.core.utils.paths import PATHS
                self.logs_dir = PATHS.MEMORY / 'logs'
            except ImportError:
                self.logs_dir = Path('memory/logs')
    
    def _init_default_sources(self):
        """Initialize default log sources"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        for name, filename, color in self.DEFAULT_SOURCES:
            # Replace {date} placeholder
            actual_filename = filename.replace('{date}', today)
            path = self.logs_dir / actual_filename
            
            self.sources[name] = LogSource(
                name=name,
                path=path,
                enabled=path.exists(),
                color=color,
            )
            
            if path.exists():
                self.active_sources.add(name)
    
    # ─── Source Management ──────────────────────────────────────────
    
    def add_source(self, name: str, path: Path, color: str = "white") -> bool:
        """Add a log source"""
        if not path.exists():
            return False
        
        self.sources[name] = LogSource(name=name, path=path, color=color)
        self.active_sources.add(name)
        return True
    
    def remove_source(self, name: str) -> bool:
        """Remove a log source"""
        if name in self.sources:
            del self.sources[name]
            self.active_sources.discard(name)
            return True
        return False
    
    def enable_source(self, name: str) -> bool:
        """Enable a log source"""
        if name in self.sources:
            self.sources[name].enabled = True
            self.active_sources.add(name)
            return True
        return False
    
    def disable_source(self, name: str) -> bool:
        """Disable a log source"""
        if name in self.sources:
            self.sources[name].enabled = False
            self.active_sources.discard(name)
            return True
        return False
    
    def get_available_sources(self) -> List[Dict]:
        """Get all available sources with status"""
        return [
            {
                'name': s.name,
                'path': str(s.path),
                'enabled': s.enabled,
                'exists': s.path.exists(),
                'color': s.color,
            }
            for s in self.sources.values()
        ]
    
    # ─── Log Loading ────────────────────────────────────────────────
    
    def load_all(self, max_lines: int = 100):
        """Load logs from all enabled sources"""
        self.entries.clear()
        
        for source in self.sources.values():
            if source.enabled and source.path.exists():
                entries = self._load_source(source, max_lines)
                self.entries.extend(entries)
        
        # Sort by timestamp
        self.entries.sort(key=lambda e: e.timestamp)
        
        # Trim to max
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
    
    def _load_source(self, source: LogSource, max_lines: int) -> List[LogEntry]:
        """Load entries from a single source"""
        entries = []
        
        try:
            with open(source.path, 'r', errors='ignore') as f:
                lines = f.readlines()[-max_lines:]
            
            for line in lines:
                entry = self._parse_line(line, source)
                if entry:
                    entries.append(entry)
                    
        except Exception:
            pass
        
        return entries
    
    def _parse_line(self, line: str, source: LogSource) -> Optional[LogEntry]:
        """Parse a log line into LogEntry"""
        line = line.strip()
        if not line:
            return None
        
        # Try standard pattern
        match = re.match(source.pattern, line)
        if match:
            timestamp, level, module, message = match.groups()
            try:
                log_level = LogLevel(level.upper())
            except ValueError:
                log_level = LogLevel.INFO
            
            # Extract correlation ID if present
            correlation_id = None
            corr_match = re.search(r'\[([a-f0-9-]{36})\]', message)
            if corr_match:
                correlation_id = corr_match.group(1)
            
            return LogEntry(
                timestamp=timestamp,
                level=log_level,
                source=source.name,
                message=message,
                correlation_id=correlation_id,
            )
        
        # Fallback: treat entire line as message
        return LogEntry(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            level=LogLevel.INFO,
            source=source.name,
            message=line,
        )
    
    def refresh(self):
        """Refresh all sources"""
        self.load_all()
    
    def tail(self) -> List[LogEntry]:
        """Get new entries since last check (tail -f style)"""
        new_entries = []
        
        for source in self.sources.values():
            if not source.enabled or not source.path.exists():
                continue
            
            try:
                current_size = source.path.stat().st_size
                
                if current_size > source._last_size:
                    with open(source.path, 'r', errors='ignore') as f:
                        f.seek(source._last_position)
                        new_lines = f.readlines()
                        source._last_position = f.tell()
                    
                    for line in new_lines:
                        entry = self._parse_line(line, source)
                        if entry:
                            new_entries.append(entry)
                            self._notify_subscribers(entry)
                
                source._last_size = current_size
                
            except Exception:
                pass
        
        # Add to entries
        self.entries.extend(new_entries)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        
        return new_entries
    
    # ─── Filtering ──────────────────────────────────────────────────
    
    def set_min_level(self, level: LogLevel | str):
        """Set minimum log level filter"""
        if isinstance(level, str):
            try:
                level = LogLevel(level.upper())
            except ValueError:
                level = LogLevel.DEBUG
        self.min_level = level
        self.scroll_offset = 0
    
    def set_sources(self, sources: List[str]):
        """Set active sources filter"""
        self.active_sources = set(s for s in sources if s in self.sources)
        self.scroll_offset = 0
    
    def set_search(self, term: str = None):
        """Set search filter"""
        self.search_term = term if term else None
        self.scroll_offset = 0
    
    def set_correlation_filter(self, correlation_id: str = None):
        """Filter by correlation ID"""
        self.correlation_filter = correlation_id
        self.scroll_offset = 0
    
    def clear_filters(self):
        """Clear all filters"""
        self.min_level = LogLevel.DEBUG
        self.active_sources = set(self.sources.keys())
        self.search_term = None
        self.correlation_filter = None
        self.scroll_offset = 0
    
    def get_filtered_entries(self) -> List[LogEntry]:
        """Get entries matching current filters"""
        return [
            e for e in self.entries
            if e.matches_filter(
                min_level=self.min_level,
                sources=self.active_sources if self.active_sources else None,
                search=self.search_term,
                correlation_id=self.correlation_filter,
            )
        ]
    
    # ─── Streaming ──────────────────────────────────────────────────
    
    def subscribe(self, callback: Callable[[LogEntry], None]):
        """Subscribe to new log entries"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[LogEntry], None]):
        """Unsubscribe from log entries"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def _notify_subscribers(self, entry: LogEntry):
        """Notify all subscribers of new entry"""
        for callback in self._subscribers:
            try:
                callback(entry)
            except Exception:
                pass
    
    # ─── Rendering ──────────────────────────────────────────────────
    
    def render(self, width: int = 80) -> str:
        """Render debug panel for CLI"""
        lines = []
        
        # Header
        lines.append("═" * width)
        lines.append(" DEBUG PANEL - Multi-Source Log Viewer ".center(width, "═"))
        lines.append("═" * width)
        
        # Source status
        source_status = []
        for name, source in self.sources.items():
            if source.enabled:
                source_status.append(f"✓{name}")
            else:
                source_status.append(f"○{name}")
        lines.append(f"Sources: {' '.join(source_status)}")
        
        # Filters
        filter_parts = []
        filter_parts.append(f"Level≥{self.min_level.value}")
        if self.search_term:
            filter_parts.append(f"Search:'{self.search_term}'")
        if self.correlation_filter:
            filter_parts.append(f"CorrID:{self.correlation_filter[:8]}...")
        lines.append(f"Filters: {' | '.join(filter_parts)}")
        
        lines.append("─" * width)
        
        # Entries
        filtered = self.get_filtered_entries()
        visible = filtered[self.scroll_offset:self.scroll_offset + self.viewport_lines]
        
        if not visible:
            lines.append("  (no log entries match filters)")
        else:
            if self.scroll_offset > 0:
                lines.append(f"  ▲ {self.scroll_offset} more above")
            
            for entry in visible:
                lines.append(entry.format_cli())
            
            remaining = len(filtered) - self.scroll_offset - len(visible)
            if remaining > 0:
                lines.append(f"  ▼ {remaining} more below")
        
        # Footer
        lines.append("─" * width)
        stats = self.get_stats()
        lines.append(f"Total: {stats['total']} | Errors: {stats['errors']} | " +
                    f"[R]efresh [F]ilter [C]lear [E]xport [Q]uit")
        
        return "\n".join(lines)
    
    def scroll_up(self, lines: int = 1):
        """Scroll view up"""
        self.scroll_offset = max(0, self.scroll_offset - lines)
        self.auto_scroll = False
    
    def scroll_down(self, lines: int = 1):
        """Scroll view down"""
        filtered = self.get_filtered_entries()
        max_offset = max(0, len(filtered) - self.viewport_lines)
        self.scroll_offset = min(max_offset, self.scroll_offset + lines)
    
    def scroll_to_bottom(self):
        """Scroll to latest entries"""
        filtered = self.get_filtered_entries()
        self.scroll_offset = max(0, len(filtered) - self.viewport_lines)
        self.auto_scroll = True
    
    # ─── Stats & Export ─────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, Any]:
        """Get panel statistics"""
        filtered = self.get_filtered_entries()
        
        level_counts = {}
        for level in LogLevel:
            level_counts[level.value] = sum(1 for e in filtered if e.level == level)
        
        return {
            'total': len(filtered),
            'errors': level_counts.get('ERROR', 0) + level_counts.get('CRITICAL', 0),
            'by_level': level_counts,
            'sources_active': len(self.active_sources),
            'sources_total': len(self.sources),
        }
    
    def get_recent_errors(self, count: int = 10) -> List[LogEntry]:
        """Get most recent errors"""
        errors = [
            e for e in self.entries
            if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]
        ]
        return errors[-count:]
    
    def export(self, path: Path = None, format: str = 'log') -> Dict[str, Any]:
        """
        Export filtered logs.
        
        Args:
            path: Output path (auto-generated if None)
            format: 'log' or 'json'
        """
        if path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = 'json' if format == 'json' else 'log'
            path = self.logs_dir / f"export_{timestamp}.{ext}"
        
        filtered = self.get_filtered_entries()
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'json':
                with open(path, 'w') as f:
                    json.dump({
                        'exported': datetime.now().isoformat(),
                        'filters': {
                            'min_level': self.min_level.value,
                            'sources': list(self.active_sources),
                            'search': self.search_term,
                            'correlation_id': self.correlation_filter,
                        },
                        'entries': [e.to_dict() for e in filtered],
                    }, f, indent=2)
            else:
                with open(path, 'w') as f:
                    f.write(f"# Debug Log Export - {datetime.now().isoformat()}\n")
                    f.write(f"# Entries: {len(filtered)}\n\n")
                    for entry in filtered:
                        f.write(f"{entry.timestamp} [{entry.level.value}] {entry.source}: {entry.message}\n")
            
            return {'success': True, 'path': str(path), 'entries': len(filtered)}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ─── API Methods ────────────────────────────────────────────────
    
    def to_dict(self) -> Dict:
        """Export state as dictionary"""
        return {
            'sources': self.get_available_sources(),
            'filters': {
                'min_level': self.min_level.value,
                'active_sources': list(self.active_sources),
                'search': self.search_term,
                'correlation_id': self.correlation_filter,
            },
            'stats': self.get_stats(),
            'entries': [e.to_dict() for e in self.get_filtered_entries()[-50:]],
        }


# ─── Convenience Functions ──────────────────────────────────────────

_service_instance: DebugPanelService = None

def get_debug_panel_service(logs_dir: Path = None) -> DebugPanelService:
    """Get singleton debug panel service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = DebugPanelService(logs_dir)
    return _service_instance


# ─── Test ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    service = DebugPanelService()
    
    print(f"Logs dir: {service.logs_dir}")
    print(f"\nAvailable sources:")
    for src in service.get_available_sources():
        status = "✓" if src['enabled'] else "○"
        exists = "exists" if src['exists'] else "missing"
        print(f"  {status} {src['name']}: {src['path']} ({exists})")
    
    # Load and display
    service.load_all(max_lines=50)
    print(f"\nLoaded {len(service.entries)} entries")
    
    stats = service.get_stats()
    print(f"Stats: {stats}")
    
    # Render
    print("\n" + service.render(width=70))
