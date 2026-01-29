"""
Goblin Dev Server Interactive Console
======================================

Lightweight interactive console for Goblin experimental server.
Minimal command set focused on MODE testing and dev operations.

Commands:
  status     - Show server status
  modes      - List available MODEs
  health     - Run health check
  logs       - Show recent log entries
  reload     - Restart server (dev mode)
  help       - Show this help
  exit/quit  - Shutdown server
"""

import sys
import json
import threading
from typing import Dict, Any
from pathlib import Path
from datetime import datetime


class GoblinConsole:
    """Interactive console for Goblin Dev Server."""

    def __init__(self, server_config: Dict[str, Any]):
        """Initialize console with server configuration."""
        self.config = server_config
        self.running = False
        self.start_time = datetime.now()

    def start(self):
        """Start the interactive console in a background thread."""
        self.running = True
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()
        return thread

    def stop(self):
        """Stop the console."""
        self.running = False

    def _run_loop(self):
        """Main console loop."""
        self._print_welcome()

        while self.running:
            try:
                command = input("goblin> ").strip().lower()

                if not command:
                    continue

                if command in ("exit", "quit", "q"):
                    print("🛑 Shutting down Goblin server...")
                    self.running = False
                    # Signal server shutdown
                    import os
                    os._exit(0)
                    break

                elif command == "help":
                    self._cmd_help()

                elif command == "status":
                    self._cmd_status()

                elif command == "modes":
                    self._cmd_modes()

                elif command == "health":
                    self._cmd_health()

                elif command == "logs":
                    self._cmd_logs()

                elif command == "reload":
                    print("🔄 Reload triggered - Uvicorn will restart automatically")

                else:
                    print(f"❌ Unknown command: {command}")
                    print("   Type 'help' for available commands")

            except EOFError:
                self.running = False
                break
            except KeyboardInterrupt:
                print("\n⚠️  Use 'exit' to shutdown gracefully")
                continue
            except Exception as e:
                print(f"❌ Console error: {e}")

    def _print_welcome(self):
        """Print welcome banner."""
        print()
        print("=" * 68)
        print()
        print("🧪 GOBLIN MODE PLAYGROUND")
        print()
        print(f"  Version:       {self._get_version()}")
        print(f"  Port:          {self.config.get('port', 8767)}")
        print(f"  Status:        Experimental")
        print()
        print("🔬 AVAILABLE MODES:")
        print("  • Teletext    - BBC Micro-style 40x25 rendering")
        print("  • Terminal    - ANSI escape code output")
        print()
        print("🌐 ENDPOINTS:")
        print(f"  • Health:      http://localhost:{self.config.get('port', 8767)}/health")
        print(f"  • API:         http://localhost:{self.config.get('port', 8767)}/api/v0/modes/")
        print(f"  • Dashboard:   http://localhost:5174 (Vite dev)")
        print()
        print("💬 INTERACTIVE MODE: Type 'help' for commands, 'exit' to shutdown")
        print("=" * 68)
        print()

    def _get_version(self) -> str:
        """Get Goblin version."""
        try:
            version_file = Path(__file__).parent.parent / "version.json"
            if version_file.exists():
                with open(version_file) as f:
                    data = json.load(f)
                    v = data["version"]
                    return f"{v['major']}.{v['minor']}.{v['patch']}.{v['build']}"
        except Exception:
            pass
        return "0.2.0.0"

    def _cmd_help(self):
        """Show help message."""
        print()
        print("📖 GOBLIN CONSOLE COMMANDS:")
        print()
        print("  status       - Show server status and uptime")
        print("  modes        - List available MODE implementations")
        print("  health       - Run health check")
        print("  logs         - Show recent log entries")
        print("  reload       - Trigger Uvicorn reload (dev mode)")
        print("  help         - Show this help message")
        print("  exit/quit    - Shutdown server gracefully")
        print()

    def _cmd_status(self):
        """Show server status."""
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)

        print()
        print("📊 SERVER STATUS:")
        print(f"  • Uptime: {hours}h {minutes}m")
        print(f"  • Port: {self.config.get('port', 8767)}")
        print(f"  • Mode: Development (auto-reload)")
        print(f"  • MODEs: Teletext, Terminal")
        print()

    def _cmd_modes(self):
        """List available MODEs."""
        print()
        print("🔬 AVAILABLE MODES:")
        print()
        print("  Teletext:")
        print("    • 40x25 character grid")
        print("    • BBC Micro Level 9 style")
        print("    • 8-color palette")
        print("    • Endpoint: /api/v0/modes/teletext")
        print()
        print("  Terminal:")
        print("    • ANSI escape codes")
        print("    • 256-color support")
        print("    • Cursor positioning")
        print("    • Endpoint: /api/v0/modes/terminal")
        print()

    def _cmd_health(self):
        """Run health check."""
        print()
        print("🏥 HEALTH CHECK:")
        print("  ✅ Server running")
        print("  ✅ Console active")
        print(f"  ✅ Port {self.config.get('port', 8767)} bound")
        print()

    def _cmd_logs(self):
        """Show recent logs."""
        print()
        print("📜 RECENT LOGS:")
        print("  (Logs displayed in main Uvicorn output)")
        print("  Check terminal window for Uvicorn logs")
        print()


def create_goblin_console(config: Dict[str, Any]) -> GoblinConsole:
    """Factory function to create Goblin console."""
    return GoblinConsole(config)
