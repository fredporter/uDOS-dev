#!/bin/bash

# Empire Private Server - TUI Launcher
# Launches the Empire CRM and business intelligence system
# Version: 1.0.0.1

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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

echo -e "${GREEN}🏛️  Empire Private Server - v1.0.0.1${NC}"
echo "────────────────────────────────────────"

# Check virtual environment - auto-create if missing
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not detected${NC}"
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        if run_with_spinner "Creating virtual environment..." "python3 -m venv $PROJECT_ROOT/.venv"; then
            echo -e "  ${GREEN}✅ Virtual environment created${NC}"
        else
            echo -e "  ${RED}✗ Failed to create virtual environment${NC}"
            exit 1
        fi
    fi
    echo "Activating .venv..."
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo -e "${GREEN}✅ Venv activated${NC}"
    
    # Check dependencies - auto-install if missing
    if ! python -c "import flask" 2>/dev/null; then
        if run_with_spinner "Installing dependencies (this may take a minute)..." "pip install -q -r $PROJECT_ROOT/requirements.txt"; then
            echo -e "  ${GREEN}✅ Dependencies installed${NC}"
        else
            echo -e "  ${RED}✗ Failed to install dependencies${NC}"
            exit 1
        fi
    fi
fi

# Check Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}✗ Python not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python ${PYTHON_VERSION}${NC}"

# Check Empire folder structure
echo ""
echo "Checking Empire structure..."
if [ -f "$PROJECT_ROOT/empire/version.json" ]; then
    VERSION=$(python -c "import json; print(json.load(open('$PROJECT_ROOT/empire/version.json'))['version'])" 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✅ Empire v${VERSION}${NC}"
else
    echo -e "${RED}✗ Empire folder not found or missing version.json${NC}"
    exit 1
fi

# Check required Python modules
echo ""
echo "Checking Python dependencies..."
REQUIRED_MODULES=("sqlite3" "json" "os" "sys")
MISSING=0

for module in "${REQUIRED_MODULES[@]}"; do
    if python -c "import $module" 2>/dev/null; then
        echo -e "${GREEN}  ✓ $module${NC}"
    else
        echo -e "${YELLOW}  ⚠ $module (optional)${NC}"
    fi
done

# Launch Empire Server TUI
echo ""
echo -e "${GREEN}────────────────────────────────────────${NC}"
echo -e "${GREEN}Launching Empire Server TUI...${NC}"
echo -e "${GREEN}────────────────────────────────────────${NC}"
echo ""

cd "$PROJECT_ROOT"

# Try to import and run Empire TUI
python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')

try:
    from empire.tui import EmpireServerTUI
    server = EmpireServerTUI()
    server.run()
except ImportError:
    print('⚠️  Empire TUI not yet implemented')
    print('Importing core modules...')
    from empire import id_generator, marketing_db
    print('✅ Core modules loaded')
    print('')
    print('Empire server interactive mode:')
    import code
    code.interact(local=globals())
except Exception as e:
    print(f'✗ Error: {e}')
    sys.exit(1)
"
