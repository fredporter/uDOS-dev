#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                  Goblin Dev Server Direct Launcher                        ║
# ║              Experimental server + dashboard (called by launch_goblin_dev)║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UDOS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$UDOS_ROOT"

# Ensure venv is activated
if [ -f "$UDOS_ROOT/.venv/bin/activate" ]; then
    source "$UDOS_ROOT/.venv/bin/activate"
fi

# Launch Goblin server directly
exec python dev/goblin/goblin_server.py "$@"
