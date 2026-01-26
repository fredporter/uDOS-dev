#!/usr/bin/env python3
"""
uDOS v1.3.2 - User Profile System

Comprehensive user profile management with:
- Profile data (bio, location, skills, interests)
- Achievement/badge system
- XP/HP/Barter points integration
- Activity statistics tracking
- Privacy controls (public/private)
- Secure local storage (hashed identifiable data)

8-Role Security Architecture:
- CRYPT (1): Encryption vault
- TOMB (2): Archive operations
- DRONE (3): Automated tasks
- GHOST (4): System monitoring
- KNIGHT (5): Security operations
- IMP (6): File system manipulation
- SORCERER (8): Advanced scripting
- WIZARD (10): Full system access

Version: 1.3.2
Author: Fred Porter
Date: December 2025
"""

import json
import hashlib
import secrets
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import IntEnum, Enum
from functools import lru_cache


# =============================================================================
# Role System
# =============================================================================


class Role(IntEnum):
    """8-level role hierarchy for security and permissions."""

    GHOST = 1  # Training/demo/sandbox mode
    TOMB = 2  # Archive operations, static files/packages
    DRONE = 3  # Automated tasks, system processes
    CRYPT = 4  # Encryption vault, cryptographic operations
    KNIGHT = 5  # Security operations, threat protection
    IMP = 6  # File system manipulation, data management
    SORCERER = 8  # Advanced scripting, system configuration
    WIZARD = 10  # Full system access, administration

    @classmethod
    def from_string(cls, name: str) -> "Role":
        """Get role from string name."""
        name = name.upper()
        for role in cls:
            if role.name == name:
                return role
        return cls.DRONE  # Default role

    @property
    def display_name(self) -> str:
        """Get display name for role."""
        return self.name.title()

    @property
    def description(self) -> str:
        """Get role description."""
        descriptions = {
            Role.GHOST: "Training, demo, and sandbox mode",
            Role.TOMB: "Archive operations and static files/packages",
            Role.DRONE: "Automated tasks and system processes",
            Role.CRYPT: "Encryption vault and cryptographic operations",
            Role.KNIGHT: "Security operations and threat protection",
            Role.IMP: "File system manipulation and data management",
            Role.SORCERER: "Advanced scripting and system configuration",
            Role.WIZARD: "Full system access and administration",
        }
        return descriptions.get(self, "Unknown role")

    def can_access(self, required_level: int) -> bool:
        """Check if this role can access a given level."""
        return self.value >= required_level


# =============================================================================
# Achievement System
# =============================================================================


class AchievementCategory(Enum):
    """Categories for achievements."""

    EXPLORATION = "exploration"
    CREATION = "creation"
    SOCIAL = "social"
    KNOWLEDGE = "knowledge"
    TECHNICAL = "technical"
    SURVIVAL = "survival"
    SPECIAL = "special"


@dataclass
class Achievement:
    """Achievement definition."""

    id: str
    name: str
    description: str
    category: AchievementCategory
    icon: str  # Emoji icon
    xp_reward: int  # XP gained on unlock
    requirement: int  # Target value to unlock
    progress_key: str  # Key in user stats to track
    secret: bool = False  # Hidden until unlocked

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "icon": self.icon,
            "xp_reward": self.xp_reward,
            "requirement": self.requirement,
            "progress_key": self.progress_key,
            "secret": self.secret,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Achievement":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=AchievementCategory(data["category"]),
            icon=data["icon"],
            xp_reward=data["xp_reward"],
            requirement=data["requirement"],
            progress_key=data["progress_key"],
            secret=data.get("secret", False),
        )


