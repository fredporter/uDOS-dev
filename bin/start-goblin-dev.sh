#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                  Goblin Dev Server Unified Launcher                       ║
# ║              Experimental server + dashboard + TUI                        ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UDOS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source shared functions
source "$UDOS_ROOT/bin/udos-common.sh"

# Delegate to unified component launcher
launch_goblin_dev "$@"
