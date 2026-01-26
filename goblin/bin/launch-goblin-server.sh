#!/bin/bash
# Launch Goblin MODE Playground Server
# Launch Goblin MODE Playground Server (Background)

cd "$(dirname "$0")/.."

echo "🧪 Launching Goblin MODE Playground..."
echo ""
echo "Server: http://localhost:8767"
echo "Dashboard: http://localhost:5174"
echo ""

# Activate venv
source ../../.venv/bin/activate

# Start server in background
python goblin_server.py > /dev/null 2>&1 &
SERVER_PID=$!

echo "✅ Server started (PID: $SERVER_PID)"
echo ""
echo "Starting interactive TUI..."
sleep 2

# Launch TUI
python goblin_tui.py

# When TUI exits, offer to stop server
echo ""
read -p "Stop Goblin server? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
	kill $SERVER_PID 2>/dev/null
	echo "✅ Server stopped"
fi
