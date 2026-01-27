#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                  Empire Dev Server Direct Launcher                        ║
# ║              CRM system + business intelligence (called by launch_empire_dev)║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UDOS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$UDOS_ROOT"

# Ensure venv is activated
if [ -f "$UDOS_ROOT/.venv/bin/activate" ]; then
    source "$UDOS_ROOT/.venv/bin/activate"
fi

# Launch Empire server TUI directly
exec python dev/empire/tui.py "$@"
