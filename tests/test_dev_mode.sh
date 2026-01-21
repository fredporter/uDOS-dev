#!/bin/bash
# Test DEV MODE and error fixes

# Navigate to project root dynamically
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
source .venv/bin/activate

echo "Testing DEV MODE commands..."
echo ""

# Test commands
echo "dev mode status" | python3 uDOS.py
echo ""
echo "---"
echo ""

echo "destroy" | python3 uDOS.py
echo ""
echo "---"
echo ""

echo "repair --check" | python3 uDOS.py
echo ""
echo "---"
echo ""

echo "history" | python3 uDOS.py