# Built-in achievements
ACHIEVEMENTS = [
    # Exploration
    Achievement(
        "explorer_1",
        "First Steps",
        "Visit your first TILE location",
        AchievementCategory.EXPLORATION,
        "🗺️",
        10,
        1,
        "tiles_visited",
    ),
    Achievement(
        "explorer_10",
        "Explorer",
        "Visit 10 unique TILE locations",
        AchievementCategory.EXPLORATION,
        "🧭",
        50,
        10,
        "tiles_visited",
    ),
    Achievement(
        "explorer_50",
        "Cartographer",
        "Visit 50 unique TILE locations",
        AchievementCategory.EXPLORATION,
        "🌍",
        200,
        50,
        "tiles_visited",
    ),
    # Creation
    Achievement(
        "author_1",
        "First Script",
        "Create your first uPY script",
        AchievementCategory.CREATION,
        "📝",
        15,
        1,
        "scripts_created",
    ),
    Achievement(
        "author_5",
        "Author",
        "Create 5 scripts",
        AchievementCategory.CREATION,
        "✍️",
        75,
        5,
        "scripts_created",
    ),
    Achievement(
        "artist_1",
        "First Tile",
        "Create your first tile",
        AchievementCategory.CREATION,
        "🎨",
        15,
        1,
        "tiles_created",
    ),
    Achievement(
        "artist_10",
        "Pixel Artist",
        "Create 10 tiles",
        AchievementCategory.CREATION,
        "🖼️",
        100,
        10,
        "tiles_created",
    ),
    # Social
    Achievement(
        "networker_1",
        "First Connection",
        "Connect to a mesh device",
        AchievementCategory.SOCIAL,
        "🔗",
        20,
        1,
        "mesh_connections",
    ),
    Achievement(
        "networker_3",
        "Networker",
        "Connect to 3 mesh devices",
        AchievementCategory.SOCIAL,
        "🌐",
        75,
        3,
        "mesh_connections",
    ),
    Achievement(
        "sharer_1",
        "First Share",
        "Share content with another user",
        AchievementCategory.SOCIAL,
        "🤝",
        25,
        1,
        "content_shared",
    ),
    Achievement(
        "contributor_1",
        "Contributor",
        "Have content accepted to Public Knowledge",
        AchievementCategory.SOCIAL,
        "⭐",
        100,
        1,
        "public_contributions",
    ),
    # Knowledge
    Achievement(
        "scholar_1",
        "Student",
        "Complete your first knowledge guide",
        AchievementCategory.KNOWLEDGE,
        "📖",
        10,
        1,
        "guides_completed",
    ),
    Achievement(
        "scholar_10",
        "Scholar",
        "Complete 10 knowledge guides",
        AchievementCategory.KNOWLEDGE,
        "📚",
        100,
        10,
        "guides_completed",
    ),
    Achievement(
        "scholar_50",
        "Sage",
        "Complete 50 knowledge guides",
        AchievementCategory.KNOWLEDGE,
        "🎓",
        500,
        50,
        "guides_completed",
    ),
    # Technical
    Achievement(
        "coder_1",
        "First Hour",
        "Use uDOS for 1 hour",
        AchievementCategory.TECHNICAL,
        "⌨️",
        10,
        1,
        "hours_used",
    ),
    Achievement(
        "coder_10",
        "Dedicated",
        "Use uDOS for 10 hours",
        AchievementCategory.TECHNICAL,
        "💻",
        50,
        10,
        "hours_used",
    ),
    Achievement(
        "coder_100",
        "Power User",
        "Use uDOS for 100 hours",
        AchievementCategory.TECHNICAL,
        "🖥️",
        500,
        100,
        "hours_used",
    ),
    Achievement(
        "commands_100",
        "Command Runner",
        "Execute 100 commands",
        AchievementCategory.TECHNICAL,
        "▶️",
        25,
        100,
        "commands_run",
    ),
    Achievement(
        "commands_1000",
        "Terminal Master",
        "Execute 1000 commands",
        AchievementCategory.TECHNICAL,
        "⚡",
        150,
        1000,
        "commands_run",
    ),
    # Survival
    Achievement(
        "survivor_water",
        "Hydration Expert",
        "Complete all water guides",
        AchievementCategory.SURVIVAL,
        "💧",
        75,
        1,
        "water_guides_complete",
    ),
    Achievement(
        "survivor_fire",
        "Fire Starter",
        "Complete all fire guides",
        AchievementCategory.SURVIVAL,
        "🔥",
        75,
        1,
        "fire_guides_complete",
    ),
    Achievement(
        "survivor_shelter",
        "Shelter Builder",
        "Complete all shelter guides",
        AchievementCategory.SURVIVAL,
        "🏠",
        75,
        1,
        "shelter_guides_complete",
    ),
    # Special (secret)
    Achievement(
        "easter_egg",
        "Curious Mind",
        "Discover a hidden feature",
        AchievementCategory.SPECIAL,
        "🥚",
        50,
        1,
        "easter_eggs_found",
        secret=True,
    ),
    Achievement(
        "wizard_mode",
        "Ascended",
        "Reach Wizard role",
        AchievementCategory.SPECIAL,
        "🧙",
        1000,
        10,
        "max_role_level",
        secret=True,
    ),
]


