#!/usr/bin/env bash
# ==============================================================================
# YouTube Studio Pro - Quick Launcher Script
# ==============================================================================

set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Check if virtualenv exists, create if not
if [ ! -d "venv" ]; then
    echo "Virtual environment not detected. Setting up..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

# Run with virtual environment
exec ./venv/bin/python3 main.py "$@"

