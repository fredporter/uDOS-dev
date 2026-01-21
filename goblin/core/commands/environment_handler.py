"""
uDOS v1.1.12 - Environment Command Handler

Handles environment and workspace management: CLEAN, SETTINGS, DEV MODE
Manages archive cleanup, system configuration, and development mode access.
"""

from pathlib import Path
from .base_handler import BaseCommandHandler


class EnvironmentHandler(BaseCommandHandler):
    """Handler for environment and workspace management commands."""

    def handle_clean(self, params, grid, parser):
        """
        Clean workspace files and manage archives.

        Commands:
        - CLEAN              - Show archive system usage
        - CLEAN --scan       - Scan all .archive/ folders for statistics
        - CLEAN --purge [N]  - Purge old archive files (default: 30 days)
        - CLEAN --dry-run    - Preview what would be purged
        - CLEAN --path <dir> - Clean specific directory's .archive/

        Returns:
            Cleanup results or interactive review
        """
        try:
            # Parse flags
            scan_mode = '--scan' in params
            purge_mode = '--purge' in params
            dry_run = '--dry-run' in params

            # Get custom path if specified
            custom_path = None
            if '--path' in params:
                idx = params.index('--path')
                if idx + 1 < len(params):
                    custom_path = Path(params[idx + 1])

            # Get custom retention days if specified with --purge
            retention_days = 30  # default
            if purge_mode:
                idx = params.index('--purge')
                if idx + 1 < len(params) and params[idx + 1].isdigit():
                    retention_days = int(params[idx + 1])

            # Route to appropriate handler
            if scan_mode:
                return self._clean_scan_archives(custom_path)
            elif purge_mode or dry_run:
                return self._clean_purge_archives(retention_days, dry_run, custom_path)
            else:
                # Show deprecation notice for legacy sandbox
                return self._clean_deprecated_notice()

        except Exception as e:
            return self.output_formatter.format_error(
                "Clean operation failed",
                error_details=str(e)
            )

    def _clean_deprecated_notice(self):
        """Show notice that sandbox is deprecated."""
        return self.output_formatter.format_panel(
            "CLEAN - Sandbox Deprecated",
            "⚠️  The sandbox/ directory has been deprecated in favor of memory/\n\n" +
            "New structure:\n" +
            "  • memory/logs/           - All log files\n" +
            "  • memory/bank/user/      - User data (user.json)\n" +
            "  • memory/bank/system/    - System config\n" +
            "  • memory/bank/data/      - Application data\n" +
            "  • memory/shared/groups/  - Group workspaces\n" +
            "  • memory/shared/public/  - Public content\n\n" +
            "Archive system:\n" +
            "  • Use --scan to view archive health across workspace\n" +
            "  • Use --purge [days] to clean old backups\n" +
            "  • All directories support .archive/ folders\n\n" +
            "Old sandbox/ files have been moved to:\n" +
            "  • sandbox/.archive/user/ (archived)\n" +
            "  • sandbox/.archive/logs/ (archived)\n\n" +
            "💡 Use: CLEAN --scan    (view archive status)\n" +
            "       CLEAN --purge 30 (remove backups >30 days)",
            style="info"
        )

    def _clean_review_sandbox(self):
        """Legacy CLEAN behavior: deprecated."""
        return self._clean_deprecated_notice()

    def _clean_scan_archives(self, custom_path=None):
        """Scan workspace for .archive/ folders and show statistics."""
        from dev.goblin.core.utils.archive_manager import ArchiveManager

        # Determine scan path
        scan_path = custom_path if custom_path else Path.cwd()

        archive_mgr = ArchiveManager(scan_path)
        metrics = archive_mgr.get_health_metrics()

        if metrics['total_archives'] == 0:
            return self.output_formatter.format_info(
                f"No archives found in: {scan_path}"
            )

        # Build output
        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║         Archive System Health Report (v1.1.16)           ║",
            "╠═══════════════════════════════════════════════════════════╣",
            f"║  Total Archives: {metrics['total_archives']:<42} ║",
            f"║  Total Files:    {metrics['total_files']:<42} ║",
            f"║  Total Size:     {metrics['total_size_mb']:.2f} MB{' ' * (42 - len(f'{metrics['total_size_mb']:.2f} MB'))} ║",
            "╠═══════════════════════════════════════════════════════════╣"
        ]

        # Show individual archives
        lines.append("║  Archives:                                                ║")
        for archive in metrics['archives']:
            path_short = str(archive['path'])[-50:]
            lines.append(f"║  • {path_short:<55} ║")
            lines.append(f"║    Files: {archive['total_files']:<3}  Size: {archive['total_size_mb']:.2f} MB{' ' * (35 - len(f'{archive['total_size_mb']:.2f} MB'))} ║")

        # Show warnings
        if metrics['warnings']:
            lines.append("╠═══════════════════════════════════════════════════════════╣")
            lines.append("║  ⚠️  Warnings:                                             ║")
            for warning in metrics['warnings']:
                # Wrap long warnings
                if len(warning) > 55:
                    warning = warning[:52] + "..."
                lines.append(f"║  {warning:<57} ║")

        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append("║  Commands:                                                ║")
        lines.append("║  CLEAN --purge [days]  - Remove old archive files         ║")
        lines.append("║  CLEAN --dry-run       - Preview what would be deleted    ║")
        lines.append("║  CLEAN --path <dir>    - Clean specific directory         ║")
        lines.append("╚═══════════════════════════════════════════════════════════╝")

        return '\n'.join(lines)

    def _clean_purge_archives(self, retention_days=30, dry_run=False, custom_path=None):
        """Purge old files from archives."""
        from dev.goblin.core.utils.archive_manager import ArchiveManager
        from datetime import datetime

        # Determine scan path
        scan_path = custom_path if custom_path else Path.cwd()

        archive_mgr = ArchiveManager(scan_path)
        archives = archive_mgr.scan_archives(scan_path)

        if not archives:
            return self.output_formatter.format_info(
                f"No archives found to purge in: {scan_path}"
            )

        # Purge each archive
        total_purged = {"deleted": 0, "backups": 0, "versions": 0}
        purge_details = []

        for archive_stats in archives:
            archive_path = Path(archive_stats['path'])
            purged = archive_mgr.purge_old_files(archive_path, dry_run=dry_run)

            # Count totals
            for category in purged:
                total_purged[category] += len(purged[category])

            # Record details if files were purged
            if any(purged.values()):
                purge_details.append({
                    'path': str(archive_path),
                    'purged': purged
                })

        # Build output
        mode_text = "DRY RUN - Would purge" if dry_run else "Purged"
        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            f"║  Archive Cleanup Report ({mode_text}){' ' * (23 - len(mode_text))} ║",
            "╠═══════════════════════════════════════════════════════════╣",
            f"║  Retention Policy: {retention_days} days{' ' * (38 - len(str(retention_days)))} ║",
            f"║  Archives Scanned: {len(archives):<39} ║",
            "╠═══════════════════════════════════════════════════════════╣",
            f"║  Deleted Files:  {total_purged['deleted']:<42} ║",
            f"║  Backup Files:   {total_purged['backups']:<42} ║",
            f"║  Version Files:  {total_purged['versions']:<42} ║",
            f"║  Total:          {sum(total_purged.values()):<42} ║"
        ]

        # Show details
        if purge_details:
            lines.append("╠═══════════════════════════════════════════════════════════╣")
            lines.append("║  Details:                                                 ║")
            for detail in purge_details:
                path_short = str(detail['path'])[-50:]
                lines.append(f"║  • {path_short:<55} ║")
                for category, files in detail['purged'].items():
                    if files:
                        lines.append(f"║    {category}: {len(files)} file(s){' ' * (41 - len(category) - len(str(len(files))))} ║")

        lines.append("╠═══════════════════════════════════════════════════════════╣")
        if dry_run:
            lines.append("║  💡 Run without --dry-run to actually delete files        ║")
        else:
            lines.append("║  ✅ Cleanup complete                                      ║")
        lines.append("╚═══════════════════════════════════════════════════════════╝")

        return '\n'.join(lines)

    def handle_settings(self, params, grid, parser):
        """
        Manage system settings.
        Delegates to ConfigurationHandler.handle_setup() for settings management.
        SETTINGS is an alias - primary command is now CONFIG.
        """
        from .configuration_handler import ConfigurationHandler

        config_handler = ConfigurationHandler(
            theme=self.theme,
            viewport=self.viewport,
            logger=self.logger,
            input_manager=getattr(self, 'input_manager', None),
            output_formatter=getattr(self, 'output_formatter', None),
            resource_manager=getattr(self, 'resource_manager', None)
        )
        return config_handler.handle_setup(params, grid, parser)

    def handle_dev_mode(self, params, grid, parser):
        """
        Handle DEV MODE commands (v1.5.0 - Master User Only).

        Commands:
        - DEV MODE ON: Enable DEV MODE (requires master password)
        - DEV MODE OFF: Disable DEV MODE
        - DEV MODE STATUS: Show current DEV MODE status
        - DEV MODE SETUP: Interactive wizard to configure credentials
        - DEV MODE HELP: Show DEV MODE help

        Args:
            params: Command parameters ['MODE', 'ON'/'OFF'/'STATUS'/'SETUP'/'HELP']
            grid: Grid instance
            parser: Parser instance

        Returns:
            Command result message
        """
        # Validate params
        if not params or len(params) < 2:
            return (
                "❌ Invalid DEV MODE command\n\n"
                "Usage:\n"
                "  DEV MODE ON      - Enable DEV MODE (master user only)\n"
                "  DEV MODE OFF     - Disable DEV MODE\n"
                "  DEV MODE STATUS  - Show current status\n"
                "  DEV MODE SETUP   - Configure master credentials\n"
                "  DEV MODE HELP    - Show detailed help"
            )

        # Parse subcommand
        if params[0].upper() != 'MODE':
            return "❌ Invalid DEV command - did you mean 'DEV MODE'?"

        subcommand = params[1].upper()

        # Route to appropriate handler
        if subcommand == 'ON':
            return self._dev_mode_enable()
        elif subcommand == 'OFF':
            return self._dev_mode_disable()
        elif subcommand == 'STATUS':
            return self._dev_mode_status()
        elif subcommand == 'SETUP':
            return self._dev_mode_setup(grid, parser)
        elif subcommand == 'HELP':
            return self._dev_mode_help()
        else:
            return f"❌ Unknown DEV MODE command: {subcommand}"

    def _dev_mode_enable(self) -> str:
        """Enable DEV MODE with password authentication."""
        success, message = self.dev_mode_manager.enable(interactive=True)
        return message

    def _dev_mode_disable(self) -> str:
        """Disable DEV MODE."""
        success, message = self.dev_mode_manager.disable()
        return message

    def _dev_mode_status(self) -> str:
        """Show current DEV MODE status."""
        status = self.dev_mode_manager.get_status()

        if not status['active']:
            return (
                "╔═══════════════════════════════════════╗\n"
                "║       DEV MODE Status                 ║\n"
                "╠═══════════════════════════════════════╣\n"
                f"║  Status: ❌ INACTIVE                  ║\n"
                f"║  Master User: {status['master_user']:<20} ║\n"
                "╚═══════════════════════════════════════╝\n\n"
                "💡 Enable with: DEV MODE ON"
            )

        return (
            "╔═══════════════════════════════════════╗\n"
            "║       DEV MODE Status                 ║\n"
            "╠═══════════════════════════════════════╣\n"
            f"║  Status: ✅ ACTIVE                    ║\n"
            f"║  User: {status['user']:<27} ║\n"
            f"║  Duration: {status['duration']:<23} ║\n"
            f"║  Commands: {status['commands_executed']:<23} ║\n"
            "╠═══════════════════════════════════════╣\n"
            "║  ⚠️  Unrestricted System Access       ║\n"
            "║  📝 All actions logged                ║\n"
            "╚═══════════════════════════════════════╝\n\n"
            f"📄 Log: {status['log_file']}"
        )

    def _dev_mode_help(self) -> str:
        """Show DEV MODE help information."""
        return (
            "╔═══════════════════════════════════════════════════════════╗\n"
            "║              DEV MODE - Master User Only                  ║\n"
            "╠═══════════════════════════════════════════════════════════╣\n"
            "║                                                           ║\n"
            "║  DEV MODE provides unrestricted access to:               ║\n"
            "║  • Dangerous system operations (DELETE, DESTROY, etc.)    ║\n"
            "║  • Development tools (debugger, profiler, test runner)    ║\n"
            "║  • Live Gemini AI coding assistance                      ║\n"
            "║  • Hot code reloading and system modification            ║\n"
            "║                                                           ║\n"
            "╠═══════════════════════════════════════════════════════════╣\n"
            "║  Commands:                                                ║\n"
            "║                                                           ║\n"
            "║  DEV MODE ON      Enable DEV MODE (password required)     ║\n"
            "║  DEV MODE OFF     Disable DEV MODE                        ║\n"
            "║  DEV MODE STATUS  Show current status                     ║\n"
            "║  DEV MODE SETUP   Configure master credentials (wizard)   ║\n"
            "║  DEV MODE HELP    Show this help                          ║\n"
            "║                                                           ║\n"
            "╠═══════════════════════════════════════════════════════════╣\n"
            "║  Security:                                                ║\n"
            "║                                                           ║\n"
            "║  • Requires master user credentials (config)              ║\n"
            "║  • All operations logged to memory/logs/dev_mode.log      ║\n"
            "║  • Session auto-expires after 1 hour of inactivity        ║\n"
            "║  • Never enable on production systems                     ║\n"
            "║                                                           ║\n"
            "╠═══════════════════════════════════════════════════════════╣\n"
            "║  Quick Setup:                                             ║\n"
            "║                                                           ║\n"
            "║  1. Run: DEV MODE SETUP                                   ║\n"
            "║  2. Follow the interactive wizard                         ║\n"
            "║  3. Run: DEV MODE ON                                      ║\n"
            "║  4. Enter master password when prompted                   ║\n"
            "║                                                           ║\n"
            "║  Manual Setup (alternative):                              ║\n"
            "║  • CONFIG SET PASSWORD <your-password>                    ║\n"
            "║  • CONFIG SET USERNAME <your-username>                    ║\n"
            "║                                                           ║\n"
            "╠═══════════════════════════════════════════════════════════╣\n"
            "║  ⚠️  WARNING:                                              ║\n"
            "║                                                           ║\n"
            "║  DEV MODE disables all safety restrictions. Use only      ║\n"
            "║  in controlled development environments. All actions      ║\n"
            "║  are irreversible and logged.                             ║\n"
            "║                                                           ║\n"
            "╚═══════════════════════════════════════════════════════════╝"
        )

    def _dev_mode_setup(self, grid, parser) -> str:
        """Interactive wizard to configure DEV MODE credentials."""
        from dev.goblin.core.uDOS_main import get_config
        config = get_config()
        
        output = []
        output.append("")
        output.append("╔═══════════════════════════════════════════════════════════╗")
        output.append("║         🔧 DEV MODE Setup Wizard (v1.2.26)                ║")
        output.append("╠═══════════════════════════════════════════════════════════╣")
        output.append("║                                                           ║")
        output.append("║  Welcome to the DEV MODE configuration wizard!            ║")
        output.append("║                                                           ║")
        output.append("║  This wizard will help you set up master user             ║")
        output.append("║  credentials for editing core system files.               ║")
        output.append("║                                                           ║")
        output.append("╚═══════════════════════════════════════════════════════════╝")
        output.append("")
        
        # Check current config
        current_username = config.get('USERNAME', '')
        current_password = config.get('PASSWORD', '')
        
        if current_username and current_password:
            output.append("⚠️  Master credentials already configured!")
            output.append("")
            output.append(f"Current master user: {current_username}")
            output.append("")
            output.append("💡 To reconfigure, use:")
            output.append("   CONFIG SET USERNAME <new-username>")
            output.append("   CONFIG SET PASSWORD <new-password>")
            output.append("")
            output.append("Or run: ./start_udos.sh (for interactive mode)")
            return "\n".join(output)
        
        # Story-style introduction
        output.append("📖 Chapter 1: Understanding DEV MODE")
        output.append("═" * 59)
        output.append("")
        output.append("In the uDOS survival OS, most files are read-only to protect")
        output.append("the integrity of the system. But sometimes, you need to modify")
        output.append("core system files, knowledge guides, or extensions.")
        output.append("")
        output.append("That's where DEV MODE comes in - a master key that grants")
        output.append("unrestricted access to the entire system.")
        output.append("")
        output.append("⚠️  With great power comes great responsibility!")
        output.append("")
        output.append("📖 Chapter 2: Configuration Required")
        output.append("═" * 59)
        output.append("")
        output.append("To enable DEV MODE, you need to configure:")
        output.append("  1. Master username (USERNAME)")
        output.append("  2. Master password (PASSWORD)")
        output.append("")
        output.append("These credentials will be stored securely in:")
        output.append("  memory/bank/user/user.json (encrypted)")
        output.append("")
        output.append("📖 Chapter 3: Setup Options")
        output.append("═" * 59)
        output.append("")
        output.append("Option A - Interactive Mode (Recommended):")
        output.append("  ./start_udos.sh")
        output.append("  uDOS> DEV MODE SETUP")
        output.append("  [Follow the wizard prompts]")
        output.append("")
        output.append("Option B - Manual Configuration:")
        output.append("  CONFIG SET USERNAME <your-username>")
        output.append("  CONFIG SET PASSWORD <your-password>")
        output.append("")
        output.append("Option C - Direct Edit:")
        output.append("  Edit memory/bank/user/user.json directly")
        output.append('  Add: "USERNAME": "your-name"')
        output.append('  Add: "PASSWORD": "your-password"')
        output.append("")
        output.append("╔═══════════════════════════════════════════════════════════╗")
        output.append("║                  📝 NEXT STEPS                             ║")
        output.append("╠═══════════════════════════════════════════════════════════╣")
        output.append("║                                                           ║")
        output.append("║  1. Choose a configuration method above                   ║")
        output.append("║  2. Set your USERNAME and PASSWORD                        ║")
        output.append("║  3. Run: DEV MODE ON                                      ║")
        output.append("║  4. Enter your password when prompted                     ║")
        output.append("║  5. You'll have unrestricted system access!               ║")
        output.append("║                                                           ║")
        output.append("╚═══════════════════════════════════════════════════════════╝")
        output.append("")
        
        return "\n".join(output)

    def _cloud_extensions_setup(self, params):
        """
        Interactive story-style wizard for cloud extension credentials.
        Supports Gmail, Google Drive, GitHub, Slack, and other cloud services.
        All credentials stored securely in .env file.
        """
        from dev.goblin.core.config import Config
        from pathlib import Path
        import os
        
        config = Config()
        env_path = Path('.env')
        
        output = []
        
        # Chapter 1: Introduction
        output.append("")
        output.append("╔═══════════════════════════════════════════════════════════╗")
        output.append("║                                                           ║")
        output.append("║  📖 Chapter 1: Cloud Extensions Setup                      ║")
        output.append("║                                                           ║")
        output.append("╚═══════════════════════════════════════════════════════════╝")
        output.append("")
        output.append("  Welcome to the Cloud Extensions Configuration Wizard!")
        output.append("")
        output.append("  uDOS supports integration with various cloud services:")
        output.append("    • Gmail - Email automation and management")
        output.append("    • Google Drive - Cloud storage and file sync")
        output.append("    • GitHub - Code repositories and version control")
        output.append("    • Slack - Team communication")
        output.append("")
        output.append("  All API keys and credentials will be stored securely in:")
        output.append("  📄 .env (gitignored, never committed)")
        output.append("")
        
        # Chapter 2: Service Selection
        output.append("╔═══════════════════════════════════════════════════════════╗")
        output.append("║                                                           ║")
        output.append("║  📖 Chapter 2: Choose Services to Configure                ║")
        output.append("║                                                           ║")
        output.append("╚═══════════════════════════════════════════════════════════╝")
        output.append("")
        output.append("  Which cloud services would you like to configure?")
        output.append("")
        output.append("  Available options:")
        output.append("    1. Gmail (email automation)")
        output.append("    2. Google Drive (cloud storage)")
        output.append("    3. GitHub (code repository)")
        output.append("    4. Slack (team messaging)")
        output.append("    5. All of the above")
        output.append("    6. Custom (I'll specify)")
        output.append("")
        
        # Interactive mode check
        try:
            choice = input("  Enter choice (1-6): ").strip()
        except (EOFError, OSError):
            output.append("  ⚠️  Interactive input required")
            output.append("  💡 Run this command in interactive mode:")
            output.append("     ./start_udos.sh")
            output.append("     uDOS> SETUP CLOUD")
            return "\n".join(output)
        
        # Determine which services to configure
        services = []
        if choice == '1':
            services = ['gmail']
        elif choice == '2':
            services = ['google_drive']
        elif choice == '3':
            services = ['github']
        elif choice == '4':
            services = ['slack']
        elif choice == '5':
            services = ['gmail', 'google_drive', 'github', 'slack']
        elif choice == '6':
            output.append("")
            output.append("  Enter service names (comma-separated):")
            output.append("  Examples: gmail,github  or  drive,slack")
            try:
                custom = input("  Services: ").strip()
                services = [s.strip().lower() for s in custom.split(',')]
            except (EOFError, OSError):
                services = []
        else:
            output.append("")
            output.append(f"  ❌ Invalid choice: {choice}")
            return "\n".join(output)
        
        if not services:
            output.append("")
            output.append("  ⚠️  No services selected")
            return "\n".join(output)
        
        output.append("")
        output.append(f"  ✅ Configuring: {', '.join(services)}")
        output.append("")
        
        # Read existing .env or create new
        env_vars = {}
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        # Chapter 3: Configuration for each service
        chapter_num = 3
        for service in services:
            output.append("╔═══════════════════════════════════════════════════════════╗")
            output.append("║                                                           ║")
            output.append(f"║  📖 Chapter {chapter_num}: {service.replace('_', ' ').title()} Configuration{' ' * (29 - len(service))}║")
            output.append("║                                                           ║")
            output.append("╚═══════════════════════════════════════════════════════════╝")
            output.append("")
            
            if service == 'gmail':
                output.extend(self._configure_gmail(env_vars))
            elif service == 'google_drive':
                output.extend(self._configure_google_drive(env_vars))
            elif service == 'github':
                output.extend(self._configure_github(env_vars))
            elif service == 'slack':
                output.extend(self._configure_slack(env_vars))
            else:
                output.extend(self._configure_generic(service, env_vars))
            
            chapter_num += 1
        
        # Save to .env
        output.append("")
        output.append("╔═══════════════════════════════════════════════════════════╗")
        output.append("║                                                           ║")
        output.append(f"║  📖 Chapter {chapter_num}: Saving Configuration{' ' * 24}║")
        output.append("║                                                           ║")
        output.append("╚═══════════════════════════════════════════════════════════╝")
        output.append("")
        output.append("  💾 Writing credentials to .env file...")
        output.append("")
        
        # Write .env file
        with open(env_path, 'w') as f:
            f.write("# uDOS Cloud Extension Credentials\n")
            f.write("# Auto-generated by SETUP CLOUD wizard\n")
            f.write(f"# Generated: {Path('.').absolute()}\n")
            f.write("# ⚠️  NEVER commit this file to git!\n\n")
            
            for key, value in sorted(env_vars.items()):
                f.write(f"{key}={value}\n")
        
        output.append("  ✅ Configuration saved successfully!")
        output.append("")
        output.append("  📄 File location: .env")
        output.append(f"  🔒 Total credentials stored: {len(env_vars)}")
        output.append("")
        output.append("  ⚠️  Security reminder:")
        output.append("    • .env is gitignored (safe)")
        output.append("    • Never share these credentials")
        output.append("    • Rotate keys regularly")
        output.append("    • Use environment-specific keys")
        output.append("")
        output.append("╔═══════════════════════════════════════════════════════════╗")
        output.append("║                  🎉 Setup Complete!                        ║")
        output.append("╠═══════════════════════════════════════════════════════════╣")
        output.append("║                                                           ║")
        output.append("║  Your cloud extensions are now configured!                ║")
        output.append("║                                                           ║")
        output.append("║  Next steps:                                              ║")
        output.append("║    1. Test connections with extension commands           ║")
        output.append("║    2. Enable extensions: EXTENSION ENABLE <name>          ║")
        output.append("║    3. Check status: EXTENSION LIST                        ║")
        output.append("║                                                           ║")
        output.append("║  📚 Documentation:                                         ║")
        output.append("║    • wiki/Gmail-Extension.md                              ║")
        output.append("║    • wiki/Cloud-Extensions.md                             ║")
        output.append("║                                                           ║")
        output.append("╚═══════════════════════════════════════════════════════════╝")
        output.append("")
        
        return "\n".join(output)
    
    def _configure_gmail(self, env_vars):
        """Configure Gmail API credentials."""
        output = []
        output.append("  📧 Gmail Integration")
        output.append("")
        output.append("  Gmail requires OAuth 2.0 credentials from Google Cloud Console:")
        output.append("    1. Visit: https://console.cloud.google.com")
        output.append("    2. Create project or select existing")
        output.append("    3. Enable Gmail API")
        output.append("    4. Create OAuth 2.0 credentials")
        output.append("    5. Download credentials.json")
        output.append("")
        
        try:
            client_id = input("  Gmail Client ID: ").strip()
            client_secret = input("  Gmail Client Secret: ").strip()
            
            if client_id:
                env_vars['GMAIL_CLIENT_ID'] = client_id
            if client_secret:
                env_vars['GMAIL_CLIENT_SECRET'] = client_secret
            
            output.append("")
            output.append("  ✅ Gmail credentials configured")
            output.append("")
        except (EOFError, OSError):
            output.append("  ⚠️  Skipped (non-interactive)")
            output.append("")
        
        return output
    
    def _configure_google_drive(self, env_vars):
        """Configure Google Drive API credentials."""
        output = []
        output.append("  📁 Google Drive Integration")
        output.append("")
        output.append("  Google Drive uses the same OAuth 2.0 setup as Gmail:")
        output.append("    1. Enable Google Drive API in Cloud Console")
        output.append("    2. Use same OAuth credentials as Gmail")
        output.append("    3. Or create separate credentials")
        output.append("")
        
        try:
            use_gmail = input("  Use Gmail credentials? (y/n): ").strip().lower()
            
            if use_gmail == 'y':
                if 'GMAIL_CLIENT_ID' in env_vars:
                    env_vars['GDRIVE_CLIENT_ID'] = env_vars['GMAIL_CLIENT_ID']
                    env_vars['GDRIVE_CLIENT_SECRET'] = env_vars['GMAIL_CLIENT_SECRET']
                    output.append("  ✅ Using Gmail credentials for Google Drive")
                else:
                    output.append("  ⚠️  Gmail not configured, please enter credentials")
                    client_id = input("  Drive Client ID: ").strip()
                    client_secret = input("  Drive Client Secret: ").strip()
                    if client_id:
                        env_vars['GDRIVE_CLIENT_ID'] = client_id
                    if client_secret:
                        env_vars['GDRIVE_CLIENT_SECRET'] = client_secret
            else:
                client_id = input("  Drive Client ID: ").strip()
                client_secret = input("  Drive Client Secret: ").strip()
                if client_id:
                    env_vars['GDRIVE_CLIENT_ID'] = client_id
                if client_secret:
                    env_vars['GDRIVE_CLIENT_SECRET'] = client_secret
            
            output.append("")
            output.append("  ✅ Google Drive credentials configured")
            output.append("")
        except (EOFError, OSError):
            output.append("  ⚠️  Skipped (non-interactive)")
            output.append("")
        
        return output
    
    def _configure_github(self, env_vars):
        """Configure GitHub API credentials."""
        output = []
        output.append("  🐙 GitHub Integration")
        output.append("")
        output.append("  GitHub requires a Personal Access Token:")
        output.append("    1. Visit: https://github.com/settings/tokens")
        output.append("    2. Generate new token (classic)")
        output.append("    3. Select scopes: repo, workflow, gist")
        output.append("    4. Copy the token")
        output.append("")
        
        try:
            token = input("  GitHub Token: ").strip()
            username = input("  GitHub Username (optional): ").strip()
            
            if token:
                env_vars['GITHUB_TOKEN'] = token
            if username:
                env_vars['GITHUB_USERNAME'] = username
            
            output.append("")
            output.append("  ✅ GitHub credentials configured")
            output.append("")
        except (EOFError, OSError):
            output.append("  ⚠️  Skipped (non-interactive)")
            output.append("")
        
        return output
    
    def _configure_slack(self, env_vars):
        """Configure Slack API credentials."""
        output = []
        output.append("  💬 Slack Integration")
        output.append("")
        output.append("  Slack requires a Bot Token:")
        output.append("    1. Visit: https://api.slack.com/apps")
        output.append("    2. Create new app or select existing")
        output.append("    3. Install app to workspace")
        output.append("    4. Copy Bot User OAuth Token")
        output.append("")
        
        try:
            token = input("  Slack Bot Token (xoxb-...): ").strip()
            webhook = input("  Slack Webhook URL (optional): ").strip()
            
            if token:
                env_vars['SLACK_BOT_TOKEN'] = token
            if webhook:
                env_vars['SLACK_WEBHOOK_URL'] = webhook
            
            output.append("")
            output.append("  ✅ Slack credentials configured")
            output.append("")
        except (EOFError, OSError):
            output.append("  ⚠️  Skipped (non-interactive)")
            output.append("")
        
        return output
    
    def _configure_generic(self, service, env_vars):
        """Configure generic service credentials."""
        output = []
        output.append(f"  🔧 {service.replace('_', ' ').title()} Integration")
        output.append("")
        output.append(f"  Enter credentials for {service}:")
        output.append("")
        
        try:
            api_key = input(f"  {service.upper()}_API_KEY: ").strip()
            secret = input(f"  {service.upper()}_SECRET (optional): ").strip()
            
            if api_key:
                env_vars[f'{service.upper()}_API_KEY'] = api_key
            if secret:
                env_vars[f'{service.upper()}_SECRET'] = secret
            
            output.append("")
            output.append(f"  ✅ {service.title()} credentials configured")
            output.append("")
        except (EOFError, OSError):
            output.append("  ⚠️  Skipped (non-interactive)")
            output.append("")
        
        return output

    @property
    def dev_mode_manager(self):
        """Lazy load DEV MODE manager."""
        if not hasattr(self, '_dev_mode_manager') or self._dev_mode_manager is None:
            from dev.goblin.core.services.dev_mode_manager import get_dev_mode_manager
            from dev.goblin.core.uDOS_main import get_config
            self._dev_mode_manager = get_dev_mode_manager(config_manager=get_config())
        return self._dev_mode_manager