@dataclass
class Badge:
    """User badge (unlocked achievement with timestamp)."""

    achievement_id: str
    unlocked_at: str  # ISO timestamp
    notification_shown: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "achievement_id": self.achievement_id,
            "unlocked_at": self.unlocked_at,
            "notification_shown": self.notification_shown,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Badge":
        """Create from dictionary."""
        return cls(
            achievement_id=data["achievement_id"],
            unlocked_at=data["unlocked_at"],
            notification_shown=data.get("notification_shown", False),
        )


# =============================================================================
# User Profile
# =============================================================================


@dataclass
class UserProfile:
    """
    User profile with secure local storage.

    Sensitive data (identifiable info) is hashed and stored separately.
    """

    # Identity (hashed for privacy)
    user_id: str  # Unique identifier (generated)
    username_hash: str  # Hashed username for privacy

    # Public profile info
    display_name: str = "Anonymous"
    bio: str = ""
    location_tile: str = ""  # TILE code (e.g., "AA340")
    avatar_icon: str = "👤"

    # Skills and interests
    skills: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)

    # Role and permissions
    role: Role = field(default=Role.DRONE)

    # XP/HP/Barter System
    xp: int = 0  # Experience points
    xp_level: int = 1  # Level (derived from XP)
    hp: int = 100  # Health points
    hp_max: int = 100  # Max health
    barter_points: int = 0  # Barter/trade points

    # Statistics
    stats: Dict[str, int] = field(default_factory=dict)

    # Badges/achievements
    badges: List[Badge] = field(default_factory=list)

    # Privacy settings
    is_public: bool = False  # Public profile visibility
    show_location: bool = False  # Show TILE location
    show_stats: bool = True  # Show activity stats

    # Timestamps
    created_at: str = ""
    last_active: str = ""
    total_time_seconds: int = 0

    def __post_init__(self):
        """Initialize timestamps and stats."""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.last_active:
            self.last_active = now
        if not self.stats:
            self.stats = self._default_stats()

    @staticmethod
    def _default_stats() -> Dict[str, int]:
        """Default statistics dictionary."""
        return {
            "commands_run": 0,
            "tiles_visited": 0,
            "scripts_created": 0,
            "scripts_run": 0,
            "tiles_created": 0,
            "guides_completed": 0,
            "mesh_connections": 0,
            "content_shared": 0,
            "public_contributions": 0,
            "hours_used": 0,
            "water_guides_complete": 0,
            "fire_guides_complete": 0,
            "shelter_guides_complete": 0,
            "easter_eggs_found": 0,
            "max_role_level": 3,  # Default DRONE
            "ratings_given": 0,
            "reviews_written": 0,
        }

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "username_hash": self.username_hash,
            "display_name": self.display_name,
            "bio": self.bio,
            "location_tile": self.location_tile,
            "avatar_icon": self.avatar_icon,
            "skills": self.skills,
            "interests": self.interests,
            "role": self.role.value,
            "xp": self.xp,
            "xp_level": self.xp_level,
            "hp": self.hp,
            "hp_max": self.hp_max,
            "barter_points": self.barter_points,
            "stats": self.stats,
            "badges": [b.to_dict() for b in self.badges],
            "is_public": self.is_public,
            "show_location": self.show_location,
            "show_stats": self.show_stats,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "total_time_seconds": self.total_time_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "UserProfile":
        """Create from dictionary."""
        profile = cls(
            user_id=data["user_id"],
            username_hash=data["username_hash"],
            display_name=data.get("display_name", "Anonymous"),
            bio=data.get("bio", ""),
            location_tile=data.get("location_tile", ""),
            avatar_icon=data.get("avatar_icon", "👤"),
            skills=data.get("skills", []),
            interests=data.get("interests", []),
            role=Role(data.get("role", 3)),
            xp=data.get("xp", 0),
            xp_level=data.get("xp_level", 1),
            hp=data.get("hp", 100),
            hp_max=data.get("hp_max", 100),
            barter_points=data.get("barter_points", 0),
            stats=data.get("stats", {}),
            is_public=data.get("is_public", False),
            show_location=data.get("show_location", False),
            show_stats=data.get("show_stats", True),
            created_at=data.get("created_at", ""),
            last_active=data.get("last_active", ""),
            total_time_seconds=data.get("total_time_seconds", 0),
        )

        # Load badges
        profile.badges = [Badge.from_dict(b) for b in data.get("badges", [])]

        # Ensure all stats exist
        for key in profile._default_stats():
            if key not in profile.stats:
                profile.stats[key] = 0

        return profile

    def add_xp(self, amount: int) -> Tuple[int, bool]:
        """
        Add XP and check for level up.

        Returns:
            Tuple of (new_xp, leveled_up)
        """
        self.xp += amount
        old_level = self.xp_level
        self.xp_level = self._calculate_level()
        return (self.xp, self.xp_level > old_level)

    def _calculate_level(self) -> int:
        """Calculate level from XP (logarithmic scaling)."""
        # Level formula: level = 1 + floor(sqrt(xp / 100))
        import math

        return 1 + int(math.sqrt(self.xp / 100))

    def xp_for_next_level(self) -> int:
        """XP required for next level."""
        next_level = self.xp_level + 1
        return (next_level - 1) ** 2 * 100

    def xp_progress(self) -> float:
        """Progress to next level (0.0 - 1.0)."""
        current_threshold = (self.xp_level - 1) ** 2 * 100
        next_threshold = self.xp_level**2 * 100
        progress = (self.xp - current_threshold) / (next_threshold - current_threshold)
        return min(1.0, max(0.0, progress))

    def heal(self, amount: int) -> int:
        """Heal HP, capped at max."""
        self.hp = min(self.hp_max, self.hp + amount)
        return self.hp

    def damage(self, amount: int) -> int:
        """Take damage, minimum 0."""
        self.hp = max(0, self.hp - amount)
        return self.hp

    def earn_barter(self, amount: int, reason: str = "") -> int:
        """Earn barter points from activities."""
        self.barter_points += amount
        return self.barter_points

    def spend_barter(self, amount: int) -> bool:
        """Spend barter points if available."""
        if self.barter_points >= amount:
            self.barter_points -= amount
            return True
        return False

    def increment_stat(self, stat_key: str, amount: int = 1) -> int:
        """Increment a statistic."""
        if stat_key not in self.stats:
            self.stats[stat_key] = 0
        self.stats[stat_key] += amount
        return self.stats[stat_key]

    def get_stat(self, stat_key: str) -> int:
        """Get a statistic value."""
        return self.stats.get(stat_key, 0)

    def has_badge(self, achievement_id: str) -> bool:
        """Check if user has a specific badge."""
        return any(b.achievement_id == achievement_id for b in self.badges)

    def award_badge(self, achievement: Achievement) -> Optional[Badge]:
        """Award a badge if not already earned."""
        if self.has_badge(achievement.id):
            return None

        badge = Badge(
            achievement_id=achievement.id, unlocked_at=datetime.now().isoformat()
        )
        self.badges.append(badge)
        self.add_xp(achievement.xp_reward)
        return badge

    def update_activity(self):
        """Update last active timestamp."""
        self.last_active = datetime.now().isoformat()


