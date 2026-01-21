#!/bin/bash
# Test DEV MODE and error fixes

cd /Users/fredbook/Code/uDOS
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
