#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                    Empire Private Server Launcher                         ║
# ║              CRM and Business Intelligence (TUI mode)                     ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# macOS launcher for Empire Server
# Keeps terminal window open for session
# Run from Finder or command line: open Launch-Empire-Server.command

set -e

# Parse args
UDOS_FORCE_REBUILD=0
ARGS=()
for arg in "$@"; do
    if [ "$arg" = "--rebuild" ]; then
        UDOS_FORCE_REBUILD=1
    else
        ARGS+=("$arg")
    fi
done
export UDOS_FORCE_REBUILD
set -- "${ARGS[@]}"

cd "$(dirname "$0")/.."

# ═══════════════════════════════════════════════════════════════════════════
# Colors and Formatting
# ═══════════════════════════════════════════════════════════════════════════
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
DIM='\033[2m'
NC='\033[0m'
BOLD='\033[1m'

# ═══════════════════════════════════════════════════════════════════════════
# Helper: Find uDOS root
# ═══════════════════════════════════════════════════════════════════════════
find_repo_root() {
    local start="$1"
    while [ -n "$start" ] && [ "$start" != "/" ]; do
        if [ -f "$start/uDOS.py" ]; then
            echo "$start"
            return 0
        fi
        start="$(dirname "$start")"
    done
    return 1
}

# ═══════════════════════════════════════════════════════════════════════════
# Resolve uDOS root
# ═══════════════════════════════════════════════════════════════════════════
resolve_udos_root() {
    if [ -n "$UDOS_ROOT" ] && [ -f "$UDOS_ROOT/uDOS.py" ]; then
        echo "$UDOS_ROOT"
        return 0
    fi

    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local found
    found="$(find_repo_root "$script_dir")" && { echo "$found"; return 0; }

    found="$(find_repo_root "$(pwd)")" && { echo "$found"; return 0; }

    return 1
}

# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════
UDOS_ROOT="$(resolve_udos_root)" || {
    echo -e "${RED}[ERROR]${NC} Could not locate uDOS repo root"
    echo "Make sure uDOS.py exists in your repo directory"
    read -p "Press Enter to exit..."
    exit 1
}

export UDOS_ROOT
cd "$UDOS_ROOT"

# Check that dev submodule is initialized
if [ ! -f "$UDOS_ROOT/dev/empire/empire.py" ]; then
    echo -e "${RED}[ERROR]${NC} Empire server not found at dev/empire/"
    echo ""
    echo -e "${YELLOW}[HINT]${NC} The dev/ folder is a private submodule. Initialize it:"
    echo -e "  git submodule update --init --recursive"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Ensure venv is activated
if [ ! -f "$UDOS_ROOT/.venv/bin/activate" ]; then
    echo -e "${YELLOW}[SETUP]${NC} Virtual environment not found"
    echo "Creating .venv..."
    python3 -m venv "$UDOS_ROOT/.venv"
fi

source "$UDOS_ROOT/.venv/bin/activate"

# Optional rebuild for Empire UI dependencies (if any)
if [ "$UDOS_FORCE_REBUILD" = "1" ] && [ -f "$UDOS_ROOT/dev/empire/package.json" ]; then
    echo -e "${YELLOW}[REBUILD]${NC} Installing Empire dependencies..."
    (cd "$UDOS_ROOT/dev/empire" && npm install --no-fund --no-audit) || true
fi

# ═══════════════════════════════════════════════════════════════════════════
# Get Version
# ═══════════════════════════════════════════════════════════════════════════
EMPIRE_VERSION="1.0.0"
if [ -f "$UDOS_ROOT/dev/empire/version.json" ]; then
    EMPIRE_VERSION=$(python3 -c "import json; v=json.load(open('$UDOS_ROOT/dev/empire/version.json')); print(v.get('version', '1.0.0'))" 2>/dev/null || echo "1.0.0")
fi

# ═══════════════════════════════════════════════════════════════════════════
# Launch Empire Server
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${BOLD}              🏛️  Empire Private Server v${EMPIRE_VERSION}${NC}${CYAN}                      ║${NC}"
echo -e "${CYAN}║${DIM}           Business Intelligence & CRM (TUI mode)${NC}${CYAN}             ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}[BOOT]${NC} uDOS Root: $UDOS_ROOT"
echo -e "${GREEN}[BOOT]${NC} Python: $(python --version)"
echo -e "${GREEN}[BOOT]${NC} Features: Contacts, HubSpot CRM, Gmail extraction, Google Business"
echo ""

# Check Empire folder structure
echo -e "${BLUE}[CHECK]${NC} Checking Empire structure..."
if [ -f "$UDOS_ROOT/dev/empire/version.json" ]; then
    echo -e "${GREEN}[✓]${NC} Empire v${EMPIRE_VERSION}"
else
    echo -e "${RED}[✗]${NC} Empire folder not found or missing version.json"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check required Python modules
echo -e "${BLUE}[CHECK]${NC} Checking Python dependencies..."
REQUIRED_MODULES=("sqlite3" "json" "os" "sys")

for module in "${REQUIRED_MODULES[@]}"; do
    if python -c "import $module" 2>/dev/null; then
        echo -e "${GREEN}  ✓ $module${NC}"
    else
        echo -e "${YELLOW}  ⚠ $module (optional)${NC}"
    fi
done

# Launch Empire Server TUI
echo ""
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Launching Empire Server TUI...${NC}"
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Try to import and run Empire TUI
python -c "
import sys
sys.path.insert(0, '$UDOS_ROOT')

try:
    from dev.empire.tui import EmpireServerTUI
    server = EmpireServerTUI()
    server.run()
except ImportError:
    print('⚠️  Empire TUI not yet implemented')
    print('Importing core modules...')
    from dev.empire import id_generator, marketing_db
    print('✅ Core modules loaded')
    print('')
    print('Empire server interactive mode:')
    import code
    code.interact(local=globals())
except Exception as e:
    print(f'✗ Error: {e}')
    sys.exit(1)
"

# Keep window open if script exits
echo ""
echo -e "${YELLOW}[EXIT]${NC} Empire Server session ended"
read -p "Press Enter to close this window..."
