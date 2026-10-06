#!/usr/bin/env bash
# ==============================================================================
# LiverCheck – Start Script
# ==============================================================================
# This script sets up the environment (if needed), checks for trained models,
# and starts the FastAPI server serving the LiverCheck web application and API.
#
# Usage:
#     ./start.sh
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=================================================="
echo "          Starting LiverCheck Screening Tool      "
echo "=================================================="

# 1. Check or activate Python virtual environment
if [ -d "$PROJECT_DIR/venv" ]; then
    echo "[✓] Activating existing virtual environment (venv)..."
    source "$PROJECT_DIR/venv/bin/activate"
elif command -v python3 >/dev/null 2>&1; then
    echo "[!] Virtual environment not found. Creating venv..."
    python3 -m venv "$PROJECT_DIR/venv"
    source "$PROJECT_DIR/venv/bin/activate"
    echo "[✓] Installing dependencies from requirements.txt..."
    pip install -r "$PROJECT_DIR/requirements.txt"
else
    echo "[ERROR] Python 3 is required but not installed." >&2
    exit 1
fi

# 2. Check if trained model artifact exists; if not, train it
MODEL_PATH="$PROJECT_DIR/outputs/models/livercheck_models.joblib"
if [ ! -f "$MODEL_PATH" ]; then
    echo "[!] Trained model bundle not found at outputs/models/."
    echo "[*] Running training pipeline (src/train.py)..."
    python3 "$PROJECT_DIR/src/train.py"
fi

# 3. Kill any lingering process on port 8000
if lsof -ti:8000 >/dev/null 2>&1; then
    echo "[*] Freeing up port 8000..."
    kill -9 $(lsof -ti:8000) 2>/dev/null || true
    sleep 1
fi

echo "=================================================="
echo " LiverCheck Web App & API: http://localhost:8000  "
echo " API Documentation:       http://localhost:8000/docs"
echo " Press Ctrl+C to stop the server                  "
echo "=================================================="

# 4. Start the server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
