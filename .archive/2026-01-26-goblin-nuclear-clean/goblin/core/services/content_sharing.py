#!/usr/bin/env python3
"""
uDOS v1.3.2 - Content Sharing System

5-tier content sharing model for user-generated content:

1. PUBLIC KNOWLEDGE (read-only)
   - Core /knowledge bank, Wizard/dev curated
   - Highest quality, vetted content
   - Distributed with uDOS installation

2. SHARED PUBLIC
   - User submissions to Public Knowledge Bank
   - Review and approval process
   - Community-vetted content

3. EXPLICIT USER-TO-USER
   - Physical proximity required (IRL connections)
   - Mesh-based verification
   - Direct peer-to-peer sharing

4. EXPLICIT USER-TO-GROUP
   - Submission to approved groups
   - Content must match group topic
   - Interest-focused communities

5. PRIVATE
   - Never shared, local only
   - Sandbox/development content
   - Personal files

Content Types: scripts, tiles, guides, workflows
Metadata: Version, TIME-DATE-LOCATION tracking
Attribution: Personal/user attribution model only

Version: 1.3.2
Author: Fred Porter
Date: December 2025
"""

import json
import hashlib
import secrets
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


# =============================================================================
# Share Status Enum
# =============================================================================

class ShareStatus(Enum):
    """
    5-tier sharing model (mutually exclusive).
    
    Each piece of content has exactly ONE share status.
    """
    PRIVATE = 1             # Never shared, local only
    USER_TO_USER = 2        # Explicit share, proximity required
    USER_TO_GROUP = 3       # Group submission, topic-relevant
    SHARED_PUBLIC = 4       # User submissions to Public Knowledge
    PUBLIC_KNOWLEDGE = 5    # Core /knowledge bank, Wizard curated
    
    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            ShareStatus.PRIVATE: "Private",
            ShareStatus.USER_TO_USER: "Shared (User)",
            ShareStatus.USER_TO_GROUP: "Shared (Group)",
            ShareStatus.SHARED_PUBLIC: "Public Submission",
            ShareStatus.PUBLIC_KNOWLEDGE: "Public Knowledge",
        }
        return names.get(self, "Unknown")
    
    @property
    def description(self) -> str:
        """Detailed description."""
        descs = {
            ShareStatus.PRIVATE: "Private content, never shared",
            ShareStatus.USER_TO_USER: "Shared with specific user (IRL proximity)",
            ShareStatus.USER_TO_GROUP: "Shared with group members (topic-relevant)",
            ShareStatus.SHARED_PUBLIC: "Submitted for Public Knowledge review",
            ShareStatus.PUBLIC_KNOWLEDGE: "Vetted content in Public Knowledge Bank",
        }
        return descs.get(self, "Unknown status")
    
    @property
    def icon(self) -> str:
        """Status icon."""
        icons = {
            ShareStatus.PRIVATE: "🔒",
            ShareStatus.USER_TO_USER: "🤝",
            ShareStatus.USER_TO_GROUP: "👥",
            ShareStatus.SHARED_PUBLIC: "📤",
            ShareStatus.PUBLIC_KNOWLEDGE: "📚",
        }
        return icons.get(self, "❓")


class ContentType(Enum):
    """Types of shareable content."""
    SCRIPT = "script"           # .upy files
    TILE = "tile"               # .json tile files
    GUIDE = "guide"             # .md knowledge guides
    WORKFLOW = "workflow"       # .upy workflow files
    TEMPLATE = "template"       # Template files
    ASSET = "asset"             # Other assets
    
    @property
    def extension(self) -> str:
        """File extension for this type."""
        exts = {
            ContentType.SCRIPT: ".upy",
            ContentType.TILE: ".json",
            ContentType.GUIDE: ".md",
            ContentType.WORKFLOW: ".upy",
            ContentType.TEMPLATE: ".json",
            ContentType.ASSET: "",
        }
        return exts.get(self, "")
    
    @property
    def directory(self) -> str:
        """Default directory for this type."""
        dirs = {
            ContentType.SCRIPT: "scripts",
            ContentType.TILE: "tiles",
            ContentType.GUIDE: "guides",
            ContentType.WORKFLOW: "workflows",
            ContentType.TEMPLATE: "templates",
            ContentType.ASSET: "assets",
        }
        return dirs.get(self, "other")


