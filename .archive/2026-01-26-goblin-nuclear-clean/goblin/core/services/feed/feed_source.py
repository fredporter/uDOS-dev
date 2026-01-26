"""
FeedSource - Base class for feed data providers

Feed sources are plugins that generate FeedItems. Built-in sources include
time, system status, and alerts. Extensions can add RSS, email, mesh, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import asyncio

from .feed_item import FeedItem, FeedType, FeedPriority


class FeedSource(ABC):
    """
    Abstract base class for feed data providers.

    Implement this class to create custom feed sources. Each source
    generates FeedItems that are collected by the FeedCompiler.
    """

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.last_poll: Optional[datetime] = None
        self.poll_interval: int = 60  # Seconds between polls
        self.item_ttl: Optional[int] = None  # Default TTL for items
        self._callbacks: List[Callable[[FeedItem], None]] = []

    @abstractmethod
    def poll(self) -> List[FeedItem]:
        """
        Poll the source for new items.

        Returns:
            List of new FeedItems
        """
        pass

    def on_item(self, callback: Callable[[FeedItem], None]) -> None:
        """Register callback for push-based items"""
        self._callbacks.append(callback)

    def push_item(self, item: FeedItem) -> None:
        """Push an item to all registered callbacks"""
        for callback in self._callbacks:
            callback(item)

    @property
    def should_poll(self) -> bool:
        """Check if source should be polled based on interval"""
        if not self.enabled:
            return False
        if self.last_poll is None:
            return True
        elapsed = (datetime.now() - self.last_poll).total_seconds()
        return elapsed >= self.poll_interval

    def mark_polled(self) -> None:
        """Mark source as just polled"""
        self.last_poll = datetime.now()

    def get_config(self) -> Dict[str, Any]:
        """Get source configuration"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "poll_interval": self.poll_interval,
            "item_ttl": self.item_ttl,
        }

    def set_config(self, config: Dict[str, Any]) -> None:
        """Update source configuration"""
        if "enabled" in config:
            self.enabled = config["enabled"]
        if "poll_interval" in config:
            self.poll_interval = config["poll_interval"]
        if "item_ttl" in config:
            self.item_ttl = config["item_ttl"]


class TimeSource(FeedSource):
    """
    Built-in source for time/date information.

    Generates periodic time updates for ambient feed display.
    """

    def __init__(self):
        super().__init__("time", enabled=True)
        self.poll_interval = 60  # Update every minute
        self.item_ttl = 60
        self.format = "%H:%M"
        self.show_date = True
        self.date_format = "%a %d %b"

    def poll(self) -> List[FeedItem]:
        """Generate current time item"""
        now = datetime.now()
        time_str = now.strftime(self.format)

        items = []

        # Time item
        items.append(
            FeedItem(
                content=time_str,
                type=FeedType.TIME,
                priority=FeedPriority.AMBIENT,
                source=self.name,
                title="Time",
                ttl=self.item_ttl,
            )
        )

        # Date item (less frequent)
        if self.show_date and now.second < 60:
            date_str = now.strftime(self.date_format)
            items.append(
                FeedItem(
                    content=date_str,
                    type=FeedType.TIME,
                    priority=FeedPriority.AMBIENT,
                    source=self.name,
                    title="Date",
                    ttl=3600,  # Keep for an hour
                )
            )

        return items


class SystemSource(FeedSource):
    """
    Built-in source for system status information.

    Reports system health, version, uptime, etc.
    """

    def __init__(self):
        super().__init__("system", enabled=True)
        self.poll_interval = 300  # Every 5 minutes
        self.item_ttl = 300
        self._start_time = datetime.now()

    def poll(self) -> List[FeedItem]:
        """Generate system status items"""
        items = []

        # Uptime
        uptime = datetime.now() - self._start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)

        items.append(
            FeedItem(
                content=f"Uptime: {hours}h {minutes}m",
                type=FeedType.SYSTEM,
                priority=FeedPriority.AMBIENT,
                source=self.name,
                ttl=self.item_ttl,
            )
        )

        return items


