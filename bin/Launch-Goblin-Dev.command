#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                    Goblin Dev Server Launcher                             ║
# ║              Experimental Development Server (port 8767)                  ║
# ║                   Includes GitHub, AI, Workflow services                  ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -e

# Source shared helpers from parent uDOS repo
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
UDOS_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
source "$UDOS_ROOT/bin/udos-common.sh"
parse_rebuild_flag "$@"
cd "$UDOS_ROOT"

clear
print_header "🧌 Goblin Dev Server - Experimental Features"
print_service_url "API Server" "http://localhost:8767"
print_service_url "Swagger UI" "http://localhost:8767/docs"
print_service_url "ReDoc" "http://localhost:8767/redoc"
echo ""

echo -e "${CYAN}${BOLD}Environment Setup${NC}"
echo ""

# Setup Python environment (venv + dependencies)
ensure_python_env || exit 1
echo -e "${GREEN}✅ Log directory ready${NC}"

# Optional rebuild for Goblin UI dependencies
maybe_npm_install "$UDOS_ROOT/dev/goblin" || exit 1

# Check port availability
if lsof -Pi :8767 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port 8767 already in use${NC}"
    echo "   Kill with: bin/port-manager kill :8767"
    exit 1
fi

echo ""
echo -e "${CYAN}${BOLD}Starting Goblin Dev Server...${NC}"
echo ""
echo -e "${DIM}Startup messages will appear below:${NC}"
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Run Goblin server
python "$UDOS_ROOT/dev/goblin/goblin_server.py" 2>&1

# If we get here, server has stopped
echo ""
echo -e "${YELLOW}🛑 Goblin Dev Server stopped${NC}"