class SubmissionState(Enum):
    """States for content submissions."""
    DRAFT = "draft"             # Not yet submitted
    PENDING = "pending"         # Awaiting review
    REVIEWING = "reviewing"     # Under active review
    APPROVED = "approved"       # Accepted
    REJECTED = "rejected"       # Declined
    REVISION = "revision"       # Needs changes


# =============================================================================
# Content Metadata
# =============================================================================

@dataclass
class ContentLocation:
    """Location data for content (TIME-DATE-LOCATION tracking)."""
    tile_code: str = ""         # TILE code (e.g., "AA340")
    created_at: str = ""        # ISO timestamp
    updated_at: str = ""        # ISO timestamp
    timezone: str = ""          # Timezone string
    
    def to_dict(self) -> Dict:
        return {
            'tile_code': self.tile_code,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'timezone': self.timezone,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContentLocation':
        return cls(
            tile_code=data.get('tile_code', ''),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            timezone=data.get('timezone', ''),
        )
    
    @classmethod
    def now(cls, tile_code: str = "") -> 'ContentLocation':
        """Create location with current timestamp."""
        now = datetime.now().isoformat()
        return cls(
            tile_code=tile_code,
            created_at=now,
            updated_at=now,
        )


@dataclass
class ContentRating:
    """Rating for content (1-5 stars quality score)."""
    user_id: str                # Who rated
    stars: int                  # 1-5 rating
    timestamp: str              # When rated
    review: str = ""            # Optional review text
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'stars': self.stars,
            'timestamp': self.timestamp,
            'review': self.review,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContentRating':
        return cls(
            user_id=data['user_id'],
            stars=data['stars'],
            timestamp=data['timestamp'],
            review=data.get('review', ''),
        )


@dataclass
class ContentAttribution:
    """Attribution for content (personal/user model only)."""
    author_id: str              # User ID of creator
    author_name: str            # Display name
    license: str = "personal"   # License type (personal only for now)
    
    def to_dict(self) -> Dict:
        return {
            'author_id': self.author_id,
            'author_name': self.author_name,
            'license': self.license,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContentAttribution':
        return cls(
            author_id=data['author_id'],
            author_name=data['author_name'],
            license=data.get('license', 'personal'),
        )


# =============================================================================
# Content Submission
# =============================================================================

@dataclass
class ContentSubmission:
    """
    Content submission with full metadata.
    
    Tracks version, location, ratings, and share status.
    """
    # Identity
    content_id: str             # Unique content ID
    title: str                  # Content title
    description: str = ""       # Content description
    
    # Type and status
    content_type: ContentType = ContentType.SCRIPT
    share_status: ShareStatus = ShareStatus.PRIVATE
    submission_state: SubmissionState = SubmissionState.DRAFT
    
    # File info
    filename: str = ""          # Original filename
    file_hash: str = ""         # SHA256 hash of content
    file_size: int = 0          # Size in bytes
    
    # Versioning
    version: str = "1.0.0"      # Semantic version
    version_history: List[str] = field(default_factory=list)
    
    # Location tracking
    location: ContentLocation = field(default_factory=ContentLocation)
    
    # Attribution
    attribution: ContentAttribution = None
    
    # Ratings
    ratings: List[ContentRating] = field(default_factory=list)
    average_rating: float = 0.0
    
    # Sharing metadata
    shared_with: List[str] = field(default_factory=list)  # User IDs
    group_id: str = ""          # Group ID if USER_TO_GROUP
    
    # Tags and categorization
    tags: List[str] = field(default_factory=list)
    category: str = ""          # Category (water, fire, etc.)
    difficulty: str = ""        # beginner/intermediate/advanced
    
    # Review data
    reviewer_notes: str = ""    # Notes from reviewer
    revision_count: int = 0     # Number of revisions
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'content_id': self.content_id,
            'title': self.title,
            'description': self.description,
            'content_type': self.content_type.value,
            'share_status': self.share_status.value,
            'submission_state': self.submission_state.value,
            'filename': self.filename,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'version': self.version,
            'version_history': self.version_history,
            'location': self.location.to_dict(),
            'attribution': self.attribution.to_dict() if self.attribution else None,
            'ratings': [r.to_dict() for r in self.ratings],
            'average_rating': self.average_rating,
            'shared_with': self.shared_with,
            'group_id': self.group_id,
            'tags': self.tags,
            'category': self.category,
            'difficulty': self.difficulty,
            'reviewer_notes': self.reviewer_notes,
            'revision_count': self.revision_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContentSubmission':
        """Create from dictionary."""
        submission = cls(
            content_id=data['content_id'],
            title=data['title'],
            description=data.get('description', ''),
            content_type=ContentType(data.get('content_type', 'script')),
            share_status=ShareStatus(data.get('share_status', 1)),
            submission_state=SubmissionState(data.get('submission_state', 'draft')),
            filename=data.get('filename', ''),
            file_hash=data.get('file_hash', ''),
            file_size=data.get('file_size', 0),
            version=data.get('version', '1.0.0'),
            version_history=data.get('version_history', []),
            shared_with=data.get('shared_with', []),
            group_id=data.get('group_id', ''),
            tags=data.get('tags', []),
            category=data.get('category', ''),
            difficulty=data.get('difficulty', ''),
            reviewer_notes=data.get('reviewer_notes', ''),
            revision_count=data.get('revision_count', 0),
        )
        
        # Load nested objects
        if data.get('location'):
            submission.location = ContentLocation.from_dict(data['location'])
        if data.get('attribution'):
            submission.attribution = ContentAttribution.from_dict(data['attribution'])
        submission.ratings = [ContentRating.from_dict(r) for r in data.get('ratings', [])]
        submission.average_rating = data.get('average_rating', 0.0)
        
        return submission
    
    def add_rating(self, user_id: str, stars: int, review: str = "") -> ContentRating:
        """Add a rating (1-5 stars)."""
        stars = max(1, min(5, stars))  # Clamp to 1-5
        
        rating = ContentRating(
            user_id=user_id,
            stars=stars,
            timestamp=datetime.now().isoformat(),
            review=review,
        )
        self.ratings.append(rating)
        self._recalculate_average()
        return rating
    
    def _recalculate_average(self):
        """Recalculate average rating."""
        if self.ratings:
            self.average_rating = sum(r.stars for r in self.ratings) / len(self.ratings)
        else:
            self.average_rating = 0.0
    
    def bump_version(self, bump_type: str = "patch") -> str:
        """Bump version number."""
        parts = self.version.split('.')
        if len(parts) != 3:
            parts = ['1', '0', '0']
        
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        self.version_history.append(self.version)
        
        if bump_type == "major":
            self.version = f"{major + 1}.0.0"
        elif bump_type == "minor":
            self.version = f"{major}.{minor + 1}.0"
        else:  # patch
            self.version = f"{major}.{minor}.{patch + 1}"
        
        self.location.updated_at = datetime.now().isoformat()
        return self.version


# =============================================================================
# Submission Validator
# =============================================================================

class SubmissionValidator:
    """Validates content submissions for safety and quality."""
    
    # Maximum file sizes by type (bytes)
    MAX_SIZES = {
        ContentType.SCRIPT: 1024 * 100,     # 100KB
        ContentType.TILE: 1024 * 50,        # 50KB
        ContentType.GUIDE: 1024 * 500,      # 500KB
        ContentType.WORKFLOW: 1024 * 100,   # 100KB
        ContentType.TEMPLATE: 1024 * 50,    # 50KB
        ContentType.ASSET: 1024 * 1024,     # 1MB
    }
    
    # Blocked patterns (security)
    BLOCKED_PATTERNS = [
        'import os',
        'import subprocess',
        'import sys',
        '__import__',
        'eval(',
        'exec(',
        'open(',
        'file(',
        'shutil.',
    ]
    
    def validate(self, submission: ContentSubmission, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate a submission.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check file exists
        if not file_path.exists():
            issues.append("File does not exist")
            return (False, issues)
        
        # Check file size
        size = file_path.stat().st_size
        max_size = self.MAX_SIZES.get(submission.content_type, 1024 * 100)
        if size > max_size:
            issues.append(f"File too large ({size} > {max_size} bytes)")
        
        # Check file extension
        expected_ext = submission.content_type.extension
        if expected_ext and not file_path.suffix == expected_ext:
            issues.append(f"Wrong extension (expected {expected_ext})")
        
        # Check content for blocked patterns
        try:
            content = file_path.read_text(encoding='utf-8')
            for pattern in self.BLOCKED_PATTERNS:
                if pattern in content:
                    issues.append(f"Blocked pattern found: {pattern}")
        except Exception as e:
            issues.append(f"Could not read file: {e}")
        
        # Check required fields
        if not submission.title:
            issues.append("Title is required")
        if not submission.description and submission.share_status.value >= ShareStatus.SHARED_PUBLIC.value:
            issues.append("Description required for public submissions")
        if not submission.attribution:
            issues.append("Attribution is required")
        
        # Check tags for public submissions
        if submission.share_status.value >= ShareStatus.SHARED_PUBLIC.value:
            if len(submission.tags) < 1:
                issues.append("At least one tag required for public submissions")
        
        return (len(issues) == 0, issues)
    
    def calculate_quality_score(self, submission: ContentSubmission, file_path: Path) -> int:
        """
        Calculate quality score (0-100).
        
        Factors:
        - Has description (+20)
        - Has tags (+10)
        - Has category (+10)
        - Has difficulty level (+5)
        - Good file size (+10)
        - Proper formatting (+20)
        - Ratings average (+25 scaled)
        """
        score = 0
        
        # Metadata completeness
        if submission.description:
            score += 20
        if submission.tags:
            score += 10
        if submission.category:
            score += 10
        if submission.difficulty:
            score += 5
        
        # File quality
        if file_path.exists():
            size = file_path.stat().st_size
            if 100 < size < 50000:  # Good size range
                score += 10
        
        # Content formatting (basic check)
        try:
            content = file_path.read_text() if file_path.exists() else ""
            if content:
                # Has comments
                if '#' in content or '"""' in content:
                    score += 10
                # Has structure
                if content.count('\n') > 5:
                    score += 10
        except Exception:
            pass
        
        # Ratings (if any)
        if submission.ratings:
            rating_score = (submission.average_rating / 5) * 25
            score += int(rating_score)
        
        return min(100, score)


# =============================================================================
# Content Library
# =============================================================================

class ContentLibrary:
    """
    Browse and search shared content.
    
    Manages content storage and retrieval across all share levels.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize content library."""
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        
        # Storage directories
        self.submissions_dir = self.project_root / "memory" / "shared" / ".submissions"
        self.public_dir = self.project_root / "memory" / "shared" / "public"
        self.metadata_dir = self.project_root / "memory" / "shared" / "metadata"
        self.private_dir = self.project_root / "memory" / "private"
        
        # Ensure directories exist
        for d in [self.submissions_dir, self.public_dir, self.metadata_dir, self.private_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Validator
        self.validator = SubmissionValidator()
        
        # Content index (lazy loaded)
        self._index: Optional[Dict[str, ContentSubmission]] = None
    
    @property
    def index(self) -> Dict[str, ContentSubmission]:
        """Get content index (lazy loaded)."""
        if self._index is None:
            self._index = self._load_index()
        return self._index
    
    def _load_index(self) -> Dict[str, ContentSubmission]:
        """Load content index from metadata."""
        index = {}
        index_file = self.metadata_dir / "index.json"
        
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data.get('content', []):
                        submission = ContentSubmission.from_dict(item)
                        index[submission.content_id] = submission
            except Exception:
                pass
        
        return index
    
    def _save_index(self):
        """Save content index."""
        index_file = self.metadata_dir / "index.json"
        
        data = {
            'version': '1.3.2',
            'updated': datetime.now().isoformat(),
            'content': [s.to_dict() for s in self.index.values()],
        }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def create_submission(
        self,
        title: str,
        file_path: Path,
        content_type: ContentType,
        author_id: str,
        author_name: str,
        description: str = "",
        tags: List[str] = None,
        category: str = "",
        tile_code: str = "",
    ) -> ContentSubmission:
        """
        Create a new content submission.
        
        Content starts as PRIVATE and DRAFT.
        """
        content_id = secrets.token_hex(16)
        
        # Calculate file hash
        file_hash = ""
        file_size = 0
        if file_path.exists():
            file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            file_size = file_path.stat().st_size
        
        submission = ContentSubmission(
            content_id=content_id,
            title=title,
            description=description,
            content_type=content_type,
            share_status=ShareStatus.PRIVATE,
            submission_state=SubmissionState.DRAFT,
            filename=file_path.name,
            file_hash=file_hash,
            file_size=file_size,
            location=ContentLocation.now(tile_code),
            attribution=ContentAttribution(
                author_id=author_id,
                author_name=author_name,
            ),
            tags=tags or [],
            category=category,
        )
        
        # Add to index
        self.index[content_id] = submission
        self._save_index()
        
        return submission
    
    def submit_for_review(
        self,
        content_id: str,
        target_status: ShareStatus,
        group_id: str = "",
        shared_with: List[str] = None,
    ) -> Tuple[bool, str]:
        """
        Submit content for sharing/review.
        
        Args:
            content_id: Content to submit
            target_status: Desired share level
            group_id: Group ID for USER_TO_GROUP
            shared_with: User IDs for USER_TO_USER
            
        Returns:
            Tuple of (success, message)
        """
        if content_id not in self.index:
            return (False, "Content not found")
        
        submission = self.index[content_id]
        
        # Get file path
        file_path = self._get_content_path(submission)
        if not file_path or not file_path.exists():
            return (False, "Content file not found")
        
        # Validate
        is_valid, issues = self.validator.validate(submission, file_path)
        if not is_valid:
            return (False, f"Validation failed: {', '.join(issues)}")
        
        # Update submission
        submission.share_status = target_status
        submission.submission_state = SubmissionState.PENDING
        submission.group_id = group_id
        submission.shared_with = shared_with or []
        submission.location.updated_at = datetime.now().isoformat()
        
        # Copy to appropriate location
        if target_status == ShareStatus.SHARED_PUBLIC:
            dest = self.submissions_dir / f"{content_id}{submission.content_type.extension}"
        elif target_status == ShareStatus.USER_TO_GROUP:
            dest = self.public_dir / "groups" / group_id / submission.filename
            dest.parent.mkdir(parents=True, exist_ok=True)
        else:
            dest = self.public_dir / submission.content_type.directory / submission.filename
            dest.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(file_path, dest)
        except Exception as e:
            return (False, f"Failed to copy content: {e}")
        
        self._save_index()
        return (True, f"Submitted for {target_status.display_name}")
    
    def approve_submission(self, content_id: str, reviewer_notes: str = "") -> Tuple[bool, str]:
        """Approve a pending submission (Wizard only)."""
        if content_id not in self.index:
            return (False, "Content not found")
        
        submission = self.index[content_id]
        
        if submission.submission_state != SubmissionState.PENDING:
            return (False, "Content not pending review")
        
        submission.submission_state = SubmissionState.APPROVED
        submission.reviewer_notes = reviewer_notes
        submission.location.updated_at = datetime.now().isoformat()
        
        # Move to public if SHARED_PUBLIC
        if submission.share_status == ShareStatus.SHARED_PUBLIC:
            src = self.submissions_dir / f"{content_id}{submission.content_type.extension}"
            dest = self.public_dir / submission.content_type.directory / submission.filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.exists():
                shutil.move(str(src), str(dest))
        
        self._save_index()
        return (True, "Content approved")
    
    def reject_submission(self, content_id: str, reason: str) -> Tuple[bool, str]:
        """Reject a pending submission."""
        if content_id not in self.index:
            return (False, "Content not found")
        
        submission = self.index[content_id]
        submission.submission_state = SubmissionState.REJECTED
        submission.reviewer_notes = reason
        submission.location.updated_at = datetime.now().isoformat()
        
        self._save_index()
        return (True, "Content rejected")
    
    def _get_content_path(self, submission: ContentSubmission) -> Optional[Path]:
        """Get file path for content."""
        # Check private first
        path = self.private_dir / submission.content_type.directory / submission.filename
        if path.exists():
            return path
        
        # Check public
        path = self.public_dir / submission.content_type.directory / submission.filename
        if path.exists():
            return path
        
        # Check submissions
        path = self.submissions_dir / f"{submission.content_id}{submission.content_type.extension}"
        if path.exists():
            return path
        
        return None
    
    # =========================================================================
    # Search and Browse
    # =========================================================================
    
    def search(
        self,
        query: str = "",
        content_type: ContentType = None,
        share_status: ShareStatus = None,
        category: str = "",
        tags: List[str] = None,
        min_rating: float = 0.0,
    ) -> List[ContentSubmission]:
        """Search content library."""
        results = []
        
        for submission in self.index.values():
            # Filter by type
            if content_type and submission.content_type != content_type:
                continue
            
            # Filter by share status
            if share_status and submission.share_status != share_status:
                continue
            
            # Filter by category
            if category and submission.category != category:
                continue
            
            # Filter by tags
            if tags:
                if not any(t in submission.tags for t in tags):
                    continue
            
            # Filter by rating
            if min_rating > 0 and submission.average_rating < min_rating:
                continue
            
            # Filter by query (title, description)
            if query:
                query_lower = query.lower()
                if query_lower not in submission.title.lower():
                    if query_lower not in submission.description.lower():
                        continue
            
            results.append(submission)
        
        # Sort by rating, then by date
        results.sort(
            key=lambda s: (s.average_rating, s.location.updated_at),
            reverse=True
        )
        
        return results
    
    def browse(
        self,
        share_status: ShareStatus = None,
        content_type: ContentType = None,
        limit: int = 50,
    ) -> List[ContentSubmission]:
        """Browse content library."""
        return self.search(
            share_status=share_status,
            content_type=content_type,
        )[:limit]
    
    def get_submission(self, content_id: str) -> Optional[ContentSubmission]:
        """Get a specific submission."""
        return self.index.get(content_id)
    
    def rate_content(
        self,
        content_id: str,
        user_id: str,
        stars: int,
        review: str = "",
    ) -> Tuple[bool, str]:
        """Rate content (1-5 stars)."""
        if content_id not in self.index:
            return (False, "Content not found")
        
        submission = self.index[content_id]
        
        # Check if already rated by this user
        for rating in submission.ratings:
            if rating.user_id == user_id:
                return (False, "Already rated by this user")
        
        submission.add_rating(user_id, stars, review)
        self._save_index()
        
        return (True, f"Rated {stars} stars")
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_stats(self) -> Dict:
        """Get library statistics."""
        stats = {
            'total': len(self.index),
            'by_type': {},
            'by_status': {},
            'by_state': {},
            'avg_rating': 0.0,
            'rated_count': 0,
        }
        
        total_rating = 0
        rated_count = 0
        
        for submission in self.index.values():
            # By type
            type_name = submission.content_type.value
            stats['by_type'][type_name] = stats['by_type'].get(type_name, 0) + 1
            
            # By status
            status_name = submission.share_status.display_name
            stats['by_status'][status_name] = stats['by_status'].get(status_name, 0) + 1
            
            # By state
            state_name = submission.submission_state.value
            stats['by_state'][state_name] = stats['by_state'].get(state_name, 0) + 1
            
            # Ratings
            if submission.ratings:
                total_rating += submission.average_rating
                rated_count += 1
        
        if rated_count > 0:
            stats['avg_rating'] = total_rating / rated_count
            stats['rated_count'] = rated_count
        
        return stats


# =============================================================================
# Factory Functions
# =============================================================================

_content_library: Optional[ContentLibrary] = None


def get_content_library() -> ContentLibrary:
    """Get singleton content library instance."""
    global _content_library
    if _content_library is None:
        _content_library = ContentLibrary()
    return _content_library


# =============================================================================
# CLI Test
# =============================================================================

if __name__ == "__main__":
    print("Content Sharing System Test")
    print("=" * 60)
    
    library = get_content_library()
    
    # Show share statuses
    print("\n5-Tier Share Model:")
    for status in ShareStatus:
        print(f"  {status.icon} {status.value}. {status.display_name}")
        print(f"      {status.description}")
    
    # Show content types
    print("\nContent Types:")
    for ct in ContentType:
        print(f"  - {ct.value} ({ct.extension}) → {ct.directory}/")
    
    # Show stats
    stats = library.get_stats()
    print(f"\nLibrary Stats:")
    print(f"  Total content: {stats['total']}")
    print(f"  By type: {stats['by_type']}")
    print(f"  By status: {stats['by_status']}")
    
    print("\n✅ Content Sharing System working!")