class AlertSource(FeedSource):
    """
    Source for system and user alerts.

    Alerts can be pushed or polled. This source maintains
    a queue of pending alerts.
    """

    def __init__(self):
        super().__init__("alerts", enabled=True)
        self.poll_interval = 10  # Check frequently
        self._pending: List[FeedItem] = []

    def add_alert(
        self,
        content: str,
        priority: FeedPriority = FeedPriority.HIGH,
        ttl: Optional[int] = 300,
        **kwargs,
    ) -> FeedItem:
        """Add an alert to the queue"""
        item = FeedItem(
            content=content,
            type=FeedType.ALERT,
            priority=priority,
            source=self.name,
            ttl=ttl,
            **kwargs,
        )
        self._pending.append(item)
        self.push_item(item)  # Also push immediately
        return item

    def poll(self) -> List[FeedItem]:
        """Return and clear pending alerts"""
        items = self._pending.copy()
        self._pending.clear()
        return items


class LogSource(FeedSource):
    """
    Source for log file monitoring.

    Can watch log files and emit new entries as feed items.
    """

    def __init__(self, log_path: Optional[str] = None):
        super().__init__("logs", enabled=True)
        self.poll_interval = 30
        self.item_ttl = 120
        self.log_path = log_path
        self._last_position = 0
        self._recent_logs: List[FeedItem] = []

    def add_log(self, message: str, level: str = "INFO") -> FeedItem:
        """Add a log entry directly"""
        priority = {
            "ERROR": FeedPriority.HIGH,
            "WARN": FeedPriority.NORMAL,
            "INFO": FeedPriority.LOW,
            "DEBUG": FeedPriority.AMBIENT,
        }.get(level.upper(), FeedPriority.LOW)

        item = FeedItem(
            content=message,
            type=FeedType.LOG,
            priority=priority,
            source=self.name,
            title=level,
            ttl=self.item_ttl,
        )
        self._recent_logs.append(item)
        if len(self._recent_logs) > 50:
            self._recent_logs = self._recent_logs[-50:]
        return item

    def poll(self) -> List[FeedItem]:
        """Return recent logs"""
        items = self._recent_logs.copy()
        self._recent_logs.clear()
        return items


class TodoSource(FeedSource):
    """
    Source for todo items and reminders.

    Emits pending todos, due items, and completed notifications.
    """

    def __init__(self):
        super().__init__("todos", enabled=True)
        self.poll_interval = 60
        self.item_ttl = 300
        self._todos: List[Dict[str, Any]] = []

    def set_todos(self, todos: List[Dict[str, Any]]) -> None:
        """Update the todo list"""
        self._todos = todos

    def poll(self) -> List[FeedItem]:
        """Generate items for pending todos"""
        items = []

        for todo in self._todos:
            if todo.get("status") == "in-progress":
                items.append(
                    FeedItem(
                        content=todo.get("title", "Untitled"),
                        type=FeedType.TODO,
                        priority=FeedPriority.NORMAL,
                        source=self.name,
                        title="In Progress",
                        ttl=self.item_ttl,
                        meta={"todo_id": todo.get("id")},
                    )
                )
            elif todo.get("status") == "not-started" and todo.get("due"):
                items.append(
                    FeedItem(
                        content=todo.get("title", "Untitled"),
                        type=FeedType.TODO,
                        priority=FeedPriority.LOW,
                        source=self.name,
                        title="Pending",
                        ttl=self.item_ttl,
                    )
                )

        return items


class StaticSource(FeedSource):
    """
    Source for static/rotating content.

    Displays pre-configured messages on rotation.
    Good for tips, quotes, ambient info.
    """

    def __init__(self, name: str = "static", items: Optional[List[str]] = None):
        super().__init__(name, enabled=True)
        self.poll_interval = 120  # Rotate every 2 minutes
        self.item_ttl = 120
        self._items = items or []
        self._current_index = 0

    def add_content(self, content: str) -> None:
        """Add content to rotation"""
        self._items.append(content)

    def set_content(self, items: List[str]) -> None:
        """Replace all content"""
        self._items = items
        self._current_index = 0

    def poll(self) -> List[FeedItem]:
        """Return next item in rotation"""
        if not self._items:
            return []

        content = self._items[self._current_index]
        self._current_index = (self._current_index + 1) % len(self._items)

        return [
            FeedItem(
                content=content,
                type=FeedType.CUSTOM,
                priority=FeedPriority.AMBIENT,
                source=self.name,
                ttl=self.item_ttl,
            )
        ]