# =============================================================================
# Profile Manager
# =============================================================================


class ProfileManager:
    """
    Manages user profiles with secure local storage.

    Separates sensitive data into encrypted files.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize profile manager."""
        self.project_root = project_root or Path(__file__).resolve().parents[2]

        # Profile storage
        self.profiles_dir = self.project_root / "memory" / "bank" / "user"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        # Secure storage (separate file)
        self.secure_dir = self.profiles_dir / ".secure"
        self.secure_dir.mkdir(parents=True, exist_ok=True)

        # Current profile
        self._current_profile: Optional[UserProfile] = None

        # Achievement registry
        self._achievements = {a.id: a for a in ACHIEVEMENTS}

        # Session tracking
        self._session_start = time.time()

    @property
    def current_profile(self) -> Optional[UserProfile]:
        """Get current loaded profile."""
        return self._current_profile

    def create_profile(self, username: str, display_name: str = None) -> UserProfile:
        """
        Create a new user profile.

        Args:
            username: Username (will be hashed)
            display_name: Optional display name

        Returns:
            New UserProfile
        """
        # Generate unique ID
        user_id = secrets.token_hex(16)

        # Hash username for privacy
        username_hash = self._hash_string(username)

        profile = UserProfile(
            user_id=user_id,
            username_hash=username_hash,
            display_name=display_name or username,
        )

        self._current_profile = profile
        self.save_profile(profile)

        return profile

    def load_profile(self, user_id: str = None) -> Optional[UserProfile]:
        """
        Load a user profile.

        Args:
            user_id: User ID to load, or None for default profile

        Returns:
            UserProfile or None
        """
        if user_id is None:
            # Load default profile
            profile_file = self.profiles_dir / "profile.json"
        else:
            profile_file = self.profiles_dir / f"profile_{user_id}.json"

        if not profile_file.exists():
            return None

        try:
            with open(profile_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                profile = UserProfile.from_dict(data)
                self._current_profile = profile
                return profile
        except Exception:
            return None

    def save_profile(self, profile: UserProfile = None) -> bool:
        """
        Save user profile.

        Args:
            profile: Profile to save, or current profile

        Returns:
            Success flag
        """
        profile = profile or self._current_profile
        if profile is None:
            return False

        # Update session time
        session_time = int(time.time() - self._session_start)
        profile.total_time_seconds += session_time
        profile.stats["hours_used"] = profile.total_time_seconds // 3600
        self._session_start = time.time()

        # Update activity
        profile.update_activity()

        # Save main profile
        profile_file = self.profiles_dir / "profile.json"
        try:
            with open(profile_file, "w", encoding="utf-8") as f:
                json.dump(profile.to_dict(), f, indent=2)
            return True
        except Exception:
            return False

    def load_or_create_default(self) -> UserProfile:
        """Load default profile or create one."""
        profile = self.load_profile()
        if profile is None:
            profile = self.create_profile("user", "Survivor")
        return profile

    def _hash_string(self, value: str) -> str:
        """Hash a string for privacy."""
        return hashlib.sha256(value.encode()).hexdigest()[:32]

    # =========================================================================
    # Statistics & Achievements
    # =========================================================================

    def track_command(self, command: str):
        """Track a command execution."""
        if self._current_profile:
            self._current_profile.increment_stat("commands_run")
            self._check_achievements()

    def track_tile_visit(self, tile_code: str):
        """Track visiting a TILE location."""
        if self._current_profile:
            self._current_profile.increment_stat("tiles_visited")
            self._check_achievements()

    def track_script_created(self):
        """Track creating a script."""
        if self._current_profile:
            self._current_profile.increment_stat("scripts_created")
            self._current_profile.add_xp(15)
            self._current_profile.earn_barter(5, "script_created")
            self._check_achievements()

    def track_tile_created(self):
        """Track creating a tile."""
        if self._current_profile:
            self._current_profile.increment_stat("tiles_created")
            self._current_profile.add_xp(10)
            self._current_profile.earn_barter(3, "tile_created")
            self._check_achievements()

    def track_guide_completed(self, category: str = None):
        """Track completing a knowledge guide."""
        if self._current_profile:
            self._current_profile.increment_stat("guides_completed")
            self._current_profile.add_xp(25)

            # Track category completion
            if category:
                key = f"{category}_guides_complete"
                if key in self._current_profile.stats:
                    self._current_profile.increment_stat(key)

            self._check_achievements()

    def track_mesh_connection(self):
        """Track a mesh device connection."""
        if self._current_profile:
            self._current_profile.increment_stat("mesh_connections")
            self._current_profile.add_xp(20)
            self._check_achievements()

    def track_content_shared(self, share_type: str = "user"):
        """Track sharing content."""
        if self._current_profile:
            self._current_profile.increment_stat("content_shared")
            self._current_profile.add_xp(30)
            self._current_profile.earn_barter(10, "content_shared")

            if share_type == "public":
                self._current_profile.increment_stat("public_contributions")
                self._current_profile.add_xp(100)
                self._current_profile.earn_barter(50, "public_contribution")

            self._check_achievements()

    def _check_achievements(self) -> List[Badge]:
        """Check and award any earned achievements."""
        if not self._current_profile:
            return []

        new_badges = []
        profile = self._current_profile

        for achievement in ACHIEVEMENTS:
            if profile.has_badge(achievement.id):
                continue

            # Check progress
            progress = profile.get_stat(achievement.progress_key)
            if progress >= achievement.requirement:
                badge = profile.award_badge(achievement)
                if badge:
                    new_badges.append(badge)

        return new_badges

    def get_achievement_progress(self) -> List[Dict]:
        """Get progress on all achievements."""
        if not self._current_profile:
            return []

        progress = []
        profile = self._current_profile

        for achievement in ACHIEVEMENTS:
            # Skip secret achievements that aren't unlocked
            if achievement.secret and not profile.has_badge(achievement.id):
                continue

            current = profile.get_stat(achievement.progress_key)
            unlocked = profile.has_badge(achievement.id)

            progress.append(
                {
                    "achievement": achievement,
                    "current": current,
                    "target": achievement.requirement,
                    "percent": min(100, int(current / achievement.requirement * 100)),
                    "unlocked": unlocked,
                }
            )

        return progress

    def get_recent_badges(self, count: int = 5) -> List[Tuple[Badge, Achievement]]:
        """Get most recently unlocked badges."""
        if not self._current_profile:
            return []

        sorted_badges = sorted(
            self._current_profile.badges, key=lambda b: b.unlocked_at, reverse=True
        )[:count]

        result = []
        for badge in sorted_badges:
            achievement = self._achievements.get(badge.achievement_id)
            if achievement:
                result.append((badge, achievement))

        return result

    # =========================================================================
    # Role Management
    # =========================================================================

    def set_role(self, role: Role) -> bool:
        """Set user role (requires appropriate permissions)."""
        if not self._current_profile:
            return False

        self._current_profile.role = role
        self._current_profile.stats["max_role_level"] = max(
            self._current_profile.stats.get("max_role_level", 0), role.value
        )
        self._check_achievements()
        return True

    def can_access_level(self, required_level: int) -> bool:
        """Check if current user can access a level."""
        if not self._current_profile:
            return False
        return self._current_profile.role.can_access(required_level)

    def get_available_roles(self) -> List[Role]:
        """Get roles available to current user."""
        if not self._current_profile:
            return [Role.DRONE]

        max_level = self._current_profile.role.value
        return [r for r in Role if r.value <= max_level]

    # =========================================================================
    # Profile Display
    # =========================================================================

    def format_profile(self, include_private: bool = False) -> str:
        """Format profile for display."""
        profile = self._current_profile
        if not profile:
            return "No profile loaded"

        lines = []
        lines.append(
            "╔════════════════════════════════════════════════════════════════╗"
        )
        lines.append(f"║  {profile.avatar_icon} {profile.display_name:<55} ║")
        lines.append(
            "╚════════════════════════════════════════════════════════════════╝"
        )
        lines.append("")

        # Basic info
        lines.append(
            f"  Role: {profile.role.display_name} (Level {profile.role.value})"
        )
        if profile.bio:
            lines.append(f"  Bio: {profile.bio[:50]}...")
        if profile.location_tile and (include_private or profile.show_location):
            lines.append(f"  Location: {profile.location_tile}")

        lines.append("")

        # XP/HP/Barter
        lines.append("  ┌─ Status ────────────────────────────────────────┐")
        xp_bar = self._progress_bar(profile.xp_progress(), 20)
        lines.append(
            f"  │ XP: {profile.xp:,} (Level {profile.xp_level}) {xp_bar}         │"
        )
        hp_pct = profile.hp / profile.hp_max
        hp_bar = self._progress_bar(hp_pct, 20)
        lines.append(f"  │ HP: {profile.hp}/{profile.hp_max} {hp_bar}              │")
        lines.append(
            f"  │ Barter Points: {profile.barter_points:,}                       │"
        )
        lines.append("  └──────────────────────────────────────────────────┘")
        lines.append("")

        # Statistics
        if include_private or profile.show_stats:
            lines.append("  ┌─ Statistics ─────────────────────────────────────┐")
            lines.append(
                f"  │ Commands Run: {profile.stats.get('commands_run', 0):,}                          │"
            )
            lines.append(
                f"  │ Tiles Visited: {profile.stats.get('tiles_visited', 0):,}                         │"
            )
            lines.append(
                f"  │ Scripts Created: {profile.stats.get('scripts_created', 0):,}                       │"
            )
            lines.append(
                f"  │ Guides Completed: {profile.stats.get('guides_completed', 0):,}                      │"
            )
            lines.append(
                f"  │ Time Used: {profile.total_time_seconds // 3600}h {(profile.total_time_seconds % 3600) // 60}m                          │"
            )
            lines.append("  └──────────────────────────────────────────────────┘")
            lines.append("")

        # Recent badges
        recent = self.get_recent_badges(3)
        if recent:
            lines.append("  Recent Achievements:")
            for badge, achievement in recent:
                lines.append(f"    {achievement.icon} {achievement.name}")

        # Badge count
        total_badges = len(profile.badges)
        total_achievements = len([a for a in ACHIEVEMENTS if not a.secret])
        lines.append("")
        lines.append(f"  Badges: {total_badges}/{total_achievements}")

        return "\n".join(lines)

    def _progress_bar(self, percent: float, width: int = 20) -> str:
        """Create a progress bar."""
        filled = int(percent * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"

    def format_achievements(self) -> str:
        """Format achievements list."""
        progress = self.get_achievement_progress()

        lines = []
        lines.append(
            "╔════════════════════════════════════════════════════════════════╗"
        )
        lines.append(
            "║  🏆 Achievements                                               ║"
        )
        lines.append(
            "╚════════════════════════════════════════════════════════════════╝"
        )
        lines.append("")

        # Group by category
        by_category = {}
        for p in progress:
            cat = p["achievement"].category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(p)

        for category, items in sorted(by_category.items()):
            lines.append(f"  {category.upper()}")
            lines.append("  " + "─" * 50)

            for item in items:
                a = item["achievement"]
                check = "✅" if item["unlocked"] else "⬜"
                pct = f"({item['percent']}%)" if not item["unlocked"] else ""
                lines.append(f"  {check} {a.icon} {a.name:<25} {pct}")
                lines.append(f"       {a.description}")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# Factory Functions
# =============================================================================

_profile_manager: Optional[ProfileManager] = None


def get_profile_manager() -> ProfileManager:
    """Get singleton profile manager instance."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager


# =============================================================================
# CLI Test
# =============================================================================

if __name__ == "__main__":
    print("User Profile System Test")
    print("=" * 60)

    manager = get_profile_manager()

    # Create or load profile
    profile = manager.load_or_create_default()

    print(f"\nLoaded profile: {profile.display_name}")
    print(f"User ID: {profile.user_id[:16]}...")
    print(f"Role: {profile.role.display_name}")
    print(f"XP: {profile.xp} (Level {profile.xp_level})")
    print(f"HP: {profile.hp}/{profile.hp_max}")
    print(f"Barter: {profile.barter_points}")

    # Track some activity
    manager.track_command("STATUS")
    manager.track_command("HELP")
    manager.track_tile_visit("AA340")

    print("\n" + manager.format_profile(include_private=True))

    # Save
    manager.save_profile()
    print("\n✅ Profile saved successfully!")

    print("\n" + "=" * 60)
    print("Role System:")
    for role in Role:
        print(f"  {role.value:2d}. {role.display_name:<12} - {role.description}")
