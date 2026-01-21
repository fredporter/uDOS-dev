#!/bin/bash

# uMarkdown Dev Launcher
# Launches the dev server with hot reload

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting uMarkdown Dev Server (Hot Reload)..."
cd "$APP_ROOT"
npm run tauri:dev || {
    echo "❌ Dev server failed"
    exit 1
}
