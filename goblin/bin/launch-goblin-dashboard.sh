#!/bin/bash
# Launch Goblin Dashboard (Dev Mode)

cd "$(dirname "$0")/../dashboard"

echo "🎨 Launching Goblin Dashboard..."
echo ""
echo "URL: http://localhost:5174"
echo "Server: http://localhost:8767"
# Open browser after short delay
(sleep 3 && open http://localhost:5174) &

echo ""

npm run dev
