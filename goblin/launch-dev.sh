#!/bin/bash
# Goblin Dev Server Launcher
# Starts both Python backend (FastAPI) and SvelteKit frontend

set -e

GOBLIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="${GOBLIN_DIR}/../../.venv"

echo "🧙 Goblin Dev Server Launcher"
echo "================================"
echo ""

# Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
  echo "📦 Activating Python virtual environment..."
  source "$VENV_PATH/bin/activate"
fi

echo "✅ Virtual environment: $VIRTUAL_ENV"
echo ""

# Start Python backend in background
echo "🚀 Starting Goblin Python Backend (port 8767)..."
cd "$GOBLIN_DIR"
python -m dev.goblin.server &
PYTHON_PID=$!
echo "   Python PID: $PYTHON_PID"
echo ""

# Wait for Python server to start
sleep 2

# Start SvelteKit frontend
echo "🎨 Starting Goblin Frontend (port 5173)..."
echo ""
echo "📍 Frontend:    http://localhost:5173"
echo "📍 Backend API: http://localhost:8767/api/v0"
echo ""
echo "Feature Routes:"
echo "  - Desktop:     http://localhost:5173/desktop"
echo "  - Editor:      http://localhost:5173/editor"
echo "  - Grid:        http://localhost:5173/grid"
echo "  - Terminal:    http://localhost:5173/terminal"
echo "  - Sprites:     http://localhost:5173/sprites"
echo "  - Stories:     http://localhost:5173/stories"
echo "  - Presentation: http://localhost:5173/present"
echo ""
echo "Press Ctrl+C to stop both servers..."
echo ""

npm run dev

# Cleanup on exit
trap "kill $PYTHON_PID" EXIT
