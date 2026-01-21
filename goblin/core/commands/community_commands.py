"""
Community Command Handler - v1.3.2
Tier 3: Community group knowledge + Content Sharing

Commands (Group Management):
  COMMUNITY CREATE <name> [description]
  COMMUNITY JOIN <name>
  COMMUNITY LEAVE <name>
  COMMUNITY LIST
  COMMUNITY INFO <name>
  COMMUNITY ADD <group> <title> [category]
  COMMUNITY BROWSE <group> [category]
  COMMUNITY MEMBERS <group>
  COMMUNITY STATUS

Commands (Content Sharing - v1.3.2):
  COMMUNITY PROFILE              View your profile
  COMMUNITY MY                   Your profile & submissions
  COMMUNITY ACHIEVEMENTS         View achievements & badges
  COMMUNITY SUBMIT <type> <file> Submit content for sharing
  COMMUNITY SEARCH <query>       Search community content
  COMMUNITY DOWNLOAD <id>        Download shared content
  COMMUNITY RATE <id> <stars>    Rate content (1-5 stars)
  COMMUNITY REVIEW <id> "<text>" Write a review
  COMMUNITY LEADERBOARD [cat]    Show top contributors

Author: uDOS Development Team
Version: 1.3.2
"""

from pathlib import Path
from typing import List, Optional, Any
from dev.goblin.core.services.community_service import CommunityService, GroupRole
from dev.goblin.core.services.memory_manager import MemoryManager, MemoryTier


