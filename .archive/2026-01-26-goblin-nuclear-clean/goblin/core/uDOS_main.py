# uDOS v1.2.23 - Main Application

# Suppress dependency warnings gracefully
import warnings

warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core")

from .output.splash import print_splash_screen
from .interpreters.uDOS_parser import Parser
from .uDOS_commands import CommandHandler
from .services.uDOS_grid import Grid
from .services.logging_manager import get_logger, LogSource
from .services.theme_bootstrap import init_theme_from_config
from .services.theme_output import themed_print
from .utils.completer import AdvancedCompleter
from .utils.setup import SystemSetup
from .services.history_manager import ActionHistory
from .utils.error_helper import (
    format_system_error,
    format_command_error,
    suggest_dev_mode_help,
)
from .services.uDOS_startup import SystemHealth, check_system_health, repair_system
from .services.connection_manager import ConnectionMonitor
from .utils.viewport import ViewportDetector
from .services.user_manager import UserManager
from .input.smart_prompt import SmartPrompt
from .ui.tui_controller import TUIController
from .ui.tui_config import get_tui_config
from .input.prompt_decorator import get_prompt_decorator
from .services.standardized_input import StandardizedInput
from .config import Config  # v1.1.12 Unified Configuration (replaces config_manager)
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory  # v1.1.12: Replace CommandHistory
import sys
import os
import time

# Global configuration manager (Uses new Config class)
_config_manager = None


