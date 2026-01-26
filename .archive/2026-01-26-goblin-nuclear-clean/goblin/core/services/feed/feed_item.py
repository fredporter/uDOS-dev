"""
FeedItem - Core data structure for FEED system

A FeedItem represents a single piece of content that can be displayed
in ticker, scroll, or panel modes. Items have priority, TTL, and can
come from any source (time, alerts, logs, todos, messages, etc).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Optional, Dict, Any
import uuid


class FeedPriority(IntEnum):
    """Priority levels for feed items (1=highest, 5=lowest)"""

    CRITICAL = 1  # System alerts, emergencies
    HIGH = 2  # Important notifications
    NORMAL = 3  # Standard items
    LOW = 4  # Background info
    AMBIENT = 5  # Time, weather, ambient data


class FeedType(Enum):
    """Categories of feed content"""

    ALERT = "alert"  # System/user alerts
    LOG = "log"  # Log messages
    TODO = "todo"  # Todo items
    MESSAGE = "message"  # User messages
    TIME = "time"  # Time/date
    LOCATION = "location"  # Location info
    WEATHER = "weather"  # Weather data
    NEWS = "news"  # News/RSS items
    WORKFLOW = "workflow"  # Workflow updates
    CHECKLIST = "checklist"  # Checklist items
    EMAIL = "email"  # Email notifications
    MESH = "mesh"  # Mesh network messages
    SYSTEM = "system"  # System status
    CUSTOM = "custom"  # Custom/user-defined


@dataclass
class FeedItem:
    """
    A single item in the feed stream.

    Attributes:
        id: Unique identifier
        type: Category of content
        priority: Display priority (1-5)
        source: Origin of the item (e.g., "system", "todo", "mesh:node1")
        title: Short label/title
        content: Main display text
        timestamp: When the item was created
        ttl: Time-to-live in seconds (None = indefinite)
        sticky: If True, item persists even after TTL
        meta: Additional metadata
        seen: Whether item has been displayed
        display_count: How many times item has been shown
    """

    content: str
    type: FeedType = FeedType.SYSTEM
    priority: FeedPriority = FeedPriority.NORMAL
    source: str = "system"
    title: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None  # Seconds, None = forever
    sticky: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)
    seen: bool = False
    display_count: int = 0

    def __post_init__(self):
        """Ensure proper types after initialization"""
        if isinstance(self.type, str):
            self.type = FeedType(self.type)
        if isinstance(self.priority, int):
            self.priority = FeedPriority(self.priority)

    @property
    def is_expired(self) -> bool:
        """Check if item has exceeded its TTL"""
        if self.ttl is None:
            return False
        if self.sticky:
            return False
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl

    @property
    def age_seconds(self) -> float:
        """Age of item in seconds"""
        return (datetime.now() - self.timestamp).total_seconds()

    @property
    def display_text(self) -> str:
        """Get formatted display text for ticker/scroll"""
        if self.title:
            return f"{self.title}: {self.content}"
        return self.content

    @property
    def ticker_text(self) -> str:
        """Get compact text for single-line ticker"""
        prefix = self._get_type_icon()
        return f"{prefix} {self.display_text}"

    def _get_type_icon(self) -> str:
        """Get icon/prefix for feed type"""
        icons = {
            FeedType.ALERT: "⚠",
            FeedType.LOG: "📋",
            FeedType.TODO: "☐",
            FeedType.MESSAGE: "✉",
            FeedType.TIME: "🕐",
            FeedType.LOCATION: "📍",
            FeedType.WEATHER: "🌤",
            FeedType.NEWS: "📰",
            FeedType.WORKFLOW: "⚙",
            FeedType.CHECKLIST: "✓",
            FeedType.EMAIL: "📧",
            FeedType.MESH: "📡",
            FeedType.SYSTEM: "💻",
            FeedType.CUSTOM: "•",
        }
        return icons.get(self.type, "•")

    def mark_seen(self) -> None:
        """Mark item as seen/displayed"""
        self.seen = True
        self.display_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": int(self.priority),
            "source": self.source,
            "title": self.title,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
            "sticky": self.sticky,
            "meta": self.meta,
            "seen": self.seen,
            "display_count": self.display_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedItem":
        """Create FeedItem from dictionary"""
        data = data.copy()
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if "type" in data and isinstance(data["type"], str):
            data["type"] = FeedType(data["type"])
        if "priority" in data and isinstance(data["priority"], int):
            data["priority"] = FeedPriority(data["priority"])
        return cls(**data)

    def __str__(self) -> str:
        return self.ticker_text

    def __repr__(self) -> str:
        return f"FeedItem(id={self.id}, type={self.type.value}, content={self.content[:30]}...)"


# Convenience constructors
def alert(content: str, **kwargs) -> FeedItem:
    """Create an alert feed item"""
    return FeedItem(content, type=FeedType.ALERT, priority=FeedPriority.HIGH, **kwargs)


def todo_item(content: str, **kwargs) -> FeedItem:
    """Create a todo feed item"""
    return FeedItem(content, type=FeedType.TODO, priority=FeedPriority.NORMAL, **kwargs)


def time_item(content: str, **kwargs) -> FeedItem:
    """Create a time/date feed item"""
    return FeedItem(
        content, type=FeedType.TIME, priority=FeedPriority.AMBIENT, ttl=60, **kwargs
    )


def message(content: str, source: str = "user", **kwargs) -> FeedItem:
    """Create a message feed item"""
    return FeedItem(content, type=FeedType.MESSAGE, source=source, **kwargs)


def system_status(content: str, **kwargs) -> FeedItem:
    """Create a system status feed item"""
    return FeedItem(content, type=FeedType.SYSTEM, priority=FeedPriority.LOW, **kwargs)