class CommunityCommandHandler:
    """Handler for COMMUNITY (Tier 3) commands + Content Sharing"""

    def __init__(self):
        """Initialize CommunityCommandHandler"""
        self.memory_manager = MemoryManager()
        self.community_service = CommunityService()
        self.groups_path = self.memory_manager.get_tier_path(MemoryTier.GROUPS)
        
        # Lazy-loaded services (v1.3.2)
        self._profile_manager = None
        self._content_library = None
        
        # Get user from config or use placeholder
        try:
            from dev.goblin.core.config import Config
            config = Config()
            self.current_user = config.get('current_user', 'owner@localhost')
        except:
            self.current_user = "owner@localhost"
    
    @property
    def profile_manager(self):
        """Lazy load profile manager (v1.3.2)."""
        if self._profile_manager is None:
            try:
                from dev.goblin.core.services.user_profile import get_profile_manager
                self._profile_manager = get_profile_manager()
            except ImportError:
                self._profile_manager = None
        return self._profile_manager
    
    @property
    def content_library(self):
        """Lazy load content library (v1.3.2)."""
        if self._content_library is None:
            try:
                from dev.goblin.core.services.content_sharing import get_content_library
                self._content_library = get_content_library()
            except ImportError:
                self._content_library = None
        return self._content_library

    def handle(self, command: str, args: List[str]) -> str:
        """
        Route COMMUNITY commands to appropriate handlers

        Args:
            command: Subcommand (CREATE, JOIN, etc.)
            args: Command arguments

        Returns:
            Formatted response string
        """
        if not command or command.upper() == "HELP":
            return self._help()

        command = command.upper()

        # Group management handlers (original)
        handlers = {
            'CREATE': self._create,
            'NEW': self._create,       # Alias
            'JOIN': self._join,
            'LEAVE': self._leave,
            'QUIT': self._leave,       # Alias
            'LIST': self._list,
            'LS': self._list,          # Alias
            'INFO': self._info,
            'SHOW': self._info,        # Alias
            'ADD': self._add,
            'CONTRIBUTE': self._add,   # Alias
            'BROWSE': self._browse,
            'VIEW': self._browse,      # Alias
            'MEMBERS': self._members,
            'STATUS': self._status,
            'STATS': self._status,     # Alias
            
            # Content sharing handlers (v1.3.2)
            'PROFILE': self._profile,
            'MY': self._my,
            'ACHIEVEMENTS': self._achievements,
            'SUBMIT': self._submit,
            'SEARCH': self._search,
            'DOWNLOAD': self._download,
            'RATE': self._rate,
            'REVIEW': self._review,
            'LEADERBOARD': self._leaderboard,
        }

        handler = handlers.get(command)
        if handler:
            return handler(args)
        else:
            return f"❌ Unknown COMMUNITY command: {command}\n\nType 'COMMUNITY HELP' for usage."

    def _help(self) -> str:
        """Display COMMUNITY command help"""
        return """
👥 COMMUNITY - Community Features (v1.3.2)

═══════════════════════════════════════════════════════════════
GROUP COMMANDS (Tier 3):
═══════════════════════════════════════════════════════════════
  COMMUNITY CREATE <name> [desc]     Create new group
  COMMUNITY JOIN <name>              Join a group
  COMMUNITY LEAVE <name>             Leave a group
  COMMUNITY LIST                     List all groups
  COMMUNITY INFO <name>              Group details
  COMMUNITY ADD <group> <title>      Contribute knowledge
  COMMUNITY BROWSE <group> [cat]     Browse group knowledge
  COMMUNITY MEMBERS <group>          List group members

═══════════════════════════════════════════════════════════════
PROFILE COMMANDS (v1.3.2):
═══════════════════════════════════════════════════════════════
  COMMUNITY PROFILE                  View your profile
  COMMUNITY MY                       Your profile & submissions
  COMMUNITY ACHIEVEMENTS             View achievements & badges
  COMMUNITY STATUS                   Community statistics

═══════════════════════════════════════════════════════════════
CONTENT SHARING (v1.3.2):
═══════════════════════════════════════════════════════════════
  COMMUNITY SUBMIT <type> <file>     Submit content
  COMMUNITY SEARCH <query>           Search community content
  COMMUNITY DOWNLOAD <id>            Download shared content
  COMMUNITY RATE <id> <stars>        Rate content (1-5)
  COMMUNITY REVIEW <id> "<text>"     Write a review
  COMMUNITY LEADERBOARD [category]   Show top contributors

SHARE LEVELS (5-Tier Model):
  🔒 PRIVATE        Never shared (default)
  🤝 USER-TO-USER   Direct sharing (IRL proximity)
  👥 USER-TO-GROUP  Group sharing (topic-focused)
  📤 SHARED PUBLIC  Submitted for review
  📚 PUBLIC         Vetted Public Knowledge

CONTENT TYPES:
  script     .upy automation scripts
  tile       .json map tiles
  guide      .md knowledge guides
  workflow   .upy workflow scripts

USER ROLES (8-Level Security):
  🪦 Crypt (1)     New/untrusted user
  ⚰️ Tomb (2)      Registered, minimal access
  🤖 Drone (3)     Basic verified user
  👻 Ghost (4)     Regular member (default new)
  ⚔️ Knight (5)    Trusted contributor
  😈 Imp (6)       Moderator/helper
  🧙 Sorcerer (8)  Admin/curator
  🪄 Wizard (10)   System owner

EXAMPLES:
  # Submit content
  COMMUNITY SUBMIT script water.upy "Water Filter"
  
  # View profile
  COMMUNITY PROFILE
  
  # Browse and rate
  COMMUNITY SEARCH fire starting
  COMMUNITY RATE abc123 5
  
  # Groups
  COMMUNITY CREATE local-gardeners "Community gardening"
  COMMUNITY JOIN local-gardeners
"""

    def _create(self, args: List[str]) -> str:
        """Create a new community group"""
        if not args:
            return "❌ Usage: COMMUNITY CREATE <name> [description]"

        group_name = args[0]
        description = " ".join(args[1:]) if len(args) > 1 else ""

        # Create group
        success = self.community_service.create_group(
            group_name, self.current_user, description
        )

        if not success:
            return f"❌ Group already exists: {group_name}"

        return f"""
✅ Community group created!

👥 Group: {group_name}
📝 Description: {description if description else "(none)"}
👑 Founder: {self.current_user}
📅 Created: {self.community_service.groups[group_name]['created'][:10]}

You are now the founder of this group.
Use 'COMMUNITY ADD {group_name} <title>' to contribute knowledge.
"""

    def _join(self, args: List[str]) -> str:
        """Join a community group"""
        if not args:
            return "❌ Usage: COMMUNITY JOIN <name>"

        group_name = args[0]

        # Join group
        success = self.community_service.join_group(group_name, self.current_user)

        if not success:
            if group_name not in self.community_service.groups:
                return f"❌ Group not found: {group_name}"
            else:
                return f"ℹ️  You are already a member of {group_name}"

        group_info = self.community_service.get_group_info(group_name)

        return f"""
✅ Joined community group!

👥 Group: {group_name}
📝 Description: {group_info['description']}
👤 Members: {group_info['stats']['total_members']}
📚 Contributions: {group_info['stats']['total_contributions']}

You can now contribute and access group knowledge.
Use 'COMMUNITY BROWSE {group_name}' to explore.
"""

    def _leave(self, args: List[str]) -> str:
        """Leave a community group"""
        if not args:
            return "❌ Usage: COMMUNITY LEAVE <name>"

        group_name = args[0]

        # Leave group
        success = self.community_service.leave_group(group_name, self.current_user)

        if not success:
            if group_name not in self.community_service.groups:
                return f"❌ Group not found: {group_name}"
            elif self.current_user not in self.community_service.groups[group_name]['members']:
                return f"ℹ️  You are not a member of {group_name}"
            else:
                return f"❌ Founders cannot leave their own groups"

        return f"""
✅ Left community group

👥 Group: {group_name}

You are no longer a member of this group.
"""

    def _list(self, args: List[str]) -> str:
        """List all groups or user's groups"""
        show_all = len(args) > 0 and args[0].upper() == "ALL"

        groups = self.community_service.list_groups(
            None if show_all else self.current_user
        )

        output = ["👥 Community Groups"]
        if not show_all:
            output.append(f"📊 Your groups")
        output.append("=" * 60)

        if not groups:
            output.append("\n📭 No groups found")
            if not show_all:
                output.append("\nUse 'COMMUNITY LIST ALL' to see all groups")
        else:
            output.append(f"\n📊 {len(groups)} group(s)\n")

            for group in groups:
                icon = "👑" if group.get('role') == 'founder' else "👤" if group.get('is_member') else "👥"

                output.append(f"{icon} {group['name']}")
                if group['description']:
                    output.append(f"   {group['description']}")
                output.append(f"   Members: {group['members']} | "
                            f"Contributions: {group['contributions']}")

                if group.get('is_member'):
                    role = group.get('role', 'member').upper()
                    output.append(f"   Your role: {role}")

                output.append("")

        output.append("=" * 60)
        output.append("\nℹ️  Use 'COMMUNITY INFO <name>' for details")

        return "\n".join(output)

    def _info(self, args: List[str]) -> str:
        """Show group information"""
        if not args:
            return "❌ Usage: COMMUNITY INFO <name>"

        group_name = args[0]
        group_info = self.community_service.get_group_info(group_name)

        if not group_info:
            return f"❌ Group not found: {group_name}"

        output = [f"👥 {group_name}"]
        output.append("=" * 60)

        # Basic info
        output.append(f"\n📝 Description: {group_info['description'] if group_info['description'] else '(none)'}")
        output.append(f"👑 Founder: {group_info['founder']}")
        output.append(f"📅 Created: {group_info['created'][:10]}")

        # Statistics
        stats = group_info['stats']
        output.append(f"\n📊 Statistics:")
        output.append(f"  Members: {stats['total_members']}")
        output.append(f"  Contributions: {stats['total_contributions']}")
        output.append(f"  Votes: {stats['total_votes']}")

        # Your membership
        if self.current_user in group_info['members']:
            member_data = group_info['members'][self.current_user]
            output.append(f"\n👤 Your Membership:")
            output.append(f"  Role: {member_data['role'].upper()}")
            output.append(f"  Joined: {member_data['joined'][:10]}")
            output.append(f"  Contributions: {member_data['contributions']}")
            output.append(f"  Reputation: {member_data['reputation']}")
        else:
            output.append(f"\nℹ️  You are not a member of this group")
            output.append(f"   Use 'COMMUNITY JOIN {group_name}' to join")

        output.append("\n" + "=" * 60)

        return "\n".join(output)

    def _add(self, args: List[str]) -> str:
        """Add contribution to group"""
        if len(args) < 2:
            return "❌ Usage: COMMUNITY ADD <group> <title> [category]"

        group_name = args[0]
        title = args[1]
        category = args[2] if len(args) > 2 else "knowledge"

        # Check membership
        if group_name not in self.community_service.groups:
            return f"❌ Group not found: {group_name}"

        if self.current_user not in self.community_service.groups[group_name]['members']:
            return f"❌ You must be a member of {group_name} to contribute"

        # Get content (in real implementation, this would open editor)
        print(f"\n📝 Enter contribution content (end with empty line):")
        lines = []
        while True:
            try:
                line = input()
                if not line:
                    break
                lines.append(line)
            except EOFError:
                break

        content = "\n".join(lines) if lines else "Contribution content goes here..."

        # Add contribution
        success = self.community_service.add_contribution(
            group_name, self.current_user, title, content, category
        )

        if not success:
            return "❌ Failed to add contribution"

        return f"""
✅ Contribution added!

👥 Group: {group_name}
📄 Title: {title}
📁 Category: {category}
💰 Reputation: +10 points

Your contribution is now available to all group members.
"""

    def _browse(self, args: List[str]) -> str:
        """Browse group knowledge"""
        if not args:
            return "❌ Usage: COMMUNITY BROWSE <group> [category]"

        group_name = args[0]
        category = args[1] if len(args) > 1 else "knowledge"

        # Check membership
        if group_name not in self.community_service.groups:
            return f"❌ Group not found: {group_name}"

        if self.current_user not in self.community_service.groups[group_name]['members']:
            return f"❌ You must be a member of {group_name} to browse"

        # Browse knowledge
        items = self.community_service.browse_group_knowledge(group_name, category)

        output = [f"📚 {group_name} - {category}"]
        output.append("=" * 60)

        if not items:
            output.append(f"\n📭 No {category} items yet")
            output.append(f"\nUse 'COMMUNITY ADD {group_name} <title> {category}' to contribute")
        else:
            output.append(f"\n📊 {len(items)} item(s)\n")

            for item in items:
                size_kb = item['size'] / 1024
                output.append(f"📄 {item['title']}")
                output.append(f"   Size: {size_kb:.1f} KB | Modified: {item['modified'][:10]}")

        output.append("\n" + "=" * 60)

        return "\n".join(output)

    def _members(self, args: List[str]) -> str:
        """List group members"""
        if not args:
            return "❌ Usage: COMMUNITY MEMBERS <group>"

        group_name = args[0]
        group_info = self.community_service.get_group_info(group_name)

        if not group_info:
            return f"❌ Group not found: {group_name}"

        output = [f"👥 {group_name} - Members"]
        output.append("=" * 60)

        members = group_info['members']
        output.append(f"\n📊 {len(members)} member(s)\n")

        # Sort by role
        role_order = {'founder': 0, 'admin': 1, 'moderator': 2, 'member': 3}
        sorted_members = sorted(members.items(),
                               key=lambda x: role_order.get(x[1]['role'], 4))

        for user, data in sorted_members:
            role_icons = {
                'founder': '👑',
                'admin': '⚡',
                'moderator': '🛡️',
                'member': '👤'
            }
            icon = role_icons.get(data['role'], '👤')

            output.append(f"{icon} {user} ({data['role'].upper()})")
            output.append(f"   Joined: {data['joined'][:10]} | "
                        f"Contributions: {data['contributions']} | "
                        f"Reputation: {data['reputation']}")

        output.append("\n" + "=" * 60)

        return "\n".join(output)

    def _status(self, args: List[str]) -> str:
        """Show community statistics"""
        stats = self.community_service.get_stats()
        tier_stats = self.memory_manager.get_tier_stats(MemoryTier.GROUPS)

        # User reputation
        user_rep = self.community_service.get_user_reputation(self.current_user)

        output = ["👥 Community Status"]
        output.append("=" * 60)

        # Tier statistics
        output.append(f"\n📊 Tier Statistics:")
        output.append(f"  Total Files: {tier_stats['file_count']}")
        output.append(f"  Total Size: {tier_stats['total_size_mb']} MB")

        # Community statistics
        output.append(f"\n🌍 Community:")
        output.append(f"  Total Groups: {stats['total_groups']}")
        output.append(f"  Active Groups: {stats['active_groups']}")
        output.append(f"  Total Members: {stats['total_members']}")
        output.append(f"  Total Contributions: {stats['total_contributions']}")

        # User statistics
        output.append(f"\n👤 Your Stats:")
        output.append(f"  Reputation: {user_rep['total_points']} points")
        output.append(f"  Contributions: {user_rep['contributions']}")

        # List user's groups
        user_groups = self.community_service.list_groups(self.current_user)
        output.append(f"  Groups: {len(user_groups)}")

        output.append("\n" + "=" * 60)

        return "\n".join(output)

    # =========================================================================
    # Content Sharing Methods (v1.3.2)
    # =========================================================================
    
    def _profile(self, args: List[str]) -> str:
        """View user profile."""
        if not self.profile_manager:
            return "❌ Profile system not available"
        
        # Ensure profile loaded
        profile = self.profile_manager.load_or_create_default()
        
        if args:
            # View another user's profile (future feature)
            return f"❌ Viewing other profiles not yet implemented"
        
        return self.profile_manager.format_profile(include_private=True)
    
    def _my(self, args: List[str]) -> str:
        """View own profile and submissions."""
        if not self.profile_manager or not self.content_library:
            return "❌ Profile/content system not available"
        
        profile = self.profile_manager.load_or_create_default()
        
        output = []
        output.append(self.profile_manager.format_profile(include_private=True))
        output.append("")
        
        # Show user's submissions
        submissions = [
            s for s in self.content_library.index.values()
            if s.attribution and s.attribution.author_id == profile.user_id
        ]
        
        if submissions:
            output.append("─" * 50)
            output.append(f"Your Submissions ({len(submissions)}):")
            output.append("")
            for sub in submissions[:10]:
                status_icon = sub.share_status.icon
                state = sub.submission_state.value.upper()
                output.append(f"  {status_icon} {sub.title:<30} [{state}]")
            if len(submissions) > 10:
                output.append(f"  ... and {len(submissions) - 10} more")
        else:
            output.append("")
            output.append("No submissions yet. Use COMMUNITY SUBMIT to share content.")
        
        return '\n'.join(output)
    
    def _achievements(self, args: List[str]) -> str:
        """View achievements."""
        if not self.profile_manager:
            return "❌ Profile system not available"
        
        self.profile_manager.load_or_create_default()
        return self.profile_manager.format_achievements()
    
    def _submit(self, args: List[str]) -> str:
        """Submit content for sharing."""
        if not self.profile_manager or not self.content_library:
            return "❌ Profile/content system not available"
        
        if len(args) < 2:
            return self._submit_help()
        
        content_type_str = args[0].lower()
        file_path = Path(args[1])
        
        # Map content type
        from dev.goblin.core.services.content_sharing import ContentType, ShareStatus
        
        type_map = {
            'script': ContentType.SCRIPT,
            'tile': ContentType.TILE,
            'guide': ContentType.GUIDE,
            'workflow': ContentType.WORKFLOW,
        }
        
        if content_type_str not in type_map:
            return f"❌ Unknown content type: {content_type_str}\nValid types: script, tile, guide, workflow"
        
        content_type = type_map[content_type_str]
        
        # Check file exists
        if not file_path.exists():
            # Try relative to common directories
            for base in [
                Path("memory/ucode/scripts"),
                Path("memory/drafts/tiles"),
                Path("memory/docs"),
            ]:
                test_path = base / file_path.name
                if test_path.exists():
                    file_path = test_path
                    break
        
        if not file_path.exists():
            return f"❌ File not found: {file_path}"
        
        # Get profile
        profile = self.profile_manager.load_or_create_default()
        
        # Get additional params
        title = args[2] if len(args) > 2 else file_path.stem
        description = " ".join(args[3:]) if len(args) > 3 else ""
        
        # Create submission
        submission = self.content_library.create_submission(
            title=title,
            file_path=file_path,
            content_type=content_type,
            author_id=profile.user_id,
            author_name=profile.display_name,
            description=description,
        )
        
        output = []
        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append("║  📤 Content Submitted                                          ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")
        output.append(f"  ID: {submission.content_id[:16]}...")
        output.append(f"  Title: {submission.title}")
        output.append(f"  Type: {submission.content_type.value}")
        output.append(f"  Status: {submission.share_status.icon} {submission.share_status.display_name}")
        output.append(f"  State: {submission.submission_state.value}")
        output.append("")
        output.append("Content created as PRIVATE. To share:")
        output.append("  COMMUNITY SHARE <id> PUBLIC    - Submit for Public Knowledge")
        output.append("  COMMUNITY SHARE <id> GROUP <g> - Share with group")
        output.append("  COMMUNITY SHARE <id> USER <u>  - Share with user (IRL)")
        
        return '\n'.join(output)
    
    def _submit_help(self) -> str:
        """Help for submit command."""
        return """
Usage: COMMUNITY SUBMIT <type> <file> [title] [description]

Types:
  script      .upy script files
  tile        .json tile files
  guide       .md knowledge guides
  workflow    .upy workflow files

Examples:
  COMMUNITY SUBMIT script water_filter.upy "Water Filter" "Automated filter setup"
  COMMUNITY SUBMIT guide shelter_basics.md "Shelter Guide"
  COMMUNITY SUBMIT tile map_icon.json "Custom Icon"

Content starts as PRIVATE. Use COMMUNITY SHARE to change visibility.
"""
    
    def _search(self, args: List[str]) -> str:
        """Search community content."""
        if not self.content_library:
            return "❌ Content library not available"
        
        if not args:
            return "❌ Usage: COMMUNITY SEARCH <query>"
        
        query = " ".join(args)
        results = self.content_library.search(query=query)
        
        output = []
        output.append(f"Search results for: '{query}'")
        output.append("─" * 50)
        
        if not results:
            output.append("No results found.")
        else:
            for item in results[:15]:
                rating = f"★{item.average_rating:.1f}" if item.ratings else ""
                output.append(f"  {item.share_status.icon} {item.title:<30} {rating}")
                if item.description:
                    output.append(f"      {item.description[:50]}...")
        
        return '\n'.join(output)
    
    def _download(self, args: List[str]) -> str:
        """Download shared content."""
        if not self.content_library:
            return "❌ Content library not available"
        
        if not args:
            return "❌ Usage: COMMUNITY DOWNLOAD <content_id>"
        
        content_id = args[0]
        
        # Find by ID prefix
        submission = None
        for sid, sub in self.content_library.index.items():
            if sid.startswith(content_id):
                submission = sub
                break
        
        if not submission:
            return f"❌ Content not found: {content_id}"
        
        # TODO: Implement actual download
        return f"✅ Download feature coming soon\nContent: {submission.title}"
    
    def _rate(self, args: List[str]) -> str:
        """Rate content."""
        if not self.profile_manager or not self.content_library:
            return "❌ Profile/content system not available"
        
        if len(args) < 2:
            return "❌ Usage: COMMUNITY RATE <content_id> <stars 1-5>"
        
        content_id = args[0]
        try:
            stars = int(args[1])
        except ValueError:
            return "❌ Stars must be a number 1-5"
        
        if not 1 <= stars <= 5:
            return "❌ Stars must be between 1 and 5"
        
        profile = self.profile_manager.load_or_create_default()
        
        success, msg = self.content_library.rate_content(
            content_id=content_id,
            user_id=profile.user_id,
            stars=stars,
        )
        
        if success:
            # Track rating
            profile.increment_stat('ratings_given')
            profile.add_xp(5)
            self.profile_manager.save_profile()
            return f"✅ {msg}"
        return f"❌ {msg}"
    
    def _review(self, args: List[str]) -> str:
        """Write a review."""
        if not self.profile_manager or not self.content_library:
            return "❌ Profile/content system not available"
        
        if len(args) < 2:
            return "❌ Usage: COMMUNITY REVIEW <content_id> \"<review text>\""
        
        content_id = args[0]
        review_text = " ".join(args[1:]).strip('"\'')
        
        if len(review_text) < 10:
            return "❌ Review must be at least 10 characters"
        
        profile = self.profile_manager.load_or_create_default()
        
        # Add review as 3-star rating (just review, neutral score)
        success, msg = self.content_library.rate_content(
            content_id=content_id,
            user_id=profile.user_id,
            stars=3,
            review=review_text,
        )
        
        if success:
            profile.increment_stat('reviews_written')
            profile.add_xp(15)
            self.profile_manager.save_profile()
            return f"✅ Review submitted"
        return f"❌ {msg}"
    
    def _leaderboard(self, args: List[str]) -> str:
        """Show community leaderboard."""
        category = args[0].lower() if args else "xp"
        
        output = []
        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append("║  🏆 Community Leaderboard                                      ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")
        output.append(f"  Category: {category.upper()}")
        output.append("")
        output.append("  Leaderboards coming in future update.")
        output.append("  (Requires community profile sync)")
        output.append("")
        output.append("Categories: xp, contributions, ratings, guides")
        
        return '\n'.join(output)


def main():
    """Test CommunityCommandHandler"""
    handler = CommunityCommandHandler()

    print("\n" + "=" * 60)
    print("Testing COMMUNITY Commands")
    print("=" * 60 + "\n")

    print(handler.handle("HELP", [])[:500] + "...")
    print("\n" + "=" * 60 + "\n")
    print(handler.handle("STATUS", []))


if __name__ == "__main__":
    main()
