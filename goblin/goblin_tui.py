"""
Goblin Interactive TUI
======================

Simple command prompt for Goblin MODE playground.

Commands:
    help     - Show available commands
    status   - Show server status
    modes    - List available MODEs
    dash     - Open dashboard in browser
    teletext - Test teletext MODE
    terminal - Test terminal MODE
    logs     - Show recent logs
    exit     - Exit TUI
"""

import sys
import os
import subprocess
import webbrowser
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from wizard.services.logging_manager import get_logger

logger = get_logger("goblin-tui")

# Colors
CYAN = '\033[0;36m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
MAGENTA = '\033[0;35m'
DIM = '\033[2m'
BOLD = '\033[1m'
NC = '\033[0m'


class GoblinTUI:
    """Interactive TUI for Goblin MODE playground."""
    
    def __init__(self):
        self.running = True
        self.server_url = "http://localhost:8767"
        self.dashboard_url = "http://localhost:5174"
        
    def start(self):
        """Start the interactive TUI."""
        self.print_banner()
        self.print_help()
        
        while self.running:
            try:
                command = input(f"\n{MAGENTA}{BOLD}goblin>{NC} ").strip().lower()
                if command:
                    self.handle_command(command)
            except KeyboardInterrupt:
                print(f"\n{YELLOW}Use 'exit' to quit{NC}")
            except EOFError:
                break
        
        print(f"\n{GREEN}Goblin TUI session ended{NC}\n")
    
    def print_banner(self):
        """Print startup banner."""
        print(f"\n{CYAN}{BOLD}╔═══════════════════════════════════════════════════════════════╗{NC}")
        print(f"{CYAN}{BOLD}║              🧪 Goblin MODE Playground - TUI                  ║{NC}")
        print(f"{CYAN}{BOLD}╚═══════════════════════════════════════════════════════════════╝{NC}")
        print(f"{DIM}Version: v0.2.0.0 | Port: 8767 | Experimental{NC}\n")
    
    def print_help(self):
        """Print available commands."""
        print(f"{CYAN}Available Commands:{NC}")
        print(f"  {BOLD}help{NC}     - Show this help")
        print(f"  {BOLD}status{NC}   - Check server status")
        print(f"  {BOLD}modes{NC}    - List available MODEs")
        print(f"  {BOLD}dash{NC}     - Open dashboard in browser")
        print(f"  {BOLD}teletext{NC} - Quick teletext test")
        print(f"  {BOLD}terminal{NC} - Quick terminal test")
        print(f"  {BOLD}logs{NC}     - Show recent server logs")
        print(f"  {BOLD}exit{NC}     - Exit TUI")
    
    def handle_command(self, command: str):
        """Handle user command."""
        if command in ["exit", "quit", "q"]:
            self.running = False
        elif command in ["help", "h", "?"]:
            self.print_help()
        elif command == "status":
            self.check_status()
        elif command == "modes":
            self.list_modes()
        elif command in ["dash", "dashboard", "open"]:
            self.open_dashboard()
        elif command == "teletext":
            self.test_teletext()
        elif command == "terminal":
            self.test_terminal()
        elif command == "logs":
            self.show_logs()
        else:
            print(f"{YELLOW}Unknown command: {command}{NC}")
            print(f"{DIM}Type 'help' for available commands{NC}")
    
    def check_status(self):
        """Check server status."""
        try:
            import requests
            response = requests.get(f"{self.server_url}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"{GREEN}✅ Server online{NC}")
                print(f"   Version: {data.get('version', 'unknown')}")
                print(f"   Status: {data.get('status', 'unknown')}")
            else:
                print(f"{YELLOW}⚠️  Server returned {response.status_code}{NC}")
        except Exception as e:
            print(f"{YELLOW}⚠️  Server offline or unreachable{NC}")
            print(f"{DIM}   Error: {e}{NC}")
    
    def list_modes(self):
        """List available MODEs."""
        try:
            import requests
            response = requests.get(f"{self.server_url}/api/v0/modes/teletext/patterns", timeout=2)
            if response.status_code == 200:
                print(f"{GREEN}Available MODEs:{NC}")
                print(f"  {BOLD}1. Teletext{NC} - Retro patterns, ANSI art")
                print(f"  {BOLD}2. Terminal{NC} - Escape codes, color schemes")
            else:
                print(f"{YELLOW}⚠️  Could not fetch MODE list{NC}")
        except Exception:
            print(f"{GREEN}Available MODEs:{NC}")
            print(f"  {BOLD}1. Teletext{NC} - Retro patterns, ANSI art")
            print(f"  {BOLD}2. Terminal{NC} - Escape codes, color schemes")
    
    def open_dashboard(self):
        """Open dashboard in browser."""
        print(f"{GREEN}Opening dashboard...{NC}")
        print(f"{DIM}URL: {self.dashboard_url}{NC}")
        try:
            webbrowser.open(self.dashboard_url)
            print(f"{GREEN}✅ Browser launched{NC}")
        except Exception as e:
            print(f"{YELLOW}⚠️  Could not open browser: {e}{NC}")
            print(f"{DIM}   Manually visit: {self.dashboard_url}{NC}")
    
    def test_teletext(self):
        """Quick teletext test."""
        print(f"{GREEN}Testing Teletext MODE...{NC}")
        try:
            import requests
            response = requests.get(
                f"{self.server_url}/api/v0/modes/teletext/render",
                params={"pattern": "chevrons", "width": 40},
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                print(f"\n{data.get('rendered', 'No output')}\n")
                print(f"{GREEN}✅ Teletext MODE working{NC}")
            else:
                print(f"{YELLOW}⚠️  Test failed: {response.status_code}{NC}")
        except Exception as e:
            print(f"{YELLOW}⚠️  Test failed: {e}{NC}")
            print(f"{DIM}   Make sure server is running on port 8767{NC}")
    
    def test_terminal(self):
        """Quick terminal test."""
        print(f"{GREEN}Testing Terminal MODE...{NC}")
        try:
            import requests
            response = requests.get(
                f"{self.server_url}/api/v0/modes/terminal/render",
                params={"text": "Goblin MODE Test", "fg": "cyan", "style": "bold"},
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                print(f"\n{data.get('rendered', 'No output')}\n")
                print(f"{GREEN}✅ Terminal MODE working{NC}")
            else:
                print(f"{YELLOW}⚠️  Test failed: {response.status_code}{NC}")
        except Exception as e:
            print(f"{YELLOW}⚠️  Test failed: {e}{NC}")
            print(f"{DIM}   Make sure server is running on port 8767{NC}")
    
    def show_logs(self):
        """Show recent server logs."""
        log_file = Path(__file__).parent.parent.parent.parent / "memory" / "logs" / "goblin-server.log"
        
        if not log_file.exists():
            print(f"{YELLOW}⚠️  Log file not found{NC}")
            return
        
        print(f"{GREEN}Recent logs:{NC}")
        try:
            lines = log_file.read_text().splitlines()
            for line in lines[-20:]:
                print(f"{DIM}{line}{NC}")
        except Exception as e:
            print(f"{YELLOW}⚠️  Could not read logs: {e}{NC}")


def main():
    """Entry point."""
    tui = GoblinTUI()
    tui.start()


if __name__ == "__main__":
    main()
