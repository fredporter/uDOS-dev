#!/bin/bash
# ============================================
# Goblin Dev Server Launcher (Backend Only)
# Starts Python FastAPI backend on port 8767
# Location: /dev/goblin (private submodule)
# ============================================

GOBLIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
UDOS_ROOT="$(cd "$GOBLIN_DIR/../.." && pwd)"
VENV_PYTHON="$UDOS_ROOT/.venv/bin/python"
PORT=8767

echo ""
echo "🧌 Goblin Dev Server - Backend Only"
echo "════════════════════════════════════"
echo "📍 Port: $PORT"
echo "📍 URL: http://127.0.0.1:$PORT"
echo "📍 Swagger: http://127.0.0.1:$PORT/docs"
echo ""

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found at $VENV_PYTHON"
    echo "   Run: cd $UDOS_ROOT && python -m venv .venv"
    exit 1
fi

# Change to project root (so PYTHONPATH includes all modules)
cd "$UDOS_ROOT"

# Set PYTHONPATH to include root for absolute imports
export PYTHONPATH="$UDOS_ROOT:$PYTHONPATH"

# Start server
echo "📡 Starting server..."
echo ""

"$VENV_PYTHON" "$GOBLIN_DIR/goblin_server.py"
