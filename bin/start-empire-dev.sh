#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                  Empire Dev Server Unified Launcher                       ║
# ║              CRM system + business intelligence                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UDOS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source shared functions
source "$UDOS_ROOT/bin/udos-common.sh"

# Delegate to unified component launcher
launch_empire_dev "$@"
