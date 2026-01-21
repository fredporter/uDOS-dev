#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                    Empire Private Server Launcher                         ║
# ║              CRM and Business Intelligence (TUI mode)                     ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -e

# Source shared helpers from parent uDOS repo
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
UDOS_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
source "$UDOS_ROOT/bin/udos-common.sh"
cd "$UDOS_ROOT"

clear
print_header "🏛️ Empire Private Server"
echo ""

# Setup Python environment (venv + dependencies)
ensure_python_env || exit 1

# Check Empire folder structure
echo ""
echo -e "${CYAN}Checking Empire structure...${NC}"
if [ -f "$UDOS_ROOT/dev/empire/version.json" ]; then
    VERSION=$(python -c "import json; print(json.load(open('$UDOS_ROOT/dev/empire/version.json'))['version'])" 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✅ Empire v${VERSION}${NC}"
else
    echo -e "${RED}❌ Empire folder not found or missing version.json${NC}"
    exit 1
fi

# Check required Python modules
echo ""
echo -e "${CYAN}Checking Python dependencies...${NC}"
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
