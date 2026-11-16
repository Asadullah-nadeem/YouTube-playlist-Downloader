#!/usr/bin/env bash
# ==============================================================================
# YouTube Studio Pro - Automated Setup & Environment Health Check
# ==============================================================================

set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================================="
echo "🎬 YouTube Studio Pro - Environment Setup"
echo "=========================================================="

# 1. Python check
PYTHON_CMD="python3"
if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH."
    exit 1
fi
echo "✓ Python version: $($PYTHON_CMD --version)"

# 2. FFmpeg check
if command -v ffmpeg &> /dev/null; then
    echo "✓ FFmpeg found: $(which ffmpeg)"
elif [ -f "$HOME/.local/bin/ffmpeg" ]; then
    echo "✓ FFmpeg found: $HOME/.local/bin/ffmpeg"
else
    echo "⚠️  Warning: FFmpeg was not found in PATH."
    echo "   Audio conversion, subtitle embedding, and video merging require FFmpeg."
    echo "   Install via: sudo apt install ffmpeg (Debian/Ubuntu) or brew install ffmpeg (macOS)"
fi

# 3. Virtual Environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment in ./venv ..."
    $PYTHON_CMD -m venv venv
else
    echo "✓ Virtual environment exists in ./venv"
fi

# 4. Install requirements
echo "📦 Installing / updating dependencies from requirements.txt..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 5. Check JS runtime (node/bun/deno) for yt-dlp challenge solving
if command -v node &> /dev/null; then
    echo "✓ JavaScript runtime found (node): $(which node)"
elif command -v bun &> /dev/null; then
    echo "✓ JavaScript runtime found (bun): $(which bun)"
fi

# 6. Verify installation
echo "🔍 Verifying installation..."
./venv/bin/python3 cli.py --check-ffmpeg

echo "=========================================================="
echo "✅ Setup Complete!"
echo "   Launch Modern Desktop App: ./run.sh (or ./venv/bin/python3 main.py)"
echo "   Launch CLI Interface     : ./run.sh --help"
echo "   Launch Web Interface     : ./venv/bin/python3 server.py"
echo "=========================================================="

