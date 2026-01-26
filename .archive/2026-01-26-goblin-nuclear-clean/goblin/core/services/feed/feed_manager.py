"""
FeedManager - Central orchestrator for the FEED system

The FeedManager coordinates sources, compiler, and renderer to provide
a unified feed experience. It handles polling, updates, and display.
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import threading
import time
import json
from pathlib import Path

from .feed_item import FeedItem, FeedType, FeedPriority
from .feed_source import (
    FeedSource,
    TimeSource,
    SystemSource,
    AlertSource,
    LogSource,
    TodoSource,
    StaticSource,
)
from .feed_compiler import FeedCompiler
from .feed_renderer import FeedRenderer, DisplayMode, FeedSpeed


# Singleton instance
_feed_manager: Optional["FeedManager"] = None


def get_feed_manager() -> "FeedManager":
    """Get or create the global FeedManager instance"""
    global _feed_manager
    if _feed_manager is None:
        _feed_manager = FeedManager()
    return _feed_manager


class FeedManager:
    """
    Central manager for the FEED system.

    Coordinates:
    - Feed sources (time, alerts, logs, todos, custom)
    - Feed compiler (aggregation, filtering, formatting)
    - Feed renderer (ticker, scroll, panel display)

    Provides high-level API for feed operations.
    """

    def __init__(self):
        # Core components
        self.compiler = FeedCompiler()
        self.renderer = FeedRenderer()

        # Sources
        self.sources: Dict[str, FeedSource] = {}

        # Polling thread
        self._poll_thread: Optional[threading.Thread] = None
        self._polling = False
        self._poll_interval = 10  # Seconds

        # Callbacks
        self._on_new_item: List[Callable[[FeedItem], None]] = []

        # Initialize built-in sources
        self._init_builtin_sources()

    def _init_builtin_sources(self):
        """Initialize built-in feed sources"""
        self.register_source(TimeSource())
        self.register_source(SystemSource())
        self.register_source(AlertSource())
        self.register_source(LogSource())
        self.register_source(TodoSource())

        # Default static content
        tips = StaticSource(
            "tips",
            [
                "Press Ctrl+C to stop feed display",
                "Type FEED HELP for commands",
                "uDOS v1.0 - Offline-first OS layer",
            ],
        )
        self.register_source(tips)

    # Source Management

    def register_source(self, source: FeedSource) -> None:
        """Register a feed source"""
        self.sources[source.name] = source

        # Hook up push callback
        source.on_item(self._handle_pushed_item)

    def unregister_source(self, name: str) -> bool:
        """Unregister a feed source"""
        if name in self.sources:
            del self.sources[name]
            return True
        return False

    def get_source(self, name: str) -> Optional[FeedSource]:
        """Get a source by name"""
        return self.sources.get(name)

    def enable_source(self, name: str) -> bool:
        """Enable a source"""
        source = self.sources.get(name)
        if source:
            source.enabled = True
            return True
        return False

    def disable_source(self, name: str) -> bool:
        """Disable a source"""
        source = self.sources.get(name)
        if source:
            source.enabled = False
            return True
        return False

    def _handle_pushed_item(self, item: FeedItem) -> None:
        """Handle items pushed by sources"""
        self.compiler.add_item(item)
        for callback in self._on_new_item:
            callback(item)

    # Polling

    def start_polling(self, interval: Optional[int] = None) -> None:
        """Start background polling of sources"""
        if self._polling:
            return

        if interval:
            self._poll_interval = interval

        self._polling = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def stop_polling(self) -> None:
        """Stop background polling"""
        self._polling = False
        if self._poll_thread:
            self._poll_thread.join(timeout=2.0)

    def _poll_loop(self) -> None:
        """Background polling loop"""
        while self._polling:
            self.poll_sources()
            time.sleep(self._poll_interval)

    def poll_sources(self) -> int:
        """
        Poll all enabled sources for new items.

        Returns count of new items added.
        """
        total_added = 0

        for source in self.sources.values():
            if source.should_poll:
                try:
                    items = source.poll()
                    added = self.compiler.add_items(items)
                    total_added += added
                    source.mark_polled()
                except Exception as e:
                    # Log error but continue
                    print(f"[FEED] Error polling {source.name}: {e}")

        return total_added

    # High-level operations

    def add_item(
        self,
        content: str,
        type: FeedType = FeedType.CUSTOM,
        priority: FeedPriority = FeedPriority.NORMAL,
        **kwargs,
    ) -> FeedItem:
        """Add a custom item to the feed"""
        item = FeedItem(content=content, type=type, priority=priority, **kwargs)
        self.compiler.add_item(item)
        return item

    def alert(
        self, content: str, priority: FeedPriority = FeedPriority.HIGH
    ) -> FeedItem:
        """Add an alert to the feed"""
        alert_source = self.sources.get("alerts")
        if isinstance(alert_source, AlertSource):
            return alert_source.add_alert(content, priority)
        else:
            return self.add_item(content, FeedType.ALERT, priority)

    def log(self, message: str, level: str = "INFO") -> FeedItem:
        """Add a log entry to the feed"""
        log_source = self.sources.get("logs")
        if isinstance(log_source, LogSource):
            return log_source.add_log(message, level)
        else:
            return self.add_item(message, FeedType.LOG)

    def set_todos(self, todos: List[Dict[str, Any]]) -> None:
        """Update the todo list for feed display"""
        todo_source = self.sources.get("todos")
        if isinstance(todo_source, TodoSource):
            todo_source.set_todos(todos)

    # Display methods

    def get_feed_text(self, limit: int = 10) -> str:
        """Get feed as plain text for ticker display"""
        return self.compiler.to_text(limit=limit)

    def get_feed_lines(self, limit: int = 20) -> List[str]:
        """Get feed as lines for scroll display"""
        return self.compiler.to_lines(limit=limit)

    def get_feed_json(self, limit: int = 50) -> str:
        """Get feed as JSON"""
        return self.compiler.to_json(limit=limit)

    def get_feed_rss(self) -> str:
        """Get feed as RSS XML"""
        return self.compiler.to_rss()

    def get_items(self, limit: int = 20) -> List[FeedItem]:
        """Get feed items directly"""
        return self.compiler.get_items(limit=limit)

    # Ticker display

    def start_ticker(
        self, callback: Optional[Callable[[str], None]] = None, speed: str = "medium"
    ) -> None:
        """
        Start ticker display mode.

        Args:
            callback: Function to receive ticker frames
            speed: Display speed (very_slow, slow, medium, fast, very_fast)
        """
        # Ensure polling is running
        if not self._polling:
            self.start_polling()

        self.renderer.set_mode(DisplayMode.TICKER)
        self.renderer.set_speed_by_name(speed)

        # Initial text
        text = self.get_feed_text()

        # Update callback that refreshes text periodically
        last_refresh = datetime.now()
        refresh_interval = 30  # Refresh content every 30 seconds

        def updating_callback(frame: str):
            nonlocal last_refresh, text

            # Refresh content periodically
            elapsed = (datetime.now() - last_refresh).total_seconds()
            if elapsed > refresh_interval:
                text = self.get_feed_text()
                self.renderer.update_ticker_text(text)
                last_refresh = datetime.now()

            if callback:
                callback(frame)

        self.renderer.start_ticker(text, updating_callback)

    def start_scroll(
        self,
        callback: Optional[Callable[[str], None]] = None,
        speed: str = "medium",
        loop: bool = True,
    ) -> None:
        """
        Start scroll display mode.

        Args:
            callback: Function to receive scroll frames
            speed: Display speed
            loop: Whether to loop content
        """
        if not self._polling:
            self.start_polling()

        self.renderer.set_mode(DisplayMode.SCROLL)
        self.renderer.set_speed_by_name(speed)

        lines = self.get_feed_lines()
        self.renderer.start_scroll(lines, callback, loop)

    def stop_display(self) -> None:
        """Stop current display"""
        self.renderer.stop()

    def pause_display(self) -> None:
        """Pause current display"""
        self.renderer.pause()

    def resume_display(self) -> None:
        """Resume current display"""
        self.renderer.resume()

    def set_speed(self, speed: str) -> bool:
        """Set display speed"""
        return self.renderer.set_speed_by_name(speed)

    # Filtering

    def filter_by_type(self, types: Optional[List[str]]) -> None:
        """Filter feed to specific types"""
        if types:
            feed_types = [
                FeedType(t) for t in types if t in [ft.value for ft in FeedType]
            ]
            self.compiler.set_type_filter(feed_types)
        else:
            self.compiler.set_type_filter(None)

    def filter_by_priority(self, max_priority: Optional[int]) -> None:
        """Filter feed to priority level and above"""
        if max_priority:
            self.compiler.set_priority_filter(FeedPriority(max_priority))
        else:
            self.compiler.set_priority_filter(None)

    def clear_filters(self) -> None:
        """Clear all filters"""
        self.compiler.clear_filters()

    # Callbacks

    def on_new_item(self, callback: Callable[[FeedItem], None]) -> None:
        """Register callback for new items"""
        self._on_new_item.append(callback)

    # Status

    def get_status(self) -> Dict[str, Any]:
        """Get feed system status"""
        return {
            "polling": self._polling,
            "poll_interval": self._poll_interval,
            "sources": {
                name: {
                    "enabled": source.enabled,
                    "poll_interval": source.poll_interval,
                    "last_poll": (
                        source.last_poll.isoformat() if source.last_poll else None
                    ),
                }
                for name, source in self.sources.items()
            },
            "compiler": self.compiler.get_stats(),
            "renderer": self.renderer.get_status(),
        }

    def shutdown(self) -> None:
        """Clean shutdown of feed system"""
        self.stop_display()
        self.stop_polling()


# Convenience functions


def feed_ticker(speed: str = "medium") -> FeedManager:
    """Start a feed ticker display"""
    manager = get_feed_manager()
    manager.start_ticker(speed=speed)
    return manager


def feed_scroll(speed: str = "medium") -> FeedManager:
    """Start a feed scroll display"""
    manager = get_feed_manager()
    manager.start_scroll(speed=speed)
    return manager


def feed_alert(content: str) -> FeedItem:
    """Add an alert to the feed"""
    return get_feed_manager().alert(content)


def feed_add(content: str, **kwargs) -> FeedItem:
    """Add an item to the feed"""
    return get_feed_manager().add_item(content, **kwargs)
