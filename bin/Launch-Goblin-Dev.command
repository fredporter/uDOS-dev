#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                    Goblin Dev Server Launcher                             ║
# ║              Experimental Development Server (port 8767)                  ║
# ║                   Includes GitHub, AI, Workflow services                  ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -e

# Get directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Source URL helper
source "$SCRIPT_DIR/udos-urls.sh"

# Spinner function for long-running tasks
run_with_spinner() {
    local message="$1"
    shift
    local cmd="$@"
    local spin_chars='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    
    eval "$cmd" &
    local pid=$!
    
    printf "  ${YELLOW}⠋${NC} %s" "$message"
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i + 1) % 10 ))
        printf "\r  ${YELLOW}${spin_chars:$i:1}${NC} %s" "$message"
        sleep 0.1
    done
    
    wait $pid
    local exit_code=$?
    printf "\r"
    return $exit_code
}

# Clear screen
clear

print_service_urls "🧌 Goblin Dev Server - Experimental Features"

echo -e "${CYAN}${BOLD}Environment Setup${NC}"
echo ""

# Check venv - auto-create if missing
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    if run_with_spinner "Creating virtual environment..." "python3 -m venv $PROJECT_ROOT/.venv"; then
        echo -e "  ${GREEN}✅ Virtual environment created${NC}"
    else
        echo -e "  ${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    fi
fi

source "$PROJECT_ROOT/.venv/bin/activate"
echo -e "${GREEN}✅ Python venv activated${NC}"

# Check dependencies - auto-install if missing
if ! python -c "import flask" 2>/dev/null; then
    if run_with_spinner "Installing dependencies (this may take a minute)..." "pip install -q -r $PROJECT_ROOT/requirements.txt"; then
        echo -e "  ${GREEN}✅ Dependencies installed${NC}"
    else
        echo -e "  ${RED}❌ Failed to install dependencies${NC}"
        exit 1
    fi
fi

# Set environment
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Create log directory
mkdir -p "$PROJECT_ROOT/memory/logs"
echo -e "${GREEN}✅ Log directory ready${NC}"

# Check port availability using port manager
if python -m wizard.cli_port_manager check goblin 2>&1 | grep -q "PORT_CONFLICT\|already in use" || lsof -Pi :8767 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port 8767 already in use${NC}"
    echo "   Kill with: bin/port-manager kill :8767"
    exit 1
fi

echo ""
echo -e "${CYAN}${BOLD}Starting Goblin Dev Server...${NC}"
echo ""

cd "$PROJECT_ROOT"

# Show URLs
echo -e "${GREEN}Services will be available at:${NC}"
echo ""
echo -e "  ${CYAN}API Server${NC}      → http://127.0.0.1:8767"
echo -e "  ${CYAN}Swagger UI${NC}      → http://127.0.0.1:8767/docs"
echo -e "  ${CYAN}ReDoc${NC}           → http://127.0.0.1:8767/redoc"
echo ""
echo -e "${DIM}Startup messages will appear below:${NC}"
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Run Goblin server
python "$PROJECT_ROOT/dev/goblin/goblin_server.py" 2>&1

# If we get here, server has stopped
echo ""
echo -e "${YELLOW}🛑 Goblin Dev Server stopped${NC}"
