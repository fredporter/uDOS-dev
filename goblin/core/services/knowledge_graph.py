"""
Knowledge Graph Service

Self-indexing knowledge graph built from .udos.md document frontmatter.
No manual index maintenance required - documents declare their own relationships.

v1.0.0.54+: Integrated with TileHierarchy for cascading knowledge.
Knowledge at parent tiles (higher zoom) cascades to child tiles (detailed zoom).

Part of uDOS Alpha v1.0.0.53+
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import yaml

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("knowledge-graph")


class DocumentStatus(Enum):
    """Document lifecycle status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class LinkType(Enum):
    """Types of document relationships."""

    REQUIRES = "requires"  # Prerequisites
    RELATED = "related"  # See also
    EXTENDS = "extends"  # Builds on
    SUPERSEDES = "supersedes"  # Replaces
    CHILDREN = "children"  # Sub-documents


@dataclass
class DocumentNode:
    """A node in the knowledge graph representing a document."""

    id: str
    title: str
    path: Path
    status: DocumentStatus = DocumentStatus.DRAFT
    doc_type: str = "guide"
    version: str = "1.0.0"

    # Timestamps
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    published: Optional[datetime] = None

    # Author info
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    author_rank: str = "novice"

    # Categorization
    tags_primary: List[str] = field(default_factory=list)
    tags_secondary: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    skill_level: str = "beginner"

    # Quality
    quality_score: float = 0.0
    quality_votes: int = 0
    verified: bool = False

    # Location
    location_binding: str = "none"
    location_tiles: List[Dict] = field(default_factory=list)
    location_regions: List[Dict] = field(default_factory=list)

    # Overlay hints
    include_in_overlays: List[str] = field(default_factory=list)
    exclude_from_overlays: List[str] = field(default_factory=list)

    # Executable
    executable: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "path": str(self.path),
            "status": self.status.value,
            "type": self.doc_type,
            "version": self.version,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "tags": {"primary": self.tags_primary, "secondary": self.tags_secondary},
            "categories": self.categories,
            "skill_level": self.skill_level,
            "quality": {
                "score": self.quality_score,
                "votes": self.quality_votes,
                "verified": self.verified,
            },
            "location": {
                "binding": self.location_binding,
                "tiles": self.location_tiles,
            },
            "executable": self.executable,
        }


@dataclass
class DocumentEdge:
    """An edge in the knowledge graph representing a relationship."""

    source_id: str
    target_id: str
    link_type: LinkType
    metadata: Dict = field(default_factory=dict)


