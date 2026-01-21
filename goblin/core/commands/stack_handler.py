"""
uDOS Stack Command Handler
==========================
TUI commands for managing installation stacks.

Commands:
    STACK LIST              - List available stacks
    STACK INFO <name>       - Show stack details
    STACK CHECK <name>      - Check requirements
    STACK COMPARE           - Compare all stacks
    STACK INSTALL <name>    - Install a stack
    STACK STATUS            - Show current installation
    STACK HELP              - Show help

Author: uDOS Team
Version: v1.0.0.13
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("command-stack")


class StackHandler:
    """Handler for STACK commands."""

    def __init__(self, workspace_root: Optional[str] = None):
        """Initialize the stack handler."""
        if workspace_root:
            self.workspace_root = Path(workspace_root).resolve()
        else:
            self.workspace_root = Path.cwd()

        self._installer = None

    @property
    def installer(self):
        """Lazy load the stack installer."""
        if self._installer is None:
            from dev.goblin.core.services.stack_installer import StackInstaller

            self._installer = StackInstaller(str(self.workspace_root))
        return self._installer

    def handle_command(self, args: List[str]) -> Dict[str, Any]:
        """
        Handle a STACK command.

        Args:
            args: Command arguments (e.g., ['LIST'] or ['INFO', 'lite'])

        Returns:
            Dict with 'success', 'content', 'error' keys
        """
        if not args:
            return self._handle_help()

        subcommand = args[0].upper()
        params = args[1:] if len(args) > 1 else []

        handlers = {
            "LIST": self._handle_list,
            "INFO": self._handle_info,
            "CHECK": self._handle_check,
            "COMPARE": self._handle_compare,
            "INSTALL": self._handle_install,
            "STATUS": self._handle_status,
            "HELP": self._handle_help,
        }

        handler = handlers.get(subcommand)
        if handler:
            try:
                return handler(params)
            except Exception as e:
                logger.error(f"[ERROR] STACK {subcommand} failed: {e}")
                return {"success": False, "error": str(e), "content": f"Error: {e}"}
        else:
            return {
                "success": False,
                "error": f"Unknown subcommand: {subcommand}",
                "content": f"Unknown STACK subcommand: {subcommand}\nUse STACK HELP for available commands.",
            }

    def _handle_list(self, params: List[str]) -> Dict[str, Any]:
        """List available stacks."""
        stacks = self.installer.list_stacks()

        if not stacks:
            return {
                "success": True,
                "content": "No stacks defined. Check distribution/stacks/stacks.json",
            }

        lines = [
            "╔══════════════════════════════════════════════════════════════════════╗",
            "║                    Available Installation Stacks                     ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
        ]

        for stack in stacks:
            default_mark = " ★" if stack.is_default else "  "
            realm_mark = f" [{stack.realm}]" if stack.realm else ""
            lines.append(
                f"║  {stack.id:<10}{default_mark} │ {stack.name:<12} │ {stack.size_mb:>4}MB{realm_mark:<10}  ║"
            )
            # Truncate description if too long
            desc = (
                stack.description[:52]
                if len(stack.description) > 52
                else stack.description
            )
            lines.append(f"║               │ {desc:<48}  ║")
            lines.append(
                f"╟──────────────┼──────────────────────────────────────────────────────╢"
            )

        # Remove last separator and close
        lines[-1] = (
            "╚══════════════════════════════════════════════════════════════════════╝"
        )

        lines.append("")
        lines.append("★ = Default stack    Use STACK INFO <name> for details")

        return {"success": True, "content": "\n".join(lines)}

    def _handle_info(self, params: List[str]) -> Dict[str, Any]:
        """Show stack details."""
        if not params:
            return {
                "success": False,
                "error": "Stack name required",
                "content": "Usage: STACK INFO <name>\nExample: STACK INFO lite",
            }

        stack_id = params[0].lower()
        details = self.installer.get_stack_details(stack_id)

        return {"success": True, "content": details}

    def _handle_check(self, params: List[str]) -> Dict[str, Any]:
        """Check stack requirements."""
        stack_id = params[0].lower() if params else "lite"
        stack = self.installer.get_stack(stack_id)

        if not stack:
            return {
                "success": False,
                "error": f"Stack not found: {stack_id}",
                "content": f"Stack '{stack_id}' not found. Use STACK LIST to see available stacks.",
            }

        result = self.installer.check_requirements(stack_id)

        lines = [
            f"╔══════════════════════════════════════════════════════════════╗",
            f"║  Requirements Check: {stack.name:<37}  ║",
            f"╠══════════════════════════════════════════════════════════════╣",
        ]

        status = (
            "✅ All requirements met" if result["met"] else "❌ Missing requirements"
        )
        lines.append(f"║  Status: {status:<49}  ║")

        if result["missing"]:
            lines.append(
                f"╠══════════════════════════════════════════════════════════════╣"
            )
            lines.append(
                f"║  Missing:                                                    ║"
            )
            for item in result["missing"]:
                lines.append(f"║    ❌ {item:<52}  ║")

        if result["warnings"]:
            lines.append(
                f"╠══════════════════════════════════════════════════════════════╣"
            )
            lines.append(
                f"║  Warnings:                                                   ║"
            )
            for item in result["warnings"]:
                lines.append(f"║    ⚠️  {item:<51}  ║")

        lines.append(
            f"╚══════════════════════════════════════════════════════════════╝"
        )

        return {
            "success": True,
            "content": "\n".join(lines),
            "requirements_met": result["met"],
        }

    def _handle_compare(self, params: List[str]) -> Dict[str, Any]:
        """Compare all stacks."""
        comparison = self.installer.get_stack_comparison()

        return {"success": True, "content": comparison}

    def _handle_install(self, params: List[str]) -> Dict[str, Any]:
        """Install a stack."""
        stack_id = params[0].lower() if params else "lite"
        stack = self.installer.get_stack(stack_id)

        if not stack:
            return {
                "success": False,
                "error": f"Stack not found: {stack_id}",
                "content": f"Stack '{stack_id}' not found. Use STACK LIST to see available stacks.",
            }

        # Check requirements first
        req_check = self.installer.check_requirements(stack_id)
        if not req_check["met"]:
            missing = ", ".join(req_check["missing"])
            return {
                "success": False,
                "error": "Requirements not met",
                "content": f"Cannot install {stack.name}: missing {missing}\nUse STACK CHECK {stack_id} for details.",
            }

        # Progress tracking
        progress_lines = []

        def progress_callback(progress):
            msg = f"[{progress.current_step}/{progress.total_steps}] {progress.status}"
            progress_lines.append(msg)
            logger.info(f"[LOCAL] STACK INSTALL: {msg}")

        self.installer.progress_callback = progress_callback

        # Install
        skip_deps = "--skip-deps" in params
        from dev.goblin.core.services.stack_installer import InstallResult

        result = self.installer.install_stack(stack_id, skip_deps=skip_deps)

        lines = [
            f"╔══════════════════════════════════════════════════════════════╗",
            f"║  Stack Installation: {stack.name:<37}  ║",
            f"╠══════════════════════════════════════════════════════════════╣",
        ]

        for pl in progress_lines:
            lines.append(f"║  {pl:<56}  ║")

        lines.append(
            f"╠══════════════════════════════════════════════════════════════╣"
        )

        if result == InstallResult.SUCCESS:
            lines.append(
                f"║  ✅ Installation completed successfully                       ║"
            )
        elif result == InstallResult.PARTIAL:
            lines.append(
                f"║  ⚠️  Installation completed with warnings                      ║"
            )
        else:
            lines.append(
                f"║  ❌ Installation failed                                        ║"
            )

        lines.append(
            f"╚══════════════════════════════════════════════════════════════╝"
        )

        return {
            "success": result in [InstallResult.SUCCESS, InstallResult.PARTIAL],
            "content": "\n".join(lines),
            "result": result.value,
        }

    def _handle_status(self, params: List[str]) -> Dict[str, Any]:
        """Show current installation status."""
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║                    Stack Installation Status                 ║",
            "╠══════════════════════════════════════════════════════════════╣",
        ]

        # System info
        system_type = self.installer.system_type
        lines.append(f"║  System Type: {system_type:<44}  ║")
        lines.append(f"║  Workspace:   {str(self.workspace_root)[:44]:<44}  ║")

        # Check what's installed
        lines.append(
            f"╠══════════════════════════════════════════════════════════════╣"
        )
        lines.append(
            f"║  Installed Components:                                       ║"
        )

        # Quick check for core components
        components_installed = []
        if (self.workspace_root / "core").exists():
            components_installed.append("core")
        if (self.workspace_root / "knowledge").exists():
            components_installed.append("knowledge")
        if (self.workspace_root / "extensions" / "api").exists():
            components_installed.append("api")
        if (self.workspace_root / "extensions" / "transport").exists():
            components_installed.append("transport")
        if (self.workspace_root / "extensions" / "cloud").exists():
            components_installed.append("cloud")
        if (self.workspace_root / "extensions" / "wizard_server").exists():
            components_installed.append("wizard")

        for comp in components_installed:
            lines.append(f"║    ✅ {comp:<52}  ║")

        if not components_installed:
            lines.append(
                f"║    (none detected)                                           ║"
            )

        lines.append(
            f"╚══════════════════════════════════════════════════════════════╝"
        )

        return {
            "success": True,
            "content": "\n".join(lines),
            "system_type": system_type,
            "components": components_installed,
        }

    def _handle_help(self, params: List[str] = None) -> Dict[str, Any]:
        """Show help information."""
        help_text = """
