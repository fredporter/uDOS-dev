"""
Document Manager Service

CRUD operations for .udos.md documents with lifecycle management.
Handles frontmatter generation, validation, and state transitions.

Part of uDOS Alpha v1.0.0.53+
"""

import re
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from dev.goblin.core.services.logging_manager import get_logger
from dev.goblin.core.services.knowledge_graph import (
    DocumentStatus,
    DocumentNode,
    get_knowledge_graph,
    rebuild_graph,
)

logger = get_logger("document-manager")


class DocumentError(Exception):
    """Document operation error."""

    pass


class PermissionError(DocumentError):
    """Permission denied for operation."""

    pass


class ValidationError(DocumentError):
    """Document validation failed."""

    pass


@dataclass
class UserContext:
    """User context for permission checking."""

    user_id: str
    name: str
    rank: str = "novice"  # novice, contributor, expert, wizard, system

    def can_edit(self, doc: DocumentNode) -> bool:
        """Check if user can edit document."""
        rank_levels = {
            "novice": 0,
            "contributor": 1,
            "expert": 2,
            "wizard": 3,
            "system": 4,
        }
        user_level = rank_levels.get(self.rank, 0)

        # Author can always edit their own drafts
        if doc.author_id == self.user_id and doc.status == DocumentStatus.DRAFT:
            return True

        # Check by rank
        if self.rank == "wizard" or self.rank == "system":
            return True
        if self.rank == "expert" and doc.author_id == self.user_id:
            return True

        return False

    def can_publish(self, global_publish: bool = False) -> bool:
        """Check if user can publish documents."""
        if global_publish:
            return self.rank in ("expert", "wizard", "system")
        else:
            return self.rank in ("contributor", "expert", "wizard", "system")

    def can_approve(self) -> bool:
        """Check if user can approve submissions."""
        return self.rank in ("expert", "wizard", "system")

    def can_archive(self) -> bool:
        """Check if user can archive documents."""
        return self.rank in ("wizard", "system")


