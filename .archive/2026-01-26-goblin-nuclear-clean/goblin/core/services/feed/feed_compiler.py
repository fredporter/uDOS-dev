"""
FeedCompiler - Aggregates and formats feed items from multiple sources

The compiler collects items from all registered sources, manages priority
ordering, handles TTL expiration, and formats items for output.
"""

from typing import List, Dict, Optional, Any, Iterator
from datetime import datetime
from collections import deque
import json

from .feed_item import FeedItem, FeedPriority, FeedType


class FeedCompiler:
    """
    Aggregates feed items from multiple sources and compiles them
    into a unified stream for display.

    Features:
    - Priority-based ordering
    - TTL management
    - Deduplication
    - Output formatting (JSON, RSS, text)
    - History tracking
    """

    def __init__(self, max_items: int = 100, max_history: int = 500):
        self.max_items = max_items
        self.max_history = max_history

        # Current active items
        self._items: List[FeedItem] = []

        # Historical items (for repeat/mix mode)
        self._history: deque = deque(maxlen=max_history)

        # Deduplication tracking
        self._seen_ids: set = set()

        # Display position for iteration
        self._position: int = 0

        # Filters
        self._type_filter: Optional[set] = None
        self._priority_filter: Optional[FeedPriority] = None
        self._source_filter: Optional[set] = None

    def add_item(self, item: FeedItem) -> bool:
        """
        Add a new item to the feed.

        Returns True if item was added, False if duplicate.
        """
        # Check for duplicate
        if item.id in self._seen_ids:
            return False

        self._seen_ids.add(item.id)
        self._items.append(item)

        # Maintain max size
        if len(self._items) > self.max_items:
            removed = self._items.pop(0)
            self._history.append(removed)

        return True

    def add_items(self, items: List[FeedItem]) -> int:
        """Add multiple items, returns count added"""
        added = 0
        for item in items:
            if self.add_item(item):
                added += 1
        return added

    def remove_expired(self) -> int:
        """Remove expired items, returns count removed"""
        before = len(self._items)
        self._items = [item for item in self._items if not item.is_expired]
        removed = before - len(self._items)
        return removed

    def get_items(
        self, limit: Optional[int] = None, sort_by_priority: bool = True
    ) -> List[FeedItem]:
        """
        Get current feed items.

        Args:
            limit: Max items to return
            sort_by_priority: If True, sort by priority (highest first)

        Returns:
            List of FeedItems
        """
        # Remove expired first
        self.remove_expired()

        # Apply filters
        items = self._apply_filters(self._items)

        # Sort by priority if requested
        if sort_by_priority:
            items = sorted(items, key=lambda x: (x.priority, x.timestamp))

        # Apply limit
        if limit:
            items = items[:limit]

        return items

    def _apply_filters(self, items: List[FeedItem]) -> List[FeedItem]:
        """Apply active filters to item list"""
        result = items

        if self._type_filter:
            result = [i for i in result if i.type in self._type_filter]

        if self._priority_filter:
            result = [i for i in result if i.priority <= self._priority_filter]

        if self._source_filter:
            result = [i for i in result if i.source in self._source_filter]

        return result

    def set_type_filter(self, types: Optional[List[FeedType]]) -> None:
        """Filter to specific types (None to clear)"""
        self._type_filter = set(types) if types else None

    def set_priority_filter(self, max_priority: Optional[FeedPriority]) -> None:
        """Filter to priority level and above (None to clear)"""
        self._priority_filter = max_priority

    def set_source_filter(self, sources: Optional[List[str]]) -> None:
        """Filter to specific sources (None to clear)"""
        self._source_filter = set(sources) if sources else None

    def clear_filters(self) -> None:
        """Clear all filters"""
        self._type_filter = None
        self._priority_filter = None
        self._source_filter = None

    # Iterator methods for sequential access

    def next_item(self) -> Optional[FeedItem]:
        """Get next item in sequence (for ticker display)"""
        items = self.get_items(sort_by_priority=False)
        if not items:
            return None

        self._position = self._position % len(items)
        item = items[self._position]
        item.mark_seen()
        self._position += 1

        return item

    def reset_position(self) -> None:
        """Reset iteration position"""
        self._position = 0

    def __iter__(self) -> Iterator[FeedItem]:
        """Iterate over current items"""
        return iter(self.get_items())

    def __len__(self) -> int:
        """Number of active items"""
        return len(self._items)

    # Output format methods

    def to_json(self, limit: Optional[int] = None) -> str:
        """Export feed as JSON"""
        items = self.get_items(limit=limit)
        return json.dumps(
            {
                "feed": {
                    "generated": datetime.now().isoformat(),
                    "count": len(items),
                    "items": [item.to_dict() for item in items],
                }
            },
            indent=2,
        )

    def to_rss(
        self, title: str = "uDOS Feed", description: str = "uDOS system feed"
    ) -> str:
        """Export feed as RSS 2.0 XML"""
        items = self.get_items()

        items_xml = ""
        for item in items:
            items_xml += f"""
        <item>
            <title>{self._escape_xml(item.title or item.type.value)}</title>
            <description>{self._escape_xml(item.content)}</description>
            <pubDate>{item.timestamp.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
            <guid>{item.id}</guid>
            <category>{item.type.value}</category>
            <source>{self._escape_xml(item.source)}</source>
        </item>"""

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>{self._escape_xml(title)}</title>
        <description>{self._escape_xml(description)}</description>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
        <generator>uDOS Feed System</generator>
        {items_xml}
    </channel>