╔══════════════════════════════════════════════════════════════════════════╗
║                         STACK Command Help                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║  STACK LIST                List available installation stacks            ║
║  STACK INFO <name>         Show detailed stack information               ║
║  STACK CHECK <name>        Check if requirements are met                 ║
║  STACK COMPARE             Side-by-side comparison of all stacks         ║
║  STACK INSTALL <name>      Install a stack (use --skip-deps for no pip)  ║
║  STACK STATUS              Show current installation status              ║
║  STACK HELP                Show this help                                ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Available Stacks:                                                       ║
║    ultra      - Minimal core (8MB)                                       ║
║    lite       - Core + Knowledge (16MB) ★ DEFAULT                        ║
║    standard   - Lite + AI (28MB)                                         ║
║    full       - Complete system (58MB)                                   ║
║    enterprise - Full + Cloud/BI (120MB)                                  ║
║    wizard     - Wizard Server (95MB) - Always-on web gateway             ║
║    mobile     - Mobile Console (4MB) - Pairing client                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Examples:                                                               ║
║    STACK INFO full         Show what's in the Full stack                 ║
║    STACK CHECK standard    Check requirements for Standard               ║
║    STACK INSTALL lite      Install the Lite stack                        ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
        return {"success": True, "content": help_text.strip()}


# For direct testing
if __name__ == "__main__":
    handler = StackHandler()

    print("=== STACK LIST ===")
    result = handler.handle_command(["LIST"])
    print(result["content"])
    print()

    print("=== STACK INFO lite ===")
    result = handler.handle_command(["INFO", "lite"])
    print(result["content"])
    print()

    print("=== STACK COMPARE ===")
    result = handler.handle_command(["COMPARE"])
    print(result["content"])
