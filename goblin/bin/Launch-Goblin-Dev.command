#!/bin/bash

# Goblin Dev Server Launcher (.command for macOS)
# Displays boot information and starts experimental dev server
# 
# Location: dev/goblin/bin/Launch-Goblin-Dev.command
# Port: 8767
# Dashboard: http://127.0.0.1:8767
# API Docs: http://127.0.0.1:8767/docs

# Get the repository root (this script is at /dev/goblin/bin/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$REPO_ROOT"

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

# Display banner
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║            👺 Goblin Dev Server v0.2.0                        ║
║     Experimental • Localhost Only • Breaking Changes OK       ║
╚═══════════════════════════════════════════════════════════════╝
EOF

# Check venv
echo ""
echo "[BOOT] Checking environment..."
echo "[BOOT] uDOS Root: $REPO_ROOT"

if [ ! -d ".venv" ]; then
    echo "[✗] Virtual environment not found at .venv/"
    exit 1
fi

# Check requirements
if [ -f "requirements.txt" ]; then
    echo "[BOOT] Features: Notion sync, Runtime execution, Task scheduling, Binder compilation"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👺 Goblin Dev Server v0.2.0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Activate venv
echo "[BOOT] Activating virtual environment..."
source .venv/bin/activate

if [ $? -eq 0 ]; then
    echo "[✓] Virtual environment activated"
    PYTHON_VERSION=$(python --version 2>&1)
    echo "[BOOT] Python: $PYTHON_VERSION"
else
    echo "[✗] Failed to activate virtual environment"
    exit 1
fi

# Check dependencies
echo "[BOOT] Checking dependencies..."
python -c "import fastapi; import uvicorn; import svelte" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[✓] Dependencies installed and ready"
else
    echo "[⚠] Some dependencies may be missing"
fi

# Optional rebuild for Goblin UI dependencies
if [ "$UDOS_FORCE_REBUILD" = "1" ] || [ ! -d "$REPO_ROOT/dev/goblin/node_modules" ] || [ "$REPO_ROOT/dev/goblin/package.json" -nt "$REPO_ROOT/dev/goblin/package-lock.json" ]; then
    echo "[BOOT] Installing Goblin UI dependencies..."
    (cd "$REPO_ROOT/dev/goblin" && npm install --no-fund --no-audit) || {
        echo "[✗] Failed to install Goblin UI dependencies"
    }
fi

# Self-healing: Kill any existing Goblin instance
echo "[BOOT] Checking for existing Goblin server..."
EXISTING_PID=$(ps aux | grep "goblin_server.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$EXISTING_PID" ]; then
    echo "[BOOT] Stopping existing Goblin server (PID: $EXISTING_PID)..."
    kill $EXISTING_PID 2>/dev/null
    sleep 2
    echo "[✓] Existing server stopped"
fi

# Start Goblin
echo "[BOOT] Starting Goblin Dev Server on port 8767..."
python dev/goblin/goblin_server.py

# If we get here, server exited
RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "[✓] Goblin Dev Server stopped cleanly"
else
    echo "[✗] Failed to start Goblin Dev Server on port 8767"
    echo "[⚠] Note: Goblin Dev Server is in the private submodule (dev/)"
    echo "[INFO] Ensure submodule is initialized: git submodule update --init --recursive"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check if port 8767 is already in use: lsof -i :8767"
    echo "  2. Verify Python dependencies: pip install -r requirements.txt"
    echo "  3. Check Goblin logs: cat memory/logs/system-*.log"
fi

exit $RESULT
