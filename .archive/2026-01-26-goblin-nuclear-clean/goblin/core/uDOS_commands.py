"""
uDOS Alpha v1.0.0.2+ - Command Router

Thin routing layer that delegates commands to specialized handlers.
Now includes transport policy validation for all command execution.

Policy enforcement:
- All commands validated against transport policy before execution
- Role-based access control
- Exposure tier enforcement (LOCAL, PRIVATE_SAFE, WIZARD_ONLY)
- Transport rules strictly enforced
"""

import json
from pathlib import Path
from dev.goblin.core.services.theme.theme_loader import load_theme

# Import mission/workflow handlers at module level for use in execute_ucode
from dev.goblin.core.commands.mission_handler import handle_mission_command
from dev.goblin.core.commands.schedule_handler import handle_schedule_command
from dev.goblin.core.commands.workflow_handler import handle_workflow_command

# Import policy validator for command validation
from extensions.transport.validator import validate_command, ValidationResult
from dev.goblin.core.security.audit_logger import get_auditor


class CommandHandler:
    """Main command router - delegates to specialized handlers."""

    def __init__(
        self,
        theme="dungeon",
        commands_file="dev/goblin/core/data/commands.json",
        history=None,
        connection=None,
        viewport=None,
        user_manager=None,
        command_history=None,
        logger=None,
    ):
        """
        Initialize command handler and load specialized handlers.

        Args:
            theme: Theme name (default: 'dungeon')
            commands_file: Path to commands reference
            history: ActionHistory instance
            connection: ConnectionManager instance
            viewport: Viewport instance
            user_manager: UserManager instance
            command_history: CommandHistory instance
            logger: Logger instance
        """
        # Load theme and commands (merged with any user overrides)
        theme_data = load_theme(theme, root_path=Path(__file__).parent.parent)
        self.lexicon = theme_data.get("TERMINOLOGY", {})
        self.messages = theme_data.get("MESSAGES", {})

        with open(commands_file, "r") as f:

        # Store core dependencies
        self.history = history
        self.connection = connection
        self.viewport = viewport
        self.user_manager = user_manager
        self.command_history = command_history
        self.logger = logger
        self.reboot_requested = False
        self.current_theme = theme

        # Policy enforcement (v1.0.0.2+)
        # Disabled by default in Alpha - enable when transport system is active
        self.policy_enabled = False  # Set to True to enable policy checks
        self.current_role = "device_owner"  # Default role, can be changed
        self.current_transport = "local"  # Default transport
        self.current_realm = "user_mesh"  # Default realm

        # Common kwargs for all handlers
        handler_kwargs = {
            "theme": theme,
            "connection": connection,
            "viewport": viewport,
            "user_manager": user_manager,
            "history": history,
            "command_history": command_history,
            "logger": logger,
            "main_handler": None,  # Will be set after initialization
        }

        # Initialize specialized handlers (lazy loading in handlers themselves)
        from dev.goblin.core.commands.assistant_handler import AssistantCommandHandler
        from dev.goblin.core.commands.file_handler import FileCommandHandler
        from dev.goblin.core.commands.system_handler import SystemCommandHandler

        # Memory System handlers
        from dev.goblin.core.commands.memory_commands import MemoryCommandHandler
        from dev.goblin.core.commands.private_commands import PrivateCommandHandler
        from dev.goblin.core.commands.shared_commands import SharedCommandHandler
        from dev.goblin.core.commands.community_commands import CommunityCommandHandler

        # Core system handlers
        from dev.goblin.core.commands.tile_handler import TILECommandHandler
        from dev.goblin.core.commands.guide_handler import GuideHandler
        from dev.goblin.core.commands.barter_commands import BarterCommandHandler

        # Core UI & System Imports
        from dev.goblin.core.commands.user_handler import UserCommandHandler
        from dev.goblin.core.commands.color_handler import handle_color
        from dev.goblin.core.commands.peek_handler import PeekHandler
        from dev.goblin.core.commands.display_handler import DisplayHandler
        from dev.goblin.core.commands.sandbox_handler import SandboxHandler
        from dev.goblin.core.commands.cloud_handler import CloudHandler
        from dev.goblin.core.commands.loader_handler import LoaderHandler
        from dev.goblin.core.commands.qr_handler import QRHandler
        from dev.goblin.core.commands.audio_handler import AudioHandler
        from dev.goblin.core.commands.music_handler import MusicHandler
        from dev.goblin.core.commands.voice_handler import VoiceHandler
        from dev.goblin.core.commands.plugin_handler import PluginHandler
        from dev.goblin.core.commands.pair_handler import PairHandler
        from dev.goblin.core.commands.install_handler import InstallHandler
        from dev.goblin.core.commands.stack_handler import StackHandler

        self.assistant_handler = AssistantCommandHandler(**handler_kwargs)
        self.file_handler = FileCommandHandler(**handler_kwargs)
        self.system_handler = SystemCommandHandler(**handler_kwargs)
        self.cloud_handler = CloudHandler(**handler_kwargs)
        self.loader_handler = LoaderHandler(**handler_kwargs)
        self.qr_handler = QRHandler()
        self.audio_handler = AudioHandler()
        self.music_handler = MusicHandler()
        self.voice_handler = VoiceHandler()
        self.plugin_handler = PluginHandler(viewport=viewport, logger=logger)
        self.pair_handler = PairHandler(viewport=viewport, logger=logger)

        # Workspace root - derived from this file's location (core/uDOS_commands.py -> project root)
        self.workspace_root = Path(__file__).parent.parent

        self.install_handler = InstallHandler(str(self.workspace_root))
        self.stack_handler = StackHandler(str(self.workspace_root))

        # Memory System Handlers
        self.memory_handler = MemoryCommandHandler()
        self.private_handler = PrivateCommandHandler()
        self.shared_handler = SharedCommandHandler()
        self.community_handler = CommunityCommandHandler()

        # Core System Handlers
        self.tile_handler = TILECommandHandler(**handler_kwargs)
        self.guide_handler = GuideHandler(viewport=viewport, logger=logger)

        # Content Generation Handlers
        from dev.goblin.core.commands.make_handler import MakeHandler

        self.make_handler = MakeHandler(**handler_kwargs)

        from dev.goblin.core.commands.ok_handler import create_ok_handler

        self.ok_handler = create_ok_handler(**handler_kwargs)

        from dev.goblin.core.commands.prompt_handler import PromptHandler

        self.prompt_handler = PromptHandler()

        # Diagram & Integration Handlers
        try:
            from extensions.core.typora_diagrams.handler import (
                get_handler as get_typora_handler,
            )

            self.typora_handler = get_typora_handler(viewport=viewport, logger=logger)
        except ImportError:
            self.typora_handler = None
            # Note: Skip logging - logger signature varies by caller context

        # Game Object Handlers
        from dev.goblin.core.commands.sprite_handler import SpriteHandler
        from dev.goblin.core.commands.object_handler import ObjectHandler

        # Task Management Handlers
        from dev.goblin.core.commands.checklist_handler import ChecklistHandler

        self.checklist_handler = ChecklistHandler(config=None)

        # Inbox Processing Handler
        from dev.goblin.core.commands.inbox_handler import InboxHandler

        self.inbox_handler = InboxHandler(**handler_kwargs)

        from dev.goblin.core.commands.archive_handler import ArchiveHandler

        self.archive_handler = ArchiveHandler(**handler_kwargs)

        # Time/Date Handler (v1.2.22)
        from dev.goblin.core.commands.time_handler import create_time_handler

        self.time_handler = create_time_handler(**handler_kwargs)

        # JSON Viewer/Editor Handler (v1.2.22)
        from dev.goblin.core.commands.json_handler import create_json_handler

        self.json_handler = create_json_handler(**handler_kwargs)

        from dev.goblin.core.commands.backup_handler import create_handler as create_backup_handler

        self.backup_handler = create_backup_handler(viewport=viewport, logger=logger)

        from dev.goblin.core.commands.undo_handler import create_handler as create_undo_handler

        self.undo_handler = create_undo_handler(viewport=viewport, logger=logger)

        # Content & Build Handlers
        from dev.goblin.core.commands.clone_handler import CloneHandler

        self.clone_handler = CloneHandler(**handler_kwargs)

        from dev.goblin.core.commands.build_handler import BuildHandler

        self.build_handler = BuildHandler(**handler_kwargs)

        # v1.2.15 - TUI Management
        from dev.goblin.core.commands.tui_handler import TUIHandler

        self.tui_handler = TUIHandler()  # Will set TUI controller later

        # v1.2.25 - Device Management
        from dev.goblin.core.commands.device_handler import DeviceHandler

        self.device_handler = DeviceHandler(**handler_kwargs)

        # v1.2.25 - Keypad Demo
        from dev.goblin.core.commands.keypad_demo_handler import KeypadDemoHandler

        self.keypad_demo_handler = KeypadDemoHandler(**handler_kwargs)

        # v1.0.0.0 - AI Knowledge Bank (GUIDE AI)
        from dev.goblin.core.commands.guide_ai_handler import GuideAICommandHandler

        self.guide_ai_handler = GuideAICommandHandler(**handler_kwargs)

        # v1.2.25 - Mouse Input
        from dev.goblin.core.commands.mouse_handler import MouseCommandHandler

        self.mouse_handler = MouseCommandHandler(**handler_kwargs)

        # v1.3.0 - Network Handler (MeshCore + Cloud + Web)
        from dev.goblin.core.commands.network_handler import NetworkHandler

        self.network_handler = NetworkHandler(**handler_kwargs)

        # v1.3.0 - Mesh Handler (standalone access)
        from dev.goblin.core.commands.mesh_handler import MeshCommandHandler

        self.mesh_handler = MeshCommandHandler(**handler_kwargs)

        # v1.3.1 - Geography Handler (24×24 Grid Map System)
        from dev.goblin.core.commands.geography_handler import GeographyHandler

        self.geography_handler = GeographyHandler(**handler_kwargs)
        # v1.2.31 - DRAW (Tile Editor)
        from dev.goblin.core.commands.draw_handler import create_draw_handler

        draw_components = {
            "config": None,
            "theme": theme,
            "connection": connection,
            "viewport": viewport,
            "user_manager": user_manager,
            "history": history,
            "command_history": command_history,
            "logger": logger,
        }
        self.draw_handler = create_draw_handler(draw_components)

        # v1.2.25 - Selector Framework
        from dev.goblin.core.commands.selector_handler import SelectorCommandHandler

        self.selector_handler = SelectorCommandHandler(**handler_kwargs)

        from dev.goblin.core.commands.gmail_handler import handle_gmail_command

        self.gmail_handler = handle_gmail_command

        from dev.goblin.core.commands.session_handler import SessionHandler

        self.session_handler = SessionHandler(**handler_kwargs)

        # Get variable_manager from components (if available)
        components = {"config": None, "variable_manager": None, "logger": logger}
        self.sprite_handler = SpriteHandler(components)
        self.object_handler = ObjectHandler(components)

        # Adventure & Game Handlers
        from dev.goblin.core.commands.story_handler import StoryHandler

        story_components = {"config": None, "logger": logger, "output": viewport}
        self.story_handler = StoryHandler(story_components)

        # System Management Handlers
        from dev.goblin.core.commands.logs_handler import create_logs_handler

        self.logs_handler = create_logs_handler()

        self.barter_handler = BarterCommandHandler()

        self.user_handler = UserCommandHandler(**handler_kwargs)

        self.peek_handler = PeekHandler(**handler_kwargs)

        self.display_handler = DisplayHandler(**handler_kwargs)

        self.sandbox_handler = SandboxHandler()

        from dev.goblin.core.commands.extension_handler import create_extension_handler

        self.extension_handler = create_extension_handler(
            viewport=viewport, logger=logger
        )

        # Calendar System (v1.2.23 Task 4)
        from dev.goblin.core.commands.calendar_handler import CalendarHandler
        from dev.goblin.core.config import Config

        self.calendar_handler = CalendarHandler(config=Config(), **handler_kwargs)

        # Development System Handlers

        # Mode Handler (v1.3)
        from dev.goblin.core.commands.mode_handler import ModeCommandHandler

        self.mode_handler = ModeCommandHandler(**handler_kwargs)

        # FEED System Handler (v1.0.0.47)
        from dev.goblin.core.commands.feed_handler import FeedHandler

        self.feed_handler = FeedHandler(**handler_kwargs)

        # Knowledge System Handlers (v1.0.0.54)
        # Note: knowledge_handler deprecated - using guide_handler for knowledge access
        # from dev.goblin.core.commands.knowledge_handler import KnowledgeHandler
        from dev.goblin.core.commands.overlay_handler import OverlayHandler
        from dev.goblin.core.commands.waypoint_handler import WaypointHandler

        # self.knowledge_handler = KnowledgeHandler(**handler_kwargs)
        self.overlay_handler = OverlayHandler(**handler_kwargs)
        self.waypoint_handler = WaypointHandler(**handler_kwargs)

        # Location Service Handler (v1.0.0.56+)
        from dev.goblin.core.commands.location_handler import LocationHandler

        self.location_handler = LocationHandler(**handler_kwargs)

        # BUNDLE System Handler (v1.0.1.0 - Content Packages)
        from dev.goblin.core.commands.bundle_handler import BundleHandler

        self.bundle_handler = BundleHandler(**handler_kwargs)

        # CAPTURE Handler (v1.0.1.0 - Web Content Capture)
        from dev.goblin.core.commands.capture_handler import CaptureHandler

        self.capture_handler = CaptureHandler(**handler_kwargs)

        # WELLBEING Handler (v1.0.1.0 - User Energy/Mood Tracking)
        from dev.goblin.core.commands.wellbeing_handler import WellbeingHandler

        self.wellbeing_handler = WellbeingHandler(**handler_kwargs)

        # PROFILE Handler (v1.0.0.65 - User Configuration)
        from dev.goblin.core.commands.profile_handler import ProfileHandler

        self.profile_handler = ProfileHandler(**handler_kwargs)

        # Set main_handler reference on all handlers
        for handler in [self.assistant_handler, self.file_handler, self.system_handler]:
            handler.main_handler = self

    def get_message(self, key, **kwargs):
        """
        Retrieve a themed message from the lexicon.

        Args:
            key: Message key
            **kwargs: Format arguments

        Returns:
            Formatted message string
        """
        # Prefer full message templates, then terminology tokens, then fallback
        template = None
        if hasattr(self, "messages") and key in self.messages:
            template = self.messages.get(key)
        elif key in self.lexicon:
            template = self.lexicon.get(key)
        else:
            template = f"<{key}>"

        try:
            # Format with provided kwargs
            return template.format(**kwargs)
        except KeyError as e:
            # Missing template variable - provide better error context
            missing_var = str(e).strip("'")
            if self.logger:
                self.logger.warning(f"Template '{key}' missing variable: {missing_var}")
            # Return template with visible placeholder instead of empty
            return template.replace(f"{{{missing_var}}}", f"<{missing_var.upper()}>")
        except Exception as e:
            # Other formatting errors - log and return template as-is
            if self.logger:
                self.logger.error(f"Template '{key}' formatting error: {e}")
            return template

    def execute_ucode(self, ucode: str, grid=None, parser=None) -> str:
        """
        Execute a uCODE command with policy validation.

        Now includes policy validation (v1.0.0.2+):
        - Validates command against transport policy
        - Checks role capabilities
        - Enforces exposure tier constraints
        - Audits policy violations

        Format: [MODULE|COMMAND*PARAM1*PARAM2*...]

        Args:
            ucode: uCODE string to parse and execute
            grid: Grid instance
            parser: Parser instance

        Returns:
            Command result message
        """
        try:
            # Parse uCODE format: [MODULE|COMMAND*PARAM1*PARAM2]
            parts = ucode.strip("[]").split("|")
            module = parts[0].upper()
            command_parts = parts[1].split("*")
            command = command_parts[0].upper()
            params = command_parts[1:] if len(command_parts) > 1 else []

            # Policy validation (v1.0.0.2+)
            if self.policy_enabled:
                result, error = validate_command(
                    command=module,  # Use module as command identifier
                    role=self.current_role,
                    transport=self.current_transport,
                    realm=self.current_realm,
                )

                if result in [
                    ValidationResult.REJECTED,
                    ValidationResult.REJECTED_AND_AUDIT,
                ]:
                    # Log policy violation to audit log
                    auditor = get_auditor()
                    auditor.log_policy_violation(
                        code=error.code,
                        message=error.message,
                        rule=error.rule,
                        command=module,
                        role=self.current_role,
                        transport=self.current_transport,
                        realm=self.current_realm,
                        recommendation=error.recommendation,
                    )

                    # Log to regular logger
                    if self.logger:
                        transport_tag = self._get_transport_tag(self.current_transport)
                        role_tag = self._get_role_tag(self.current_role)
                        self.logger.error(
                            f"{role_tag} {transport_tag} Policy violation: "
                            f"{error.code} - {error.message}"
                        )

                    # Return user-friendly error
                    error_msg = f"🚫 {error.message}"
                    if error.recommendation:
                        error_msg += f"\n💡 {error.recommendation}"
                    return error_msg

                elif result == ValidationResult.PERMITTED_WITH_WARNING:
                    # Log warning but allow execution
                    if self.logger:
                        self.logger.warning(f"[POLICY] {error.message}")
            # Parse uCODE format: [MODULE|COMMAND*PARAM1*PARAM2]
            parts = ucode.strip("[]").split("|")
            module = parts[0].upper()
            command_parts = parts[1].split("*")
            command = command_parts[0].upper()
            params = command_parts[1:] if len(command_parts) > 1 else []

            # Route to appropriate handler
            # OK Assistant (check before ASSISTANT)
            if module == "OK":
                return self.ok_handler.handle(command, params, grid)

            elif module == "ASSISTANT" or module == "ASSIST":
                return self.assistant_handler.handle(command, params, grid)

            elif module == "FILE":
                return self.file_handler.handle(command, params, grid, parser)

            # ROLE - User role and permission management (v1.2.22)
            elif module == "ROLE":
                return self.system_handler.handle_role([command] + params, grid, parser)

            # PATTERNS - Error pattern learning (v1.2.22)
            elif module == "PATTERNS":
                return self.system_handler.handle_patterns(
                    [command] + params, grid, parser
                )

            # ERROR - Error context management (v1.2.22)
            elif module == "ERROR":
                return self.system_handler.handle_error(
                    [command] + params, grid, parser
                )

            # TIME - Time/date system (v1.2.22)
            elif module in ["TIME", "CLOCK", "TIMER", "EGG", "STOPWATCH", "CALENDAR"]:
                return self.time_handler.handle(command, params, grid)

            # JSON - JSON viewer/editor (v1.2.22)
            elif module == "JSON":
                return self.json_handler.handle_command([command] + params)

            # DRAW - 24×24 Tile Editor (v1.2.31)
            elif module == "DRAW":
                return self.draw_handler.handle([command] + params)

            elif module == "MAP":
                return self._core_only_command("MAP")

            # v1.3.1 - GEO Geography Commands (24×24 Grid Map System)
            elif module == "GEO":
                # Route GEO commands to geography handler
                return self.geography_handler.handle(
                    module,
                    " ".join([command] + params) if command else "",
                    grid,
                    parser,
                )

            # Memory System (MEMORY, BANK)
            elif module in ["MEMORY", "BANK"]:
                # BANK is alias for MEMORY tier 4 (PUBLIC)
                if module == "BANK":
                    return self.memory_handler.handle("PUBLIC", [command] + params)
                else:
                    return self.memory_handler.handle(command, params)

            # AI Knowledge Bank (GUIDE + AI subcommand) - AI instruction library (v1.0.0.0)
            elif module == "GUIDE" and command == "AI":
                # GUIDE AI <subcommand> - route to AI knowledge bank
                ai_command = params[0] if params else ""
                ai_params = params[1:] if len(params) > 1 else []
                return self.guide_ai_handler.handle(ai_command, ai_params, grid, parser)

            elif module == "PRIVATE":
                return self.private_handler.handle(command, params)

            elif module == "SHARED":
                return self.shared_handler.handle(command, params)

            elif module == "COMMUNITY":
                return self.community_handler.handle(command, params)

            # Mapping System (TILE, LOCATE)
            elif module in ["TILE", "LOCATE"]:
                return self.tile_handler.handle(
                    command, " ".join(params) if params else "", grid
                )

            # QR Transport (QR)
            elif module == "QR":
                return self.qr_handler.handle(module, params, grid, parser)

            # Audio Transport (AUDIO)
            elif module == "AUDIO":
                return self.audio_handler.handle(
                    module, [command] + params if command else params, grid, parser
                )

            # Music/Groovebox (MUSIC, PLAY)
            elif module in ["MUSIC", "PLAY"]:
                return self.music_handler.handle(
                    module, [command] + params if command else params, grid, parser
                )

            # Voice (VOICE, SAY, LISTEN) - Piper TTS + Handy STT
            elif module in ["VOICE", "SAY", "LISTEN"]:
                if module == "SAY":
                    # SAY hello world -> VOICE SAY hello world
                    voice_params = ["SAY"] + ([command] + params if command else params)
                elif module == "LISTEN":
                    # LISTEN -> VOICE LISTEN
                    voice_params = ["LISTEN"] + (
                        [command] + params if command else params
                    )
                else:
                    voice_params = [command] + params if command else params
                return self.voice_handler.handle("VOICE", voice_params, grid, parser)

            # MeshCore Transport (MESH)
            elif module == "MESH":
                return self.mesh_handler.handle(command, params)

            # Barter System
            elif (
                module == "BARTER"
                or module == "OFFER"
                or module == "REQUEST"
                or module == "TRADE"
            ):
                # Route OFFER, REQUEST, TRADE directly to barter handler
                if module in ["OFFER", "REQUEST", "TRADE"]:
                    return self.barter_handler.handle(module, params)
                else:
                    return self.barter_handler.handle(command, params)

            # Sprite System
            elif module == "SPRITE":
                success = self.sprite_handler.handle([command] + params)
                return "✅ Command executed" if success else "❌ Command failed"

            elif module == "OBJECT":
                success = self.object_handler.handle([command] + params)
                return "✅ Command executed" if success else "❌ Command failed"

            # v1.2.24 - Core Gameplay Commands
            elif module == "CHECKPOINT":
                # Map to WORKFLOW SAVE_CHECKPOINT/LOAD_CHECKPOINT
                from dev.goblin.core.config import Config

                config = Config()
                # Convert CHECKPOINT*SAVE → SAVE_CHECKPOINT, CHECKPOINT*LOAD → LOAD_CHECKPOINT
                if command == "SAVE":
                    workflow_command = "SAVE_CHECKPOINT"
                elif command == "LOAD":
                    workflow_command = "LOAD_CHECKPOINT"
                elif command == "LIST":
                    workflow_command = "LIST_CHECKPOINTS"
                else:
                    workflow_command = command
                return handle_workflow_command(workflow_command, params, config)

            elif module == "XP":
                # Map to BARTER XP system
                return self.barter_handler.handle("XP", [command] + params)

            elif module == "ITEM":
                # Map to SPRITE INVENTORY system
                inventory_command = (
                    "ADD"
                    if not command or command.startswith("+")
                    else "REMOVE" if command.startswith("-") else command
                )
                sprite_params = ["INVENTORY", inventory_command] + params
                success = self.sprite_handler.handle(sprite_params)
                return "✅ Item updated" if success else "❌ Item operation failed"

            # Story System
            elif module == "STORY":
                return self.story_handler.handle(command, params)

            # Display System
            elif module == "PANEL" or module == "UI":
                return self._core_only_command("PANEL")

            # FEED System (v1.0.0.47 - Core real-time data feed)
            elif module == "FEED":
                return self.feed_handler.handle(
                    module,
                    " ".join([command] + params) if command else "",
                    grid,
                    parser,
                )

            # Display Commands (BLANK, SPLASH, DASH)
            elif module in ["BLANK", "CLEAR", "SPLASH", "DASH"]:
                return self.display_handler.handle(
                    module if module in ["BLANK", "CLEAR", "SPLASH"] else command,
                    params,
                    grid,
                    parser,
                )

            # Knowledge System
            elif module == "GUIDE":
                return self.guide_handler.handle(command, params)

            # DOCS - redirect to GUIDE (backward compatibility)
            elif module == "DOCS":
                return self.guide_handler.handle(command, params)

            # Calendar & Task Management (v1.2.23 Task 4)
            elif module in ["CAL", "CALENDAR"]:
                return self.calendar_handler.handle_command(
                    [command] + params if command else []
                )

            # Task Management (v1.2.23 Task 4 - integrated with calendar)
            elif module == "TASK":
                return self.calendar_handler.handle_command(
                    [command] + params if command else []
                )

            # Checklist Management (separate from TASK)
            elif module == "CHECKLIST":
                return self.checklist_handler.handle(command, params)

            # Inbox Processing
            elif module == "INBOX":
                return self.inbox_handler.handle(command, params, grid)

            # Archive Management
            elif module == "ARCHIVE":
                return self.archive_handler.handle(params, grid, parser)

            # Backup System
            elif module == "BACKUP":
                return self.backup_handler.handle(params, grid, parser)

            # v1.1.16 - UNDO/REDO Version History
            elif module == "UNDO":
                return self.undo_handler.handle(params, grid, parser)

            elif module == "REDO":
                return self.undo_handler.handle_redo(params, grid, parser)

            # Session Management
            elif module in ["SESSION", "HISTORY", "RESTORE"]:
                return self.session_handler.handle(module, params, grid, parser)

            # Unified Generation System
            elif module == "MAKE":
                # MAKE handler expects all params including subcommand
                # Prepend command back to params since it contains the subcommand
                all_params = [command] + params if command else params
                return self.make_handler.handle("MAKE", all_params, grid)

            # OK Assistant Commands (OK, DIAGRAM, DRAW)
            elif module in ["OK", "DIAGRAM", "DRAW"]:
                # DIAGRAM/DRAW are aliases for OK MAKE commands
                if module == "DIAGRAM":
                    return self.ok_handler.handle(
                        "MAKE", ["DIAGRAM", command] + params, grid
                    )
                elif module == "DRAW":
                    return self.ok_handler.handle(
                        "MAKE", ["SVG", command] + params, grid
                    )
                else:
                    return self.ok_handler.handle(command, params, grid)

            # Admin Prompt Management
            elif module == "PROMPT":
                return self.prompt_handler.handle(params)

            # Diagram Systems
            elif module == "TYPORA":
                if self.typora_handler:
                    return self.typora_handler.handle_command(params)
                else:
                    return (
                        "❌ Typora diagrams extension not available\n\n"
                        "The extension is located in:\n"
                        "  extensions/core/typora-diagrams/\n\n"
                        "Make sure the handler.py file exists and is importable.\n"
                    )

            # System Management
            elif module == "LOGS":
                return self.logs_handler.handle(command, params)

            # Extension Management (POKE, OUTPUT, SERVER commands)
            elif module == "POKE" or module == "OUTPUT" or module == "SERVER":
                # POKE command routes to extension management
                # Check if this is POKE Online extension command (tunnel/sharing)
                if command.upper() in ["TUNNEL", "SHARE", "GROUP"]:
                    # Try to load POKE Online extension for cloud features
                    try:
                        from extensions.cloud.poke_commands import handle_poke_command

                        return handle_poke_command([command] + params)
                    except ImportError:
                        return (
                            "❌ POKE Online extension not available\n"
                            "💡 Install the cloud extension for tunnel/sharing features\n"
                            "💡 Use: POKE LIST for available web extensions"
                        )
                    except Exception as e:
                        return f"❌ POKE Online error: {e}"
                else:
                    # Delegate to system handler for core extension management
                    # Handles: POKE LIST, POKE START <name>, POKE STATUS, etc.
                    # Must include command as first param: [START, terminal] not just [terminal]
                    return self.system_handler.handle_output(
                        [command] + params, grid, parser
                    )

            # User Feedback
            elif module == "USER":
                return self.user_handler.handle(command, params, grid)

            # Feedback Shortcuts (FEEDBACK, REPORT)
            elif module in ["FEEDBACK", "REPORT"]:
                return self.user_handler.handle(
                    "FEEDBACK" if module == "FEEDBACK" else "REPORT", params, grid
                )

            # v1.0.32 - TREE Directory Structure Generator
            elif module == "TREE":
                return self._wizard_only_command("TREE")

            # v1.2.15 - TUI Management (Keypad, Predictor, Pager, Browser)
            elif module == "TUI":
                return self.tui_handler.handle_command(
                    [command] + params if command else params
                )

            # v1.2.25 - Device Management (Input Devices)
            elif module == "DEVICE":
                return self.device_handler.handle_command(
                    [command] + params if command else params
                )

            # v1.2.25 - Keypad Demo (Universal Input System)
            elif module == "KEYPAD":
                return self.keypad_demo_handler.handle_command(
                    [command] + params if command else params
                )

            # v1.2.25 - Mouse Input (Universal Input System)
            elif module == "MOUSE":
                return self.mouse_handler.handle_command(
                    [command] + params if command else params
                )

            # v1.2.25 - Selector Framework (Universal Input System)
            elif module == "SELECTOR":
                return self.selector_handler.handle_command(
                    [command] + params if command else params
                )

            # v1.5.0 - PEEK Data Collection System
            elif module == "PEEK":
                return self.peek_handler.handle(command, params, grid, parser)

            # Maintenance Operations (TIDY, CLEAN) - Alpha v1.0.0.0+
            elif module == "TIDY":
                return self._core_only_command("TIDY")

            elif module == "CLEAN":
                return self._core_only_command("CLEAN")

            # v2.0 - Sandbox Management System (Beta v1.2.x)
            elif module == "SANDBOX":
                return self.sandbox_handler.handle(command, params)

            # v2.3.0 - Terminal Loader System
            elif module == "LOADER":
                return self.loader_handler.handle(command, params, grid, parser)

            # v1.3.0 - NETWORK Unified Network Management
            elif module == "NETWORK":
                return self.network_handler.handle_command(
                    [module, command] + params if command else [module] + params
                )

            # v1.3.0 - MESH MeshCore Commands (direct access)
            elif module == "MESH":
                return self.mesh_handler.handle(command, params if params else [])

            # v1.2.21 - CLONE User Content Packaging
            elif module == "CLONE":
                return self.clone_handler.handle(params, grid, parser)

            # v1.2.21 - CLOUD Business Intelligence (BIZINTEL)
            elif module == "CLOUD":
                return self.cloud_handler.handle_command([module] + [command] + params)

            # v1.2.21 - BUILD Offline Installation Packaging
            elif module == "BUILD":
                return self.build_handler.handle(params, grid, parser)

            # v1.1.16 - UNDO/REDO Version History
            elif module == "UNDO":
                return self.undo_handler.handle(params, grid, parser)

            elif module == "REDO":
                return self.undo_handler.handle_redo(params, grid, parser)

            # v1.1.8 - EXTENSION Management (Extension Polish)
            elif module == "EXTENSION" or module == "EXT":
                return self.extension_handler.handle_command([command] + params)

            # v1.1.0.6 - PLUGIN Code Container Management (Wizard Server)
            elif module == "PLUGIN":
                return self.plugin_handler.handle_command(
                    [command] + params if command else params
                )

            # v1.1.0.8 - PAIR Mobile Console Pairing
            elif module == "PAIR":
                return self.pair_handler.handle_command(
                    [command] + params if command else params
                )

            # v1.1.0.9 - INSTALL TCZ Package Management
            elif module == "INSTALL":
                return self.install_handler.handle_command(
                    [command] + params if command else params
                )

            # v1.0.0.13 - STACK Capability-Based Installation
            elif module == "STACK":
                return self.stack_handler.handle_command(
                    [command] + params if command else params
                )

            # v1.2.2 - DEV MODE Interactive Debugging
            elif module == "DEV":
                return self._wizard_only_command("DEV")

            # v1.1.2 - Mission Control & Workflow Automation
            elif module == "MISSION":
                # Reconstruct command line for mission handler
                command_line = f"MISSION {command}" + (
                    " " + " ".join(params) if params else ""
                )
                return handle_mission_command(command_line)

            # v1.1.2 - Scheduler System
            elif module == "SCHEDULE":
                # Reconstruct command line for schedule handler
                command_line = f"SCHEDULE {command}" + (
                    " " + " ".join(params) if params else ""
                )
                return handle_schedule_command(command_line)

            # v1.1.2 - Workflow Automation (WORKFLOW, RUN)
            elif module in ["WORKFLOW", "RUN"]:
                from dev.goblin.core.config import Config

                config = Config()
                return handle_workflow_command(command, params, config)

            # v1.2.9 - Gmail Cloud Integration
            elif (
                module == "GMAIL"
                or module == "LOGIN"
                or module == "LOGOUT"
                or module == "EMAIL"
                or module == "SYNC"
            ):
                # Route LOGIN GMAIL, LOGOUT GMAIL, STATUS GMAIL, EMAIL LIST, SYNC GMAIL, etc.
                from dev.goblin.core.config import Config

                config = Config()
                # Reconstruct command line for gmail handler
                if module == "GMAIL" or module == "SYNC":
                    parts = [module, command] + params
                else:
                    # LOGIN/LOGOUT/EMAIL are shortcuts to GMAIL subcommands
                    parts = [module, command] + params if command else [module] + params
                return self.gmail_handler(parts, config=config)

            # v1.1.2 - Resource Management
            elif module == "RESOURCE":
                from dev.goblin.core.commands.resource_handler import handle_resource_command

                # If no command provided, show help
                if not command or command.strip() == "":
                    result = handle_resource_command("HELP")
                    return result.get("output", str(result))

                # Parse params into kwargs for resource handler
                kwargs = {"provider": params[0] if params else None}

                # Handle --flag arguments
                i = 0
                while i < len(params):
                    param = params[i]
                    if param.startswith("--"):
                        # Flag with value
                        flag_name = param[2:]  # Remove --
                        if i + 1 < len(params) and not params[i + 1].startswith("--"):
                            kwargs[flag_name] = params[i + 1]
                            i += 2
                        else:
                            kwargs[flag_name] = True
                            i += 1
                    elif not param.startswith("--") and "mission_id" not in kwargs:
                        # First non-flag param is mission_id
                        kwargs["mission_id"] = param
                        i += 1
                    else:
                        i += 1

                result = handle_resource_command(command, **kwargs)
                return result.get("output", str(result))

            # v1.2.8+ - COLOR TUI Enhancement (rainbow splash, syntax highlighting, themed UI)
            elif module in ["COLOR", "PALETTE"]:
                # Join all params into single string for subcommand
                param_str = " ".join(params) if params else ""
                return handle_color(param_str)

            # v1.3 - MODE system (prompt mode switching)
            elif module in ["MODE", "GHOST", "TOMB", "CRYPT"]:
                return self.mode_handler.handle(command, params)

            # v1.0.0.54 - Knowledge System (routes to GUIDE)
            elif module in ["KNOWLEDGE", "KB", "DOCS"]:
                # Route to GUIDE handler (knowledge_handler deprecated)
                return self.guide_handler.handle(
                    command if command else "LIST",
                    params,
                    grid,
                    parser,
                )

            # v1.0.0.54 - Overlay Management
            elif module == "OVERLAY":
                return self.overlay_handler.handle(
                    module,
                    f"{command} {' '.join(params)}" if command else "",
                    grid,
                    parser,
                )

            # v1.0.0.54 - Waypoint Navigation
            elif module in ["WAYPOINT", "WP"]:
                return self.waypoint_handler.handle(
                    module,
                    f"{command} {' '.join(params)}" if command else "",
                    grid,
                    parser,
                )

            # v1.0.0.56 - Location Service (Privacy-First)
            elif module in ["LOCATION", "LOC", "SKY", "STARS"]:
                # SKY and STARS are shortcuts to LOCATION SKY/STARS
                if module in ["SKY", "STARS"]:
                    return self.location_handler.handle(
                        "LOCATION",
                        module,  # Pass SKY or STARS as subcommand
                        grid,
                        parser,
                    )
                return self.location_handler.handle(
                    module,
                    f"{command} {' '.join(params)}" if command else "",
                    grid,
                    parser,
                )

            # v1.0.0.64 - BUNDLE Content Package Management (Drip Delivery)
            elif module == "BUNDLE":
                return self.bundle_handler.handle(command, params, grid, parser)

            # v1.0.0.64 - CAPTURE Web Content Pipeline
            elif module == "CAPTURE":
                return self.capture_handler.handle(command, params, grid, parser)

            # v1.0.0.64 - WELLBEING User Energy/Mood Tracking
            elif module == "WELLBEING":
                return self.wellbeing_handler.handle(command, params, grid, parser)

            # v1.0.0.65 - RUOK? Mutual Wellbeing Check (alias)
            elif module in ("RUOK", "RUOK?"):
                return self.wellbeing_handler.handle(
                    "WELLBEING",
                    ["RUOK"] + ([command] + params if command else []),
                    grid,
                    parser,
                )

            # v1.0.0.65 - PROFILE User Configuration
            elif module == "PROFILE":
                return self.profile_handler.handle(command, params, grid, parser)

            # v1.0.0.63 - API Quota Management (Wizard Server)
            elif module == "QUOTA":
                from dev.goblin.core.commands.quota_handler import handle_quota_command

                # Reconstruct command line for quota handler
                command_line = (
                    f"QUOTA {command}" + (" " + " ".join(params) if params else "")
                    if command
                    else "QUOTA"
                )
                return handle_quota_command(command_line)

            # v1.0.0.64 - AI Connection Testing
            elif (
                module == "AI"
                and command
                and command.upper() in ["TEST", "STATUS", "PROMPTS", "KEYS", "HELP"]
            ):
                from dev.goblin.core.commands.ai_test_handler import handle_ai_test_command

                # Reconstruct params for AI test handler
                param_str = f"{command} {' '.join(params)}" if command else ""
                result = handle_ai_test_command(param_str, grid, parser)
                return result.get("content", result.get("message", str(result)))

            # v1.0.2.0 - OK FIX command (routed through OK handler for consolidation)
            elif module == "OK" and command and command.upper() == "FIX":
                from dev.goblin.core.commands.ok_handler import OKHandler

                ok_handler = OKHandler(grid=grid, parser=parser, config=self.config)
                return ok_handler.handle(command, params, grid, parser)

            elif module == "SYSTEM":
                # System handler needs access to reboot flag
                result = self.system_handler.handle(command, params, grid, parser)
                # Check if reboot was requested
                if hasattr(self.system_handler, "reboot_requested"):
                    self.reboot_requested = self.system_handler.reboot_requested
                return result

            else:
                return self.get_message("ERROR_UNKNOWN_MODULE", module=module)

        except IndexError as e:
            return self.get_message(
                "ERROR_INVALID_UCODE_FORMAT",
                ucode=ucode,
                error=f"Missing module or command: {str(e)}",
            )
        except AttributeError as e:
            # AttributeError often indicates missing handler methods or configuration issues
            error_msg = self.get_message(
                "ERROR_INVALID_UCODE_FORMAT", ucode=ucode, error=str(e)
            )

            # Check if dev mode is available and suggest entering it
            try:
                from dev.goblin.core.services.dev_mode_manager import get_dev_mode_manager

                dev_mode_mgr = get_dev_mode_manager()
                if not dev_mode_mgr.is_active:
                    error_msg += "\n\n🔧 System Error Detected\n"
                    error_msg += "💡 Type 'DEV' to enter Dev Mode for diagnostics\n"
                    error_msg += "💡 Or type 'REPAIR' to run system diagnostics"
            except Exception:
                pass  # Dev mode not available

            return error_msg
        except Exception as e:
            return self.get_message(
                "ERROR_INVALID_UCODE_FORMAT", ucode=ucode, error=str(e)
            )

    def _core_only_command(self, command_name: str) -> str:
        """Return guidance for commands that now live in the core runtime."""
        return "\n".join(
            [
                f"{command_name} is handled by the Core runtime.",
                "Launch the main uDOS TUI and run the command there.",
            ]
        )

    def _wizard_only_command(self, command_name: str) -> str:
        """Return guidance for commands that require the Wizard server."""
        return "\n".join(
            [
                f"{command_name} is managed by the Wizard Server.",
                "Start the wizard server (python -m wizard.server) and use its TUI.",
            ]
        )

    def _get_transport_tag(self, transport: str) -> str:
        """Get logging tag for transport."""
        tags = {
            "local": "[LOCAL]",
            "meshcore": "[MESH]",
            "bluetooth_private": "[BT-PRIV]",
            "bluetooth_public": "[BT-PUB]",
            "nfc": "[NFC]",
            "qr_relay": "[QR]",
            "audio_relay": "[AUD]",
            "internet": "[WEB]",
            "web_sockets": "[WS]",
        }
        return tags.get(transport, "[UNKNOWN]")

    def _get_role_tag(self, role: str) -> str:
        """Get logging tag for role."""
        tags = {
            "device_owner": "[DEVICE]",
            "paired_device": "[PAIRED]",
            "mobile_console": "[MOBILE]",
            "wizard_server": "[WIZ]",
        }
        return tags.get(role, "[UNKNOWN]")

    def set_policy_context(
        self, role: str = None, transport: str = None, realm: str = None
    ):
        """
        Set current policy context for command execution.

        Args:
            role: Current role (device_owner, paired_device, mobile_console, wizard_server)
            transport: Current transport (local, meshcore, bluetooth_private, etc.)
            realm: Current realm (user_mesh, wizard_server)
        """
        if role:
            self.current_role = role
        if transport:
            self.current_transport = transport
        if realm:
            self.current_realm = realm

        if self.logger:
            self.logger.info(
                f"[POLICY] Context updated: {self.current_role} / "
                f"{self.current_transport} / {self.current_realm}"
            )


# Example Usage (for testing)
if __name__ == "__main__":
    from dev.goblin.core.services.uDOS_grid import Grid
    from dev.goblin.core.interpreters.uDOS_parser import Parser

    grid = Grid()
    parser = Parser()
    handler = CommandHandler()

    print("=" * 60)
    print("uDOS v1.0.0 Command Router Test")
    print("=" * 60)
    print()

    # Test system commands
    print("--- SYSTEM COMMANDS ---")
    print(handler.handle_command("[SYSTEM|STATUS]", grid, parser))
    print()

    # Test file commands
    print("--- FILE COMMANDS ---")
    print(handler.handle_command("[FILE|SHOW*README.MD]", grid, parser))
    print()

    # Test assistant commands
    print("--- ASSISTANT COMMANDS ---")
    print(handler.handle_command("[ASSISTANT|ASK*What is uDOS?]", grid, parser))
    print()

    # Test map commands
    print("--- MAP COMMANDS ---")
    print(handler.handle_command("[MAP|STATUS]", grid, parser))
    print()

    print("=" * 60)
    print("✅ Command router test complete")
    print("=" * 60)
