#!/bin/bash
# Test runner script for HomeSeer MCP Server
# Run this script to execute all unit tests

set -e  # Exit on error

echo "========================================"
echo "HomeSeer MCP Server - Test Runner"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[!] Virtual environment not found!"
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "[*] Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "[X] Could not find activation script"
    exit 1
fi

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "[+] Installing test dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "[*] Running tests..."
echo "========================================"
echo ""

# Run pytest with options
python -m pytest tests/ \
    --verbose \
    --color=yes \
    --tb=short \
    "$@"

TEST_EXIT_CODE=$?

echo ""
echo "========================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "[OK] All tests passed!"
else
    echo "[FAIL] Some tests failed (exit code: $TEST_EXIT_CODE)"
fi
echo "========================================"

exit $TEST_EXIT_CODE
