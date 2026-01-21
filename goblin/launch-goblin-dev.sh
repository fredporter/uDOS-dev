#!/bin/bash
# Goblin Dev Server Launcher
# Usage: ./launch-goblin-dev.sh

GOBLIN_DIR="/Users/fredbook/Code/uDOS/dev/goblin"
UDOS_DIR="/Users/fredbook/Code/uDOS"
VENV_PYTHON="$UDOS_DIR/.venv/bin/python"
PORT=8767

echo "🧌 Launching Goblin Dev Server v0.1.0.0"
echo "   Port: $PORT"
echo "   URL: http://127.0.0.1:$PORT"
echo "   Swagger UI: http://127.0.0.1:$PORT/docs"
echo ""

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found at $VENV_PYTHON"
    echo "   Run: cd $UDOS_DIR && python -m venv .venv"
    exit 1
fi

# Change to project root (so PYTHONPATH includes all modules)
cd "$UDOS_DIR"

# Set PYTHONPATH to include root for absolute imports
export PYTHONPATH="$UDOS_DIR:$PYTHONPATH"

# Start server
echo "📡 Starting server..."
echo ""

"$VENV_PYTHON" "$GOBLIN_DIR/goblin_server.py"