class KnowledgeGraph:
    """
    Self-indexing knowledge graph.

    Builds automatically from document frontmatter.
    Supports queries by tag, category, location, and graph traversal.

    v1.0.0.54+: Integrates with TileHierarchy for cascading knowledge.
    """

    def __init__(self, knowledge_paths: List[Path] = None):
        """
        Initialize knowledge graph.

        Args:
            knowledge_paths: Paths to scan for .udos.md files
        """
        self.nodes: Dict[str, DocumentNode] = {}
        self.edges: List[DocumentEdge] = []
        self.back_links: Dict[str, List[Tuple[str, LinkType]]] = (
            {}
        )  # target -> [(source, type)]

        # Indexes for fast lookup
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> doc_ids
        self._category_index: Dict[str, Set[str]] = {}  # category -> doc_ids
        self._tile_index: Dict[str, Set[str]] = {}  # tile -> doc_ids (flat)
        self._status_index: Dict[str, Set[str]] = {}  # status -> doc_ids

        # Hierarchical tile index (v1.0.0.54+)
        self._tile_hierarchy = None  # Lazy load

        # Paths to scan
        self.knowledge_paths = knowledge_paths or []

        # Cache metadata
        self._last_build: Optional[datetime] = None
        self._doc_count: int = 0

        logger.info(
            f"[LOCAL] KnowledgeGraph initialized with {len(self.knowledge_paths)} paths"
        )

    @property
    def tile_hierarchy(self):
        """Lazy-load tile hierarchy integration."""
        if self._tile_hierarchy is None:
            from dev.goblin.core.services.tile_hierarchy import get_tile_hierarchy

            self._tile_hierarchy = get_tile_hierarchy()
        return self._tile_hierarchy

    def build(self, force: bool = False) -> int:
        """
        Build/rebuild the knowledge graph from documents.

        Args:
            force: Force rebuild even if cache is fresh

        Returns:
            Number of documents indexed
        """
        logger.info("[LOCAL] Building knowledge graph...")

        # Clear existing data
        self.nodes.clear()
        self.edges.clear()
        self.back_links.clear()
        self._tag_index.clear()
        self._category_index.clear()
        self._tile_index.clear()
        self._status_index.clear()

        # Scan all paths
        doc_count = 0
        for base_path in self.knowledge_paths:
            if not base_path.exists():
                logger.warning(f"[LOCAL] Knowledge path not found: {base_path}")
                continue

            for doc_path in base_path.rglob("*.udos.md"):
                try:
                    node = self._parse_document(doc_path)
                    if node:
                        self._add_node(node)
                        doc_count += 1
                except Exception as e:
                    logger.error(f"[LOCAL] Error parsing {doc_path}: {e}")

            # Also index regular .md files with frontmatter
            for doc_path in base_path.rglob("*.md"):
                if doc_path.suffix == ".md" and not str(doc_path).endswith(".udos.md"):
                    try:
                        node = self._parse_document(doc_path)
                        if node:
                            self._add_node(node)
                            doc_count += 1
                    except Exception as e:
                        logger.error(f"[LOCAL] Error parsing {doc_path}: {e}")

        # Build edges from links
        self._build_edges()

        # Update metadata
        self._last_build = datetime.now()
        self._doc_count = doc_count

        logger.info(
            f"[LOCAL] Knowledge graph built: {doc_count} documents, {len(self.edges)} edges"
        )
        return doc_count

    def _parse_document(self, path: Path) -> Optional[DocumentNode]:
        """
        Parse document frontmatter into a DocumentNode.

        Args:
            path: Path to the document

        Returns:
            DocumentNode or None if no valid frontmatter
        """
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"[LOCAL] Cannot read {path}: {e}")
            return None

        # Extract YAML frontmatter
        frontmatter = self._extract_frontmatter(content)
        if not frontmatter:
            return None

        # Generate ID if not present
        doc_id = frontmatter.get("id")
        if not doc_id:
            # Generate from path
            rel_path = path.stem.replace(".udos", "")
            doc_id = f"kb_{rel_path.replace('-', '_').replace('/', '_')}"

        # Parse timestamps
        created = self._parse_datetime(frontmatter.get("created"))
        updated = self._parse_datetime(frontmatter.get("updated"))
        published = self._parse_datetime(frontmatter.get("published"))

        # Parse author
        author = frontmatter.get("author", {})
        if isinstance(author, str):
            author = {"name": author}

        # Parse tags
        tags = frontmatter.get("tags", {})
        if isinstance(tags, list):
            tags = {"primary": tags}

        # Parse location
        location = frontmatter.get("location", {})

        # Parse quality
        quality = frontmatter.get("quality", {})

        # Create node
        node = DocumentNode(
            id=doc_id,
            title=frontmatter.get("title", path.stem),
            path=path,
            status=DocumentStatus(frontmatter.get("status", "draft")),
            doc_type=frontmatter.get("type", "guide"),
            version=frontmatter.get("version", "1.0.0"),
            created=created,
            updated=updated,
            published=published,
            author_id=author.get("id"),
            author_name=author.get("name"),
            author_rank=author.get("rank", "novice"),
            tags_primary=tags.get("primary", []),
            tags_secondary=tags.get("secondary", []),
            categories=frontmatter.get("categories", []),
            skill_level=tags.get("skill_level", "beginner"),
            quality_score=quality.get("score", 0.0),
            quality_votes=quality.get("votes", 0),
            verified=quality.get("verified", False),
            location_binding=location.get("binding", "none"),
            location_tiles=location.get("tiles", []),
            location_regions=location.get("regions", []),
            include_in_overlays=frontmatter.get("overlay", {}).get("include_in", []),
            exclude_from_overlays=frontmatter.get("overlay", {}).get(
                "exclude_from", []
            ),
            executable=frontmatter.get("executable", False),
        )

        # Store raw links for edge building
        node._raw_links = frontmatter.get("links", {})

        return node

    def _extract_frontmatter(self, content: str) -> Optional[Dict]:
        """Extract YAML frontmatter from document content."""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not match:
            return None

        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError as e:
            logger.warning(f"[LOCAL] Invalid YAML frontmatter: {e}")
            return None

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _add_node(self, node: DocumentNode):
        """Add a node and update indexes."""
        self.nodes[node.id] = node

        # Update tag index
        for tag in node.tags_primary + node.tags_secondary:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(node.id)

        # Update category index
        for category in node.categories:
            if category not in self._category_index:
                self._category_index[category] = set()
            self._category_index[category].add(node.id)

            # Also index parent categories
            parts = category.split("/")
            for i in range(len(parts)):
                parent = "/".join(parts[: i + 1])
                if parent not in self._category_index:
                    self._category_index[parent] = set()
                self._category_index[parent].add(node.id)

        # Update tile index (flat and hierarchical)
        for tile in node.location_tiles:
            coord = tile.get("coord", "")
            layer = tile.get("layer", 300)
            cascade = tile.get("cascade", True)  # Default: cascade to children

            if coord:
                # Flat index (backward compat)
                if coord not in self._tile_index:
                    self._tile_index[coord] = set()
                self._tile_index[coord].add(node.id)

                # Full tile path
                full_path = f"L{layer:03d}:{coord}"
                if full_path not in self._tile_index:
                    self._tile_index[full_path] = set()
                self._tile_index[full_path].add(node.id)

                # Register with tile hierarchy for cascade support
                try:
                    self.tile_hierarchy.attach_document(
                        node.id, full_path, cascade_up=False
                    )
                except Exception as e:
                    logger.debug(f"[LOCAL] Tile hierarchy attach failed: {e}")

        # Update status index
        status = node.status.value
        if status not in self._status_index:
            self._status_index[status] = set()
        self._status_index[status].add(node.id)

    def _build_edges(self):
        """Build edges from document links."""
        for node_id, node in self.nodes.items():
            raw_links = getattr(node, "_raw_links", {})

            for link_type_str, links in raw_links.items():
                try:
                    link_type = LinkType(link_type_str)
                except ValueError:
                    continue

                if not isinstance(links, list):
                    continue

                for link in links:
                    if isinstance(link, dict):
                        target_id = link.get("id")
                    elif isinstance(link, str):
                        target_id = link
                    else:
                        continue

                    if not target_id:
                        continue

                    # Create edge
                    edge = DocumentEdge(
                        source_id=node_id,
                        target_id=target_id,
                        link_type=link_type,
                        metadata=link if isinstance(link, dict) else {},
                    )
                    self.edges.append(edge)

                    # Create back-link
                    if target_id not in self.back_links:
                        self.back_links[target_id] = []
                    self.back_links[target_id].append((node_id, link_type))

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get(self, doc_id: str) -> Optional[DocumentNode]:
        """Get a document by ID."""
        return self.nodes.get(doc_id)

    def query(
        self,
        tags: List[str] = None,
        tags_any: List[str] = None,
        tags_all: List[str] = None,
        categories: List[str] = None,
        status: DocumentStatus = None,
        tile: str = None,
        include_inherited: bool = False,
        skill_level: str = None,
        min_quality: float = None,
        verified_only: bool = False,
        limit: int = None,
    ) -> List[DocumentNode]:
        """
        Query documents with filters.

        Args:
            tags: Alias for tags_any
            tags_any: Match if any tag present
            tags_all: Match only if all tags present
            categories: Match if in any category (supports wildcards)
            status: Filter by status
            tile: Filter by tile coordinate (e.g., "L300:BD14" or "BD14")
            include_inherited: Include docs from ancestor tiles (cascade)
            skill_level: Filter by skill level
            min_quality: Minimum quality score
            verified_only: Only verified documents
            limit: Maximum results

        Returns:
            List of matching DocumentNodes
        """
        results = set(self.nodes.keys())

        # Tags (any)
        if tags or tags_any:
            tag_list = tags or tags_any
            tag_matches = set()
            for tag in tag_list:
                tag_matches.update(self._tag_index.get(tag, set()))
            results &= tag_matches

        # Tags (all)
        if tags_all:
            for tag in tags_all:
                results &= self._tag_index.get(tag, set())

        # Categories
        if categories:
            cat_matches = set()
            for cat in categories:
                if cat.endswith("/*"):
                    # Wildcard - match all in category
                    prefix = cat[:-2]
                    for key, ids in self._category_index.items():
                        if key.startswith(prefix):
                            cat_matches.update(ids)
                else:
                    cat_matches.update(self._category_index.get(cat, set()))
            results &= cat_matches

        # Status
        if status:
            results &= self._status_index.get(status.value, set())

        # Tile (with optional inheritance from parent tiles)
        if tile:
            tile_matches = set()

            if include_inherited:
                # Use hierarchical query with inheritance
                tile_matches = self.tile_hierarchy.get_documents_at(
                    tile, include_inherited=True
                )

            # Also check flat index (for backward compatibility and wildcards)
            if tile.endswith("*"):
                # Wildcard matching
                prefix = tile[:-1]
                for key, ids in self._tile_index.items():
                    if key.startswith(prefix):
                        tile_matches.update(ids)
            else:
                tile_matches.update(self._tile_index.get(tile, set()))

            results &= tile_matches

        # Convert to nodes and apply remaining filters
        nodes = []
        for doc_id in results:
            node = self.nodes[doc_id]

            # Skill level filter
            if skill_level and node.skill_level != skill_level:
                continue

            # Quality filter
            if min_quality is not None and node.quality_score < min_quality:
                continue

            # Verified filter
            if verified_only and not node.verified:
                continue

            nodes.append(node)

        # Sort by quality score (descending)
        nodes.sort(key=lambda n: n.quality_score, reverse=True)

        # Apply limit
        if limit:
            nodes = nodes[:limit]

        return nodes

    def get_linked(
        self, doc_id: str, link_type: LinkType = None, direction: str = "out"
    ) -> List[DocumentNode]:
        """
        Get documents linked to/from a document.

        Args:
            doc_id: Source document ID
            link_type: Filter by link type (or all if None)
            direction: "out" for outgoing, "in" for incoming (back-links)

        Returns:
            List of linked DocumentNodes
        """
        results = []

        if direction == "out":
            # Outgoing links
            for edge in self.edges:
                if edge.source_id == doc_id:
                    if link_type is None or edge.link_type == link_type:
                        target = self.nodes.get(edge.target_id)
                        if target:
                            results.append(target)
        else:
            # Incoming links (back-links)
            back = self.back_links.get(doc_id, [])
            for source_id, lt in back:
                if link_type is None or lt == link_type:
                    source = self.nodes.get(source_id)
                    if source:
                        results.append(source)

        return results

    def get_prerequisites(self, doc_id: str) -> List[DocumentNode]:
        """Get all prerequisite documents (requires links)."""
        return self.get_linked(doc_id, LinkType.REQUIRES, "out")

    def get_related(self, doc_id: str) -> List[DocumentNode]:
        """Get all related documents (bidirectional)."""
        out = self.get_linked(doc_id, LinkType.RELATED, "out")
        incoming = self.get_linked(doc_id, LinkType.RELATED, "in")
        # Deduplicate
        seen = set()
        results = []
        for node in out + incoming:
            if node.id not in seen:
                seen.add(node.id)
                results.append(node)
        return results

    def get_citations(self, doc_id: str) -> List[DocumentNode]:
        """Get documents that cite this one (all incoming links)."""
        return self.get_linked(doc_id, direction="in")

    # =========================================================================
    # Hierarchical Tile Queries (v1.0.0.54+)
    # =========================================================================

    def query_at_tile(
        self,
        tile_path: str,
        include_inherited: bool = True,
        status: DocumentStatus = None,
        min_quality: float = None,
        limit: int = None,
    ) -> List[DocumentNode]:
        """
        Query documents at a tile with inheritance from parent tiles.

        Knowledge cascades DOWN: a document at L300 (world overview) is
        available at all child tiles (L310, L320, etc).

        Args:
            tile_path: Tile path (e.g., "L300:BD14" or "BD14")
            include_inherited: Include docs from ancestor tiles
            status: Filter by status
            min_quality: Minimum quality score
            limit: Maximum results

        Returns:
            List of matching DocumentNodes
        """
        # Get document IDs from tile hierarchy
        doc_ids = self.tile_hierarchy.get_documents_at(tile_path, include_inherited)

        # Also check flat index for backward compatibility
        from dev.goblin.core.services.tile_hierarchy import TileHierarchy

        location = TileHierarchy.parse_tile(tile_path)
        if location:
            # Add from flat index
            doc_ids.update(self._tile_index.get(location.coord, set()))
            doc_ids.update(self._tile_index.get(location.full_path, set()))

        # Convert to nodes and filter
        nodes = []
        for doc_id in doc_ids:
            node = self.nodes.get(doc_id)
            if not node:
                continue

            if status and node.status != status:
                continue

            if min_quality is not None and node.quality_score < min_quality:
                continue

            nodes.append(node)

        # Sort by quality
        nodes.sort(key=lambda n: n.quality_score, reverse=True)

        if limit:
            nodes = nodes[:limit]

        return nodes

    def query_tile_pattern(
        self, pattern: str, include_inherited: bool = True, limit: int = None
    ) -> List[DocumentNode]:
        """
        Query documents matching a tile pattern with wildcards.

        Patterns:
            - "L300:*"      - All tiles at layer 300 (world level)
            - "L300:BD*"    - Tiles starting with BD at layer 300
            - "L3*:BD14"    - BD14 across all Earth layers (300-399)
            - "*:BD14"      - BD14 at any layer

        Args:
            pattern: Tile pattern with wildcards
            include_inherited: Include inherited documents
            limit: Maximum results

        Returns:
            List of matching DocumentNodes
        """
        doc_ids = self.tile_hierarchy.query_tiles(pattern, include_inherited)

        nodes = [self.nodes[did] for did in doc_ids if did in self.nodes]
        nodes.sort(key=lambda n: n.quality_score, reverse=True)

        if limit:
            nodes = nodes[:limit]

        return nodes

    def get_tile_hierarchy_path(self, tile_path: str) -> List[Dict[str, Any]]:
        """
        Get the knowledge hierarchy for a tile.

        Returns list from global (root) to specific (tile), showing
        document counts at each level.

        Example for L320:BD14:
        [
            {"location": "L300:BD14", "name": "Earth", "doc_count": 5},
            {"location": "L310:BD14", "name": "Europe", "doc_count": 12},
            {"location": "L320:BD14", "name": "UK", "doc_count": 8},
        ]
        """
        return self.tile_hierarchy.get_hierarchy_path(tile_path)

    def get_knowledge_at_zoom(
        self, tile_path: str, zoom_level: int = None
    ) -> Dict[str, Any]:
        """
        Get knowledge summary at a specific zoom level.

        Args:
            tile_path: Base tile path
            zoom_level: Override zoom (or use tile's layer)

        Returns:
            Dict with knowledge summary including inherited docs
        """
        from dev.goblin.core.services.tile_hierarchy import TileHierarchy

        location = TileHierarchy.parse_tile(tile_path)
        if not location:
            return {"error": "Invalid tile path"}

        # Get hierarchy path
        hierarchy = self.get_tile_hierarchy_path(tile_path)

        # Get documents with inheritance
        docs = self.query_at_tile(tile_path, include_inherited=True)

        # Categorize by source level
        local_docs = []
        inherited_docs = []

        local_path = location.full_path
        for doc in docs:
            is_local = False
            for tile in doc.location_tiles:
                tile_full = f"L{tile.get('layer', 300):03d}:{tile.get('coord', '')}"
                if tile_full == local_path:
                    is_local = True
                    break

            if is_local:
                local_docs.append(doc)
            else:
                inherited_docs.append(doc)

        return {
            "tile": location.full_path,
            "realm": location.realm.value,
            "hierarchy": hierarchy,
            "local_documents": len(local_docs),
            "inherited_documents": len(inherited_docs),
            "total_documents": len(docs),
            "documents": [
                {
                    "id": d.id,
                    "title": d.title,
                    "inherited": d not in local_docs,
                    "quality": d.quality_score,
                }
                for d in docs[:20]  # Limit preview
            ],
        }

    def search(self, query: str, limit: int = 20) -> List[DocumentNode]:
        """
        Full-text search in titles and tags.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching DocumentNodes
        """
        query_lower = query.lower()
        scored = []

        for node in self.nodes.values():
            score = 0

            # Title match (highest weight)
            if query_lower in node.title.lower():
                score += 10
                if node.title.lower().startswith(query_lower):
                    score += 5

            # Tag match
            for tag in node.tags_primary:
                if query_lower in tag.lower():
                    score += 5
            for tag in node.tags_secondary:
                if query_lower in tag.lower():
                    score += 2

            # Category match
            for cat in node.categories:
                if query_lower in cat.lower():
                    score += 3

            if score > 0:
                scored.append((node, score))

        # Sort by score, then quality
        scored.sort(key=lambda x: (x[1], x[0].quality_score), reverse=True)

        return [node for node, score in scored[:limit]]

    # =========================================================================
    # Statistics
    # =========================================================================

    def stats(self) -> Dict:
        """Get graph statistics."""
        return {
            "documents": len(self.nodes),
            "edges": len(self.edges),
            "unique_tags": len(self._tag_index),
            "unique_categories": len(self._category_index),
            "indexed_tiles": len(self._tile_index),
            "by_status": {
                status: len(ids) for status, ids in self._status_index.items()
            },
            "last_build": self._last_build.isoformat() if self._last_build else None,
        }

    def export_json(self, path: Path):
        """Export graph to JSON for caching."""
        data = {
            "meta": {"exported": datetime.now().isoformat(), "stats": self.stats()},
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "type": e.link_type.value,
                    "metadata": e.metadata,
                }
                for e in self.edges
            ],
        }

        path.write_text(json.dumps(data, indent=2))
        logger.info(f"[LOCAL] Knowledge graph exported to {path}")


# Singleton instance
_graph: Optional[KnowledgeGraph] = None


def get_knowledge_graph() -> KnowledgeGraph:
    """Get or create the singleton knowledge graph."""
    global _graph
    if _graph is None:
        from dev.goblin.core.config import Config

        config = Config()

        # Default paths
        paths = [
            Path(config.get("knowledge_path", "knowledge")),
            Path(config.get("memory_path", "memory")) / "library",
        ]

        _graph = KnowledgeGraph(knowledge_paths=paths)

    return _graph


def rebuild_graph() -> int:
    """Force rebuild of the knowledge graph."""
    graph = get_knowledge_graph()
    return graph.build(force=True)