class DocumentManager:
    """
    Manages .udos.md document lifecycle.

    Provides CRUD operations with permission checking and
    automatic frontmatter management.
    """

    def __init__(
        self,
        drafts_path: Path = None,
        contributions_path: Path = None,
        knowledge_path: Path = None,
        library_path: Path = None,
    ):
        """
        Initialize document manager.

        Args:
            drafts_path: Where user drafts are stored
            contributions_path: Where submissions await review
            knowledge_path: Global published knowledge
            library_path: User's personal library
        """
        self.drafts_path = drafts_path or Path("memory/drafts")
        self.contributions_path = contributions_path or Path("memory/contributions")
        self.knowledge_path = knowledge_path or Path("knowledge")
        self.library_path = library_path or Path("memory/library")

        # Ensure directories exist
        self.drafts_path.mkdir(parents=True, exist_ok=True)
        self.contributions_path.mkdir(parents=True, exist_ok=True)
        self.library_path.mkdir(parents=True, exist_ok=True)

        logger.info("[LOCAL] DocumentManager initialized")

    def _generate_id(self, title: str, category: str = "") -> str:
        """Generate unique document ID."""
        # Slugify title
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower())[:30]
        # Get category prefix
        cat_prefix = category.split("/")[0][:10] if category else "doc"
        # Random suffix
        suffix = secrets.token_hex(3)
        return f"kb_{cat_prefix}_{slug}_{suffix}"

    def _generate_frontmatter(
        self,
        title: str,
        doc_type: str = "guide",
        user: UserContext = None,
        categories: List[str] = None,
        tags: List[str] = None,
        **kwargs,
    ) -> str:
        """Generate YAML frontmatter for a new document."""
        now = datetime.now().isoformat()
        doc_id = self._generate_id(title, categories[0] if categories else "")

        frontmatter = {
            "id": doc_id,
            "title": title,
            "type": doc_type,
            "version": "1.0.0",
            "status": "draft",
            "created": now,
            "updated": now,
        }

        # Author info
        if user:
            frontmatter["author"] = {
                "id": user.user_id,
                "name": user.name,
                "rank": user.rank,
            }

        # Tags
        if tags:
            frontmatter["tags"] = {"primary": tags, "secondary": []}

        # Categories
        if categories:
            frontmatter["categories"] = categories

        # Quality (starts at 0)
        frontmatter["quality"] = {"score": 0.0, "votes": 0, "verified": False}

        # Location (optional)
        if kwargs.get("location"):
            frontmatter["location"] = kwargs["location"]

        # Executable
        if kwargs.get("executable"):
            frontmatter["executable"] = True
            frontmatter["runtime"] = {"requires": ["core"], "sandbox": True}

        # Convert to YAML-like string (simple formatting)
        lines = ["---"]
        lines.extend(self._dict_to_yaml(frontmatter))
        lines.append("---")

        return "\n".join(lines)

    def _dict_to_yaml(self, d: Dict, indent: int = 0) -> List[str]:
        """Convert dict to YAML lines (simple implementation)."""
        lines = []
        prefix = "  " * indent

        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.extend(self._dict_to_yaml(value, indent + 1))
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{prefix}{key}: []")
                elif isinstance(value[0], dict):
                    lines.append(f"{prefix}{key}:")
                    for item in value:
                        lines.append(f"{prefix}  -")
                        for k, v in item.items():
                            lines.append(f"{prefix}    {k}: {v}")
                else:
                    lines.append(f"{prefix}{key}: [{', '.join(str(v) for v in value)}]")
            elif isinstance(value, bool):
                lines.append(f"{prefix}{key}: {str(value).lower()}")
            elif isinstance(value, (int, float)):
                lines.append(f"{prefix}{key}: {value}")
            elif value is None:
                lines.append(f"{prefix}{key}: null")
            else:
                # String - quote if contains special chars
                if any(c in str(value) for c in ":#{}[]"):
                    lines.append(f'{prefix}{key}: "{value}"')
                else:
                    lines.append(f"{prefix}{key}: {value}")

        return lines

    def create(
        self,
        title: str,
        content: str = "",
        doc_type: str = "guide",
        user: UserContext = None,
        categories: List[str] = None,
        tags: List[str] = None,
        **kwargs,
    ) -> Path:
        """
        Create a new document in drafts.

        Args:
            title: Document title
            content: Initial markdown content
            doc_type: Document type (guide, checklist, etc.)
            user: User context
            categories: Categories for the document
            tags: Primary tags
            **kwargs: Additional frontmatter fields

        Returns:
            Path to created document
        """
        # Generate frontmatter
        frontmatter = self._generate_frontmatter(
            title=title,
            doc_type=doc_type,
            user=user,
            categories=categories,
            tags=tags,
            **kwargs,
        )

        # Create filename
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower())[:50]
        filename = f"{slug}.udos.md"

        # Determine path based on category
        if categories:
            doc_path = self.drafts_path / categories[0].replace("/", "-") / filename
        else:
            doc_path = self.drafts_path / filename

        doc_path.parent.mkdir(parents=True, exist_ok=True)

        # Build document
        full_content = f"{frontmatter}\n\n# {title}\n\n{content}\n"

        # Write
        doc_path.write_text(full_content, encoding="utf-8")

        logger.info(f"[LOCAL] Created document: {doc_path}")
        return doc_path

    def read(self, doc_id: str) -> Optional[Dict]:
        """
        Read a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Dict with frontmatter and content, or None
        """
        graph = get_knowledge_graph()
        node = graph.get(doc_id)

        if not node:
            return None

        try:
            content = node.path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"[LOCAL] Cannot read document {doc_id}: {e}")
            return None

        # Split frontmatter and content
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if match:
            return {
                "id": doc_id,
                "path": str(node.path),
                "frontmatter": node.to_dict(),
                "content": match.group(2),
            }

        return {
            "id": doc_id,
            "path": str(node.path),
            "frontmatter": node.to_dict(),
            "content": content,
        }

    def update(
        self,
        doc_id: str,
        content: str = None,
        frontmatter_updates: Dict = None,
        user: UserContext = None,
    ) -> bool:
        """
        Update an existing document.

        Args:
            doc_id: Document ID
            content: New content (or None to keep existing)
            frontmatter_updates: Fields to update in frontmatter
            user: User context for permission check

        Returns:
            True if updated successfully
        """
        graph = get_knowledge_graph()
        node = graph.get(doc_id)

        if not node:
            raise DocumentError(f"Document not found: {doc_id}")

        # Permission check
        if user and not user.can_edit(node):
            raise PermissionError(f"User cannot edit document: {doc_id}")

        # Read current content
        try:
            current = node.path.read_text(encoding="utf-8")
        except Exception as e:
            raise DocumentError(f"Cannot read document: {e}")

        # Parse existing frontmatter
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", current, re.DOTALL)
        if not match:
            raise DocumentError("Document has invalid format")

        existing_content = match.group(2)

        # Use new content if provided
        if content is not None:
            existing_content = content

        # Update frontmatter timestamp
        if frontmatter_updates is None:
            frontmatter_updates = {}
        frontmatter_updates["updated"] = datetime.now().isoformat()

        # Add contributor if not author
        if user and node.author_id != user.user_id:
            # This would need to parse and update the contributors list
            pass

        # Rebuild frontmatter (simplified - in production, parse and merge)
        # For now, just update the timestamp in the raw content
        updated = re.sub(
            r"(updated:\s*).*", f"\\1{frontmatter_updates['updated']}", current
        )

        if content is not None:
            # Replace content after frontmatter
            updated = re.sub(
                r"^(---\s*\n.*?\n---\s*\n).*$",
                f"\\1{content}",
                updated,
                flags=re.DOTALL,
            )

        # Write
        node.path.write_text(updated, encoding="utf-8")

        logger.info(f"[LOCAL] Updated document: {doc_id}")
        return True

    def submit(self, doc_id: str, user: UserContext) -> bool:
        """
        Submit a draft for review.

        Args:
            doc_id: Document ID
            user: User context

        Returns:
            True if submitted successfully
        """
        graph = get_knowledge_graph()
        node = graph.get(doc_id)

        if not node:
            raise DocumentError(f"Document not found: {doc_id}")

        if node.status != DocumentStatus.DRAFT:
            raise DocumentError(
                f"Only drafts can be submitted. Current status: {node.status.value}"
            )

        if node.author_id != user.user_id:
            raise PermissionError("Only author can submit document")

        # Move to contributions folder
        new_path = self.contributions_path / node.path.name

        # Update status in content
        content = node.path.read_text(encoding="utf-8")
        content = re.sub(r"status:\s*draft", "status: submitted", content)

        # Write to new location
        new_path.write_text(content, encoding="utf-8")

        # Remove from drafts
        node.path.unlink()

        # Rebuild graph
        rebuild_graph()

        logger.info(f"[LOCAL] Submitted document for review: {doc_id}")
        return True

    def approve(
        self, doc_id: str, user: UserContext, global_publish: bool = True
    ) -> bool:
        """
        Approve a submitted document and publish it.

        Args:
            doc_id: Document ID
            user: User context (must be expert+)
            global_publish: Publish to global knowledge (vs personal library)

        Returns:
            True if approved and published
        """
        if not user.can_approve():
            raise PermissionError("User cannot approve documents")

        graph = get_knowledge_graph()
        node = graph.get(doc_id)

        if not node:
            raise DocumentError(f"Document not found: {doc_id}")

        if node.status != DocumentStatus.SUBMITTED:
            raise DocumentError(
                f"Only submitted documents can be approved. Current status: {node.status.value}"
            )

        # Determine destination
        if global_publish:
            # Get category from document
            category = node.categories[0] if node.categories else "general"
            dest_path = self.knowledge_path / category / node.path.name
        else:
            dest_path = self.library_path / node.path.name

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Update status and add published timestamp
        content = node.path.read_text(encoding="utf-8")
        content = re.sub(r"status:\s*submitted", "status: published", content)
        content = re.sub(
            r"(updated:.*)", f"\\1\npublished: {datetime.now().isoformat()}", content
        )

        # Write to destination
        dest_path.write_text(content, encoding="utf-8")

        # Remove from contributions
        node.path.unlink()

        # Rebuild graph
        rebuild_graph()

        logger.info(f"[LOCAL] Approved and published document: {doc_id} -> {dest_path}")
        return True

    def archive(self, doc_id: str, user: UserContext) -> bool:
        """
        Archive a published document.

        Args:
            doc_id: Document ID
            user: User context (must be wizard+)

        Returns:
            True if archived
        """
        if not user.can_archive():
            raise PermissionError("User cannot archive documents")

        graph = get_knowledge_graph()
        node = graph.get(doc_id)

        if not node:
            raise DocumentError(f"Document not found: {doc_id}")

        # Move to archive
        archive_path = self.knowledge_path / ".archive" / node.path.name
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        # Update status
        content = node.path.read_text(encoding="utf-8")
        content = re.sub(r"status:\s*\w+", "status: archived", content)

        # Write to archive
        archive_path.write_text(content, encoding="utf-8")

        # Remove original
        node.path.unlink()

        # Rebuild graph
        rebuild_graph()

        logger.info(f"[LOCAL] Archived document: {doc_id}")
        return True

    def delete(self, doc_id: str, user: UserContext) -> bool:
        """
        Delete a draft document (only drafts can be deleted).

        Args:
            doc_id: Document ID
            user: User context

        Returns:
            True if deleted
        """
        graph = get_knowledge_graph()
        node = graph.get(doc_id)

        if not node:
            raise DocumentError(f"Document not found: {doc_id}")

        if node.status != DocumentStatus.DRAFT:
            raise DocumentError(
                "Only drafts can be deleted. Archive or deprecate published documents."
            )

        if node.author_id != user.user_id and user.rank not in ("wizard", "system"):
            raise PermissionError("Only author or wizard can delete document")

        # Delete file
        node.path.unlink()

        # Rebuild graph
        rebuild_graph()

        logger.info(f"[LOCAL] Deleted document: {doc_id}")
        return True


# Singleton instance
_manager: Optional[DocumentManager] = None


def get_document_manager() -> DocumentManager:
    """Get or create the singleton document manager."""
    global _manager
    if _manager is None:
        _manager = DocumentManager()
    return _manager
