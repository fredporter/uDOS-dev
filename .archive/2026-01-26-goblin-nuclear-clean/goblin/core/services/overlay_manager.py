"""
Overlay Manager Service

Manages user overlays for filtering knowledge views.
Overlays define which documents appear in a user's knowledge view
based on tags, categories, locations, and quality filters.

Part of uDOS Alpha v1.0.0.53+
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from dev.goblin.core.services.logging_manager import get_logger
from dev.goblin.core.services.knowledge_graph import (
    KnowledgeGraph,
    DocumentNode,
    DocumentStatus,
    get_knowledge_graph,
)

logger = get_logger("overlay-manager")


class OverlayType(Enum):
    """Types of overlays."""

    SYSTEM = "system"  # Built-in overlays (@all, @emergency, etc.)
    USER = "user"  # User-created overlays
    SHARED = "shared"  # Overlays shared with others
    TEMPORARY = "temporary"  # Session-only overlays


@dataclass
class OverlayFilter:
    """Filter criteria for an overlay."""

    include_tags: List[str] = field(default_factory=list)
    exclude_tags: List[str] = field(default_factory=list)
    include_categories: List[str] = field(default_factory=list)
    exclude_categories: List[str] = field(default_factory=list)
    min_quality: float = 0.0
    max_quality: float = 10.0
    verified_only: bool = False
    statuses: List[str] = field(default_factory=lambda: ["published"])
    include_locations: List[str] = field(default_factory=list)  # Tile coords
    exclude_locations: List[str] = field(default_factory=list)
    author_ids: List[str] = field(default_factory=list)
    exclude_author_ids: List[str] = field(default_factory=list)


@dataclass
class Overlay:
    """A named overlay for filtering knowledge."""

    name: str
    overlay_type: OverlayType
    description: str = ""
    filters: OverlayFilter = field(default_factory=OverlayFilter)
    created: str = ""
    updated: str = ""
    user_id: str = ""

    # Sorting preferences
    sort_by: str = "updated"  # updated, quality, title, created
    sort_order: str = "desc"  # asc, desc

    # Limit results
    limit: int = 100

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.overlay_type.value,
            "description": self.description,
            "filters": {
                "include_tags": self.filters.include_tags,
                "exclude_tags": self.filters.exclude_tags,
                "include_categories": self.filters.include_categories,
                "exclude_categories": self.filters.exclude_categories,
                "min_quality": self.filters.min_quality,
                "max_quality": self.filters.max_quality,
                "verified_only": self.filters.verified_only,
                "statuses": self.filters.statuses,
                "include_locations": self.filters.include_locations,
                "exclude_locations": self.filters.exclude_locations,
                "author_ids": self.filters.author_ids,
                "exclude_author_ids": self.filters.exclude_author_ids,
            },
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "limit": self.limit,
            "created": self.created,
            "updated": self.updated,
            "user_id": self.user_id,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Overlay":
        """Create from dictionary."""
        filters_data = data.get("filters", {})
        filters = OverlayFilter(
            include_tags=filters_data.get("include_tags", []),
            exclude_tags=filters_data.get("exclude_tags", []),
            include_categories=filters_data.get("include_categories", []),
            exclude_categories=filters_data.get("exclude_categories", []),
            min_quality=filters_data.get("min_quality", 0.0),
            max_quality=filters_data.get("max_quality", 10.0),
            verified_only=filters_data.get("verified_only", False),
            statuses=filters_data.get("statuses", ["published"]),
            include_locations=filters_data.get("include_locations", []),
            exclude_locations=filters_data.get("exclude_locations", []),
            author_ids=filters_data.get("author_ids", []),
            exclude_author_ids=filters_data.get("exclude_author_ids", []),
        )

        return cls(
            name=data.get("name", ""),
            overlay_type=OverlayType(data.get("type", "user")),
            description=data.get("description", ""),
            filters=filters,
            sort_by=data.get("sort_by", "updated"),
            sort_order=data.get("sort_order", "desc"),
            limit=data.get("limit", 100),
            created=data.get("created", ""),
            updated=data.get("updated", ""),
            user_id=data.get("user_id", ""),
        )


class OverlayManager:
    """
    Manages knowledge overlays.

    Overlays filter the knowledge graph to show only
    relevant documents based on user preferences.
    """

    # Built-in system overlays
    SYSTEM_OVERLAYS = {
        "@all": {
            "name": "@all",
            "type": "system",
            "description": "All published knowledge",
            "filters": {"statuses": ["published"]},
        },
        "@global": {
            "name": "@global",
            "type": "system",
            "description": "Global/universal knowledge (not location-specific)",
            "filters": {"statuses": ["published"], "exclude_locations": ["*"]},
        },
        "@personal": {
            "name": "@personal",
            "type": "system",
            "description": "Your authored documents",
            "filters": {"statuses": ["draft", "submitted", "published"]},
        },
        "@nearby": {
            "name": "@nearby",
            "type": "system",
            "description": "Knowledge linked to your current location",
            "filters": {"statuses": ["published"]},
        },
        "@emergency": {
            "name": "@emergency",
            "type": "system",
            "description": "Emergency/survival knowledge only",
            "filters": {
                "statuses": ["published"],
                "include_tags": ["emergency", "survival", "first-aid", "sos", "rescue"],
            },
        },
        "@verified": {
            "name": "@verified",
            "type": "system",
            "description": "Expert-verified knowledge only",
            "filters": {"statuses": ["published"], "verified_only": True},
        },
        "@high-quality": {
            "name": "@high-quality",
            "type": "system",
            "description": "High quality score documents (7+)",
            "filters": {"statuses": ["published"], "min_quality": 7.0},
        },
        "@drafts": {
            "name": "@drafts",
            "type": "system",
            "description": "Your draft documents",
            "filters": {"statuses": ["draft"]},
        },
        "@pending": {
            "name": "@pending",
            "type": "system",
            "description": "Documents pending review",
            "filters": {"statuses": ["submitted"]},
        },
    }

    def __init__(self, overlays_path: Path = None):
        """
        Initialize overlay manager.

        Args:
            overlays_path: Where user overlays are stored
        """
        self.overlays_path = overlays_path or Path("memory/overlays")
        self.overlays_path.mkdir(parents=True, exist_ok=True)

        # Cache loaded overlays
        self._overlay_cache: Dict[str, Overlay] = {}

        # Load system overlays
        self._load_system_overlays()

        # Load user overlays
        self._load_user_overlays()

        logger.info("[LOCAL] OverlayManager initialized")

    def _load_system_overlays(self):
        """Load built-in system overlays."""
        for name, data in self.SYSTEM_OVERLAYS.items():
            self._overlay_cache[name] = Overlay.from_dict(data)

    def _load_user_overlays(self):
        """Load user overlays from disk."""
        for overlay_file in self.overlays_path.glob("*.overlay.json"):
            try:
                data = json.loads(overlay_file.read_text(encoding="utf-8"))
                overlay = Overlay.from_dict(data)
                self._overlay_cache[overlay.name] = overlay
                logger.debug(f"[LOCAL] Loaded overlay: {overlay.name}")
            except Exception as e:
                logger.warning(f"[LOCAL] Failed to load overlay {overlay_file}: {e}")

    def get(self, name: str) -> Optional[Overlay]:
        """Get an overlay by name."""
        return self._overlay_cache.get(name)

    def list(self, user_id: str = None, include_system: bool = True) -> List[Overlay]:
        """
        List available overlays.

        Args:
            user_id: Filter to overlays owned by this user
            include_system: Include system overlays

        Returns:
            List of overlays
        """
        result = []

        for overlay in self._overlay_cache.values():
            if overlay.overlay_type == OverlayType.SYSTEM:
                if include_system:
                    result.append(overlay)
            elif user_id is None or overlay.user_id == user_id:
                result.append(overlay)

        return sorted(result, key=lambda o: o.name)

    def create(
        self,
        name: str,
        user_id: str,
        description: str = "",
        filters: Dict = None,
        sort_by: str = "updated",
        sort_order: str = "desc",
        limit: int = 100,
    ) -> Overlay:
        """
        Create a new user overlay.

        Args:
            name: Overlay name (must not start with @)
            user_id: Owner user ID
            description: Overlay description
            filters: Filter criteria dict
            sort_by: Sort field
            sort_order: Sort direction
            limit: Max results

        Returns:
            Created overlay
        """
        if name.startswith("@"):
            raise ValueError("User overlays cannot start with @")

        if name in self._overlay_cache:
            raise ValueError(f"Overlay already exists: {name}")

        now = datetime.now().isoformat()

        # Build filter object
        filter_obj = OverlayFilter()
        if filters:
            filter_obj = OverlayFilter(
                include_tags=filters.get("include_tags", []),
                exclude_tags=filters.get("exclude_tags", []),
                include_categories=filters.get("include_categories", []),
                exclude_categories=filters.get("exclude_categories", []),
                min_quality=filters.get("min_quality", 0.0),
                max_quality=filters.get("max_quality", 10.0),
                verified_only=filters.get("verified_only", False),
                statuses=filters.get("statuses", ["published"]),
                include_locations=filters.get("include_locations", []),
                exclude_locations=filters.get("exclude_locations", []),
                author_ids=filters.get("author_ids", []),
                exclude_author_ids=filters.get("exclude_author_ids", []),
            )

        overlay = Overlay(
            name=name,
            overlay_type=OverlayType.USER,
            description=description,
            filters=filter_obj,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            created=now,
            updated=now,
            user_id=user_id,
        )

        # Save to disk
        self._save_overlay(overlay)

        # Add to cache
        self._overlay_cache[name] = overlay

        logger.info(f"[LOCAL] Created overlay: {name}")
        return overlay

    def update(self, name: str, user_id: str, **updates) -> Overlay:
        """
        Update an existing overlay.

        Args:
            name: Overlay name
            user_id: Must match owner (for user overlays)
            **updates: Fields to update

        Returns:
            Updated overlay
        """
        overlay = self._overlay_cache.get(name)

        if not overlay:
            raise ValueError(f"Overlay not found: {name}")

        if overlay.overlay_type == OverlayType.SYSTEM:
            raise ValueError("Cannot modify system overlays")

        if overlay.user_id != user_id:
            raise PermissionError("Cannot modify another user's overlay")

        # Update fields
        if "description" in updates:
            overlay.description = updates["description"]
        if "filters" in updates:
            filters = updates["filters"]
            overlay.filters = OverlayFilter(
                include_tags=filters.get("include_tags", overlay.filters.include_tags),
                exclude_tags=filters.get("exclude_tags", overlay.filters.exclude_tags),
                include_categories=filters.get(
                    "include_categories", overlay.filters.include_categories
                ),
                exclude_categories=filters.get(
                    "exclude_categories", overlay.filters.exclude_categories
                ),
                min_quality=filters.get("min_quality", overlay.filters.min_quality),
                max_quality=filters.get("max_quality", overlay.filters.max_quality),
                verified_only=filters.get(
                    "verified_only", overlay.filters.verified_only
                ),
                statuses=filters.get("statuses", overlay.filters.statuses),
                include_locations=filters.get(
                    "include_locations", overlay.filters.include_locations
                ),
                exclude_locations=filters.get(
                    "exclude_locations", overlay.filters.exclude_locations
                ),
                author_ids=filters.get("author_ids", overlay.filters.author_ids),
                exclude_author_ids=filters.get(
                    "exclude_author_ids", overlay.filters.exclude_author_ids
                ),
            )
        if "sort_by" in updates:
            overlay.sort_by = updates["sort_by"]
        if "sort_order" in updates:
            overlay.sort_order = updates["sort_order"]
        if "limit" in updates:
            overlay.limit = updates["limit"]

        overlay.updated = datetime.now().isoformat()

        # Save
        self._save_overlay(overlay)

        logger.info(f"[LOCAL] Updated overlay: {name}")
        return overlay

    def delete(self, name: str, user_id: str) -> bool:
        """
        Delete a user overlay.

        Args:
            name: Overlay name
            user_id: Must match owner

        Returns:
            True if deleted
        """
        overlay = self._overlay_cache.get(name)

        if not overlay:
            raise ValueError(f"Overlay not found: {name}")

        if overlay.overlay_type == OverlayType.SYSTEM:
            raise ValueError("Cannot delete system overlays")

        if overlay.user_id != user_id:
            raise PermissionError("Cannot delete another user's overlay")

        # Remove file
        file_path = self.overlays_path / f"{name}.overlay.json"
        if file_path.exists():
            file_path.unlink()

        # Remove from cache
        del self._overlay_cache[name]

        logger.info(f"[LOCAL] Deleted overlay: {name}")
        return True

    def _save_overlay(self, overlay: Overlay):
        """Save overlay to disk."""
        file_path = self.overlays_path / f"{overlay.name}.overlay.json"
        data = overlay.to_dict()
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def apply(
        self,
        overlay_name: str,
        user_id: str = None,
        current_tile: str = None,
        graph: KnowledgeGraph = None,
    ) -> List[DocumentNode]:
        """
        Apply an overlay to get filtered documents.

        Args:
            overlay_name: Name of overlay to apply
            user_id: Current user ID (for @personal, @drafts)
            current_tile: Current tile coordinate (for @nearby)
            graph: Knowledge graph to query (uses default if None)

        Returns:
            List of matching documents
        """
        overlay = self._overlay_cache.get(overlay_name)

        if not overlay:
            raise ValueError(f"Overlay not found: {overlay_name}")

        if graph is None:
            graph = get_knowledge_graph()

        filters = overlay.filters

        # Handle special system overlay logic
        if overlay_name == "@personal":
            if not user_id:
                return []
            # Override to filter by author
            filters.author_ids = [user_id]

        elif overlay_name == "@nearby":
            if not current_tile:
                return []
            # Get adjacent tiles (simplified - just current tile for now)
            filters.include_locations = [current_tile]

        elif overlay_name == "@drafts":
            if not user_id:
                return []
            filters.author_ids = [user_id]

        # Build query kwargs
        query_kwargs = {}

        if filters.include_tags:
            query_kwargs["tags"] = filters.include_tags

        if filters.include_categories:
            query_kwargs["categories"] = filters.include_categories

        if filters.statuses:
            query_kwargs["status"] = [DocumentStatus(s) for s in filters.statuses]

        if filters.include_locations:
            query_kwargs["tile"] = (
                filters.include_locations[0]
                if len(filters.include_locations) == 1
                else None
            )

        if filters.min_quality > 0:
            query_kwargs["min_quality"] = filters.min_quality

        if filters.verified_only:
            query_kwargs["verified_only"] = True

        # Get base results
        results = graph.query(**query_kwargs)

        # Apply exclusion filters
        if filters.exclude_tags:
            exclude_set = set(filters.exclude_tags)
            results = [doc for doc in results if not (set(doc.tags) & exclude_set)]

        if filters.exclude_categories:
            exclude_set = set(filters.exclude_categories)
            results = [
                doc for doc in results if not (set(doc.categories) & exclude_set)
            ]

        if filters.exclude_locations and "*" not in filters.exclude_locations:
            exclude_set = set(filters.exclude_locations)
            results = [doc for doc in results if doc.tile not in exclude_set]
        elif "*" in filters.exclude_locations:
            # Exclude all location-specific docs
            results = [doc for doc in results if not doc.tile]

        if filters.max_quality < 10.0:
            results = [doc for doc in results if doc.quality <= filters.max_quality]

        if filters.author_ids:
            author_set = set(filters.author_ids)
            results = [doc for doc in results if doc.author_id in author_set]

        if filters.exclude_author_ids:
            exclude_set = set(filters.exclude_author_ids)
            results = [doc for doc in results if doc.author_id not in exclude_set]

        # Sort
        sort_key = overlay.sort_by
        reverse = overlay.sort_order == "desc"

        if sort_key == "updated":
            results.sort(key=lambda d: d.updated or "", reverse=reverse)
        elif sort_key == "created":
            results.sort(key=lambda d: d.created or "", reverse=reverse)
        elif sort_key == "quality":
            results.sort(key=lambda d: d.quality, reverse=reverse)
        elif sort_key == "title":
            results.sort(key=lambda d: d.title.lower(), reverse=reverse)

        # Limit
        if overlay.limit and len(results) > overlay.limit:
            results = results[: overlay.limit]

        return results


# Singleton instance
_manager: Optional[OverlayManager] = None


def get_overlay_manager() -> OverlayManager:
    """Get or create the singleton overlay manager."""
    global _manager
    if _manager is None:
        _manager = OverlayManager()
    return _manager
