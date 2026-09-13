#!/bin/bash

# ============================================================
# Floating Platform Tide Measurement Runner (3-parameter)
# ============================================================
# Usage:
#   ./start_measurements.sh <raw_folder> <processed_folder> <output_csv>
# ============================================================

RAW_DIR="$1"
PROCESSED_DIR="$2"
OUTPUT_CSV="$3"

if [ -z "$RAW_DIR" ] || [ -z "$PROCESSED_DIR" ] || [ -z "$OUTPUT_CSV" ]; then
    echo "Usage: ./start_measurements.sh <raw_folder> <processed_folder> <output_csv>"
    exit 1
fi

echo "[INFO] Checking python3..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found."
    exit 1
fi

echo "[INFO] Checking pip..."
if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "[ERROR] pip not found."
    exit 1
fi

VENV_DIR="/tmp/tide_venv_$$"
echo "[INFO] Creating venv at $VENV_DIR"
python3 -m venv "$VENV_DIR"

source "$VENV_DIR/bin/activate"

echo "[INFO] Installing dependencies..."
pip install --upgrade pip
pip install opencv-python-headless numpy

echo "[INFO] Running measurement script..."
python3 src/measure_object.py "$RAW_DIR" "$PROCESSED_DIR" "$OUTPUT_CSV"

echo "[INFO] Cleaning up..."
deactivate
rm -rf "$VENV_DIR"

echo "[INFO] Done."