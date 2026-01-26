#!/bin/bash
# Empire Server Launcher
# Delegates to unified launch_component() system

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UDUDUDUDUDUDUDUDUDUDUDUDUDUDUDe "UDUDUDUDUDUDUDUDUDUDUDUDUDUDOS_ROOT/bin/udos-common.sh"
launch_component "empire" "dev" "$@"