</rss>"""

    def to_text(self, separator: str = " | ", limit: Optional[int] = None) -> str:
        """Export feed as plain text (for ticker)"""
        items = self.get_items(limit=limit)
        return separator.join(item.ticker_text for item in items)

    def to_lines(self, limit: Optional[int] = None) -> List[str]:
        """Export feed as list of lines (for scroll display)"""
        items = self.get_items(limit=limit)
        return [item.ticker_text for item in items]

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    # History and mixing

    def get_mixed_items(
        self, new_ratio: float = 0.7, limit: int = 10
    ) -> List[FeedItem]:
        """
        Get a mix of new and historical items.

        Args:
            new_ratio: Proportion of new items (0.0-1.0)
            limit: Total items to return

        Returns:
            Mixed list of current and historical items
        """
        new_count = int(limit * new_ratio)
        old_count = limit - new_count

        new_items = self.get_items(limit=new_count)

        # Get random historical items
        history_list = list(self._history)
        import random

        old_items = (
            random.sample(history_list, min(old_count, len(history_list)))
            if history_list
            else []
        )

        # Interleave
        result = []
        new_iter = iter(new_items)
        old_iter = iter(old_items)

        for i in range(limit):
            if i % 3 == 2 and old_items:  # Every 3rd item from history
                try:
                    result.append(next(old_iter))
                except StopIteration:
                    try:
                        result.append(next(new_iter))
                    except StopIteration:
                        break
            else:
                try:
                    result.append(next(new_iter))
                except StopIteration:
                    try:
                        result.append(next(old_iter))
                    except StopIteration:
                        break

        return result

    def clear(self) -> None:
        """Clear all items and history"""
        self._items.clear()
        self._history.clear()
        self._seen_ids.clear()
        self._position = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get feed statistics"""
        return {
            "active_items": len(self._items),
            "history_items": len(self._history),
            "seen_ids": len(self._seen_ids),
            "by_type": self._count_by_type(),
            "by_priority": self._count_by_priority(),
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count items by type"""
        counts = {}
        for item in self._items:
            key = item.type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _count_by_priority(self) -> Dict[int, int]:
        """Count items by priority"""
        counts = {}
        for item in self._items:
            key = int(item.priority)
            counts[key] = counts.get(key, 0) + 1
        return counts
