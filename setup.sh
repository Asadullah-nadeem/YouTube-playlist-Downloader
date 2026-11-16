#!/usr/bin/env bash
# ==============================================================================
# Media Studio Pro - Automated Setup & Environment Health Check
# ==============================================================================

set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================================="
echo "Media Studio Pro - Environment Setup"
echo "=========================================================="

# 1. Python check
PYTHON_CMD="python3"
if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    exit 1
fi
echo "[OK] Python version: $($PYTHON_CMD --version)"

# 2. FFmpeg check
if command -v ffmpeg &> /dev/null; then
    echo "[OK] FFmpeg found: $(which ffmpeg)"
elif [ -f "$HOME/.local/bin/ffmpeg" ]; then
    echo "[OK] FFmpeg found: $HOME/.local/bin/ffmpeg"
else
    echo "[WARN] FFmpeg was not found in standard PATH."
    echo "       Audio extraction and video merging require FFmpeg."
    echo "       Install via: sudo apt install ffmpeg (Debian/Ubuntu) or brew install ffmpeg (macOS)"
fi

# 3. Virtual Environment
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment in ./venv ..."
    $PYTHON_CMD -m venv venv
else
    echo "[OK] Virtual environment exists in ./venv"
fi

# 4. Install requirements
echo "[*] Installing / updating dependencies from requirements.txt..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 5. Check JS runtime (node/bun) for yt-dlp challenge solving
if command -v node &> /dev/null; then
    echo "[OK] JavaScript runtime found (node): $(which node)"
elif command -v bun &> /dev/null; then
    echo "[OK] JavaScript runtime found (bun): $(which bun)"
fi

# 6. Verify installation
echo "[*] Verifying FFmpeg integration..."
./venv/bin/python3 main.py --check-ffmpeg

echo "=========================================================="
echo "[SUCCESS] Setup Complete!"
echo "   Launch Desktop Application: ./run.sh (or python3 main.py)"
echo "   View Supported Platforms  : ./run.sh --platforms"
echo "   Launch Web Dashboard      : python3 main.py --server"
echo "   Build Windows .EXE        : python3 build_exe.py (or build_exe.bat on Windows)"
echo "=========================================================="
