#!/bin/bash

# Goblin Dev Server Launcher (shell script)
# Starts experimental dev server with boot checks
# 
# Location: dev/goblin/bin/launch-goblin-dev.sh
# Port: 8767
# Dashboard: http://127.0.0.1:8767
# API Docs: http://127.0.0.1:8767/docs

# Get the repository root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$REPO_ROOT"

# Display banner
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║            👺 Goblin Dev Server v0.2.0                        ║
║     Experimental • Localhost Only • Breaking Changes OK       ║
╚═══════════════════════════════════════════════════════════════╝
EOF

# Check environment
echo ""
echo "[BOOT] Checking environment..."
echo "[BOOT] uDOS Root: $REPO_ROOT"

if [ ! -d ".venv" ]; then
    echo "[✗] Virtual environment not found at .venv/"
    exit 1
fi

if [ -f "requirements.txt" ]; then
    echo "[BOOT] Features: Notion sync, Runtime execution, Task scheduling, Binder compilation"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👺 Goblin Dev Server v0.2.0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Activate venv
echo "[BOOT] Activating virtual environment..."
source .venv/bin/activate 2>/dev/null

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
python -c "import fastapi; import uvicorn" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[✓] Dependencies installed and ready"
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

# Start server
echo "[BOOT] Starting Goblin Dev Server on port 8767..."
echo ""
python dev/goblin/goblin_server.py

# Capture exit code
RESULT=$?
if [ $RESULT -ne 0 ]; then
    echo ""
    echo "[✗] Failed to start Goblin Dev Server on port 8767"
    echo "[⚠] Note: Goblin Dev Server is in the private submodule (dev/)"
    echo "[INFO] Ensure submodule is initialized: git submodule update --init --recursive"
fi

exit $RESULT
