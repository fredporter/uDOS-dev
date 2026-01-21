#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                    uDOS URL Helper Functions                              ║
# ║              Shared utilities for launch scripts                          ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# Print service URLs banner
print_service_urls() {
    local title="$1"
    echo -e "${MAGENTA}${BOLD}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}${BOLD}║${NC}  $title"
    echo -e "${MAGENTA}${BOLD}╚═══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check if port is available
check_port() {
    local port=$1
    lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
    return $?
}

# Get process using port
get_port_process() {
    local port=$1
    lsof -Pi :$port -sTCP:LISTEN | tail -n 1 | awk '{print $2}'
}
