#!/bin/bash

# ============================================
# uMarkdown App Dev Launcher
# Location: /dev/app (private submodule)
# Launches Tauri dev server with hot reload
# ============================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UDOS_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo ""
echo "🍎 uMarkdown Mac App - Dev Mode"
echo "════════════════════════════════"
echo "📍 App: $APP_ROOT"
echo "🏠 uDOS: $UDOS_ROOT"
echo ""

# Check node_modules
if [ ! -d "$APP_ROOT/node_modules" ]; then
    echo "📦 Installing dependencies..."
    cd "$APP_ROOT" && npm install
fi

echo "🚀 Starting Tauri Dev Server (Hot Reload)..."
echo "   Frontend: http://localhost:1420"
echo ""

cd "$APP_ROOT"
npm run tauri:dev || {
    echo ""
    echo "❌ Dev server failed"
    echo "   Try: npm install && npm run tauri:dev"
    exit 1
}
