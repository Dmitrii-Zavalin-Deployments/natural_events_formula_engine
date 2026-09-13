#!/bin/bash

# ============================================================
# Natural Events Formula Engine – Measurement Runner
# ============================================================
# Usage:
#   ./start_measurements.sh
#
# All paths and technical parameters are loaded strictly from:
#   config/config.json
#
# No CLI arguments are accepted. If config is missing or invalid,
# the Python script will stop with a clear, human-readable error.
# ============================================================

echo "[INFO] Checking python3..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found. Please install Python 3."
    exit 1
fi

echo "[INFO] Checking pip..."
if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "[ERROR] pip not found. Please install pip for Python 3."
    exit 1
fi

echo "[INFO] Checking Firefox..."
if ! command -v firefox >/dev/null 2>&1; then
    echo "[WARN] Firefox not found. Installing Firefox via apt-get..."
    sudo apt-get update && sudo apt-get install -y firefox
else
    echo "[INFO] Firefox is installed."
fi

VENV_DIR="/tmp/measurement_venv_$$"
echo "[INFO] Creating virtual environment at $VENV_DIR"
python3 -m venv "$VENV_DIR"

# Activate venv
source "$VENV_DIR/bin/activate"

echo "[INFO] Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install opencv-python-headless numpy jsonschema

echo "[INFO] Running Natural Events Formula Engine..."
python3 src/measure_object.py

EXIT_CODE=$?

echo "[INFO] Cleaning up virtual environment..."
deactivate
rm -rf "$VENV_DIR"

if [ $EXIT_CODE -ne 0 ]; then
    echo "[ERROR] Measurement run failed. See logs above."
    exit $EXIT_CODE
fi

echo "[INFO] Measurement run completed successfully."