def get_config():
    """
    Get global Config instance.

    Returns:
        Config instance (v1.1.12: New unified config with .env and user.json support)
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = Config()
    return _config_manager


def run_script(
    script_path, parser, grid, command_handler, logger, command_history=None
):
    """
    Executes a uDOS script file (.upy format only).

    v1.2.24: Uses UPYRuntime parser for bracket syntax COMMAND[ args | ... ]
    v1.1.12: Uses UPYParser for new COMMAND(args) syntax.
    v2.0.2: Updated for v2.0.2 syntax support.
    Backward compatibility for .uscript removed in v1.1.12.
    """
    from pathlib import Path

    try:
        # Convert string path to Path object
        script_file = Path(script_path) if isinstance(script_path, str) else script_path

        # v1.1.12: Only .upy files supported
        if not str(script_file).lower().endswith(".upy"):
            error_msg = f"❌ Unsupported file format. Only .upy files are supported.\n   Convert with: python bin/migrate_upy.py {script_file}"
            logger.error(error_msg)
            print(error_msg)
            return

        # Use v1.2.24 runtime for COMMAND[ args ] bracket syntax
        from dev.goblin.core.runtime.upy_runtime import UPYRuntime

        runtime = UPYRuntime(command_handler=command_handler, grid=grid, parser=parser)

        logger.info(f"🔷 Running uPY v1.2.x script: {script_file}")

        # Execute script
        try:
            output = runtime.execute_file(script_file)
            if output:
                result = "\n".join(output)
                logger.info(result)
        except Exception as e:
            error_msg = f"❌ Error executing '{script_file}': {e}"
            logger.error(error_msg)
            print(error_msg)

    except FileNotFoundError:
        error_msg = f"Error: Script file not found at '{script_path}'"
        logger.error(error_msg)
        print(error_msg)
    except Exception as e:
        error_msg = f"An error occurred while running the script: {e}"
        logger.error(error_msg)
        print(error_msg)


def initialize_system(is_script_mode=False, run_health_check=False):
    """
    Initialize all system components.

    Args:
        is_script_mode: True if running a script (non-interactive)
        run_health_check: True to run full health check (slower)
    """
    # Standard initialization
    components = {}

    try:
        # 1. Initialize configuration (v1.5.0+)
        if not is_script_mode:
            themed_print("Loading configuration...", "status", end=" ", flush=True)
        config = get_config()
        components["config"] = config
        if not is_script_mode:
            username = config.get("username", "user")
            themed_print(f"✓ {username}", "success")

        # Initialize theme overlay from config (display-layer only)
        active_theme = init_theme_from_config(config)
        if not is_script_mode and active_theme != "default":
            themed_print(f"Theme overlay active: {active_theme}", "status")

        # 2. Detect viewport (force fresh detection)
        if not is_script_mode:
            themed_print("Detecting viewport...", "status", end=" ", flush=True)
        viewport = ViewportDetector()
        # Force fresh detection - don't rely on cached values
        actual_size = viewport.detect_terminal_size()
        viewport.classify_device()
        components["viewport"] = viewport
        if not is_script_mode:
            themed_print(
                f"✓ {viewport.device_type} ({viewport.width}×{viewport.height})",
                "success",
            )
            # Show educational viewport splash
            try:
                from dev.goblin.core.services.viewport_manager import ViewportManager
                from dev.goblin.core.utils.viewport_viz import ViewportVisualizer

                vp_manager = ViewportManager()
                vp_manager.refresh_viewport()

                viz = ViewportVisualizer(viewport=viewport)
                splash = viz.generate_educational_splash(viewport_manager=vp_manager)
                print(splash)
            except Exception:
                # Don't fail startup if splash fails
                pass

        # 3. Check connection
        if not is_script_mode:
            themed_print("Checking connectivity...", "status", end=" ", flush=True)
        connection = ConnectionMonitor()
        connection.check_internet_connection()
        components["connection"] = connection
        mode = connection.get_mode()
        if not is_script_mode:
            themed_print(f"✓ {mode}", "success")

        # 4. User profile
        user_manager = UserManager()
        components["user_manager"] = user_manager

        viewport_data = viewport.get_status_summary()

        if user_manager.needs_user_setup():
            user_manager.run_user_setup(
                interactive=not is_script_mode, viewport_data=viewport_data
            )
        else:
            user_manager.load_user_profile()
            session_id = f"session_{int(time.time())}"
            user_manager.update_session_data(session_id, viewport_data)

        # 5. System health check
        if not is_script_mode and run_health_check:
            print("🏥 System health...", end=" ", flush=True)

        from dev.goblin.core.services.uDOS_startup import (
            quick_health_check,
            check_system_health,
            repair_system,
        )

        is_healthy, message = quick_health_check()
        health = None  # Initialize health variable

        if not is_script_mode and run_health_check:
            # Show brief status
            if is_healthy and "warning" not in message.lower():
                print("✓ Healthy")
            elif is_healthy:
                print(f"⚠️  Warnings")
            else:
                print(f"❌ Issues")

            # If there are issues, offer to repair
            if not is_healthy:
                print()
                print(f"  {message}")
                print()

                # Only prompt if we have an interactive terminal
                import sys

                if sys.stdin.isatty():
                    try:
                        input_service = StandardizedInput()
                        response = input_service.select_option(
                            title="Attempt auto-repair?",
                            options=["Yes", "No", "OK"],
                            default_index=0,
                        )
                        if response in ["Yes", "OK"]:
                            print()
                            health = check_system_health(
                                verbose=False, return_dict=False
                            )
                            health = repair_system(health, verbose=True)
                            print()
                            if health.is_healthy():
                                print("  ✅ System repaired successfully!")
                            else:
                                print(
                                    "  ⚠️  Some issues remain - run 'REPAIR --report' for details"
                                )
                    except (EOFError, KeyboardInterrupt):
                        print("\n  ⚠️  Skipping auto-repair")
                        print("  💡 Run 'REPAIR' command later to fix issues")
                else:
                    print("  ⚠️  Non-interactive mode - skipping auto-repair")
                    print("  💡 Run 'REPAIR' command to fix issues")
                print()
        elif not is_script_mode and not run_health_check:
            # Fast mode: skip health check silently
            pass

        # Store health check results (if available)
        if health:
            components["health"] = health

        # 5. Project setup
        setup = SystemSetup()
        if setup.needs_setup():
            story_data = (
                setup.create_default_story() if is_script_mode else setup.run_setup()
            )
        else:
            story_data = setup.load_story()

        setup.increment_session()
        components["setup"] = setup
        components["story_data"] = story_data

        # Tree generation removed from startup - use TREE command instead
        components["tree_generated"] = False

        return components

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"\n💥 Critical initialization error: {e}")
        return None


def main():
    """Main function with full system initialization."""
    try:
        # Check for help flag first
        if "--help" in sys.argv or "-h" in sys.argv:
            print("uDOS v1.2.23 - Universal Device Operating System")
            print("Usage:")
            print("  python uDOS.py                     # Interactive mode")
            print('  python uDOS.py -c "COMMAND"       # Execute single command')
            print("  python uDOS.py script.upy          # Run uPY script")
            print("  python uDOS.py --version           # Show version")
            print("  python uDOS.py --check             # Run system health check")
            print("  python uDOS.py --help              # Show this help")
            print("\nExamples:")
            print('  python uDOS.py -c "STATUS"')
            print('  python uDOS.py -c "HELP"')
            print('  echo "STATUS" | python uDOS.py')
            return 0

        # Check for version flag
        if "--version" in sys.argv or "-v" in sys.argv:
            print("uDOS v1.2.23 - uPY Migration Complete")
            print("Released: December 2, 2025")
            print("\nFeatures:")
            print("  • .upy format only (COMMAND args syntax)")
            print("  • Python-first architecture")
            print("  • Backward compatibility removed")
            print("  • Migration tools included")
            print("  • 166+ survival knowledge guides")
            return 0

        # Check for command flags first
        command_to_run = None
        if "-c" in sys.argv:
            try:
                c_index = sys.argv.index("-c")
                if c_index + 1 < len(sys.argv):
                    command_to_run = sys.argv[c_index + 1]
            except (ValueError, IndexError):
                print("Error: -c flag requires a command argument")
                return 1

        # Check for other flags
        is_script_mode = (
            len(sys.argv) > 1
            and not sys.argv[1].startswith("--")
            and "-c" not in sys.argv
        )
        run_health_check = "--check" in sys.argv
        fast_mode = (
            not run_health_check
        )  # Skip health by default unless --check is passed

        components = initialize_system(is_script_mode, run_health_check)
        if not components:
            return 1

        viewport = components["viewport"]
        connection = components["connection"]
        user_manager = components["user_manager"]
        story_data = components["story_data"]

        print_splash_screen()

        # Educational viewport splash already shown during initialize_system() (v1.2.25)
        # No need to show twice

        # Show startup time (v1.2.22)
        try:
            from dev.goblin.core.services.timedate_manager import get_timedate_manager

            tdm = get_timedate_manager()
            tz_info = tdm.get_time_info()
            time_str = tdm.get_current_time(None, "%Y-%m-%d %H:%M:%S")
            print(f"🕐 {time_str} | {tz_info.abbreviation} ({tz_info.offset})", end="")
            if tz_info.city:
                print(f" | 📍 {tz_info.city}", end="")
            if tz_info.tile:
                print(f" | 🗺️  TILE {tz_info.tile}", end="")
            print()
        except Exception:
            pass  # Silently skip if time system not available

        # Initialize core components (only once!)
        parser = Parser()
        grid = Grid()
        # v1.0.0.29: Use canonical logger with TUI source for unified logging
        logger = get_logger("session-commands", source=LogSource.TUI)
        # ActionHistory doesn't use logger in critical path - set to None for now
        history = ActionHistory(logger=None)

        # Initialize command history system (v1.1.12: using InMemoryHistory)
        command_history = InMemoryHistory()

        # Handle -c command flag (single command execution)
        if command_to_run:
            try:
                # Initialize command handler with proper parameters
                command_handler = CommandHandler(
                    history=history,
                    connection=connection,
                    viewport=viewport,
                    user_manager=user_manager,
                    command_history=command_history,
                    logger=logger,
                )

                # Execute single command and exit
                ucode = parser.parse(command_to_run)
                result = command_handler.handle_command(ucode, grid, parser)
                if result:
                    print(result)
                return 0
            except Exception as e:
                print(f"Error executing command '{command_to_run}': {e}")
                return 1

        # Handle piped input (stdin) - process commands from pipe then exit
        if not sys.stdin.isatty():
            try:
                # Initialize command handler with proper parameters
                command_handler = CommandHandler(
                    history=history,
                    connection=connection,
                    viewport=viewport,
                    user_manager=user_manager,
                    command_history=command_history,
                    logger=logger,
                )

                # Read and process all piped commands
                for line in sys.stdin:
                    line = line.strip()
                    if line and line.lower() != "exit":
                        try:
                            ucode = parser.parse(line)
                            result = command_handler.execute_ucode(ucode, grid, parser)
                            if result:
                                print(result)
                        except Exception as e:
                            print(f"Error executing command '{line}': {e}")

                return 0
            except (KeyboardInterrupt, EOFError):
                return 0
            except Exception as e:
                print(f"Error processing piped input: {e}")
                return 1

        # Get session and move stats (Alpha v1.0.0.0: simplified, no move tracking yet)
        move_stats = {"session_number": 1, "move_count": 0, "total_moves": 0}

        # Display startup information (v1.2.25 - condensed)
        if not is_script_mode:
            # Compact status line: greeting + key stats
            greeting = user_manager.get_user_greeting()
            conn_status = connection.get_mode()
            viewport_info = f"{viewport.width}×{viewport.height}"
            device_type = viewport.device_type.upper()
            moves_info = f"{move_stats['total_moves']} moves"

            print(f"\n{greeting}")
            print(f"{conn_status}  │  {viewport_info} {device_type}  │  {moves_info}")

            # Check lifespan status
            lifespan_status = user_manager.check_lifespan_status(
                move_stats["total_moves"]
            )
            if lifespan_status["status"] != "OK":
                print(f"⏳ {lifespan_status['message']}")

        command_handler = CommandHandler(
            history=history,
            connection=connection,
            viewport=viewport,
            user_manager=user_manager,
            command_history=command_history,
            logger=logger,
        )

        if is_script_mode:
            script_path = sys.argv[1]
            run_script(
                script_path, parser, grid, command_handler, logger, command_history
            )
            return 0

        project_name = (
            story_data.get("STORY", {}).get("PROJECT_NAME", "uDOS")
            if story_data
            else "uDOS"
        )

        # Initialize smart prompt with autocomplete and viewport
        smart_prompt = SmartPrompt(
            command_history=command_history,
            theme="default",
            viewport=viewport  # Pass detected viewport for dynamic header width
        )

        # Initialize TUI controller (v1.2.15)
        tui_config = get_tui_config()
        tui = TUIController(config=tui_config.settings)

        # Pass TUI controller to SmartPrompt for integration
        smart_prompt.set_tui_controller(tui)

        # Command loading already shown by startup script (start_udos.sh)
        print()  # Blank line before prompt

        # Initialize prompt decorator for themed prompts
        prompt_decorator = get_prompt_decorator(theme="default")

        # OPTIONAL: Web GUI Extension - API Server
        # Only loads if explicitly enabled in user settings
        # CLI functionality is complete without this
        api_server_started = False
        try:
            user_data = user_manager.get_user_data()
            if user_data.get("settings", {}).get("api_server_enabled", False):
                # Try to load API server extension (not in core)
                from extensions.api.manager import APIServerManager

                print("🌐 Starting Web GUI API server...", end=" ", flush=True)
                api_manager = APIServerManager(port=5001, auto_restart=True)
                if api_manager.start_server():
                    api_server_started = True
                    print("✓ http://localhost:5001")
                else:
                    print("❌ Failed (continuing in CLI mode)")
        except ImportError:
            # Extension not installed - CLI works fine without it
            pass
        except Exception as e:
            # Extension failed to load - not critical for CLI
            pass

        print()  # Blank line before prompt

        # Connect TUI controller to command handler (v1.2.15)
        command_handler.tui_handler.tui = tui

        last_command = None

        while True:
            try:
                if command_handler.reboot_requested:
                    print("\n🔄 Restarting uDOS...\n")
                    os.execv(sys.executable, ["python"] + sys.argv)

                # Generate smart prompt string with flash effect
                # Note: Flash disabled by default to preserve terminal scrollback
                # Set flash=True below if you want the animated prompt
                is_assist = user_manager.is_assist_mode()

                # Check DEV MODE status (v1.5.0)
                dev_mode_active = False
                try:
                    from dev.goblin.core.services.dev_mode_manager import get_dev_mode_manager

                    dev_mode_mgr = get_dev_mode_manager()
                    dev_mode_active = dev_mode_mgr.is_active
                except Exception:
                    pass  # DEV MODE not available, continue normally

                prompt_string = prompt_decorator.get_prompt(
                    is_assist_mode=is_assist,
                    panel_name=grid.selected_panel,
                    flash=False,  # Changed from True - preserves scrollback
                    dev_mode=dev_mode_active,  # v1.5.0: Show 🔧 DEV indicator
                )

                # Show context hints if available
                hint = prompt_decorator.get_context_hint(
                    last_command=last_command,
                    panel_content_length=len(grid.get_panel(grid.selected_panel) or ""),
                )
                if hint:
                    print(hint)

                # Use new SmartPrompt with autocomplete (v1.0.19)
                # Check if we have a character from pager exit
                if (
                    hasattr(command_handler, "_pager_char")
                    and command_handler._pager_char
                ):
                    # Use the stored character as default
                    user_input = smart_prompt.ask_with_default(
                        prompt_text=prompt_string, default=command_handler._pager_char
                    )
                    command_handler._pager_char = None  # Clear after use
                else:
                    user_input = smart_prompt.ask(prompt_text=prompt_string)

                # Handle TUI dev browser mode (v1.2.19)
                if tui and tui.mode == "dev_browser":
                    # Render dev browser
                    print("\n" + tui.system_browser.render())
                    continue

                # Handle TUI debug panel mode (v1.2.19)
                if tui and tui.mode == "debug_panel":
                    # Render debug panel
                    print("\n" + tui.debug_panel.render())
                    continue

                # Handle TUI test panel mode (v1.2.19)
                if tui and tui.mode == "test_panel":
                    # Render testing interface
                    print("\n" + tui.testing_interface.render())
                    continue

                # Handle TUI workflow panel mode (v1.2.20)
                if tui and tui.mode == "workflow_panel":
                    # Render workflow manager
                    print_formatted_text(tui.workflow_manager.render())

                    # Get user input for workflow panel
                    panel_input = smart_prompt.ask(prompt_text="Workflow> ")
                    result = tui.workflow_manager.handle_input(panel_input)

                    if result == "close":
                        tui.close_workflow_panel()

                    continue

                # Handle TUI OK assistant panel mode (v1.2.21)
                if tui and tui.mode == "ok_panel":
                    # Render OK assistant panel
                    print("\n" + tui.ok_panel.render())

                    # Get user input for OK panel
                    panel_input = smart_prompt.ask(prompt_text="OK> ")

                    # Handle panel commands
                    if panel_input.strip().upper() in (
                        "ESC",
                        "ESCAPE",
                        "EXIT",
                        "CLOSE",
                    ):
                        tui.close_ok_panel()
                    elif panel_input.strip().upper() == "C":
                        tui.ok_panel.clear_history()
                        print("✓ Conversation history cleared")
                    elif panel_input.strip().upper() == "P":
                        tui.ok_panel.view_mode = "prompts"
                    elif panel_input.strip().upper() == "H":
                        tui.ok_panel.view_mode = "history"
                    elif panel_input.strip():
                        # Execute OK command
                        ucode = parser.parse(panel_input)
                        result = command_handler.execute_ucode(ucode, grid, parser)
                        print(result)

                    continue

                # Handle TUI config panel mode (v1.2.18)
                if tui and tui.mode == "config_panel":
                    # Render config panel
                    print("\n" + tui.config_browser.render())
                    continue

                # Handle TUI browser mode (v1.2.16)
                if tui and tui.mode == "browser":
                    # Check if file operation menu requested (5-key on file)
                    browser_action = getattr(smart_prompt, "_last_browser_action", None)
                    if (
                        browser_action
                        and browser_action.get("action") == "show_file_menu"
                    ):
                        # Display file operation menu
                        file_info = browser_action["file"]
                        print(f"\n📄 {file_info['name']} ({file_info['size']} bytes)")
                        print("─" * 60)
                        print("File Operations:")
                        print("  O - Open/View")
                        print("  C - Copy")
                        print("  M - Move/Rename")
                        print("  D - Delete")
                        print("  ESC - Cancel")
                        print("─" * 60)

                        # Get operation choice
                        op_input = smart_prompt.ask(prompt_text="Operation> ")

                        if op_input.upper() == "O":
                            # Open file
                            result = tui.perform_file_operation("open")
                            if result and not result.get("error"):
                                print(f"✓ Opening: {result['path']}")
                                # TODO: Integrate with FILE READ command
                                try:
                                    content = Path(result["path"]).read_text()
                                    print("\n" + content)
                                except Exception as e:
                                    print(f"❌ Error reading file: {e}")
                        elif op_input.upper() == "C":
                            # Copy file
                            dest = smart_prompt.ask(prompt_text="Copy to> ")
                            result = tui.perform_file_operation(
                                "copy", destination=Path(dest)
                            )
                            if result.get("success"):
                                print(f"✓ Copied to: {result['destination']}")
                            elif result.get("error"):
                                print(f"❌ {result['error']}")
                        elif op_input.upper() == "M":
                            # Move/rename file
                            dest = smart_prompt.ask(prompt_text="Move to> ")
                            result = tui.perform_file_operation(
                                "move", destination=Path(dest)
                            )
                            if result.get("success"):
                                print(f"✓ Moved to: {result['destination']}")
                            elif result.get("error"):
                                print(f"❌ {result['error']}")
                        elif op_input.upper() == "D":
                            # Delete file (with confirmation)
                            result = tui.perform_file_operation("delete", confirm=False)
                            if result.get("needs_confirmation"):
                                confirm = smart_prompt.ask(
                                    prompt_text=f"Delete {result['name']}? (yes/no)> "
                                )
                                if confirm.lower() == "yes":
                                    result = tui.perform_file_operation(
                                        "delete", confirm=True
                                    )
                                    if result.get("success"):
                                        print(f"✓ Deleted: {result['name']}")
                                    elif result.get("error"):
                                        print(f"❌ {result['error']}")
                                else:
                                    print("Cancelled")

                        # Clear action and continue browser
                        smart_prompt._last_browser_action = None
                        print("\n" + tui.render_current_view())
                        continue
                    else:
                        # Normal browser display (navigation)
                        print("\n" + tui.render_current_view())
                        continue

                # Skip empty input (happens with piped input at EOF)
                if not user_input or not user_input.strip():
                    # Check if we're at EOF with piped input
                    if not sys.stdin.isatty():
                        # Non-interactive stdin reached EOF - exit gracefully
                        break
                    continue

                logger.debug(f"INPUT: {user_input}")

                if user_input.lower() == "exit":
                    break

                # Store for smart hints
                last_command = user_input

                ucode = parser.parse(user_input)

                # Note: DEV MODE permission checks moved to file operations
                # Commands like REPAIR, DESTROY work for all users on memory/ files
                # Only core/knowledge/extensions require DEV MODE

                result = command_handler.execute_ucode(ucode, grid, parser)

                # Track command usage
                try:
                    # Parse the ucode to extract command and params
                    parts = ucode.strip("[]").split("|")
                    if len(parts) >= 2:
                        command_parts = parts[1].split("*")
                        command = command_parts[0].upper()
                        params = command_parts[1:] if len(command_parts) > 1 else []

                        # Track the command (success if we got a result)
                        command_handler.system_handler.usage_tracker.track_command(
                            command=command,
                            params=params,
                            success=(
                                result is not None
                                and "ERROR" not in result.upper()[:50]
                            ),
                        )
                except:
                    pass  # Silently ignore tracking errors

                if result:
                    logger.debug(f"OUTPUT: {result}")

                    # Non-blocking pager: activate pager mode if output exceeds viewport
                    result_lines = result.split("\n")
                    terminal_height = viewport.height - 3  # Reserve space for prompt

                    if len(result_lines) > terminal_height and tui:
                        # Output exceeds viewport - enter paging loop
                        # Update pager viewport to match terminal height
                        tui.pager.state.viewport_height = terminal_height
                        tui.set_pager_content(result_lines)

                        # Calculate pages using terminal viewport height
                        from dev.goblin.core.utils.pager import ScrollDirection

                        page_height = int(terminal_height)
                        total_pages = int(
                            (len(result_lines) + page_height - 1) // page_height
                        )

                        # Render page with progress bar and prompt
                        def render_page():
                            # Calculate current page based on visible content position
                            offset = tui.pager.state.offset
                            max_offset = tui.pager.state.max_offset

                            # Special case: if at max offset (end of content), we're on the last page
                            if offset >= max_offset and max_offset > 0:
                                current_page = total_pages
                            else:
                                # Page number is 1-based
                                current_page = (offset // page_height) + 1

                            page_content = tui.pager.render(style="minimal")

                            # Progress bar (only shown live, flows with pages)
                            bar_width = 40
                            filled = (current_page * bar_width) // total_pages
                            progress_bar = (
                                "┌─ "
                                + ("█" * filled)
                                + ("░" * (bar_width - filled))
                                + " ─┐"
                            )
                            page_info = f"Page {current_page}/{total_pages}  •  8↑ 2↓ 4← 6→ = Navigate  •  Any key = Exit"

                            # Show page content (flows naturally, no screen clear)
                            # Clear previous progress bar (cursor is at end of page_info line)
                            # Go to start of line, move up 2 lines, then clear to end of screen
                            print(
                                "\r\033[2A\033[J", end=""
                            )  # Return to start, up 2 lines, clear to end
                            print(page_content)

                            # Show progress bar at bottom (will be cleared on next render)
                            print("\n" + progress_bar)
                            print(page_info, end="", flush=True)

                            # Auto-exit if we're on the last page
                            if current_page >= total_pages:
                                return True  # Signal to exit pager
                            return False

                        # Initial render - auto-exit if on last page
                        if render_page():
                            print("\n")  # Just newline after last page
                            continue

                        # Paging loop: handle navigation until user exits
                        import termios
                        import tty

                        while tui.mode == "pager":
                            try:
                                # Get single keypress
                                fd = sys.stdin.fileno()
                                old_settings = termios.tcgetattr(fd)
                                try:
                                    tty.setraw(fd)
                                    ch = sys.stdin.read(1)

                                    # Handle escape sequences (arrow keys)
                                    if ch == "\x1b":
                                        seq = sys.stdin.read(2)
                                        if seq == "[A":  # Up arrow
                                            ch = "8"
                                        elif seq == "[B":  # Down arrow
                                            ch = "2"
                                        elif seq == "[D":  # Left arrow
                                            ch = "4"
                                        elif seq == "[C":  # Right arrow
                                            ch = "6"
                                finally:
                                    termios.tcsetattr(
                                        fd, termios.TCSADRAIN, old_settings
                                    )

                                # Handle paging keys (all 4 directions work for paging)
                                if ch in ["8", "4"]:  # Up or Left = Previous page
                                    tui.pager.scroll(ScrollDirection.PAGE_UP)
                                    if render_page():
                                        print("\n")  # Just newline
                                        break
                                elif ch in ["2", "6"]:  # Down or Right = Next page
                                    # Check if we're already at the last page
                                    current_page = (
                                        tui.pager.state.offset // page_height
                                    ) + 1
                                    if current_page >= total_pages:
                                        # Already at last page - exit pager
                                        tui.mode = "command"
                                        print("\n")  # Just newline
                                        break
                                    else:
                                        tui.pager.scroll(ScrollDirection.PAGE_DOWN)
                                        if render_page():
                                            print("\n")  # Just newline
                                            break
                                else:
                                    # Any other key exits pager - don't clear screen, show key in prompt
                                    tui.mode = "command"
                                    # Store character for next prompt (if printable)
                                    if ch.isprintable():
                                        # Store in a place smart_prompt can access
                                        if not hasattr(command_handler, "_pager_char"):
                                            command_handler._pager_char = None
                                        command_handler._pager_char = ch
                                    print("\n")  # Newline to separate from pager
                                    break
                            except (KeyboardInterrupt, EOFError):
                                tui.mode = "command"
                                print("\n")  # Newline but don't clear
                                break
                    else:
                        # Output fits - display normally
                        print(result)

                    # Show command chain hint
                    chain_hint = smart_prompt.format_command_chain_hint(user_input)
                    if chain_hint:
                        print(chain_hint)

                if (
                    user_manager.is_assist_mode()
                    and not command_handler.reboot_requested
                ):
                    suggestion = command_handler.offline_engine.generate_response(
                        "What should I do next?", context=result
                    )
                    if suggestion and not suggestion.startswith("I don't"):
                        print(f"\n💡 {suggestion}\n")

            except KeyboardInterrupt:
                logger.info("EVENT: KeyboardInterrupt")
                print(f"\n{command_handler.get_message('INFO_EXIT')}")
                break
            except EOFError:
                logger.info("EVENT: EOFError")
                print(f"\n{command_handler.get_message('INFO_EXIT')}")
                break
            except BrokenPipeError:
                # Handle pipe errors gracefully (e.g., when piping to head/tail)
                logger.info("EVENT: BrokenPipeError (handled)")
                # Silence the error - this is normal when output is piped
                sys.stderr.close()
                break
            except IOError as e:
                # Handle other I/O errors gracefully
                if e.errno == 32:  # EPIPE
                    logger.info("EVENT: EPIPE (handled)")
                    sys.stderr.close()
                    break
                else:
                    logger.error(f"ERROR: IOError: {e}")
                    print(command_handler.get_message("ERROR_GENERIC", error=str(e)))
            except Exception as e:
                # Check if this is a normal termination condition
                error_str = str(e).lower()
                if any(
                    term in error_str for term in ["eof", "closed", "input", "terminal"]
                ):
                    # Likely end of piped input or terminal closed - exit gracefully
                    logger.info(f"EVENT: Terminal condition: {e}")
                    break

                # Otherwise log and display error with recovery suggestions
                logger.error(str(e))
                error_msg = format_command_error(
                    e, command=user_input, show_traceback=True
                )
                print(error_msg)

                # Self-healing attempt for recoverable errors
                if "connection" in error_str or "timeout" in error_str:
                    print("🔧 Attempting self-heal...")
                    try:
                        connection = ConnectionMonitor()
                        command_handler.connection = connection
                        print("✅ Connection reset successful")
                    except:
                        print("⚠️  Self-heal failed - continuing anyway")

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        return 0
    except Exception as e:
        from .utils.error_helper import format_startup_error

        error_msg = format_startup_error(e, component="Main System")
        print(error_msg)
        return 1

    return 0


# Signal handler for graceful shutdown
def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    import signal

    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully"""
        print("\n\n👋 Shutting down gracefully...")
        sys.exit(0)

    # Handle common signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Handle SIGPIPE (broken pipe) by ignoring it
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)


if __name__ == "__main__":
    setup_signal_handlers()
    sys.exit(main())
