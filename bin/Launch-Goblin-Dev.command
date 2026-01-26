#!/bin/bash
# Goblin Dev Server Launcher
# Delegates to unified launch_component() system

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UDOS_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
source "$UDOS_ROOT/bin/udos-common.sh"
launch_component "goblin" "dev" "$@"
